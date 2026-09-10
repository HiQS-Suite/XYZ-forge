#!/usr/bin/env python3
"""jog_run.py — GH-259: Jog serial immediate-queue execution engine supervisor.

Supervises the serial execution of tasks in jog_queue:
1. Acquires the outer driver lock (`relay-driver.lock`) and exports RELAY_DRIVER_LOCKED=1.
2. Reconciles any orphan `running` leases on startup via perform_write (resets dead PIDs to pending).
3. Pops pending tasks in strict position order.
4. Auto-promotes 1-INBOX contracts to 2-WORKING with probe linting and safety checks.
5. Executes swarm-preflight (ready -> drive, already-landed -> drop, not-ready -> park).
6. Dispatches single-phase turn runner.
7. Defaults to pausing at landing boundaries for operator confirmation before merging PRs into development (with --auto-merge as opt-in).
8. Re-anchors same-seam tasks on development and tears down throwaway worktrees cleanly.

GH-280 Phase 5: the DEFAULT per-task executor is marathon (the reviewed one-phase driver —
items 5-8 above describe the LEGACY relay loop, still reached via `--executor relay` or
`--simulate` during a documented compatibility window; every such run prints a deprecation
notice naming the window and the separate-removal fact).
"""

import argparse
import atexit
import datetime as _dt
import glob
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile

# Ensure utils/py is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_paths import harness_home, repo_root, is_vendored, resolve_tool  # noqa: E402
from rtl import driver_lock_path  # noqa: E402
import relay_attest  # noqa: E402  GH-505/GH-509: validated reader of relay-drive/attest@1
from releases_app import (  # noqa: E402
    _ensure_jog_schema,
    _table_exists,
    jog_acquire_lease,
    jog_set_status,
    jog_reconcile_orphan_leases,
)


TRIVIAL_PROBE_PATTERNS = [
    re.compile(r"^(?:true|exit\s+0|:|echo\s+.*|sleep\s+.*)$", re.IGNORECASE),
]


# ── GH-280: structured Jog ↔ Preflight ↔ Marathon machine contracts ────────────────────────────
# Jog consumes Swarm Preflight's marathon-invocation@1 artifact and Marathon's marathon-drive/
# result@1 receipt as DATA. It never parses shell text, relay prose, or the driver's stdout —
# that is the GH-279 failure family this recalibration exists to end. These loaders are the one
# validation boundary: unsupported schema versions and malformed artifacts are refused loudly
# BEFORE any dispatch (no lease mutation, no token spend).

MARATHON_INVOCATION_SCHEMA = "swarm-preflight/marathon-invocation@1"
MARATHON_RESULT_SCHEMA = "marathon-drive/result@1"


class ContractError(Exception):
    """A machine contract failed validation — refuse before dispatch, never guess."""


def _load_contract_json(path, expected_schema, what):
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except OSError as exc:
        raise ContractError(f"{what} unreadable at {path}: {exc}")
    except ValueError as exc:
        raise ContractError(f"{what} at {path} is not valid JSON: {exc}")
    if not isinstance(obj, dict):
        raise ContractError(f"{what} at {path} is not a JSON object")
    schema = obj.get("schema")
    if schema != expected_schema:
        raise ContractError(
            f"{what} at {path} carries schema {schema!r}; this Jog supports only "
            f"{expected_schema!r} — refusing rather than guessing at an unknown contract")
    return obj


def load_marathon_invocation(path):
    """Load and validate a swarm-preflight/marathon-invocation@1 artifact.

    Returns the dict on success; raises ContractError on anything a supervisor must not
    dispatch against. Packet presence is checked because argv embeds the packet path.
    """
    obj = _load_contract_json(path, MARATHON_INVOCATION_SCHEMA, "marathon invocation")

    argv = obj.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a for a in argv):
        raise ContractError("invocation argv must be a non-empty array of non-empty strings")
    drive = argv[0]
    if not os.path.isabs(drive):
        raise ContractError(f"invocation argv[0] must be absolute (got {drive!r})")
    if not os.path.isfile(drive) or not os.access(drive, os.X_OK):
        raise ContractError(f"invocation drive command is not an executable file: {drive}")

    env = obj.get("env")
    if not isinstance(env, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                        for k, v in env.items()):
        raise ContractError("invocation env must be an object of string -> string")

    for key, check in (
        ("harness_root", os.path.isdir),
        ("target_root", os.path.isdir),
        ("packet_path", os.path.isfile),
    ):
        val = obj.get(key)
        if not isinstance(val, str) or not val:
            raise ContractError(f"invocation field {key!r} must be a non-empty string")
        if not check(val):
            raise ContractError(f"invocation field {key!r} does not resolve: {val}")

    for key in ("issue", "phase", "lane", "gate", "builder", "reviewer", "base_ref",
                "result_path", "packet_dir"):
        if key not in obj:
            raise ContractError(f"invocation is missing required field {key!r}")
    if not isinstance(obj.get("artifacts"), list):
        raise ContractError("invocation artifacts must be an array")
    return obj


def load_marathon_result(path):
    """Load and validate a marathon-drive/result@1 receipt.

    Field VALUES may be null (Marathon writes explicit nulls for unreached values); the KEYS
    must all be present with the right shape, so a truncated or hand-edited receipt is refused
    rather than half-trusted.
    """
    obj = _load_contract_json(path, MARATHON_RESULT_SCHEMA, "marathon result")

    for key in ("execution_id", "outcome", "reason", "exit_code", "issue", "phase", "lane",
                "token", "attempt", "target_repo", "base_branch", "head_branch", "head_sha",
                "gate", "acceptance", "pr", "timestamps"):
        if key not in obj:
            raise ContractError(f"result receipt is missing required field {key!r}")

    if not isinstance(obj["execution_id"], str) or not obj["execution_id"]:
        raise ContractError("result execution_id must be a non-empty string")
    if not isinstance(obj["exit_code"], int) or isinstance(obj["exit_code"], bool):
        raise ContractError("result exit_code must be an integer")
    if not isinstance(obj["outcome"], str) or not obj["outcome"]:
        raise ContractError("result outcome must be a non-empty string")
    for key in ("target_repo", "gate", "attempt", "pr", "timestamps"):
        if not isinstance(obj[key], dict):
            raise ContractError(f"result field {key!r} must be an object")
    return obj


# ── GH-280 Phase 2: the opt-in Marathon executor ───────────────────────────────────────────────
# `releases jog run --executor marathon --reviewer <agent>` delegates each leased item's
# execution to Marathon's reviewed one-phase driver through the Phase 1 contracts. Jog still
# owns the queue, lease, and driver lock (the outer serial boundary); it never seeds Tick,
# renders a relay, picks a branch, interprets agent output, runs a gate, or discovers a PR —
# those belong to Marathon, and the receipt is the only outcome Jog reads.
#
# Execution state lives under <root>/.tick/jog/<queue-global-id>/ (gitignored by every harness
# layout, so it can never trip the packet's own --require-clean): state.json is an append-only
# execution ledger for cold-start recovery, and <exec-id>/ holds that execution's packet and
# Marathon result receipt.
#
# GH-280 Phase 5: `marathon` is the DEFAULT executor. The legacy `relay` machinery stays
# functional behind `--executor relay` (and `--simulate`) for a documented compatibility
# window — it is THE rollback path — and its removal lands as its own commit one release
# cycle after this flip. Every legacy invocation prints a one-line stderr deprecation notice.

JOG_EXECUTION_STATE_SCHEMA = "jog/execution-state@1"

# Marathon's reviewed-phase contract (marathon_drive.py): reviewer ids must start with one of
# these. Jog mirrors the rule so an invalid reviewer fails before ANY lease mutation.
_MARATHON_REVIEWER_PREFIXES = ("codex", "gemini", "agy")

# GH-280 Phase 5: one line, stderr, on every legacy-machinery invocation (explicit
# `--executor relay`, or `--simulate` which stays on the relay machinery). Names the window
# and the separate-removal fact — removal is NOT part of the flip commit.
JOG_RELAY_DEPRECATION_NOTICE = (
    "jog: relay executor is legacy (compatibility window; removal lands as its own commit "
    "one release cycle after the Phase 5 flip — see "
    "PROJECT/3-COMPLETED/GH-280-JOG-MARATHON-RECALIBRATION.md)"
)


def validate_marathon_executor(args):
    """Fail-closed executor validation. Returns an error string or None; called before any
    lease mutation, lock acquisition, or dispatch (GH-280 reviewer policy: explicit only)."""
    reviewer = getattr(args, "reviewer", None)
    if not reviewer:
        return ("--reviewer <agent> is required with --executor marathon (the default "
                "executor since the Phase 5 flip) — Jog does not select a reviewer by "
                "default (GH-280: no silent cost-bearing or same-agent route)")
    if reviewer == args.builder:
        return f"--reviewer must differ from --builder (both are '{reviewer}')"
    if not reviewer.startswith(_MARATHON_REVIEWER_PREFIXES):
        return (f"--reviewer '{reviewer}' must start with one of "
                f"{'/'.join(_MARATHON_REVIEWER_PREFIXES)} (marathon's reviewed-phase contract)")
    if reviewer.startswith("agy"):
        bin_name = os.environ.get("AGY_BIN", "agy")
    elif reviewer.startswith("codex"):
        bin_name = os.environ.get("CODEX_BIN", "codex")
    else:  # gemini*
        bin_name = os.environ.get("GEMINI_BIN", "gemini")
    if not (shutil.which(bin_name) or (os.path.isfile(bin_name) and os.access(bin_name, os.X_OK))):
        return f"reviewer binary '{bin_name}' not found on PATH (--reviewer {reviewer})"
    return None


def _jog_state_paths(root, gid):
    base = os.path.join(root, ".tick", "jog", gid)
    return base, os.path.join(base, "state.json")


def _ledger_abs_path(root, gid, path):
    """Resolve a ledger-recorded path. GH-292 F2: new records store paths RELATIVE to the
    ledger base (<root>/.tick/jog/<gid>/) so the ledger survives a queue-row re-add (a fresh
    global_id) without re-key surgery. Absolute paths from older records still resolve."""
    if not path:
        return path
    if os.path.isabs(path):
        return path
    base, _ = _jog_state_paths(root, gid)
    return os.path.join(base, path)


def _ledger_rel_path(root, gid, path):
    """Store-side twin of _ledger_abs_path: absolute→relative when the path sits inside this
    ledger; anything else is stored verbatim."""
    if not path or not os.path.isabs(path):
        return path
    base, _ = _jog_state_paths(root, gid)
    try:
        rel = os.path.relpath(path, base)
    except ValueError:
        return path
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return path
    return rel


def jog_regenerate_dashboard(root):
    """GH-292 F3: jog's promotion repoints roadmap rows and stalens the committed
    ROADMAP-DASHBOARD.md — the lane's own gate then fails on drift (observed on both Phase-4
    dogfood items). Regenerate after promotion, before dispatch. Best-effort and scoped to
    installs that ship the renderer."""
    script = None
    for candidate in (os.path.join(root, "utils", "roadmap-dashboard.sh"),
                      os.path.join(harness_home(), "utils", "roadmap-dashboard.sh")):
        if os.path.isfile(candidate):
            script = candidate
            break
    if not script:
        return
    try:
        env = dict(os.environ)
        env["ROADMAP_DASHBOARD_ROOT"] = str(root)
        r = subprocess.run(["bash", script], cwd=root, env=env, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"jog: warning: roadmap-dashboard refresh failed ({r.returncode}): {(r.stderr or r.stdout).strip()}",
                  file=sys.stderr)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"jog: warning: roadmap-dashboard refresh exception: {e}", file=sys.stderr)


def jog_commit_supervisor_state(root, gh_num, exec_id):
    """GH-292 F1: commit the supervisor's own ledger/doc writes before dispatch.

    The turn-containment pass restores tracked working-tree modifications to HEAD, and jog's
    uncommitted writes (releases.db/sql, regenerated views, the promoted doc pair) are
    indistinguishable from an agent's off-lane edits — the Phase-4 dogfood lost queue rows to
    exactly this, twice. Committing supervisor-owned paths BEFORE any turn dispatches makes
    containment have nothing of the supervisor's to revert.

    Stages an explicit path list only — never `git add -A` (the GH-124 sweep lesson). The
    promotion's own `git rm`/`git add` of the doc pair is already staged by promotion.
    Commits only on the integration branch: a retry-build dispatches from a lane branch,
    and a ledger commit there would ride into the lane PR and block later branch switches.
    Returns True when a commit was made."""
    integration = os.environ.get("MARATHON_INTEGRATION_BRANCH", "development")
    current = subprocess.run(["git", "-C", root, "symbolic-ref", "--quiet", "--short", "HEAD"],
                             capture_output=True, text=True)
    if current.returncode == 0 and current.stdout.strip() != integration:
        print(f"jog: supervisor-state commit skipped — on branch '{current.stdout.strip()}' "
              f"(not the integration branch '{integration}'); uncommitted ledger writes on a "
              f"lane are the containment-revert tradeoff (GH-292 F1)")
        return False
    paths = [p for p in ("releases.db", "releases.sql", "releases.gen",
                         "ROADMAP-DASHBOARD.md", "LEADERBOARD.html", "RELEASES-PREVIEW.html")
             if os.path.exists(os.path.join(root, p))]
    if paths:
        subprocess.run(["git", "-C", root, "add", "--"] + paths, capture_output=True)
    staged = subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet"],
                            capture_output=True)
    if staged.returncode == 0:
        return False
    res = subprocess.run(
        ["git", "-C", root, "commit", "-q", "-m",
         f"jog-state: intake + lease for GH-{gh_num} (execution {exec_id}) — supervisor-owned "
         f"ledger, doc, and view writes committed before dispatch (GH-292 F1)"],
        capture_output=True, text=True)
    if res.returncode != 0:
        print(f"jog: warning: supervisor-state commit failed: {(res.stderr or '').strip()}",
              file=sys.stderr)
        return False
    return True


def jog_resolve_ledger_gid(root, gh_num):
    """GH-292 F2: the gid whose ledger holds this issue's executions.

    Prefers the queue row's own global_id when its ledger exists; otherwise scans
    .tick/jog/*/state.json for a matching gh_number (newest first) so history written under a
    previous row identity is still found after DB loss + re-add. Returns None when the issue
    has no ledger at all."""
    gid = jog_current_gid(root, gh_num)
    if gid:
        _base, path = _jog_state_paths(root, gid)
        if os.path.isfile(path):
            return gid
    jog_dir = os.path.join(root, ".tick", "jog")
    if not os.path.isdir(jog_dir):
        return None
    candidates = []
    for name in os.listdir(jog_dir):
        _base, path = _jog_state_paths(root, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, ValueError):
            continue
        if state.get("gh_number") == gh_num:
            candidates.append((os.path.getmtime(path), name))
    if not candidates:
        return None
    return max(candidates)[1]


def jog_load_state(root, gid):
    """Load the append-only execution ledger for a queue row; a fresh one if absent."""
    _base, path = _jog_state_paths(root, gid)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if isinstance(state, dict) and state.get("schema") == JOG_EXECUTION_STATE_SCHEMA \
                    and isinstance(state.get("executions"), list):
                return state
        except (OSError, ValueError):
            pass
    return {"schema": JOG_EXECUTION_STATE_SCHEMA, "gid": gid, "executions": []}


def jog_save_state(root, gid, state):
    _base, path = _jog_state_paths(root, gid)
    os.makedirs(_base, exist_ok=True)
    tmp = path + f".tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def jog_current_gid(root, gh_num):
    """The queue row's global_id (its durable identity across retries)."""
    conn = sqlite3.connect(os.path.join(root, "releases.db"))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT global_id FROM jog_queue WHERE gh_number = ? "
                           "ORDER BY id DESC LIMIT 1", (gh_num,)).fetchone()
        return row["global_id"] if row else None
    finally:
        conn.close()


def jog_verify_pr_before_merge(root, receipt, pr_number):
    """GH-300 (PR #281 review B1): verify GitHub truth against the receipt BEFORE merging.

    An approved receipt's PR identity is Marathon-owned and trusted as a record, but the
    merge must not act on it blind: a stale PR number that happens to resolve in this repo
    (or a PR whose head moved after the reviewed build) would otherwise be merged as-is.
    Mirrors the verification family `jog land` performs post-merge, adapted to pre-merge:
    the PR must still be OPEN with the receipt's base/head/head-SHA, the receipt must name
    this repo, and the gate must be green for that head. Returns (failures, pr); an empty
    failures list means the merge may proceed.
    """
    pr, err = _gh_pr_view(root, pr_number)
    if pr is None:
        return [f"pr view failed: {err}"], None
    checks = [
        ("state OPEN", pr.get("state") == "OPEN"),
        (f"base {receipt.get('base_branch')}", pr.get("baseRefName") == receipt.get("base_branch")),
        (f"head {receipt.get('head_branch')}", pr.get("headRefName") == receipt.get("head_branch")),
        (f"head SHA {str(receipt.get('head_sha') or '')[:8]}",
         pr.get("headRefOid") == receipt.get("head_sha")),
        ("receipt repo is this repo",
         not receipt.get("target_repo", {}).get("path")
         or os.path.realpath(receipt["target_repo"]["path"]) == os.path.realpath(root)),
    ]
    gate = receipt.get("gate") or {}
    checks.append(("gate green on the merge head",
                   gate.get("result") == "green"
                   and (not gate.get("receipt_path") or os.path.isfile(gate["receipt_path"]))))
    return [name for name, ok in checks if not ok], pr


def jog_project_marathon_outcome(root, gh_num, receipt, auto_merge=False,
                                 execution_id=None, result_path=None):
    """Project a validated Marathon result receipt into the queue via perform_write.

    Marathon owns the outcome; this only records it. Returns the queue action taken
    ("completed", "parked", "failed") plus a human reason. Never guesses a branch or PR:
    landing identity comes from the receipt, and a green phase without a PR is parked with
    the receipt's branch fields — it is never a global failure.

    GH-291 Scope 4: refused/escalated/parked reasons carry a trace segment naming the
    execution_id and result_path when the caller provides them, so a failed row points at
    its receipt without a ledger inspection.
    """
    outcome = receipt.get("outcome")
    reason = receipt.get("reason")
    if outcome == "approved":
        pr = receipt.get("pr") or {}
        pr_number = pr.get("number")
        if pr_number:
            note = f"awaiting-landing (PR #{pr_number}: {pr.get('url') or 'url unavailable'})"
            if auto_merge:
                failures, _ = jog_verify_pr_before_merge(root, receipt, pr_number)
                if failures:
                    return "parked", (f"{note} — auto-merge refused (verification failed: "
                                      f"{', '.join(failures)})")
                # GH-505/GH-509: an approved receipt without a validated candidate came from an
                # unattested run — park it; otherwise merge exactly that candidate.
                if not receipt.get("reviewed_candidate") or not receipt.get("attest_path"):
                    return "parked", f"{note} — auto-merge refused: receipt carries no reviewer attestation (GH-505)"
                record, why = relay_attest.load(
                    receipt.get("token"), expected_reviewer=receipt.get("reviewer"),
                    relay_file=None, target_repo=root, path=receipt.get("attest_path"))
                if record is None:
                    return "parked", f"{note} — auto-merge refused: {why}"
                merged, reason = _merge_reviewed_pr(root, pr_number, record,
                                                    expected_candidate=receipt.get("reviewed_candidate"))
                if merged:
                    return "completed", f"marathon approved; PR #{pr_number} merged at {receipt['reviewed_candidate'][:12]}"
                return "parked", f"{note} — auto-{reason}"
            return "parked", note
        head = receipt.get("head_branch")
        base = receipt.get("base_branch")
        pr_note = receipt.get("pr_note")
        bits = [f"head={head or 'unknown'}", f"base={base or 'unknown'}"]
        if pr_note:
            bits.append(pr_note)
        return "parked", "awaiting-landing (no PR yet — open one from the receipt's branches: " + \
            "; ".join(bits) + ")"
    label = f"marathon {outcome}: {reason} (exit {receipt.get('exit_code')})"
    if execution_id or result_path:
        label += f" [{execution_id or 'no-execution-id'}; result: {result_path or 'no-result-path'}]"
    return ("failed", label) if outcome != "parked" else ("parked", label)


def jog_reconcile_cold_start(root, gh_nums):
    """GH-280 cold start for the marathon executor: for each orphan-reconciled row that has a
    dispatched Marathon execution on record, inspect the durable result BEFORE the queue can
    lease and refire. A valid terminal result is re-projected idempotently (no turn spent);
    a dispatched execution with no valid result parks the row — never a silent refire."""
    for gh_num in gh_nums:
        gid = jog_resolve_ledger_gid(root, gh_num)
        if not gid:
            continue
        state = jog_load_state(root, gid)
        executions = state.get("executions") or []
        if not executions:
            continue
        latest = executions[-1]
        if latest.get("status") != "dispatched":
            continue
        receipt = None
        load_error = None
        result_path = _ledger_abs_path(root, gid, latest.get("result_path"))
        if result_path and os.path.isfile(result_path):
            try:
                receipt = load_marathon_result(result_path)
            except ContractError as exc:
                # GH-291 Scope 2: a future-schema (or otherwise invalid) receipt must be
                # distinguishable from a missing one — version skew parks with its cause named.
                receipt = None
                load_error = str(exc)
        if receipt is not None:
            action, reason = jog_project_marathon_outcome(
                root, gh_num, receipt,
                execution_id=latest.get("execution_id"), result_path=latest.get("result_path"))
            latest["status"] = f"projected-{action}"
            latest["projected_reason"] = reason
            jog_save_state(root, gid, state)
            jog_set_status(root, gh_num, action, failure_reason=reason)
            print(f"jog: cold start GH-{gh_num}: re-projected terminal Marathon result "
                  f"({action}) — no new execution fired")
        else:
            latest["status"] = "cold-start-paused"
            jog_save_state(root, gid, state)
            jog_set_status(root, gh_num, "parked",
                           failure_reason="cold-start: dispatched Marathon execution has no valid "
                                          "result receipt"
                                          + (f" (load error: {load_error})" if load_error else "")
                                          + " — inspect manually before any refire")
            print(f"jog: cold start GH-{gh_num}: dispatched execution {latest.get('execution_id')} "
                  f"has no valid result{f' ({load_error})' if load_error else ''} — parked; "
                  f"never silently refire")


def _marathon_argv_from_invocation(invocation, builder, reviewer):
    """The packet's argv with Jog's supervisor policy applied.

    Policy overrides, in one place so every dispatch path (run / retry-gate / retry-build)
    stays identical: the operator's reviewer/builder replace the packet's suggestions, the
    packet's --require-clean is dropped (a supervisor's own queue writes make the tree
    legitimately non-pristine between lease and dispatch), and the packet's suggested
    per-issue phase id is adopted so Marathon's lane namespace (and its attempt cap) stays
    per-issue instead of collapsing onto marathon's bare 'p1' default.
    """
    argv = list(invocation["argv"])
    for flag, value in (("--reviewer", reviewer), ("--builder", builder)):
        if flag in argv:
            argv[argv.index(flag) + 1] = value
        else:
            argv += [flag, value]
    if "--require-clean" in argv:
        argv.remove("--require-clean")
    if "--phase-id" not in argv and invocation.get("phase"):
        argv += ["--phase-id", invocation["phase"]]
    return argv


def run_marathon_phase(root, gh_num, gid, builder, reviewer, auto_merge=False, mode="run"):
    """Execute one leased queue item through Preflight → Marathon's one-phase driver.

    Returns (queue_status, failure_reason): one of ("completed", reason) / ("parked", reason) /
    ("failed", reason) for jog_set_status. All durable state lands in the execution ledger
    under .tick/jog/<gid>/ so a restart can reconcile without a second dispatch.
    """
    home = harness_home()
    preflight_py = os.path.join(home, "utils", "py", "swarm_preflight.py")
    if not os.path.isfile(preflight_py):
        return "parked", f"marathon executor: swarm_preflight not found at {preflight_py} " \
                        f"(vendored installs resolve .xyz via the harness home — GH-279 #2)"

    state = jog_load_state(root, gid)
    exec_id = f"gh{gh_num}-exec{len(state['executions']) + 1}"
    exec_dir = os.path.join(_jog_state_paths(root, gid)[0], exec_id)
    packet_dir = os.path.join(exec_dir, "preflight")
    record = {
        "execution_id": exec_id,
        "mode": mode,
        "started_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "dispatched",
        # GH-292 F2: ledger-internal paths are stored RELATIVE to the ledger base so the
        # history survives a queue-row re-add (fresh gid) without re-key surgery.
        "packet_dir": _ledger_rel_path(root, gid, packet_dir),
        "result_path": None,
    }
    state["executions"].append(record)
    state["gh_number"] = gh_num
    jog_save_state(root, gid, state)
    print(f"jog: marathon execution {exec_id} for GH-{gh_num} (packet: {packet_dir})")

    pf = subprocess.run(
        [sys.executable, preflight_py, "--gh-issue", str(gh_num), "--out", packet_dir],
        cwd=root, capture_output=True, text=True)
    if pf.returncode == 4:
        record["status"] = "completed-preflight-stale"
        jog_save_state(root, gid, state)
        return "completed", "preflight: already-landed"
    if pf.returncode != 0:
        record["status"] = "preflight-refused"
        jog_save_state(root, gid, state)
        tail = (pf.stderr or pf.stdout or "").strip().splitlines()
        detail = tail[-1][:200] if tail else ""
        return "parked", f"preflight-refused (exit {pf.returncode}){': ' + detail if detail else ''}"

    invocation_path = os.path.join(packet_dir, "marathon-invocation.json")
    try:
        invocation = load_marathon_invocation(invocation_path)
    except ContractError as exc:
        record["status"] = "invalid-invocation"
        jog_save_state(root, gid, state)
        return "parked", f"invalid marathon invocation artifact: {exc}"

    argv = _marathon_argv_from_invocation(invocation, builder, reviewer)
    if mode == "retry-build":
        # A rebuild must not be satisfied by the attempt it retries (GH-491): dispatch on a
        # FRESH suffixed token in the same family. The spent token's history stays untouched —
        # Tick events are append-only and prior execution records are never deleted.
        prior_record, prior_receipt = _jog_latest_receipt(root, gid)
        prior_token = (prior_receipt or {}).get("token")
        if prior_token:
            argv += ["--relay-task", f"{prior_token}-{len(state['executions'])}"]
    argv += ["--execution-id", exec_id]
    record["result_path"] = _ledger_rel_path(root, gid, invocation["result_path"])
    # PR #281 review B4: persist the result path BEFORE dispatch — a crash mid-drive otherwise
    # orphans a receipt that was actually written (the ledger's newest record still says null).
    jog_save_state(root, gid, state)

    env = dict(os.environ)
    env.update(invocation["env"])
    # Jog already holds the outer driver lock; exporting it keeps marathon-drive from
    # contending with its own supervisor on the same lock directory.
    env["RELAY_DRIVER_LOCKED"] = "1"

    # GH-292 F1: supervisor-owned writes are committed BEFORE any turn dispatches, so the
    # containment pass (which restores tracked modifications to HEAD) has nothing of the
    # supervisor's to revert. GH-292 F3: the dashboard was regenerated after promotion —
    # the call was previously dead code (defined, never invoked), observed live 2026-08-29
    # when the supervisor commit carried a stale dashboard and the lane's gate failed
    # roadmap-dashboard.sh drift; regenerate BEFORE the commit so the fresh one rides it.
    jog_regenerate_dashboard(root)
    jog_commit_supervisor_state(root, gh_num, exec_id)

    print(f"jog: dispatching marathon-drive ({invocation['drive_command']})")
    proc = subprocess.run(argv, cwd=invocation["target_root"], env=env)
    record["drive_exit"] = proc.returncode

    try:
        receipt = load_marathon_result(invocation["result_path"])
    except ContractError as exc:
        record["status"] = "no-valid-result"
        jog_save_state(root, gid, state)
        return "failed", (f"marathon-drive exited {proc.returncode} without a valid result "
                          f"receipt: {exc}")
    record["status"] = "terminal"
    record["outcome"] = receipt["outcome"]
    record["reason"] = receipt["reason"]
    jog_save_state(root, gid, state)

    action, reason = jog_project_marathon_outcome(
        root, gh_num, receipt, auto_merge=auto_merge,
        execution_id=exec_id, result_path=invocation["result_path"])
    record["status"] = f"projected-{action}"
    record["projected_reason"] = reason
    jog_save_state(root, gid, state)
    return action, reason


# ── GH-280 Phase 3: explicit resume / gate-only retry / rebuild / landing semantics ────────────

def _jog_latest_receipt(root, gid, outcomes=None):
    """Newest loadable receipt (optionally filtered by outcome): (record, receipt) or (None, None).

    Scans executions newest-first; within an execution, its gate-retry receipts are newer than
    the original dispatch receipt (a green gate retry is the outcome that lands). History is
    read-only here — recovery never rewrites old receipts. Paths resolve relative-to-ledger
    (GH-292 F2) with absolute legacy paths still honored."""
    state = jog_load_state(root, gid)
    for record in reversed(state.get("executions") or []):
        candidates = [g.get("result_path") for g in reversed(record.get("gate_retries") or [])]
        candidates.append(record.get("result_path"))
        for rel_path in candidates:
            path = _ledger_abs_path(root, gid, rel_path)
            if not path or not os.path.isfile(path):
                continue
            try:
                receipt = load_marathon_result(path)
            except ContractError:
                continue
            if outcomes and receipt.get("outcome") not in outcomes:
                continue
            return record, receipt
    return None, None


def _jog_exec_dir(root, gid, record):
    packet_dir = _ledger_abs_path(root, gid, record.get("packet_dir"))
    return os.path.dirname(packet_dir or "") or \
        os.path.join(_jog_state_paths(root, gid)[0], record.get("execution_id", "exec"))


def jog_resume(root, gh_num, args=None):
    """`jog resume <GH>` — reconcile existing durable state, spend nothing.

    Reconciliation only: a valid terminal receipt is re-projected idempotently (no dispatch,
    no token); a dispatched execution without a receipt parks the row (the operator chooses
    retry-build); anything else is reported. Resume never fires Marathon on its own — a new
    fire is always the explicit retry-build decision."""
    gid = jog_resolve_ledger_gid(root, gh_num)
    if not gid:
        print(f"jog: GH-{gh_num} is not in the jog queue")
        sys.exit(2)
    state = jog_load_state(root, gid)
    executions = state.get("executions") or []
    if not executions:
        print(f"jog: GH-{gh_num} has no marathon execution state — run `releases jog run "
              f"--reviewer <agent>` (marathon is the default executor) or `jog retry-build` "
              f"to dispatch")
        return 0

    latest = executions[-1]
    record, receipt = _jog_latest_receipt(root, gid)
    if record is not None and record.get("execution_id") == latest.get("execution_id"):
        action, reason = jog_project_marathon_outcome(
            root, gh_num, receipt,
            execution_id=latest.get("execution_id"), result_path=latest.get("result_path"))
        latest["status"] = f"projected-{action}"
        latest["projected_reason"] = reason
        jog_save_state(root, gid, state)
        jog_set_status(root, gh_num, action, failure_reason=reason)
        print(f"jog: resume GH-{gh_num}: terminal Marathon result re-projected ({action}) — {reason}")
        return 0
    if latest.get("status") == "dispatched":
        # GH-291 Scope 2: distinguish a future-schema/invalid receipt from a missing one —
        # version skew must park with its cause named, not read as "no result".
        load_error = None
        _p = _ledger_abs_path(root, gid, latest.get("result_path"))
        if _p and os.path.isfile(_p):
            try:
                load_marathon_result(_p)
            except ContractError as exc:
                load_error = str(exc)
        latest["status"] = "cold-start-paused"
        jog_save_state(root, gid, state)
        jog_set_status(root, gh_num, "parked",
                       failure_reason="resume: dispatched Marathon execution has no valid result "
                                      "receipt"
                                      + (f" (load error: {load_error})" if load_error else "")
                                      + " — inspect, then `jog retry-build` if a rebuild is wanted")
        print(f"jog: resume GH-{gh_num}: execution {latest.get('execution_id')} dispatched with no "
              f"valid result{f' ({load_error})' if load_error else ''} — parked; no token spent")
        return 1
    print(f"jog: resume GH-{gh_num}: latest execution {latest.get('execution_id')} is "
          f"'{latest.get('status')}' — nothing to reconcile; use jog retry-gate / retry-build / land")
    return 0


def jog_retry_gate(root, gh_num, args):
    """`jog retry-gate <GH>` — re-run ONLY the gate against the same head SHA.

    Marathon's native satisfied-lane path (GH-274) is the mechanism: with the phase's relay
    terminal and its tick token done, re-invoking marathon-drive skips render/reseed/dispatch
    and re-runs the pre-advance gate alone. Jog refuses if the head SHA moves during the
    retry — that state needs retry-build, not a gate check."""
    error = validate_marathon_executor(args)
    if error:
        print(f"jog: {error}", file=sys.stderr)
        sys.exit(2)
    # GH-300 (B2): retry verbs dispatch marathon-drive exactly like the run executor, so
    # they hold the same supervisor lock — a retry fired beside a live drive is precisely
    # the concurrency the lock exists to prevent (GH-42 / GH-354).
    supervisor_lock = JogSupervisorLock(root)
    supervisor_lock.acquire()
    try:
        return _jog_retry_gate_locked(root, gh_num, args)
    finally:
        supervisor_lock.release()


def _jog_retry_gate_locked(root, gh_num, args):
    gid = jog_resolve_ledger_gid(root, gh_num)
    if not gid:
        # Same refusal retry-build already had: a None gid here would otherwise surface
        # as a TypeError traceback from jog_load_state instead of a clean exit.
        print(f"jog: GH-{gh_num} has no jog queue row and no execution ledger", file=sys.stderr)
        sys.exit(2)
    record, receipt = _jog_latest_receipt(root, gid, outcomes=("approved",))
    if record is None:
        # A red gate escalates with outcome 'escalated'; the relay behind it is terminal and
        # its receipt still names the head — retry-gate applies there too.
        record, receipt = _jog_latest_receipt(root, gid, outcomes=("escalated",))
    if record is None:
        print(f"jog: GH-{gh_num} has no terminal Marathon execution to gate-retry", file=sys.stderr)
        sys.exit(2)

    prior_head = receipt.get("head_sha")
    invocation_path = os.path.join(
        _ledger_abs_path(root, gid, record.get("packet_dir")), "marathon-invocation.json")
    try:
        invocation = load_marathon_invocation(invocation_path)
    except ContractError as exc:
        print(f"jog: cannot gate-retry — {exc}", file=sys.stderr)
        sys.exit(2)

    # The head-moved guard runs BEFORE dispatch: marathon's own runs commit transcripts (the
    # receipt head legitimately advances by those), so the meaningful invariant is that the
    # head is UNCHANGED between the execution and this retry — checked against the live repo
    # pre-dispatch, not against the post-run receipt (which would false-trip on the retry's
    # own transcript commit and burn a gate run to report it).
    pre_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=invocation["target_root"],
                              capture_output=True, text=True)
    if pre_head.returncode == 0 and pre_head.stdout.strip() != prior_head:
        print(f"jog: refusing gate retry for GH-{gh_num} — head is {pre_head.stdout.strip()[:8]} "
              f"but the execution ran on {str(prior_head or '')[:8]}; the head moved between "
              f"runs (use jog retry-build)", file=sys.stderr)
        sys.exit(2)

    state = jog_load_state(root, gid)
    entry = next((e for e in state.get("executions") or []
                  if e.get("execution_id") == record["execution_id"]), None)
    if entry is None:
        print(f"jog: ledger lost execution {record['execution_id']} — refusing to gate-retry",
              file=sys.stderr)
        sys.exit(2)
    gate_retries = entry.setdefault("gate_retries", [])
    attempt_no = len(gate_retries) + 1
    retry_dir = os.path.join(_jog_exec_dir(root, gid, record), f"gate-retry-{attempt_no}")
    os.makedirs(retry_dir, exist_ok=True)
    argv = _marathon_argv_from_invocation(invocation, args.builder, args.reviewer)
    argv += ["--execution-id", f"{record['execution_id']}-gateretry{attempt_no}",
             "--result-file", os.path.join(retry_dir, "marathon-result.json")]

    env = dict(os.environ)
    env.update(invocation["env"])
    env["RELAY_DRIVER_LOCKED"] = "1"
    print(f"jog: gate-only retry for GH-{gh_num} against head {prior_head} "
          f"(no builder turn; satisfied-lane path)")
    proc = subprocess.run(argv, cwd=invocation["target_root"], env=env)
    result_path = os.path.join(retry_dir, "marathon-result.json")
    try:
        new_receipt = load_marathon_result(result_path)
    except ContractError as exc:
        gate_retries.append({"execution_id": record["execution_id"], "attempt": attempt_no,
                             "status": "no-valid-result", "drive_exit": proc.returncode})
        jog_save_state(root, gid, state)
        print(f"jog: gate retry exited {proc.returncode} without a valid receipt: {exc}",
              file=sys.stderr)
        sys.exit(2)
    gate_retries.append({"execution_id": record["execution_id"], "attempt": attempt_no,
                         "status": new_receipt.get("outcome"),
                         "result_path": result_path})
    jog_save_state(root, gid, state)

    action, reason = jog_project_marathon_outcome(
        root, gh_num, new_receipt,
        auto_merge=getattr(args, "auto_merge", False),
        execution_id=f"{record['execution_id']}-gateretry{attempt_no}",
        result_path=_ledger_rel_path(root, gid, result_path))
    jog_set_status(root, gh_num, action, failure_reason=reason)
    print(f"jog: gate retry result: {new_receipt.get('outcome')} → queue {action} — {reason}")
    return 0 if new_receipt.get("outcome") == "approved" else 1


def jog_retry_build(root, gh_num, args):
    """`jog retry-build <GH>` — a fresh Marathon attempt on a fresh execution id.

    Marathon's namespaced attempt record is the sole retry cap: the lane key is unchanged, so
    attempts accumulate and the cap parks the lane exactly as an ordinary marathon caller
    would experience. All prior Tick history and execution records are preserved."""
    error = validate_marathon_executor(args)
    if error:
        print(f"jog: {error}", file=sys.stderr)
        sys.exit(2)
    # GH-300 (B2): same supervisor lock as the run executor — see jog_retry_gate.
    supervisor_lock = JogSupervisorLock(root)
    supervisor_lock.acquire()
    try:
        return _jog_retry_build_locked(root, gh_num, args)
    finally:
        supervisor_lock.release()


def _jog_retry_build_locked(root, gh_num, args):
    gid = jog_resolve_ledger_gid(root, gh_num) or jog_current_gid(root, gh_num)
    if not gid:
        print(f"jog: GH-{gh_num} is not in the jog queue", file=sys.stderr)
        sys.exit(2)
    conn = sqlite3.connect(os.path.join(root, "releases.db"))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT status FROM jog_queue WHERE global_id = ?", (gid,)).fetchone()
        if row and row["status"] == "running":
            print(f"jog: GH-{gh_num} has a live lease — resume or wait; retry-build refused",
                  file=sys.stderr)
            sys.exit(2)
    finally:
        conn.close()

    jog_acquire_lease(root, gh_num, os.getpid())
    action, reason = run_marathon_phase(
        root, gh_num, gid,
        builder=getattr(args, "builder", "agy"), reviewer=args.reviewer,
        auto_merge=getattr(args, "auto_merge", False), mode="retry-build")
    jog_set_status(root, gh_num, action, failure_reason=reason)
    print(f"jog: retry-build GH-{gh_num} → {action} — {reason}")
    return 0 if action in ("completed", "parked") else 1


def _gh_pr_view(root, pr_number):
    out = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--json",
         "number,url,state,baseRefName,headRefName,headRefOid,mergedAt,mergeCommit,title,body"],
        cwd=root, capture_output=True, text=True)
    if out.returncode != 0:
        return None, (out.stderr or "gh pr view failed").strip()
    try:
        return json.loads(out.stdout), None
    except ValueError as exc:
        return None, f"gh pr view returned unparseable JSON: {exc}"


def jog_land(root, gh_num, pr_arg=None):
    """`jog land <GH> [--pr N|URL]` — verify merged delivery, complete the row, delegate lifecycle.

    Replay-safe order (the plan's idempotency key is (repo, gid, execution id, merged SHA)):
      1. verify GitHub truth (PR identity, merged state, base/head/head-SHA match against the
         execution receipt, merge-SHA reachability, qualifying gate evidence)
      2. persist the landing projection (queue completed + ledger landing record)
      3. invoke wave_reconcile.py --pr <N> with the verified PR metadata as its offline manifest
      4. persist reconciliation evidence
    A crash at any boundary resumes at the first missing durable step on re-run."""
    gid = jog_resolve_ledger_gid(root, gh_num)
    if not gid:
        print(f"jog: GH-{gh_num} has no jog queue row and no execution ledger", file=sys.stderr)
        sys.exit(2)
    record, receipt = _jog_latest_receipt(root, gid, outcomes=("approved",))
    if record is None:
        print(f"jog: GH-{gh_num} has no approved Marathon execution to land — nothing terminal "
              f"with a green outcome is on record", file=sys.stderr)
        sys.exit(2)

    # A gate-only retry inherits its lane from the original dispatch but never passes the
    # branch guard (the satisfied-lane short-circuit runs first), and a rebuild fired while
    # the lane branch is already checked out likewise records no redirect. Branch identity is
    # stable across one issue's execution family: fall back to the newest receipt in the
    # ledger that carries base/head — never guess.
    if not receipt.get("base_branch") or not receipt.get("head_branch"):
        _state_all = jog_load_state(root, gid)
        for _rec in reversed(_state_all.get("executions") or []):
            for _path in ([g.get("result_path") for g in reversed(_rec.get("gate_retries") or [])]
                          + [_rec.get("result_path")]):
                _path = _ledger_abs_path(root, gid, _path)
                if not _path or not os.path.isfile(_path):
                    continue
                try:
                    _other = load_marathon_result(_path)
                except (ContractError, OSError):
                    continue
                for field in ("base_branch", "head_branch"):
                    if not receipt.get(field) and _other.get(field):
                        receipt[field] = _other[field]
            if receipt.get("base_branch") and receipt.get("head_branch"):
                break

    # ── PR identity: explicit --pr wins, but only after matching it against the receipt.
    pr_number = None
    if pr_arg:
        m = re.search(r"/pull/(\d+)|^#?(\d+)$", str(pr_arg).strip())
        pr_number = (m.group(1) or m.group(2)) if m else None
        if not pr_number:
            print(f"jog: --pr expects a PR number or URL, got {pr_arg!r}", file=sys.stderr)
            sys.exit(2)
    else:
        pr_number = (receipt.get("pr") or {}).get("number")
        if not pr_number:
            print(f"jog: receipt for {record['execution_id']} has no PR identity — pass "
                  f"`--pr <N|URL>` after opening one from its branches "
                  f"(head={receipt.get('head_branch')}, base={receipt.get('base_branch')})",
                  file=sys.stderr)
            sys.exit(2)

    # ── Step 1: verify GitHub truth against the execution receipt.
    pr, err = _gh_pr_view(root, pr_number)
    if pr is None:
        print(f"jog: could not verify PR #{pr_number}: {err}", file=sys.stderr)
        sys.exit(2)
    checks = [
        ("state MERGED", pr.get("state") == "MERGED"),
        (f"base {receipt.get('base_branch')}", pr.get("baseRefName") == receipt.get("base_branch")),
        (f"head {receipt.get('head_branch')}", pr.get("headRefName") == receipt.get("head_branch")),
        (f"head SHA {str(receipt.get('head_sha') or '')[:8]}",
         pr.get("headRefOid") == receipt.get("head_sha")),
        ("receipt repo is this repo",
         not receipt.get("target_repo", {}).get("path")
         or os.path.realpath(receipt["target_repo"]["path"]) == os.path.realpath(root)),
    ]
    gate = receipt.get("gate") or {}
    checks.append(("gate green on the landed head",
                   gate.get("result") == "green"
                   and (not gate.get("receipt_path") or os.path.isfile(gate["receipt_path"]))))
    merged_sha = ((pr.get("mergeCommit") or {}).get("oid")) or None
    checks.append(("merge commit present", bool(merged_sha)))
    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"jog: refusing to land GH-{gh_num} via PR #{pr_number} — failed verification: "
              f"{', '.join(failed)}", file=sys.stderr)
        sys.exit(2)
    base_ref = pr.get("baseRefName")
    reach = subprocess.run(["git", "merge-base", "--is-ancestor", merged_sha, base_ref],
                           cwd=root, capture_output=True)
    if reach.returncode != 0:
        print(f"jog: merge commit {merged_sha[:8]} is not reachable from '{base_ref}' — refusing "
              f"to land GH-{gh_num}", file=sys.stderr)
        sys.exit(2)

    # ── Step 2: persist the landing projection (idempotent by key).
    state = jog_load_state(root, gid)
    entry = next((e for e in state.get("executions") or []
                  if e.get("execution_id") == record["execution_id"]), None)
    if entry is None:
        print(f"jog: ledger lost execution {record['execution_id']} — refusing to land",
              file=sys.stderr)
        sys.exit(2)
    landing = entry.setdefault("landing", {})
    key = {
        "repo": (receipt.get("target_repo") or {}).get("origin_url") or root,
        "gid": gid,
        "execution_id": record["execution_id"],
        "merged_sha": merged_sha,
    }
    if landing.get("key") != key:
        landing.update({
            "key": key,
            "pr_number": int(pr_number),
            "pr_url": pr.get("url"),
            "merged_at": pr.get("mergedAt"),
            "landed_via": "jog land",
            "landed_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        jog_save_state(root, gid, state)
        jog_set_status(root, gh_num, "completed",
                       failure_reason=f"landed via PR #{pr_number} (merged {merged_sha[:8]})")
        print(f"jog: GH-{gh_num} landed — PR #{pr_number} merged into {base_ref} at {merged_sha[:8]}")
    else:
        print(f"jog: landing projection already recorded for PR #{pr_number} — replaying "
              f"missing steps only")

    # ── Step 3: delegate lifecycle closeout to wave_reconcile.py (idempotent).
    if landing.get("reconciled"):
        print(f"jog: GH-{gh_num} already reconciled at {landing.get('reconciled_at')} — nothing to do")
        return 0
    manifest = {
        "prs": [{
            "number": int(pr_number),
            "title": pr.get("title") or f"GH-{gh_num}",
            "state": "MERGED",
            "mergedAt": pr.get("mergedAt"),
            "baseRefName": pr.get("baseRefName"),
            "headRefName": pr.get("headRefName"),
            "body": pr.get("body") or f"Closes #{gh_num}",
        }],
        "source": "jog land (verified gh pr view)",
    }
    exec_dir = _jog_exec_dir(root, gid, record)
    os.makedirs(exec_dir, exist_ok=True)
    manifest_path = os.path.join(exec_dir, "wave-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    # The tree is never pristine here (jog's own tracked releases.db/sql writes), and the pull/
    # branch checks belong to an operator's working context, not this supervised closeout; the
    # offline manifest carries the PR truth verified seconds ago, so no second network fetch.
    reconcile_py = os.path.join(harness_home(), "utils", "py", "wave_reconcile.py")
    proc = subprocess.run(
        [sys.executable, reconcile_py, "--root", root, "--pr", str(pr_number),
         "--offline", manifest_path, "--skip-pull", "--skip-branch-check", "--allow-dirty"],
        cwd=root)
    if proc.returncode != 0:
        print(f"jog: wave_reconcile exited {proc.returncode} — landing is recorded; re-run "
              f"`jog land GH-{gh_num}` to resume reconciliation at this step", file=sys.stderr)
        sys.exit(6)

    # ── Step 4: persist reconciliation evidence.
    state = jog_load_state(root, gid)
    for entry in state.get("executions") or []:
        if entry.get("execution_id") == record["execution_id"]:
            entry.setdefault("landing", {}).update({
                "key": key,
                "reconciled": True,
                "reconciled_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "manifest_path": manifest_path,
            })
    jog_save_state(root, gid, state)
    print(f"jog: GH-{gh_num} lifecycle reconciled (wave_reconcile --pr {pr_number})")
    return 0


class JogSupervisorLock:
    """Outer driver lock supervisor ensuring exclusive execution on the clone."""

    def __init__(self, root):
        self.root = root
        self.lock_dir, self.lock_label = driver_lock_path(root)
        self.acquired = False

    def acquire(self):
        try:
            os.mkdir(self.lock_dir)
            self.acquired = True
        except OSError:
            holder = ""
            pid_file = os.path.join(self.lock_dir, "pid")
            if os.path.isfile(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        holder = f.read().strip()
                except Exception:
                    pass

            is_running = False
            if holder and holder.isdigit():
                try:
                    os.kill(int(holder), 0)
                    is_running = True
                except OSError:
                    pass

            if is_running:
                print(
                    f"jog: another driver is active in this repo (pid {holder}, lock: {self.lock_label}).\n"
                    f"jog: Concurrent runs in the same clone are unsafe (GH-42 / GH-354).",
                    file=sys.stderr,
                )
                sys.exit(4)

            print(
                f"jog: reclaiming stale relay-driver.lock (holder pid {holder or 'none'} not running).",
                file=sys.stderr,
            )
            try:
                shutil.rmtree(self.lock_dir)
                os.mkdir(self.lock_dir)
                self.acquired = True
            except Exception as exc:
                print(f"jog: could not acquire relay-driver.lock: {exc}", file=sys.stderr)
                sys.exit(4)

        try:
            with open(os.path.join(self.lock_dir, "pid"), "w") as f:
                f.write(f"{os.getpid()}\n")
        except Exception:
            pass

        os.environ["RELAY_DRIVER_LOCKED"] = "1"

    def release(self):
        if self.acquired:
            try:
                if os.path.exists(self.lock_dir):
                    shutil.rmtree(self.lock_dir)
            except Exception:
                pass
            self.acquired = False


def lint_probe(root, probe_cmd):
    """Lint a probe command to ensure it is non-trivial and resolves to a real target."""
    cmd = probe_cmd.strip()
    if not cmd:
        return False, "empty probe command"
    for pat in TRIVIAL_PROBE_PATTERNS:
        if pat.match(cmd):
            return False, f"trivial probe pattern rejected: {cmd!r}"

    # Verify referenced file/glob resolves if command specifies a test path
    tokens = cmd.split()
    if len(tokens) >= 2 and tokens[0] in ("bash", "sh", "python3", "pytest"):
        target_path = tokens[1]
        # Resolve target relative to root
        full_pattern = os.path.join(root, target_path)
        matches = glob.glob(full_pattern)
        if not matches and not os.path.exists(full_pattern):
            return False, f"probe target path does not resolve: {target_path}"

    return True, "ok"


def find_issue_doc(root, gh_num):
    """Find the capture/working doc associated with an issue number."""
    patterns = [
        os.path.join(root, "PROJECT", "2-WORKING", f"GH-{gh_num}-*.md"),
        os.path.join(root, "PROJECT", "1-INBOX", f"GH-{gh_num}-*.md"),
        os.path.join(root, "PROJECT", "3-COMPLETED", f"GH-{gh_num}-*.md"),
    ]
    for pat in patterns:
        matches = glob.glob(pat)
        if matches:
            return matches[0]
    return None


def extract_probes_from_doc(doc_path):
    """Extract fix_probes from doc frontmatter or body."""
    if not os.path.isfile(doc_path):
        return []
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    probes = []
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        probes_match = re.search(r"fix_probes:\s*\n((?:\s+-\s+.*\n?)+)", fm_text)
        if probes_match:
            for line in probes_match.group(1).splitlines():
                line = line.strip()
                if line.startswith("- "):
                    p = line[2:].strip().strip("\"'")
                    if p:
                        probes.append(p)
    return probes


def promote_contract_to_working(root, gh_num, doc_path, interactive=True):
    """Promote a 1-INBOX doc to 2-WORKING/ with verified status table and probes."""
    basename = os.path.basename(doc_path)
    new_doc_path = os.path.join(root, "PROJECT", "2-WORKING", basename)
    rel_new_path = os.path.relpath(new_doc_path, root)

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure status table exists
    if "## Status" not in content:
        status_table = (
            "\n## Status\n\n"
            "| What was just completed | What's next |\n"
            "|---|---|\n"
            "| Promoted to active working contract via jog | Execute implementation and verify probes |\n\n"
        )
        if "---" in content:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = re.sub(r"(?m)^status:\s*.*$", "status: Active", parts[1])
                today = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
                fm = re.sub(r"(?m)^updated:\s*.*$", f"updated: {today}", fm)
                content = f"---{fm}---{status_table}{parts[2].lstrip()}"
        else:
            content = status_table + content

    probes = extract_probes_from_doc(doc_path)
    valid_probes = []
    for p in probes:
        ok, reason = lint_probe(root, p)
        if ok:
            valid_probes.append(p)

    if not valid_probes:
        if not interactive:
            return None, "unreviewed-probe-contract (no valid probes in unattended mode)"

    if interactive and sys.stdin.isatty():
        print(f"\n[jog] Auto-promoted contract for GH-{gh_num}:")
        print(f"      Source: {doc_path}")
        print(f"      Target: {new_doc_path}")
        print(f"      Probes: {valid_probes or '(none declared)'}")
        resp = input(f"Proceed with preflight for GH-{gh_num}? [Y/n] ").strip().lower()
        if resp in ("n", "no"):
            return None, "promotion-cancelled-by-operator"

    # Move doc to 2-WORKING
    os.makedirs(os.path.dirname(new_doc_path), exist_ok=True)
    with open(new_doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Use git mv or clean deletion
    try:
        git_res = subprocess.run(["git", "rm", "-f", doc_path], cwd=root, capture_output=True)
        if git_res.returncode != 0 and os.path.exists(doc_path):
            os.remove(doc_path)
    except Exception:
        if os.path.exists(doc_path):
            os.remove(doc_path)

    try:
        subprocess.run(["git", "add", new_doc_path], cwd=root, capture_output=True)
    except Exception:
        pass

    # Repoint roadmap item
    rp_res = subprocess.run(
        [
            sys.executable,
            os.path.join(root, "utils", "py", "releases_app.py"),
            "roadmap",
            "repoint",
            "--issue-num",
            str(gh_num),
            "--doc-path",
            rel_new_path,
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if rp_res.returncode != 0:
        print(f"jog: warning: roadmap repoint returned code {rp_res.returncode}: {rp_res.stderr.strip()}", file=sys.stderr)

    return new_doc_path, None


def run_single_phase_drive(root, gh_num, builder="agy", reviewer=None, simulate=False):
    """Execute a single-phase drive for a task using relay-drive.

    GH-505: the drive is a builder turn followed by a REVIEWER turn; relay-drive attests only the
    reviewer's approval. Same reviewer policy as the marathon executor (explicit, different agent).
    """
    if simulate:
        print(f"jog: [simulate] simulated single-phase drive on GH-{gh_num} with builder={builder}")
        return 0
    if not reviewer:
        print("jog: --reviewer <agent> is required for the relay executor too — relay-drive accepts a terminal STATUS only from the named reviewer (GH-505)", file=sys.stderr)
        return 2
    if reviewer == builder:
        print(f"jog: --reviewer must differ from --builder (both are '{reviewer}')", file=sys.stderr)
        return 2

    # Locate relay-drive and turn runner shims
    drive_candidates = [
        os.path.join(root, "relay-automation", "relay-drive.sh"),
        os.path.join(root, ".xyz", "relay-automation", "relay-drive.sh"),
    ]
    drive_script = None
    for c in drive_candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            drive_script = c
            break

    # GH-505: two agents take turns, so dispatch through the shared per-actor router (the same one
    # marathon uses) instead of a single builder shim.
    shim_candidates = [
        os.path.join(root, "relay-automation", "marathon-agent.sh"),
        os.path.join(root, ".xyz", "relay-automation", "marathon-agent.sh"),
    ]
    shim_script = None
    for c in shim_candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            shim_script = c
            break

    if not drive_script or not shim_script:
        print(
            f"jog: runner scripts not found or not executable (drive={drive_script}, shim={shim_script})",
            file=sys.stderr,
        )
        return 2

    # Scaffold single-phase relay review thread file if absent
    today_str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    relay_dir = os.path.join(root, "relay-system", today_str)
    os.makedirs(relay_dir, exist_ok=True)
    relay_file = os.path.join(relay_dir, f"gh{gh_num}-jog-drive.md")

    if not os.path.isfile(relay_file):
        with open(relay_file, "w", encoding="utf-8") as f:
            f.write(
                f"# RELAY · GH-{gh_num} Jog Serial Drive\n\n"
                f"NEXT: {builder}\n"
                f"STATUS: Open\n"
                f"ROUND: 1 / 2\n\n"
                f"## Setup\n"
                f"- Issue: GH-{gh_num}\n"
                f"- Builder: {builder}\n"
                f"- Reviewer: {reviewer}\n"
                f"- Started: {today_str}\n\n"
                f"## Log\n\n"
                f"### Round 1 — Producer (jog) — {today_str}\n"
                f"Dispatched task GH-{gh_num} for execution.\n\n"
                f"NEXT: {builder}\n"
            )

    task_name = f"RELAY-gh{gh_num}-jog-drive"
    tick_bin = os.path.join(root, "bin", "tick")
    if os.path.isfile(tick_bin) and os.access(tick_bin, os.X_OK):
        subprocess.run([tick_bin, "log", "task.created", task_name, "--agent", "jog"], cwd=root, capture_output=True)
        subprocess.run([tick_bin, "claim", task_name, "--agent", "jog", "--paths", relay_file], cwd=root, capture_output=True)
        subprocess.run([tick_bin, "release", task_name, "--agent", "jog", "--to", builder], cwd=root, capture_output=True)

    cmd = [
        drive_script,
        "--relay-file",
        relay_file,
        "--agent-cmd",
        shim_script,
        "--relay-task",
        task_name,
        "--reviewer", reviewer,
        "--builder", builder,
    ]
    env = dict(os.environ)
    env["RELAY_DRIVER_LOCKED"] = "1"
    env["XYZ_ROOT"] = root
    env["MARATHON_BUILDER"] = builder
    env["MARATHON_REVIEWER"] = reviewer
    env[f"{reviewer.upper()}_AGENT"] = reviewer
    env.setdefault(f"{reviewer.upper()}_LOG",
                   os.path.join(tempfile.gettempdir(), f"{reviewer}-turn-jog-{os.getpid()}.log"))
    # Turn-taker shim env contract (relay-xyz Path A): <BUILDER>_AGENT selects the
    # dispatching actor (must match the tick token's handoff target above), ALLOW_PATHS
    # (comma-separated) grants the contract's artifact paths for a build turn, and
    # <BUILDER>_LOG keeps concurrent runs from sharing one log. Without these the shim
    # dies at startup ("AGY_AGENT required") before any turn runs.
    env[f"{builder.upper()}_AGENT"] = builder
    env.setdefault(f"{builder.upper()}_LOG",
                   os.path.join(tempfile.gettempdir(), f"{builder}-turn-jog-{os.getpid()}.log"))
    doc = find_issue_doc(root, gh_num)
    artifacts = []
    if doc:
        m = re.search(r"##\s*Swarm Preflight Contract\s*\n+```json\n(.*?)\n```", open(doc).read(), re.S)
        if m:
            try:
                artifacts = [a for a in json.loads(m.group(1)).get("artifacts", []) if isinstance(a, str)]
            except Exception:
                pass
    env["ALLOW_PATHS"] = ",".join(artifacts)

    proc = subprocess.run(cmd, cwd=root, env=env)
    # GH-505: the driver's exit IS the verdict. The override that used to live here read the
    # relay file's STATUS word and turned a non-zero driver exit into 0 when it said Approved —
    # the exact word a builder turn can write. Deleted; relay-drive now attests approvals itself.
    return proc.returncode


def _verify_legacy_pr_before_merge(root, pr_num):
    """GH-300: minimal pre-merge guard for the relay-path landing boundary.

    The legacy path has no marathon receipt to verify against — it discovers its PR by
    branch-name convention — so the guard is the subset that convention can support: the
    discovered PR must be OPEN and based on development before it is merged. Returns None
    when the merge may proceed, else the failed-check names.
    """
    pr, err = _gh_pr_view(root, pr_num)
    if pr is None:
        return [f"pr view failed: {err}"]
    return [name for name, ok in [
        ("state OPEN", pr.get("state") == "OPEN"),
        ("base development", pr.get("baseRefName") == "development"),
    ] if not ok]


def _tick_bin(root):
    for cand in (os.environ.get("TICK_BIN"), os.path.join(root, "bin", "tick"),
                 os.path.join(harness_home(), "bin", "tick")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _token_done(root, task):
    """GH-505: the relay token must READ done in the pinned tick root — a record alone is not a
    verdict. Returns (ok, reason)."""
    tick = _tick_bin(root)
    if not tick:
        return False, "tick CLI not found"
    # The token lives in the repo jog operates on — never an ambient TICK_REPO_ROOT from a parent shell.
    env = dict(os.environ); env["TICK_REPO_ROOT"] = root
    info = subprocess.run([tick, "info", task], cwd=root, env=env, capture_output=True, text=True)
    if info.returncode != 0:
        return False, f"token {task} unreadable ({(info.stderr or '').strip() or 'tick info failed'})"
    for line in (info.stdout or "").splitlines():
        if line.startswith("status:"):
            st = line.split(":", 1)[1].strip()
            return (st == "done"), (None if st == "done" else f"token {task} reads {st or 'unknown'}, not done")
    return False, f"token {task} not found"


def _merge_reviewed_pr(root, pr_num, record, expected_candidate=None):
    """GH-505/GH-509/GH-510: the ONE merge step for every jog landing branch.

    Merges only the revision the reviewer's attestation covers: the PR head must be the reviewed
    revision plus transcript-only commits (`candidate_ok`), it must equal `expected_candidate` when
    the caller has one (marathon's validated `reviewed_candidate`), and the merge is bound to that
    exact SHA with --match-head-commit so the checked object is the merged object. A refused or
    failed merge PARKS — never "completed" (GH-510).

    Returns (merged: bool, reason: str or None).
    """
    if record is None:
        return False, "merge refused: no valid reviewer attestation for this task (GH-505)"
    done, why = _token_done(root, record["task"])
    if not done:
        return False, f"merge refused: {why} (GH-505)"
    view = subprocess.run(["gh", "pr", "view", str(pr_num), "--json", "headRefOid"],
                          cwd=root, capture_output=True, text=True)
    try:
        candidate = (json.loads(view.stdout or "{}").get("headRefOid") or "").strip() if view.returncode == 0 else ""
    except ValueError:
        candidate = ""
    if not candidate:
        return False, f"merge refused: could not read PR #{pr_num} head ({(view.stderr or view.stdout or '').strip() or 'empty'})"
    if expected_candidate and candidate != expected_candidate:
        return False, (f"merge refused: PR #{pr_num} head {candidate[:12]} is not the validated candidate "
                       f"{expected_candidate[:12]} (candidate-drifted-from-reviewed-head)")
    ok, why = relay_attest.candidate_ok(record, candidate, root)
    if not ok:
        return False, f"merge refused: {why} (candidate-drifted-from-reviewed-head)"
    merge = subprocess.run(["gh", "pr", "merge", str(pr_num), "--merge", "--auto=false",
                            "--match-head-commit", candidate],
                           cwd=root, capture_output=True, text=True)
    if merge.returncode != 0:
        return False, f"merge failed (gh exit {merge.returncode}): {(merge.stderr or merge.stdout or '').strip()}"
    return True, None


def _legacy_attestation(root, gh_num, reviewer):
    task = f"RELAY-gh{gh_num}-jog-drive"
    relay_file = None
    for d in sorted(glob.glob(os.path.join(root, "relay-system", "*")), reverse=True):
        cand = os.path.join(d, f"gh{gh_num}-jog-drive.md")
        if os.path.isfile(cand):
            relay_file = cand
            break
    if not relay_file:
        return None, f"no relay file found for GH-{gh_num}"
    return relay_attest.load(task, expected_reviewer=reviewer, relay_file=relay_file, target_repo=root)


def handle_landing_boundary(root, gh_num, auto_merge=False, reviewer=None, simulate=False):
    """Handle landing confirmation, PR merge, and development re-anchoring.

    Returns:
        (success: bool, status: str, failure_reason: str or None)
    """
    if simulate:
        # GH-505: nothing was driven and nothing is merged; say so instead of pretending a PR landed.
        print(f"jog: [simulate] simulated landing for GH-{gh_num} (no PR, no merge)")
        return True, "completed", None
    record, why = _legacy_attestation(root, gh_num, reviewer)
    if auto_merge:
        print(f"jog: task GH-{gh_num} passed; auto-merging into development...")
        # Check for active PR via gh
        pr_view = subprocess.run(
            ["gh", "pr", "list", "--head", f"feat/gh{gh_num}", "--json", "number,state", "--jq", ".[0].number"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        pr_num = pr_view.stdout.strip()
        if pr_num and pr_num.isdigit():
            failures = _verify_legacy_pr_before_merge(root, pr_num)
            if failures:
                print(f"jog: auto-merge refused (verification failed: {', '.join(failures)})",
                      file=sys.stderr)
                return False, "parked", f"auto-merge refused (verification failed: {', '.join(failures)})"
            merged, reason = _merge_reviewed_pr(root, pr_num, record)
            if not merged:
                print(f"jog: auto-merge refused/failed: {reason}", file=sys.stderr)
                return False, "parked", f"auto-{reason}"
        else:
            # GH-510: no PR is not a landed task.
            return False, "parked", f"awaiting-landing (no open PR found for feat/gh{gh_num})"

        # Re-anchor on development
        subprocess.run(["git", "checkout", "development"], cwd=root, capture_output=True)
        subprocess.run(["git", "pull", "--ff-only", "origin", "development"], cwd=root, capture_output=True)
        return True, "completed", None

    if not sys.stdin.isatty():
        print(f"jog: unattended run without --auto-merge -> parking GH-{gh_num} awaiting landing confirmation.")
        return False, "parked", "awaiting-landing (unattended run without --auto-merge)"

    print(f"\n[jog] Task GH-{gh_num} completed drive pass.")
    resp = input(f"Confirm merge into development and advance to next item? [Y/n] ").strip().lower()
    if resp in ("n", "no"):
        print(f"jog: operator paused merge for GH-{gh_num}; parking item in awaiting-landing state.")
        return False, "parked", "awaiting-landing (operator paused merge)"

    # Operator confirmed merge
    pr_view = subprocess.run(
        ["gh", "pr", "list", "--head", f"feat/gh{gh_num}", "--json", "number,state", "--jq", ".[0].number"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    pr_num = pr_view.stdout.strip()
    if pr_num and pr_num.isdigit():
        failures = _verify_legacy_pr_before_merge(root, pr_num)
        if failures:
            print(f"jog: merge refused (verification failed: {', '.join(failures)}) — parking; "
                  f"the discovered PR is not mergeable into development as confirmed",
                  file=sys.stderr)
            return False, "parked", f"merge refused (verification failed: {', '.join(failures)})"
        merged, reason = _merge_reviewed_pr(root, pr_num, record)
        if not merged:
            # GH-510: this branch used to discard the merge result and report completed.
            print(f"jog: {reason} — parking GH-{gh_num}", file=sys.stderr)
            return False, "parked", reason
    else:
        return False, "parked", f"awaiting-landing (no open PR found for feat/gh{gh_num})"

    subprocess.run(["git", "checkout", "development"], cwd=root, capture_output=True)
    subprocess.run(["git", "pull", "--ff-only", "origin", "development"], cwd=root, capture_output=True)
    return True, "completed", None


def jog_run_main(args=None):
    """Main execution loop for jog supervisor."""
    if args is None:
        parser = argparse.ArgumentParser(description="Jog serial execution runner")
        parser.add_argument("--root", default=None, help="repository root path")
        parser.add_argument("--auto-merge", action="store_true", help="auto-merge passing PRs")
        parser.add_argument("--builder", default="agy", help="builder turn-taker (agy, codex, aider)")
        parser.add_argument("--reviewer", default=None,
                            help="reviewer agent — REQUIRED with --executor marathon (the "
                                 "default executor; no default is selected; must differ from "
                                 "--builder)")
        parser.add_argument("--executor", choices=["relay", "marathon"], default="marathon",
                            help="per-task executor (GH-280 Phase 5): 'marathon' is the default — "
                                 "the reviewed one-phase driver via the structured contracts, "
                                 "requires --reviewer; 'relay' is the legacy rollback path kept "
                                 "for a documented compatibility window")
        parser.add_argument("--max-tasks", type=int, default=None, help="max tasks to process")
        parser.add_argument("--simulate", action="store_true", help="simulate drive execution (test mode)")
        parser.add_argument("--dry-run", action="store_true", help="simulate queue run without mutations")
        args = parser.parse_args()

    # GH-280 Phase 5: marathon is the default executor. A namespace without an `executor`
    # attribute (programmatic callers) resolves to the same default as the CLI.
    executor = getattr(args, "executor", "marathon") or "marathon"
    simulate = getattr(args, "simulate", False)
    dry_run = getattr(args, "dry_run", False)

    # GH-280: reviewer/executor validation happens BEFORE the driver lock or any lease — an
    # invalid configuration must not mutate queue state at all. --simulate and --dry-run are
    # excluded: both stay on the hermetic/relay machinery and dispatch no Marathon execution,
    # so the reviewer policy (which governs real dispatches) does not apply to them.
    if executor == "marathon" and not simulate and not dry_run:
        executor_error = validate_marathon_executor(args)
        if executor_error:
            print(f"jog: {executor_error}", file=sys.stderr)
            sys.exit(2)

    # GH-280 Phase 5: anything still on the relay machinery is legacy — explicit
    # `--executor relay` (THE documented rollback path) or `--simulate` (which stays on the
    # relay machinery by design). --dry-run dispatches nothing, so it stays silent.
    if not dry_run and (executor == "relay" or simulate):
        print(JOG_RELAY_DEPRECATION_NOTICE, file=sys.stderr)

    root = os.path.abspath(getattr(args, "root", None) or os.getcwd())
    db_path = os.path.join(root, "releases.db")

    if not os.path.exists(db_path):
        print(f"jog: releases.db not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    # Hermetic --dry-run: zero mutations, zero locks, zero DB writes
    if getattr(args, "dry_run", False):
        print(f"jog: [dry-run] simulating queue execution (root: {root})")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            _ensure_jog_schema(conn)
            rows = conn.execute(
                "SELECT gh_number, position, attempt_count FROM jog_queue WHERE status = 'pending' ORDER BY position ASC"
            ).fetchall()
            if not rows:
                print("jog: [dry-run] queue is empty (0 pending items).")
                return
            max_t = getattr(args, "max_tasks", None)
            limit_str = f" (capped at {max_t})" if max_t is not None else ""
            print(f"jog: [dry-run] would process {len(rows)} pending item(s){limit_str}:")
            for idx, r in enumerate(rows):
                if max_t is not None and idx >= max_t:
                    break
                print(f"  {r['position']}. GH-{r['gh_number']} (builder={args.builder}, auto_merge={args.auto_merge})")
        finally:
            conn.close()
        return

    supervisor_lock = JogSupervisorLock(root)
    supervisor_lock.acquire()

    def _cleanup():
        supervisor_lock.release()

    atexit.register(_cleanup)

    def _signal_handler(signum, frame):
        print("\njog: interrupted by signal; cleaning up leases and locks.", file=sys.stderr)
        _cleanup()
        sys.exit(130)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        # Reconcile orphan leases via perform_write on startup
        reconciled = jog_reconcile_orphan_leases(root)
        if reconciled:
            print(f"jog: reconciled orphan lease(s) for: {', '.join('GH-%d' % n for n in reconciled)}")
            if executor == "marathon" and not simulate:
                # GH-280 cold start: a dispatched Marathon execution on a crashed row is
                # reconciled from its durable result BEFORE the loop can lease and refire.
                jog_reconcile_cold_start(root, reconciled)

        tasks_processed = 0
        while True:
            if args.max_tasks is not None and tasks_processed >= args.max_tasks:
                print(f"jog: reached max-tasks limit ({args.max_tasks}); pausing queue.")
                break

            # Query next pending task
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                _ensure_jog_schema(conn)
                row = conn.execute(
                    """SELECT id, global_id, gh_number, position, attempt_count
                       FROM jog_queue
                       WHERE status = 'pending'
                       ORDER BY position ASC, id ASC
                       LIMIT 1"""
                ).fetchone()
            finally:
                conn.close()

            if not row:
                print("jog: queue complete (0 pending tasks).")
                break

            gh_num = row["gh_number"]
            att = row["attempt_count"] + 1

            # Acquire lease via perform_write
            jog_acquire_lease(root, gh_num, os.getpid())

            print(f"\n{'=' * 60}")
            print(f"jog: processing GH-{gh_num} (attempt {att}) at position {row['position']}")
            print(f"{'=' * 60}")

            doc_path = find_issue_doc(root, gh_num)
            if doc_path and "/PROJECT/1-INBOX/" in doc_path:
                print(f"jog: promoting 1-INBOX contract for GH-{gh_num} to 2-WORKING...")
                promoted_path, err = promote_contract_to_working(
                    root, gh_num, doc_path, interactive=sys.stdin.isatty()
                )
                if err:
                    print(f"jog: contract promotion failed: {err}")
                    jog_set_status(root, gh_num, "parked", failure_reason=err)
                    continue
                doc_path = promoted_path

            # GH-280 Phase 5: the DEFAULT Marathon executor — Jog leases the row, delegates
            # execution to the reviewed one-phase driver through the structured contracts, and
            # projects the receipt's outcome. No Tick seeding, relay rendering, branch choice,
            # gate, or PR discovery happens here; the legacy relay path below is reached only
            # via --executor relay or --simulate during the compatibility window.
            if executor == "marathon" and not simulate:
                ledger_gid = jog_resolve_ledger_gid(root, gh_num) or row["global_id"]
                action, reason = run_marathon_phase(
                    root, gh_num, ledger_gid,
                    builder=args.builder, reviewer=args.reviewer,
                    auto_merge=getattr(args, "auto_merge", False))
                jog_set_status(root, gh_num, action, failure_reason=reason)
                jog_regenerate_dashboard(root)
                if action == "completed":
                    tasks_processed += 1
                    continue
                if action == "failed":
                    print("jog: stopping queue execution on task failure.")
                else:
                    print("jog: advancing halted at landing boundary.")
                break

            # Swarm Preflight check
            preflight_py = os.path.join(root, "utils", "py", "swarm_preflight.py")
            if os.path.isfile(preflight_py) and not getattr(args, "simulate", False):
                pf_res = subprocess.run(
                    # swarm_preflight.py has no --root flag (it resolves the repo from cwd,
                    # which this subprocess already pins below); passing one is a usage error
                    # that parked every queue item on the first real run.
                    [sys.executable, preflight_py, "--gh-issue", str(gh_num)],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                if pf_res.returncode == 4:
                    print(f"jog: GH-{gh_num} preflight reported already-landed (auto-dropping).")
                    jog_set_status(root, gh_num, "completed", failure_reason="preflight: already-landed")
                    tasks_processed += 1
                    continue
                elif pf_res.returncode != 0:
                    print(f"jog: GH-{gh_num} preflight failed (exit {pf_res.returncode}); parking item.")
                    jog_set_status(root, gh_num, "parked", failure_reason=f"preflight-refused (exit {pf_res.returncode})")
                    continue

            # Execute single-phase drive
            drive_rc = run_single_phase_drive(
                root,
                gh_num,
                builder=args.builder,
                reviewer=args.reviewer,
                simulate=getattr(args, "simulate", False),
            )

            if drive_rc != 0:
                print(f"jog: drive execution failed for GH-{gh_num} (exit {drive_rc}).")
                jog_set_status(root, gh_num, "failed", failure_reason=f"drive failed (exit {drive_rc})")
                print("jog: stopping queue execution on task failure.")
                break

            # Handle landing boundary
            landed, status, reason = handle_landing_boundary(root, gh_num, auto_merge=args.auto_merge, reviewer=args.reviewer,
                                                             simulate=getattr(args, "simulate", False))
            jog_set_status(root, gh_num, status, failure_reason=reason)

            if landed:
                tasks_processed += 1
            else:
                print("jog: advancing halted at landing boundary.")
                break

    finally:
        _cleanup()


if __name__ == "__main__":
    jog_run_main()
