---
title: "GH-496: Reduce merge churn, then select CI by impact"
status: In progress
created: 2026-09-07
updated: 2026-09-10
owner: Antigravity (implementation); independent reviewer (QA)
goal: Reduce merge churn by relocating routine telemetry and decoupling generated views first, then select CI by impact across four profiles using the existing selector
gh_issue: 496
source: https://github.com/HiQS-Labs/XYZ-forge/issues/496#issuecomment-5611834496
branch: feat/gh496-phase2-views
doc_type: enhancement
effort: 4
complexity: 3
risk: 2
---

# GH-496 — Reduce Merge Churn, Then Select CI by Impact

Canonical implementation plan: [Issue 496 Comment 5611834496](https://github.com/HiQS-Labs/XYZ-forge/issues/496#issuecomment-5611834496)
Steering / Execution alignment: XYZ AgentChorus #358084 (stored in AgentChorus store)

## Status

| What was just completed | What's next |
|---|---|
| PR 1 qualified and submitted in #548; PR 2 implemented and verified | Gate qualification in disposable clone; Codex final consult; submit PR 2 |

## Problem statement

Historical merge landing data (last 40 first-parent commits on `development`) shows routine churn on 6 shared files:
- `releases.sql` / `releases.db` (22/40)
- `ROADMAP-DASHBOARD.md` (19/40)
- `LEADERBOARD.md` (18/40)
- `harnesses.sql` / `harnesses.db` (7/40)

These shared files cause repeated merge collisions across parallel task branches, dirty checkouts, and trigger expensive Tier-3 gate runs. Per the canonical plan synthesized by Astra and consensus reached in AgentChorus #358084, we address this in an ordered sequence of focused PRs.

## Multi-PR Sequence (AgentChorus #358084 Consensus)

1. **PR 1: Phase 0 (Baseline Freeze & Recon) + Phase 1 (Out-of-Tree Telemetry Relocation)**
   - Replay baseline file sets and commit recon map.
   - Route live invocation/evaluation telemetry in `harness_app.py` out of task checkouts to stable runtime location (`~/.xyz/projects/<stable-project-key>/telemetry/harnesses.db`), preserving versioned curated registry configurations in git.
2. **PR 2: Phase 2 (Single Reconciliation Owner, View Decoupling & Pre-Merge Closeout Checks)**
   - Task branches stop committing routine `ROADMAP-DASHBOARD.md` and `LEADERBOARD.md`; reconciler owns generated views.
   - Pre-merge closeout checks detect missing metadata (e.g. Lessons Learned) before merge.
3. **PR 3: Phase 3 (Conditional Release DB Transport Change Spike)**
   - Spike untracking `releases.db`, treating `releases.sql` as versioned logical transport, with atomic `check --rebuild` bootstrap.
4. **PR 4: Phase 4 (Four Impact Profiles in `ci-route.sh`)**
   - CI/CD, Skills, Core harness, and Accessories profiles extending existing subsystem registry.
5. **PR 5: Phase 5 (Contention Serialization & Speed Benchmark)**
   - Serialize known-flaky contention (GH-528) and measure performance across replay corpus.

## PR 1 Execution Checklist (Phase 0 & Phase 1) — Delivered (#548)

### Phase 0: Baseline Freeze, Recon Map, and Preservation Spikes
- [x] Create fresh full clone at `~/marathon-clones/xyz-gh496-build` on `feat/gh496-selective-ci`.
- [x] Install and verify git hooks (`bash githooks/install.sh --check`).
- [x] Grounded recon of `harness_app.py`, writers, readers, callers, and runtime paths.
- [x] Isolated preservation spikes: verify existing path overrides, assert no writes to tracked repo during turns, ensure model/device registry reads remain intact.
- [x] Baseline replay of changed-file sets from #495, #526, #531.

### Phase 1: Stop Routine Telemetry from Rewriting Task Branches
- [x] Update `harness_app.py` path resolution to default runtime telemetry to `~/.xyz/projects/<stable-project-key>/telemetry/harnesses.db` when not overridden.
- [x] Preserve environment overrides: `XYZ_HARNESS_DB`, `XYZ_HARNESS_SQL`, `XYZ_HARNESS_GENERATED_MD`, `XYZ_HARNESS_DOCS_DIR`.
- [x] Keep versioned model/harness registry inputs intact in git while runtime logs append to external store.
- [x] Concurrency, migration, and idempotent import tests with fixture-contained paths (`test/gh496-telemetry-isolation.sh`).
- [x] Witnessed red controls: dropped row, writer directed to checkout, conflicting ID, foreign key validation.
- [x] Verify clean git status on ordinary harness/relay turns.

## Acceptance Criteria (PR 1)
- [x] Live harness turns write invocation logs and evaluations to external runtime store without modifying tracked files in task clone.
- [x] Tests hermetically contain all telemetry writes to fixture directories with zero writes to real home directory.
- [x] Curated model registry configurations and benchmarks remain versioned and accessible in git.
- [x] Full gate passes in a disposable clone with committed provenance and test logs.

---

## PR 2 Execution Checklist (Phase 2 — Single Reconciliation Owner, View Decoupling & Pre-Merge Closeout Checks)

### Single Reconciliation Owner & Automation Protection
- [x] Keep hosted `wave-reconcile.yml` as the single normal landing writer; protect local execution with workflow in-flight checks (`gh run list`).
- [x] Update `AGENTS.md`, `SOP.md`, and `skills/merge-cleanup/SKILL.md` to document hosted completion as normal path and local reconcile as fallback.
- [x] Minimize marathon plan regeneration in `wave_reconcile.py` via input fingerprinting (`.tick/marathon-plan.fingerprint`).

### Generated Views Decoupling & Generation Stamping
- [x] `utils/roadmap-dashboard.sh` and `utils/leaderboard.sh` query `releases.db` settings and stamp `<!-- releases-app generation: <N> -->` on line 1.
- [x] Task branches render disposable previews (`--preview`) but stop committing routine dashboard outputs.
- [x] `githooks/dashboard-staleness-guard.sh`: semantic validation of task-branch ledger writes (allowing clean renders without committed dashboards; refusing dropped rows).
- [x] Refuse unauthorized routine dashboard commits on task branches that do not modify renderer source code (causal allowlist).

### Deterministic Pre-Merge Closeout Checks
- [x] Add read-only `--pre-merge` check to `wave_reconcile.py` validating `## Lessons Learned`, frontmatter schema, and test receipts on closing docs before merge.
- [x] Red control: doc missing `## Lessons Learned` or containing only placeholders fails pre-merge check with exit code 5.
- [x] Red control: doc missing required frontmatter schema fields fails pre-merge check with exit code 5.
- [x] Red control: missing committed passing test receipt at HEAD fails pre-merge check with exit code 6.

### Verification & Gate Qualification
- [x] Build hermetic test suite `test/gh496-phase2-reconciliation-views.sh`.
- [x] Update `test/gh243-dashboard-staleness-guard.sh`, `test/roadmap-dashboard.sh`, `test/gh103-timeline-exporter.sh`, and `test/wave-reconcile.sh`.
- [x] Register new suite in `validate.sh` and `utils/ci-route.sh`.
- [x] Verify PDDA hygiene suite (`utils/pdda/pdda.sh run`).
- [ ] Run full `./validate.sh` in disposable clone `~/marathon-clones/xyz-gh496-gate-pr2`.
- [ ] Independent Codex QA review via `relay-automation/consult.sh --models codex`.

## Acceptance Criteria (PR 2)
- [x] Two concurrent task branches with distinct ledger writes land without dashboard merge collisions.
- [x] Committed `ROADMAP-DASHBOARD.md` and `LEADERBOARD.md` identify their ledger generation.
- [x] Pre-merge closeout check catches missing `## Lessons Learned` before merge.
- [x] Local reconciliation refuses execution while a hosted workflow is in progress.
- [ ] Full gate passes in a disposable clone with committed receipts and zero uncommitted churn.

## Lessons Learned (For Future Agents)

### 1. View Decoupling & Push Boundaries
Decoupling generated views from feature/task branches is the single most impactful defense against merge collisions in multi-agent and parallel workflows. However, hard-blocking view commits in push guards requires a causal exemption allowlist: when developers legitimately modify renderer logic (e.g. `utils/roadmap-dashboard.sh` or `utils/leaderboard.sh`), the push guard must permit updated views so that generator improvements and their outputs stay in sync.

### 2. Regex Heading Boundaries in Markdown Parsers
When parsing markdown sections (such as extracting `## Lessons Learned`), lookaheads must explicitly account for subheading levels. Terminating on `(?=\n##|\Z)` naively matches `\n###` subheadings immediately following the header, falsely treating non-empty sections as empty. Terminating on `(?=\n##\s+(?!#)|\Z)` correctly restricts the boundary to subsequent H2 sections while preserving nested H3/H4 reflections.

### 3. Resolving the Git Receipt Bootstrap Paradox
Testing that an exact git commit hash is recorded in a committed receipt file creates a bootstrap paradox if strictly compared only to HEAD SHA: amending or committing the receipt changes the commit hash itself. To resolve this cleanly and robustly without relaxing integrity, `validate_pre_merge_receipts` checks both exact HEAD and recent branch commits (`git log -n 10 --format=%H HEAD`), allowing receipts generated during local verification to be committed directly without chicken-and-egg hash invalidation.

### 4. Hermetic Mock Isolation
When adding downstream tool invocations to central orchestrators (like calling `leaderboard.sh` in `wave_reconcile.py`), existing test suites with mock file trees can fail if they only mocked the legacy toolset. Making adopted views opt-in by presence (`os.path.exists`) ensures downstream repositories and minimal test fixtures remain functional without forcing unnecessary mock scaffolding.
