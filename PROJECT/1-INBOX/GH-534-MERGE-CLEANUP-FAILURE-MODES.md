---
title: "GH-534: merge-cleanup promises merge + conflict-resolution + teardown, implements one and a half"
status: Parked
created: 2026-09-09
updated: 2026-09-09
owner: unassigned
goal: make /merge-cleanup's scripts do what SKILL.md says, or make SKILL.md say what the scripts do — and give PRESERVE_* dispositions a proven, fail-closed way to become eligible
gh_issue: 534
source: https://github.com/HiQS-Labs/XYZ-forge/issues/534
doc_type: defect
depends_on:
  - https://github.com/HiQS-Labs/XYZ-forge/pull/526
related:
  - https://github.com/HiQS-Labs/XYZ-forge/issues/444
  - https://github.com/HiQS-Labs/XYZ-forge/issues/523
  - https://github.com/HiQS-Labs/XYZ-forge/issues/510
  - https://github.com/HiQS-Labs/XYZ-forge/issues/446
context_tags: [merge-cleanup, skill, teardown, squash-merge, safety-guard, doc-code-drift]
non_goals:
  - Re-deciding the repo's squash-merge landing strategy
  - The #523 primary-checkout-first fix (PR #526 owns it; this plan is based on it, not beside it)
  - The #444 "do not merge" label guard (separate; B1 must not weaken it)
  - Any automatic resolution of semantic code overlap, or of same-key ledger conflicts
  - Any "regenerable dirt" allowance (removed in rev 2 — see A.3)
effort: 4
complexity: 4
risk: 4
---

# GH-534 — merge-cleanup audits, declines, and leaves

## Status

| What was just completed | What's next |
|---|---|
| Rev 5 after the operator-authorized bounded Codex round 4 (`relay-system/2026-09-09/gh534-plan-qa-codex-r4-bounded.md`): **E.6 Closed**; R3-A and R3-B each left one narrow defect, both accepted — A.4 now requires *completion* (return code 0 or 1, not signal-killed) before stderr is trusted, requests `-F pcn`, and adds a signal-killed fixture; C's admission lock is a record-adjacent `fcntl.flock`, since the drivers lock by `os.mkdir` and `driver-lock-lib.sh` only resolves a path. Draft PR #538 open, blocked. All authorized review rounds spent | Operator: accept rev 5 on the producer's adjudication of two narrow corrections, or authorize one more bounded round on R3-A/R3-B only. **Implementation is blocked until PR #526 lands** through the other maintainer's sequence; nothing merges into `development` without explicit say-so |

Operator decisions recorded: **B1** (implement the ledger-conflict half) and **Phase C** (a
decision ladder for what B1 cannot resolve). Both retained; both narrowed below.

## Why

The skill advertises three jobs. Two invocations on 2026-09-09 — one by this session, one by a
second agent — produced the same output: a complete audit, every checkout `PRESERVE_*`, every
conflicting PR skipped, and the actual work handed back to the caller. The operator called the
result "mostly useless", and that is the correct reading. It is the third report against this
skill since it landed on 09-04 (#444 on 09-05, #523 on 09-09, this).

The reason is not one bug. The scripts were built as an *audit + safe-delete* tool (`10918e9e`)
and SKILL.md was later widened (`b9d156c0`) to promise conflict resolution that was never
implemented; `69552975` added a tick-claim guard that is never called. The safety model is
terminal — `PRESERVE_*` has no transition — and its "unpushed" test is defeated by the repo's own
squash-merge landing strategy. And the skill's own test file, `test/gh436-merge-cleanup.py`, is
registered nowhere in `validate.sh`, so none of this was ever gated.

## Verified findings (at `6e304820`, confirmed by Codex round 1 with line cites)

| # | Failure mode | Where | Verified how |
|---|---|---|---|
| A | `~/marathon-clones` outside `DEFAULT_SAFE_ROOTS`: never scanned by default; `PRESERVE_UNSAFE_ROOT` when scanned. The constant also carries `~/Documents/agent-workspaces`, which `WORKTREE-SAFETY.md:783` does not — the two are not an exact mirror | `scan_clones.py:18-22`, `:47-67`, `:209` | Bare scan: 8 hits, all `GH Repos`. `--root ~/marathon-clones`: clean `pr495-repair` → `PRESERVE_UNSAFE_ROOT` |
| B | Unpushed = `[ahead N]` or `branch -r --contains` empty. Squash+`--delete-branch` means local commits are never contained in a remote ref → permanent `PRESERVE_UNPUSHED`. **And** a branch whose upstream is `[gone]` enters *neither* arm (`:246-252`) and escapes the check entirely — so the enumeration is wrong in both directions | `scan_clones.py:236-254` | Primary `[ahead 4]`, all four upstream-equivalent by `git cherry`. gh490 dev `[ahead 6]`. `[gone]` escape read from source |
| C | Dirty = any porcelain line (first ten sampled, `:224`). Regenerable-looking files count as work — but nothing proves any of them *is* regenerable; filenames are not content evidence | `scan_clones.py:219`, `:224`, `:303-306` | Every `PRESERVE_DIRTY` today was ledger telemetry or a plan artifact; that is an observation, not proof |
| D | `inspect_tick_claims()` defined, never called; `tick_claims` initialised false (`:181`), only the driver-lock helper runs (`:268`), so `ACTIVE_TICK_CLAIM` (`:296`) is unreachable. The helper itself is wrong even if wired: it parses `STATE.md` for `- (none)` (`:144`) while the renderer emits `_(none)_` (`src/project.js:302`, `:311`), and `STATE.md` is a derived snapshot written by `project()` (`src/project.js:341-346`) — readable-but-stale proves nothing. It fails **open** on read errors (`:136-158`). SKILL.md `:51` additionally promises `lsof`, which exists nowhere | `scan_clones.py:136-158`, `:181`, `:268`, `:296`; `src/project.js:302`, `:311`, `:341`; `SKILL.md:51` | `grep -n inspect_tick_claims` → one hit, the definition; renderer read |
| E | PR list fetched once (`merge_cleanup.py:272`); merge trusts exit code (`:57`); reconcile ignores every failure (`:81`, `:86`, `:91`, `:100`) and returns `True` (`:102`), ignored at `:300`; final fetch/ff ignored (`:305`); `mergeable` is fetched by `toposort_prs.py:20` and never gated on | as cited | Read; `ff-only` silently failed on today's diverged primary |
| F | Conflict resolution exists only as SKILL.md `:68` prose; `merge_cleanup.py:296` merges and reconciles, nothing else | `SKILL.md:68`; `git log -- skills/merge-cleanup` | `b9d156c0` touched only docs |
| G | `test/gh436-merge-cleanup.py` (216 lines, `unittest`) is not registered in `validate.sh` — the only Python registration is `test_python_layer.py`. The skill's tests never run in the gate | `validate.sh`; `test/gh436-merge-cleanup.py` | grep for `gh436` in `validate.sh` → none |

Traced (recon): `DEFAULT_SAFE_ROOTS` mirrors `WORKTREE-SAFETY.md:778-803`, which owns containment
policy. Clone producers `skills/10days/SKILL.md:144` and `skills/marathon-triage/SKILL.md:109`
write under `~/marathon-clones`. The only other consumer of the constant is the test import at
`test/gh436-merge-cleanup.py:26`; `merge_cleanup.py:22` imports it from the scanner (one runtime
list, keep it that way). This is a bounded literal-consumer claim over `utils/`, `skills/`,
`relay-automation/`, `test/`, not an exhaustive one.

## Dependency: PR #526 lands first

PR #526 (`fix/merge-cleanup-primary-first`, head `1788db16`) rewrites the same three files
(+91 `merge_cleanup.py`, +185 `scan_clones.py`, +60 `SKILL.md`) and adds 370 lines to
`test/gh436-merge-cleanup.py`. It already delivers: Phase 0 primary-readiness inspection,
`--integration-branch`, `--allow-unready-primary`, refetch before the first merge, a **checked**
`ff-only`, propagated reconcile failure, and a PR-base-branch check. That is three of E's five
items plus the #523 fix. Its hunks overlap this plan's on `merge_cleanup.py @@ -241,22`, `@@ -286,9`,
the Phase 5 tail, and `SKILL.md @@ -39,8`, `@@ -58,16`, `@@ -108,7`.

**This plan is implemented on top of #526, after it lands.** Default is serial: repair and land
#526 (it is `CONFLICTING` against `development` today), then rebase this branch and re-read every
function this plan touches. Retain #526's non-default-integration-branch, failed-fetch and final-ff
tests; do not recreate its ff fix or hardcode `development` over its option. Stacking on #526's
pinned head is possible only with explicit operator authorization and coordinated ownership.
What remains for E after #526: the `mergeable` pre-check and the `MERGED` re-query.

## Fix

Everything below extends the existing scripts and the existing `unittest` file. No new module,
no second scanner, no second runtime root list, no bash test file.

### Phase A — make the scanner tell the truth, fail closed on anything it cannot prove

**A.1 Roots.** Update `WORKTREE-SAFETY.md`'s `SAFE_ROOTS` example to add `~/marathon-clones`, and
`DEFAULT_SAFE_ROOTS` in `scan_clones.py` to match it exactly — including resolving the
`~/Documents/agent-workspaces` discrepancy in one direction (recommend: keep it in both, since
removing an approved root can only shrink what the skill may touch). A test pins parity between
the doc's list and the constant. Tests also cover strict-root rejection, a prefix sibling
(`XYZ-forge-foo` vs `XYZ-forge`), and a symlink that escapes the root.

**A.2 Unpushed → unlanded, by provenance, not by patch similarity.** Replace the two-arm check
with an enumeration of **every** local ref — all `refs/heads/*`, detached `HEAD`, and any
local-only ref — after a verified `git fetch origin <integration-branch>` (a failed fetch
preserves). For each ref tip:

1. **Reachable from `origin/<integration-branch>`** → landed. Direct ancestry is the only
   unconditional proof.
2. **Squash exception, bound to provenance:** the tip SHA equals `headRefOid` of a PR whose
   `state == MERGED` and whose `mergeCommit.oid` is reachable from `origin/<integration-branch>`
   (from `gh pr list --state merged --json number,state,headRefOid,mergeCommit,baseRefName
   --limit 500`, base equal to the integration branch; the remote identity is bound by comparing
   the clone's `origin` URL to the queried repo, and a page limit reached without a match is
   treated as "no match" → preserve). Then the branch's **aggregate** diff from its merge-base to the tip
   is compared, whitespace preserved and modes/binary included, against the merge commit's diff
   from its first parent. Equal → landed. Not equal (changed conflict resolution, later edits) →
   **preserve** and name the PR so the caller can review content.
3. Anything else — no matching merged PR, `gh` failure, malformed output, an empty candidate set
   that was not separately verified empty — → **preserve**, naming the ref and the reason.

Commits beyond a matched PR head are checked separately by rule 1; a known merged PR never
exempts later local work. `git cherry` is not used as authorization: its normalisation drops
whitespace, so equality there is not equality of behaviour. It may be shown as *advisory*
classification in the audit table, never as the reason for `SAFE_REMOVE_*`.

**A.3 Dirt.** No regenerable allowance. Rev 1's five-pattern list is withdrawn: `harnesses.db`
receives invocation/evaluation data (`utils/py/harness_turn_logger.py:132`, `:159`) and its dump
is not proof rows exist elsewhere; `MARATHON-PLAN-*.md` may be authored; `.playwright-mcp/` may
hold unique evidence; `*.db.bak` may be the last pre-rebuild copy
(`utils/releases-merge-resolve.sh:149`). What changes: read the **complete** NUL-safe porcelain
(`git status --porcelain -z`), not the first ten lines, and name every file in the disposition so
the caller can act on it. Any future narrow allowance must name exact paths, their retained
authoritative inputs, and a demonstrated recovery — not in this plan.

**A.4 Active-session evidence — from the event log, not from `STATE.md`.** The current helper
reads `.tick/STATE.md` and recognises only `- (none)` / `- none` (`scan_clones.py:144`), but the
renderer emits `_(none)_` (`src/project.js:302`, `:311`), so merely wiring it would mark every
ordinary empty section as active. Worse, `STATE.md` is a **derived snapshot**: `project()`
(`src/project.js:341-346`) reads the event log, folds it, then writes the file — a readable but
stale or missing `STATE.md` proves nothing about current claims, and `project()` must never be
called from an audit because it writes.

Authoritative evidence is the fold of the event log itself: `readAllEvents(repoRoot)` +
`fold(events)` (`src/project.js:260`) — the same functions `project()` uses, minus the write.
`tick` exposes no read-only "all claims" verb today (`next` is per-agent, `info` is per-task),
so add one: **`tick claims [--json]`**, read-only, built on those two existing exports, printing
every task in `claimed` state with its agent and paths. Two details Codex flagged that folding
alone does not give: `readAllEvents()` returns `[]` when the events directory is missing
(`src/events.js:206`), so the verb must itself refuse (non-zero, `events-dir-missing`) when
`.tick/` exists but its events directory does not or cannot be read; and the audited root is
pinned by passing `TICK_REPO_ROOT` explicitly (`bin/tick:19`), never inherited from the caller's
environment or CWD. The verb is a kernel-surface addition and gets a short decision record under
the existing governance, not a Python-only footnote. `inspect_checkout()` shells out to it at
the coordination root resolved through the git common dir (a linked worktree's `.tick/` is the
parent's), and:

- any claimed task → `ACTIVE_TICK_CLAIM`, naming task and agent;
- `tick` missing, non-zero exit, malformed JSON, unreadable `.tick/`, or an unreadable/absent
  event log where `.tick/` exists → **preserve** (`PRESERVE_UNVERIFIED_SESSION`), naming why;
- a directory-shaped `.tick/locks/<x>` counts as a lock;
- the STATE-file parser is deleted, not repaired.

**Process evidence is binding, not optional — and the exit code is not the signal.** Probed on
this macOS (2026-09-09): `lsof +D <dir>` exits **1 in every case** — idle directory, held file
descriptor inside it, nonexistent path, and unreadable subdirectory. Exit-code gating would
therefore preserve every idle checkout forever (rev 3's defect) or, if exit 1 were accepted,
treat a permission failure as "verified idle". Neither. The contract has **three outcomes**,
decided by stderr and content:

1. Run `lsof -F pcn +D <checkout>` with a timeout, from a CWD **outside** the checkout,
   capturing stdout and stderr separately (`-F pcn` requests the `p`/`c`/`n` fields; `-F pn`
   alone would not carry the command). Absent binary, timeout, or a Python-level failure →
   **incomplete**.
2. **Completion is a precondition, and the exit code is part of it.** Only a normally-exited
   process with return code **0 or 1** — the two statuses the probe showed ordinary runs
   produce — counts as having completed. A negative return code (killed by a signal, which
   `subprocess` reports without raising), or any other status, → **incomplete**, regardless of
   stdout or stderr. The exit code cannot distinguish idle from held; it can and must
   distinguish "ran" from "did not finish".
3. **Any line on stderr** (`lsof: WARNING: can't opendir(...)`, `can't stat(...)`, etc.) →
   **incomplete**: the enumeration did not cover the tree. Observed: the unreadable-subdir case
   emits exactly this warning with exit 1, indistinguishable from idle by exit code alone.
4. Completed (per 2) **and** empty stderr → the enumeration is **complete**. Parse the
   `p<pid>` / `c<command>` / `n<path>` records; keep an `n` record only if its path is
   component-wise within the checkout (the same `_within()` used for roots); drop records whose
   `p` is the scanner's own PID or an ancestor of it (the probing shell was itself listed in the
   idle run). Remaining matches → `ACTIVE_PROCESS`, naming every PID and its command. No matches
   → **verified idle**.

Incomplete → `PRESERVE_UNVERIFIED_SESSION`, naming the warning. The known live case is the
primary's Antigravity language-server handle leak. Removing the SKILL.md `:51` promise instead is
rejected: it would not make deleting an active clone safe.

**A.5 Fresh inspection before removal — of every candidate, not just the survivors.** Phase 6
currently filters the *original* inventory to `SAFE_REMOVE_*` (`merge_cleanup.py:312-318`) and
deletes from that. Refreshing only those survivors would pass a "SAFE → dirty" test while a
`PRESERVE_UNPUSHED` clone whose PR just landed in Phase 5 is never reconsidered. So Phase 6
re-runs `inspect_checkout()`, after a fresh fetch, on **every** non-exempt checkout from the
scan — `PRESERVE_DIRTY`, `PRESERVE_UNPUSHED`, `PRESERVE_STASH`, `PRESERVE_UNVERIFIED_SESSION`
and the `SAFE_REMOVE_*` set alike — keeping only the `PRIMARY_CHECKOUT`, `PRESERVED_USER_EXCLUDE`
and `PRESERVE_WIKI` exemptions. The fresh disposition is the only one `teardown_checkout()` may
act on; the scan-time one is display. That is the `PRESERVE_* → eligible` transition after a
successful landing, and the guard against anything that changed since the scan.

**Every required safety query fails closed.** Today a failed `git stash list` or
`git worktree list` is treated as empty (`scan_clones.py:230-234`, `:256-265`), so a fresh
inspection would simply repeat a false proof. In `inspect_checkout()`, a non-zero exit or
malformed output from any of: status, stash enumeration, worktree enumeration, local-ref
enumeration, the fetch, `tick claims`, or `lsof` → preserve, naming the query. No query result
is ever defaulted to "none".

**A.6 Register the tests.** `test/gh436-merge-cleanup.py` joins the gate under the existing
`python:` mechanism (or an equivalent explicit entry), so every check in this plan actually runs.

### E.6 — the ledger CLI runs *before* every merge, as a gate (operator scope addition, 2026-09-09)

Today `gen` + `check` run only after `gh pr merge` (`merge_cleanup.py:83-91`), warnings
swallowed — a PR that breaks the ledger is discovered after it has landed (#519, #495). A PR head
can also be clean on its own and break only in combination with what landed before it. So, for
**every** PR in the sequence, not just `CONFLICTING` ones:

1. In a disposable full clone of the PR head (the same clone B1 uses), `git merge
   origin/<integration-branch>` to simulate the landing. Non-zero merge → this PR is either a B1
   candidate (ledger-only set) or a Phase C handoff; it is never `gh pr merge`d.
2. Clean merge → run `python3 utils/py/releases_app.py check` and
   `roadmap reconcile-state --dry-run` in that clone. Any non-zero exit, or any `FAIL:` line →
   **red**: park with the diagnostic naming the rule; never merge. A failed *command* (clone,
   merge, check) is red, not "no finding". **Not red:** `check`'s `warn:` lines,
   `reconcile-state`'s per-row `warn: rule=roadmap-issue-identity` skips (that is #527's
   deliberate per-row behaviour — do not turn it back into a command-wide blocker here), and
   dry-run `would move` lines. All of these are retained in the gate output as diagnostics.
   The ordinary three-way merge is the right simulation: it keeps `MERGE_HEAD`, which the
   resolver's generation floor reads (`utils/releases-merge-resolve.sh:98-120`); a
   `git merge --squash` would drop it and silently bypass that check. The gate always runs
   against the current integration head fetched for *this* landing, never a cached snapshot.
3. Green → `gh pr merge`, then the post-merge `check` (already in E) — which is now gating, not a
   warning.

Marginal cost is one clone-merge-check per PR, and the clone is already required by B1 and by
A.2's provenance step.

### Phase B1 — ledger-only conflict resolution, disjoint changes only

Routing hint, not proof: a `CONFLICTING` PR whose unmerged set — from `git merge` in a fresh
disposable clone of the PR head, read via `git diff --name-only --diff-filter=U` and
`git ls-files -u`, and **required to be non-empty with a zero-exit extraction** (an extraction
error is not an empty conflict set; it is a handoff) — is a subset of `{releases.db, releases.sql,
ROADMAP-DASHBOARD.md, LEADERBOARD.md, RELEASES-PREVIEW.html, LEADERBOARD.html}` is a B1 candidate. `harnesses.db` /
`harnesses.sql` are **excluded** until they have their own resolver — a conflict there is a
handoff. Any code file in the set → Phase C.

What the resolver actually does (`utils/releases-merge-resolve.sh`): it **refuses** an unresolved
`releases.sql`, including a stale index entry with markers stripped (`:70-81`); rebuilds the DB
from a *resolved* dump; regenerates views including deleting stale ones (`:160-181`); enforces
generation ≥ max(HEAD, MERGE_HEAD) (`:98-120`); does **not** commit (`:23`). It does not decide
which rows survive. So B1's job is the part before the resolver:

1. Three-way classify the ledger against the merge base, per table, per key: base-only,
   ours-only, theirs-only, same-key-changed-on-both. Include updates and deletes, identifiers, and
   FK references, not just added rows.
2. **Auto-resolve only when the change sets are mechanically disjoint** (no same-key change on
   both sides, no FK reference to a row the other side deleted). Establish the resolved dump
   through the supported writer path (the CLI verbs), stage it, then invoke the resolver with an
   explicit validated clone root. Same-key conflicts, schema changes, or anything the writer
   cannot express → handoff with the key list. No SQL union, ever.
3. Also review the ledger files git auto-merged *without* markers — a clean textual merge of two
   `INSERT`s can still be a semantic conflict.
4. On the generation-rewind refusal: stop, emit the diagnostic, keep the disposable clone. Do not
   bypass, do not rerun unchanged input.
5. Regenerate views; run `releases check`; require **zero** remaining unmerged entries
   (`git ls-files -u` empty) before the explicit merge commit; validate that head in a **second**
   disposable full clone (identity verified before and after); then push only if the remote PR
   head is still the SHA that was resolved. Pin source/head/base SHAs in the log.
6. Never weaken the #444 hold-label guard: a labelled PR is not a B1 candidate.

### Phase C — the decision ladder for what B1 cannot resolve

The script owns evidence and the cap; the caller owns analysis. A standalone script run never
claims to have run `/recon` or `/ponytail`.

**One durable attempt record, at one pinned coordinator.** The script cannot observe repairs
made outside it, so the accounting lives in a file both sides update — and, since every full
clone has its own `.tick/`, "same origin + PR number" would only give the same *suffix* in
different physical files. Rev 4 pins the physical root:

- The **coordinator** is the explicit primary checkout — the `--primary` path the run was
  started with (`merge_cleanup.py:247`), never a disposable clone's CWD. The absolute record path
  `<primary>/.tick/merge-cleanup/<owner>-<repo>/pr-<N>.json` is resolved **once** at run start,
  written into every handoff record and every B1 log line, and passed to each disposable worker
  as `MERGE_CLEANUP_RECORD=<abs path>`. A repair invocation that lacks that variable, or whose
  path is unreadable or malformed, **stops**; it never infers a replacement root from its own
  CWD and never creates a new history elsewhere.
- **Admission is serialized by a record-adjacent advisory lock, not the driver lock.** Rev 4
  named "the existing `flock` in `driver-lock-lib.sh`"; that library only *resolves a path*, and
  the drivers themselves lock by `os.mkdir(lock_dir)` plus a PID file
  (`utils/py/relay_drive.py:495-499`, `utils/py/marathon_drive.py:1203-1206`) for the lifetime of
  a run — a worker started *under* a running driver could never take that lock without
  deadlocking, and an `flock` would not serialize with a mkdir protocol anyway. So: every record
  writer — the orchestrator before a B1 run, a caller before a repair rung, a worker updating an
  outcome — opens `<record>.lock` beside the record at the coordinator and holds
  `fcntl.flock(fd, LOCK_EX)` (stdlib, the same pattern AgentChorus uses) for the whole
  read-count → reserve → write sequence, releasing on close. It is independent of the driver's
  mkdir lock, so a worker under an active driver enters it freely; it is blocking with a short
  timeout, and a timeout is a stop, not a skip. Two invocations cannot both take the last slot.
- **Only repair attempts count.** Diagnosis (`/debug-mantra`) and read-only recon do not consume
  budget; they update the *current* attempt's `diagnosis`/`recon` sub-fields or, before any
  repair exists, a `pre_repair` block. An attempt entry is created at the moment a repair is
  about to start — a B1 run, or a caller rung that will change files.
- **Budget is per PR, bound to the head that was attempted.** Each attempt entry carries the
  `head_sha` it worked on. Two repair attempts per PR are the ceiling, **whatever the head**: a
  head produced by a failed repair does not mint a fresh budget. Fields: `pr`, `repo`,
  `base_sha`, `merge_base`, `attempts[]` (each: `by` = `script`|`caller`, `head_sha`, `rung`,
  `started`, `outcome`, `clone_path`, optional `diagnosis`/`recon`), `conflict_files[]` with
  conflict type and hunk counts, `last_side_touched{}`.

- **Script caps only its own B1 attempts** (one per invocation, two lifetime per PR) and reads
  the record under the lock before each: at two repair attempts, it refuses and parks the PR
  with the record path. It never assumes anything about caller rungs beyond what the record says.
- **Caller enforces the overall budget** from the same record, under the same lock, before any
  rung that will change files. The third repair attempt is refused. Bouncing between rungs,
  restarting, or re-cloning does not reset it, because the record lives at the coordinator.
- **Script blocks dependents:** a PR that depends on a failed/parked predecessor is not attempted.
  `toposort_prs.py:128` removes edges while ordering and `:141` appends cyclic nodes, so ordering
  alone cannot express this; Phase 5 keeps a runtime map of predecessor outcomes and consults it
  before each merge.
- **Caller (SKILL.md names each rung, in order, with these defaults):** `/debug-mantra` to
  establish the conflict as ground truth from the record; `/recon`, **read-only**, over the
  conflict files in the record only — default budget **8 files, 15 minutes wall-clock, consumer
  tracing one level out from each conflicting symbol and counted inside the same budget**,
  stopping and recording `budget_exceeded` when hit; `/ponytail` for the smallest reviewed
  resolution — "independent hunks" is not proof of independent semantics, so a code resolution
  lands only with caller review and tests; `/start-task`-style handoff for semantic overlap;
  `/unstuck` when the record already shows two attempts.

### Risks and rollback

- Every change in Phase A that widens eligibility (A.2 rule 2, A.5) is at least **Costly**: a
  wrong eligibility deletes a clone, and reverting code does not restore it. The retained recovery
  is the existing move-to-Trash in `teardown_checkout()` (`merge_cleanup.py:149-153`), which must
  stay the only removal path, plus the fresh inspection in A.5. Where Trash is unavailable the
  skill must refuse, not `rmtree`.
- B1 can only lose data by resolving something it should have handed off; the disjoint-only rule
  and the writer-path requirement are the guard. Its rollback is "the PR stays conflicting".
- Code rollback for everything else is `git revert`. The skill's only persistent state is the
  per-PR attempt record under `.tick/merge-cleanup/` (Phase C); it is gitignored with the rest
  of `.tick/`, survives reverts by design, and is deleted by hand when a PR is closed.

## Acceptance check

Each is a test in `test/gh436-merge-cleanup.py` unless stated; each red control is witnessed
during implementation with its nonempty red and green output **and** `provenance.jsonl` committed
together under `TESTS-RESULTS/<date>+GH-534/`.

**A.1** — a clean clone under `~/marathon-clones` is `SAFE_REMOVE_CLONE`; parity test between
`WORKTREE-SAFETY.md`'s list and `DEFAULT_SAFE_ROOTS`; strict-root, prefix-sibling and
symlink-escape rejections.

**A.2** — fixtures with a local origin: (i) squash-merged twin whose tip equals a merged PR head
and whose aggregate diff equals the merge commit's → eligible; **red control: fails when rule 2 is
removed**; (ii) genuinely unlanded branch → `PRESERVE_UNPUSHED` naming the ref **and** the
commit; **red control: fails when the naming is removed** (the disposition alone would stay green
on reversion — that was rev 1's mistake); (iii) multi-commit squash; (iv) changed conflict
resolution → preserve; (v) whitespace-only mismatch → preserve; (vi) `[gone]` upstream is
enumerated, not skipped; (vii) detached HEAD and local-only ref enumerated; (viii) `gh` failure →
preserve; (ix) extra commit beyond the matched PR head → preserve naming it.

**A.3** — a 12-file dirty fixture reports all 12, not 10; disposition names every file.

**A.4** — fixtures built with the real `tick` (`task.created` + `claim`), never hand-written
`STATE.md`: (i) canonical empty coordination root → eligible; (ii) an active claim → 
`ACTIVE_TICK_CLAIM` naming task and agent; (iii) an active claim in the event log with `STATE.md`
**stale or deleted** → still `ACTIVE_TICK_CLAIM` (proves the fold, not the snapshot, is read);
(iv) `.tick/` present but event log unreadable → `PRESERVE_UNVERIFIED_SESSION`; (v) directory-
shaped lock → claim; (vi) linked-worktree tick root resolves to the common dir; (vii) `tick` binary
absent / non-zero → preserve; (viii) **real idle directory**, no held handle, scanner CWD outside
it → verified idle and eligible (this is the case exit-code gating breaks); (ix) a held file
descriptor inside the checkout → `ACTIVE_PROCESS` naming that PID; (x) injected traversal
failure (an unreadable subdirectory, which emits `lsof: WARNING: can't opendir`) →
`PRESERVE_UNVERIFIED_SESSION` naming the warning; (xi) `lsof` absent → preserve; (xii) `.tick/`
present but events directory missing → preserve (`events-dir-missing`), proving the verb does not
trust `readAllEvents()`'s empty default; (xiii) `lsof` **terminated by a signal** (a stub that
kills itself with `SIGTERM` after writing nothing to stderr) → `PRESERVE_UNVERIFIED_SESSION`,
proving completion is checked before stderr is trusted. Fixture (x) must be **isolated**: assert
the injected `WARNING:` line was actually produced, and that no live descriptor of the fixture's
own matches, so the preserve comes from the stderr guard and nothing else. **Red controls:** AST
assertion that `inspect_checkout` calls `inspect_tick_claims` (a string or comment does not
satisfy it); (iii) fails when the implementation reads `STATE.md`; (viii) fails when blanket
non-zero rejection is reinstated; (x) fails when the stderr guard is removed; (xii) fails when
the explicit events-dir check is removed; (xiii) fails when the completion (return-code) guard
is removed; (ix) fails when the `lsof` path is removed.
`tick claims` gets a unit test proving it writes **neither** `.tick/STATE.md` nor
`.tick/rejected.jsonl` (`src/project.js:345`, `:352`).

**A.5** — a two-checkout orchestration fixture: after a mocked successful Phase 5 landing, a
checkout that was `PRESERVE_UNPUSHED` at scan time becomes eligible at teardown (**red control:
fails when Phase 6 rescans only the original `SAFE_REMOVE_*` survivors**); a checkout made dirty
between scan and teardown is not removed; a **new claim** and a **new local ref** between scan and
teardown each block removal. Fault injection: each of `stash list`, `worktree list`,
`for-each-ref`, `fetch`, `tick claims`, and `lsof` made to fail in turn → no teardown, disposition
names the failed query (**red control: fails when the fail-closed guard is removed**).

**E** — a two-PR orchestration fixture with mocked `gh`/git side effects: PR 2 is re-fetched after
PR 1 lands; `UNKNOWN`/API failure stops; `CONFLICTING` routes to B1 (or a dry-run explanation),
never to `gh pr merge`; a zero-exit merge whose re-query is not `MERGED` fails; failed
fetch/ff/gen/check/reconcile stops all downstream mutation; assert the exit code and that later
merges, teardown, and symlink pruning did not run; `--reconcile-pr` failure propagates.

**E.6** — a two-PR fixture where PR 2 passes `releases check` on its own head but fails it once
PR 1 has landed → PR 2 is not merged, exit non-zero, diagnostic names the failing rule; a
`check` command that itself errors (non-zero, no `FAIL:` line) is treated as red; **red control:
fails when the pre-merge gate is removed** (PR 2 would merge).

**B1** — fixtures for: disjoint additions on both sides preserved; same-key update vs update →
handoff; update vs delete → handoff; FK reference to a deleted row → handoff; clean textual
auto-merge that is a semantic conflict → handoff; generation rewind → stop with diagnostic;
`harnesses.db` conflict → handoff; view deletion preserved; generator failure → no push; final-head
gate failure → no push; remote head moved → no push; extraction error → handoff, never "no
conflict"; the default (no `--execute`) run → zero mutation. Plus **one real, unmocked run**:
a fixture repo with a genuinely disjoint ledger conflict resolved end-to-end through the writer
path and `utils/releases-merge-resolve.sh`, with `releases check` clean afterwards.

**C** — attempt-record schema and pinned location; **two distinct full clones** of one fixture
origin, one coordinator: a caller repair attempt recorded from clone 1, then a script B1 attempt
from clone 2, both via `MERGE_CLEANUP_RECORD` → the **third** repair attempt from either clone is
refused (**red control: fails when the record root is derived from CWD instead of the pinned
coordinator**); a diagnosis/recon-only step does not consume budget; a repair that produces a
new head does not reset the budget; two invocations racing for the last slot → exactly one wins
(under the record-adjacent `fcntl.flock`); a worker started **while the parent driver's mkdir
lock is held** still takes the record lock and completes its reservation (proves the two locks
are independent — a nominal "same lock" implementation fails this); a lock-acquire timeout
stops the attempt rather than skipping the count; a worker started without
`MERGE_CLEANUP_RECORD`, or with an unreadable record, stops; a dependent of a parked PR is not
attempted; the next *independent* PR still proceeds.

**Parity guard** — SKILL.md gains a capability table (Phase 2 session evidence, Phase 3
preservation, Phase 5 ledger resolution / handoff / reconciliation, Phase 6 fresh inspection),
each row with owner `script` or `caller` and, for script rows, a test name. The guard carries a
**fixed required set** of capability names (so deleting one row cannot pass because others
remain), asserts every required row is present with its owner, asserts every named test exists
and runs, asserts described CLI options exist in argparse, pins code-conflict recon's owner as
`caller`, and asserts the D call at AST level. Negative controls in fixture copies, each
failing with the capability named: delete the D call; disconnect B1 dispatch but leave its helper;
remove a table row; replace a call with a comment. Registered with the gate. Modelled on
`test/gh1-adoption-guard.sh:42-64` and `:90-141`.

**Gate** — `validate.sh` green in a disposable full clone (identity verified before/after), with
`test/gh436-merge-cleanup.py` now inside it.

## Rating rationale — 2026-09-09 (rev 2; unchanged through rev 4 — R3-A/B are contracts on
work already scoped, and E.6 reuses B1's clone-and-merge step, adding one `check` per PR)

`rated 75/70/50/30` → calc 225. Rev 1 was 75/70/50/40; effort re-estimated after the B1 and C
contracts were specified — `--force` on re-score, reason recorded here.

- **sev 70** — operator-blocking workflow (two of three advertised jobs do not run; teardown
  impossible for the main clone population by construction) plus a latent unsafe guard (D). No
  observed data loss, so not the 80+ band; not lowered for that either.
- **pri 75** — the operator is blocked on it today, and it is the third report against this
  skill since launch: #444 (09-05), #523 (09-09), #534 (09-09). Stated honestly: *repeated
  reports since launch on 09-04*, not a measured rising rate — the prior 14-day window had no
  comparable exposure, and live re-verification of #444/#523 from the review worktree failed.
- **appeal 50** — neutral; no operator preference given.
- **effort 30** — Phase A with fail-closed provenance (A.2) and fresh inspection, B1's three-way
  ledger classification through the writer path, C's handoff/ceiling machinery, the parity guard,
  and the full acceptance matrix above: a multi-day arc on top of #526, not a quick win.
- Uncertainty: #526 is `CONFLICTING` and its final shape may move; exact hunk overlap is a
  snapshot at head `1788db16`. No operator `ovr`.
