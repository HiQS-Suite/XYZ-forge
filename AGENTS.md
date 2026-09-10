# AGENTS.md

## Danger: commands agents must not run

- Never run `git reset --hard`, `git checkout -- <path>`, or a tree-wide `git stash` in a checkout
  whose state matters; they overwrite tracked work or hide shared worktree-family state.
- Never run `rm -rf`, `find ... -delete`, or equivalent recursive cleanup through an empty,
  unresolved, relative, root, home, workspace, or otherwise unproven target path.
- Never remove or move a linked worktree with `rm -rf` or `mv`, and never hand-delete
  `.git/worktrees/*`; use `git worktree remove` / `move` / `prune` / `repair`.
- Never run sandboxed `git switch --track` or `git branch -D` directly; wrap the complete command
  with `utils/git-sandbox-guard.sh --repo <root> -- <git command>`.
- Never delete or move a full-clone folder until its working tree, stashes, local refs, and registered
  worktrees prove that it contains no unique or depended-on state.
- Never run `validate.sh` or `test/*.sh` from a linked worktree or a full clone whose state matters;
  run mutation-heavy gates only in a separate disposable full clone.

Read [`WORKTREE-SAFETY.md`](WORKTREE-SAFETY.md) for the rationale, recovery paths, and safe patterns.

> **Safety and warranty:** XYZ Forge is provided **“AS IS,” without warranty**, under the applicable
> license. Coding models may choose commands through their own runtimes and safety controls, outside
> the intended harness workflow. XYZ Forge cannot guarantee model behavior or data integrity; maintain
> tested, independent backups and follow industry-standard backup and recovery practices.

Read `ROUTER.md` first for startup order and canonical files.

Read `GUIDING-PRINCIPLES.md` for the product north stars — its "The North Star" section (durable,
reversible, DRY; extend what exists rather than forking a parallel system) is canonical and governs
everything below.

Read `PROJECT/PDDA.md` when the task touches project docs or `CHANGELOG.md`.
Its document contract is adopted here; [ROUTER’s role split](ROUTER.md#role-split) distinguishes
XYZ-owned policy from PDDA-layer scope.

Read `HARNESS-MODELS-REGISTRY.md` for evaluated agent harnesses, model compatibility grades, and CLI flags.

Read `TESTS-RESULTS/README.md` for committed test artifacts, telemetry receipts, and benchmark logs.
Read `SOP.md` → "Arc planning" before starting a large refactor — scheduling the follow-up arcs (review/dogfood/conformance lanes) at plan time is what keeps the arc linear.

## Runtime default

Entry-point shims run their **Python** implementation by default (`XYZ_PYTHON` unset → Python). To
force the legacy Bash path for a single run, prefix it with `XYZ_PYTHON=0`; for a whole session,
`export XYZ_PYTHON=0`. The Bash body stays inline in every shim, so the opt-out is always available.

## What this file owns

This file is the behavioral playbook for work in this repo: decision quality, reversibility, blast
radius, planning shape, and proof.

Do not restate routing, roadmap, changelog, or active-doc contracts here. Those live in
`ROUTER.md` and `PROJECT/PDDA.md`.

After a PR merges into `development`, the hosted reconciliation workflow (`wave-reconcile.yml`)
automatically reconciles docs, ledger, and views (`ROADMAP-DASHBOARD.md`, `LEADERBOARD.md`). Task
branches do not commit routine views. Local reconciliation via `python3 utils/py/wave_reconcile.py --pr <N>`
serves as an emergency fallback (failing closed if a hosted reconciler is in-flight; pass `--force-local-reconcile`
to override); `pdda.sh issue-doc-sync` is the deterministic drift detector when in doubt.

Maintainer-only workflow defaults (branch discipline, express-to-development, fresh-clone-per-task)
live in `SOP.md` → "Opinionated SOPs" — optional for downstream users, binding for us. That section
is a standing carve-out from the "do not create new git branches automatically" rail: it
pre-authorizes one `feat/`/`fix/` branch per fresh task clone, nothing more.

## Operating principles

### 1. Lead with the line that survives skimming

Your first sentence gives the verdict, current state, or call. No setup first.

### 2. Make the bet explicit before acting

State the assumption, tradeoff, and failure mode that matter before you commit to a path. If a future
reader could not say "that assumption was wrong," you have not made the real bet legible yet.

### 3. Use one reversibility scale

Consequential changes get a read on the shared scale: **Easy / Costly / One-way door**, with one line
of why. If undoing it would take more than a day of focused work, it is at least Costly. Costly
changes need a rollback path. One-way doors need explicit confirmation before proceeding.

This scale is how `GUIDING-PRINCIPLES.md` → "The North Star" gets applied per change; that section
owns the *why*, this one owns the read.

### 4. Size the blast radius before changing shared surfaces

Before a refactor, schema change, dependency bump, coordination-kernel change, or relay-containment
change, say what ripples, what might break, and who notices. A change you cannot size is not ready.

### 5. One plan, one ordered list

When you give executable steps, put them in one numbered list in execution order. Keep verification
inline (`-> expect ...`). Do not scatter action items across prose.

### 6. Verified beats plausible

Do not claim success without the relevant test, script, or observable proof. If verification was
skipped or failed, say that plainly and include the result.

An uncommitted `provenance.jsonl` is not proof (GH-430). Any run cited as evidence in an issue, PR,
ROADMAP entry, or decision record must have its `provenance.jsonl` committed in the same PR — a path
you merely ran and can no longer show counts as no claim at all.

**A check that cannot fail is not a check.** A passing assertion is evidence only once you have seen
it fail: mutate the thing it guards — break the code, transpose the fix, delete the value — and watch
it go red. If you cannot make it fail, it is decorative, and it is worse than nothing because it
reports confidence it never earned. This is the precise way this principle fails while looking
satisfied: you *did* verify, and the verification was hollow. Three examples from GH-377/GH-379, all
of which passed cleanly before they were mutated — an `awk` range that terminated on its own first
line, `not matches -- "$pat"` where the helper already supplied `--` so the check searched for the
literal string `--`, and a telemetry `rc` assertion that no *passing* run could ever exercise.

**An empty input passes every check.** Before asserting anything about extracted data, assert that
you extracted some: a failed command substitution yields an empty string, a shell redirect creates
the file regardless, and a scanner then reports CLEAN against zero bytes. Size-check the artifact,
or guard the extraction with its own assertion, before trusting a verdict computed from it.

**Never expose the operator's machine to the network without asking.** A tunnel, port forward, or
remote bridge needs explicit permission each time — running the tests is not permission, and neither
is working on the feature that provides it. `SOP.md` §3b has the incident and the teardown rule that
goes with it.

### 7. Record only consequential bets

If a change is Costly, One-way door, or assumption-heavy, record the bet in `CHANGELOG.md` per
`PROJECT/PDDA.md`. Below that threshold, skip the ritual.

### 8. Stay quiet on trivial work

Most edits are small and reversible. Do not manufacture ceremony for a rename, typo fix, or other
local change.

## Repo-specific rails

- **This repo's purpose is to keep a long-horizon marathon under load — and that is a work-selection
  filter, not a slogan.** The harness is only proven by work long enough, parallel enough, and
  failure-prone enough to tax the whole system: worktree isolation, path claims, the driver lock,
  multi-round handoff, escalation, and resume. Short, single-shot tasks land fine but prove nothing.
  Four rules follow, and they are load-bearing:

  1. **Exactly one long-horizon marathon is in flight at a time.** When one lands, choosing the next
     is a real decision, not a default. It is named in the roadmap ledger's **Immediate next-up**
     (read `ROADMAP-DASHBOARD.md`; the RELEASES DB is the source of truth since the
     `ROADMAP_SOURCE=releases` flip) as the marathon, so an agent arriving cold can tell which item
     is the load and which items are riding alongside it.
  2. **Prefer the marathon-shaped candidate.** *Marathon-shaped* means: decomposable into many items
     with an identical transform, a per-item pass condition a machine can check, and a plausible way
     to break the harness. GH-10 (73 unaudited suites, one mechanical adoption each) is the
     archetype. Picking a non-marathon-shaped item over a marathon-shaped one of comparable value
     needs a stated reason — write it in the ledger entry, not in a commit message.
  3. **Only real work.** Never manufacture a marathon to keep the system busy, and never build a
     synthetic workload that cannot damage anything — a run with no blast radius does not surface
     the failures that matter. If nothing genuinely needed is marathon-shaped right now, **the
     correct state is idle**. Say so plainly and do the smaller work; an idle gap is honest signal,
     a fabricated marathon is noise that costs real tokens.
  4. **The point is the failures.** A marathon that completes cleanly and teaches nothing is a
     weaker result than one that escalates and names a defect. Report what broke; do not smooth it.

- **The RELEASES DB is two subsystems behind one CLI** (`utils/py/releases_app.py`): the GH-32
  release ledger and the roadmap ledger (`roadmap_items`). Since the `ROADMAP_SOURCE=releases`
  flip (GH-169/GH-238/GH-243) and ROADMAP.md retirement (GH-269), the DB is the roadmap's source of truth in THIS repo: park intake
  with `releases roadmap add` (or `hq park`), and read with `roadmap list` / `ROADMAP-DASHBOARD.md`.
  `roadmap sync` is for legacy-mode repos only and no-ops here — it mirrors markdown and would delete
  `add`-parked rows. Never hand-edit `releases.sql` or `releases.db`. Merge conflicts on the dump have
  a one-command resolver (`utils/releases-merge-resolve.sh`). The whole contract, including what a real
  merge conflict looks like: [RELEASES-DB-FAQS.md](RELEASES-DB-FAQS.md).

- **The local gate runs at the push boundary; hosted CI independently attests public-repo changes
  (GH-544, XYZ-forge #16).** The private-phase bridge ended when this repository became public on
  2026-08-15. `.github/workflows/ci.yml` now covers `push`/`pull_request` on `main` and `development`;
  the macOS promotion boundary remains restricted to a push on `main`, while the Ubuntu job is an
  advisory portability canary. Local commits are ungated on purpose; pushes are still gated by
  `githooks/pre-push` so failures are caught before the remote round trip.
  - Wire a new clone once: `bash githooks/install.sh` (idempotent). It installs a dispatch stub into
    `.git/hooks/`, which covers **every branch and linked worktree** of that clone, including branches
    with no `githooks/` directory (GH-549 — the first design wired `core.hooksPath` at the in-tree
    directory, and git skips a hook path that does not resolve *in total silence*). **The wiring is
    still per clone and does not travel** — a fresh clone or second machine has NO gate until this
    runs. Check with `bash githooks/install.sh --check`.
  - `./validate.sh` is **parallel by default** (~4–6 min at the GH-35 balanced width of cores/2 capped 4; `--burst`
  restores the old full-core width), auto-sized to the host, and announces a
    sequential fallback with its reason. `bash ci-local.sh` is still the qualifying run that writes
    the evidence record — it stays sequential and does not call `validate.sh`.
  - Bypasses are `git push --no-verify` and `XYZ_SKIP_PREPUSH=1`. Both announce themselves. Use them
    deliberately, not reflexively — they skip the local boundary even when hosted CI later runs.
    Draft-review publication (GH-487) is a legitimate bypass use and is NOT merge readiness: an
    operator-requested WIP draft may bypass only with current focused evidence for the changed area,
    the skipped-gate disclosure echoed into the PR description, and merge readiness still
    outstanding — a bypassed push never authorises merge, promotion, or teardown.
  - **PR checks are meaningful again only after a hosted run actually appears for the commit.** A
    configured workflow is not evidence; query the run and cite its SHA.

- **Never use a git command that overwrites the working tree from a committed state to undo a
  working-tree experiment.** In this clone other agents hold uncommitted work you cannot see.
  Three spellings destroyed peer work three times in one session (GH-527) and the common factor
  is not obvious from any one of them:
  - `git reset --hard <anything>`
  - `git checkout -- <path>` (restores **HEAD**, not the state before your edit)
  - tree-wide `git stash` (and it may time out before its `pop`)

  To undo your own experiment, copy the file first (`cp f f.bak`) and restore from that. The
  blast radius is **tracked** modifications; untracked files survive. `relay-automation/hooks/gh527-destructive-git-guard.sh`
  snapshots the doomed tracked files into `.tick/orphan-backups/` before the command runs, so
  this is recoverable rather than prevented — the snapshot is a net, not permission to swing.
- **Preflight sandboxed branch mutations (GH-50).** A sandbox may let `git switch --track` rewrite
  the index and working tree, then deny the `.git/config` lock and leave HEAD on the old branch.
  Before a harness runs a tracking switch or destructive branch mutation such as `git branch -D`,
  wrap the complete command with `utils/git-sandbox-guard.sh --repo <root> -- <git command>` so it
  refuses before mutation when the config cannot be written. Never truncate git stderr for branch
  operations: the decisive `could not lock config file` line can otherwise disappear behind an
  unrelated upstream hint.
- `ROUTER.md` owns startup order, canonical files, command rails, and the issue-first SOP.
- `GUIDING-PRINCIPLES.md` owns the product/runtime priorities: local event-log coordination,
  containment, skill-first relay work, durable fixes, and verified done.
- `PROJECT/PDDA.md` owns doc lifecycle, roadmap pointer-ledger rules, and `CHANGELOG.md`
  governance.
- Before approving a PDDA dependency sync, follow the repo-owned
  [PDDA sync review policy](PROJECT/PDDA-SYNC-POLICY.md); a green suite after fixups does not by
  itself establish that deleted local behaviour was safe to remove.
- `validate.sh` is the code/runtime gate. `utils/pdda/pdda.sh run` and its targeted
  `utils/pdda/pdda.sh <check>` subcommands are the doc-hygiene gates.
- **Scratch and temporary files go in `temp/`, never the repo root.** `/temp/` is already gitignored
  (`.gitignore:13`). Probes, reproduction scripts, one-off analysis, captured command output,
  half-written notes — anything you would not put in a commit — belongs there or outside the repo
  entirely. **Do not create `scratch-*.md`, `notes-*.md`, `*.tmp` or similar at the repo root.**

  This is a housekeeping rule with a real failure mode behind it, which is why it is a rail and not a
  preference. Root-level scratch is *untracked*, so it survives branch switches, rebases and
  worktree teardown; it accumulates silently across sessions until nobody can say which agent or
  which lane produced it, or whether it is safe to delete. It also puts unreviewed prose one
  `git add -A` away from a commit — and `marathon-closeout.sh` has already swept 20 unrelated files
  into a lane's PR once (2026-08-10), which is exactly this hazard firing.

  A file that turns out to be worth keeping gets *promoted* deliberately — into `PROJECT/1-INBOX/`
  as a capture doc, into `test/baselines/` as recorded evidence, or into the CHANGELOG — rather than
  being left at the root in the hope that someone later works out what it was.
- **Frozen Bash twins (GH-308).** Python in `utils/py/` is authoritative for the twelve Tier-A
  entry points (`agy-turn`, `aider-turn`, `claude-turn`, `codex-turn`, `pi-turn`, `poll`,
  `relay-loop`, `relay-drive`, `consult`, `marathon-drive`, `marathon-plan`, and
  `swarm-preflight`). Their `.sh`
  files are historical `XYZ_PYTHON=0` fallbacks: put behavior fixes in the named Python twin, not
  the Bash body. Before committing, run `bash test/gh308-frozen-twin-guard.sh --check --staged`; the
  `Frozen Bash twin guard (GH-308)` step in `.github/workflows/ci.yml` runs the same guard with
  `--base <PR base> --allow-exceptions` on every PR to reject a committed twin edit. **Escape
  hatch:** a safety defect in a fallback can warrant an edit anyway — GH-319 left a silently-fake
  pre-advance gate in `marathon-drive.sh` under `XYZ_PYTHON=0`. Such a commit must carry a trailer
  that **names the twin it covers**, with an em-dash before the reason:

  ```
  Frozen-twin-exception: relay-automation/marathon-drive.sh — silently-fake pre-advance gate (GH-319)
  ```

  **Per file, not per PR (GH-321).** Every frozen twin changed in the range must be named by some
  trailer in that range; one exception no longer excuses a different, undeclared edit riding along
  on the same branch — the common case on a multi-lane marathon PR. A trailer naming a path that is
  not a frozen twin fails loudly rather than silently covering nothing, and the bare
  `Frozen-twin-exception: <reason>` form (no path) no longer covers anything. Comma-separate to cover
  several twins with one reason. No trailer, no edit.

  **`utils/marathon-plan.sh` is no longer the exception (GH-362).** It was, while its Python "port"
  shelled out to a copied node engine with documented gaps; GH-340 deleted that copy and made the
  Python lane native, so the exception outlived its reason and marathon-plan is now the **12th frozen
  twin**. `relay-turn-lib.sh` remains a shared Bash runtime dependency rather than a twin, and is the
  only non-frozen file left in the Tier-A surface.

  **No new Bash either (GH-551).** New executables are Python in `utils/py/`; the same guard rejects
  a **new** `.sh` file added under `utils/` or `relay-automation/` unless a
  `New-bash-exception: <path> — <reason>` trailer names it (per file, like GH-321). `test/`, git
  hooks, and existing shims are out of scope.

  **Two edits the guard permits without a trailer, both narrow (GH-362).** A commit that *introduces*
  a path's `FROZEN` banner establishes the freeze for that path and is not a violation of it — a range
  reaching back before the freeze (a release merge, a bisect, an old fork base) contains exactly that
  commit. The exemption covers the establishing edit only; anything touching the path *after* it in
  the same range still needs a trailer. Relatedly, the pre-GH-321 pathless trailer is tolerated **only**
  inside such a commit, because it is permanently in git history and cannot be rewritten — a new
  pathless trailer is still rejected everywhere.
- **Builder/orchestrator role split (GH-221)** — **Claude Code (terminal and VS Code agents) is the
  orchestrator and reviewer, never a default builder.** It plans, dispatches marathon/relay lanes, and
  reviews/verifies their output; it does not drive itself headlessly as a build lane. **Agy CLI and
  Codex CLI are the builders** — the two cost-blind (subscription-billed) headless build lanes
  `marathon.sh`/`marathon-drive.sh` default to (GH-212). **Claude CLI (billed via the Anthropic API) is
  NOT a builder by default** — `--builder claude` stays fully supported, but only as an explicit,
  cost-acknowledged choice the *user* makes locally (their own `--builder claude` flag or a local
  settings override), never something a session reaches for on its own reasoning that it's "just
  another supported builder option." If a task calls for a headless build lane and neither agy nor
  codex is available, stop and ask — don't default to spawning a headless Claude CLI turn.

  **As the orchestrator, you are the final outer reviewer of any emitted artifact (e.g., an automated PR).**
  You must treat an automation's emission as an event requiring inspection, not as an automatic success.
  Before permitting an automated loop to proceed to its next iteration, you must query and verify the emitted PR:
  1. **Base Branch Sanity:** The PR targets the active WIP branch (`development`), not `main`.
  2. **Diff Size Sanity:** The diff size matches the logical scope of the fix (e.g. < 500 lines for targeted bugs).
  3. **Verification Status:** A test gate ran against the final committed state (either CI or a local `validate.sh` run).
  **Halt Condition:** If an emitted artifact fails any of these predicates, you must suspend the automation loop immediately.
- **HQ (multi-repo command center)** — for cross-repo tasking (resolve a project → land intake on its
  own PDDA rails → prepare dispatch), drive `utils/hq/hq.sh` via the `/hq` skill rather than hand-editing
  another repo's docs. Full command surface (`status`/`resolve`/`next`/`park`/`promote`/`queue`/`fire`),
  install, and the resolution ladder and agent-facing invocation flow + guardrails are in [skills/hq/SKILL.md](skills/hq/SKILL.md). Write paths preview by default; `fire` never drives the harness.
- Changes to `.tick/events/`, `src/project.js`, relay containment, or event/verb shape are usually
  broader than they look. Treat them as at least Costly until proven otherwise.
- **Contain tree-touching subagents with `isolation: "worktree"` (GH-177/GH-233).** A Claude Code
  session spawning Agent/Workflow subagents that will *modify files* in this repo should pass
  `isolation: "worktree"` so a runaway destructive command shreds a disposable checkout, not the main
  tree (this repo has been wiped twice — see
  `PROJECT/3-COMPLETED/GH-177-MKTEMP-TRAP-REPO-WIPE.md`). Know what it does NOT protect: worktrees
  share `.git` objects/refs, so destructive *git* operations (`update-ref`, `branch -D`, resets,
  force-push) still hit the real repo — a worktree-isolated agent once reset ROOT HEAD via
  `rtl_enforce`'s commit-bypass guard. Harness-driven codex/agy lanes are covered by
  `rtl_worktree_begin` instead and don't need the flag. Known frictions: `--require-clean` self-trips
  on the driver's own lock dir inside a linked worktree, and untracked artifacts are invisible to a
  worktree checkout — commit review inputs first. Read-only subagents (Explore, audits) don't need
  isolation. Related guards: never execute `validate.sh`/`test/*.sh` under a sandboxed Bash call
  (enforced by `relay-automation/hooks/gh177-sandbox-test-guard.sh` — re-run it un-sandboxed; do NOT
  push it to CI to be exercised, see the CI rail below), and `test/mktemp-trap-guard.sh` statically
  outlaws the wipe idiom repo-wide. **The "what it does NOT protect" list above is narrower than
  reality — see the next rail (GH-564): a worktree isolates the working tree only, and everything
  under `.git` is shared, which is why running the suite in one contaminated the parent clone twice.**
- **Run the suite in a SEPARATE FULL CLONE, never in a clone whose state you care about — and a
  linked worktree is NOT a way around it (GH-564).** `validate.sh` and `test/*.sh` can write to the
  git config, remotes, and refs of the repository they are invoked from. On 2026-08-15 the primary
  clone was contaminated **twice in one morning**: `core.bare=true`, `remote.origin.url` repointed at
  a fixture bare repo, a fixture `[user]` identity appended, and `refs/heads/development` reset onto
  ~35 fixture commits. It also **defeated the push gate while corrupting it** — pushes failed with
  `'/var/folders/…/bare.XXXXXX' does not appear to be a git repository` because the suite repointed
  `origin` mid-hook.
  - **The worktree precaution was taken and it FAILED.** Both bursts came from `./validate.sh` run in
    linked worktrees cut off the primary clone, chosen specifically to isolate the risk. **Linked
    worktrees share `.git/config` with the parent clone**, so an escape landing in a worktree's CWD
    writes the parent's config. Reproduced deterministically: from a worktree CWD, `r=""; git -C "$r"
    remote set-url origin "$b"` rewrote the *parent* clone's origin. Same structural fact the
    driver-lock matrix documents from the other side (GH-42/GH-354/GH-448) — a linked worktree
    resolves to the parent's `git-common-dir`, which is why it grants no second lane either.
  - **State the boundary precisely, because the previous rail's version was too narrow.** The rail
    above says worktree isolation does not protect against destructive *git operations*. That is
    true and insufficient: a worktree isolates the **working tree only**. Everything reached through
    `.git` — config, remotes, refs, objects, hooks — is shared with the parent clone, whether it is
    touched deliberately or by an escaped fixture. Only a **separate full clone** isolates any of it.
  - **Why it escapes at all:** `git -C ""` is documented to leave the working directory unchanged and
    `cd ""` is a bash no-op, and these suites run without `set -e` — so one unguarded
    `r="$(mktemp -d …)"` silently redirects every "fixture" operation onto the caller's clone. It
    fires under **parallel** load (the failure mode of `mktemp`), which is why a serial re-run of the
    same suite reproduces nothing and must not be read as an all-clear. GH-177 family.
  - **Until #564's suite-wide invariant gate lands**, treat any clone you ran the suite in as
    suspect: check `git config --get core.bare`, `git remote -v`, `git config --local --get user.email`,
    and `git log --oneline -1` before trusting a push, a fetch, or a green run from it. A guarded
    fixture helper (`require_fixture`: the path must exist AND live under `$WORK` — containment, not
    a null check) is the pattern to copy; `test/gh544-pre-push-gate.sh` has it, 31 other suites do
    not.
  - **Validate a sandbox path at the USE boundary, not where it was created (GH-567).** An empty
    variable does not fail — `git -C ""` uses the current directory, `cd ""` is a no-op,
    `rm -rf "$VAR/"` becomes `/`, `find "$VAR" -delete` becomes `.`. So guard immediately before the
    first dangerous use **in every function that receives the path**, not once at the `mktemp` that
    derived it: a variable that was safe at line 10 can be empty at line 50, and a derivation-site
    check never covers a path passed in from elsewhere. Assert non-empty, a **resolved** descendant
    of the sandbox root, and the expected type — `require_fixture`'s current `case "$p" in "$WORK"/*)`
    is lexical and still accepts `$WORK/../../<real repo>`, so harden it before copying it into the
    other 31. `set -e` is not the containment proof; these suites deliberately run without it.
  - **A clone whose identity changed under a run cannot attribute that run (GH-567).** If a suite
    fails only under parallel load, compare `core.bare`, `git remote -v`, the local user identity and
    `HEAD` against their pre-run values **before** blaming your diff. Unexpected drift invalidates
    every result from that clone — re-clone, then run candidate and base at the same width. Identity
    intact means it is your diff or ordinary flakiness: investigate normally. This is a trigger, not a
    licence to write failures off as harness noise; the 2026-08-15 incident cost several full-suite
    runs to a single green control run treated as proof, which is one sample from a nondeterministic
    process.
  - **An audit that recognizes only one invocation shape stops covering the same operation reached a
    different way (GH-195).** `marathon-root-audit.sh` exists (GH-401) specifically to catch an
    unscoped marathon-drive invocation writing into the real clone instead of a fixture — but its
    detector only matches `bash <driver>.sh`. A test that calls `python3 marathon_drive.py` directly
    is invisible to it. That exact gap let `test/gh115-round-cap.sh` commit a live transcript onto
    whichever real clone was running `validate.sh`, every single run, reproduced across 4 separate
    clones including a brand-new one. **If you add or harden an audit that matches on invocation
    text, ask what it does NOT match, not just what it does.** Diagnosing this cost ~2.5h chasing
    plausible-but-wrong external causes (a leftover process, a second concurrent agent, a scheduled
    job) before a one-shot stack-trace at the actual write call site named the real culprit in one
    run — when a repeatable artifact exists (here: the per-clone `.tick/attempts/<phase>` fire
    ledger, timestamp-correlated to each gate run), inspect it directly before building a
    process-hunting hypothesis chain. Full writeup:
    [GH-195-MARATHON-ROOT-AUDIT-BLIND-SPOT.md](PROJECT/3-COMPLETED/GH-195-MARATHON-ROOT-AUDIT-BLIND-SPOT.md).
- **The local macOS run is the gate; hosted ubuntu is advisory (GH-509).** XYZ is a developer toolkit
  for **macOS**; Linux and Windows are on the roadmap and not here yet. So `./validate.sh` (or
  `./ci-local.sh`) on your Mac is the highest-fidelity evidence available — it is the shipping
  platform with the real toolchain — and it runs a **superset** of the hosted job, including
  `registry-lock-concurrency.sh`, which CI skips for a contended-Linux flake. The hosted `canary-ubuntu`
  job is `continue-on-error: true`: its red means *portability drift*, not breakage, and must not be
  reported as a broken commit. Two consequences that bite: **never defer a test run to CI** — CI is
  advisory and tests the wrong OS; and **a green local run is self-reported**, so it does not qualify a
  promotion. Promotion needs a hosted **macOS** run for that exact commit. When a claim really is about
  Linux, the canary is the right instrument and its red is authoritative.
- **Commit to the QUEUE; re-anchor, don't rabbit-hole (GH-45).** A wave's committed lane list *is* the
  active commitment — after each lane attempt, re-read it before acting further. A driven lane that
  fails **parks** after `LANE_MAX_ATTEMPTS` (default 2): the driver (`marathon-drive.sh` /
  `relay-drive.sh`) refuses to re-fire it (exit 8, no token), you capture the findings as an issue and
  stop. Re-firing a parked lane or going off-wave to deep-dive one item requires an explicit operator
  override (`--force`) or a replan note — never a quiet slide off the plan.
- **Do not create new git branches** automatically. Only create a new branch if explicitly requested by the user. **This governs interactive work only — it is NOT a licence to commit a marathon onto `development`.** The very next bullet is the carve-out: a marathon/relay-fired lane cuts its own `marathon/gh-<n>-*` branch and PRs back into `development`, and that per-lane branch IS the explicitly-requested case. Read 2026-08-15 as permission to skip the branch, which is how four Meter commits landed straight on `development` with no PR (GH-561). The guard now refuses that (`marathon_drive.py`'s branch guard protects `development`, not just `origin/HEAD`), because a rule an agent can talk itself past is not a rule.
- **`development` is the standing WIP branch — ALL work targets it, including marathon/relay-fired lanes (cut fresh from `main` 2026-07-17, [GH-216](https://github.com/Claude-AI-Tools-Ventura-County/xyz-3-agents-swarm/issues/216); policy widened 2026-07-17 to cover marathon lanes too, first applied to [PR #217](https://github.com/Claude-AI-Tools-Ventura-County/xyz-3-agents-swarm/pull/217)).** The prior `development` had drifted 295 commits behind `main` with no open PRs — retired to `development-archived-2026-07-04` rather than deleted outright. Both manual/exploratory work AND marathon-fired lanes (`marathon/gh-<n>-*` branches, GH-212 convention) now branch off `development` and PR back into it — `--plan`/`marathon.sh` still cuts its own short-lived per-lane branch, just off `development` instead of `main`. Periodically merge `development` → `main` once it's in a shippable state; don't let `main` sit behind `development` indefinitely. Watch for `development` drifting stale again the same way the old one did; re-cut from `main` if it does.
- **Anti-pattern: renaming a branch with an open PR via GitHub's branch-rename API
  (`POST /repos/{owner}/{repo}/branches/{branch}/rename`, or `gh api ... branches/<old>/rename`).**
  It does **not** rename in place — it deletes the old ref and recreates a new one, which GitHub
  treats as `head_ref_deleted` and **auto-closes the open PR** pointed at that branch (found
  2026-07-10 renaming a branch backing PR #193; recovered by opening a new PR from the renamed
  branch and pointer-commenting the closed one). If a branch needs a new name and has an open PR:
  either rename it *before* opening the PR, or accept that renaming after will require re-opening a
  fresh PR — don't assume the PR follows the rename.
- **Aider Configuration (AIDER.md / GH-77)**: When using Aider as a headless runner against OpenRouter, do not hardcode the API key or attempt to use a secrets manager. The `OPENROUTER_API_KEY` is securely stored at `~/secrets/openrouter/openrouter.txt` and is exported dynamically by `~/.zshrc`.
- **Aider edit-format compat for OpenRouter models (GH-118)**: many OpenRouter-proxied models
  (confirmed: GLM-5.2, Nemotron Ultra 3) default to Aider's `whole` edit format and fail to emit
  parseable edits, stalling the turn. Fix is `AIDER_FLAGS=--edit-format diff` (existing passthrough
  in `aider-turn.sh`) — see `relay-automation/README.md`'s "Known OpenRouter edit-format quirks"
  section before adding a new OpenRouter model to a driven lane.
- **Resolving an OpenRouter model name before setting `AIDER_MODEL` (GH-120)**: don't probe
  `aider --list-models` or curl `openrouter.ai/api/v1/models` by hand — run
  `relay-automation/resolve-model-alias.sh "<colloquial name>"` first (local alias table, no live
  query) or use the `/open-router` skill. Only fall back to the live catalog on a miss. **Do not
  append the resolved slug to `relay-automation/openrouter-model-aliases.yml` — it is a generated
  file (GH-450)** rendered from the vendored HiQS-Labs/Model-catalog copy, and a hand-added line
  fails `test/gh450-model-catalog-pin.sh`. Add the row upstream in Model-catalog, then land a sync
  PR here (`utils/py/model_catalog.py pin` / `render` / `check`); the exact two-PR recipe is in
  `relay-automation/README.md` → "Adding a new model alias".

## Conflict order

1. The current user request
2. The canonical doc that owns the surface you are touching (`ROUTER.md`, `GUIDING-PRINCIPLES.md`,
   `PROJECT/PDDA.md`, or the active `PROJECT/**` doc)
3. This file
4. Skill defaults
