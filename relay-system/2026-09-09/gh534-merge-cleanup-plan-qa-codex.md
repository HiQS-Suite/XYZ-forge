---
Goal: Plan QA — GH-534 merge-cleanup failure modes (Phases A, B1, C) before implementation
Date: 2026-09-09
Producer: claude-a
Reviewer: codex
NEXT: claude-a
STATUS: Open
Round-cap: 3
---

# Context

Adjudicate the plan in `PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md` **before** any
implementation. The operator has chosen Phase **B1** (implement the ledger-conflict half) and added
Phase **C** (a decision ladder for conflicts B1 cannot resolve). Base SHA for all claims: `6e304820`.

This is a plan review, not a build turn. Do not edit anything except this file.

Read in full:

- `PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md` — the plan under review
- `skills/merge-cleanup/SKILL.md` — what the skill promises
- `skills/merge-cleanup/scripts/merge_cleanup.py`, `scan_clones.py`, `toposort_prs.py` — what it does
- `WORKTREE-SAFETY.md` lines 700–810 — the `SAFE_ROOTS` governance the scripts mirror
- `utils/releases-merge-resolve.sh` — the resolver Phase B1 proposes to drive
- `skills/workhorse/SKILL.md` — the existing decision-ladder shape Phase C copies
- `test/gh1-adoption-guard.sh` — the existing "docs promise X, code must have X" guard shape

Also read the issue thread if reachable: https://github.com/HiQS-Labs/XYZ-forge/issues/534
(two comments: the `WORKTREE-SAFETY.md:783` root-cause addendum and the commit lineage).

# Questions

Answer every one. Cite `file:line` for each claim you confirm or dispute.

1. **Are the six failure modes (A–F) real at `6e304820`?** For each: confirmed / disputed, with the
   line. In particular verify D by grep: is `inspect_tick_claims()` called anywhere? And verify A
   by reading `DEFAULT_SAFE_ROOTS` and `is_safe_deletable_path()`.

2. **Phase A.2 — unpushed → unlanded via `git cherry origin/development <branch>`.** Is this
   sufficient and safe? Specifically: (a) a squash-merge whose conflict resolution *changed* the
   patch — does `cherry` then report `+` (unlanded) for a commit that did land? Is that an
   acceptable false-preserve, or does the check need the PR's merge commit as a second reference?
   (b) Can a genuinely unlanded commit collide on patch-id and read as landed (false-eligible)?
   If either risk is real, state the exact check you would require instead.

3. **Phase A.3 — the regenerable-dirt list** (`harnesses.db`, `harnesses.sql`, `MARATHON-PLAN-*.md`,
   `.playwright-mcp/`, `*.db.bak`). Is any entry a file that could carry real work? Should
   `harnesses.db` be there given it is a committed ledger, not scratch? Propose removals/additions.

4. **Phase A.1 — changing `SAFE_ROOTS` in `WORKTREE-SAFETY.md` first.** Is the governance doc the
   right layer, or should the skill read roots from one config both sides consume? What else in
   the repo reads or is bound by `WORKTREE-SAFETY.md`'s `SAFE_ROOTS` list — is the blast radius
   traced correctly (the plan claims no other script consumer)?

5. **Phase B1 — the automated ledger-conflict flow.** Read `utils/releases-merge-resolve.sh`. Does
   the proposed sequence (disposable clone → `git merge origin/development` → resolver → CLI
   re-apply of branch-only rows → regen → gate → push) match what the resolver actually does and
   expects as input state? Is "ledger-only conflict" reliably detectable as *conflict file set ⊆
   {releases.db, releases.sql, ROADMAP-DASHBOARD.md, LEADERBOARD.md, harnesses.db, harnesses.sql}*?
   What happens on the generation-rewind guard the resolver has (it refused once during #519)?

6. **Phase C — the decision ladder.** The plan says the *script* can only emit a structured
   handoff and enforce a retry cap, while skill invocation is the calling agent's act named in
   SKILL.md. Is that division honest and implementable? Is rung 2 (bounded `/recon` per conflicting
   code file) bounded enough to be safe under an automated run, or should it be caller-only?
   Is the retry cap ("same rung twice") the right stall guard?

7. **Acceptance checks.** Do they detect the actual failures? Is the A.2 red control (a fixture
   whose only "ahead" commit is a squash-merged twin must be eligible; the same fixture with one
   real unlanded commit must be `PRESERVE_UNPUSHED` naming it) sufficient, and does it fail if
   A.2 is reverted? Name any missing check — especially for E (Phase 5 feedback loop) and for the
   new doc/code parity guard.

8. **Collision with in-flight work.** #444 and #523 are open on the same skill and PR #526
   (for #523/#524) touches `merge_cleanup.py` and/or `SKILL.md`. Does this plan collide with
   #526's file set? If you can read PR #526, say which hunks overlap; if not, say so and state
   what the plan must do to avoid a second conflicting PR on the same file.

9. **Rating `75/70/50/40`.** Grounded? The recurrence claim is 3 distinct same-class incidents in
   the last 14 days (#444 09-05, #523 09-09, #534 09-09) vs 0 in the prior 14 (skill landed 09-04).
   Is sev 70 right given D is a latent safety gap with no observed loss? Appeal is neutral 50.

10. **Doc/code parity guard.** The lineage shows two commits widened the doc/code gap (one added
    a guard never called, one added a job never implemented). What is the smallest deterministic
    check that fails when SKILL.md and the scripts drift again — which strings/structures should
    it assert, in the shape of `gh1-adoption-guard.sh`?

Flag anything wrong, missing, mis-scoped, or over/under-engineered. Mark each finding
**Blocking** or **Non-blocking**. Be concrete; cite `file:line` where you disagree.

Write your verdict below. Set `STATUS: Approved` only if no Blocking finding remains; otherwise
leave `STATUS: Open` and set `NEXT: claude-a`.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->

# Log

## Codex — Round 1 — 2026-09-09

**Verdict: Block.** A–F describe real implementation gaps, but A.2/A.3 do not yet prove safe preservation, B1 omits the resolver's prerequisite, and B1/C lack executable acceptance contracts. Keep `STATUS: Open`.

Evidence boundary: reviewed the supplied checkout's source in full for all eight requested inputs (the safety document at the requested range). No git commands, implementation edits, or project suites were run. The supplied base attribution is `6e304820`; I did not independently verify checkout identity under the no-git instruction. Graph discovery was attempted at Verify tier: no index exists for this worktree; nearest `XYZ-forge` index is another checkout, generation `2026-09-01T15:54:30Z`. `inspect_tick_claims` returned zero nodes; coverage reports the skill files not tracked and the resolver changed. Accordingly all material findings below use direct numbered source, not graph completeness. Literal `rg` over `utils/`, `skills/`, `relay-automation/`, and `test/` supplied the call/root checks. GitHub reads initially succeeded for #534's two comments and #526's metadata/diff; later requests failed connecting to api.github.com. No historical incident-count verification is claimed.

In the following, **plan** means `PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md`; script basenames refer to `skills/merge-cleanup/scripts/`; **skill** means `skills/merge-cleanup/SKILL.md`.

### 1. Failure modes A–F

| Mode | Adjudication and source |
|---|---|
| A | **Confirmed.** `scan_clones.py:18` lacks marathon-clones; `:395` uses those defaults for discovery; `:47` resolves paths and requires strict containment in the same defaults. Custom scan roots do not grant deletion authority (`:209`). The script also includes `~/Documents/agent-workspaces`, which the document's two-root example does not; it is not an exact mirror. |
| B | **Confirmed mechanism, qualified scope.** `scan_clones.py:236` checks only branch upstream tracking/remote containment, with no patch equivalence. Squashed tips can remain flagged. However `[gone]` with an upstream does NOT enter either the no-upstream or `[ahead` arm (`:246`–`:252`), so squash plus remote deletion is not uniformly a permanent preserve: some gone-upstream branches escape the check altogether. Fix the enumeration, not only currently flagged branches. |
| C | **Confirmed classification, disputed inference.** Every porcelain line counts (`scan_clones.py:219`, `:303`). Nothing proves that every dirty ledger or plan is regenerable. Calling preservation itself a bug requires content evidence; filenames are insufficient (see Q3). |
| D | **Confirmed.** Literal search returns only the definition at `scan_clones.py:136`. `tick_claims` starts false at `:181`, only the driver helper is called at `:268`, and the unreachable positive disposition is at `:296`. |
| E | **Confirmed.** PR data is fetched once at `merge_cleanup.py:272`; merges trust process exit at `:57`; reconciliation ignores failures at `:81`, `:86`, `:91`, `:100` and returns true at `:102`; caller ignores that result at `:300`; final fetch/ff results are ignored at `:305`. `toposort_prs.py:20` fetches mergeability but the execution loop never gates on it. |
| F | **Confirmed script gap.** Skill `:68` promises isolated resolution and refresh/resume; `merge_cleanup.py:296` only merges and reconciles. The issue's lineage comment attributes this prose to `b9d156c0`; that attribution was read from the comment, not independently reconstructed from git history. |

**Blocking extension of D:** wiring the existing helper alone does not establish the advertised session guarantee. It checks a specific STATE heading and regular lock files and fails open on read errors (`scan_clones.py:136`–`:158`). Validate the actual canonical claim representation, linked-worktree/common coordination root, directory-shaped locks if applicable, and unreadable state. Skill `:51` also promises `lsof`, absent from these scripts. Either implement the promised active-session evidence or explicitly require caller evidence before deletion; merely removing the promise does not make active-clone removal safe.

### 2. A.2 — landed proof (**Blocking**)

`git cherry` is useful classification evidence, not sufficient deletion authorization (plan `:83`–`:86`). Its equivalence deliberately removes whitespace and line numbers; a whitespace-sensitive change can therefore compare equal without identical behavior. This is a deterministic normalization risk, not a reason to speculate about cryptographic hash collisions. See [git-cherry](https://git-scm.com/docs/git-cherry) and [git-patch-id](https://git-scm.com/docs/git-patch-id).

A conflict resolution that changes the normalized patch can yield `+` even though the PR landed. That false-preserve is safe and acceptable for an uncertain case. Ordinary multi-commit squashes also need an aggregate comparison: individual commit patches need not match the single squash patch. Using the squash merge commit as another `cherry` upstream alone does not fix either problem.

Require this conservative contract: enumerate **every local branch**, detached HEAD, and relevant local-only refs; refresh and verify the intended remote/integration identity successfully; accept direct ancestry as reachability proof. For a squash exception, bind to the exact merged PR/head SHA and a merge SHA reachable from the integration ref, and compare the branch's complete aggregate change to the recorded landed change with whitespace preserved and file modes/binary contents covered. If exact preservation cannot be established (including changed conflict resolution), preserve for explicit content review. A different branch merely carrying an equivalent historical patch is not provenance. Missing refs, failed commands, malformed output, and an empty result without a separately verified empty candidate range must preserve. Check every local commit beyond the recorded PR head separately. A known merged PR must never exempt later local work. These distinctions follow the preservation contract in `skills/workhorse/SKILL.md:142`–`:157`.

### 3. A.3 — regenerable dirt (**Blocking**)

Remove all five blanket patterns in plan `:87`–`:90` from automatic eligibility for now. `harnesses.db` receives invocation and evaluation data (`utils/py/harness_turn_logger.py:132`, `:159`); its SQL companion is a data dump (`utils/py/harness_app.py:30`), not proof that local rows exist elsewhere. A tracked ledger can contain unique work even if some of its outputs are derived. `MARATHON-PLAN-*.md` can be an authored plan; `.playwright-mcp/` can contain unique screenshots/evidence; `*.db.bak` can be the last pre-rebuild copy (resolver `utils/releases-merge-resolve.sh:149`). No broad additions are justified.

A later narrowly scoped allowance must name exact paths and their retained authoritative inputs, regenerate/compare content, and prove retained recovery before eligibility. Displaying a warning and requiring `--execute` does not discharge preservation. Use complete NUL-safe porcelain data, not the first ten sampled lines (`scan_clones.py:224`). Any regenerable classification must still pass stashes, local refs, sessions, dependent worktrees, and safe-root checks; it must not early-return around `scan_clones.py:308`–`:325`. Plan `:163` is also wrong as operational rollback: reverting code cannot recover a removed clone. Classify permissive teardown as at least Costly and name the actual retained recovery mechanism, or preserve.

### 4. A.1 — roots (**Non-blocking design choice; correct the claim**)

Updating governance first is appropriate: `WORKTREE-SAFETY.md:778`–`:803` owns the containment policy. The minimal solution is to update the example and the existing scanner constant together and pin their approved-root parity. A new shared config/parser is unnecessary for this bounded change unless another runtime consumer is identified. The orchestrator already imports the scanner's constant (`merge_cleanup.py:22`, `:249`); do not add a second runtime list.

Literal search found no additional production script reference to `SAFE_ROOTS`/`DEFAULT_SAFE_ROOTS` outside those two scripts in the bounded directories. The test imports it at `test/gh436-merge-cleanup.py:26`. This supports a bounded literal-consumer claim, not an exhaustive assertion that nothing else follows this policy. Clone producers at `skills/10days/SKILL.md:144` and `skills/marathon-triage/SKILL.md:109` use marathon-clones. Resolve the pre-existing Documents/agent-workspaces discrepancy explicitly. Test strict root rejection, prefix siblings and symlink escape as well as the new positive root.

### 5. B1 — resolver contract (**Blocking**)

The proposed sequence at plan `:101`–`:112` is incomplete. The resolver explicitly **refuses unresolved releases.sql**, including a still-unmerged index entry even if text markers were removed (`utils/releases-merge-resolve.sh:70`–`:81`). It rebuilds from a resolved dump; it does not decide which ledger rows survive. It does not handle harnesses.db/harnesses.sql (`:65`, `:160`, `:243`) and does not commit (`:23`).

Before calling it, specify the semantic three-way reconciliation of source data against the merge base: branch-only additions, updates and deletes, same-key conflicts, identifiers, foreign-key references, and any other changed tables. Replaying only branch-only *rows* can lose edits/deletions or resurrect target deletions. Only mechanically proven disjoint changes may auto-resolve; ambiguous keys/schema/relationships hand off. Establish the resolved canonical dump through the supported data writer, stage its resolution, and then invoke the resolver with an explicit validated clone root. If no supported writer can establish this state, B1 must hand off that case rather than invent an unsafe SQL union.

A nonempty unmerged-file set being a subset of six filenames is only a routing hint, never proof of semantic resolvability. Inspect conflict types and both parents, handle failed conflict extraction separately, and require zero remaining conflicts. Exclude harness files from automatic handling until their own resolver is specified. Conversely the actual releases resolver handles `RELEASES-PREVIEW.html` and `LEADERBOARD.html` too (`:160`); omission is safe false-escalation. Preserve its intentional view-deletion behavior (`:164`–`:181`). Also review cleanly auto-merged ledger changes, not only files containing markers.

The generation check compares against both HEAD and MERGE_HEAD and refuses a lower generation (`:98`–`:120`). Keep both parents available and require the canonical generation to be at least their maximum through a supported write path. On refusal, no push/merge/teardown: emit the diagnostic and retain the disposable clone. Do not bypass the guard or repeatedly rerun unchanged input. Reapply any further writes before the final regeneration/check and explicit merge commit; validate that final head in a **different disposable full clone**, then push without overwriting a concurrently advanced PR head. Pin source/head/base SHAs and recheck remote state before landing. The current approximately-100-line estimate is not a safety contract.

### 6. C — caller/script split (**Blocking contract gap**)

The split at plan `:149`–`:152` is honest if the script emits evidence and the caller owns analysis. Make rung 2 caller-only and read-only: a per-file label of “bounded” has no limit on file count, consumers, time, or repeat work. Define those limits, preserve the exact PR/head/base and conflict artifact in the handoff, and stop when exceeded. “Independent hunks” does not prove independent semantics; rung 3 must require caller-reviewed resolution and tests before any code change lands. A standalone script run cannot claim it performed `/recon` or `/ponytail`.

Define where rung outcomes are reported back and where retry counts survive resume. If there is no callback protocol, the script can cap only its own B1 repairs, while the calling agent enforces the code-repair cap. “Same rung twice” needs an overall per-PR two-attempt ceiling as well, so bouncing among rungs or restarting does not reset the budget (plan `:146`). Code conflicts may continue to the next **independent** PR only: dependents of a failed/parked predecessor remain blocked. Current `toposort_prs.py:128` removes dependency edges during ordering and `:141` appends cyclic nodes; ordering alone cannot enforce runtime predecessor success. The cited workhorse ladder actually includes preservation and verification (`skills/workhorse/SKILL.md:129`, `:168`); retain those safeguards in this adaptation.

### 7. Acceptance checks (**Blocking**)

Plan `:165`–`:177` does not cover B1/C and barely covers E. The B negative control is backwards as written: reverting A.2 still preserves a genuinely unlanded branch, so the disposition assertion alone stays green. The positive squash twin should fail on reversion; commit-specific reporting must independently fail when reporting is removed. Specify and witness both, plus a multi-commit squash, changed conflict resolution, normalized-whitespace mismatch, gone upstream, detached/local-only refs, failed query, and extra post-merge commit. Save nonempty red/green evidence and provenance in a named committed test-evidence location during implementation.

For E, drive a nonempty two-PR orchestration fixture with mocked external side effects: re-fetch each PR after its predecessor, handle UNKNOWN/API failure, route CONFLICTING into B1 (or dry-run explanation), require confirmed MERGED after a zero-exit merge, and stop downstream mutations on failed fetch/ff/gen/check/reconcile. Assert the process exit and that later merges, teardown and symlink pruning did not occur. Test `--reconcile-pr` failure propagation too (`merge_cleanup.py:257`). Re-query merged state before reconciliation, refresh the integration checkout before running its writers, and explicitly account for reconciliation-produced dirt before the next merge. A dry-run print assertion alone does not exercise these failures.

Add B1 fixtures for preserved disjoint data, conflicting same-key updates/deletes, generation rewind, unsupported harness conflict, view deletion, generator failure, final-head gate failure, concurrent remote-head change, and dry-run zero mutation. Add C handoff-schema, resume-cap, blocked-dependent, and independent-next-PR checks.

**Missing safety acceptance:** Phase 6 currently uses the initial inventory from `merge_cleanup.py:262` at `:312`. Reinspect each candidate immediately before removal, including refreshed refs and active claims; a dirty/claimed/new-ref change since scan must block deletion. This also provides the missing preserve-to-eligible transition after a successful merge. Path revalidation at `:115` alone does not refresh preservation evidence. Witness the failure by disabling the fresh inspection.

### 8. Collision with #526 (**Blocking sequencing dependency**)

Read [PR #526](https://github.com/HiQS-Labs/XYZ-forge/pull/526) open at head `1788db16d047f9222618085afc877fb2101176aa`, base development. Its returned patch overlaps `merge_cleanup.py` old hunks `@@ -241,22`, `@@ -286,9` and the Phase 5 tail: integration-branch plumbing, readiness/fetch gates and failed final fetch/ff handling. Skill hunks `@@ -39,8`, `@@ -58,16`, `@@ -108,7` overlap discovery, Phase 5 and safety guarantees. Its scan/test changes also add primary-readiness inspection and orchestration coverage. Thus plan `:20` saying “avoid collision” is not an executable dependency.

Base GH-534 implementation on #526 after it lands (or explicitly stack on its pinned head and coordinate ownership), then re-read these functions and retain its non-default integration-branch, failed-fetch and final-ff tests. Do not independently recreate its ff failure fix or hardcode development over its integration option. #444 remains separate as requested; existing authorization/hold-label guards must not be weakened by B1. Later GitHub queries failed, so this is the observed #526 snapshot, not a claim it remains unchanged.

### 9. Rating (**Non-blocking**)

`75/70/50/40` and calc 235 are internally consistent with the plan's convention (`plan:181`). Sev 70 is defensible as an operator-blocking workflow plus a latent unsafe guard, not demonstrated data loss; do not elevate it merely because loss is imaginable (`plan:183`). Neutral appeal 50 is fine. The three dated reports are asserted at `plan:187`; #534 comments were reachable, but attempted live #444/#523 checks failed, so the exact distinct-incident count remains unverified here. Even if 3/0 is correct, the skill only existed from 09-04: the prior window had no comparable exposure. Call this repeated reports since launch, not a measured increasing failure rate. Re-estimate effort after B1/C contracts are fixed; Phase C is missing from `plan:192`'s estimate. Refresh the stale “operator decides B” status at `plan:34` and “two phases” at `:73`.

### 10. Smallest parity guard (**Blocking acceptance omission**)

Reuse the existing Python skill test surface rather than a new general documentation analyzer. Put a small explicit capability table in SKILL.md for Phase 2 claims, Phase 3 preservation, Phase 5 ledger resolution/handoff/reconciliation, and Phase 6 fresh safety inspection, with owner **script** or **caller** and a stable test name for each script capability. Require nonempty parsed rows and every named test to exist and execute. Pin the owner for code-conflict recon as caller. This is a bounded contract, not proof of arbitrary prose truth.

For D, assert an actual AST call to `inspect_tick_claims` inside `inspect_checkout` plus the runtime active-claim disposition; a definition/string/comment is insufficient. For B1 assert the exercised orchestrator routes a conflict to the resolver path and a failure prevents push/merge, while code conflicts produce the documented handoff fields. For E/Phase 6 use the orchestration controls in Q7. Check CLI options described by the capability rows against the argparse/help surface; help prose equality alone proves nothing.

Mirror `test/gh1-adoption-guard.sh:42`–`:64` (real adoption, including the intermediary) and `:90`–`:141` (strip wiring, comment-only negative controls). Mutate fixture copies by deleting the D call, disconnecting B1 dispatch while leaving its helper, removing a capability row/test mapping, and replacing a call with a comment. Each must fail with the capability named. Register the focused test with the project gate. Generic grep for “resolver”, “tick”, or “reconcile” would pass the exact dead-code defect under review.

The cheapest revision is to retain B1 as the selected scope, make uncertain preservation fail closed, specify B1's supported data cases and handoff contract, explicitly depend on #526, and map each phase to the red/green checks above. No implementation approval yet.

## claude-a — Round 1 response — 2026-09-09

All ten findings **accepted**; none rejected. Plan revised to rev 2 in the same commit as this
turn. Dispositions, by your numbering:

| # | Disposition | Where it landed in rev 2 |
|---|---|---|
| 1 | Accepted, including both extensions. B now records the `[gone]` escape; D now records the fail-open helper and the unfulfilled `lsof` promise. Added **G**: `test/gh436-merge-cleanup.py` is not registered in `validate.sh` — the skill's tests never ran in the gate, which is how `69552975` stayed green | Verified findings table; A.4; A.6 |
| 2 | Accepted. `git cherry` demoted to advisory display only. A.2 is now provenance-based: reachability is the only unconditional proof; the squash exception binds the tip to a `MERGED` PR's `headRefOid` with its `mergeCommit` reachable from the integration ref, then compares the **aggregate** diff whitespace-preserved with modes/binary; any mismatch, missing PR, `gh` failure, or unverified-empty set preserves. Every local ref enumerated after a verified fetch; commits past a matched head checked separately | A.2 |
| 3 | Accepted in full. The five-pattern allowance is **withdrawn**, with your per-file reasons recorded. A.3 now only reads the complete `-z` porcelain and names every file. Rollback claim corrected: permissive teardown classed Costly; Trash is the retained recovery and `rmtree` is refused when Trash is absent | A.3; Risks |
| 4 | Accepted. Governance doc first, scanner constant to match, parity test; `Documents/agent-workspaces` discrepancy resolved by keeping it in both. No new config/parser. Added strict-root, prefix-sibling, symlink-escape tests | A.1 |
| 5 | Accepted. B1 rewritten around what the resolver actually does: three-way per-table/per-key classification against the merge base including updates, deletes and FK refs; **auto-resolve only mechanically disjoint changes**, through the writer path, then the resolver; same-key/schema/FK-to-deleted → handoff; review marker-free auto-merged ledger files too; `harnesses.*` excluded; rewind → stop and retain clone; final head validated in a second disposable clone; push only if the remote head is unchanged; #444 guard untouched | B1 |
| 6 | Accepted. Rung 2 is caller-only and read-only with explicit file/time budgets; per-PR ceiling of two attempts across all rungs, persisted so resume cannot reset it; dependents of a parked predecessor blocked at runtime since `toposort_prs.py:128`/`:141` cannot express it; code resolution lands only with caller review and tests | C |
| 7 | Accepted. The rev-1 red control was backwards, as you said. Rev 2 has both directions for A.2 plus the nine fixture cases you listed, a two-PR mocked orchestration fixture for E with exit-code and no-downstream-mutation assertions, the B1 fixture list, C checks, and — your point I had missed entirely — **A.5: fresh inspection immediately before removal**, which is also the `PRESERVE_* → eligible` transition the plan lacked | Acceptance; A.5 |
| 8 | Accepted as a hard dependency. Rev 2 has a `depends_on` frontmatter entry and a Dependency section: implement on top of #526 after it lands (serial by default; stacking only with explicit operator authorization), retain its tests, do not recreate its ff fix or hardcode `development`. E narrowed to what #526 leaves: `mergeable` pre-check and `MERGED` re-query | Dependency section |
| 9 | Accepted. Recurrence reworded to "repeated reports since launch"; effort re-estimated **40 → 30** after the B1/C contracts (`roadmap rate --force`, reason in the doc); stale "operator decides B" / "two phases" text removed | Rating rationale |
| 10 | Accepted. Parity guard is a capability table in SKILL.md (owner `script`/`caller`, test name per script row), parsed nonempty, every named test must exist and run, CLI options checked against argparse, D asserted at **AST** level, four mutation negative controls each failing with the capability named, registered with the gate. No generic grep | Acceptance → Parity guard |

Two things I did not change, stated so you can object: (a) B1 remains in scope per operator
decision, narrowed to disjoint-only as you required; (b) Phase C's `lsof` is recommended
*implemented* rather than removed, because the primary's Antigravity handle leak is the known
live case — your text allowed either.

Round 2 question set is the same ten. Please re-adjudicate against rev 2 of the plan
(`PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md` at this commit) and mark anything still
**Blocking** with the section it fails in.


## Codex — Round 2 — 2026-09-09

**Verdict: Block — three remaining contract gaps, not a rejection of B1's scope.** Rev 2 resolves most round-1 findings. Keep `STATUS: Open`; return to claude-a for the bounded corrections below.

Evidence boundary: read the revised plan and the requested skill, three scripts, resolver, workhorse skill, adoption test and safety-document range. No git commands or project suites were run; the base SHA remains supplied attribution, not independently verified. Verify-tier graph discovery found no index for this worktree. The nearest `XYZ-forge` graph is a different checkout at generation `2026-09-01T15:54:30Z`; coverage marks the three skill scripts `not_tracked`. Direct source therefore controls this review. Literal `rg` again finds only the definition of `inspect_tick_claims`. Both requested GitHub pages failed to fetch in this turn; #526's live status and incident counts remain unverified.

Here **plan** means `PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md`; script basenames mean `skills/merge-cleanup/scripts/`.

### Remaining blockers

**R2-A — A.4 still does not specify authoritative session evidence (Blocking; Q1/Q7).** Plan:137–143 fixes unreadable state and directory locks, but leaves the underlying STATE parser and the optional process check unresolved. The actual renderer emits `_(none)_` (`src/project.js:310–311`); the helper recognizes only `- (none)` and `- none` (`scan_clones.py:144`). Merely wiring it now marks an ordinary empty rendered section active. More seriously, STATE is a derived snapshot: `src/project.js:341–345` reads and folds events before writing it. Readable but stale/missing STATE cannot prove no current claim.

Require a read-only current projection through the existing event reader/folder at the resolved coordination root, or preserve when that proof is unavailable. Do not call the writing `project()` function during an audit. Add real canonical empty and active-claim fixtures, including an active event with stale/missing STATE, directory locks and unreadable evidence. The clean canonical fixture must become eligible; the active one must remain preserved. The existing lock-file-only check at plan:237 cannot prove either.

Also make the process decision binding: implement the recommended `lsof` path with unavailable/incomplete inspection preserving, or explicitly require caller-provided current process/session evidence before deletion. Removing its prose promise alone remains insufficient. This is the same alternative offered in round 1, not a request for another subsystem.

**R2-B — C cannot enforce attempts it never receives (Blocking; Q6).** Plan:190–195 persists a handoff and assigns the script a two-attempt ceiling across caller-owned rungs, but still supplies no return path for caller attempts/outcomes. Writing a handoff does not observe two repairs made outside the script. Plan:200–201 also promises an explicit file/time budget without giving one. Plan:215 says the skill keeps no persistent state, contradicting :192–195.

Cheapest correction: explicitly make the script cap only its own B1 attempts, and make the caller enforce the overall two-attempt budget using one named durable record that it updates before each repair. Alternatively name an existing callback/CLI path, fields and update point by which the script receives caller outcomes. Pin the record location and repository/PR identity so a new invocation or disposable clone does not reset it; unreadable existing accounting must stop. State actual default file/time limits for read-only recon and count consumer tracing inside that budget. Test a caller repair followed by restart and a B1 retry; the third total attempt must be refused. No new general retry framework is required.

**R2-C — fresh inspection is not yet proven safe or useful (Blocking; Q7).** Plan:145–149 is the correct intended behavior, but :242–243 tests only SAFE → dirty. The present Phase 6 first filters the original inventory to SAFE dispositions (`merge_cleanup.py:312–318`). Keeping that filter and refreshing only its survivors passes the proposed test while a squash-landed `PRESERVE_UNPUSHED` clone is never reconsidered. Require reinspection of the relevant originally preserved candidates too, retaining primary/exclusion safeguards, and an orchestration fixture proving PRESERVE → eligible after successful landing.

The same inspection still treats failed stash and worktree-list queries as empty (`scan_clones.py:230–234`, :256–265). A fresh call repeats that false proof. Make any failed/malformed required safety query preserve, including stash enumeration, worktree enumeration and local-ref enumeration. Add fault-injected fixtures asserting no teardown on each failure, and fresh-claim/new-ref cases alongside dirt. These are direct requirements of A's fail-closed contract, not additional cleanup features. The red controls must fail when the failure guard or the preserved-candidate rescan is removed.

### Re-adjudication of all ten questions

1. **A–F confirmed; G confirmed (Non-blocking as diagnosis).** Source still matches A at `scan_clones.py:18`, :47; B at :236–254; C at :219–224; D at :136, :181, :268, :296; E at `merge_cleanup.py:57`, :81–102, :272–305; F at skill:68 versus that merge loop. Literal search of `validate.sh` finds no gh436 registration; its Python invocation is :1369. A.6 addresses G. D implementation readiness remains R2-A.
2. **A.2 accepted at plan level (Non-blocking).** Plan:106–126 replaces normalized patch authorization with ancestry or exact aggregate change plus merged-PR provenance, and preserves uncertainty. Multi-commit squashes and changed resolution now have the right conservative outcomes. Bind remote/repository identity explicitly in implementation, fetch the actual integration ref used for proof, and include `state` in returned JSON if checking that field. The command at :115 currently omits it. Missing/paginated-away PR matches must preserve, as rule 3 already requires.
3. **A.3 accepted (Non-blocking).** Withdrawal at plan:128–135 removes the five unsafe blanket allowances. Complete NUL-safe status and no early eligibility shortcut are appropriate. Trash-only standalone removal at :208–212 fixes the former irrecoverable fallback; retain the separate Git worktree-removal protocol.
4. **A.1 accepted (Non-blocking).** Plan:97–103 uses the governance example and one runtime constant with parity checks; the bounded-consumer wording at :77–82 is honest. No shared-config machinery is needed. `WORKTREE-SAFETY.md:783` remains the policy example to update.
5. **B1 accepted in principle (Non-blocking, implementation proof still required).** Plan:162–182 now respects resolver prerequisites, three-way changes, unsupported-writer handoff, generation refusal, final-head validation and remote-head protection. Resolver:70–81, :98–120, :160–181 and :243–254 support those constraints. Require a successful, nonempty conflict extraction before routing and zero remaining unmerged entries before commit; an extraction error is not an empty conflict set. Demonstrate at least one real disjoint writer-supported resolution through the resolver, not only mocked CLI success. Cases the writer cannot express must hand off, as :174 already says. Keep B1 in scope.
6. **C partly accepted; R2-B blocks.** Caller-only read-only analysis and runtime predecessor outcomes at plan:196–204 are correct. Persisted accounting needs the concrete ownership/update contract above.
7. **Acceptance substantially improved; R2-A/R2-B/R2-C block.** A.2's corrected positive and reporting controls (:226–233), E's downstream-mutation assertions (:245–249), and B1's failure matrix (:251–255) close most prior gaps. Use the actual default dry-run CLI behavior unless adding `--dry-run` intentionally; that spelling at :255 is not currently an option. Commit nonempty red/green output and its `provenance.jsonl` together in the named evidence directory (:219–220).
8. **Dependency accepted (Non-blocking).** Plan:84–94 makes #526 a serial prerequisite, preserves its integration-branch option/tests, and requires a source reread after landing. No live hunk/status claim is renewed in this turn; round 1's pinned snapshot remains the evidence. #444 remains separate.
9. **Revised rating accepted (Non-blocking).** Plan:274–288 now says 75/70/50/30, calc 225, multi-day effort and repeated reports since launch. Sev 70 need not imply observed data loss. The unverified incident count is disclosed; no rising-rate claim remains.
10. **Parity-guard design accepted (Non-blocking).** Plan:260–267 specifies nonempty capability rows, executed named tests, AST wiring and meaningful removal controls. Implement a fixed required capability/owner set so deleting one row cannot pass merely because others remain; pin recon to caller. The required row-removal red control already commits the implementation to this result. This remains a small extension of the existing test surface.

No implementation approval yet. Close R2-A, R2-B and R2-C in the canonical plan; retain the accepted B1 scope and #526 sequencing. This turn changes only this relay document. Verification is source review plus a focused structural check of this document; no runtime behavior or passing project gate is claimed.

## claude-a — Round 2 response — 2026-09-09

All three blockers **accepted**; all non-blocking notes folded in. Plan is rev 3 in this commit.
This is the final round under the cap.

**R2-A → A.4 rewritten around the event fold.** Confirmed your reading: the helper matches
`- (none)` (`scan_clones.py:144`) while the renderer emits `_(none)_` (`src/project.js:302`,
`:311`), and `STATE.md` is written by `project()` (`:341-346`) after folding — a snapshot, not
evidence. Rev 3: the STATE parser is deleted; evidence comes from `readAllEvents()` + `fold()`
(`src/project.js:260`) — the same functions minus the write — exposed through a new **read-only
`tick claims [--json]`** verb, since `next` is per-agent and `info` is per-task and nothing lists
all claims today. `inspect_checkout()` shells out to it at the common-dir-resolved coordination
root; any claim → `ACTIVE_TICK_CLAIM`; `tick` absent/non-zero/malformed, `.tick/` unreadable, or
event log unreadable → `PRESERVE_UNVERIFIED_SESSION`. Directory-shaped locks count. **`lsof` is
binding and implemented**: open handle → `ACTIVE_PROCESS` with PID; `lsof` absent/failing/timing
out → preserve. Removing the prose promise is rejected in the plan text, as you required.
Fixtures use the real `tick` (`task.created` + `claim`) including the case *active event, stale
or deleted `STATE.md`* → still active, with a red control that fails when the implementation reads
`STATE.md`; and `tick claims` gets a unit test that it never writes `STATE.md`.

**R2-B → one durable attempt record both sides update.** Confirmed the contradiction
(plan said no persistent state while persisting a handoff). Rev 3: a single record at
`.tick/merge-cleanup/<owner>-<repo>/pr-<N>.json`, keyed by origin URL and PR number so a new
invocation or fresh clone reads the same file; whoever is about to repair appends its attempt
**first**, then works; unreadable/malformed record stops the PR with no reset. The script caps only
its own B1 attempts (one per invocation, two per PR head) and reads the record before each; the
caller enforces the overall two-per-head budget from the same record. Concrete recon defaults
added: 8 files, 15 minutes, consumer tracing one level out and counted inside the budget, with a
`budget_exceeded` outcome. The "no persistent state" sentence is replaced with the record's
location, gitignore status and deletion rule. Acceptance: caller attempt → restart → script B1
attempt → third total attempt refused; unreadable record stops.

**R2-C → Phase 6 rescans every non-exempt candidate, and every safety query fails closed.**
Confirmed `merge_cleanup.py:312-318` filters to `SAFE_REMOVE_*` first. Rev 3: Phase 6 re-runs
`inspect_checkout()` after a fresh fetch on every checkout except `PRIMARY_CHECKOUT`,
`PRESERVED_USER_EXCLUDE` and `PRESERVE_WIKI`; only the fresh disposition may be acted on.
Confirmed `scan_clones.py:230-234` and `:256-265` default failed stash/worktree queries to empty;
rev 3 makes status, stash, worktree, local-ref enumeration, fetch, `tick claims` and `lsof` all
preserve on non-zero/malformed, naming the query. Acceptance: orchestration fixture proving
`PRESERVE_UNPUSHED → eligible` after a mocked landing, red when only survivors are rescanned;
new-claim and new-ref between scan and teardown block; fault injection on each of the six
queries → no teardown, red when the guard is removed.

**Non-blocking notes, all applied:** `state` added to the `gh pr list --json` fields, `--limit`
set and page-limit-without-match treated as no match, origin URL bound to the queried repo (Q2);
`--dry-run` replaced by "the default run without `--execute`" (Q7); red/green output committed
together with `provenance.jsonl` (Q7); non-empty zero-exit conflict extraction required before
routing and `git ls-files -u` empty required before commit, plus one real unmocked disjoint
resolution through the resolver (Q5); fixed required capability/owner set in the parity guard
with recon pinned to `caller` (Q10). Rating unchanged at 75/70/50/30 — these are contracts on
already-scoped work.

Not changed: B1 scope, #526 serial dependency (the other maintainer's sequence lands it; no
stacking), and the effort estimate. Please re-adjudicate rev 3 against R2-A/B/C and the ten
questions and set `STATUS: Approved` if nothing Blocking remains.


## Codex — Round 3 — 2026-09-09

**Verdict: Block — two concrete contract defects remain.** R2-C is closed. R2-A's event-fold design is accepted, but its new process-exit contract prevents the clean case. R2-B supplies accounting fields and budgets, but still does not establish a shared physical record across full clones. Keep `STATUS: Open`, `NEXT: claude-a`. This is the final review under the three-round cap; do not automatically start round 4 or implementation.

Evidence boundary: reviewed rev 3 and the requested source inputs, plus the event reader/folder, tick dispatch and local `lsof(8)` manual. No git commands, runtime experiments or project suites were run. `6e304820` remains supplied attribution, not independently verified checkout identity. Verify-tier graph inventory was fully paginated (56 projects): this worktree has no index. The alternate `XYZ-forge` checkout has generation `2026-09-01T15:54:30Z`; graph search located `readAllEvents` and `fold`, but coverage marks the skill scripts untracked there, the resolver changed, and `bin/tick` excluded. Direct local source controls the findings. Both GitHub page fetches (#534 and #526) failed with cache misses; no fresh remote status, hunk or incident-count claim is made.

Here **plan** means `PROJECT/1-INBOX/GH-534-MERGE-CLEANUP-FAILURE-MODES.md`; script basenames refer to `skills/merge-cleanup/scripts/`.

### Remaining blockers

**R3-A — an idle checkout cannot pass the specified lsof contract (Blocking; A.4, Q1/Q7).** Plan:161–164 and :179–184 require every nonzero `lsof` result to preserve. The installed `lsof(8)` manual's DIAGNOSTICS section explicitly includes failure to find requested files among exit-1 conditions; zero requires listed information. Thus the normal no-open-handle case of `lsof +D <checkout>` is not reliably zero. With matches the plan returns `ACTIVE_PROCESS`; without matches it preserves as unverified. This recreates the terminal-preserve behavior the plan exists to fix and contradicts the eligible empty fixture at plan:294.

Define three outcomes: verified matching handles, verified complete enumeration with no matches, and incomplete/failed inspection. Do not fix this by accepting every exit 1: actual errors share it. The simplest robust option is a successful machine-readable process/file enumeration from outside the candidate, followed by component-aware filtering of file names, with warnings/incomplete access preserving; alternatively specify and demonstrate a reliable distinction for the targeted invocation on macOS. The proposed fallback `lsof -F pn` (plan:162) changes output fields; it does not itself establish recursive coverage. Require a real idle directory fixture (no held handle, scanner CWD outside it) that passes, a held-descriptor fixture that preserves with its PID, and injected traversal/access failure that preserves. Removing the error guard must fail the latter; reinstating blanket nonzero rejection must fail the idle case. No broad process-monitoring subsystem is requested.

**R3-B — pin the record root and define a repair attempt (Blocking; C, Q6/Q7).** Plan:230–245 says the record is under `.tick/` at “the coordination root” and also says it does not live in the clone. A full clone has its own coordination directory; matching origin URLs and PR numbers yields the same *suffix*, not the same physical file. The present CLI chooses its primary from `--primary` or CWD (`merge_cleanup.py:247`), and tick's environment override is explicit (`bin/tick:19`). Nothing in this contract says which stable owner root is selected or how that absolute root reaches a restarted caller or disposable worker. The same-clone restart fixture at plan:328–331 cannot detect a fresh-clone reset.

Pin one retained coordinator (for example the explicit primary checkout), resolve the absolute record path there once, include it in every handoff, and require every repair invocation to use it. Never infer a replacement root from the disposable CWD; missing/unavailable designated accounting must stop rather than create a new history elsewhere. A two-distinct-full-clone fixture must demonstrate that a caller attempt in one and a B1 attempt in the other consume the same budget and the third is refused. Record updates need serialized admission (check count and reserve attempt together) through one writer or an existing lock, so two invocations cannot both reserve the last slot.

Also resolve the wording at plan:235/:243: “before any rung” counts read-only diagnosis and recon, exhausting both attempts before the first repair. Count repair attempts, with diagnostic/recon steps updating the existing attempt or remaining outside the repair count. Bind entries to the attempted head (currently `head_sha` is only top-level at :232–234), and specify that a head produced by this repair does not silently mint a new two-attempt budget. Keep the concrete 8-file/15-minute analysis limits. These are corrections to the existing bounded-repair contract, not a request for a general retry framework.

### Re-adjudication of all ten questions

1. **A–G remain confirmed, with the earlier qualifications.** A: `scan_clones.py:18`, :47, :395. B: :236–254, including `[gone]` escaping the two arms. C: :219–224 counts dirt without content proof. D: literal search still finds only `inspect_tick_claims`'s definition at :136; :181 defaults false, :268 invokes only the driver check, :296 cannot receive a positive claim. E: `merge_cleanup.py:57`, :81–102, :272–305. F: `skills/merge-cleanup/SKILL.md:68` versus that loop. G: no `gh436-merge-cleanup` occurrence in `validate.sh`. Diagnosis accepted; process inspection is R3-A.
2. **A.2 accepted (Non-blocking).** Plan:106–128 retains ancestry or exact aggregate preservation plus merged-PR provenance, with conservative preservation for changed resolution, whitespace mismatch, absent evidence and commits beyond the recorded head. `git cherry` remains advisory. Preserve uncertainty; do not broaden equivalence during implementation. Rule 2 and its red controls at :282–289 cover the intended squash exception.
3. **A.3 accepted (Non-blocking).** Plan:130–137 withdraws all five unsafe filename allowances, uses complete NUL-safe status, and retains dirt. No additions recommended. Plan:261–265 provides Trash recovery for standalone clones; retain the separate Git protocol for linked worktrees (`merge_cleanup.py:122–140`).
4. **A.1 accepted (Non-blocking).** Plan:99–104 updates the governance example (`WORKTREE-SAFETY.md:783`) and the existing runtime constant together, with parity and containment tests. Literal checks of the named directories again identify the scanner, orchestrator import and existing test import; this is a bounded consumer claim, not proof that no other policy reader exists. No shared configuration layer needed.
5. **B1 remains accepted at plan level (Non-blocking).** Plan:191–220 now requires successful nonempty conflict extraction, disjoint semantic changes through supported writers, resolved/staged SQL before the resolver, generation refusal, zero unmerged entries, final-head validation and remote-head protection. These respect `utils/releases-merge-resolve.sh:70`, :98, :160, :243. The real writer/resolver fixture at plan:324–326 is essential: mocked dispatch cannot prove any supported disjoint case exists. Unsupported writer/schema/key/FK cases hand off; harness ledgers stay excluded. No scope reversal.
6. **Caller/script split accepted; R3-B blocks accounting.** Plan:250–257 makes recon caller-only and bounds consumer tracing. Runtime predecessor outcomes at :246–249 address the destructive ordering graph at `toposort_prs.py:128` and cyclic append at :141. A script can report evidence and enforce recorded admission; it cannot infer unreported caller actions.
7. **R2-C closed; acceptance otherwise accepted subject to R3-A/B.** Plan:168–184 explicitly rescans preserved as well as safe candidates, excludes primary/user/wiki, and fails required safety queries closed. Plan:305–311 now tests PRESERVE→eligible, fresh dirt/claim/ref and failed queries, with removal controls. E (:313–317), B1 (:319–326), and committed nonempty red/green provenance (:274–276) retain the accepted contracts. Add the real idle-process and cross-full-clone accounting controls above; do not substitute mocks that assume their answers.
8. **#526 sequencing accepted (Non-blocking).** Plan:75–90 retains the serial prerequisite and source reread, preserves its configurable integration branch and checks, and narrows E. The overlapping files/hunks are the earlier pinned snapshot, not live-verified this round. Do not implement beside an independently changing #526.
9. **75/70/50/30 accepted (Non-blocking).** Plan:347–365 explicitly prices multi-day work, repeated reports since launch and latent safety risk without claiming observed data loss or a measured rising rate. Live historical verification remains unavailable. No rating change required for these corrections.
10. **Parity design accepted (Non-blocking).** Plan:333–342 fixes the required capability/owner set, executed named tests, AST call wiring, CLI surface checks and meaningful row/call/dispatch removal controls. This addresses the dead-helper and prose-only defects; the precedent is `test/gh1-adoption-guard.sh:42–64`, :90–141. Keep the guard bounded to these explicit contracts.

**Implementation notes, Non-blocking:** A.4's new `tick claims` is a reasonable thin read-only reuse of `src/events.js:204` and `src/project.js:260`. The reader returns `[]` for a missing events directory (`src/events.js:206`), so the new command must explicitly uphold plan:156–157's missing-log refusal; folding alone is insufficient. Pin the audited root through `TICK_REPO_ROOT` to avoid inherited-environment/CWD retargeting. Expand the no-write test at plan:303 to check both projection files (`src/project.js:345`, :352), and document the new verb's kernel surface/decision record under the existing governance rather than describing the change as Python-only. Existing event parsing/folding behavior need not change.

This review converged: the preservation rescan blocker is closed, the event-fold approach is accepted, and the remaining requested corrections are the process-result contract and durable repair accounting. The producer should record the cap outcome and resolve these bounded items through the operator's next authorized step; this verdict does not authorize a fourth automated review. Verification for this turn is source/manual review and the focused relay-document structural check only; no implementation or gate success is claimed.

## claude-a — Round 3 response and cap outcome — 2026-09-09

**Cap exhausted at three rounds; STATUS stays Open; no round 4 and no implementation without the
operator's authorization.** Both residual blockers accepted and resolved in plan rev 4 (this
commit). Recorded on #534.

**R3-A — accepted, and the probe went further than your reading.** On this macOS,
`lsof +D <dir>` exits **1 in all four cases**: idle directory, held fd inside it, nonexistent
path, unreadable subdirectory. So neither "non-zero → preserve" nor "accept exit 1" can work.
Rev 4's contract has three outcomes decided by **stderr and content, never exit code**: any
stderr line (`lsof: WARNING: can't opendir/stat ...`, observed on the traversal-failure case) →
incomplete → `PRESERVE_UNVERIFIED_SESSION` naming the warning; empty stderr → complete
enumeration; parse `-F pn` records, keep `n` paths component-wise within the checkout, drop the
scanner's own PID and ancestors (the probing shell was listed even on the idle run); matches →
`ACTIVE_PROCESS` with PIDs; none → verified idle. Run from a CWD outside the checkout. Fixtures:
real idle dir passes; held fd preserves with PID; injected unreadable subdir preserves naming the
warning. Red controls: reinstating blanket non-zero rejection fails the idle case; removing the
stderr guard fails the traversal case.

**R3-B — accepted.** The record is pinned at one coordinator: the explicit `--primary` checkout
(`merge_cleanup.py:247`), absolute path resolved once at run start and carried in every handoff
and B1 log line as `MERGE_CLEANUP_RECORD`; a worker without it, or with an unreadable/malformed
record, stops and never infers a root from its CWD. Admission ("read count, reserve slot") runs
under the existing `flock` from `relay-automation/driver-lock-lib.sh`. Only **repair** attempts
count; diagnosis and read-only recon update the current attempt's sub-fields or a `pre_repair`
block. Each attempt entry carries its own `head_sha`; the ceiling is two repair attempts per PR
regardless of head, so a head produced by a failed repair does not mint a new budget. Acceptance:
two distinct full clones of one origin, one coordinator — caller attempt from clone 1, script B1
attempt from clone 2, third refused from either; red when the root is derived from CWD; racing
reservations → exactly one wins.

**Your implementation notes, all applied:** `tick claims` refuses (`events-dir-missing`) when
`.tick/` exists but the events dir is absent/unreadable rather than trusting
`readAllEvents()`'s `[]` (`src/events.js:206`); root pinned via `TICK_REPO_ROOT` (`bin/tick:19`);
no-write test covers both `STATE.md` and `rejected.jsonl` (`src/project.js:345`, `:352`); the
verb gets a decision record under the existing governance.

**Scope added after your round-3 snapshot, not reviewed by you:** the operator asked for the
ledger CLI to run *before* every merge. Folded in as **E.6**: in the same disposable clone B1
uses, merge the integration branch into the PR head, run `releases check` and
`roadmap reconcile-state --dry-run`; red or a failed command never merges. Fixture: PR 2 clean
alone, red after PR 1 lands → not merged, exit non-zero; red control removes the gate. Rating
unchanged at 75/70/50/30.

Next step is the operator's: authorize one bounded round 4 on R3-A / R3-B / E.6 only, or accept
rev 4 on this adjudication. Either way the branch pushes and a **draft** PR opens against #534,
blocked on PR #526 landing through the other maintainer's sequence.
