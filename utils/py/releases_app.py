#!/usr/bin/env python3
"""releases_app.py — GH-32 Phase 0+1: SQLite-backed RELEASES ledger CLI.

PRD: PROJECT/1-INBOX/GH-32-RELEASES-APP-SQLITE.md (rev 5, post r1-r4 relay review,
relay-system/2026-08-18/gh32-releases-app-prd-review.md). Where this file and the PRD disagree,
the PRD wins.

Authority split (PRD "Decisions" 1): the DB is authoritative for reads/writes at runtime; the
committed logical dump (releases.sql, global-ID-keyed) is authoritative at git merge boundaries
only. On DB<->dump divergence `releases check` fails and `releases check --rebuild`
(dump -> DB, atomic, with a .bak of the displaced DB) is the one documented recovery. Rebuild is
for MERGE RESOLUTION ONLY, never crash recovery — crash recovery is the per-boundary journal
protocol in perform_write()/recover_from_journal().

HARD BOUNDARY (Phase 0): this tool NEVER writes RELEASES.md. `gen` is side-by-side only — it
writes RELEASES.generated.md plus a drift report. If a code path here can reach RELEASES.md for
writing, that is a bug; the only permitted touch on that file is READING it (import, drift).

RELEASES-PREVIEW.md was removed 2026-08-19. It existed to give a human a readable view of the DB
without SQL, and both of its jobs now have better homes: a desktop SQLite viewer for browsing, and
`releases project sync` (GH-39) for pushing release cards to GitHub Projects. Deleting it removes a
tracked, generated artifact that conflicted on every concurrent write, one staged output from every
write transaction, and one crash-recovery surface. The three CLI readers (`list`, `show`, `next`)
remain the in-terminal view.

Artifacts (repo root unless noted):
  releases.db                    the SQLite DB (committed per-repo, PRD Decision 2)
  releases.sql                   canonical logical dump (committed, git-mergeable)
  releases.db.bak                backup of a DB displaced by `check --rebuild`
  RELEASES.generated.md          side-by-side generated view (Phase 0; gen only)
  RELEASES.generated.md.drift    drift report: generated view vs the real RELEASES.md (gen only)
In the git common-dir (GH-448 idiom — never a literal .git/... path; in a linked worktree .git
is a file):
  releases-app.lock              the repo-scoped writer lock
  releases-app-lock-audit.log    append-only contention sidecar (r4: lock evidence lives OUTSIDE
                                 the DB/dump/digest/generation contract, so a refused writer
                                 never mutates a committed artifact)
  releases-app-journal.json      intent journal; exists only mid-write (crash-recovery input)

Environment:
  RELEASES_APP_SESSION   stable per-dogfood-session id stamped into op_receipts (r3)
  RELEASES_APP_NOW       mocked clock (ISO 8601) for the temp-ref staleness and target-date
                         advisories (rule=release-overdue / rule=release-target-passed)
  RELEASES_APP_LOCK_WAIT seconds a busy lock is retried before refusing (default 3)
  RELEASES_APP_CRASH_AT  crash-injection boundary for the recovery negative controls:
                         pre-commit | post-commit | post-stage | mid-rename | post-rename
  RELEASES_APP_EXTRA_DBS colon-separated extra DB paths for `list --all-repos` (the Phase-3
                         cross-repo aggregator reads the hq registry; this is its v1 test surface)

Readers (no lock, no write, safe to run anywhere): `list` (one line per release), `show` (one
full record, by --gid OR --version), `next` (the next unshipped release by target date). Start
with `next` / `show`; drop to raw SQL only for something these three do not answer.

Exit codes: 0 ok; 1 check failure; 2 usage; 3 rule refusal (rule named on stderr);
4 writer-lock refusal; 70 injected crash.
"""

import argparse
import datetime as _dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

# ── constants ───────────────────────────────────────────────────────────────────────────────────

APP = "releases-app"

# GH-491: one vocabulary for CLI writes and the dashboard's ledgerSections.
# `roadmap sections --json` exposes it without opening a repository or database.
ROADMAP_SECTIONS = (
    "Queue / parked intake",
    "Queue",  # Historical short heading (GH-243).
    "In progress",
    "Completed",
    "Deferred · vision",
)


EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2
EXIT_REFUSED = 3      # a rule refused the write; stderr names the rule
EXIT_LOCK_REFUSED = 4
EXIT_CRASH_INJECTED = 70

DB_NAME = "releases.db"
DUMP_NAME = "releases.sql"
DB_BAK_NAME = "releases.db.bak"
GEN_NAME = "RELEASES.generated.md"
DRIFT_NAME = "RELEASES.generated.md.drift"
LEDGER_NAME = "RELEASES.md"          # READ-ONLY for this tool, forever in Phase 0
LOCK_NAME = "releases-app.lock"
AUDIT_NAME = "releases-app-lock-audit.log"
JOURNAL_NAME = "releases-app-journal.json"

# GitHub Projects are a one-way visual projection of this DB.  The immutable Release ID field
# is deliberately the remote idempotency key: we do not add GitHub-owned IDs to the release
# schema, and deleting a card merely lets the next sync recreate its projection.
PROJECT_FIELDS = (
    "Release ID", "Release status", "Target date", "Shipped date", "Codename",
    "Tracking issue", "GitHub release", "Front-door reviewed", "Shakedown reviewed",
    "License file",
)

STATUSES = ("draft", "active", "shipped", "cut")
STATUS_RENDER = {"draft": "Draft", "active": "Active", "shipped": "Shipped", "cut": "Cut"}
MARATHON_STATUSES = ("planned", "running", "done", "escalated", "abandoned")
ITEM_STATES = ("open", "shipped", "cut")
# manifest-state transition legality is CLI-enforced (PRD schema note). GH-111 retires FREEZE for
# DIALED-IN membership: a task is dialed into a release, ships, or is cut. `shipped` is no longer a
# dead end that only the schema knew about — `manifest ship` writes it. Both `shipped` and `cut` are
# terminal FOR THAT ROW: re-admitting an item is a NEW dial-in row, which keeps the trail append-only
# and readable rather than flipping one row back and forth.
# GH-351: `shipped` was a dead end. `manifest cut` refuses on a shipped row and re-dialing adds a
# SECOND row beside it, so a manifest could permanently assert that one issue both shipped and is
# pending. `manifest unship` retracts a false shipped item back to dialed_in instead.
LEGAL_ITEM_TRANSITIONS = {("dialed_in", "shipped"), ("dialed_in", "cut"), ("shipped", "dialed_in")}
GH_ISSUE_URL_RE = re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+/issues/[0-9]+$")
TMP_RE = re.compile(r"^TMP-[A-Z0-9]{6}$")
MIG_RE = re.compile(r"^MIG-[A-Z0-9]{6}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# The legacy `GH_URL:` import field means a RELEASE pointer; it accepted issue URLs only before
# GH-349 and still does. Widening it to PRs was an unrequested cross-caller change with no contract
# test behind it — codex QA, 2026-08-31. The roadmap ledger keeps its own, wider matcher below.
URL_EXTRACT_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/issues/[0-9]+")

# The roadmap ledger has always accepted a `pull` URL in an entry (the pre-GH-349 regex did too),
# so it matches both kinds — org-agnostic, which is the whole point of GH-349.
ROADMAP_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/(?:issues|pull|pulls)/[0-9]+")

# Crockford base32 (PRD GID shape note): every global_id CHECK is the type prefix plus exactly
# 26 characters of [0-9A-HJKMNP-TV-Z], written out in full in the migration so length AND
# alphabet are schema-refused, not convention.
CROCKFORD_GLOB_CLASS = "[0-9A-HJKMNP-TV-Z]"

GENERATION_KEY = "generation"

# GH-525: some repos write a literal placeholder in RELEASES.md for a release that has not shipped
# a version yet — AEGIS-Sleuth's convention is "versions are RECORDED, never RESERVED", so every
# unshipped block reads `Release: TBD`. The schema already models "no version yet" as SQL NULL
# (releases.version is nullable and UNIQUE(repo_id, version) permits any number of NULLs); the
# importer just never mapped a placeholder onto it, so every unshipped block collided on the same
# "version" string. Downstream's only recourse was to FORK this file for two lines, which is how it
# drifted ~1700 lines behind and re-derived an INSERT_RE fix that already existed here.
#
# Comma-separated so a repo can carry more than one placeholder (TBD, N/A, -). Unset by default:
# behaviour is byte-identical to before for every existing install.
UNSHIPPED_VERSION_TOKENS_KEY = "unshipped_version_tokens"

# The settings keys an operator may write with `releases settings set`. Deliberately a
# deny-by-default allowlist: `generation` belongs to the writer protocol and `repo_slug` is the
# ledger's identity, so exposing either here would be handing out a supported way to corrupt the
# ledger. A new configurable key is a deliberate addition to this tuple, never an accident.
CONFIGURABLE_SETTINGS = (UNSHIPPED_VERSION_TOKENS_KEY,)

CRASH_BOUNDARIES = ("pre-commit", "post-commit", "post-stage", "mid-rename", "post-rename")


def _env_float(name, default):
    raw = os.environ.get(name, "")
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


# ── small utilities ─────────────────────────────────────────────────────────────────────────────

def now_iso():
    """Current UTC ISO-8601, mockable via RELEASES_APP_NOW (temp-ref staleness tests)."""
    raw = os.environ.get("RELEASES_APP_NOW", "")
    if raw:
        return raw
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_id():
    return os.environ.get("RELEASES_APP_SESSION", "default")


def new_txn_id():
    return uuid.uuid4().hex


def _ulid_body():
    """26 Crockford-base32 chars: 48-bit ms timestamp + 80 random bits (128-bit ULID)."""
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = int.from_bytes(os.urandom(10), "big")
    value = (ms << 80) | rand
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return "".join(alphabet[(value >> shift) & 0x1F] for shift in range(125, -1, -5))


def new_gid(prefix):
    return "%s%s" % (prefix, _ulid_body())


def warn(rule, detail):
    print("warn: rule=%s: %s" % (rule, detail))


def refuse(rule, detail, code=EXIT_REFUSED):
    print("refused: rule=%s: %s" % (rule, detail), file=sys.stderr)
    sys.exit(code)


def valid_date(s):
    if not DATE_RE.match(s or ""):
        return False
    try:
        _dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def sentence_count(text):
    parts = [p for p in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if p.strip()]
    return len(parts)


def _project_value(item, field_name):
    """Read a GH CLI item field across CLI versions that vary its display-key casing."""
    wanted = field_name.casefold()
    for key, value in item.items():
        if str(key).casefold() == wanted:
            return value
    return None


def _gh_json(argv):
    """Run the configured GH CLI and return its JSON output with an actionable failure."""
    gh_bin = os.environ.get("RELEASES_GH_BIN", "gh")
    try:
        completed = subprocess.run([gh_bin] + argv, check=True, text=True,
                                   capture_output=True)
    except FileNotFoundError:
        refuse("github-project-cli",
               "cannot find %r; install GitHub CLI or set RELEASES_GH_BIN" % gh_bin)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "GitHub CLI failed").strip()
        refuse("github-project-cli", detail)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        refuse("github-project-cli-json",
               "GitHub CLI did not return JSON: %s" % completed.stdout.strip())


def _gh_run(argv):
    """Run a mutating GH CLI command and surface its error without masking it."""
    gh_bin = os.environ.get("RELEASES_GH_BIN", "gh")
    try:
        subprocess.run([gh_bin] + argv, check=True, text=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        refuse("github-project-cli",
               "cannot find %r; install GitHub CLI or set RELEASES_GH_BIN" % gh_bin)
    except subprocess.CalledProcessError as exc:
        refuse("github-project-cli", (exc.stderr or "GitHub CLI failed").strip())


def _project_body(release):
    """Render the draft-card body; all GitHub state remains a read-only DB projection."""
    tracking = release["tracking_url"] or release["tracking_temp"] or "—"
    return """## Release

- **Release ID:** `%s`
- **Milestone:** %s
- **Tracking issue:** %s
- **GitHub release:** %s

## Description

%s

## Exit criterion

%s

---

> Read-only projection from `releases.db`. Edit the release through the Releases CLI; GitHub Project edits do not synchronize back.
""" % (release["global_id"], release["milestone"] or "—", tracking,
       release["gh_release_url"] or "—", release["description"],
       release["exit_criterion"] or "Not recorded")


def _project_release_rows(conn):
    return conn.execute("""SELECT r.*, t.url AS tracking_url, t.temp_id AS tracking_temp
                           FROM releases r JOIN issue_refs t ON t.id = r.tracking_ref_id
                           ORDER BY r.target_date IS NULL, r.target_date, r.version""").fetchall()


# ── repo root + GH-448 lock-path resolution ─────────────────────────────────────────────────────

def resolve_root(explicit):
    if explicit:
        return os.path.abspath(explicit)
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL).decode().strip()
        if out:
            return os.path.abspath(out)
    except Exception:
        pass
    refuse("not-a-git-repo",
           "releases-app resolves the repo root and its lock through git; run inside the repo "
           "or pass --root (vendored/no-.git layouts are not supported in v1)")


def git_common_dir(root):
    """The GH-448 idiom (see utils/py/rtl.py driver_lock_path): the lock must live at the git
    common-dir, never a literal .git/... path — in a linked worktree .git is a file."""
    git_path = os.path.join(root, ".git")
    if os.path.isdir(git_path):
        return git_path
    if os.path.isfile(git_path):
        try:
            common = subprocess.check_output(
                ["git", "-C", root, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                stderr=subprocess.DEVNULL).decode().strip()
            if common and os.path.isdir(common):
                return common
        except Exception:
            pass
    return None


def state_dir(root):
    common = git_common_dir(root)
    if common is None:
        refuse("not-a-git-repo", "cannot resolve the git common-dir for the lock/journal "
               "(GH-448); a git checkout is required")
    return common


def lock_paths(root):
    common = state_dir(root)
    return (os.path.join(common, LOCK_NAME), os.path.join(common, AUDIT_NAME),
            os.path.join(common, JOURNAL_NAME))


def artifact_paths(root):
    return {
        "db": os.path.join(root, DB_NAME),
        "dump": os.path.join(root, DUMP_NAME),
        "bak": os.path.join(root, DB_BAK_NAME),
        "gen": os.path.join(root, GEN_NAME),
        "drift": os.path.join(root, DRIFT_NAME),
        "ledger": os.path.join(root, LEDGER_NAME),
    }


# ── lock + audit sidecar ────────────────────────────────────────────────────────────────────────

def audit_log(root, outcome, detail=""):
    """Append-only contention evidence, OUTSIDE the DB (r4 review finding: a refused writer
    inserting into the committed DB would itself be an unlocked write, able to tear the very trio
    it exists to audit). Line shape: <session_id> <timestamp> <outcome> <detail>, outcome in
    acquired|refused|retried|recovered."""
    _, audit_path, _ = lock_paths(root)
    line = "%s %s %s %s\n" % (session_id(), now_iso(), outcome, detail)
    try:
        with open(audit_path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        print("warn: rule=lock-audit: could not append to %s (%s)" % (audit_path, exc))


class WriterLock:
    """Repo-scoped writer lock (PRD Git story 1). Every acquisition attempt is logged to the
    sidecar; a busy lock retries for RELEASES_APP_LOCK_WAIT seconds, then refuses with exit 4 —
    and a refusal changes no committed artifact (that is the r4 negative control)."""

    def __init__(self, root):
        self.root = root
        self.lock_path, _, self.journal_path = lock_paths(root)
        self.fh = None

    def acquire(self):
        wait = _env_float("RELEASES_APP_LOCK_WAIT", 3.0)
        deadline = time.time() + max(wait, 0.0)
        announced_retry = False
        while True:
            self.fh = open(self.lock_path, "a+", encoding="utf-8")
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                self.fh.close()
                self.fh = None
                if not announced_retry:
                    audit_log(self.root, "retried", "lock busy; retrying for up to %.0fs" % wait)
                    announced_retry = True
                if time.time() >= deadline:
                    audit_log(self.root, "refused", "lock still busy after %.0fs" % wait)
                    refuse("writer-lock",
                           "another releases-app writer holds %s; refusal recorded in the "
                           "lock-audit sidecar; no committed artifact was changed"
                           % self.lock_path, code=EXIT_LOCK_REFUSED)
                time.sleep(0.1)
                continue
            self.fh.seek(0)
            self.fh.truncate()
            self.fh.write("%s %s %s\n" % (now_iso(), session_id(), os.getpid()))
            self.fh.flush()
            audit_log(self.root, "acquired", "pid %d" % os.getpid())
            return self

    def release(self):
        if self.fh is not None:
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            finally:
                self.fh.close()
                self.fh = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False


# ── DB connection (PRAGMA foreign_keys asserted per connection) ─────────────────────────────────

def connect(db_path, must_exist=True):
    if must_exist and not os.path.exists(db_path):
        refuse("not-initialized", "no %s here; run `releases init` first" % DB_NAME)
    # isolation_level=None: transactions are BEGIN/COMMIT'd explicitly by perform_write, so the
    # intent journal -> COMMIT -> stage -> rename ordering is the ONLY ordering that exists.
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        conn.close()
        refuse("foreign-keys-pragma",
               "PRAGMA foreign_keys=ON did not take effect on this connection; refusing to run")
    return conn


def get_setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def unshipped_version_tokens(conn):
    """The configured placeholders that mean "no version yet" (GH-525).

    Returns a set, empty when the setting is absent — and an empty set is what keeps this
    inert for every install that never opts in. Entries are trimmed and compared
    case-sensitively: `TBD` is a literal token in a hand-maintained ledger, not a word to be
    normalised, and accepting `tbd` would quietly widen what counts as "unshipped". Blank
    entries are dropped so a trailing comma cannot turn the empty string into a placeholder —
    an empty `Release:` value stays a malformed ledger, refused as it always was."""
    raw = get_setting(conn, UNSHIPPED_VERSION_TOKENS_KEY)
    if not raw:
        return set()
    return {token.strip() for token in raw.split(",") if token.strip()}


def get_generation(conn):
    try:
        return int(get_setting(conn, GENERATION_KEY, "0"))
    except ValueError:
        return 0


def enforcement_mode(conn):
    return get_setting(conn, "enforcement", "lenient")


# ── migration 001 (v1 schema, PRD "Schema (v1)") ────────────────────────────────────────────────

def _gid_check(column, prefix):
    """Exact-shape global-id CHECK: the type prefix plus exactly 26 characters of the Crockford
    base32 alphabet, written out in full (PRD GID shape note — prefix-only GLOBs were theater)."""
    return "CHECK (%s GLOB '%s%s')" % (column, prefix, CROCKFORD_GLOB_CLASS * 26)


MIGRATION_001 = """
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE settings (            -- per-repo DB, so per-repo enforcement mode lives here
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE repos (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {repo_gid},
  slug TEXT NOT NULL UNIQUE CHECK (length(trim(slug)) > 0)
);  -- device-local paths deliberately NOT committed (review finding): the UI resolves local
    -- checkout paths from the utils/hq/ registry, which is already per-device.

CREATE TABLE issue_refs (          -- normalized issue reference: real URL XOR placeholder
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {ref_gid},
  url TEXT UNIQUE CHECK (url IS NULL OR url GLOB 'https://github.com/*/issues/*'),
  temp_id TEXT UNIQUE CHECK (temp_id IS NULL OR
    temp_id GLOB 'TMP-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]' OR
    temp_id GLOB 'MIG-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]'),  -- MIG-: import-only (CLI-enforced)
  created_at TEXT NOT NULL,
  CHECK ((url IS NULL) != (temp_id IS NULL))   -- exactly one
);

CREATE TABLE marathons (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {mar_gid},
  repo_id INTEGER NOT NULL REFERENCES repos(id),
  tracking_ref_id INTEGER NOT NULL REFERENCES issue_refs(id),
  status TEXT NOT NULL CHECK (status IN ('planned','running','done','escalated','abandoned')),
  created_at TEXT NOT NULL
);

CREATE TABLE releases (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {rel_gid},
  repo_id INTEGER NOT NULL REFERENCES repos(id),
  version TEXT CHECK (version IS NULL OR length(trim(version)) > 0),
  codename TEXT,
  status TEXT NOT NULL CHECK (status IN ('draft','active','shipped','cut')),
  target_date TEXT CHECK (target_date IS NULL OR target_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  shipped_date TEXT CHECK (shipped_date IS NULL OR shipped_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  description TEXT NOT NULL CHECK (length(trim(description)) > 0),
  exit_criterion TEXT,
  tracking_ref_id INTEGER NOT NULL REFERENCES issue_refs(id),
  marathon_id INTEGER REFERENCES marathons(id),
  gh_release_url TEXT,
  milestone TEXT,
  front_door_reviewed TEXT CHECK (front_door_reviewed IN ('Yes','No') OR front_door_reviewed IS NULL),
  shakedown_reviewed  TEXT CHECK (shakedown_reviewed  IN ('Yes','No') OR shakedown_reviewed  IS NULL),
  license_file        TEXT CHECK (license_file        IN ('Yes','No') OR license_file        IS NULL),
  UNIQUE (repo_id, version)
);

CREATE TABLE manifest_items (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {mfi_gid},
  release_id INTEGER NOT NULL REFERENCES releases(id),
  issue_ref_id INTEGER NOT NULL REFERENCES issue_refs(id),
  state TEXT NOT NULL CHECK (state IN ('open','shipped','cut')),
  UNIQUE (release_id, issue_ref_id)
);

CREATE TABLE manifest_state_events (   -- append-only re-scope trail (review finding: the old
  id INTEGER PRIMARY KEY,              -- single overwriteable state_changed cell lost history)
  item_id INTEGER NOT NULL REFERENCES manifest_items(id),
  from_state TEXT NOT NULL CHECK (from_state IN ('open','shipped','cut')),
  to_state   TEXT NOT NULL CHECK (to_state   IN ('open','shipped','cut')),
  at TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(trim(reason)) > 0)   -- a cut without a reason is refused
);
-- Append-only is enforced by triggers, not convention (r2 review finding):
CREATE TRIGGER mse_no_update BEFORE UPDATE ON manifest_state_events
  BEGIN SELECT RAISE(ABORT, 'manifest_state_events is append-only'); END;
CREATE TRIGGER mse_no_delete BEFORE DELETE ON manifest_state_events
  BEGIN SELECT RAISE(ABORT, 'manifest_state_events is append-only'); END;
-- (same trigger pair on op_receipts). Transition LEGALITY and the item-state/event coupling are
-- CLI-enforced, stated as such: the CLI updates manifest_items.state and appends the event in ONE
-- transaction; a direct writer that skips the event is caught by the digest chain below, not
-- prevented.

CREATE TABLE doc_lines (               -- document-level verbatim preservation (r2: the 86-line
  id INTEGER PRIMARY KEY,              -- preamble is release-less; legacy_lines can't hold it)
  repo_id INTEGER NOT NULL REFERENCES repos(id),
  position INTEGER NOT NULL,           -- ordering among document-level segments
  content TEXT NOT NULL,
  UNIQUE (repo_id, position)
);

CREATE TABLE legacy_lines (            -- lossless import: unmapped/continuation lines, verbatim
  id INTEGER PRIMARY KEY,
  release_id INTEGER NOT NULL REFERENCES releases(id),
  position INTEGER NOT NULL,
  content TEXT NOT NULL,
  disposition TEXT,                    -- NULL = pending; else 'kept'|'migrated'|'dropped:<why>'
  UNIQUE (release_id, position)
);

CREATE TABLE grandfather_entries (     -- r3: referenced throughout but previously never defined
  id INTEGER PRIMARY KEY,
  import_run TEXT NOT NULL,            -- one id per `releases import` invocation
  release_gid TEXT,                    -- NULL for document-level entries
  rule TEXT NOT NULL,                  -- which rule was tolerated/defaulted
  source_value TEXT,                   -- what the legacy file had (NULL = field absent)
  supplied_value TEXT,                 -- what import wrote (default, MIG- ref, normalization)
  disposition TEXT                     -- NULL = pending; strict flip requires none pending
);

CREATE TABLE op_receipts (             -- append-only CLI operation log (append-only via the same
  id INTEGER PRIMARY KEY,              -- trigger pair as manifest_state_events)
  op TEXT NOT NULL,
  target_gid TEXT,
  at TEXT NOT NULL,
  txn_id TEXT NOT NULL,                -- one per CLI transaction
  session_id TEXT NOT NULL,            -- r3: stable per-dogfood-session id (env-provided), so the
                                       --   exit gate's ">=2 sessions" is mechanically checkable
  state_digest_before TEXT NOT NULL,   -- sha256 of the BUSINESS-STATE dump (r3: excludes
  state_digest_after TEXT NOT NULL     --   op_receipts, lock_audit, generation, and all digest
);                                     --   fields — the old dump digest was self-referential and
                                       --   uncomputable). Chain rule: each receipt's `before` must
                                       --   equal the previous receipt's `after`; `check` recomputes
                                       --   the current business-state digest and a mismatch with the
                                       --   latest `after` = receipt-less mutation.
CREATE TRIGGER op_no_update BEFORE UPDATE ON op_receipts
  BEGIN SELECT RAISE(ABORT, 'op_receipts is append-only'); END;
CREATE TRIGGER op_no_delete BEFORE DELETE ON op_receipts
  BEGIN SELECT RAISE(ABORT, 'op_receipts is append-only'); END;

CREATE INDEX idx_releases_repo ON releases(repo_id);
CREATE INDEX idx_items_release ON manifest_items(release_id);
CREATE INDEX idx_mse_item ON manifest_state_events(item_id);
CREATE INDEX idx_legacy_release ON legacy_lines(release_id);
CREATE INDEX idx_gf_import ON grandfather_entries(import_run);
""".format(
    repo_gid=_gid_check("global_id", "repo-"),
    ref_gid=_gid_check("global_id", "ref-"),
    mar_gid=_gid_check("global_id", "mar-"),
    rel_gid=_gid_check("global_id", "rel-"),
    mfi_gid=_gid_check("global_id", "mfi-"),
)


MIGRATION_002_DDL = """
CREATE TABLE IF NOT EXISTS roadmap_items (  -- GH-69/GH-269: roadmap ledger.
  id INTEGER PRIMARY KEY,                   --
  global_id TEXT NOT NULL UNIQUE {rmi_gid}, -- edit; `releases roadmap sync` mirrors it here. Rows
  repo_id INTEGER NOT NULL REFERENCES repos(id),  -- follow the GH-32 grammar (GID-keyed, no
  gh_number INTEGER,                        -- integer ids as dump values), so merges and rebuilds
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),  -- need nothing new.
  section TEXT NOT NULL CHECK (length(trim(section)) > 0),
  position INTEGER NOT NULL,                -- order within its section at last sync
  status_marker TEXT,                       -- the entry's leading status emoji, when present
  complexity INTEGER, risk INTEGER, effort INTEGER,     -- cx/risk/eff when the entry states them
  doc_path TEXT,                            -- first PROJECT/** link
  issue_url TEXT,                           -- first this-repo issue/PR URL
  raw_text TEXT NOT NULL,                   -- the entry block VERBATIM (lossless shadow)
  first_seen TEXT NOT NULL,
  updated_at TEXT NOT NULL,                 -- last sync that CHANGED this row (not last sync run)
  UNIQUE (repo_id, gh_number)
);
CREATE INDEX IF NOT EXISTS idx_roadmap_repo ON roadmap_items(repo_id);
""".format(rmi_gid=_gid_check("global_id", "rmi-"))


def _ddl_statements(script):
    """Split a trigger-free DDL script into individual statements.

    GH-111: exists so migrations can avoid executescript(), which commits the caller's
    transaction. Deliberately NOT general — it would mis-split a CREATE TRIGGER body, whose
    BEGIN…END contains its own semicolons. Only trigger-free scripts may use it; migration
    004 issues its trigger DDL as explicit single execute() calls instead.
    """
    if "CREATE TRIGGER" in script.upper():
        raise ValueError("_ddl_statements cannot split trigger bodies; issue them individually")
    # sqlite3.complete_statement() is comment- and string-literal-aware; a naive split(";")
    # cuts mid-statement on the first `--` comment containing a semicolon.
    statements, buffer = [], ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        statements.append(buffer.strip())
    return statements


def _table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def _col(row, name, default=None):
    """Read a column that may not exist yet on an un-migrated ledger. sqlite3.Row raises
    IndexError for an absent key, so a bare row["baseline_count"] would turn "you have not run
    `releases migrate`" into a traceback."""
    try:
        return row[name]
    except (IndexError, KeyError):
        return default


def _has_column(conn, table, column):
    """Schema probe. The dump writer uses it so a PRE-migration database can still be dumped
    (and therefore digested) — `perform_migration` needs `business_digest` on the old shape
    before it touches anything, and the dump grammar's absent-trailing-fields-read-as-NULL rule
    makes the shorter record a legal dump rather than a lossy one."""
    if not _table_exists(conn, table):
        return False
    return any(r["name"] == column for r in conn.execute("PRAGMA table_info(%s)" % table))


def _ensure_roadmap_schema(conn, stamp=True):
    """Apply migration 002 idempotently. MUST run inside a perform_write mutate when the DB
    predates it: the new schema_migrations row is business state, and a schema change outside a
    receipt would trip check's receipt-vs-change bypass detection — correctly.

    GH-111: issued as individual execute() calls, NOT executescript(). Python's sqlite3
    COMMITs any open transaction before running a script, so the old idiom would silently
    split perform_migration()'s single transaction when 002 and 004 are both pending —
    leaving 002 durable after a 004 failure while the journal still claims all-or-nothing.

    stamp=False is the REGISTRY entry point: `apply_migrations` owns the ledger row there, and
    `_rebuild` calls it with stamping suppressed entirely so it can write the ledger itself
    afterwards. A self-stamping callback would collide with that on the primary key.
    """
    for statement in _ddl_statements(MIGRATION_002_DDL):
        conn.execute(statement)
    if stamp and conn.execute("SELECT 1 FROM schema_migrations WHERE version = 2").fetchone() is None:
        conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (2, ?)",
                     (now_iso(),))


MIGRATION_004_ITEMS_NEW = """
CREATE TABLE manifest_items_new (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {mfi_gid},
  release_id INTEGER NOT NULL REFERENCES releases(id),
  issue_ref_id INTEGER NOT NULL REFERENCES issue_refs(id),
  state TEXT NOT NULL CHECK (state IN ('dialed_in','shipped','cut')),
  dialed_in_at TEXT,
  dial_reason TEXT,
  marathon_id INTEGER REFERENCES marathons(id)
)"""

MIGRATION_004_EVENTS_NEW = """
CREATE TABLE manifest_state_events_new (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES manifest_items(id),
  from_state TEXT NOT NULL CHECK (from_state IN ('open','dialed_in','shipped','cut')),
  to_state   TEXT NOT NULL CHECK (to_state   IN ('open','dialed_in','shipped','cut')),
  at TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(trim(reason)) > 0)
)"""


def _migration_004(conn):
    """GH-111: retire FREEZE for DIALED-IN membership.

    TRANSACTION-SAFE BY CONSTRUCTION — every statement goes through execute(), never
    executescript(), which would COMMIT the caller's transaction and silently void
    perform_migration()'s FK bracket, rollback, digest chain and receipt coupling.

    Parent (manifest_items) is rebuilt before child (manifest_state_events), and `id`
    values are carried across verbatim so the child's item_id linkage — and with it the
    event digest chain — still resolves. Both CHECK vocabularies change, which SQLite
    cannot do in place, hence the rebuilds. `open` stays legal in the EVENT table forever:
    historical rows are copied unchanged rather than remapped, because rewriting them
    would be the silent history edit this repo forbids everywhere else.
    """
    # ── parent: manifest_items ────────────────────────────────────────────────────────
    conn.execute(MIGRATION_004_ITEMS_NEW.format(mfi_gid=_gid_check("global_id", "mfi-")))
    conn.execute("""INSERT INTO manifest_items_new
                      (id, global_id, release_id, issue_ref_id, state,
                       dialed_in_at, dial_reason, marathon_id)
                    SELECT id, global_id, release_id, issue_ref_id,
                           CASE state WHEN 'open' THEN 'dialed_in' ELSE state END,
                           NULL, NULL, NULL
                      FROM manifest_items""")
    conn.execute("DROP TABLE manifest_items")
    conn.execute("ALTER TABLE manifest_items_new RENAME TO manifest_items")
    # The old UNIQUE (release_id, issue_ref_id) is deliberately NOT recreated: re-admitting a
    # cut item is a NEW row, which that constraint would refuse. Exclusivity now applies to
    # ACTIVE membership only, so cut history never blocks a redial here or on another release.
    conn.execute("""CREATE UNIQUE INDEX idx_mfi_active_exclusive
                      ON manifest_items(issue_ref_id) WHERE state = 'dialed_in'""")
    conn.execute("CREATE INDEX idx_mfi_release ON manifest_items(release_id)")

    # ── child: manifest_state_events (DROP TABLE also drops its triggers) ─────────────
    conn.execute(MIGRATION_004_EVENTS_NEW)
    conn.execute("""INSERT INTO manifest_state_events_new (id, item_id, from_state, to_state, at, reason)
                    SELECT id, item_id, from_state, to_state, at, reason
                      FROM manifest_state_events""")
    conn.execute("DROP TABLE manifest_state_events")
    conn.execute("ALTER TABLE manifest_state_events_new RENAME TO manifest_state_events")
    conn.execute("""CREATE TRIGGER mse_no_update BEFORE UPDATE ON manifest_state_events
                      BEGIN SELECT RAISE(ABORT, 'manifest_state_events is append-only'); END""")
    conn.execute("""CREATE TRIGGER mse_no_delete BEFORE DELETE ON manifest_state_events
                      BEGIN SELECT RAISE(ABORT, 'manifest_state_events is append-only'); END""")
    conn.execute("CREATE INDEX idx_mse_item ON manifest_state_events(item_id)")

    # ── releases: baseline (one count field + two provenance fields) ──────────────────
    conn.execute("ALTER TABLE releases ADD COLUMN baseline_count INTEGER")
    conn.execute("ALTER TABLE releases ADD COLUMN baseline_at TEXT")
    conn.execute("ALTER TABLE releases ADD COLUMN baseline_source TEXT "
                 "CHECK (baseline_source IS NULL OR baseline_source IN ('observed','backfilled'))")
    # A marathon belongs to at most one release; links are historical and permanent.
    conn.execute("""CREATE UNIQUE INDEX idx_rel_marathon_exclusive
                      ON releases(marathon_id) WHERE marathon_id IS NOT NULL""")
    # The plan calls for a table CHECK on the baseline trio (all-NULL or all-populated) and for
    # write-once. SQLite cannot add a CHECK in place, and `releases` is the most-referenced table
    # in the schema — rebuilding it costs more risk than the invariant is worth — so the same two
    # rules are expressed as triggers. Structural either way: a direct DB writer is refused, not
    # merely detected. A partial baseline must never reach rendering, and overwriting one would
    # erase the exact thing it exists to measure.
    for name, event, when in (
        ("rel_baseline_shape_ins", "BEFORE INSERT ON releases",
         "(NEW.baseline_count IS NULL) + (NEW.baseline_at IS NULL) + "
         "(NEW.baseline_source IS NULL) NOT IN (0, 3)"),
        ("rel_baseline_shape_upd", "BEFORE UPDATE ON releases",
         "(NEW.baseline_count IS NULL) + (NEW.baseline_at IS NULL) + "
         "(NEW.baseline_source IS NULL) NOT IN (0, 3)"),
    ):
        conn.execute("CREATE TRIGGER %s %s WHEN %s BEGIN SELECT RAISE(ABORT, "
                     "'releases baseline fields are all-NULL or all-populated'); END"
                     % (name, event, when))
    conn.execute("""CREATE TRIGGER rel_baseline_write_once BEFORE UPDATE OF baseline_count
                      ON releases
                      WHEN OLD.baseline_count IS NOT NULL
                       AND NEW.baseline_count IS NOT OLD.baseline_count
                      BEGIN SELECT RAISE(ABORT, 'releases.baseline_count is write-once'); END""")
    # Backfill releases already underway. Flagged 'backfilled', never 'observed': the count is
    # inferred from today's manifest, not witnessed at the kickoff it claims to describe.
    stamp = now_iso()
    for row in conn.execute("SELECT id FROM releases WHERE status = 'active'").fetchall():
        n = conn.execute("""SELECT COUNT(*) FROM manifest_items
                             WHERE release_id = ? AND state IN ('dialed_in','shipped')""",
                         (row["id"],)).fetchone()[0]
        if n:
            conn.execute("""UPDATE releases SET baseline_count = ?, baseline_at = ?,
                             baseline_source = 'backfilled' WHERE id = ?""", (n, stamp, row["id"]))


RATING_COLUMNS = ("rating_pri", "rating_sev", "rating_appeal", "rating_effort", "rating_ovr")


def _migration_003(conn):
    """GH-108: the pri/sev/appeal/effort rating columns on roadmap_items.

    Physically prefixed `rating_` because the table already carries a legacy `effort` column
    (cx/risk/eff's third field), which SQLite cannot duplicate and whose grandfathered data must
    not share storage with the new vocabulary. The prefix never leaks past this module — the
    exporter translates to the frozen public axis names.

    TRANSACTION-SAFE: plain execute() calls, never executescript(), because a v2 database runs
    this and 004 inside ONE BEGIN IMMEDIATE — a mid-flight commit here would leave 003 durable
    after a 004 failure while the journal still described an all-or-nothing migration.
    Idempotent by SCHEMA PROBE, not by version number, so a residual version/DDL mismatch
    degrades to a no-op rather than an error.
    """
    ranges = {"rating_ovr": (4, 400)}       # calc's own 4-400 scale; the four axes are 1-100
    for column in RATING_COLUMNS:
        if _has_column(conn, "roadmap_items", column):
            continue
        low, high = ranges.get(column, (1, 100))
        conn.execute("ALTER TABLE roadmap_items ADD COLUMN %s INTEGER "
                     "CHECK (%s IS NULL OR (%s BETWEEN %d AND %d))"
                     % (column, column, column, low, high))


def _has_trigger(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
                        (name,)).fetchone() is not None


def _migration_005(conn):
    """GH-111 follow-up: extend baseline write-once to the PROVENANCE fields.

    Migration 004 guarded `baseline_count` only, so a direct writer could relabel a `backfilled`
    baseline as `observed`, or move `baseline_at`, without tripping anything (aider/qwen3.8-max QA
    r1). The provenance is what makes the count trustworthy — a count whose source can be quietly
    rewritten is worth less than no count — so it gets the same structural guarantee.

    This is a NEW version rather than an edit to 004 because 004 has already been applied to live
    ledgers. Amending an applied migration would leave two databases at the same stamped version
    with different schemas, which is the one thing the registry rule exists to prevent.

    TRANSACTION-SAFE and idempotent by schema probe.
    """
    for column in ("baseline_at", "baseline_source"):
        name = "rel_baseline_%s_write_once" % column.split("_", 1)[1]
        if _has_trigger(conn, name):
            continue
        conn.execute("""CREATE TRIGGER %s BEFORE UPDATE OF %s ON releases
                          WHEN OLD.%s IS NOT NULL AND NEW.%s IS NOT OLD.%s
                          BEGIN SELECT RAISE(ABORT,
                            'releases.%s is write-once (baseline provenance)'); END"""
                     % (name, column, column, column, column, column))


MIGRATION_006_DDL = """
CREATE TABLE IF NOT EXISTS jog_queue (
  id INTEGER PRIMARY KEY,
  global_id TEXT NOT NULL UNIQUE {jog_gid},
  repo_id INTEGER NOT NULL REFERENCES repos(id),
  gh_number INTEGER NOT NULL,
  position INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'parked', 'failed', 'dropped', 'archived')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  lease_pid INTEGER,
  failure_reason TEXT,
  UNIQUE (repo_id, gh_number)
);
CREATE INDEX IF NOT EXISTS idx_jog_queue_repo_pos ON jog_queue(repo_id, position);
CREATE INDEX IF NOT EXISTS idx_jog_queue_status ON jog_queue(status);
"""


def _ensure_jog_schema(conn, stamp=True):
    """Apply migration 006 idempotently."""
    ddl = MIGRATION_006_DDL.format(jog_gid=_gid_check("global_id", "jog-"))
    for statement in _ddl_statements(ddl):
        conn.execute(statement)
    if stamp and conn.execute("SELECT 1 FROM schema_migrations WHERE version = 6").fetchone() is None:
        conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (6, ?)",
                     (now_iso(),))


def _migration_006(conn):
    """GH-259: Add dedicated jog_queue table for serial execution."""
    _ensure_jog_schema(conn, stamp=False)


def _migration_007(conn):
    """GH-355: Add updated_at modification timestamps to remaining tables.

    Only roadmap_items and jog_queue previously carried updated_at; adding updated_at to
    releases, manifest_items, marathons, repos, settings, issue_refs, doc_lines, legacy_lines,
    and grandfather_entries allows consumers to detect changes and staleness across the ledger.
    """
    stamp = now_iso()
    tables = ("releases", "manifest_items", "marathons", "repos", "settings", "issue_refs",
              "doc_lines", "legacy_lines", "grandfather_entries")
    for table in tables:
        if _table_exists(conn, table) and not _has_column(conn, table, "updated_at"):
            conn.execute("ALTER TABLE %s ADD COLUMN updated_at TEXT" % table)
            if table == "issue_refs" and _has_column(conn, table, "created_at"):
                conn.execute("UPDATE issue_refs SET updated_at = COALESCE(created_at, ?)", (stamp,))
            elif table == "marathons" and _has_column(conn, table, "created_at"):
                conn.execute("UPDATE marathons SET updated_at = COALESCE(created_at, ?)", (stamp,))
            elif table == "releases":
                conn.execute("UPDATE releases SET updated_at = COALESCE(shipped_date, baseline_at, ?)", (stamp,))
            elif table == "manifest_items":
                conn.execute("UPDATE manifest_items SET updated_at = COALESCE(dialed_in_at, ?)", (stamp,))
            else:
                conn.execute("UPDATE %s SET updated_at = ?" % table, (stamp,))



# The migration REGISTRY is the truth (GH-111). apply/rebuild stamp exactly the versions
# present here — never a hard-coded range — so a deliberate gap (e.g. GH-111's 004 landing
# before GH-108's 003) yields a ledger of {1,2,4} rather than a false claim to 3. Pending
# migrations apply in ascending numeric order; gaps are safe only because migrations are
# mutually INDEPENDENT, a standing constraint on every future entry.
#
# `txn_safe` marks a callback that may run inside perform_migration()'s single transaction:
# it must never use executescript() or any other implicit-commit API. 001 is exempt because
# it is reachable only on a fresh database (cmd_init) or a rebuild, never alongside other
# pending versions on a live ledger.
MIGRATIONS = {
    1: {"apply": lambda conn: conn.executescript(MIGRATION_001), "txn_safe": False},
    2: {"apply": lambda conn: _ensure_roadmap_schema(conn, stamp=False), "txn_safe": True},
    3: {"apply": _migration_003, "txn_safe": True},
    4: {"apply": _migration_004, "txn_safe": True},
    5: {"apply": _migration_005, "txn_safe": True},
    6: {"apply": _migration_006, "txn_safe": True},
    7: {"apply": _migration_007, "txn_safe": True},
}



def registry_versions():
    """Ordered versions this codebase defines. The ledger never claims more than this."""
    return sorted(MIGRATIONS)


def pending_versions(conn):
    try:
        applied = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
    except sqlite3.OperationalError:
        applied = set()   # fresh DB: the tracker table itself is created by migration 001
    return [v for v in registry_versions() if v not in applied]


def apply_migrations(conn, stamp_ledger=True):
    """Apply pending registry migrations in ascending order.

    stamp_ledger=False is the rebuild path: _rebuild() materializes DDL here and writes the
    ledger rows itself AFTER load_dump() (which skips the dump's schema_migrations records),
    so DDL and ledger agree by construction instead of colliding on the primary key.
    """
    for version in pending_versions(conn):
        MIGRATIONS[version]["apply"](conn)
        if stamp_ledger and conn.execute("SELECT 1 FROM schema_migrations WHERE version = ?",
                                         (version,)).fetchone() is None:
            conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                         (version, now_iso()))


# ── canonical dump (PRD Git story 6) ────────────────────────────────────────────────────────────
# GID-bearing rows keyed by global_id; non-GID rows by natural key (parent GID / repo slug +
# position / txn_id / the grandfather import_run composite). Integer PKs and FK ids never appear
# as VALUES; row order follows insertion order (stable through merges), and rebuild renumbers
# the integer PKs deterministically in that order. grandfather_entries rows carry an explicit
# `-- gf-key:` comment spelling out the PRD's natural key (import_run + release-gid-or-document
# + rule + source ordinal) — the ordinal is the row's position within its key group, which the
# dump's order preserves. The lock-audit sidecar is not in the dump at all (it is not in the DB).

def _sql_str(value):
    if value is None:
        return "NULL"
    return "'%s'" % str(value).replace("'", "''")


def _rows(conn, sql):
    return [dict(r) for r in conn.execute(sql).fetchall()]


def _emit(w, table, columns, rows):
    if not rows:
        return
    w("-- table: %s" % table)
    for row in rows:
        values = ", ".join(_sql_str(row[c]) for c in columns)
        w("INSERT INTO %s(%s) VALUES(%s);" % (table, ", ".join(columns), values))


def dump_text(conn, generation, include_receipts=True, include_generation=True):
    """Canonical logical dump. include_receipts=False, include_generation=False yields exactly
    the BUSINESS-STATE text the receipt digests hash (r3: excluding op_receipts, generation and
    digest fields keeps the digest computable and non-self-referential)."""
    out = []

    def w(s=""):
        out.append(s)

    w("-- releases-app canonical dump (GH-32 grammar: GID-keyed rows, natural keys elsewhere,")
    w("-- no integer PKs/FKs as values; rebuild renumbers deterministically)")
    if include_generation:
        w("-- generation: %d" % generation)

    _emit(w, "schema_migrations", ["version", "applied_at"],
          _rows(conn, "SELECT version, applied_at FROM schema_migrations ORDER BY version"))

    settings_cols = ["key", "value"]
    settings_select = "SELECT key, value{extra} FROM settings"
    if _has_column(conn, "settings", "updated_at"):
        settings_cols.append("updated_at")
        settings_extra = ", updated_at"
    else:
        settings_extra = ""
    if not include_generation:
        settings_select += " WHERE key != '%s'" % GENERATION_KEY
    _emit(w, "settings", settings_cols, _rows(conn, settings_select.format(extra=settings_extra) + " ORDER BY key"))

    repo_cols = ["global_id", "slug"]
    repo_extra = ""
    if _has_column(conn, "repos", "updated_at"):
        repo_cols.append("updated_at")
        repo_extra = ", updated_at"
    _emit(w, "repos", repo_cols,
          _rows(conn, "SELECT global_id, slug%s FROM repos ORDER BY id" % repo_extra))

    ref_cols = ["global_id", "url", "temp_id", "created_at"]
    ref_extra = ""
    if _has_column(conn, "issue_refs", "updated_at"):
        ref_cols.append("updated_at")
        ref_extra = ", updated_at"
    _emit(w, "issue_refs", ref_cols,
          _rows(conn, "SELECT global_id, url, temp_id, created_at%s FROM issue_refs ORDER BY id" % ref_extra))

    mar_cols = ["global_id", "repo_gid", "tracking_ref_gid", "status", "created_at"]
    mar_extra = ""
    if _has_column(conn, "marathons", "updated_at"):
        mar_cols.append("updated_at")
        mar_extra = ", m.updated_at"
    _emit(w, "marathons", mar_cols,
          _rows(conn, """SELECT m.global_id, r.global_id AS repo_gid, t.global_id AS tracking_ref_gid,
                         m.status, m.created_at%s
                         FROM marathons m JOIN repos r ON r.id = m.repo_id
                         JOIN issue_refs t ON t.id = m.tracking_ref_id ORDER BY m.id""" % mar_extra))

    # GH-111 appends three baseline fields to the RELEASE record and three membership fields to
    # the MANIFEST ITEM record, both in fixed trailing order. They are emitted only when the
    # schema has them, so a pre-004 database still dumps (and digests) cleanly; on the way back
    # in, absent trailing fields read as NULL.
    rel_cols = ["global_id", "repo_gid", "version", "codename", "status", "target_date",
                "shipped_date", "description", "exit_criterion", "tracking_ref_gid",
                "marathon_gid", "gh_release_url", "milestone", "front_door_reviewed",
                "shakedown_reviewed", "license_file"]
    rel_select = """SELECT rel.global_id, r.global_id AS repo_gid, rel.version, rel.codename,
                    rel.status, rel.target_date, rel.shipped_date, rel.description,
                    rel.exit_criterion, t.global_id AS tracking_ref_gid,
                    mar.global_id AS marathon_gid, rel.gh_release_url, rel.milestone,
                    rel.front_door_reviewed, rel.shakedown_reviewed, rel.license_file{extra}
                    FROM releases rel JOIN repos r ON r.id = rel.repo_id
                    JOIN issue_refs t ON t.id = rel.tracking_ref_id
                    LEFT JOIN marathons mar ON mar.id = rel.marathon_id ORDER BY rel.id"""
    rel_extra = ""
    if _has_column(conn, "releases", "baseline_count"):
        rel_cols += ["baseline_count", "baseline_at", "baseline_source"]
        rel_extra += ", rel.baseline_count, rel.baseline_at, rel.baseline_source"
    if _has_column(conn, "releases", "updated_at"):
        rel_cols.append("updated_at")
        rel_extra += ", rel.updated_at"
    _emit(w, "releases", rel_cols, _rows(conn, rel_select.format(extra=rel_extra)))

    mfi_cols = ["global_id", "release_gid", "issue_ref_gid", "state"]
    mfi_select = """SELECT mi.global_id, rel.global_id AS release_gid,
                    t.global_id AS issue_ref_gid, mi.state{extra}
                    FROM manifest_items mi JOIN releases rel ON rel.id = mi.release_id
                    JOIN issue_refs t ON t.id = mi.issue_ref_id{join} ORDER BY mi.id"""
    mfi_extra, mfi_join = "", ""
    if _has_column(conn, "manifest_items", "dialed_in_at"):
        # marathon_id is an integer FK, and integer FKs never appear as dump VALUES — the row
        # carries its marathon's GID, exactly as the release record does.
        mfi_cols += ["dialed_in_at", "dial_reason", "marathon_gid"]
        mfi_extra += ", mi.dialed_in_at, mi.dial_reason, mar.global_id AS marathon_gid"
        mfi_join = " LEFT JOIN marathons mar ON mar.id = mi.marathon_id"
    if _has_column(conn, "manifest_items", "updated_at"):
        mfi_cols.append("updated_at")
        mfi_extra += ", mi.updated_at"
    _emit(w, "manifest_items", mfi_cols,
          _rows(conn, mfi_select.format(extra=mfi_extra, join=mfi_join)))

    _emit(w, "manifest_state_events", ["item_gid", "from_state", "to_state", "at", "reason"],
          _rows(conn, """SELECT mi.global_id AS item_gid, e.from_state, e.to_state, e.at, e.reason
                         FROM manifest_state_events e JOIN manifest_items mi ON mi.id = e.item_id
                         ORDER BY e.id"""))

    doc_cols = ["repo_gid", "position", "content"]
    doc_extra = ""
    if _has_column(conn, "doc_lines", "updated_at"):
        doc_cols.append("updated_at")
        doc_extra = ", d.updated_at"
    _emit(w, "doc_lines", doc_cols,
          _rows(conn, """SELECT r.global_id AS repo_gid, d.position, d.content%s
                         FROM doc_lines d JOIN repos r ON r.id = d.repo_id
                         ORDER BY d.repo_id, d.position""" % doc_extra))

    leg_cols = ["release_gid", "position", "content"]
    leg_extra = ""
    if _has_column(conn, "legacy_lines", "updated_at"):
        leg_cols.append("updated_at")
        leg_extra = ", l.updated_at"
    _emit(w, "legacy_lines", leg_cols,
          _rows(conn, """SELECT rel.global_id AS release_gid, l.position, l.content%s
                         FROM legacy_lines l JOIN releases rel ON rel.id = l.release_id
                         ORDER BY l.release_id, l.position""" % leg_extra))

    gf_extra = ""
    if _has_column(conn, "grandfather_entries", "updated_at"):
        gf_extra = ", g.updated_at"
    gf_rows = _rows(conn, """SELECT g.import_run, COALESCE(g.release_gid, '(document)') AS rgid,
                             g.rule, g.source_value, g.supplied_value, g.disposition, g.id AS _id%s
                             FROM grandfather_entries g
                             ORDER BY g.import_run, COALESCE(g.release_gid, ''), g.rule, g.id""" % gf_extra)
    if gf_rows:
        w("-- table: grandfather_entries (natural key per PRD grammar: import_run + "
          "release_gid-or-(document) + rule + source ordinal)")
        ordinal = {}
        for row in gf_rows:
            key = (row["import_run"], row["rgid"], row["rule"])
            ordinal[key] = ordinal.get(key, 0) + 1
            cols = ["import_run", "rgid", "rule", "source_value", "supplied_value", "disposition"]
            if _has_column(conn, "grandfather_entries", "updated_at"):
                cols.append("updated_at")
            values = ", ".join(_sql_str(row.get(c)) for c in cols)
            w("-- gf-key: %s/%s/%s/%d" % (row["import_run"], row["rgid"], row["rule"],
                                           ordinal[key]))
            ins_cols = ["import_run", "release_gid", "rule", "source_value", "supplied_value", "disposition"]
            if _has_column(conn, "grandfather_entries", "updated_at"):
                ins_cols.append("updated_at")
            w("INSERT INTO grandfather_entries(%s) VALUES(%s);" % (", ".join(ins_cols), values))

    if _table_exists(conn, "roadmap_items"):
        # GH-108's five rating columns are appended in fixed trailing order, emitted only when the
        # schema has them (same absent-reads-as-NULL rule as the GH-111 fields above). `calc` is
        # NEVER dumped: it is derived at read time from the four axes, and storing a derived value
        # invites the drift class this grammar exists to prevent.
        rmi_cols = ["global_id", "repo_gid", "gh_number", "title", "section", "position",
                    "status_marker", "complexity", "risk", "effort", "doc_path", "issue_url",
                    "raw_text", "first_seen", "updated_at"]
        rmi_select = """SELECT ri.global_id, r.global_id AS repo_gid, ri.gh_number, ri.title,
                        ri.section, ri.position, ri.status_marker, ri.complexity, ri.risk,
                        ri.effort, ri.doc_path, ri.issue_url, ri.raw_text, ri.first_seen,
                        ri.updated_at{extra}
                        FROM roadmap_items ri JOIN repos r ON r.id = ri.repo_id
                        ORDER BY ri.id"""
        if _has_column(conn, "roadmap_items", "rating_pri"):
            rmi_cols += list(RATING_COLUMNS)
            rmi_extra = "".join(", ri.%s" % c for c in RATING_COLUMNS)
        else:
            rmi_extra = ""
        _emit(w, "roadmap_items", rmi_cols, _rows(conn, rmi_select.format(extra=rmi_extra)))

    if _table_exists(conn, "jog_queue"):
        jq_cols = ["global_id", "repo_gid", "gh_number", "position", "status",
                   "created_at", "updated_at", "attempt_count", "lease_pid", "failure_reason"]
        jq_select = """SELECT jq.global_id, r.global_id AS repo_gid, jq.gh_number,
                       jq.position, jq.status, jq.created_at, jq.updated_at,
                       jq.attempt_count, NULL AS lease_pid, jq.failure_reason
                       FROM jog_queue jq JOIN repos r ON r.id = jq.repo_id
                       ORDER BY jq.position, jq.id"""
        _emit(w, "jog_queue", jq_cols, _rows(conn, jq_select))


    if include_receipts:

        _emit(w, "op_receipts",
              ["op", "target_gid", "at", "txn_id", "session_id",
               "state_digest_before", "state_digest_after"],
              _rows(conn, "SELECT op, target_gid, at, txn_id, session_id, state_digest_before, "
                          "state_digest_after FROM op_receipts ORDER BY id"))
    return "\n".join(out) + "\n"


def business_digest(conn):
    text = dump_text(conn, generation=0, include_receipts=False, include_generation=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump_generation_from_text(text):
    for line in text.splitlines():
        m = re.match(r"^-- generation: (\d+)$", line.strip())
        if m:
            return int(m.group(1))
    return None


# ── generation marker in the generated file ─────────────────────────────────────────────────────
# The side-by-side generated file carries the marker as an HTML comment on line 1 (the trio
# contract needs it there). The real RELEASES.md never carries one — this tool never writes that
# file, and no header is added during Phase 0 (the header arrives with the Phase 2 flip).

GEN_MARKER_RE = re.compile(r"^<!-- releases-app generation: (\d+) -->$")


def gen_marker(generation):
    return "<!-- releases-app generation: %d -->" % generation


# ── staged writes + crash injection ─────────────────────────────────────────────────────────────

def _crash(boundary):
    if os.environ.get("RELEASES_APP_CRASH_AT", "") == boundary:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(EXIT_CRASH_INJECTED)


def _stage_write(final_path, content):
    """Staged temp-name write; the caller renames (atomic) only once the DB commit is durable."""
    tmp = "%s.tmp-%s" % (final_path, new_txn_id()[:12])
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    return tmp


def _atomic_write(final_path, content):
    tmp = _stage_write(final_path, content)
    os.replace(tmp, final_path)


# ── the writer protocol (PRD Git story 2-3): journal -> txn -> stage -> rename -> clear ─────────

def refresh_preview(root):
    """GH-106: after a successful write, refresh the baked viewer artifacts — but only the ones
    the repo has ADOPTED (the file already exists at root; presence is the opt-in signal, so
    fixtures and non-adopting repos are silent no-ops). Best-effort by design: the write is
    already durable with its receipt when this runs, so a refresh failure WARNS on stderr and
    never fails the operation. Success is silent (the exporter's stdout is captured).

    GH-108 adds LEADERBOARD.html on the same terms — one template, two baked artifacts, both
    regenerated by the same hook so a ranking can never lag the ledger it ranks."""
    exporter = os.path.join(root, "utils", "timeline", "export_timeline.py")
    if not os.path.exists(exporter):
        return
    for name, flag in (("RELEASES-PREVIEW.html", "--preview"),
                       ("LEADERBOARD.html", "--leaderboard")):
        target = os.path.join(root, name)
        if not os.path.exists(target):
            continue
        try:
            r = subprocess.run([sys.executable, exporter, flag, target],
                               cwd=root, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                print("warning: %s refresh failed (the write itself is committed): %s"
                      % (name, r.stderr.strip() or r.stdout.strip() or
                         "exit %d" % r.returncode), file=sys.stderr)
        except Exception as exc:  # never let a rendered artifact break a committed write
            print("warning: %s refresh failed (the write itself is committed): %s"
                  % (name, exc), file=sys.stderr)
    # LEADERBOARD.md rides the same adoption signal — generated, never hand-edited.
    board = os.path.join(root, "LEADERBOARD.md")
    script = os.path.join(root, "utils", "leaderboard.sh")
    if os.path.exists(board) and os.path.exists(script):
        try:
            r = subprocess.run(["bash", script], cwd=root, capture_output=True, text=True,
                               timeout=60)
            if r.returncode != 0:
                print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
                      % (r.stderr.strip() or "exit %d" % r.returncode), file=sys.stderr)
        except Exception as exc:
            print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
                  % exc, file=sys.stderr)


def perform_write(root, conn, op, target_gid, mutate):
    """Run one CLI transaction under the full multi-artifact protocol:

      write intent journal (txn_id, NEXT generation, planned outputs)   [BEFORE the DB commit]
      -> BEGIN IMMEDIATE -> mutate -> stamp generation into settings -> COMMIT
      -> stage dump (+ generated view when one exists), each carrying that generation
      -> atomic renames -> clear journal.

    `mutate(conn)` does the business writes; the op_receipt (before/after business-state digests)
    is appended HERE so no writer can forget it. Recovery per boundary is `check`'s job
    (recover_from_journal); RELEASES_APP_CRASH_AT lands on the five named boundaries. The caller
    must NOT hold the writer lock (this function takes it)."""
    paths = artifact_paths(root)
    lock = WriterLock(root)
    lock.acquire()
    try:
        if os.path.exists(lock.journal_path):
            refuse("journal-live",
                   "an intent journal from an interrupted write exists (%s); run `releases check` "
                   "to recover before writing again" % lock.journal_path)

        generation = get_generation(conn) + 1
        txn_id = new_txn_id()
        planned = [paths["dump"]]
        if os.path.exists(paths["gen"]):
            planned.append(paths["gen"])

        journal = {
            "app": APP, "txn_id": txn_id, "session_id": session_id(), "op": op,
            "generation": generation, "planned_outputs": planned,
            "db": paths["db"], "started_at": now_iso(),
        }
        _atomic_write(lock.journal_path, json.dumps(journal, indent=2) + "\n")

        digest_before = business_digest(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            mutate(conn)
        except BaseException:
            # a refused/mutating error never leaves a live journal behind: the DB rolled back,
            # so there is nothing to recover — clear the journal and re-raise. (An injected
            # crash uses os._exit and deliberately does NOT pass through here.)
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
            try:
                os.unlink(lock.journal_path)
            except OSError:
                pass
            raise
        now = now_iso()
        if _has_column(conn, "settings", "updated_at"):
            cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                               (str(generation), now, GENERATION_KEY))
            if cur.rowcount == 0:
                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
                             (GENERATION_KEY, str(generation), now))
        else:
            cur = conn.execute("UPDATE settings SET value = ? WHERE key = ?",
                               (str(generation), GENERATION_KEY))
            if cur.rowcount == 0:
                conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
                             (GENERATION_KEY, str(generation)))
        digest_after = business_digest(conn)
        conn.execute("""INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id,
                         state_digest_before, state_digest_after)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (op, target_gid, now, txn_id, session_id(),
                      digest_before, digest_after))
        _crash("pre-commit")
        conn.commit()
        _crash("post-commit")

        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
        if os.path.exists(paths["gen"]):
            staged.append((_stage_write(paths["gen"],
                                        gen_marker(generation) + "\n" + render_ledger(conn)),
                           paths["gen"]))
        _crash("post-stage")

        for i, (tmp, final) in enumerate(staged):
            os.replace(tmp, final)
            if i == 0 and len(staged) > 1:
                _crash("mid-rename")
        _crash("post-rename")

        os.unlink(lock.journal_path)
        refresh_preview(root)  # GH-106: adoption-gated, best-effort — after full durability
        return txn_id
    finally:
        lock.release()


def perform_migration(root, conn):
    """Upgrade a LIVE ledger to the registry's current schema, under perform_write's durability
    contract plus one step it structurally cannot host.

    `perform_write` issues BEGIN IMMEDIATE on a connection where `connect()` already turned
    foreign keys on, and SQLite IGNORES a `PRAGMA foreign_keys` change while a transaction is
    open. A table-rebuild migration therefore has no executable path through it — the pragma
    would silently fail to take effect and the swap would trip enforcement mid-flight. The one
    difference is where the bracket goes:

        acquire writer lock -> write intent journal
        -> PRAGMA foreign_keys = OFF          [after the journal, BEFORE BEGIN]
        -> BEGIN IMMEDIATE
        -> apply pending registry migrations, ascending, parent-before-child
        -> PRAGMA foreign_key_check           [fails the migration if it returns any row]
        -> stamp generation + op_receipt -> COMMIT
        -> PRAGMA foreign_keys = ON           [restored only after commit]
        -> stage dump -> atomic renames -> clear journal

    On any error the transaction rolls back, enforcement is restored, and the journal is LEFT IN
    PLACE so `releases check` sees an interrupted migration exactly as it sees an interrupted
    write. That is deliberately louder than perform_write's error path, which clears the journal:
    a half-considered schema change is worth stopping the world for.
    """
    paths = artifact_paths(root)
    lock = WriterLock(root)
    lock.acquire()
    try:
        if os.path.exists(lock.journal_path):
            refuse("journal-live",
                   "an intent journal from an interrupted write exists (%s); run `releases check` "
                   "to recover before migrating" % lock.journal_path)

        pending = pending_versions(conn)
        if not pending:
            applied = [r["version"] for r in
                       conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
            print("schema is current at version %d (registry: %s); nothing to migrate"
                  % (max(applied) if applied else 0,
                     ", ".join(str(v) for v in registry_versions())))
            return None
        unsafe = [v for v in pending if not MIGRATIONS[v]["txn_safe"]]
        if unsafe:
            refuse("migration-not-transaction-safe",
                   "migration(s) %s are not marked transaction-safe and cannot run against a live "
                   "ledger; they are reachable only from `releases init` or `check --rebuild`"
                   % ", ".join(str(v) for v in unsafe))

        generation = get_generation(conn) + 1
        txn_id = new_txn_id()
        planned = [paths["dump"]]
        if os.path.exists(paths["gen"]):
            planned.append(paths["gen"])
        journal = {
            "app": APP, "txn_id": txn_id, "session_id": session_id(), "op": "migrate",
            "generation": generation, "planned_outputs": planned, "db": paths["db"],
            "started_at": now_iso(), "pending_migrations": pending,
        }
        _atomic_write(lock.journal_path, json.dumps(journal, indent=2) + "\n")

        digest_before = business_digest(conn)
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN IMMEDIATE")
            apply_migrations(conn)
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                refuse("migration-fk-violation",
                       "the migrated schema has %d foreign-key violation(s) (first: %s); the "
                       "migration is rolled back and the ledger is untouched"
                       % (len(violations), tuple(violations[0])))
            now = now_iso()
            if _has_column(conn, "settings", "updated_at"):
                cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                                   (str(generation), now, GENERATION_KEY))
                if cur.rowcount == 0:
                    conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
                                 (GENERATION_KEY, str(generation), now))
            else:
                cur = conn.execute("UPDATE settings SET value = ? WHERE key = ?",
                                   (str(generation), GENERATION_KEY))
                if cur.rowcount == 0:
                    conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
                                 (GENERATION_KEY, str(generation)))
            digest_after = business_digest(conn)
            conn.execute("""INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id,
                             state_digest_before, state_digest_after)
                             VALUES ('migrate', ?, ?, ?, ?, ?, ?)""",
                         ("migrations: %s" % ",".join(str(v) for v in pending), now_iso(),
                          txn_id, session_id(), digest_before, digest_after))
            _crash("pre-commit")
            conn.commit()
        except BaseException:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
            conn.execute("PRAGMA foreign_keys = ON")
            raise      # journal deliberately left in place
        conn.execute("PRAGMA foreign_keys = ON")
        _crash("post-commit")

        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
        if os.path.exists(paths["gen"]):
            staged.append((_stage_write(paths["gen"],
                                        gen_marker(generation) + "\n" + render_ledger(conn)),
                           paths["gen"]))
        _crash("post-stage")
        for i, (tmp, final) in enumerate(staged):
            os.replace(tmp, final)
            if i == 0 and len(staged) > 1:
                _crash("mid-rename")
        _crash("post-rename")
        os.unlink(lock.journal_path)
        refresh_preview(root)
        print("migrated %s to schema version %d (applied %s; generation %d)"
              % (DB_NAME, max(pending), ", ".join(str(v) for v in pending), generation))
        return txn_id
    finally:
        lock.release()


def cmd_migrate(args):
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        perform_migration(root, conn)
    finally:
        conn.close()


def recover_from_journal(root, conn):
    """Per-boundary crash recovery (PRD Git story 3), run by `check` (which holds the writer
    lock — this function must not take it again). pre-COMMIT (DB generation < journal's):
    discard stage remnants, clear the journal — the DB never changed. post-COMMIT, any later
    boundary (DB generation == journal's): the DB is truth; REGENERATE the dump and generated
    view from the DB state (staged files, present or missing, are disposable — they are
    derivable), complete the renames, clear the journal — the committed operation is never
    discarded."""
    paths = artifact_paths(root)
    _, _, journal_path = lock_paths(root)
    if not os.path.exists(journal_path):
        return None
    with open(journal_path, encoding="utf-8") as fh:
        journal = json.load(fh)
    txn_id = journal.get("txn_id", "?")
    jgen = int(journal.get("generation", 0))

    # A crash mid-transaction can leave an inert (header-only, never-recognized-hot) sqlite
    # rollback journal behind. Give SQLite the chance to play back a genuinely hot one, then
    # sweep the leftover — we hold the writer lock and know this crash is ours.
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.rollback()
    except sqlite3.Error:
        pass
    for suffix in ("-journal", "-wal"):
        p = paths["db"] + suffix
        if os.path.exists(p):
            try:
                os.unlink(p)
            except OSError:
                pass

    db_gen = get_generation(conn)

    # stage remnants are disposable on BOTH branches; sweep them first
    for final in journal.get("planned_outputs", []):
        d, base = os.path.split(final)
        try:
            names = os.listdir(d) if os.path.isdir(d) else []
        except OSError:
            names = []
        for name in names:
            if name.startswith(base + ".tmp-"):
                try:
                    os.unlink(os.path.join(d, name))
                except OSError:
                    pass

    if db_gen < jgen:
        os.unlink(journal_path)
        audit_log(root, "recovered",
                  "pre-COMMIT crash discarded (txn %s, gen %d); DB unchanged" % (txn_id, jgen))
        return ("discarded", txn_id)
    if db_gen == jgen:
        _atomic_write(paths["dump"], dump_text(conn, db_gen))
        if os.path.exists(paths["gen"]):
            _atomic_write(paths["gen"], gen_marker(db_gen) + "\n" + render_ledger(conn))
        os.unlink(journal_path)
        audit_log(root, "recovered",
                  "post-COMMIT crash completed (txn %s, gen %d); committed operation preserved"
                  % (txn_id, jgen))
        return ("completed", txn_id)
    refuse("recovery-impossible",
           "DB generation %d is ahead of the journal's %d — state is not interpretable; inspect "
           "%s manually" % (db_gen, jgen, journal_path))


# ── legacy RELEASES.md parsing (import + drift) ─────────────────────────────────────────────────

LABEL_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 '&/_-]{0,48}):(?:[ \t](.*))?$")

# Labels the v1 schema maps to columns. Everything else in a block — `Iterations:` bands (absent
# from the schema BY DESIGN, aegis proved them harmful), `Manifest:` prose, `RC evidence:`,
# `Post RC update:`, ad-hoc labels, and continuation paragraphs — is preserved VERBATIM, in
# order, in legacy_lines until dispositioned. `Manifest-Members:` bare numbers stay legacy too:
# they cannot be auto-converted to URLs offline (the rebalanceOS retired-tracker case is the
# reason), and each becomes a grandfather entry awaiting disposition.
MAPPED_LABELS = {
    "Release", "Status", "Target Date", "Codename", "Description", "Exit criterion",
    "GH_URL", "Milestone", "Front-door reviewed", "Shakedown reviewed", "License file",
    "Shipped", "Tracking Issue",
}
UNMAPPED_LABELS = {"Iterations", "Manifest", "Manifest-Members", "RC evidence", "Post RC update"}


def parse_legacy_ledger(path):
    """Parse a RELEASES.md-format ledger. Returns (doc_lines, blocks): doc_lines is the verbatim
    preamble (everything before the first `Release:` line); each block carries its mapped field
    values (LAST occurrence wins, matching the awk consumers) and its extras — unmapped label
    lines and continuation lines, verbatim, with their original line numbers as ordering."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    doc, blocks = [], []
    current = None
    for idx, raw in enumerate(lines):
        line = raw.rstrip("\r")
        if line.startswith("Release:"):
            current = {"line": idx, "fields": {}, "extras": []}
            current["fields"]["Release"] = [(line[len("Release:"):].strip())]
            blocks.append(current)
            continue
        if current is None:
            doc.append(line)
            continue
        m = LABEL_RE.match(line)
        label = m.group(1).strip() if m else None
        if m and label in MAPPED_LABELS:
            current["fields"].setdefault(label, []).append(m.group(2) or "")
            if label != "Shipped":
                continue
            # Shipped keeps its whole prose line verbatim alongside the extracted date
            current["extras"].append((idx, line))
            continue
        if m and label in UNMAPPED_LABELS:
            current["extras"].append((idx, line))
            continue
        if m:
            current["extras"].append((idx, line))   # unknown ad-hoc label
            continue
        if not line.strip():
            continue                                 # block separator; renderer emits its own
        current["extras"].append((idx, line))        # continuation paragraph
    return doc, blocks


def _normalize_status(raw):
    low = (raw or "").strip().lower()
    if low in STATUSES:
        return low, False
    return "active", True


# ── generator: the pinned normalized rendering (PRD Generator contract) ─────────────────────────
# Canonical field order and spellings are defined HERE, once. Consumers parse fields, not bytes;
# lossless preservation lives in doc_lines/legacy_lines, both re-rendered verbatim in order until
# dispositioned. `Manifest-Members:` is generated from manifest_items when they exist (imported
# bare numbers stay in legacy_lines verbatim instead). `Status: Shipped` normalizes to the enum;
# the generator renders the canonical capitalized spelling.

def render_ledger(conn):
    out = []

    def w(s=""):
        out.append(s)

    for row in conn.execute("""SELECT d.content FROM doc_lines d JOIN repos r ON r.id = d.repo_id
                               ORDER BY d.repo_id, d.position"""):
        w(row["content"])

    first = True
    for rel in conn.execute("""SELECT rel.*, t.url AS tracking_url, t.temp_id AS tracking_temp
                               FROM releases rel JOIN issue_refs t ON t.id = rel.tracking_ref_id
                               ORDER BY rel.id""").fetchall():
        if not first:
            w()
        first = False
        w("Release: %s" % (rel["version"] if rel["version"] else "(unversioned)"))
        w("Status: %s" % STATUS_RENDER[rel["status"]])
        if rel["shipped_date"]:
            w("Shipped: %s" % rel["shipped_date"])
        if rel["target_date"]:
            w("Target Date: %s" % rel["target_date"])
        if rel["codename"]:
            w("Codename: %s" % rel["codename"])
        if rel["description"]:
            w("Description: %s" % rel["description"])
        if rel["exit_criterion"]:
            w("Exit criterion: %s" % rel["exit_criterion"])
        members = conn.execute("""SELECT t.url, t.temp_id FROM manifest_items mi
                                  JOIN issue_refs t ON t.id = mi.issue_ref_id
                                  WHERE mi.release_id = ? ORDER BY mi.id""",
                               (rel["id"],)).fetchall()
        if members:
            nums = [ (m["url"] or "").rsplit("/", 1)[-1] or (m["temp_id"] or "?") for m in members ]
            w("Manifest-Members: %s" % " ".join(nums))
        if rel["gh_release_url"]:
            w("GH_URL: %s" % rel["gh_release_url"])
        if rel["tracking_url"]:
            w("Tracking Issue: %s" % rel["tracking_url"])
        elif rel["tracking_temp"]:
            w("Tracking Issue: %s" % rel["tracking_temp"])
        if rel["milestone"]:
            w("Milestone: %s" % rel["milestone"])
        if rel["front_door_reviewed"]:
            w("Front-door reviewed: %s" % rel["front_door_reviewed"])
        if rel["shakedown_reviewed"]:
            w("Shakedown reviewed: %s" % rel["shakedown_reviewed"])
        if rel["license_file"]:
            w("License file: %s" % rel["license_file"])
        for ll in conn.execute("""SELECT content FROM legacy_lines l
                                  WHERE l.release_id = ? ORDER BY l.position""",
                               (rel["id"],)).fetchall():
            w(ll["content"])
    return "\n".join(out) + "\n"


def write_drift_report(root, conn):
    """Side-by-side drift report (Phase 0 sole-writer evidence): compares the DB-backed view
    against the real RELEASES.md. A hand-edit during the measured window is visible here, and
    each one resets the sole-writer clock (PRD Phase 0). A stale real file after CLI writes is
    EXPECTED in Phase 0 — the flip is Phase 2 — so direction matters and is labeled."""
    paths = artifact_paths(root)
    lines = ["releases-app drift report (GH-32 Phase 0, side-by-side)",
             "generated: %s" % now_iso(),
             "real ledger: %s (READ-ONLY — never written by this tool)" % paths["ledger"],
             ""]
    if not os.path.exists(paths["ledger"]):
        lines.append("no real RELEASES.md present — nothing to drift against")
        _atomic_write(paths["drift"], "\n".join(lines) + "\n")
        return
    doc, blocks = parse_legacy_ledger(paths["ledger"])
    db_rows = {r["version"]: r for r in conn.execute("SELECT * FROM releases ORDER BY id")}
    db_versions = set(db_rows)
    file_versions = {b["fields"]["Release"][0] for b in blocks if b["fields"].get("Release")}

    hand_edits = 0
    only_db = sorted(v for v in (db_versions - file_versions) if v)
    only_file = sorted(v for v in (file_versions - db_versions) if v)
    if only_db:
        lines.append("[stale-file] in the DB but not in RELEASES.md (expected after CLI writes; "
                     "the real file is refreshed only at the Phase 2 flip): %s"
                     % ", ".join(only_db))
    if only_file:
        hand_edits += len(only_file)
        lines.append("[hand-edit] blocks in RELEASES.md with no DB counterpart: %s"
                     % ", ".join(only_file))
    for b in blocks:
        version = b["fields"].get("Release", [None])[0]
        if version not in db_rows:
            continue
        row = db_rows[version]
        f = b["fields"]

        def fv(label):
            vals = f.get(label, [])
            return vals[-1] if vals else None

        status, _ = _normalize_status(fv("Status") or "")
        for label, file_val, db_val in (
                ("Status", status, row["status"]),
                ("Codename", fv("Codename"), row["codename"]),
                ("Target Date", fv("Target Date"), row["target_date"]),
                ("Description", fv("Description"), row["description"]),
                ("Milestone", fv("Milestone"), row["milestone"])):
            if (file_val or "") != (db_val or ""):
                hand_edits += 1
                lines.append("[drift] Release %s: %s is %r in the file, %r in the DB "
                             "(file edited by hand, or stale after a CLI write)"
                             % (version, label, file_val, db_val))
    lines.append("")
    lines.append("summary: %d file-only block(s), %d field-level difference(s). File-only blocks "
                 "and unexpected field drift are hand-edits — each resets the Phase 0 "
                 "sole-writer clock. Stale-after-CLI directions do not." % (len(only_file),
                                                                            hand_edits))
    _atomic_write(paths["drift"], "\n".join(lines) + "\n")


# ── structural validation (refused in BOTH modes — lenient tolerates imported legacy debt,
#    never new corruption) and GH-28 thresholds (strict: refuse / lenient: warn and write) ───────

def check_tracking_token(token, allow_mig=False):
    """Returns ('url', url) or ('temp', temp_id); refuses otherwise, naming the rule."""
    token = (token or "").strip()
    if not token:
        refuse("tracking-required",
               "every release/marathon requires a tracking GH issue (SOP 1/2): pass an issue "
               "URL or a TMP-XXXXXX offline placeholder")
    if GH_ISSUE_URL_RE.match(token):
        return ("url", token)
    if TMP_RE.match(token):
        return ("temp", token)
    if MIG_RE.match(token):
        if allow_mig:
            return ("temp", token)
        refuse("mig-import-only",
               "MIG-XXXXXX placeholders are import-only (migration debt, distinct from the "
               "GitHub-down TMP- fallback); disposition them via `releases reconcile`")
    refuse("issue-url-shape",
           "tracking reference %r must be https://github.com/<org>/<repo>/issues/<n> or "
           "TMP-XXXXXX" % token)


def issue_ref_for_token(conn, token, allow_mig=False):
    """Find or create the issue_refs row for a URL/TMP-/MIG- token (identity is the row, so
    re-adding an existing URL reuses it)."""
    kind, value = check_tracking_token(token, allow_mig=allow_mig)
    col, other = ("url", "temp_id") if kind == "url" else ("temp_id", "url")
    row = conn.execute("SELECT * FROM issue_refs WHERE %s = ?" % col, (value,)).fetchone()
    if row:
        return row
    gid = new_gid("ref-")
    now = now_iso()
    if _has_column(conn, "issue_refs", "updated_at"):
        conn.execute("INSERT INTO issue_refs(global_id, url, temp_id, created_at, updated_at) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (gid, value if kind == "url" else None,
                      value if kind == "temp" else None, now, now))
    else:
        conn.execute("INSERT INTO issue_refs(global_id, url, temp_id, created_at) "
                     "VALUES (?, ?, ?, ?)",
                     (gid, value if kind == "url" else None,
                      value if kind == "temp" else None, now))
    return conn.execute("SELECT * FROM issue_refs WHERE global_id = ?", (gid,)).fetchone()


def _github_slug_from_origin(root):
    """Best-effort '<org>/<repo>' from a github.com origin remote; None when unresolved."""
    try:
        out = subprocess.check_output(["git", "-C", root, "remote", "get-url", "origin"],
                                      stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None
    m = re.search(r"github\.com[/:]([\w.\-]+/[\w.\-]+?)(?:\.git)?$", out)
    return m.group(1) if m else None


def tracking_token_to_url(conn, root, token):
    """GH-222: canonicalize `releases update --tracking-issue <N|URL>` to a real issue URL.
    A bare issue number expands against the tracked repo slug (when org/repo shaped) or the
    github.com origin remote; a full URL passes the shared shape check. Placeholders are
    refused: a re-point supersedes a real issue with a real issue (the TMP-/MIG- lifecycle
    belongs to `add` and `reconcile --map`). GitHub issue state is never consulted — the
    legitimate case is re-pointing to an already-closed superseding umbrella."""
    token = (token or "").strip()
    if re.fullmatch(r"[0-9]+", token):
        row = conn.execute("SELECT slug FROM repos ORDER BY id LIMIT 1").fetchone()
        slug = row["slug"] if row else ""
        if not re.fullmatch(r"[\w.\-]+/[\w.\-]+", slug):
            slug = _github_slug_from_origin(root) or ""
        if not slug:
            refuse("tracking-issue-slug",
                   "cannot expand bare issue number %r: the repo slug is not org/repo shaped "
                   "and no github.com origin remote resolves; pass the full "
                   "https://github.com/<org>/<repo>/issues/<n> URL" % token)
        return "https://github.com/%s/issues/%s" % (slug, token)
    kind, value = check_tracking_token(token)
    if kind != "url":
        refuse("tracking-repoint-shape",
               "re-pointing to placeholder %r is refused: a re-point supersedes a real issue "
               "with a real issue (the TMP-/MIG- lifecycle belongs to `add` and "
               "`reconcile --map`)" % value)
    return value


def validate_release_fields(conn, mode, *, version=None, status=None, target_date=None,
                            shipped_date=None, description=None, exit_criterion=None,
                            editing_gid=None):
    """Structural rules refuse in both modes; GH-28 thresholds (new/edited rows only) refuse in
    strict and warn-and-write in lenient. Every refusal and warning names its rule. `version` is
    the EFFECTIVE version (new or current-when-editing) so uniqueness covers updates too."""
    if status is not None and status not in STATUSES:
        refuse("enum-status", "status %r must be one of %s" % (status, "|".join(STATUSES)))
    if version is not None and not version.strip():
        refuse("version-nonempty", "version must be non-empty when present")
    for name, value in (("target_date", target_date), ("shipped_date", shipped_date)):
        if value is not None and not valid_date(value):
            refuse("date-shape", "%s %r must be a valid YYYY-MM-DD calendar date" % (name, value))
    if description is not None and not description.strip():
        refuse("description-nonempty", "description must be non-empty")
    if version is not None:
        q = "SELECT global_id FROM releases WHERE version = ?"
        args = [version]
        if editing_gid:
            q += " AND global_id != ?"
            args.append(editing_gid)
        if conn.execute(q, args).fetchone():
            refuse("version-uniqueness",
                   "version %r already exists in this repo (structural: UNIQUE(repo_id, version) "
                   "is refused in both modes)" % version)
    if description is not None and sentence_count(description) > 4:
        msg = "description is %d sentences; GH-28 threshold is <= 4" % sentence_count(description)
        if mode == "strict":
            refuse("description-length", msg + " (strict mode refuses)")
        warn("description-length", msg + " (lenient mode: warned and written)")
    if exit_criterion is not None and len(exit_criterion) > 1000:
        msg = "exit criterion is %d chars; GH-28 threshold is ~1000" % len(exit_criterion)
        if mode == "strict":
            refuse("exit-criterion-length", msg + " (strict mode refuses)")
        warn("exit-criterion-length", msg + " (lenient mode: warned and written)")


def find_release(conn, gid):
    row = conn.execute("SELECT * FROM releases WHERE global_id = ?", (gid,)).fetchone()
    if not row:
        refuse("unknown-gid", "no release with global id %r" % gid)
    return row


def _qa(value):
    return value if value in ("Yes", "No") else None


# ── commands ────────────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    if os.path.exists(paths["db"]):
        refuse("already-initialized", "%s already exists here" % DB_NAME)
    slug = args.slug or os.path.basename(os.path.normpath(root))
    lock = WriterLock(root)
    lock.acquire()
    try:
        conn = connect(paths["db"], must_exist=False)
        try:
            apply_migrations(conn)
            now = now_iso()
            if _has_column(conn, "repos", "updated_at"):
                conn.execute("INSERT INTO repos(global_id, slug, updated_at) VALUES (?, ?, ?)",
                             (new_gid("repo-"), slug, now))
            else:
                conn.execute("INSERT INTO repos(global_id, slug) VALUES (?, ?)",
                             (new_gid("repo-"), slug))
            if _has_column(conn, "settings", "updated_at"):
                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES ('enforcement', 'lenient', ?)", (now,))
                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES ('repo_slug', ?, ?)", (slug, now))
                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, '1', ?)", (GENERATION_KEY, now))
            else:
                conn.execute("INSERT INTO settings(key, value) VALUES ('enforcement', 'lenient')")
                conn.execute("INSERT INTO settings(key, value) VALUES ('repo_slug', ?)", (slug,))
                conn.execute("INSERT INTO settings(key, value) VALUES (?, '1')", (GENERATION_KEY,))
            generation = get_generation(conn)
            _atomic_write(paths["dump"], dump_text(conn, generation))
        finally:
            conn.close()
    finally:
        lock.release()
    print("initialized %s (slug %r, enforcement=lenient, generation 1); canonical dump at %s"
          % (paths["db"], slug, paths["dump"]))


def _grandfather(conn, import_run, release_gid, rule, source_value, supplied_value):
    if _has_column(conn, "grandfather_entries", "updated_at"):
        conn.execute("""INSERT INTO grandfather_entries(import_run, release_gid, rule, source_value,
                         supplied_value, disposition, updated_at) VALUES (?, ?, ?, ?, ?, NULL, ?)""",
                     (import_run, release_gid, rule, source_value, supplied_value, now_iso()))
    else:
        conn.execute("""INSERT INTO grandfather_entries(import_run, release_gid, rule, source_value,
                         supplied_value, disposition) VALUES (?, ?, ?, ?, ?, NULL)""",
                     (import_run, release_gid, rule, source_value, supplied_value))


def cmd_import(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if conn.execute("SELECT COUNT(*) c FROM releases").fetchone()["c"]:
            refuse("import-once",
                   "this DB already holds releases; the legacy import is ONE-SHOT (PRD Phase 0) "
                   "— diverge via the dump merge procedure, not re-import")
        ledger = args.file or paths["ledger"]
        if not os.path.exists(ledger):
            refuse("import-source-missing", "no ledger file at %s" % ledger)
        doc_lines, blocks = parse_legacy_ledger(ledger)
        repo = conn.execute("SELECT * FROM repos ORDER BY id LIMIT 1").fetchone()
        import_run = "imp-%s-%s" % (_dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S"),
                                    uuid.uuid4().hex[:6])

        def mutate(conn):
            now = now_iso()
            for pos, content in enumerate(doc_lines):
                if _has_column(conn, "doc_lines", "updated_at"):
                    conn.execute("INSERT INTO doc_lines(repo_id, position, content, updated_at) VALUES (?, ?, ?, ?)",
                                 (repo["id"], pos, content, now))
                else:
                    conn.execute("INSERT INTO doc_lines(repo_id, position, content) VALUES (?, ?, ?)",
                                 (repo["id"], pos, content))
            placeholder_versions = unshipped_version_tokens(conn)
            for block in blocks:
                f = block["fields"]

                def fv(label):
                    vals = f.get(label, [])
                    return vals[-1] if vals else None

                version = (fv("Release") or "").strip()
                if not version:
                    refuse("release-value", "a block's Release: value is empty (malformed ledger)")
                # GH-525: a configured placeholder means "not shipped yet" -> SQL NULL, so any
                # number of unshipped blocks coexist. Read once per import, above the loop.
                if version in placeholder_versions:
                    version = None
                gid = new_gid("rel-")

                status_raw = fv("Status")
                if not status_raw:
                    status = "draft"
                    _grandfather(conn, import_run, gid, "status-default", None, "draft")
                else:
                    status, normalized = _normalize_status(status_raw)
                    if normalized:
                        _grandfather(conn, import_run, gid, "status-enum", status_raw, status)

                description = fv("Description")
                if not (description or "").strip():
                    description = "(imported without a Description; legacy block omitted it)"
                    _grandfather(conn, import_run, gid, "description-default", None, description)

                raw_target = fv("Target Date")
                target_date = None
                if raw_target is not None and raw_target.strip():
                    if valid_date(raw_target.strip()):
                        target_date = raw_target.strip()
                    else:
                        _grandfather(conn, import_run, gid, "target-date-invalid", raw_target, None)
                        block["extras"].append((block["line"], "Target Date: %s" % raw_target))

                gh_raw = fv("GH_URL")
                gh_release_url = None
                if gh_raw and gh_raw.strip():
                    m = URL_EXTRACT_RE.search(gh_raw)
                    if m:
                        gh_release_url = m.group(0)
                        if gh_release_url != gh_raw.strip():
                            _grandfather(conn, import_run, gid, "gh-url-normalized", gh_raw,
                                         gh_release_url)
                    else:
                        _grandfather(conn, import_run, gid, "gh-url-unparsed", gh_raw, None)

                qa = {}
                for label, column in (("Front-door reviewed", "front_door_reviewed"),
                                      ("Shakedown reviewed", "shakedown_reviewed"),
                                      ("License file", "license_file")):
                    val = fv(label)
                    if val in ("Yes", "No"):
                        qa[column] = val
                    elif val and val.strip():
                        _grandfather(conn, import_run, gid, "qa-invalid",
                                     "%s: %s" % (label, val), None)

                shipped_date = None
                for ln, text in sorted(block["extras"], key=lambda e: e[0]):
                    if text.startswith("Shipped:"):
                        m = re.match(r"(\d{4}-\d{2}-\d{2})", text[len("Shipped:"):].strip())
                        if m and valid_date(m.group(1)):
                            shipped_date = m.group(1)
                            _grandfather(conn, import_run, gid, "shipped-prose-extracted",
                                         text, shipped_date)
                        else:
                            _grandfather(conn, import_run, gid, "shipped-unparsed", text, None)
                        break

                for ln, text in block["extras"]:
                    if text.startswith("Manifest-Members:"):
                        _grandfather(conn, import_run, gid, "manifest-bare-numbers", text, None)

                tracking_raw = fv("Tracking Issue")
                if tracking_raw and GH_ISSUE_URL_RE.match(tracking_raw.strip()):
                    ref = issue_ref_for_token(conn, tracking_raw.strip())
                else:
                    # SOP 1 postdates every legacy block: import — and ONLY import — may create
                    # MIG-XXXXXX placeholders, each recorded here (r2 review finding).
                    mig = "MIG-" + uuid.uuid4().hex[:6].upper()
                    ref = issue_ref_for_token(conn, mig, allow_mig=True)
                    _grandfather(conn, import_run, gid, "tracking-issue-missing", tracking_raw,
                                 mig)

                codename = fv("Codename")
                exit_criterion = fv("Exit criterion")
                milestone = fv("Milestone")

                # GH-28 thresholds on legacy rows are grandfathered (tolerated + tracked), not
                # warned-and-written: the debt IS the record.
                if sentence_count(description) > 4:
                    _grandfather(conn, import_run, gid, "description-length",
                                 description[:80] + ("..." if len(description) > 80 else ""), None)
                if exit_criterion and len(exit_criterion) > 1000:
                    _grandfather(conn, import_run, gid, "exit-criterion-length",
                                 "%d chars" % len(exit_criterion), None)
                if _has_column(conn, "releases", "updated_at"):
                    conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                                 target_date, shipped_date, description, exit_criterion,
                                 tracking_ref_id, marathon_id, gh_release_url, milestone,
                                 front_door_reviewed, shakedown_reviewed, license_file, updated_at)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
                                 (gid, repo["id"], version, codename, status, target_date,
                                  shipped_date, description, exit_criterion, ref["id"],
                                  gh_release_url, milestone, qa.get("front_door_reviewed"),
                                  qa.get("shakedown_reviewed"), qa.get("license_file"), now))
                else:
                    conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                                 target_date, shipped_date, description, exit_criterion,
                                 tracking_ref_id, marathon_id, gh_release_url, milestone,
                                 front_door_reviewed, shakedown_reviewed, license_file)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)""",
                                 (gid, repo["id"], version, codename, status, target_date,
                                  shipped_date, description, exit_criterion, ref["id"],
                                  gh_release_url, milestone, qa.get("front_door_reviewed"),
                                  qa.get("shakedown_reviewed"), qa.get("license_file")))
                rel_id = conn.execute("SELECT id FROM releases WHERE global_id = ?",
                                      (gid,)).fetchone()["id"]
                for ln, text in sorted(block["extras"], key=lambda e: e[0]):
                    if _has_column(conn, "legacy_lines", "updated_at"):
                        conn.execute("""INSERT INTO legacy_lines(release_id, position, content,
                                     disposition, updated_at) VALUES (?, ?, ?, NULL, ?)""",
                                     (rel_id, ln, text, now))
                    else:
                        conn.execute("""INSERT INTO legacy_lines(release_id, position, content,
                                     disposition) VALUES (?, ?, ?, NULL)""", (rel_id, ln, text))

        txn = perform_write(root, conn, "import", None, mutate)
        gf = conn.execute("SELECT COUNT(*) c FROM grandfather_entries").fetchone()["c"]
        ll = conn.execute("SELECT COUNT(*) c FROM legacy_lines").fetchone()["c"]
        dl = conn.execute("SELECT COUNT(*) c FROM doc_lines").fetchone()["c"]
        print("imported %d block(s) from %s (txn %s): %d doc_lines, %d legacy_lines, "
              "%d grandfather_entries pending disposition"
              % (len(blocks), ledger, txn[:12], dl, ll, gf))
    finally:
        conn.close()


def cmd_add(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        mode = enforcement_mode(conn)
        validate_release_fields(conn, mode, version=args.version, status=args.status,
                                target_date=args.target_date, shipped_date=args.shipped_date,
                                description=args.description, exit_criterion=args.exit_criterion)
        gid = new_gid("rel-")

        def mutate(conn):
            ref = issue_ref_for_token(conn, args.tracking_issue)
            marathon_id = None
            if args.marathon:
                row = conn.execute("SELECT id FROM marathons WHERE global_id = ?",
                                   (args.marathon,)).fetchone()
                if not row:
                    refuse("unknown-gid", "no marathon with global id %r" % args.marathon)
                marathon_id = row["id"]
            if _has_column(conn, "releases", "updated_at"):
                conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                             target_date, shipped_date, description, exit_criterion, tracking_ref_id,
                             marathon_id, gh_release_url, milestone, front_door_reviewed,
                             shakedown_reviewed, license_file, updated_at)
                             VALUES (?, (SELECT id FROM repos ORDER BY id LIMIT 1), ?, ?, ?, ?, ?, ?, ?,
                                     ?, ?, ?, ?, ?, ?, ?, ?)""",
                             (gid, args.version, args.codename, args.status, args.target_date,
                              args.shipped_date, args.description, args.exit_criterion, ref["id"],
                              marathon_id, args.gh_release_url, args.milestone,
                              _qa(args.front_door), _qa(args.shakedown), _qa(args.license), now_iso()))
            else:
                conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                             target_date, shipped_date, description, exit_criterion, tracking_ref_id,
                             marathon_id, gh_release_url, milestone, front_door_reviewed,
                             shakedown_reviewed, license_file)
                             VALUES (?, (SELECT id FROM repos ORDER BY id LIMIT 1), ?, ?, ?, ?, ?, ?, ?,
                                     ?, ?, ?, ?, ?, ?, ?)""",
                             (gid, args.version, args.codename, args.status, args.target_date,
                              args.shipped_date, args.description, args.exit_criterion, ref["id"],
                              marathon_id, args.gh_release_url, args.milestone,
                              _qa(args.front_door), _qa(args.shakedown), _qa(args.license)))
            print("added release %s (version %s, status %s)" % (gid, args.version, args.status))

        perform_write(root, conn, "add", gid, mutate)
    finally:
        conn.close()


def cmd_update(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        row = find_release(conn, args.gid)
        mode = enforcement_mode(conn)
        # GH-222: `--tracking-issue <N|URL>` re-points the tracking ref (validated pre-write,
        # applied inside the perform_write transaction so the dump/receipt chain stays atomic).
        new_tracking_url = None
        if args.tracking_issue is not None:
            new_tracking_url = tracking_token_to_url(conn, root, args.tracking_issue)
        eff_version = args.version if args.version is not None else row["version"]
        validate_release_fields(conn, mode, version=eff_version,
                                status=args.status, target_date=args.target_date,
                                shipped_date=args.shipped_date, description=args.description,
                                exit_criterion=args.exit_criterion, editing_gid=args.gid)

        def mutate(conn):
            tracking_ref_id = row["tracking_ref_id"]
            if new_tracking_url is not None:
                ref = issue_ref_for_token(conn, new_tracking_url)
                tracking_ref_id = ref["id"]
            upd_clause = ""
            extra_params = ()
            if _has_column(conn, "releases", "updated_at"):
                upd_clause = ", updated_at=?"
                extra_params = (now_iso(),)
            conn.execute("""UPDATE releases SET version=?, codename=?, status=?, target_date=?,
                         shipped_date=?, description=?, exit_criterion=?, tracking_ref_id=?,
                         gh_release_url=?, milestone=?, front_door_reviewed=?, shakedown_reviewed=?,
                         license_file=?""" + upd_clause + " WHERE global_id=?",
                         (eff_version,
                          args.codename if args.codename is not None else row["codename"],
                          args.status if args.status is not None else row["status"],
                          args.target_date if args.target_date is not None else row["target_date"],
                          args.shipped_date if args.shipped_date is not None else row["shipped_date"],
                          args.description if args.description is not None else row["description"],
                          args.exit_criterion if args.exit_criterion is not None
                          else row["exit_criterion"],
                          tracking_ref_id,
                          args.gh_release_url if args.gh_release_url is not None
                          else row["gh_release_url"],
                          args.milestone if args.milestone is not None else row["milestone"],
                          _qa(args.front_door) if args.front_door is not None
                          else row["front_door_reviewed"],
                          _qa(args.shakedown) if args.shakedown is not None
                          else row["shakedown_reviewed"],
                          _qa(args.license) if args.license is not None
                          else row["license_file"]) + extra_params + (args.gid,))
            # GH-111 baseline auto-capture, in the SAME writer-locked transaction as the status
            # flip — a dial-in landing between the two would pin a manifest state that never
            # existed. Only on draft -> active, only when nothing is captured yet: an
            # active -> draft -> active round trip is a SILENT no-op here (the explicit
            # `releases baseline` verb is the one that refuses), because a legitimate status
            # round trip must not fail while an accidental second capture stays impossible.
            new_status = args.status if args.status is not None else row["status"]
            if (row["status"] == "draft" and new_status == "active"
                    and _col(row, "baseline_count") is None
                    and _has_column(conn, "releases", "baseline_count")):
                count = _capture_baseline(conn, row["id"], "observed")
                if count:
                    print("baseline for %s captured at %d (observed)" % (args.gid, count))
            if new_tracking_url is not None:
                print("re-pointed tracking issue -> %s (old ref row kept its identity)"
                      % new_tracking_url)
            print("updated release %s" % args.gid)

        perform_write(root, conn, "update", args.gid, mutate)
    finally:
        conn.close()


def _live_manifest_count(conn, release_id):
    """The commitment denominator: dialed-in plus shipped. Cut rows are history, not scope —
    counting them contradicts the repo's own prose that a cut REDUCES the manifest."""
    return conn.execute("""SELECT COUNT(*) FROM manifest_items
                            WHERE release_id = ? AND state IN ('dialed_in','shipped')""",
                        (release_id,)).fetchone()[0]


def _capture_baseline(conn, release_id, source):
    """Write the kickoff snapshot. Returns the count, or 0 when the manifest is empty.

    An empty manifest yields NO baseline rather than a baseline of zero. Releases here are
    created as a row first and dialed in afterwards, so a naive snapshot-on-activate would give
    most releases a 0 and then report every real commitment as scope growth — the metric would
    lie in the common case. Baseline-less is the honest state, and `releases baseline` fills it
    in later."""
    count = _live_manifest_count(conn, release_id)
    if not count:
        return 0
    now = now_iso()
    if _has_column(conn, "releases", "updated_at"):
        conn.execute("""UPDATE releases SET baseline_count = ?, baseline_at = ?, baseline_source = ?,
                        updated_at = ? WHERE id = ?""", (count, now, source, now, release_id))
    else:
        conn.execute("""UPDATE releases SET baseline_count = ?, baseline_at = ?, baseline_source = ?
                        WHERE id = ?""", (count, now, source, release_id))
    return count


def cmd_baseline(args):
    """Capture a release's baseline explicitly — the path for a release that was activated with
    an empty manifest (`releases add --status active` has no draft->active transition to hook)."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        row = find_release(conn, args.gid)
        if not _has_column(conn, "releases", "baseline_count"):
            refuse("schema-behind",
                   "this ledger predates the baseline columns; run `releases migrate` first")
        if row["baseline_count"] is not None:
            refuse("baseline-already-set",
                   "release %s already has a baseline of %d (%s, taken %s). A baseline is "
                   "write-once: overwriting it would erase the very thing it measures."
                   % (args.gid, row["baseline_count"], row["baseline_source"], row["baseline_at"]))
        if not _live_manifest_count(conn, row["id"]):
            refuse("baseline-empty-manifest",
                   "release %s has no dialed-in or shipped members; a baseline of zero would "
                   "report every later commitment as scope growth. Dial the work in first."
                   % args.gid)

        def mutate(conn):
            count = _capture_baseline(conn, row["id"], "observed")
            print("baseline for %s captured at %d (observed)" % (args.gid, count))

        perform_write(root, conn, "baseline", args.gid, mutate)
    finally:
        conn.close()


def cmd_ship(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        row = find_release(conn, args.gid)
        evidence = (args.evidence or "").strip()
        if not evidence:
            refuse("ship-needs-evidence",
                   "shipping requires --evidence citing the exit-criterion run (structural, "
                   "both modes)")
        if row["status"] not in ("draft", "active"):
            refuse("transition",
                   "cannot ship a release in status %r (legal: draft|active -> shipped); "
                   "transition legality is CLI-enforced" % row["status"])
        when = args.date or now_iso()[:10]
        if not valid_date(when):
            refuse("date-shape", "--date %r must be a valid YYYY-MM-DD calendar date" % when)

        def mutate(conn):
            if _has_column(conn, "releases", "updated_at"):
                conn.execute("""UPDATE releases SET status='shipped', shipped_date=?, updated_at=?
                                WHERE global_id=?""",
                             (when, now_iso(), args.gid))
            else:
                conn.execute("UPDATE releases SET status='shipped', shipped_date=? WHERE global_id=?",
                             (when, args.gid))
            # The evidence citation rides in the append-only audit trail (the schema has no
            # evidence column by design): a ship-evidence receipt in the SAME transaction as the
            # status flip. check()'s chain rule skips op='ship-evidence' rows.
            conn.execute("""INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id,
                         state_digest_before, state_digest_after)
                         VALUES ('ship-evidence', ?, ?, ?, ?, '', '')""",
                         (args.gid, "evidence: %s" % evidence, new_txn_id(), session_id()))
            print("shipped %s on %s (evidence recorded in the op_receipts audit trail)"
                  % (args.gid, when))

        perform_write(root, conn, "ship", args.gid, mutate)
    finally:
        conn.close()


def cmd_manifest_add(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        rel = find_release(conn, args.gid)
        gid = new_gid("mfi-")

        def mutate(conn):
            ref = issue_ref_for_token(conn, args.issue)
            if conn.execute("""SELECT 1 FROM manifest_items
                              WHERE release_id=? AND issue_ref_id=? AND state='dialed_in'""",
                            (rel["id"], ref["id"])).fetchone():
                refuse("manifest-duplicate",
                       "issue is already dialed into this release (refused in both modes). A cut "
                       "row for the same issue does NOT block a redial — only a live one does.")
            # GH-111 EXCLUSIVITY: a task is dialed into exactly one release at a time. This REVERSES
            # the former `shared-manifest-issue` warning, which allowed one issue to sit on several
            # releases at once and called handoffs legitimate. Handoffs are still legitimate — they
            # are now expressed as `cut --reason "handed off to X"` then `dial-in` on the target,
            # which records the move instead of leaving the task silently on both ledgers.
            held = conn.execute("""SELECT r.global_id, r.codename FROM manifest_items mi
                                   JOIN releases r ON r.id = mi.release_id
                                   WHERE mi.issue_ref_id = ? AND mi.release_id != ?
                                     AND mi.state = 'dialed_in'""",
                                (ref["id"], rel["id"])).fetchall()
            if held:
                refuse("dialed-in-elsewhere",
                       "issue is already dialed into %s — a task belongs to ONE release at a time. "
                       "To hand it over: `manifest cut --gid %s <issue> --reason \"handed off\"` "
                       "then dial it in here."
                       % (", ".join("%s (%s)" % (h["global_id"], h["codename"] or "?")
                                    for h in held), held[0]["global_id"]))
            marathon_id = None
            if getattr(args, "marathon", None):
                mar = conn.execute("SELECT id FROM marathons WHERE global_id = ?",
                                   (args.marathon,)).fetchone()
                if not mar:
                    refuse("unknown-marathon", "no marathon with gid %r" % args.marathon)
                # The two marathon links are independent FKs, so nothing in the schema stops an item
                # on release B carrying release A's marathon. That would let the viewer assert a
                # membership the data never claimed (GH-109). CLI-enforced, since SQLite cannot
                # express a cross-table CHECK.
                if rel["marathon_id"] != mar["id"]:
                    refuse("marathon-not-this-release",
                           "marathon %s does not belong to release %s; an item's marathon must be "
                           "its own release's marathon" % (args.marathon, args.gid))
                marathon_id = mar["id"]
            if _has_column(conn, "manifest_items", "updated_at"):
                conn.execute("""INSERT INTO manifest_items(global_id, release_id, issue_ref_id, state,
                                                           dialed_in_at, dial_reason, marathon_id, updated_at)
                             VALUES (?, ?, ?, 'dialed_in', ?, ?, ?, ?)""",
                             (gid, rel["id"], ref["id"], now_iso(),
                              getattr(args, "reason", None), marathon_id, now_iso()))
            else:
                conn.execute("""INSERT INTO manifest_items(global_id, release_id, issue_ref_id, state,
                                                           dialed_in_at, dial_reason, marathon_id)
                             VALUES (?, ?, ?, 'dialed_in', ?, ?, ?)""",
                             (gid, rel["id"], ref["id"], now_iso(),
                              getattr(args, "reason", None), marathon_id))
            print("manifest item %s dialed into %s (state=dialed_in)" % (gid, args.gid))

        perform_write(root, conn, "manifest-add", gid, mutate)
    finally:
        conn.close()


def cmd_manifest_ship(args):
    """GH-110/GH-111: move a dialed-in member to shipped.

    Before this verb, `shipped` was a state the schema allowed and no code path ever wrote, so a
    manifest member could never be marked done and mid-release progress was unreportable. The
    event table's `reason` is NOT NULL, so shipping carries `--evidence` for the same reason
    `releases ship` does: a claim that work landed should cite what landed.
    """
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        rel = find_release(conn, args.gid)
        evidence = (args.evidence or "").strip()
        if not evidence:
            refuse("ship-needs-evidence",
                   "marking a manifest item shipped without evidence is refused (structural, "
                   "both modes) — cite the commit, PR, or test receipt")
        kind, value = check_tracking_token(args.issue)

        def mutate(conn):
            column = "url" if kind == "url" else "temp_id"
            ref = conn.execute("SELECT * FROM issue_refs WHERE %s = ?" % column,
                               (value,)).fetchone()
            if not ref:
                refuse("unknown-issue", "no issue_refs row for %r" % value)
            item = _live_manifest_item(conn, rel, ref, value, args.gid, "shipped")
            if _has_column(conn, "manifest_items", "updated_at"):
                conn.execute("UPDATE manifest_items SET state='shipped', updated_at=? WHERE id=?",
                             (now_iso(), item["id"]))
            else:
                conn.execute("UPDATE manifest_items SET state='shipped' WHERE id=?", (item["id"],))
            # State and event land in ONE transaction — the coupling the digest chain checks.
            conn.execute("""INSERT INTO manifest_state_events(item_id, from_state, to_state, at,
                         reason) VALUES (?, ?, 'shipped', ?, ?)""",
                         (item["id"], item["state"], now_iso(), evidence))
            print("manifest item %s shipped (%s -> shipped); evidence recorded"
                  % (item["global_id"], item["state"]))

        perform_write(root, conn, "manifest-ship", args.gid, mutate)
    finally:
        conn.close()


def cmd_manifest_marathon(args):
    """Link an ALREADY dialed-in item to its release's marathon.

    Migration 004 leaves `marathon_id` NULL on every migrated row, deliberately: the only fact
    available at migration time is "this release has a marathon", and inferring membership from
    that is precisely the defect #109 names. So membership on pre-existing manifests is recorded
    the same way a baseline is — witnessed by an operator, one item at a time — rather than
    guessed by a migration and then indistinguishable from the real thing.
    """
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        rel = find_release(conn, args.gid)
        kind, value = check_tracking_token(args.issue)

        def mutate(conn):
            column = "url" if kind == "url" else "temp_id"
            ref = conn.execute("SELECT * FROM issue_refs WHERE %s = ?" % column,
                               (value,)).fetchone()
            if not ref:
                refuse("unknown-issue", "no issue_refs row for %r" % value)
            item = conn.execute("""SELECT * FROM manifest_items
                                  WHERE release_id=? AND issue_ref_id=? AND state='dialed_in'""",
                                (rel["id"], ref["id"])).fetchone()
            if not item:
                refuse("unknown-issue",
                       "issue %r is not dialed into release %s" % (value, args.gid))
            mar = conn.execute("SELECT id FROM marathons WHERE global_id = ?",
                               (args.marathon,)).fetchone()
            if not mar:
                refuse("unknown-marathon", "no marathon with gid %r" % args.marathon)
            if rel["marathon_id"] != mar["id"]:
                refuse("marathon-not-this-release",
                       "marathon %s does not belong to release %s; an item's marathon must be "
                       "its own release's marathon" % (args.marathon, args.gid))
            if item["marathon_id"] is not None and item["marathon_id"] != mar["id"]:
                refuse("marathon-link-permanent",
                       "manifest item %s already belongs to another marathon; marathon links are "
                       "historical and permanent" % item["global_id"])
            if _has_column(conn, "manifest_items", "updated_at"):
                conn.execute("UPDATE manifest_items SET marathon_id=?, updated_at=? WHERE id=?",
                             (mar["id"], now_iso(), item["id"]))
            else:
                conn.execute("UPDATE manifest_items SET marathon_id=? WHERE id=?",
                             (mar["id"], item["id"]))
            print("manifest item %s linked to marathon %s" % (item["global_id"], args.marathon))

        perform_write(root, conn, "manifest-marathon", args.gid, mutate)
    finally:
        conn.close()


def _live_manifest_item(conn, rel, ref, token, gid_arg, target_state):
    """Select the ONE live (dialed_in) manifest row for this (release, issue), or refuse.

    GH-111: dropping UNIQUE(release_id, issue_ref_id) means a (release, issue) pair can now
    hold several rows — a cut row plus a later redial. The old lookup had no state predicate
    and was correct ONLY while that UNIQUE guaranteed a single row; left as-is it could pick
    the historical cut row and refuse "cut is terminal" while a live row sat beside it.
    """
    item = conn.execute("""SELECT * FROM manifest_items
                           WHERE release_id=? AND issue_ref_id=? AND state='dialed_in'""",
                        (rel["id"], ref["id"])).fetchone()
    if item:
        if (item["state"], target_state) not in LEGAL_ITEM_TRANSITIONS:
            refuse("transition",
                   "cannot move an item from %r to %r (legality is CLI-enforced)"
                   % (item["state"], target_state))
        return item
    # No live row. Distinguish "never here" from "here, but already terminal" — the second is a
    # transition error, and saying so is how the operator learns the item's actual state.
    prior = conn.execute("""SELECT state FROM manifest_items
                            WHERE release_id=? AND issue_ref_id=?
                            ORDER BY id DESC LIMIT 1""",
                         (rel["id"], ref["id"])).fetchone()
    if prior:
        refuse("transition",
               "issue %r is in release %s at state %r, not dialed_in; %s and cut are terminal for "
               "that row (re-admitting is a new dial-in)" % (token, gid_arg, prior["state"],
                                                             prior["state"]))
    refuse("unknown-issue", "issue %r is not in release %s's manifest" % (token, gid_arg))


def cmd_manifest_cut(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        rel = find_release(conn, args.gid)
        reason = (args.reason or "").strip()
        if not reason:
            refuse("cut-needs-reason",
                   "a manifest cut without a reason is refused (structural, both modes)")
        kind, value = check_tracking_token(args.issue)

        def mutate(conn):
            if kind == "url":
                ref = conn.execute("SELECT * FROM issue_refs WHERE url = ?", (value,)).fetchone()
            else:
                ref = conn.execute("SELECT * FROM issue_refs WHERE temp_id = ?",
                                   (value,)).fetchone()
            if not ref:
                refuse("unknown-issue", "no issue_refs row for %r" % value)
            item = _live_manifest_item(conn, rel, ref, value, args.gid, "cut")
            if _has_column(conn, "manifest_items", "updated_at"):
                conn.execute("UPDATE manifest_items SET state='cut', updated_at=? WHERE id=?",
                             (now_iso(), item["id"]))
            else:
                conn.execute("UPDATE manifest_items SET state='cut' WHERE id=?", (item["id"],))
            # item state and its event land in ONE transaction (PRD: the coupling is
            # CLI-enforced; a direct writer that skips the event is caught by the digest chain)
            conn.execute("""INSERT INTO manifest_state_events(item_id, from_state, to_state, at,
                         reason) VALUES (?, ?, 'cut', ?, ?)""",
                         (item["id"], item["state"], now_iso(), reason))
            print("manifest item %s cut (%s -> cut); re-scope event appended"
                  % (item["global_id"], item["state"]))

        perform_write(root, conn, "manifest-cut", args.gid, mutate)
    finally:
        conn.close()



def cmd_manifest_unship(args):
    """GH-351: retract a shipped manifest item back to dialed_in.

    `shipped` used to be terminal with no way out. `manifest cut` refuses on a shipped row, and the
    refusal pointed at re-dialing — which retracts nothing and adds a SECOND row, leaving the
    manifest asserting that one issue both shipped and is pending. AGENTS.md forbids hand-editing
    releases.db, so an operator had no supported way to correct a false ship at all.

    The correction is a real state transition with an auditable event, not a silent UPDATE: the
    retraction lands in manifest_state_events beside the ship it reverses, so the ledger records
    that the claim was withdrawn rather than pretending it was never made.
    """
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        rel = find_release(conn, args.gid)
        reason = (args.reason or "").strip()
        if not reason:
            refuse("unship-needs-reason",
                   "retracting a shipped manifest item without a reason is refused (structural, "
                   "both modes)")
        kind, value = check_tracking_token(args.issue)

        def mutate(conn):
            column = "url" if kind == "url" else "temp_id"
            ref = conn.execute("SELECT * FROM issue_refs WHERE %s = ?" % column,
                               (value,)).fetchone()
            if not ref:
                refuse("unknown-issue", "no issue_refs row for %r" % value)

            item = conn.execute("""SELECT * FROM manifest_items
                                   WHERE release_id=? AND issue_ref_id=? AND state='shipped'
                                   ORDER BY id DESC LIMIT 1""",
                                (rel["id"], ref["id"])).fetchone()
            if not item:
                prior = conn.execute("""SELECT state FROM manifest_items
                                        WHERE release_id=? AND issue_ref_id=?
                                        ORDER BY id DESC LIMIT 1""",
                                     (rel["id"], ref["id"])).fetchone()
                if prior:
                    refuse("transition",
                           "issue %r is in release %s at state %r, not shipped"
                           % (value, args.gid, prior["state"]))
                refuse("unknown-issue",
                       "issue %r is not in release %s's manifest" % (value, args.gid))

            # Un-shipping must not manufacture the very contradiction it exists to remove: if a live
            # row already sits beside the shipped one (GH-111 dropped UNIQUE(release_id,
            # issue_ref_id), so it can), retracting would leave TWO dialed_in rows.
            existing = conn.execute("""SELECT 1 FROM manifest_items
                                       WHERE release_id=? AND issue_ref_id=? AND state='dialed_in'
                                         AND id != ?""",
                                    (rel["id"], ref["id"], item["id"])).fetchone()
            if existing:
                refuse("manifest-duplicate",
                       "issue is already dialed into this release as dialed_in; unship would "
                       "create a duplicate live row")

            held = conn.execute("""SELECT r.global_id, r.codename FROM manifest_items mi
                                   JOIN releases r ON r.id = mi.release_id
                                   WHERE mi.issue_ref_id = ? AND mi.release_id != ?
                                     AND mi.state = 'dialed_in'""",
                                (ref["id"], rel["id"])).fetchall()
            if held:
                refuse("dialed-in-elsewhere",
                       "issue is already dialed into %s — a task belongs to ONE release at a time."
                       % (", ".join("%s (%s)" % (h["global_id"], h["codename"] or "?")
                                    for h in held)))

            if (item["state"], "dialed_in") not in LEGAL_ITEM_TRANSITIONS:
                refuse("transition",
                       "cannot move an item from %r to 'dialed_in' (legality is CLI-enforced)"
                       % item["state"])

            if _has_column(conn, "manifest_items", "updated_at"):
                conn.execute("UPDATE manifest_items SET state='dialed_in', updated_at=? WHERE id=?",
                             (now_iso(), item["id"]))
            else:
                conn.execute("UPDATE manifest_items SET state='dialed_in' WHERE id=?",
                             (item["id"],))
            # item state and its event land in ONE transaction, matching ship/cut: a direct writer
            # that skips the event is caught by the digest chain.
            conn.execute("""INSERT INTO manifest_state_events(item_id, from_state, to_state, at,
                            reason) VALUES (?, 'shipped', 'dialed_in', ?, ?)""",
                         (item["id"], now_iso(), reason))
            print("manifest item %s un-shipped (shipped -> dialed_in); retraction event appended"
                  % item["global_id"])

        perform_write(root, conn, "manifest-unship", args.gid, mutate)
    finally:
        conn.close()

def cmd_marathon_add(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gid = new_gid("mar-")

        def mutate(conn):
            ref = issue_ref_for_token(conn, args.tracking_issue)
            repo_id = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()["id"]
            if _has_column(conn, "marathons", "updated_at"):
                conn.execute("""INSERT INTO marathons(global_id, repo_id, tracking_ref_id, status,
                             created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)""",
                             (gid, repo_id, ref["id"], args.status, now_iso(), now_iso()))
            else:
                conn.execute("""INSERT INTO marathons(global_id, repo_id, tracking_ref_id, status,
                             created_at) VALUES (?, ?, ?, ?, ?)""",
                             (gid, repo_id, ref["id"], args.status, now_iso()))
            print("marathon %s added (status %s)" % (gid, args.status))

        perform_write(root, conn, "marathon-add", gid, mutate)
    finally:
        conn.close()


def cmd_marathon_list(args):
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        for row in conn.execute("""SELECT m.global_id, m.status, m.created_at, t.url, t.temp_id
                                   FROM marathons m JOIN issue_refs t ON t.id = m.tracking_ref_id
                                   ORDER BY m.id"""):
            print("%s  %-9s  %s  %s" % (row["global_id"], row["status"], row["created_at"],
                                        row["url"] or row["temp_id"]))
    finally:
        conn.close()


def _repo_label(path):
    return os.path.basename(os.path.normpath(path))


def _aggregate_all_repos(root, conn):
    """v1 aggregation surface: this DB plus RELEASES_APP_EXTRA_DBS (colon-separated). The
    Phase-3 cockpit card reads the hq registry instead; until then this is the testable reader.
    Duplicate global IDs across DBs fail the aggregation LOUDLY, never merge silently (PRD)."""
    extra = [p for p in os.environ.get("RELEASES_APP_EXTRA_DBS", "").split(":") if p]
    seen = {}
    for r in conn.execute("SELECT global_id FROM releases"):
        seen.setdefault(r["global_id"], set()).add(_repo_label(root))
    for db_path in extra:
        if not os.path.exists(db_path):
            refuse("extra-db-missing", "RELEASES_APP_EXTRA_DBS entry %s does not exist" % db_path)
        econn = connect(db_path)
        try:
            for r in econn.execute("SELECT global_id FROM releases"):
                seen.setdefault(r["global_id"], set()).add(_repo_label(os.path.dirname(db_path)))
        finally:
            econn.close()
    dups = {g: locs for g, locs in seen.items() if len(locs) > 1}
    # cross-repo codename duplication warns, never refuses — the survey's "Silverlining in two
    # repos" case. Emitted before the duplicate-GID exit so a failing aggregation still carries
    # its warnings.
    names = {}
    for db_path in [None] + extra:
        c = conn if db_path is None else connect(db_path)
        try:
            for r in c.execute("SELECT codename FROM releases WHERE codename IS NOT NULL"):
                names.setdefault((r["codename"] or "").strip().lower(), set()).add(
                    _repo_label(root if db_path is None else os.path.dirname(db_path)))
        finally:
            if db_path is not None:
                c.close()
    for name, locs in sorted(names.items()):
        if len(locs) > 1:
            warn("cross-repo-codename",
                 "codename %r appears in %s (warn, never refuse — the survey's copy-paste case)"
                 % (name, ", ".join(sorted(locs))))
    if dups:
        for gid, locs in sorted(dups.items()):
            print("FAIL: rule=duplicate-gid: %s appears in %s" % (gid, ", ".join(sorted(locs))))
        sys.exit(EXIT_CHECK_FAILED)
    print("aggregated %d release gid(s) across %d repo DB(s); no duplicate global IDs"
          % (len(seen), 1 + len(extra)))


def cmd_list(args):
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        rows = conn.execute("""SELECT rel.global_id, rel.version, rel.codename, rel.status,
                                      rel.target_date, rel.shipped_date, t.url, t.temp_id,
                                      (SELECT COUNT(*) FROM manifest_items mi
                                       WHERE mi.release_id = rel.id) AS items
                               FROM releases rel JOIN issue_refs t ON t.id = rel.tracking_ref_id
                               ORDER BY rel.id""").fetchall()
        if args.status:
            rows = [r for r in rows if r["status"] == args.status]
        for r in rows:
            print("%s  %-8s %-12s %-8s target=%s shipped=%s tracking=%s items=%d" % (
                r["global_id"], r["version"] or "-", r["codename"] or "-", r["status"],
                r["target_date"] or "-", r["shipped_date"] or "-", r["url"] or r["temp_id"],
                r["items"]))
        if args.all_repos:
            _aggregate_all_repos(root, conn)
    finally:
        conn.close()


def _resolve_one(conn, gid=None, version=None):
    """Reader-side lookup by GID or version. Readers accept either so an agent that only knows
    '0.6.0' does not need a separate lookup round-trip first."""
    if bool(gid) == bool(version):
        refuse("selector", "pass exactly one of --gid or --version")
    if gid:
        return find_release(conn, gid)
    row = conn.execute("SELECT * FROM releases WHERE version = ?", (version,)).fetchone()
    if row is None:
        refuse("unknown-version", "no release with version %r in this repo" % version)
    return row


SHOW_ELIDE = 240   # imported legacy prose runs to thousands of chars; orientation needs the head


def _elide(text, full):
    """Long values are elided by DEFAULT: this reader exists for fast orientation, and an
    imported description can run past 3,000 characters. --full prints verbatim. The elision
    always states the true length so a reader knows what it is not seeing."""
    text = str(text)
    if full or len(text) <= SHOW_ELIDE:
        return text
    return "%s… (%d chars total; --full to print it all)" % (text[:SHOW_ELIDE], len(text))


def cmd_show(args):
    """Full record for ONE release — the detail reader `list` deliberately does not provide."""
    root = resolve_root(args.root)
    full = getattr(args, "full", False)
    conn = connect(artifact_paths(root)["db"])
    try:
        rel = _resolve_one(conn, args.gid, args.version)
        ref = conn.execute("SELECT url, temp_id FROM issue_refs WHERE id = ?",
                           (rel["tracking_ref_id"],)).fetchone()
        print("GID:           %s" % rel["global_id"])
        print("Release:       %s" % (rel["version"] or "(unversioned)"))
        print("Status:        %s" % rel["status"])
        for label, key in (("Codename", "codename"), ("Target Date", "target_date"),
                           ("Shipped", "shipped_date"), ("Milestone", "milestone"),
                           ("GH_URL", "gh_release_url"), ("Description", "description"),
                           ("Exit criterion", "exit_criterion"),
                           ("Front-door reviewed", "front_door_reviewed"),
                           ("Shakedown reviewed", "shakedown_reviewed"),
                           ("License file", "license_file")):
            if rel[key]:
                print("%-14s %s" % (label + ":", _elide(rel[key], full)))
        print("%-14s %s" % ("Tracking:", (ref["url"] or ref["temp_id"]) if ref else "-"))

        items = conn.execute("""SELECT t.url, t.temp_id, mi.state FROM manifest_items mi
                                JOIN issue_refs t ON t.id = mi.issue_ref_id
                                WHERE mi.release_id = ? ORDER BY mi.id""",
                             (rel["id"],)).fetchall()
        print("Manifest:      %d item(s)" % len(items))
        for it in items:
            print("  - %s [%s]" % (it["url"] or it["temp_id"], it["state"]))

        legacy = conn.execute("""SELECT content FROM legacy_lines WHERE release_id = ?
                                 ORDER BY position""", (rel["id"],)).fetchall()
        if legacy:
            print("Legacy lines:  %d (imported verbatim, pending disposition)" % len(legacy))
            for ll in legacy:
                print("  | %s" % _elide(ll["content"], full))

        pending = conn.execute("""SELECT rule, COUNT(*) AS n FROM grandfather_entries
                                  WHERE release_gid = ? AND disposition IS NULL
                                  GROUP BY rule""", (rel["global_id"],)).fetchall()
        if pending:
            print("Grandfathered: %s"
                  % ", ".join("%s x%d" % (g["rule"], g["n"]) for g in pending))
    finally:
        conn.close()


def cmd_next(args):
    """The next release to work on: unshipped, earliest target date first. A release with no
    target date sorts last — undated is not urgent, it is unplanned."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        rows = conn.execute("""SELECT global_id, version, codename, status, target_date
                               FROM releases WHERE status IN ('draft', 'active')
                               ORDER BY target_date IS NULL, target_date, version""").fetchall()
        if not rows:
            print("no unshipped releases — the ledger has nothing queued")
            return
        head = rows[0]
        print("NEXT: %s %s (%s) target=%s gid=%s"
              % (head["version"] or "-", head["codename"] or "", head["status"],
                 head["target_date"] or "unplanned", head["global_id"]))
        for r in rows[1:]:
            print("then: %s %s (%s) target=%s"
                  % (r["version"] or "-", r["codename"] or "", r["status"],
                     r["target_date"] or "unplanned"))
        if args.verbose:
            print()
            cmd_show(argparse.Namespace(root=args.root, gid=head["global_id"], version=None,
                                        full=False))
    finally:
        conn.close()


def _project_field_map(payload):
    fields = {field.get("name"): field for field in payload.get("fields", [])}
    missing = [name for name in PROJECT_FIELDS if not fields.get(name, {}).get("id")]
    if missing:
        refuse("github-project-schema",
               "project is missing required field(s): %s" % ", ".join(missing))
    return fields


def _project_select_option(field, value):
    for option in field.get("options", []):
        if option.get("name") == value:
            return option.get("id")
    refuse("github-project-schema",
           "field %r is missing required option %r" % (field.get("name"), value))


def _project_edit_field(project_id, item_id, field, value, kind):
    base = ["project", "item-edit", "--id", item_id, "--project-id", project_id,
            "--field-id", field["id"]]
    if value in (None, ""):
        _gh_run(base + ["--clear"])
    elif kind == "text":
        _gh_run(base + ["--text", str(value)])
    elif kind == "date":
        _gh_run(base + ["--date", str(value)])
    else:
        _gh_run(base + ["--single-select-option-id", _project_select_option(field, value)])


def cmd_project_sync(args):
    """Project the release ledger to GitHub draft cards; DB writes are intentionally impossible."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        project = _gh_json(["project", "view", str(args.number), "--owner", args.owner,
                            "--format", "json"])
        project_id = project.get("id")
        if not project_id:
            refuse("github-project", "project view returned no project ID")
        fields = _project_field_map(_gh_json(
            ["project", "field-list", str(args.number), "--owner", args.owner,
             "--limit", "100", "--format", "json"]))
        items = _gh_json(["project", "item-list", str(args.number), "--owner", args.owner,
                          "--limit", "1000", "--format", "json"]).get("items", [])
        by_release_id = {}
        for item in items:
            release_id = _project_value(item, "Release ID")
            if release_id:
                if release_id in by_release_id:
                    refuse("github-project-duplicate-card",
                           "Release ID %s occurs in more than one Project card" % release_id)
                by_release_id[release_id] = item

        releases = _project_release_rows(conn)
        if not args.apply:
            print("DRY RUN: GitHub Project is unchanged; repeat with --apply to write cards.")

        for release in releases:
            title = "%s — %s" % (release["version"] or "Unversioned",
                                  release["codename"] or "Untitled")
            body = _project_body(release)
            existing = by_release_id.get(release["global_id"])
            action = "UPDATE" if existing else "CREATE"
            print("%s %s (%s)" % (action, title, release["global_id"]))
            if not args.apply:
                continue

            if existing:
                item_id = existing.get("id")
                if not item_id:
                    refuse("github-project-item", "existing card %s has no item ID"
                           % release["global_id"])
                content = existing.get("content") or {}
                content_id = content.get("id")
                if content.get("type") != "DraftIssue" or not content_id:
                    refuse("github-project-item",
                           "existing card %s is not an editable draft item"
                           % release["global_id"])
                _gh_run(["project", "item-edit", "--id", content_id,
                         "--title", title, "--body", body])
            else:
                created = _gh_json(["project", "item-create", str(args.number), "--owner",
                                    args.owner, "--title", title, "--body", body,
                                    "--format", "json"])
                item_id = created.get("id")
                if not item_id:
                    refuse("github-project-item", "created card %s has no item ID"
                           % release["global_id"])

            tracking = release["tracking_url"] or release["tracking_temp"]
            values = (
                ("Release ID", release["global_id"], "text"),
                ("Release status", STATUS_RENDER[release["status"]], "select"),
                ("Target date", release["target_date"], "date"),
                ("Shipped date", release["shipped_date"], "date"),
                ("Codename", release["codename"], "text"),
                ("Tracking issue", tracking, "text"),
                ("GitHub release", release["gh_release_url"], "text"),
                ("Front-door reviewed", release["front_door_reviewed"], "select"),
                ("Shakedown reviewed", release["shakedown_reviewed"], "select"),
                ("License file", release["license_file"], "select"),
            )
            for name, value, kind in values:
                _project_edit_field(project_id, item_id, fields[name], value, kind)
        print("project sync: %d release card(s) %s"
              % (len(releases), "applied" if args.apply else "planned"))
    finally:
        conn.close()


# ── GH-269: roadmap ledger (`releases roadmap sync` / `list`) ────────────────────────────────
# Ledger contract: the database is the ONLY thing humans and
# agents edit; this code only READS it and mirrors the ledger into roadmap_items. The parser is a
# twin of the marathon planner's (utils/py/_marathon_plan.py) with one deliberate difference: the
# planner recognises only its four SECTIONS and skips the rest silently, while the shadow captures
# EVERY `###` section under `## Ledger` — the shadow's job is to mirror what the file says, not to
# re-decide what the planner should see.

ROADMAP_NAME = "ROADMAP.md"
_ROADMAP_STATUS_MARKERS = ["\U0001F195", "\U0001F6A7", "\u2705", "\u23F8\uFE0F", "\U0001F7E1",
                           "\u2699\uFE0F", "\U0001F532", "\u26D4", "\U0001F52E", "\U0001F7E2",
                           "\U0001F534", "\U0001F41E"]


# ── GH-108: the one canonical rating grammar ────────────────────────────────────────────────────
# `rated N/N/N/N` — exactly four slash-separated integers 1-100, axis order fixed as
# pri/sev/appeal/effort — optionally followed by ` ovr N` (an integer 4-400 on calc's own scale).
# There is no labeled long form: the axis NAMES live in RELEASES-DB-FAQS.md (and
# PROJECT/3-COMPLETED/GH-108-RATING-SYSTEM.md), not in the entry line. Higher is better on every axis,
# effort included (it scores CHEAPNESS), so the four combine without sign-flipping.
#
# The refusal contract matters as much as the grammar: the PRESENCE of a `rated` or `ovr` token
# either parses as the full form or refuses with a named rule. A malformed shape must never read
# as "unrated" — that would silently drop an operator's prioritisation and look like they never
# scored the task.
# The TOKEN test requires a digit after the word, so ordinary prose ("a highly rated entry",
# "underrated") is not mistaken for a score — while a genuinely malformed `rated 70/40/55` still
# counts as a token and is refused rather than read as unrated.
_RATED_TOKEN_RE = re.compile(r"\brated\s+\d")
# The DUPLICATE test is deliberately NARROWER than the presence test: it counts only
# slash-bearing matches. "the rated 3rd priority item ... rated 90/90/90/90" is ONE rating
# beside prose, and refusing it as a duplicate rejects a correctly-scored entry
# (aider/qwen3.8-max QA r1, [Should] #1 — reproduced before fixing). The PRESENCE test stays
# broad on purpose: a bare `rated 70` is a truncated score, and reading it as "unrated" would
# be exactly the silent drop this contract exists to prevent. Prose shaped "rated <int> <word>"
# with no real score beside it therefore still refuses — loudly, and fixable in one edit, which
# is the trade this repo prefers over an invisible drop.
_RATED_SCORE_TOKEN_RE = re.compile(r"\brated\s+\d+/")
_RATED_RE = re.compile(r"\brated\s+(\d+)/(\d+)/(\d+)/(\d+)(?![\w/])")
# `ovr` requires a DIGIT, not merely a following token. Unbackticked prose — "the ovr wins over
# calc" — otherwise refuses an entry carrying a perfectly good rating (aider/qwen3.8-max QA r1,
# [Should] #2 — reproduced before fixing). The asymmetry with `rated` above is deliberate and is
# what makes it safe: the override is OPTIONAL, so a dropped `ovr` degrades to "no override"
# while the four axes still land, whereas a dropped `rated` loses the whole score. A real typo
# is still caught, because the SHAPE test needs the integer to end cleanly: `ovr 35O` matches
# the token and then fails the shape.
_OVR_TOKEN_RE = re.compile(r"\bovr\s+\d")
_OVR_RE = re.compile(r"\bovr\s+(\d+)(?![\w/])")
_LEGACY_CRE_RE = re.compile(r"cx/risk/eff (\d+)/(\d+)/(\d+)")

_RATING_GRAMMAR = "the grammar is `rated N/N/N/N` (pri/sev/appeal/effort, 1-100) with an " \
                  "optional ` ovr N` (4-400)"


def parse_rating(raw, title):
    """Parse the rating tokens out of one ROADMAP entry. Returns the five column values."""
    blank = dict.fromkeys(RATING_COLUMNS)
    rated_tokens = _RATED_TOKEN_RE.findall(raw)
    ovr_tokens = _OVR_TOKEN_RE.findall(raw)
    if not rated_tokens and not ovr_tokens:
        return blank
    where = "entry %r" % title[:60]

    if _LEGACY_CRE_RE.search(raw) and rated_tokens:
        refuse("rating-vocabulary-clash",
               "%s carries BOTH `cx/risk/eff` and `rated`. The two vocabularies measure different "
               "things and never share a row; convert the entry to `rated` and delete the legacy "
               "triple." % where)
    score_tokens = _RATED_SCORE_TOKEN_RE.findall(raw)
    if len(score_tokens) > 1:
        refuse("rating-duplicate", "%s carries %d `rated` scores; exactly one is allowed"
               % (where, len(score_tokens)))
    if len(ovr_tokens) > 1:
        refuse("ovr-duplicate", "%s carries %d `ovr` tokens; at most one is allowed"
               % (where, len(ovr_tokens)))
    if ovr_tokens and not rated_tokens:
        refuse("ovr-orphan",
               "%s carries `ovr` with no `rated` scores. The override replaces the computed score "
               "for ranking; it does not stand in for the four axes, which keep their honest "
               "values underneath. %s" % (where, _RATING_GRAMMAR))

    m = _RATED_RE.search(raw)
    if not m:
        refuse("rating-shape",
               "%s carries a `rated` token that does not parse — %s. A malformed rating is refused "
               "rather than read as unrated, so a mistyped score is never silently dropped."
               % (where, _RATING_GRAMMAR))
    values = [int(g) for g in m.groups()]
    for axis, value in zip(("pri", "sev", "appeal", "effort"), values):
        if not 1 <= value <= 100:
            refuse("rating-range", "%s scores %s at %d; every axis is 1-100 (100 = strongest, "
                                   "effort included — it scores cheapness)" % (where, axis, value))
    out = dict(zip(RATING_COLUMNS[:4], values))
    out["rating_ovr"] = None
    if ovr_tokens:
        mo = _OVR_RE.search(raw)
        if not mo:
            refuse("ovr-shape", "%s carries an `ovr` token with no integer after it; %s"
                   % (where, _RATING_GRAMMAR))
        ovr = int(mo.group(1))
        if not 4 <= ovr <= 400:
            refuse("ovr-range", "%s overrides to %d; the override is on calc's own 4-400 scale"
                   % (where, ovr))
        out["rating_ovr"] = ovr
    return out


# GH-349 review (LTVera-Pandas #322): a ledger entry's GH number is a KEY, not a mention. It is
# only read from the HEAD of the title. An unanchored search harvested 111 out of "Execution
# checklist for GH-111 + GH-108", which collided with the real GH-111 entry and made
# `roadmap sync` refuse outright on this repo's own ROADMAP.md. A title that names several issues
# (`#129/#130/#131 · Wave 1 …`) is an umbrella heading, not a key, and must stay unnumbered.
_ROADMAP_KEY_RE = re.compile(r"^(?:GH-|#)(\d+)\b")
# The separator set distinguishes a RANGE from prose. `..`/`...` and U+2013 EN DASH are the
# conventional numeric-range delimiters (`GH-135..140`, `GH-135–140` — six issues, not issue 135).
# U+2014 EM DASH is deliberately EXCLUDED: `GH-100 — 2026 planning` is a single-issue title whose
# key would otherwise be silently dropped. The ASCII hyphen is excluded for the same reason.
# The first pass conflated the two dashes; codex QA separated them, 2026-08-31.
_ROADMAP_MULTI_KEY_RE = re.compile(
    r"^(?:GH-|#)\d+\s*(?:[/,+&\u2013]|\.\.\.?)\s*(?:GH-|#)?\d+")

# Markdown task-list items (`- [ ]`, `- [x]`) share the `- [` prefix with a link bullet but are
# not ledger entries; without this they parsed as rows with an empty or "x" title.
_ROADMAP_TASKBOX_RE = re.compile(r"^- \[[ xX]\]")


def _is_ledger_bullet(line):
    """A ledger entry opener: a bold bullet or a link bullet, never a task-list checkbox."""
    if line.startswith("- **"):
        return True
    return line.startswith("- [") and not _ROADMAP_TASKBOX_RE.match(line)


def _roadmap_gh_number(title):
    """The GH number a ledger entry is keyed by, or None. Anchored at the head of the title."""
    if _ROADMAP_MULTI_KEY_RE.match(title):
        return None
    m = _ROADMAP_KEY_RE.match(title)
    return int(m.group(1)) if m else None


# A scheme in a markdown link target: `https:`, `mailto:`, or a Windows drive prefix `C:`. Any of
# these means the target is not a repo-relative path, whatever it ends with.
_DOC_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _doc_pointer(target):
    """The repo-relative document path a link target names, or None.

    The `doc_path` column is a path a consumer resolves against the filesystem, so an absolute
    URL, a mail address or a drive-lettered path in it yields a miss indistinguishable from a
    dead pointer. codex QA found the first cut let all three through, because the extraction
    regexes accepted any `.md`-suffixed target and this check was only consulted on the fallback
    branch. It is now the SINGLE validator every candidate passes through, whichever regex found
    it — a scheme-bearing `https://github.com/acme/specs/blob/main/DESIGN.md` is rejected here
    even though it ends `.md`."""
    if not target:
        return None
    target = target.strip()
    if not target:
        return None
    if _DOC_SCHEME_RE.match(target) or target.startswith("/") or "\\" in target:
        return None
    path = target.split("#", 1)[0].split("?", 1)[0]
    return path if path.endswith(".md") else None


def _roadmap_issue_url(raw, link_target, gh_number):
    """The URL a ledger entry is keyed to, or None.

    Exactly two things count as evidence of identity: the bullet's OWN link target, and a URL in
    the block whose number corroborates the title's GH key. Nothing else — an unanchored search
    keyed GH-94 to a DIFFERENT repo's issue #2 and GH-68 to a PR, because both hooks cite other
    work in passing.

    An earlier cut kept a third branch for UNKEYED entries: the first URL on the bullet's first
    line. codex QA showed that branch is wrong on the reporting repo's live data, where it stored
    a BLOCKER as the row's identity — `Grow Willies …` took #42 (a blocker that has its own ledger
    row) and `Marathon Plan 2026-07-07 …` took #47 (merely its only fireable lane). Being first is
    not evidence. An unkeyed entry whose own link is a document now stores nothing.

    Position never implies identity here: no URL beats a wrong URL."""
    if link_target:
        target = link_target.strip()
        m = ROADMAP_URL_RE.fullmatch(target)
        if m:
            num = int(target.rsplit("/", 1)[1])
            if gh_number is None or num == gh_number:
                return m.group(0)
    if gh_number is None:
        return None
    for cand in ROADMAP_URL_RE.findall(raw):
        if int(cand.rsplit("/", 1)[1]) == gh_number:
            return cand
    return None


def parse_roadmap_ledger(path):
    """ROADMAP.md -> [entry dict], file order. Same block boundaries as the planner: an entry runs
    from its bullet line (`- **` or `- [`) to the next bullet, `###`, or `##`."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    entries = []
    sec = None
    inledger = False
    pos = {}
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"^##\s+Ledger\s*$", line.strip()):
            inledger = True
            i += 1
            continue
        if inledger and re.match(r"^##\s+", line):
            break
        if inledger and line.startswith("### "):
            sec = line[4:].strip()
            i += 1
            continue
        if inledger and sec and _is_ledger_bullet(line):
            j = i + 1
            while j < n and not (_is_ledger_bullet(lines[j]) or lines[j].startswith("### ")
                                 or re.match(r"^##\s+", lines[j])):
                j += 1
            raw = "\n".join(lines[i:j]).rstrip()
            m_bold = re.match(r"^- \*\*(.+?)\*\*", raw)
            m_link = re.match(r"^- \[(.+?)\](?:\((.*?)\))?", raw)
            if m_bold:
                title = m_bold.group(1).strip()
            elif m_link:
                title = m_link.group(1).strip()
            else:
                title = raw[2:].strip()[:80]
            gh_number = _roadmap_gh_number(title)
            marker = None
            for cand in _ROADMAP_STATUS_MARKERS:
                if cand in raw:
                    marker = cand
                    break
            cre = re.search(r"cx/risk/eff (\d+)/(\d+)/(\d+)", raw)
            link_target = m_link.group(2) if m_link else None
            doc = (re.search(r"\]\((PROJECT/[^)#]+\.md)(?:#[^)]*)?\)", raw)
                   or re.search(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", raw))
            # Every candidate goes through the one validator — the extraction regexes only find
            # a shape, they do not decide whether it is a document pointer.
            doc_path = _doc_pointer(doc.group(1)) if doc else None
            if doc_path is None:
                doc_path = _doc_pointer(link_target)
            issue_url = _roadmap_issue_url(raw, link_target, gh_number)
            pos[sec] = pos.get(sec, 0) + 1
            entry = {
                "gh_number": gh_number,
                "title": title, "section": sec, "position": pos[sec],
                "status_marker": marker,
                "complexity": int(cre.group(1)) if cre else None,
                "risk": int(cre.group(2)) if cre else None,
                "effort": int(cre.group(3)) if cre else None,
                "doc_path": doc_path,
                "issue_url": issue_url,
                "raw_text": raw,
            }
            entry.update(parse_rating(raw, title))
            entries.append(entry)
            i = j
            continue
        i += 1
    return entries


_ROADMAP_FIELDS = ("gh_number", "title", "section", "position", "status_marker",
                   "complexity", "risk", "effort", "doc_path", "issue_url", "raw_text") \
                  + RATING_COLUMNS



def validate_raw_text(raw_text, issue_num=None):
    """GH-257: validate that raw_text matches the markdown shape the renderer requires.

    The renderer (utils/roadmap-dashboard.sh) parses bullets starting with an exact `- **<title>**`
    prefix. An unparseable line (e.g. `- [ ] #255 ...`, `-   **`, or unclosed bold) is dropped by
    the dashboard renderer. Validating at write time catches malformed input immediately.
    """
    if not isinstance(raw_text, str):
        refuse("invalid-raw-text", "raw_text must be a string")
    if "\r" in raw_text or "\n" in raw_text:
        refuse("invalid-raw-text",
               "malformed --raw-text: raw_text must be a single line (no newlines permitted)")
    stripped = raw_text.strip()
    if not re.match(r'^- \*\*[^\r\n*]+?\*\*', stripped):
        refuse("invalid-raw-text",
               "malformed --raw-text %r: expected markdown bullet starting with '- **<title>**' "
               "(e.g. '- **GH-%s · <title>** ...')" % (raw_text, str(issue_num) if issue_num else "<num>"))
    if issue_num is not None:
        gh_patterns = [r'\bGH-%d\b' % issue_num, r'#%d\b' % issue_num]
        if not any(re.search(p, raw_text) for p in gh_patterns):
            refuse("invalid-raw-text",
                   "malformed --raw-text: does not reference issue GH-%d / #%d" % (issue_num, issue_num))
    return stripped



def validate_issue_identity(issue_url, gh_number, require_github=False):
    """GH-527: a GitHub issue_url must name the same issue as the row's gh_number.

    `reconcile-state` reads issue identity from this pair, so a row where they disagree can never
    be reconciled — it cannot ask GitHub about the right issue. GH-61 was imported that way: the
    legacy ROADMAP.md importer took the FIRST issue link in a line that named four child issues
    before its own `→ [#61]` pointer. That importer is retired, but intake accepted the same
    mismatch with no complaint, so the defect stayed creatable. Checked at BOTH writers now.

    The shape check is deliberately NOT enforced at intake. Rows legitimately carry URLs this
    regex does not match — imported cross-repo references, and fixtures that use short stand-in
    hosts — and refusing those would reject shapes intake has always accepted. Identity is what
    matters: if the URL IS a GitHub issue URL, its number must agree. `require_github` is for the
    repair verb, whose entire purpose is to make a row resolvable, so a malformed URL there is a
    failed repair rather than a pre-existing shape to tolerate.
    """
    url = issue_url or ""
    if not GH_ISSUE_URL_RE.fullmatch(url):
        if require_github:
            refuse("roadmap-issue-url", "%s is not a GitHub issue URL" % issue_url)
        return
    if gh_number is not None and url.rsplit("/", 1)[-1] != str(gh_number):
        refuse("roadmap-issue-url", "%s does not name issue #%s; a row's issue_url and gh_number "
               "must agree, or reconcile-state can never resolve the row"
               % (issue_url, gh_number))


def cmd_roadmap_add(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        validate_issue_identity(args.issue_url, args.issue_num)
        basename = os.path.basename(args.doc_path)
        # hq park passes the hq_roadmap_line rendering via --raw-text so preview and stored row
        # share ONE template; the inline fallback exists only for direct CLI use.
        if args.raw_text:
            raw_text = validate_raw_text(args.raw_text, args.issue_num)
        else:
            raw_text = "- **GH-%d · %s** 🆕 **captured %s via HQ** — [%s](%s) · [#%d](%s)" % (
                args.issue_num, args.title, args.created, basename, args.doc_path,
                args.issue_num, args.issue_url
            )
        # GH-249: the rating rides in the ledger line, parsed by the SAME parse_rating() the
        # markdown sync uses — one grammar, one parser, never a second scorer. Before this, ratings
        # could only enter through `roadmap sync`, which GH-169 turned into a no-op in releases-mode
        # repos, so every row parked after the flip was silently unrated.
        rating = parse_rating(raw_text, args.title)

        if args.dry_run:
            print("ROADMAP line: %s" % raw_text)
            if rating["rating_pri"] is not None:
                print("rating: %s" % "/".join(str(rating[c]) for c in RATING_COLUMNS[:4]))
                if rating["rating_ovr"] is not None:
                    print("ovr: %d" % rating["rating_ovr"])
            return

        # Dup guard — only when the shadow table exists; a pre-migration ledger gets the schema
        # installed inside mutate (mirrors cmd_roadmap_sync) instead of a raw OperationalError.
        if _table_exists(conn, "roadmap_items"):
            row = conn.execute("SELECT id FROM roadmap_items WHERE issue_url = ?", (args.issue_url,)).fetchone()
            if row:
                refuse("roadmap-duplicate", "issue %s is already parked in the roadmap" % args.issue_url)

            row2 = conn.execute("SELECT id FROM roadmap_items WHERE gh_number = ?", (args.issue_num,)).fetchone()
            if row2:
                refuse("roadmap-duplicate", "issue GH-%d is already parked in the roadmap" % args.issue_num)

        gid = new_gid("rmi-")

        def mutate(conn):
            _ensure_roadmap_schema(conn)
            ts = now_iso()
            section = "Queue / parked intake"   # the canonical ledger queue heading (GH-243)
            max_pos = conn.execute("SELECT MAX(position) FROM roadmap_items WHERE section = ?", (section,)).fetchone()
            pos = (max_pos[0] or 0) + 1 if max_pos else 1
            
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")
            
            # Mirrors cmd_roadmap_sync: feature commands never self-migrate. A rated line meeting
            # a ledger with no rating columns is refused BY NAME rather than written with its
            # scores silently dropped — an unrated row is indistinguishable from "never scored".
            rating_ok = _has_column(conn, "roadmap_items", "rating_pri")
            if not rating_ok and rating["rating_pri"] is not None:
                refuse("schema-behind",
                       "GH-%d carries `rated` scores but this ledger has no rating columns. Run "
                       "`releases migrate` first — intake stores scores, it never installs schema."
                       % args.issue_num)

            cols = ["global_id", "repo_id", "gh_number", "title", "section", "position",
                    "status_marker", "doc_path", "issue_url", "raw_text", "first_seen", "updated_at"]
            vals = [gid, repo["id"], args.issue_num, args.title, section, pos,
                    "🆕", args.doc_path, args.issue_url, raw_text, ts, ts]
            if rating_ok:
                cols += list(RATING_COLUMNS)
                vals += [rating[c] for c in RATING_COLUMNS]
            conn.execute("INSERT INTO roadmap_items(%s) VALUES (%s)"
                         % (", ".join(cols), ", ".join("?" * len(cols))), vals)
                          
        perform_write(root, conn, "roadmap-add", gid, mutate)
        print("added roadmap entry %s for GH-%d" % (gid, args.issue_num))
    finally:
        conn.close()

def cmd_roadmap_rate(args):
    """GH-253: score a roadmap row that is already parked.

    GH-249 taught intake to STORE a rating, but rows parked between the GH-169 flip and that fix
    were written unrated and had no path back — `roadmap add` only inserts, `roadmap sync` is a
    no-op in releases-mode, and nothing else writes the columns. That made "unrated" permanent for
    exactly the rows the bug created. This is the way back.

    The rating is rendered into the SAME `rated N/N/N/N [ovr N]` token the ledger line carries and
    handed to the SAME parse_rating() — the token in raw_text and the five columns are written in
    one transaction so the lossless shadow can never disagree with the scores derived from it.
    """
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if not _table_exists(conn, "roadmap_items"):
            refuse("no-ledger", "this DB has no roadmap_items table; run `releases migrate` first")
        # A row imported from a multi-issue ROADMAP bullet ("#129/#130/#131 · Wave 1 …") carries NO
        # gh_number, so --issue-num cannot address it and it would be unscorable forever — the same
        # permanence bug this command exists to end. --gid is the escape hatch for those rows.
        if (args.issue_num is None) == (args.gid is None):
            refuse("selector", "pass exactly one of --issue-num or --gid")
        if args.issue_num is not None:
            where, param, label = "gh_number = ?", args.issue_num, "GH-%d" % args.issue_num
        else:
            where, param, label = "global_id = ?", args.gid, args.gid
        row = conn.execute(
            "SELECT global_id, title, raw_text, rating_pri, complexity, risk, effort "
            "FROM roadmap_items WHERE " + where, (param,)).fetchone()
        if not row:
            refuse("no-such-row", "no roadmap row for %s; park it with `roadmap add` first" % label)
        if not _has_column(conn, "roadmap_items", "rating_pri"):
            refuse("schema-behind",
                   "this ledger has no rating columns. Run `releases migrate` first — rating "
                   "stores scores, it never installs schema.")
        if row["rating_pri"] is not None and not args.force:
            refuse("already-rated",
                   "%s is already rated. Re-scoring is a deliberate act, not a retry: pass "
                   "--force if you mean to replace the existing scores." % label)
        if any(_col(row, c) is not None for c in ("complexity", "risk", "effort")):
            refuse("rating-vocabulary-clash",
                   "%s carries legacy `cx/risk/eff`. The two vocabularies measure different "
                   "things and never share a row; convert the entry deliberately rather than "
                   "stacking a `rated` score on top of it." % label)

        token = "(rated %s%s)" % (args.rated, "" if args.ovr is None else " ovr %d" % args.ovr)
        # parse_rating is the ONE parser and the ONE validator: a malformed --rated is refused by
        # name here, exactly as it is on the intake path, rather than reaching the columns.
        rating = parse_rating(token, row["title"])
        raw_text = _RATED_TOKEN_RE.sub("", row["raw_text"]).rstrip()
        raw_text = "%s %s" % (raw_text, token)

        if args.dry_run:
            print("ROADMAP line: %s" % raw_text)
            print("rating: %s" % "/".join(str(rating[c]) for c in RATING_COLUMNS[:4]))
            if rating["rating_ovr"] is not None:
                print("ovr: %d" % rating["rating_ovr"])
            return

        def mutate(conn):
            conn.execute(
                "UPDATE roadmap_items SET raw_text = ?, updated_at = ?, %s WHERE %s"
                % (", ".join("%s = ?" % c for c in RATING_COLUMNS), where),
                [raw_text, now_iso()] + [rating[c] for c in RATING_COLUMNS] + [param])

        perform_write(root, conn, "roadmap-rate", row["global_id"], mutate)
        print("rated %s %s" % (label, args.rated))
    finally:
        conn.close()


def cmd_roadmap_repoint(args):
    """Re-point a parked row's capture doc after the doc moves between PROJECT stages.

    `roadmap add` records doc_path once and refuses duplicates, and nothing else rewrites it — so
    promoting a doc 1-INBOX -> 2-WORKING left the row pointing at a path that no longer exists, and
    pdda-check-roadmap-coverage fails on it with no supported way to fix it.

    The move itself stays a `git mv` by the operator: this verb only rewrites the row (and the
    dashboard regenerates separately via utils/roadmap-dashboard.sh), so the GH-243 ledger-with-
    dashboard guard sees a clean regeneration range on the next push.
    """
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        row = conn.execute("SELECT global_id, doc_path, raw_text FROM roadmap_items "
                           "WHERE gh_number = ?", (args.issue_num,)).fetchone()
        if not row:
            refuse("no-such-row", "no roadmap row for GH-%d" % args.issue_num)
        new = args.doc_path
        if not os.path.isfile(os.path.join(root, new)):
            refuse("no-such-doc", "%s does not exist under %s — re-point to a real doc, never a "
                                  "path that merely looks right" % (new, root))
        old = row["doc_path"]
        # The ledger line embeds the path too; rewriting one without the other just moves the drift.
        raw_text = row["raw_text"].replace(old, new) if old else row["raw_text"]
        if args.dry_run:
            print("doc_path: %s -> %s" % (old, new))
            print("ROADMAP line: %s" % raw_text)
            return

        def mutate(conn):
            conn.execute("UPDATE roadmap_items SET doc_path = ?, raw_text = ?, updated_at = ? "
                         "WHERE gh_number = ?", (new, raw_text, now_iso(), args.issue_num))

        perform_write(root, conn, "roadmap-repoint", row["global_id"], mutate)
        print("repointed GH-%d -> %s" % (args.issue_num, new))
    finally:
        conn.close()


def cmd_settings_set(args):
    """`releases settings set <key> <value>` — write a settings row THROUGH the writer protocol.

    GH-525: without this there is no supported way to configure the ledger at all. A settings row
    is part of the business-state digest, so a direct `sqlite3 INSERT` — the only alternative —
    leaves the latest receipt's after-digest disagreeing with the state and `check` fails with
    `receipt-chain: ... a receipt-less mutation`. Measured, not assumed: setting
    `unshipped_version_tokens` by hand took a clean ledger to `check: 2 failure(s)`.

    So a configurable ledger needs a configuring verb. Only keys in CONFIGURABLE_SETTINGS are
    writable: `generation` is owned by the writer protocol and `repo_slug` is identity, and letting
    either be set here would hand an operator a supported way to corrupt the ledger."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        if args.key not in CONFIGURABLE_SETTINGS:
            refuse("setting-not-configurable",
                   "%s is not an operator-configurable setting; configurable keys are: %s"
                   % (args.key, ", ".join(sorted(CONFIGURABLE_SETTINGS))))
        old = get_setting(conn, args.key)
        if args.dry_run:
            print("%s: %s -> %s" % (args.key, old if old is not None else "(unset)", args.value))
            return

        def mutate(conn):
            if _has_column(conn, "settings", "updated_at"):
                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?) "
                             "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                             "updated_at = excluded.updated_at",
                             (args.key, args.value, now_iso()))
            else:
                conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) "
                             "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                             (args.key, args.value))

        perform_write(root, conn, "settings-set", None, mutate)
        print("%s = %s" % (args.key, args.value))
    finally:
        conn.close()


def cmd_settings_list(args):
    """Print every settings row, so "what is this ledger configured to do" is one command."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        for row in conn.execute("SELECT key, value FROM settings ORDER BY key"):
            mark = " (configurable)" if row["key"] in CONFIGURABLE_SETTINGS else ""
            print("%-28s %s%s" % (row["key"], row["value"], mark))
    finally:
        conn.close()


def cmd_settings_get(args):
    """Print one setting value."""
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        val = get_setting(conn, args.key, None)
        if val is None:
            sys.exit(1)
        print(val)
    finally:
        conn.close()


def validate_roadmap_section(section):
    """Refuse headings the dashboard cannot render; never silently rename input."""
    if section not in ROADMAP_SECTIONS:
        hint = (" 'Deferred / cancelled' is a legacy markdown heading; use 'Deferred · vision'."
                if section == "Deferred / cancelled" else "")
        refuse("invalid-section", "unknown roadmap section %r.%s Valid sections: %s"
               % (section, hint, ", ".join(repr(s) for s in ROADMAP_SECTIONS)))
    return section


def cmd_roadmap_sections(args):
    print(json.dumps(ROADMAP_SECTIONS, ensure_ascii=False) if args.as_json
          else "\n".join(ROADMAP_SECTIONS))


def cmd_roadmap_update(args):
    """Update a parked row's explicit fields through the receipt-backed writer.

    GH-257 adds raw_text/section updates; GH-424 adds an explicit status marker.
    Marker-only updates preserve raw_text, ratings, section and doc_path.
    """
    marker = getattr(args, "status_marker", None)  # `move` shares this handler.
    if marker is not None and marker not in _ROADMAP_STATUS_MARKERS:
        refuse("invalid-status-marker", "--status-marker must be one of %s"
               % ", ".join(_ROADMAP_STATUS_MARKERS))
    if args.section is not None:
        validate_roadmap_section(args.section)
    # `roadmap move` delegates here with its OWN namespace, which has no --issue-url. Read it
    # defensively rather than adding the flag to a verb that has no business setting it.
    issue_url = getattr(args, "issue_url", None)
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if not _table_exists(conn, "roadmap_items"):
            refuse("no-ledger", "this DB has no roadmap_items table; run `releases migrate` first")
        if (args.issue_num is None) == (args.gid is None):
            refuse("selector", "pass exactly one of --issue-num or --gid")
        if args.issue_num is not None:
            where, param, label = "gh_number = ?", args.issue_num, "GH-%d" % args.issue_num
        else:
            where, param, label = "global_id = ?", args.gid, args.gid

        has_rating_cols = _has_column(conn, "roadmap_items", "rating_pri")
        select_cols = ["global_id", "gh_number", "title", "raw_text", "issue_url"]
        row = conn.execute(
            "SELECT %s FROM roadmap_items WHERE %s" % (", ".join(select_cols), where), (param,)).fetchone()
        if not row:
            refuse("no-such-row", "no roadmap row for %s; park it with `roadmap add` first" % label)

        if args.raw_text is None and args.section is None and marker is None and issue_url is None:
            refuse("no-update", "pass at least one of --raw-text, --section, --status-marker or --issue-url")

        new_raw_text = None
        rating = None
        if args.raw_text is not None:
            new_raw_text = validate_raw_text(args.raw_text, row["gh_number"])
            old_raw_text = row["raw_text"] or ""
            if (new_raw_text == old_raw_text.strip()
                    and args.section is None and marker is None and issue_url is None):
                print("roadmap update: %s raw_text unchanged; nothing written" % label)
                return
            rating = parse_rating(new_raw_text, row["title"])
            if not has_rating_cols and rating["rating_pri"] is not None:
                refuse("schema-behind",
                       "this ledger has no rating columns. Run `releases migrate` first — rating "
                       "stores scores, it never installs schema.")

        if issue_url is not None:
            # The repair must not be able to re-create the defect it exists to fix.
            validate_issue_identity(issue_url, row["gh_number"], require_github=True)

        if args.dry_run:
            if args.raw_text is not None:
                print("raw_text: %s -> %s" % (old_raw_text, new_raw_text))
                if rating["rating_pri"] is not None:
                    print("rating: %s" % "/".join(str(rating[c]) for c in RATING_COLUMNS[:4]))
                    if rating["rating_ovr"] is not None:
                        print("ovr: %d" % rating["rating_ovr"])
            if args.section:
                print("section: -> %s" % args.section)
            if marker is not None:
                print("status_marker: -> %s" % marker)
            if issue_url:
                print("issue_url: %s -> %s" % (row["issue_url"], issue_url))
            return

        def mutate(conn):
            ts = now_iso()
            updates = ["updated_at = ?"]
            params = [ts]
            if args.raw_text is not None:
                updates.append("raw_text = ?")
                params.append(new_raw_text)
                if has_rating_cols:
                    for c in RATING_COLUMNS:
                        updates.append("%s = ?" % c)
                        params.append(rating[c])
            if args.section is not None:
                updates.append("section = ?")
                params.append(args.section)
            if marker is not None:
                updates.append("status_marker = ?")
                params.append(marker)
            if issue_url is not None:
                updates.append("issue_url = ?")
                params.append(issue_url)

            params.append(param)
            conn.execute("UPDATE roadmap_items SET %s WHERE %s" % (", ".join(updates), where), params)

        perform_write(root, conn, "roadmap-update", row["global_id"], mutate)
        print("updated %s" % label)
    finally:
        conn.close()


def cmd_roadmap_move(args):
    """GH-269: move a roadmap row to a new section (e.g. 'Completed', 'Deferred · vision')."""
    return cmd_roadmap_update(args)


def cmd_roadmap_reconcile_state(args):
    """GH-492: preview by default; apply only positively verified terminal issue states.

    Read every candidate before taking the writer lock, so one failed lookup cannot leave a
    partially swept ledger. Local updated_at is a concurrency fence, not a GitHub freshness
    watermark: an issue can close without any local row changing.
    """
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        if not _table_exists(conn, "roadmap_items"):
            refuse("no-ledger", "this DB has no roadmap_items table; run `releases migrate` first")
        terminal = tuple(validate_roadmap_section(s) for s in ("Completed", "Deferred · vision"))
        rows = conn.execute(
            "SELECT * FROM roadmap_items WHERE section NOT IN (?, ?) AND gh_number IS NOT NULL "
            "ORDER BY gh_number, global_id", terminal).fetchall()
        changes = []
        unresolvable = []
        for row in rows:
            # Full URLs preserve repository identity, including imported cross-repo references.
            url = row["issue_url"] or ""
            if (not GH_ISSUE_URL_RE.fullmatch(url)
                    or url.rsplit("/", 1)[-1] != str(row["gh_number"])):
                # Per-row, not per-command: one row whose issue_url disagrees with its gh_number
                # is a local data defect, and refusing the whole sweep over it strands every other
                # row (#527). Still never guess this row's state — skip it and name it.
                unresolvable.append(row["gh_number"])
                continue
            try:
                result = subprocess.run(
                    [os.environ.get("RELEASES_GH_BIN", "gh"), "issue", "view", url,
                     "--json", "state,stateReason"], cwd=root,
                    capture_output=True, text=True, check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as exc:
                refuse("roadmap-issue-state", "%s could not be read (%s); refusing to guess issue state"
                       % (url, exc))
            if result.returncode:
                refuse("roadmap-issue-state", "%s failed (exit %d): %s; refusing to guess issue state"
                       % (url, result.returncode, result.stderr.strip()))
            try:
                issue = json.loads(result.stdout)
            except ValueError:
                issue = None
            if not isinstance(issue, dict) or issue.get("state") not in ("OPEN", "CLOSED"):
                refuse("roadmap-issue-state", "%s returned invalid state; refusing to guess issue state" % url)
            if issue["state"] == "OPEN":
                continue
            reason = issue.get("stateReason")
            if reason not in ("COMPLETED", "NOT_PLANNED"):
                refuse("roadmap-issue-state", "%s returned unknown closure reason; refusing to guess "
                       "issue state" % url)
            target = terminal[0] if reason == "COMPLETED" else terminal[1]
            changes.append((row, target))

        for gh in unresolvable:
            print("warn: rule=roadmap-issue-identity: GH-%s has no matching issue URL; skipped "
                  "(fix with `releases roadmap update --issue-num %s --issue-url <url>`)"
                  % (gh, gh))
        if not changes:
            print("roadmap reconcile-state: no changes; nothing written")
            return
        if not args.apply:
            for row, target in changes:
                print("would move GH-%d: %s -> %s" % (row["gh_number"], row["section"], target))
            print("roadmap reconcile-state: dry-run; nothing written (pass --apply to write)")
            return

        def mutate(conn):
            # Recheck the observed rows inside BEGIN IMMEDIATE; never overwrite a concurrent edit.
            for row, target in changes:
                current = conn.execute("SELECT * FROM roadmap_items WHERE global_id = ?",
                                       (row["global_id"],)).fetchone()
                if current is None or dict(current) != dict(row):
                    refuse("roadmap-state-stale", "GH-%d changed during lookup; rerun the sweep"
                           % row["gh_number"])
            ts = now_iso()
            for row, target in changes:
                conn.execute("UPDATE roadmap_items SET section = ?, updated_at = ? WHERE global_id = ?",
                             (target, ts, row["global_id"]))

        perform_write(root, conn, "roadmap-reconcile-state", None, mutate)
        for row, target in changes:
            print("moved GH-%d: %s -> %s" % (row["gh_number"], row["section"], target))
    finally:
        conn.close()


def cmd_roadmap_sync(args):
    root = resolve_root(args.root)
    # PR #240 review: sync mirrors ROADMAP.md and DELETES rows absent from it — in a releases-mode
    # repo the DB is canonical and rows arrive via `roadmap add` with no markdown source line, so
    # mirroring would destroy parked intake. Skip cleanly (exit 0): wave_reconcile.py calls sync
    # unconditionally post-merge and must stay green in both modes.
    try:
        with open(os.path.join(root, ".pdda-mode")) as f:
            if "ROADMAP_SOURCE=releases" in f.read():
                print("roadmap sync: skipped — releases-mode repo (the DB is canonical; sync only "
                      "mirrors ROADMAP.md in legacy mode, and would delete rows parked by `roadmap add`)")
                return
    except OSError:
        pass
    conn = connect(artifact_paths(root)["db"])
    try:
        md_path = os.path.join(root, ROADMAP_NAME)
        if not os.path.exists(md_path):
            refuse("roadmap-missing", "no %s at %s — nothing to shadow" % (ROADMAP_NAME, root))
        parsed = parse_roadmap_ledger(md_path)
        if len(parsed) == 0:
            ledger_has_content = False
            in_ledger_check = False
            with open(md_path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            for line in lines:
                if re.match(r"^##\s+Ledger\s*$", line.strip()):
                    in_ledger_check = True
                    continue
                if in_ledger_check and re.match(r"^##\s+", line):
                    break
                # A `###` section heading is ledger STRUCTURE, not content: a ledger with its
                # sections and no bullets is genuinely empty. Format drift, by contrast, is
                # bullets in a shape the parser missed — still non-heading lines, still caught.
                if (in_ledger_check and line.strip()
                        and not line.strip().startswith("<!--")
                        and not line.startswith("###")):
                    ledger_has_content = True
                    break
            has_rows = bool(_table_exists(conn, "roadmap_items")
                            and conn.execute("SELECT 1 FROM roadmap_items LIMIT 1").fetchone())
            if ledger_has_content or has_rows:
                # --allow-empty is the ONE sanctioned way to clear the mirror. It is deliberately
                # narrow: it never excuses a ledger that still has content, so it cannot be used to
                # paper over the format drift this guard exists to catch. Without it, an
                # intentionally emptied ledger was a dead end, and AGENTS.md forbids the hand-edit
                # of releases.db that agy suggested as the workaround. codex QA, 2026-08-31.
                if ledger_has_content or not getattr(args, "allow_empty", False):
                    refuse("roadmap-empty-parse",
                           "parsed 0 entries from %s (%s); refusing to delete roadmap_items%s"
                           % (ROADMAP_NAME,
                              "ledger is non-empty" if ledger_has_content else "table has existing rows",
                              "" if ledger_has_content else " — pass --allow-empty if the ledger is "
                              "meant to be empty and you intend to clear the mirror"))
                n_rows = conn.execute("SELECT COUNT(*) FROM roadmap_items").fetchone()[0]
                print("roadmap sync: --allow-empty — %s ledger is empty, clearing %d mirrored row(s)"
                      % (ROADMAP_NAME, n_rows))
        # duplicate GH keys in the markdown would make the mirror ambiguous — name it, do not pick
        seen = {}
        for e in parsed:
            if e["gh_number"] is not None:
                if e["gh_number"] in seen:
                    refuse("roadmap-duplicate-gh",
                           "GH-%d appears twice in %s (%r and %r). The mirror keys entries by GH "
                           "number; merge or renumber one of them, then re-run."
                           % (e["gh_number"], ROADMAP_NAME, seen[e["gh_number"]][:60],
                              e["title"][:60]))
                seen[e["gh_number"]] = e["title"]

        # An unkeyed row is keyed by its TITLE instead (see the `have`/`parsed` key below), so two
        # identical unkeyed titles are the same ambiguity as a duplicate GH number — and more
        # reachable since GH-349 made umbrella and range headings deliberately unkeyed. Left
        # unguarded, both enter `adds` on the first sync and collapse to one key on the next,
        # leaving an orphan row behind. codex QA, 2026-08-31.
        seen_titles = set()
        for e in parsed:
            if e["gh_number"] is None:
                if e["title"] in seen_titles:
                    refuse("roadmap-duplicate-title",
                           "the unkeyed entry %r appears twice in %s. Entries without a GH number "
                           "are mirrored by title, so two identical ones are ambiguous; give one a "
                           "GH key or retitle it, then re-run." % (e["title"][:80], ROADMAP_NAME))
                seen_titles.add(e["title"])

        repo = conn.execute("SELECT id, global_id FROM repos ORDER BY id LIMIT 1").fetchone()
        if repo is None:
            refuse("no-repo", "the DB has no repos row; run `releases init` first")

        # GH-108/GH-111: feature commands do NOT self-migrate. Rating storage arrives through
        # `releases migrate` (migration 003); sync refuses clearly when a rated entry meets a
        # ledger that cannot hold it, rather than installing schema of its own or — worse —
        # writing the entry with its scores silently dropped.
        rating_ok = _has_column(conn, "roadmap_items", "rating_pri")
        if not rating_ok and any(e["rating_pri"] is not None for e in parsed):
            refuse("schema-behind",
                   "%s carries `rated` scores but this ledger has no rating columns. Run "
                   "`releases migrate` first — sync mirrors ROADMAP.md, it never installs schema."
                   % ROADMAP_NAME)

        have = {}
        if _table_exists(conn, "roadmap_items"):
            for r in conn.execute("SELECT * FROM roadmap_items WHERE repo_id = ?", (repo["id"],)):
                key = ("gh", r["gh_number"]) if r["gh_number"] is not None else ("title", r["title"])
                have[key] = {c: _col(r, c) for c in r.keys()}
                for c in RATING_COLUMNS:
                    have[key].setdefault(c, None)
        schema_missing = not _table_exists(conn, "roadmap_items") or conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = 2").fetchone() is None

        adds, updates, keeps = [], [], []
        matched = set()
        for e in parsed:
            key = ("gh", e["gh_number"]) if e["gh_number"] is not None else ("title", e["title"])
            row = have.get(key)
            if row is None:
                adds.append(e)
                continue
            matched.add(key)
            if any(e[f] != row[f] for f in _ROADMAP_FIELDS):
                updates.append((row, e))
            else:
                keeps.append(row)
        removes = [have[k] for k in have if k not in matched]

        changed = bool(adds or updates or removes or schema_missing)
        summary = "roadmap sync: %d in %s -> +%d added, ~%d updated, -%d removed, %d unchanged" % (
            len(parsed), ROADMAP_NAME, len(adds), len(updates), len(removes), len(keeps))
        if not changed:
            print(summary + " — already in sync; no write, generation unchanged")
            return
        if getattr(args, "dry_run", False):
            print(summary + " — DRY RUN, nothing written")
            for e in adds:
                print("  + [%s] %s" % (e["section"], e["title"][:70]))
            for row, e in updates:
                print("  ~ [%s] %s" % (e["section"], e["title"][:70]))
            for row in removes:
                print("  - [%s] %s" % (row["section"], row["title"][:70]))
            return

        # The row MIRRORS the entry text: converting an entry from cx/risk/eff to `rated` populates
        # the rating columns and NULLs the legacy ones in the SAME sync. A mirror that disagreed
        # with its source would re-update on every sync forever; the entry's lossless raw_text is
        # the historical record, not the row.
        fields = [f for f in _ROADMAP_FIELDS if rating_ok or f not in RATING_COLUMNS]

        def mutate(c):
            _ensure_roadmap_schema(c)
            ts = now_iso()
            ins_cols = ["global_id", "repo_id"] + fields + ["first_seen", "updated_at"]
            ins_sql = "INSERT INTO roadmap_items(%s) VALUES (%s)" % (
                ", ".join(ins_cols), ", ".join("?" for _ in ins_cols))
            upd_sql = "UPDATE roadmap_items SET %s, updated_at=? WHERE id=?" % (
                ", ".join("%s=?" % f for f in fields))
            for e in adds:
                c.execute(ins_sql,
                          [new_gid("rmi-"), repo["id"]] + [e[f] for f in fields] + [ts, ts])
            for row, e in updates:
                c.execute(upd_sql, [e[f] for f in fields] + [ts, row["id"]])
            for row in removes:
                c.execute("DELETE FROM roadmap_items WHERE id = ?", (row["id"],))

        txn = perform_write(root, conn, "roadmap-sync", None, mutate)
        print(summary + " (txn %s, generation %d)" % (txn[:12], get_generation(conn)))
    finally:
        conn.close()


def roadmap_render(conn):
    """Replay the ledger, preserving section names and each stored entry block (GH-423).

    Positions are section-local. The GID breaks position ties deterministically without
    depending on SQLite's row order. Unknown sections are retained, just as sync retains them;
    consumers still decide which sections they accept.
    """
    parts = ["## Ledger\n"]
    if not _table_exists(conn, "roadmap_items"):
        return parts[0]
    section = None
    for row in conn.execute("SELECT * FROM roadmap_items ORDER BY section, position, global_id"):
        if row["section"] != section:
            section = row["section"]
            parts.append("\n### %s\n\n" % section)
        raw = row["raw_text"]
        if not raw or not raw.strip():
            title = row["title"]
            gh = row["gh_number"]
            if gh is not None and _roadmap_gh_number(title) != gh:
                title = "GH-%d · %s" % (gh, title)
            raw = "- **%s**" % title
            if row["status_marker"]:
                raw += " " + row["status_marker"]
            if all(_col(row, c) is not None for c in RATING_COLUMNS[:4]):
                raw += " rated " + "/".join(str(row[c]) for c in RATING_COLUMNS[:4])
                if _col(row, "rating_ovr") is not None:
                    raw += " ovr %s" % row["rating_ovr"]
            elif all(_col(row, c) is not None for c in ("complexity", "risk", "effort")):
                raw += " cx/risk/eff %s/%s/%s" % (row["complexity"], row["risk"], row["effort"])
            if row["doc_path"]:
                raw += " → [doc](%s)" % row["doc_path"]
            if row["issue_url"]:
                raw += " · [issue](%s)" % row["issue_url"]
        parts.append(raw)
        parts.append("\n\n")
    return "".join(parts)


def cmd_roadmap_render(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    out = os.path.realpath(args.out) if args.out else None
    if out:
        if out in {os.path.realpath(p) for p in paths.values()}:
            refuse("roadmap-render-output", "--out must not overwrite a releases ledger artifact")
        # Check the destination's repository, including foreign repos and symlink targets.
        # Fail closed when git cannot establish whether ROADMAP.md is tracked.
        for candidate in dict.fromkeys((out, os.path.abspath(args.out))):
            if os.path.basename(candidate) != ROADMAP_NAME:
                continue
            try:
                tracked = subprocess.run(
                    ["git", "-C", os.path.dirname(candidate), "ls-files", "--error-unmatch", "--", ROADMAP_NAME],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError as exc:
                refuse("roadmap-render-output", "cannot check tracked ROADMAP.md: %s" % exc)
            if tracked.returncode != 1:
                refuse("roadmap-render-output", "--out refuses tracked ROADMAP.md (or unverifiable tracking)")
    conn = connect(paths["db"])
    try:
        rendered = roadmap_render(conn)
    finally:
        conn.close()
    if out:
        try:
            _atomic_write(out, rendered)
        except OSError as exc:
            refuse("roadmap-render-output", "cannot write --out: %s" % exc)
    else:
        sys.stdout.write(rendered)


def cmd_roadmap_list(args):
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        if getattr(args, "as_json", False):
            # Machine-readable contract for consumers (hq rollup): the human rendering below is
            # a display, not an API — its column offsets shift whenever a field widens.
            rows = []
            if _table_exists(conn, "roadmap_items"):
                for r in conn.execute("SELECT * FROM roadmap_items ORDER BY section, position"):
                    rows.append({"global_id": r["global_id"], "gh_number": r["gh_number"],
                                 "title": r["title"], "section": r["section"],
                                 "position": r["position"], "status_marker": r["status_marker"],
                                 "doc_path": _col(r, "doc_path"), "issue_url": _col(r, "issue_url"),
                                 "raw_text": _col(r, "raw_text")})
            print(json.dumps(rows, ensure_ascii=False))
            return
        if not _table_exists(conn, "roadmap_items"):
            print("(no roadmap shadow yet — run `releases roadmap sync`)")
            return
        for r in conn.execute("""SELECT * FROM roadmap_items ORDER BY section, position"""):
            gh = ("GH-%d" % r["gh_number"]) if r["gh_number"] is not None else "-"
            cre = ("%s/%s/%s" % (r["complexity"], r["risk"], r["effort"])
                   if r["complexity"] is not None else "-")
            # calc is DERIVED here, never stored — the equal-weighted sum of the four axes, and
            # the override wins over it for ranking wherever both exist.
            score = "-"
            if _col(r, "rating_pri") is not None:
                calc = sum(_col(r, c) for c in RATING_COLUMNS[:4])
                score = str(calc)
                if _col(r, "rating_ovr") is not None:
                    score = "%s>%d" % (score, r["rating_ovr"])
            print("%s  %-7s %-22s #%-3d cre=%-6s calc=%-8s %s %s" % (
                r["global_id"], gh, (r["section"] or "")[:22], r["position"], cre, score,
                r["status_marker"] or " ", r["title"][:64]))
    finally:
        conn.close()


def resolve_issue_number(target):
    """Resolve a target string or int into a GitHub issue number (int)."""
    if isinstance(target, int):
        return target
    s = str(target).strip()
    if s.isdigit():
        return int(s)
    m = re.search(r"(?:GH-|gh-|#|issues/)(\d+)", s)
    if m:
        return int(m.group(1))
    refuse("invalid-issue-target", "cannot resolve GitHub issue number from %r" % target)


def cmd_jog_add(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gh_num = resolve_issue_number(args.target)

        if args.dry_run:
            print("jog add: would enqueue GH-%d at position %s" % (gh_num, args.pos or "end"))
            return

        gid = new_gid("jog-")

        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")

            existing = conn.execute(
                "SELECT id, status, position FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                (repo["id"], gh_num)).fetchone()
            ts = now_iso()
            if existing:
                if existing["status"] in ("pending", "running"):
                    refuse("jog-duplicate",
                           "GH-%d is already in jog queue (%s at position %d)"
                           % (gh_num, existing["status"], existing["position"]))
                if args.pos is not None:
                    new_pos = max(1, args.pos)
                    conn.execute("UPDATE jog_queue SET position = position + 1 WHERE repo_id = ? AND status IN ('pending', 'running') AND position >= ?",
                                 (repo["id"], new_pos))
                else:
                    max_pos = conn.execute("SELECT MAX(position) FROM jog_queue WHERE repo_id = ? AND status IN ('pending', 'running')",
                                           (repo["id"],)).fetchone()[0]
                    new_pos = (max_pos or 0) + 1
                conn.execute("""UPDATE jog_queue SET status = 'pending', position = ?, updated_at = ?,
                                attempt_count = 0, lease_pid = NULL, failure_reason = NULL
                                WHERE id = ?""", (new_pos, ts, existing["id"]))
                return

            if args.pos is not None:
                new_pos = max(1, args.pos)
                conn.execute("UPDATE jog_queue SET position = position + 1 WHERE repo_id = ? AND status IN ('pending', 'running') AND position >= ?",
                             (repo["id"], new_pos))
            else:
                max_pos = conn.execute("SELECT MAX(position) FROM jog_queue WHERE repo_id = ? AND status IN ('pending', 'running')",
                                       (repo["id"],)).fetchone()[0]
                new_pos = (max_pos or 0) + 1

            conn.execute("""INSERT INTO jog_queue(global_id, repo_id, gh_number, position, status,
                            created_at, updated_at, attempt_count, lease_pid, failure_reason)
                            VALUES (?, ?, ?, ?, 'pending', ?, ?, 0, NULL, NULL)""",
                         (gid, repo["id"], gh_num, new_pos, ts, ts))

        perform_write(root, conn, "jog-add", gid, mutate)
        print("jog: enqueued GH-%d" % gh_num)
    finally:
        conn.close()


def cmd_jog_list(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if not _table_exists(conn, "jog_queue"):
            if args.as_json:
                print("[]")
            else:
                print("Jog queue is empty (table not initialized).")
            return

        where_clause = "" if args.show_all else "WHERE jq.status IN ('pending', 'running')"
        has_rm = _table_exists(conn, "roadmap_items")
        if has_rm:
            query = """
                SELECT jq.id, jq.global_id, jq.gh_number, jq.position, jq.status,
                       jq.attempt_count, jq.lease_pid, jq.failure_reason, jq.created_at, jq.updated_at,
                       ri.title, ri.doc_path, ri.issue_url
                FROM jog_queue jq
                LEFT JOIN roadmap_items ri ON ri.gh_number = jq.gh_number
                %s
                ORDER BY CASE WHEN jq.status IN ('running', 'pending') THEN 0 ELSE 1 END, jq.position ASC, jq.id ASC
            """ % where_clause
        else:
            query = """
                SELECT jq.id, jq.global_id, jq.gh_number, jq.position, jq.status,
                       jq.attempt_count, jq.lease_pid, jq.failure_reason, jq.created_at, jq.updated_at,
                       NULL AS title, NULL AS doc_path, NULL AS issue_url
                FROM jog_queue jq
                %s
                ORDER BY CASE WHEN jq.status IN ('running', 'pending') THEN 0 ELSE 1 END, jq.position ASC, jq.id ASC
            """ % where_clause

        rows = [dict(r) for r in conn.execute(query).fetchall()]
        if args.as_json:
            print(json.dumps(rows, indent=2))
            return

        if not rows:
            print("Jog queue is empty.")
            return

        print("%-4s %-8s %-10s %-4s %-8s %s" % ("Pos", "Issue", "Status", "Att", "PID", "Title / Doc"))
        print("-" * 75)
        for r in rows:
            pos_str = str(r["position"]) if r["status"] in ("pending", "running") else "-"
            issue_str = "GH-%d" % r["gh_number"]
            status_str = r["status"]
            att_str = str(r["attempt_count"])
            pid_str = str(r["lease_pid"] or "-")
            title_str = r["title"] or r["doc_path"] or "(no title)"
            if len(title_str) > 38:
                title_str = title_str[:35] + "..."
            print("%-4s %-8s %-10s %-4s %-8s %s" % (pos_str, issue_str, status_str, att_str, pid_str, title_str))
    finally:
        conn.close()


def cmd_jog_bump(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gh_num = resolve_issue_number(args.target)

        if args.dry_run:
            print("jog bump: would move GH-%d to position 1" % gh_num)
            return

        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")
            row = conn.execute("SELECT id, global_id, position, status FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d is not in jog queue" % gh_num)
            if row["status"] not in ("pending", "running"):
                refuse("jog-terminal", "GH-%d is %s; retry or re-add it first" % (gh_num, row["status"]))
            cur_pos = row["position"]
            if cur_pos == 1:
                return
            conn.execute("UPDATE jog_queue SET position = position + 1 WHERE repo_id = ? AND status IN ('pending', 'running') AND position < ?",
                         (repo["id"], cur_pos))
            conn.execute("UPDATE jog_queue SET position = 1, updated_at = ? WHERE id = ?", (now_iso(), row["id"]))

        perform_write(root, conn, "jog-bump", "GH-%d" % gh_num, mutate)
        print("jog: bumped GH-%d to position 1" % gh_num)
    finally:
        conn.close()


def cmd_jog_drop(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gh_num = resolve_issue_number(args.target)

        if args.dry_run:
            print("jog drop: would drop GH-%d with reason: %s" % (gh_num, args.reason))
            return

        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")
            row = conn.execute("SELECT id, position, status FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d is not in jog queue" % gh_num)
            if row["status"] == "completed" and not getattr(args, "force", False):
                refuse("jog-already-completed", "GH-%d is already completed (pass --force to drop anyway)" % gh_num)
            cur_pos = row["position"]
            conn.execute("""UPDATE jog_queue SET status = 'dropped', failure_reason = ?, lease_pid = NULL,
                            updated_at = ? WHERE id = ?""", (args.reason, now_iso(), row["id"]))
            conn.execute("UPDATE jog_queue SET position = position - 1 WHERE repo_id = ? AND status IN ('pending', 'running') AND position > ?",
                         (repo["id"], cur_pos))

        perform_write(root, conn, "jog-drop", "GH-%d" % gh_num, mutate)
        print("jog: dropped GH-%d (reason: %s)" % (gh_num, args.reason))
    finally:
        conn.close()


def cmd_jog_retry(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gh_num = resolve_issue_number(args.target)

        if args.dry_run:
            print("jog retry: would reset GH-%d to pending" % gh_num)
            return

        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")
            row = conn.execute("SELECT id FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d is not in jog queue" % gh_num)
            max_pos = conn.execute("SELECT MAX(position) FROM jog_queue WHERE repo_id = ? AND status IN ('pending', 'running')",
                                   (repo["id"],)).fetchone()[0]
            new_pos = (max_pos or 0) + 1
            conn.execute("""UPDATE jog_queue SET status = 'pending', position = ?, lease_pid = NULL,
                            failure_reason = NULL, updated_at = ? WHERE id = ?""",
                         (new_pos, now_iso(), row["id"]))

        perform_write(root, conn, "jog-retry", "GH-%d" % gh_num, mutate)
        print("jog: reset GH-%d to pending" % gh_num)
    finally:
        conn.close()


def cmd_jog_skip(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        gh_num = resolve_issue_number(args.target)

        if args.dry_run:
            print("jog skip: would park GH-%d with reason: %s" % (gh_num, args.reason))
            return

        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "the DB has no repos row; run `releases init` first")
            row = conn.execute("SELECT id, position FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d is not in jog queue" % gh_num)
            cur_pos = row["position"]
            conn.execute("""UPDATE jog_queue SET status = 'parked', failure_reason = ?, lease_pid = NULL,
                            updated_at = ? WHERE id = ?""", (args.reason, now_iso(), row["id"]))
            conn.execute("UPDATE jog_queue SET position = position - 1 WHERE repo_id = ? AND status IN ('pending', 'running') AND position > ?",
                         (repo["id"], cur_pos))

        perform_write(root, conn, "jog-skip", "GH-%d" % gh_num, mutate)
        print("jog: skipped GH-%d (status: parked)" % gh_num)
    finally:
        conn.close()


def cmd_jog_clear(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if args.dry_run:
            print("jog clear: would archive terminal items in jog queue")
            return

        def mutate(conn):
            _ensure_jog_schema(conn)
            conn.execute("""UPDATE jog_queue SET status = 'archived', updated_at = ?
                            WHERE status IN ('completed', 'dropped', 'parked', 'failed')""", (now_iso(),))

        perform_write(root, conn, "jog-clear", "jog_queue", mutate)
        print("jog: archived terminal queue items")
    finally:
        conn.close()


def cmd_jog_to_marathon(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if not _table_exists(conn, "jog_queue"):
            print("No active jog items.")
            return
        rows = conn.execute("SELECT gh_number FROM jog_queue WHERE status IN ('pending', 'running') ORDER BY position").fetchall()
        issues = ["GH-%d" % r["gh_number"] for r in rows]
        if issues:
            print(" ".join(issues))
        else:
            print("No active jog items.")
    finally:
        conn.close()


def jog_acquire_lease(root, gh_num, pid):
    """Acquire a lease on an enqueued item via perform_write (receipt-backed)."""
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "no repos row")
            row = conn.execute("SELECT id, status, attempt_count FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d not in jog queue" % gh_num)
            ts = now_iso()
            att = row["attempt_count"] + 1
            conn.execute("""UPDATE jog_queue SET status = 'running', lease_pid = ?, attempt_count = ?, updated_at = ?
                            WHERE id = ?""", (pid, att, ts, row["id"]))

        perform_write(root, conn, "jog-lease", "GH-%d" % gh_num, mutate)
    finally:
        conn.close()


def jog_set_status(root, gh_num, status, failure_reason=None, clear_lease=True):
    """Transition a jog queue item to a new status via perform_write (receipt-backed)."""
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        def mutate(conn):
            _ensure_jog_schema(conn)
            repo = conn.execute("SELECT id FROM repos ORDER BY id LIMIT 1").fetchone()
            if not repo:
                refuse("no-repo", "no repos row")
            row = conn.execute("SELECT id, position FROM jog_queue WHERE repo_id = ? AND gh_number = ?",
                               (repo["id"], gh_num)).fetchone()
            if not row:
                refuse("jog-not-found", "GH-%d not in jog queue" % gh_num)
            ts = now_iso()
            pid_clause = ", lease_pid = NULL" if clear_lease else ""
            conn.execute(f"""UPDATE jog_queue SET status = ?, failure_reason = ?, updated_at = ?{pid_clause}
                            WHERE id = ?""", (status, failure_reason, ts, row["id"]))
            if status in ("completed", "dropped", "archived", "parked", "failed"):
                conn.execute("""UPDATE jog_queue SET position = position - 1
                                WHERE repo_id = ? AND status IN ('pending', 'running') AND position > ?""",
                             (repo["id"], row["position"]))

        perform_write(root, conn, f"jog-{status}", "GH-%d" % gh_num, mutate)
    finally:
        conn.close()


def jog_reconcile_orphan_leases(root):
    """Inspect and reconcile orphan running rows whose lease_pid is dead via perform_write."""
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    try:
        if not _table_exists(conn, "jog_queue"):
            return []
        rows = conn.execute("SELECT id, gh_number, attempt_count, lease_pid FROM jog_queue WHERE status = 'running'").fetchall()
        orphans = []
        for r in rows:
            pid = r["lease_pid"]
            alive = False
            if pid and isinstance(pid, int):
                try:
                    os.kill(pid, 0)
                    alive = True
                except OSError:
                    pass
            if not alive:
                orphans.append(r)

        if not orphans:
            return []

        def mutate(conn):
            ts = now_iso()
            for r in orphans:
                att = r["attempt_count"]
                if att >= 3:
                    conn.execute("""UPDATE jog_queue SET status = 'parked', failure_reason = 'orphan lease: max attempts exceeded',
                                    lease_pid = NULL, updated_at = ? WHERE id = ?""", (ts, r["id"]))
                else:
                    conn.execute("""UPDATE jog_queue SET status = 'pending', lease_pid = NULL, updated_at = ?
                                    WHERE id = ?""", (ts, r["id"]))

        perform_write(root, conn, "jog-reconcile", "jog_queue", mutate)
        return [r["gh_number"] for r in orphans]
    finally:
        conn.close()


def cmd_jog_run(args):
    """Execute the serial jog queue supervisor."""
    try:
        from jog_run import jog_run_main
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from jog_run import jog_run_main
    jog_run_main(args)


def _jog_verb_dispatch(fn_name):
    """GH-280 Phase 3 verb dispatch: shared root/target resolution, then delegate to jog_run."""
    def handler(args):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import jog_run
        root = resolve_root(getattr(args, "root", None))
        gh_num = resolve_issue_number(args.target)
        sys.exit(getattr(jog_run, fn_name)(root, gh_num, args))
    return handler


def cmd_jog_resume(args):
    _jog_verb_dispatch("jog_resume")(args)


def cmd_jog_retry_gate(args):
    _jog_verb_dispatch("jog_retry_gate")(args)


def cmd_jog_retry_build(args):
    _jog_verb_dispatch("jog_retry_build")(args)


def cmd_jog_land(args):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import jog_run
    root = resolve_root(getattr(args, "root", None))
    gh_num = resolve_issue_number(args.target)
    sys.exit(jog_run.jog_land(root, gh_num, getattr(args, "pr", None)))




def cmd_gen(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    conn = connect(paths["db"])
    lock = WriterLock(root)
    lock.acquire()
    try:
        if os.path.exists(lock.journal_path):
            refuse("journal-live", "run `releases check` to recover the interrupted write first")
        generation = get_generation(conn)
        _atomic_write(paths["gen"], gen_marker(generation) + "\n" + render_ledger(conn))
        write_drift_report(root, conn)
        print("generated %s (side-by-side, generation %d) + drift report %s"
              % (paths["gen"], generation, paths["drift"]))
        print("NOTE: Phase 0 is side-by-side ONLY — %s is never written by this tool"
              % LEDGER_NAME)
    finally:
        lock.release()
        conn.close()


# ── check ───────────────────────────────────────────────────────────────────────────────────────

def _parse_reanchor_breaks(target_gid):
    """Extract re-anchored break count from a merge-rebuild receipt's target_gid (GH-360).
    Returns int count for canonical 'reanchor:N', None if target_gid is NULL (legacy un-scoped rebuild),
    or -1 for any non-NULL malformed/non-canonical target_gid.
    """
    if target_gid is None:
        return None
    if not isinstance(target_gid, str):
        return -1
    m = re.fullmatch(r"reanchor:(\d+)", target_gid)
    if m:
        return int(m.group(1))
    return -1


def cmd_check(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    lock = WriterLock(root)
    lock.acquire()
    failures, warnings = [], []

    def fail(rule, detail):
        failures.append(rule)
        print("FAIL: rule=%s: %s" % (rule, detail))

    try:
        if not os.path.exists(paths["db"]):
            refuse("not-initialized", "no %s here; run `releases init` first" % DB_NAME)

        # Stale sqlite artifacts (PRD Git story 5). Under our protocol an intent journal ALWAYS
        # precedes BEGIN, so a hot -journal/-wal with no live journal means an out-of-protocol
        # writer — fail loudly; no new write proceeds over a dirty state.
        stale = [p for p in (paths["db"] + "-wal", paths["db"] + "-journal") if os.path.exists(p)]
        journal_live = os.path.exists(lock.journal_path)
        if stale and not journal_live:
            fail("stale-artifact",
                 "leftover %s with no live intent journal — a writer bypassed the protocol or "
                 "crashed outside it; inspect before writing"
                 % ", ".join(os.path.basename(p) for p in stale))

        if journal_live:
            conn = connect(paths["db"])
            try:
                outcome = recover_from_journal(root, conn)
            finally:
                conn.close()
            if outcome:
                kind, txn = outcome
                print("RECOVERED: %s crash (txn %s) — %s" % (
                    kind, txn[:12],
                    "the DB never changed; staged remnants discarded" if kind == "discarded"
                    else "the committed operation is preserved; dump/generated regenerated from "
                         "the DB"))
                print("OK: crash recovery completed; continuing the consistency checks")

        conn = connect(paths["db"])
        try:
            if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                fail("foreign-keys-pragma",
                     "connection could not assert PRAGMA foreign_keys=ON")
            else:
                print("OK: foreign_keys pragma asserted per connection")

            db_gen = get_generation(conn)

            dump_ok = False
            if os.path.exists(paths["dump"]):
                with open(paths["dump"], encoding="utf-8") as fh:
                    dump_content = fh.read()
                dump_gen = dump_generation_from_text(dump_content)
                if dump_gen != db_gen:
                    fail("generation-mismatch",
                         "settings.generation=%d but %s says %s — write in progress, crashed, or "
                         "a torn trio" % (db_gen, DUMP_NAME, dump_gen))
                elif dump_content != dump_text(conn, db_gen):
                    if not args.rebuild:
                        fail("dump-divergence",
                             "%s does not equal the canonical dump of the DB; recovery is "
                             "`releases check --rebuild` (merge resolution ONLY — never crash "
                             "recovery)" % DUMP_NAME)
                else:
                    dump_ok = True
            else:
                fail("dump-missing", "no %s committed alongside the DB" % DUMP_NAME)
            if dump_ok:
                print("OK: generation trio consistent at %d (DB <-> dump)" % db_gen)

            if os.path.exists(paths["gen"]):
                with open(paths["gen"], encoding="utf-8") as fh:
                    first = fh.readline().strip()
                m = GEN_MARKER_RE.match(first)
                gen_file_gen = int(m.group(1)) if m else None
                if gen_file_gen != db_gen:
                    fail("generation-mismatch",
                         "%s carries generation %s but the DB is at %d — regenerate with "
                         "`releases gen`" % (GEN_NAME, gen_file_gen, db_gen))
                else:
                    print("OK: %s generation marker matches (%d)" % (GEN_NAME, db_gen))

            # receipt chain (r3): before == previous after. A git branch switch, rebase, or divergent-dump
            # merge legitimately forks the receipt chain between operations. The merge-rebuild receipt
            # records that re-anchored fork point and scopes it to the specific breaks present at rebuild
            # time (GH-360). A break with no matching merge-rebuild receipt is caught here and can be
            # re-anchored via `releases check --rebuild`. The latest after must equal the current
            # business-state digest regardless — that is what catches a receipt-less direct write
            # (detected, not prevented).
            receipts = conn.execute("""SELECT op, txn_id, target_gid, state_digest_before,
                                              state_digest_after
                                       FROM op_receipts WHERE op != 'ship-evidence'
                                       ORDER BY id""").fetchall()
            chain_ok = True
            breaks = 0
            tolerated_breaks = 0
            prev_after = None
            for r in receipts:
                if prev_after is not None and r["state_digest_before"] != prev_after:
                    breaks += 1
                if r["op"] == "merge-rebuild":
                    scoped = _parse_reanchor_breaks(r["target_gid"])
                    if scoped == -1:
                        fail("malformed-reanchor-receipt",
                             "merge-rebuild receipt carries unparseable target_gid %r — "
                             "expected 'reanchor:N' or NULL" % r["target_gid"])
                        chain_ok = False
                    elif scoped is not None:
                        tolerated_breaks = scoped
                    else:
                        # Legacy merge-rebuild receipt with NULL target_gid tolerates breaks up to this point
                        tolerated_breaks = breaks
                prev_after = r["state_digest_after"]

            if breaks > tolerated_breaks:
                unreanchored = breaks - tolerated_breaks
                if tolerated_breaks == 0:
                    fail("receipt-chain",
                         "%d receipt(s) break the chain (before != previous after) with no "
                         "merge-rebuild receipt — likely caused by git branch switching or "
                         "rebasing; run `releases check --rebuild` to re-anchor" % breaks)
                else:
                    fail("receipt-chain",
                         "%d new receipt(s) break the chain (%d total break(s), %d re-anchored) — "
                         "likely caused by git branch switching or rebasing; run "
                         "`releases check --rebuild` to re-anchor"
                         % (unreanchored, breaks, tolerated_breaks))
                chain_ok = False
            digest = business_digest(conn)
            if receipts and receipts[-1]["state_digest_after"] != digest:
                fail("receipt-chain",
                     "latest receipt's after-digest != current business-state digest — a "
                     "receipt-less mutation (a direct write that bypassed the CLI) is caught "
                     "here, not prevented")
                chain_ok = False
            if chain_ok:
                note = (", %d merge fork(s) tolerated under the merge-rebuild receipt" % breaks
                        if breaks else "")
                print("OK: receipt chain intact (%d receipt(s), business-state digest matches%s)"
                      % (len(receipts), note))

            # temp-ref staleness (SOP 3): warn on placeholders older than 7 days (mocked clock).
            try:
                now_dt = _dt.datetime.fromisoformat(now_iso().replace("Z", "+00:00"))
            except ValueError:
                now_dt = _dt.datetime.now(_dt.timezone.utc)
            for r in conn.execute("""SELECT temp_id, created_at FROM issue_refs
                                     WHERE temp_id IS NOT NULL"""):
                try:
                    created = _dt.datetime.fromisoformat(
                        (r["created_at"] or "").replace("Z", "+00:00"))
                except ValueError:
                    continue
                age_days = (now_dt - created).total_seconds() / 86400.0
                if age_days > 7:
                    is_tmp = (r["temp_id"] or "").startswith("TMP-")
                    warn("temp-ref-stale" if is_tmp else "mig-ref-stale",
                         "%s is %.0f days old (> 7) — %s" % (
                             r["temp_id"], age_days,
                             "reconcile the real URL when GitHub returns" if is_tmp else
                             "disposition the migration debt before the strict flip"))
                    warnings.append("stale-ref")

            # duplication warnings (light-touch guard; these warn, never refuse)
            for r in conn.execute("""SELECT codename, COUNT(*) c FROM releases
                                     WHERE version IS NULL AND codename IS NOT NULL
                                     GROUP BY repo_id, codename HAVING c > 1"""):
                warn("unversioned-codename-dup",
                     "%d unversioned releases share codename %r in one repo (the version-unique "
                     "guarantee covers versioned releases only)" % (r["c"], r["codename"]))
                warnings.append("unversioned-codename-dup")
            for r in conn.execute("""SELECT t.global_id, COUNT(DISTINCT mi.release_id) c
                                     FROM manifest_items mi
                                     JOIN issue_refs t ON t.id = mi.issue_ref_id
                                     WHERE mi.state != 'cut'
                                     GROUP BY t.id HAVING c > 1"""):
                warn("shared-manifest-issue",
                     "issue ref %s sits in %d non-cut releases (handoffs are legitimate)"
                     % (r["global_id"], r["c"]))
                warnings.append("shared-manifest-issue")

            # target-date advisories (warn-only, never refuse).
            #
            # `ship` is deliberately a human verb — it requires evidence, and nothing should be
            # able to declare a release shipped on its own. The cost of that design is that a
            # release whose exit criterion is already satisfied can sit `active` indefinitely with
            # nobody noticing: 0.7.1 Bulwark did exactly that for a day while its own merge and all
            # three manifest items were already closed. This does not fix the design (it shouldn't)
            # — it removes the silence. Purely local arithmetic on the stored target date; no
            # network call, no GitHub read, so `check` stays offline and fast.
            today = now_dt.date()
            for r in conn.execute("""SELECT version, codename, status, target_date FROM releases
                                     WHERE status IN ('active','draft') AND target_date IS NOT NULL
                                     ORDER BY target_date"""):
                try:
                    target = _dt.date.fromisoformat(r["target_date"])
                except (ValueError, TypeError):
                    continue  # malformed dates are the schema's problem, not this advisory's
                if target >= today:
                    continue
                overdue = (today - target).days
                label = "%s %s" % (r["version"] or "(unversioned)", r["codename"] or "")
                if r["status"] == "active":
                    warn("release-overdue",
                         "%s is active and %d day(s) past its target of %s — if the exit criterion "
                         "is met, `releases ship` it; if not, `releases update` the target"
                         % (label.strip(), overdue, r["target_date"]))
                    warnings.append("release-overdue")
                else:
                    warn("release-target-passed",
                         "%s is still a draft and %d day(s) past its target of %s — the plan has "
                         "drifted from the calendar" % (label.strip(), overdue, r["target_date"]))
                    warnings.append("release-target-passed")

            pending = conn.execute("""SELECT COUNT(*) c FROM grandfather_entries
                                      WHERE disposition IS NULL""").fetchone()["c"]
            print("info: %d grandfather_entries pending disposition (the strict flip requires "
                  "none pending)" % pending)

            if args.rebuild:
                _rebuild(root, conn)
                # the rebuild resolved the consistency-family failures recorded above (they
                # described the PRE-rebuild state); a failed rebuild refused/exited already
                resolved = {"dump-divergence", "dump-missing", "generation-mismatch",
                            "receipt-chain"}
                failures = [f for f in failures if f not in resolved]
                print("OK: post-rebuild verification — DB rebuilt from %s, displaced DB at %s"
                      % (DUMP_NAME, DB_BAK_NAME))
        finally:
            conn.close()
    finally:
        lock.release()

    if failures:
        print("check: %d failure(s), %d warning(s)" % (len(failures), len(warnings)))
        sys.exit(EXIT_CHECK_FAILED)
    print("check: clean (0 failures, %d warning(s))" % len(warnings))


# ── dump parsing (the merge-boundary direction: dump -> DB) ────────────────────────────────────
# The dump is a LOGICAL grammar (GID/natural-keyed, no integer PKs/FKs), so it cannot be
# executescript'd onto the physical schema. load_dump() maps grammar rows back onto physical
# inserts, resolving parent GIDs to fresh integer ids in dump order — the "deterministic
# renumbering on rebuild" the grammar promises.

# re.S: a dumped value may contain newlines (a roadmap_items raw_text, say). parse_dump
# already buffers multi-line statements; without DOTALL the regex could never match one,
# so the buffer swallowed the rest of the file and --rebuild refused with dump-parse.
INSERT_RE = re.compile(r"^INSERT INTO ([a-z_]+)\(([^)]*)\) VALUES\((.*)\);$", re.S)


def _split_values(blob):
    """Split a VALUES(...) blob on top-level commas, honoring '...' quoting with '' escapes."""
    parts, buf, in_str = [], [], False
    i = 0
    while i < len(blob):
        ch = blob[i]
        if in_str:
            buf.append(ch)
            if ch == "'":
                if i + 1 < len(blob) and blob[i + 1] == "'":
                    buf.append("'")
                    i += 1
                else:
                    in_str = False
        else:
            if ch == "'":
                in_str = True
                buf.append(ch)
            elif ch == ",":
                parts.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return [p.strip() for p in parts]


def _value(p):
    if p == "NULL":
        return None
    if p.startswith("'") and p.endswith("'"):
        return p[1:-1].replace("''", "'")
    return p


def parse_dump(text):
    """Parse canonical-dump text into {table: [rowdict,...]} in file order."""
    tables = {}
    buf = ""

    def try_stmt(stmt):
        m = INSERT_RE.match(stmt)
        if not m:
            return False
        table, cols_blob, vals_blob = m.groups()
        cols = [c.strip() for c in cols_blob.split(",")]
        vals = _split_values(vals_blob)
        if len(cols) != len(vals):
            return False
        tables.setdefault(table, []).append(dict(zip(cols, [_value(v) for v in vals])))
        return True

    for line in text.split("\n"):
        if not buf and (not line.strip() or line.lstrip().startswith("--")):
            continue
        buf = (buf + "\n" + line) if buf else line
        if buf.rstrip().endswith(");"):
            if try_stmt(buf.rstrip()):
                buf = ""
    if buf.strip():
        refuse("dump-parse", "unparseable trailing statement in the dump: %r" % buf[:80])
    return tables


def validate_merged_dump(text, tables):
    """Refuse a dump carrying the damage a naive text merge leaves behind (#54).

    A union-style merge of two canonical dumps is ALMOST correct: GID-keyed rows from both sides
    coexist happily, which is the whole point of the grammar. What it also does — measured
    2026-08-19 against real two-branch merges — is duplicate the single-row tables, and, when the
    branches made unequal numbers of writes, keep BOTH `-- generation:` headers with no conflict
    markers to show for it.

    Loading that hits a UNIQUE constraint deep inside load_dump and surfaces as a raw Python
    traceback, which tells the operator nothing about what to fix. Each case is named here instead,
    before anything is written. This runs on the rebuild path only: it is a merge-damage check, not
    a general dump validator."""
    headers = [ln.strip() for ln in text.splitlines()
               if re.match(r"^-- generation: \d+$", ln.strip())]
    if len(headers) > 1:
        refuse("dump-multi-generation",
               "the dump carries %d '-- generation:' headers (%s); a canonical dump has exactly one. "
               "This is what a plain union merge leaves behind when the two branches made a different "
               "number of writes. The rebuild reads only the FIRST one, so accepting this would "
               "silently understate the generation. Keep the HIGHEST header, delete the rest, then "
               "rebuild." % (len(headers), ", ".join(h.split()[-1] for h in headers)))

    # GH-111: two branches that each authored a migration and then union-merged their dumps leave
    # the SAME version number twice in the ledger. Scope this honestly — it catches a merged DUMP,
    # not two source branches that both numbered a migration 003. Source-level collision surfaces
    # as an ordinary releases_app.py merge conflict, and is pinned separately by the ordered
    # v2 -> 003 -> 004 fixture.
    seen_versions = set()
    for row in tables.get("schema_migrations", []):
        version = row.get("version")
        if version in seen_versions:
            refuse("dump-duplicate-migration",
                   "schema_migrations version %s appears more than once. Each migration is applied "
                   "once, so two rows sharing a version means both branches stamped that number — "
                   "the two sides may not even be the same migration. Decide which row is true, "
                   "delete the other, then rebuild." % version)
        seen_versions.add(version)

    seen_keys = set()
    for row in tables.get("settings", []):
        key = row.get("key")
        if key in seen_keys:
            refuse("dump-duplicate-setting",
                   "settings key %r appears more than once. `settings` holds one row per key, so a "
                   "merge that unioned both sides' lines duplicated it. Keep the row that should win "
                   "(for 'generation', the higher value), delete the other, then rebuild." % key)
        seen_keys.add(key)

    for table in sorted(tables):
        seen_gids = set()
        for row in tables[table]:
            gid = row.get("global_id")
            if gid is None:
                continue
            if gid in seen_gids:
                refuse("dump-duplicate-gid",
                       "%s carries global_id %s twice. Global IDs are unique by construction, so two "
                       "rows sharing one means BOTH branches edited the same record — a real content "
                       "conflict that no union can settle. Decide which row wins, delete the other, "
                       "then rebuild." % (table, gid))
            seen_gids.add(gid)


def load_dump(conn, tables, skip_schema_migrations=False):
    """Insert parsed dump rows into the (already-migrated, empty) DB, resolving the grammar's
    natural keys to physical ids in dump order.

    skip_schema_migrations=True is the rebuild path (GH-111). The migration LEDGER is owned by
    exactly one writer there — `_rebuild`, which stamps the registry's versions after this
    returns — so loading the dump's own rows would either collide on the primary key or leave a
    v2 ledger describing a v4 schema. The dump's other tables load normally."""
    def _int_or_none(v):
        return None if v in (None, "") else int(v)

    if not skip_schema_migrations:
        for row in tables.get("schema_migrations", []):
            conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                         (int(row["version"]), row["applied_at"]))
    now = now_iso()
    for row in tables.get("settings", []):
        if _has_column(conn, "settings", "updated_at"):
            conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
                         (row["key"], row["value"], row.get("updated_at") or now))
        else:
            conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)", (row["key"], row["value"]))
    repo_ids = {}
    for row in tables.get("repos", []):
        if _has_column(conn, "repos", "updated_at"):
            cur = conn.execute("INSERT INTO repos(global_id, slug, updated_at) VALUES (?, ?, ?)",
                               (row["global_id"], row["slug"], row.get("updated_at") or now))
        else:
            cur = conn.execute("INSERT INTO repos(global_id, slug) VALUES (?, ?)",
                               (row["global_id"], row["slug"]))
        repo_ids[row["global_id"]] = cur.lastrowid
    ref_ids = {}
    for row in tables.get("issue_refs", []):
        if _has_column(conn, "issue_refs", "updated_at"):
            ref_updated = row.get("updated_at") or row.get("created_at") or now
            cur = conn.execute("""INSERT INTO issue_refs(global_id, url, temp_id, created_at, updated_at)
                                  VALUES (?, ?, ?, ?, ?)""",
                               (row["global_id"], row.get("url"), row.get("temp_id"),
                                row["created_at"], ref_updated))
        else:
            cur = conn.execute("""INSERT INTO issue_refs(global_id, url, temp_id, created_at)
                                  VALUES (?, ?, ?, ?)""",
                               (row["global_id"], row.get("url"), row.get("temp_id"),
                                row["created_at"]))
        ref_ids[row["global_id"]] = cur.lastrowid
    mar_ids = {}
    for row in tables.get("marathons", []):
        if _has_column(conn, "marathons", "updated_at"):
            mar_updated = row.get("updated_at") or row.get("created_at") or now
            cur = conn.execute("""INSERT INTO marathons(global_id, repo_id, tracking_ref_id, status,
                                  created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)""",
                               (row["global_id"], repo_ids[row["repo_gid"]],
                                ref_ids[row["tracking_ref_gid"]], row["status"], row["created_at"],
                                mar_updated))
        else:
            cur = conn.execute("""INSERT INTO marathons(global_id, repo_id, tracking_ref_id, status,
                                  created_at) VALUES (?, ?, ?, ?, ?)""",
                               (row["global_id"], repo_ids[row["repo_gid"]],
                                ref_ids[row["tracking_ref_gid"]], row["status"], row["created_at"]))
        mar_ids[row["global_id"]] = cur.lastrowid
    rel_ids = {}
    for row in tables.get("releases", []):
        if _has_column(conn, "releases", "updated_at"):
            rel_updated = row.get("updated_at") or row.get("shipped_date") or row.get("baseline_at") or now
            cur = conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                                  target_date, shipped_date, description, exit_criterion,
                                  tracking_ref_id, marathon_id, gh_release_url, milestone,
                                  front_door_reviewed, shakedown_reviewed, license_file,
                                  baseline_count, baseline_at, baseline_source, updated_at)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (row["global_id"], repo_ids[row["repo_gid"]], row.get("version"),
                                row.get("codename"), row["status"], row.get("target_date"),
                                row.get("shipped_date"), row["description"], row.get("exit_criterion"),
                                ref_ids[row["tracking_ref_gid"]],
                                mar_ids.get(row["marathon_gid"]) if row.get("marathon_gid") else None,
                                row.get("gh_release_url"), row.get("milestone"),
                                row.get("front_door_reviewed"), row.get("shakedown_reviewed"),
                                row.get("license_file"),
                                _int_or_none(row.get("baseline_count")), row.get("baseline_at"),
                                row.get("baseline_source"), rel_updated))
        else:
            cur = conn.execute("""INSERT INTO releases(global_id, repo_id, version, codename, status,
                                  target_date, shipped_date, description, exit_criterion,
                                  tracking_ref_id, marathon_id, gh_release_url, milestone,
                                  front_door_reviewed, shakedown_reviewed, license_file,
                                  baseline_count, baseline_at, baseline_source)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (row["global_id"], repo_ids[row["repo_gid"]], row.get("version"),
                                row.get("codename"), row["status"], row.get("target_date"),
                                row.get("shipped_date"), row["description"], row.get("exit_criterion"),
                                ref_ids[row["tracking_ref_gid"]],
                                mar_ids.get(row["marathon_gid"]) if row.get("marathon_gid") else None,
                                row.get("gh_release_url"), row.get("milestone"),
                                row.get("front_door_reviewed"), row.get("shakedown_reviewed"),
                                row.get("license_file"),
                                _int_or_none(row.get("baseline_count")), row.get("baseline_at"),
                                row.get("baseline_source")))
        rel_ids[row["global_id"]] = cur.lastrowid
    item_ids = {}
    for row in tables.get("manifest_items", []):
        # `open` is the pre-2026-08-20 name for `dialed_in`. Old dumps stay loadable — they are the
        # git-merge surface, and a colleague's branch may carry one for weeks — but only the new
        # vocabulary is ever emitted.
        state = "dialed_in" if row["state"] == "open" else row["state"]
        if _has_column(conn, "manifest_items", "updated_at"):
            item_updated = row.get("updated_at") or row.get("dialed_in_at") or now
            cur = conn.execute("""INSERT INTO manifest_items(global_id, release_id, issue_ref_id, state,
                                  dialed_in_at, dial_reason, marathon_id, updated_at)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                               (row["global_id"], rel_ids[row["release_gid"]],
                                ref_ids[row["issue_ref_gid"]], state,
                                row.get("dialed_in_at"), row.get("dial_reason"),
                                mar_ids.get(row["marathon_gid"]) if row.get("marathon_gid") else None,
                                item_updated))
        else:
            cur = conn.execute("""INSERT INTO manifest_items(global_id, release_id, issue_ref_id, state,
                                  dialed_in_at, dial_reason, marathon_id)
                                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
                               (row["global_id"], rel_ids[row["release_gid"]],
                                ref_ids[row["issue_ref_gid"]], state,
                                row.get("dialed_in_at"), row.get("dial_reason"),
                                mar_ids.get(row["marathon_gid"]) if row.get("marathon_gid") else None))
        item_ids[row["global_id"]] = cur.lastrowid
    for row in tables.get("manifest_state_events", []):
        conn.execute("""INSERT INTO manifest_state_events(item_id, from_state, to_state, at, reason)
                        VALUES (?, ?, ?, ?, ?)""",
                     (item_ids[row["item_gid"]], row["from_state"], row["to_state"], row["at"],
                      row["reason"]))
    for row in tables.get("doc_lines", []):
        if _has_column(conn, "doc_lines", "updated_at"):
            conn.execute("""INSERT INTO doc_lines(repo_id, position, content, updated_at) VALUES (?, ?, ?, ?)""",
                         (repo_ids[row["repo_gid"]], int(row["position"]), row["content"], row.get("updated_at") or now))
        else:
            conn.execute("""INSERT INTO doc_lines(repo_id, position, content) VALUES (?, ?, ?)""",
                         (repo_ids[row["repo_gid"]], int(row["position"]), row["content"]))
    for row in tables.get("legacy_lines", []):
        if _has_column(conn, "legacy_lines", "updated_at"):
            conn.execute("""INSERT INTO legacy_lines(release_id, position, content, disposition, updated_at)
                            VALUES (?, ?, ?, ?, ?)""",
                         (rel_ids[row["release_gid"]], int(row["position"]), row["content"],
                          row.get("disposition"), row.get("updated_at") or now))
        else:
            conn.execute("""INSERT INTO legacy_lines(release_id, position, content, disposition)
                            VALUES (?, ?, ?, ?)""",
                         (rel_ids[row["release_gid"]], int(row["position"]), row["content"],
                          row.get("disposition")))
    for row in tables.get("grandfather_entries", []):
        rgid = row.get("release_gid")
        if rgid in ("(document)", ""):
            rgid = None
        elif rgid is not None and not rgid.startswith("rel-"):
            rgid = None   # tolerate older shapes; the (document) marker is the contract
        if _has_column(conn, "grandfather_entries", "updated_at"):
            conn.execute("""INSERT INTO grandfather_entries(import_run, release_gid, rule, source_value,
                            supplied_value, disposition, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (row["import_run"], rgid, row["rule"], row.get("source_value"),
                          row.get("supplied_value"), row.get("disposition"), row.get("updated_at") or now))
        else:
            conn.execute("""INSERT INTO grandfather_entries(import_run, release_gid, rule, source_value,
                            supplied_value, disposition) VALUES (?, ?, ?, ?, ?, ?)""",
                         (row["import_run"], rgid, row["rule"], row.get("source_value"),
                          row.get("supplied_value"), row.get("disposition")))
    for row in tables.get("roadmap_items", []):
        conn.execute("""INSERT INTO roadmap_items(global_id, repo_id, gh_number, title, section,
                        position, status_marker, complexity, risk, effort, doc_path, issue_url,
                        raw_text, first_seen, updated_at,
                        rating_pri, rating_sev, rating_appeal, rating_effort, rating_ovr)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (row["global_id"], repo_ids[row["repo_gid"]], _int_or_none(row.get("gh_number")),
                      row["title"], row["section"], int(row["position"]),
                      row.get("status_marker"), _int_or_none(row.get("complexity")),
                      _int_or_none(row.get("risk")), _int_or_none(row.get("effort")),
                      row.get("doc_path"), row.get("issue_url"), row["raw_text"],
                      row["first_seen"], row["updated_at"],
                      *[_int_or_none(row.get(c)) for c in RATING_COLUMNS]))
    for row in tables.get("jog_queue", []):
        conn.execute("""INSERT INTO jog_queue(global_id, repo_id, gh_number, position, status,
                        created_at, updated_at, attempt_count, lease_pid, failure_reason)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (row["global_id"], repo_ids[row["repo_gid"]], int(row["gh_number"]),
                      int(row["position"]), row["status"], row["created_at"], row["updated_at"],
                      int(row.get("attempt_count") or 0),
                      _int_or_none(row.get("lease_pid")), row.get("failure_reason")))
    for row in tables.get("op_receipts", []):

        conn.execute("""INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id,
                        state_digest_before, state_digest_after) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (row["op"], row.get("target_gid"), row["at"], row["txn_id"],
                      row["session_id"], row["state_digest_before"], row["state_digest_after"]))


def _rebuild(root, conn):
    """`check --rebuild`: dump -> DB, atomic, with a .bak of the displaced DB. MERGE RESOLUTION
    ONLY (PRD) — crash recovery is the journal protocol, and a live journal is refused here. A
    merge legitimately forks the receipt chain (both sides branch from one ancestor), so the
    rebuild appends a merge-rebuild receipt — the one legal fork point in the chain rule."""
    paths = artifact_paths(root)
    _, _, journal_path = lock_paths(root)
    if os.path.exists(journal_path):
        refuse("journal-live",
               "recover the interrupted write with plain `releases check` first; --rebuild is "
               "for git-merge resolution only, never crash recovery")
    if not os.path.exists(paths["dump"]):
        refuse("dump-missing", "nothing to rebuild from")
    with open(paths["dump"], encoding="utf-8") as fh:
        dump_content = fh.read()
    dump_gen = dump_generation_from_text(dump_content)
    if dump_gen is None:
        refuse("dump-generation", "%s carries no generation header — not a canonical dump"
               % DUMP_NAME)

    old_digest = business_digest(conn)
    old_gen = get_generation(conn)
    new_gen = max(dump_gen, old_gen) + 1

    tmp_db = "%s.rebuild-%s" % (paths["db"], new_txn_id()[:12])
    try:
        tconn = sqlite3.connect(tmp_db, isolation_level=None)
        try:
            tconn.row_factory = sqlite3.Row
            tconn.execute("PRAGMA foreign_keys = ON")
            # GH-111 — ONE rule, three steps, so DDL and ledger agree by construction:
            #   1. materialize DDL for the versions THE REGISTRY defines (never a hard-coded
            #      range), writing no ledger rows;
            #   2. load everything from the dump EXCEPT its schema_migrations records;
            #   3. stamp exactly those same registry versions, ascending.
            # A GH-111-first build therefore materializes and stamps {1, 2, 4} and never claims 3.
            # Pre-stamping and then loading a v2 dump's rows would collide on the primary key;
            # deferring to the dump would leave a v2 ledger describing a v4 schema.
            apply_migrations(tconn, stamp_ledger=False)
            parsed = parse_dump(dump_content)
            # #54: name the merge damage BEFORE loading. Without this the duplicate rows a union
            # merge leaves surface as a bare sqlite3.IntegrityError traceback from inside load_dump.
            validate_merged_dump(dump_content, parsed)
            try:
                load_dump(tconn, parsed, skip_schema_migrations=True)
            except sqlite3.IntegrityError as exc:
                # backstop for damage validate_merged_dump does not yet name: still a refusal with a
                # rule and a pointer, never a traceback.
                refuse("dump-load",
                       "the dump could not be loaded: %s. This usually means the merged dump "
                       "contains a row twice, or a reference to a row that is not in it. Fix "
                       "%s and rebuild; the live DB has not been touched." % (exc, DUMP_NAME))
            # Step 3: stamp exactly the registry's versions. Each keeps the dump's own applied_at
            # where the dump had it — the ledger row is business state that feeds the digest, so
            # restamping an unchanged migration with "now" would make every rebuild look like a
            # content change. Versions the dump did NOT carry are genuinely new here and take the
            # current time, which is the honest record of when this schema actually arrived.
            dump_applied = {int(r["version"]): r["applied_at"]
                            for r in parsed.get("schema_migrations", [])}
            stamped_at = now_iso()
            for version in registry_versions():
                tconn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                              (version, dump_applied.get(version, stamped_at)))
            if _has_column(tconn, "settings", "updated_at"):
                tconn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                              (str(new_gen), stamped_at, GENERATION_KEY))
                if tconn.execute("SELECT 1 FROM settings WHERE key = ?",
                                 (GENERATION_KEY,)).fetchone() is None:
                    tconn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
                                  (GENERATION_KEY, str(new_gen), stamped_at))
            else:
                tconn.execute("UPDATE settings SET value = ? WHERE key = ?",
                              (str(new_gen), GENERATION_KEY))
                if tconn.execute("SELECT 1 FROM settings WHERE key = ?",
                                 (GENERATION_KEY,)).fetchone() is None:
                    tconn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
                                  (GENERATION_KEY, str(new_gen)))
            new_receipts = tconn.execute("""SELECT op, state_digest_before, state_digest_after
                                           FROM op_receipts WHERE op != 'ship-evidence'
                                           ORDER BY id""").fetchall()
            reanchored_breaks = 0
            prev_after = None
            for r in new_receipts:
                if prev_after is not None and r["state_digest_before"] != prev_after:
                    reanchored_breaks += 1
                prev_after = r["state_digest_after"]
            if prev_after is not None and old_digest != prev_after:
                reanchored_breaks += 1

            new_digest = business_digest(tconn)
            reanchor_gid = "reanchor:%d" % reanchored_breaks
            tconn.execute("""INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id,
                             state_digest_before, state_digest_after)
                             VALUES ('merge-rebuild', ?, ?, ?, ?, ?, ?)""",
                          (reanchor_gid, now_iso(), new_txn_id(), session_id(), old_digest, new_digest))
        finally:
            tconn.close()
        probe = connect(tmp_db)   # FK pragma + openability of the rebuilt DB, before it goes live
        probe.close()
    except BaseException:
        try:
            os.unlink(tmp_db)
        except OSError:
            pass
        raise

    shutil.copy2(paths["db"], paths["bak"])
    os.replace(tmp_db, paths["db"])
    conn.close()
    fresh = connect(paths["db"])
    try:
        _atomic_write(paths["dump"], dump_text(fresh, new_gen))
        if os.path.exists(paths["gen"]):
            _atomic_write(paths["gen"], gen_marker(new_gen) + "\n" + render_ledger(fresh))
    finally:
        fresh.close()
    print("rebuilt %s from %s (generation %d -> %d); displaced DB backed up at %s"
          % (DB_NAME, DUMP_NAME, old_gen, new_gen, paths["bak"]))

def cmd_dashboard(args):
    root = resolve_root(args.root)
    paths = artifact_paths(root)
    db_path = paths["db"]
    
    if not os.path.exists(db_path):
        refuse("not-initialized", "no %s here" % DB_NAME)

    # read-only connection
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    conn.row_factory = sqlite3.Row

    try:
        # Trust header info
        db_gen = get_generation(conn)
        receipts = conn.execute("SELECT COUNT(*) FROM op_receipts").fetchone()[0]
        
        # Staleness: dump vs DB
        dump_path = paths["dump"]
        dump_gen = -1
        if os.path.exists(dump_path):
            with open(dump_path, "r", encoding="utf-8") as f:
                dump_gen = dump_generation_from_text(f.read())
        
        staleness_banner = ""
        if dump_gen != db_gen:
            staleness_banner = "<div style='background: red; color: white; padding: 10px; font-weight: bold;'>STALE SYNC: DB generation (%d) != Dump generation (%d)</div>" % (db_gen, dump_gen)
            
        # Releases panel
        releases = conn.execute("""
            SELECT version, codename, status, target_date, shipped_date, description, exit_criterion, id
            FROM releases ORDER BY target_date IS NULL, target_date, version
        """).fetchall()

        releases_html = "<h2>Releases</h2><div style='display: flex; gap: 1rem; overflow-x: auto;'>"
        for r in releases:
            open_items = conn.execute("SELECT COUNT(*) FROM manifest_items WHERE release_id = ? AND state != 'cut' AND state != 'shipped'", (r["id"],)).fetchone()[0]
            closed_items = conn.execute("SELECT COUNT(*) FROM manifest_items WHERE release_id = ? AND state = 'shipped'", (r["id"],)).fetchone()[0]
            
            # calculate days to target
            target = r["target_date"]
            days_str = ""
            if target:
                try:
                    today = _dt.date.today()
                    t_date = _dt.date.fromisoformat(target)
                    delta = (t_date - today).days
                    days_str = " | %d days %s" % (abs(delta), 'overdue' if delta < 0 else 'to target')
                except ValueError:
                    pass
            
            releases_html += f"""
            <div style='border: 1px solid #ccc; padding: 1rem; min-width: 250px;'>
                <h3>{r['version'] or ''} {r['codename'] or ''}</h3>
                <p>Status: {r['status']}{days_str}</p>
                <p>Manifest: {open_items} open / {closed_items} closed</p>
                <p>Exit: {r['exit_criterion'] or 'None'}</p>
            </div>
            """
        releases_html += "</div>"

        # Roadmap panel
        roadmap_items = conn.execute("""
            SELECT section, gh_number, title, status_marker 
            FROM roadmap_items 
            ORDER BY position
        """).fetchall()
        
        roadmap_by_section = {}
        for item in roadmap_items:
            roadmap_by_section.setdefault(item["section"], []).append(item)
            
        roadmap_html = "<h2>Roadmap</h2>"
        for section, items in roadmap_by_section.items():
            roadmap_html += f"<h3>{section}</h3><ul>"
            for i in items:
                gh = f"GH-{i['gh_number']} " if i['gh_number'] else ""
                roadmap_html += f"<li>{i['status_marker'] or ''} {gh}{i['title']}</li>"
            roadmap_html += "</ul>"

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Releases Dashboard</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h1>Releases Dashboard</h1>
    <div style='background: #eee; padding: 10px; margin-bottom: 20px;'>
        <strong>Trust Header</strong> | Generation: {db_gen} | Receipts: {receipts}
    </div>
    {staleness_banner}
    {releases_html}
    <hr>
    {roadmap_html}
</body>
</html>
"""
        print(html)
    finally:
        conn.close()


def cmd_reconcile(args):
    root = resolve_root(args.root)
    conn = connect(artifact_paths(root)["db"])
    try:
        if not args.map:
            refuse("reconcile-map", "pass --map TMP-XXXXXX=<url> (repeatable)")

        def mutate(conn):
            for pair in args.map:
                if "=" not in pair:
                    refuse("reconcile-map", "--map expects TMP-XXXXXX=<url>, got %r" % pair)
                temp, url = pair.split("=", 1)
                temp, url = temp.strip(), url.strip()
                if not (TMP_RE.match(temp) or MIG_RE.match(temp)):
                    refuse("reconcile-map",
                           "--map key %r must be a TMP-XXXXXX or MIG-XXXXXX placeholder" % temp)
                if not GH_ISSUE_URL_RE.match(url):
                    refuse("issue-url-shape",
                           "mapped URL %r must be https://github.com/<org>/<repo>/issues/<n>"
                           % url)
                row = conn.execute("SELECT * FROM issue_refs WHERE temp_id = ?",
                                   (temp,)).fetchone()
                if not row:
                    refuse("unknown-temp-ref", "no issue_refs row carries temp id %r" % temp)
                now = now_iso()
                if _has_column(conn, "issue_refs", "updated_at"):
                    conn.execute("UPDATE issue_refs SET url = ?, temp_id = NULL, updated_at = ? WHERE id = ?",
                                 (url, now, row["id"]))
                else:
                    conn.execute("UPDATE issue_refs SET url = ?, temp_id = NULL WHERE id = ?",
                                 (url, row["id"]))
                if temp.startswith("MIG-"):
                    if _has_column(conn, "grandfather_entries", "updated_at"):
                        conn.execute("""UPDATE grandfather_entries SET disposition = ?, updated_at = ?
                                     WHERE rule = 'tracking-issue-missing' AND supplied_value = ?
                                       AND disposition IS NULL""",
                                     ("reconciled:%s" % now, now, temp))
                    else:
                        conn.execute("""UPDATE grandfather_entries SET disposition = ?
                                     WHERE rule = 'tracking-issue-missing' AND supplied_value = ?
                                       AND disposition IS NULL""",
                                     ("reconciled:%s" % now, temp))
                print("reconciled %s -> %s (row %s kept its identity)"
                      % (temp, url, row["global_id"]))

        perform_write(root, conn, "reconcile", None, mutate)
    finally:
        conn.close()


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(prog="releases",
                                 description="GH-32 SQLite-backed RELEASES ledger CLI "
                                             "(Phase 0+1: side-by-side generation only)")
    p.add_argument("--root", help="repo root (default: git toplevel of the CWD)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="create the DB + dump; settings default lenient")
    sp.add_argument("--slug", help="repo slug (default: root directory basename)")

    sp = sub.add_parser("import", help="ONE-SHOT legacy ledger import (Phase 0)")
    sp.add_argument("file", nargs="?",
                    help="path to the legacy RELEASES.md (default: <root>/RELEASES.md)")

    sp = sub.add_parser("add", help="add a release (validated write)")
    for flag in ("--version", "--codename", "--target-date", "--shipped-date", "--description",
                 "--exit-criterion", "--milestone", "--gh-release-url", "--marathon"):
        sp.add_argument(flag)
    sp.add_argument("--status", required=True, choices=STATUSES)
    for flag in ("--front-door", "--shakedown", "--license"):
        sp.add_argument(flag, choices=["Yes", "No"])
    sp.add_argument("--tracking-issue", required=True,
                    help="issue URL or TMP-XXXXXX (GitHub-down fallback)")

    sp = sub.add_parser("update", help="update a release by --gid")
    sp.add_argument("--gid", required=True)
    for flag in ("--version", "--codename", "--status", "--target-date", "--shipped-date",
                 "--description", "--exit-criterion", "--milestone", "--gh-release-url"):
        sp.add_argument(flag)
    for flag in ("--front-door", "--shakedown", "--license"):
        sp.add_argument(flag, choices=["Yes", "No"])
    sp.add_argument("--tracking-issue", metavar="N|URL",
                    help="GH-222: re-point the tracking issue (bare number expands against the "
                         "org/repo slug or the github origin remote; the new URL is stored "
                         "canonically like `add`)")

    sp = sub.add_parser("migrate",
                        help="upgrade a LIVE ledger to the registry's schema version "
                             "(idempotent; feature commands never self-migrate)")

    sp = sub.add_parser("baseline",
                        help="capture a release's kickoff commitment count (write-once)")
    sp.add_argument("--gid", required=True)

    sp = sub.add_parser("ship", help="mark a release shipped, with evidence")
    sp.add_argument("--gid", required=True)
    sp.add_argument("--evidence", default="",
                    help="exit-criterion run cite (REQUIRED — an empty value is refused with rule=ship-needs-evidence)")
    sp.add_argument("--date", help="shipped date (default: today)")

    sp = sub.add_parser("manifest", help="manifest items")
    msub = sp.add_subparsers(dest="manifest_cmd", required=True)
    # GH-111: `dial-in` is the verb; `add` stays as a back-compatible alias so existing scripts
    # and the vendored payload keep working while the vocabulary moves.
    for _name, _help in (("dial-in", "dial an issue into a release (one release at a time)"),
                         ("add", "alias for dial-in (pre-GH-111 name)")):
        _p = msub.add_parser(_name, help=_help)
        _p.add_argument("--gid", required=True)
        _p.add_argument("issue", help="issue URL or TMP-XXXXXX")
        _p.add_argument("--reason", default=None,
                        help="the case for committing this task to this release")
        _p.add_argument("--marathon", default=None,
                        help="marathon gid; must be THIS release's marathon")
    sp_ship = msub.add_parser("ship",
                              help="mark a dialed-in item shipped (REQUIRES --evidence)")
    sp_ship.add_argument("--gid", required=True)
    sp_ship.add_argument("issue", help="issue URL or TMP-XXXXXX")
    sp_ship.add_argument("--evidence", default="",
                         help="commit, PR, or test receipt (empty is refused)")
    sp_mar = msub.add_parser("marathon",
                             help="link an already dialed-in item to its release's marathon")
    sp_mar.add_argument("--gid", required=True)
    sp_mar.add_argument("issue", help="issue URL or TMP-XXXXXX")
    sp_mar.add_argument("--marathon", required=True, help="marathon gid; must be THIS release's")
    sp_cut = msub.add_parser("cut",
                             help="cut an item from a release's manifest (REQUIRES --reason)")
    sp_cut.add_argument("--gid", required=True)
    sp_cut.add_argument("issue", help="issue URL or TMP-XXXXXX")
    sp_cut.add_argument("--reason", default="")
    sp_unship = msub.add_parser("unship",
                                help="retract a falsely shipped manifest item back to dialed_in "
                                     "(REQUIRES --reason)")
    sp_unship.add_argument("--gid", required=True)
    sp_unship.add_argument("issue", help="issue URL or TMP-XXXXXX")
    sp_unship.add_argument("--reason", default="")

    sp = sub.add_parser("marathon", help="marathon CRUD (v1: add/list)")
    msub = sp.add_subparsers(dest="marathon_cmd", required=True)
    sp_add = msub.add_parser("add")
    sp_add.add_argument("--tracking-issue", required=True, help="issue URL or TMP-XXXXXX")
    sp_add.add_argument("--status", default="planned", choices=MARATHON_STATUSES)
    msub.add_parser("list")

    sp = sub.add_parser("list", help="list releases")
    sp.add_argument("--all-repos", action="store_true",
                    help="aggregate RELEASES_APP_EXTRA_DBS too; duplicate GIDs fail loudly")
    sp.add_argument("--status", choices=STATUSES)

    sp = sub.add_parser("show", help="full record for one release (by --gid or --version)")
    sp.add_argument("--gid")
    sp.add_argument("--version")
    sp.add_argument("--full", action="store_true",
                    help="print long values verbatim (default elides them at %d chars)"
                         % SHOW_ELIDE)

    sp = sub.add_parser("next", help="the next unshipped release, by target date")
    sp.add_argument("--verbose", action="store_true", help="also print its full record")

    sp = sub.add_parser("gen", help="side-by-side generation (Phase 0: NEVER writes RELEASES.md)")
    sp.add_argument("--side-by-side", action="store_true", default=True,
                    help="the only mode in Phase 0 (accepted for CLI-shape compatibility)")

    sp = sub.add_parser("check",
                        help="DB<->dump<->generated consistency; FK pragma; stale WAL; "
                             "receipt-vs-change bypass detection; temp-ref staleness; "
                             "duplication warnings; per-boundary crash recovery")
    sp.add_argument("--rebuild", action="store_true",
                    help="rebuild the DB from the dump (git-merge resolution ONLY)")

    sp = sub.add_parser("reconcile", help="fill real URLs into temp refs")
    sp.add_argument("--map", action="append", metavar="TMP-X=URL",
                    help="placeholder -> real issue URL (repeatable)")

    sp = sub.add_parser("dashboard", help="render the releases and roadmap dashboard HTML")

    # GH-525: a ledger with configurable behaviour needs a configuring verb. A settings row is part
    # of the business-state digest, so writing one by hand breaks the receipt chain and `check`
    # fails — this is the only supported way to set one.
    sp_set = sub.add_parser("settings", help="read/write operator-configurable ledger settings")
    ssub = sp_set.add_subparsers(dest="settings_cmd", required=True)
    sp_sl = ssub.add_parser("list", help="print every settings row")
    sp_sg = ssub.add_parser("get", help="print one setting value")
    sp_sg.add_argument("key", help="setting key name")
    sp_ss = ssub.add_parser("set", help="write one operator-configurable setting (receipted)")
    sp_ss.add_argument("key", help="setting key; only configurable keys are accepted")
    sp_ss.add_argument("value", help="new value")
    sp_ss.add_argument("--dry-run", action="store_true", help="print the change, write nothing")

    sp = sub.add_parser("roadmap", help="Roadmap ledger: sync/list/render the ledger items")
    rsub = sp.add_subparsers(dest="roadmap_cmd", required=True)
    sp_sections = rsub.add_parser("sections", help="list accepted roadmap section names (no DB required)")
    sp_sections.add_argument("--json", dest="as_json", action="store_true",
                             help="emit the dashboard's section vocabulary as a JSON array")
    sp_rs = rsub.add_parser("sync", help="mirror legacy ROADMAP.md's ledger into roadmap_items (one-way)")
    sp_rs.add_argument("--dry-run", action="store_true", help="report the diff, write nothing")
    sp_rs.add_argument("--allow-empty", action="store_true",
                       help="permit clearing roadmap_items when the ledger is genuinely empty. "
                            "Without it a 0-entry parse REFUSES (rule=roadmap-empty-parse) so "
                            "format drift can never silently delete the mirror; this flag never "
                            "excuses a ledger that still has content")
    sp_rs = rsub.add_parser("reconcile-state", help="reconcile nonterminal rows against GitHub issue state")
    rs_mode = sp_rs.add_mutually_exclusive_group()
    rs_mode.add_argument("--dry-run", action="store_true", help="preview only (the default)")
    rs_mode.add_argument("--apply", action="store_true", help="apply verified changes in one transaction")
    sp_rl = rsub.add_parser("list", help="print the shadow rows")
    sp_rl.add_argument("--json", dest="as_json", action="store_true",
                       help="emit rows as a JSON array (machine-readable; the default rendering "
                            "is a display, not an API)")
    sp_render = rsub.add_parser("render", help="replay DB rows as ledger markdown (stdout by default)")
    sp_render.add_argument("--out", help="output file (relative to cwd); refuses tracked ROADMAP.md")

    sp_ra = rsub.add_parser("add", help="intake a single issue into the roadmap ledger directly")
    sp_ra.add_argument("--issue-num", required=True, type=int, help="GH issue number")
    sp_ra.add_argument("--issue-url", required=True, help="GH issue URL")
    sp_ra.add_argument("--title", required=True, help="Issue title")
    sp_ra.add_argument("--created", required=True, help="Created date YYYY-MM-DD")
    sp_ra.add_argument("--doc-path", required=True, help="Capture doc relpath")
    sp_ra.add_argument("--raw-text", default=None,
                       help="pre-rendered ROADMAP line (hq park passes hq_roadmap_line output so "
                            "preview and stored row share one template). GH-249: a `rated "
                            "N/N/N/N [ovr N]` token in this line is parsed and stored — in a "
                            "releases-mode repo this is the ONLY way to score an entry, since "
                            "`roadmap sync` is a no-op there")
    sp_ra.add_argument("--dry-run", action="store_true", help="print what would be written and write nothing")

    sp_rr = rsub.add_parser("rate", help="score a roadmap row that is already parked (GH-253)")
    sp_rr.add_argument("--issue-num", type=int, help="GH issue number of the parked row")
    sp_rr.add_argument("--gid", help="the row's rmi- global id — for a multi-issue row that has no "
                                     "gh_number and cannot be addressed any other way")
    sp_rr.add_argument("--rated", required=True,
                       help="the four axes as N/N/N/N (pri/sev/appeal/effort, 1-100, higher is "
                            "better on every axis — effort scores CHEAPNESS)")
    sp_rr.add_argument("--ovr", type=int, default=None,
                       help="operator override (4-400) replacing the derived calc for ranking; "
                            "the four axes keep their honest values underneath")
    sp_rr.add_argument("--force", action="store_true",
                       help="replace an existing rating (refused by default)")
    sp_rr.add_argument("--dry-run", action="store_true", help="print what would be written and write nothing")

    sp_rp = rsub.add_parser("repoint", help="re-point a parked row's capture doc after the doc moves")
    sp_rp.add_argument("--issue-num", required=True, type=int, help="GH issue number of the parked row")
    sp_rp.add_argument("--doc-path", required=True, help="the doc's NEW repo-relative path")
    sp_rp.add_argument("--dry-run", action="store_true", help="print what would be written and write nothing")

    sp_ru = rsub.add_parser("update", help="update a roadmap row's text, section or status marker")
    sp_ru.add_argument("--issue-num", type=int, help="GH issue number of the parked row")
    sp_ru.add_argument("--gid", help="the row's rmi- global id")
    sp_ru.add_argument("--raw-text", help="new raw_text for the row")
    sp_ru.add_argument("--status-marker", choices=_ROADMAP_STATUS_MARKERS,
                       help="explicit lifecycle marker; never inferred from raw_text")
    sp_ru.add_argument("--section", help="new section; accepted names: " + ", ".join(ROADMAP_SECTIONS))
    sp_ru.add_argument("--issue-url", help="corrected GitHub issue URL for the row (GH-527). Must "
                       "name the same issue as the row's gh_number — this is the only verb that "
                       "can repair an issue_url written wrong at intake")
    sp_ru.add_argument("--dry-run", action="store_true", help="print what would be written and write nothing")

    sp_rm = rsub.add_parser("move", help="move an existing roadmap row to a new section (GH-269)")
    sp_rm.add_argument("--issue-num", type=int, help="GH issue number of the parked row")
    sp_rm.add_argument("--gid", help="the row's rmi- global id")
    sp_rm.add_argument("--section", required=True,
                       help="new section; accepted names: " + ", ".join(ROADMAP_SECTIONS))
    sp_rm.add_argument("--raw-text", default=None, help="optional updated raw_text for the row")
    sp_rm.add_argument("--dry-run", action="store_true", help="print what would be written and write nothing")

    sp = sub.add_parser("project", help="GitHub Project release-card projection")
    psub = sp.add_subparsers(dest="project_cmd", required=True)
    sp_sync = psub.add_parser("sync", help="plan or apply DB -> GitHub Project draft cards")
    sp_sync.add_argument("--owner", required=True, help="GitHub organization or user owning the Project")
    sp_sync.add_argument("--number", required=True, type=int, help="GitHub Project number")
    sp_sync.add_argument("--apply", action="store_true",
                         help="perform GitHub writes (default is an auditable dry run)")

    sp = sub.add_parser("jog", help="Jog serial immediate-queue execution engine (GH-259)")
    jsub = sp.add_subparsers(dest="jog_cmd", required=True)
    sp_ja = jsub.add_parser("add", help="enqueue an issue into the jog queue")
    sp_ja.add_argument("target", help="issue number (e.g. 123 or GH-123) or doc path")
    sp_ja.add_argument("--pos", type=int, default=None, help="queue position (default: append to end)")
    sp_ja.add_argument("--dry-run", action="store_true", help="report what would be queued, write nothing")

    sp_jl = jsub.add_parser("list", help="list active jog queue items")
    sp_jl.add_argument("--all", dest="show_all", action="store_true", help="include completed/dropped/archived items")
    sp_jl.add_argument("--json", dest="as_json", action="store_true", help="output as JSON array")

    sp_jb = jsub.add_parser("bump", help="bump an issue to the head of the jog queue (position 1)")
    sp_jb.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jb.add_argument("--dry-run", action="store_true", help="report what would be bumped, write nothing")

    sp_jd = jsub.add_parser("drop", help="mark a jog queue item as dropped with a reason")
    sp_jd.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jd.add_argument("--reason", required=True, help="reason for dropping from the queue")
    sp_jd.add_argument("--force", action="store_true", help="force dropping an already completed item")
    sp_jd.add_argument("--dry-run", action="store_true", help="report what would be dropped, write nothing")

    sp_jr = jsub.add_parser("retry", help="retry a parked or failed jog item (resets to pending)")
    sp_jr.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jr.add_argument("--dry-run", action="store_true", help="report what would be retried, write nothing")

    sp_js = jsub.add_parser("skip", help="park/skip an item at the head of the queue")
    sp_js.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_js.add_argument("--reason", default="skipped by operator", help="reason for skipping")
    sp_js.add_argument("--dry-run", action="store_true", help="report what would be skipped, write nothing")

    sp_jc = jsub.add_parser("clear", help="archive terminal items (completed, dropped, parked, failed) in jog queue")
    sp_jc.add_argument("--dry-run", action="store_true", help="report what would be archived, write nothing")

    sp_jtm = jsub.add_parser("to-marathon", help="export active jog items to marathon format")

    sp_jres = jsub.add_parser("resume", help="reconcile durable Marathon state for an item (spends no token)")
    sp_jres.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jres.add_argument("--root", default=None, help="repository root path")

    sp_jrg = jsub.add_parser("retry-gate", help="re-run ONLY the gate against the same head SHA (no builder turn)")
    sp_jrg.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jrg.add_argument("--builder", default="agy", help="builder identity recorded for the retry")
    sp_jrg.add_argument("--reviewer", default=None, help="reviewer agent (required; must differ from --builder)")
    sp_jrg.add_argument("--auto-merge", action="store_true", help="merge the PR if the gate retry approves")
    sp_jrg.add_argument("--root", default=None, help="repository root path")

    sp_jrb = jsub.add_parser("retry-build", help="fresh Marathon attempt on a fresh execution id (history preserved)")
    sp_jrb.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jrb.add_argument("--builder", default="agy", help="builder turn-taker (default: agy; or codex, aider)")
    sp_jrb.add_argument("--reviewer", default=None, help="reviewer agent (required; must differ from --builder)")
    sp_jrb.add_argument("--auto-merge", action="store_true", help="opt-in to auto-merge an approved PR")
    sp_jrb.add_argument("--root", default=None, help="repository root path")

    sp_jl = jsub.add_parser("land", help="verify merged delivery, complete the row, delegate lifecycle to wave_reconcile")
    sp_jl.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jl.add_argument("--pr", default=None, help="PR number or URL (required when the receipt has no PR identity)")
    sp_jl.add_argument("--root", default=None, help="repository root path")

    sp_jrec = jsub.add_parser("reconcile", help="idempotent replay entry for jog land (same verification and steps)")
    sp_jrec.add_argument("target", help="issue number (e.g. 123 or GH-123)")
    sp_jrec.add_argument("--pr", default=None, help="PR number or URL (required when the receipt has no PR identity)")
    sp_jrec.add_argument("--root", default=None, help="repository root path")

    sp_jrun = jsub.add_parser("run", help="execute the serial jog queue loop")
    sp_jrun.add_argument("--auto-merge", action="store_true", help="opt-in to auto-merge passing PRs on same-seam tasks")
    sp_jrun.add_argument("--builder", default="agy", help="builder turn-taker (default: agy; or codex, aider)")
    sp_jrun.add_argument("--reviewer", default=None,
                         help="reviewer agent — REQUIRED with --executor marathon, the default "
                              "executor (GH-280 Phase 5); no default is selected")
    sp_jrun.add_argument("--executor", choices=["relay", "marathon"], default="marathon",
                         help="per-task executor (GH-280 Phase 5): 'marathon' is the default — the "
                              "reviewed one-phase driver via the structured contracts, requires "
                              "--reviewer; 'relay' is the legacy rollback path kept for a "
                              "documented compatibility window")
    sp_jrun.add_argument("--max-tasks", type=int, default=None, help="maximum tasks to process in this run")
    sp_jrun.add_argument("--simulate", action="store_true", help="simulate drive execution in test environments")
    sp_jrun.add_argument("--dry-run", action="store_true", help="simulate queue run without mutations")

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "init": cmd_init, "import": cmd_import, "add": cmd_add, "update": cmd_update,
        "ship": cmd_ship, "migrate": cmd_migrate, "baseline": cmd_baseline,
        "manifest": lambda a: cmd_manifest_add(a) if a.manifest_cmd in ("dial-in", "add")
        else (cmd_manifest_ship(a) if a.manifest_cmd == "ship"
              else (cmd_manifest_marathon(a) if a.manifest_cmd == "marathon"
    else (cmd_manifest_unship(a) if a.manifest_cmd == "unship"
                    else cmd_manifest_cut(a)))),
        "marathon": lambda a: cmd_marathon_add(a) if a.marathon_cmd == "add"
        else cmd_marathon_list(a),
        "list": cmd_list, "show": cmd_show, "next": cmd_next, "gen": cmd_gen,
        "check": cmd_check, "reconcile": cmd_reconcile,
        "project": lambda a: cmd_project_sync(a) if a.project_cmd == "sync" else None,
        # A lookup, not a ternary chain: `rate` (GH-253) was the fourth branch, and the nested
        # form was already one subcommand past readable.
        "roadmap": lambda a: {"add": cmd_roadmap_add, "sync": cmd_roadmap_sync,
                              "rate": cmd_roadmap_rate, "list": cmd_roadmap_list,
                              "render": cmd_roadmap_render,
                              "repoint": cmd_roadmap_repoint, "update": cmd_roadmap_update,
                              "move": cmd_roadmap_move, "sections": cmd_roadmap_sections,
                              "reconcile-state": cmd_roadmap_reconcile_state}[a.roadmap_cmd](a),
        "settings": lambda a: {"set": cmd_settings_set,
                               "list": cmd_settings_list,
                               "get": cmd_settings_get}[a.settings_cmd](a),
        "dashboard": cmd_dashboard,
        "jog": lambda a: {"add": cmd_jog_add, "list": cmd_jog_list,
                          "bump": cmd_jog_bump, "drop": cmd_jog_drop,
                          "retry": cmd_jog_retry, "skip": cmd_jog_skip,
                          "clear": cmd_jog_clear, "to-marathon": cmd_jog_to_marathon,
                          "run": cmd_jog_run, "resume": cmd_jog_resume,
                          "retry-gate": cmd_jog_retry_gate, "retry-build": cmd_jog_retry_build,
                          "land": cmd_jog_land, "reconcile": cmd_jog_land}[a.jog_cmd](a),
    }
    handlers[args.cmd](args)



if __name__ == "__main__":
    main()
