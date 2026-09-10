# GH-496 PR 2 — Gate Provenance & Test Results Summary

Branch: `feat/gh496-phase2-views`
Target Commit: `cb06de33`
Qualification Environment: Disposable full clone `~/marathon-clones/xyz-gh496-gate-pr2` (un-sandboxed, independent `.git`)
Gate: `./validate.sh` (368+ parallel test suites + pytest layer + clone invariants)

## Gate Results Summary

| Suite / Check | Result | Detail |
|---|---|---|
| `test/gh496-phase2-reconciliation-views.sh` | 29 / 29 PASS | Single reconciler in-flight check, GITHUB_ACTIONS enforcement, pre-merge checks, active-doc content fingerprinting, stale receipt rejection, fail-closed PR metadata queries |
| `test/gh421-auto-wave-reconcile.sh` | 17 / 17 PASS | Catch-up, lifecycle, second apply idempotency, rollback boundaries |
| `test/wave-reconcile.sh` | 16 / 16 PASS | Core wave reconciliation suite, promotion, archive formatting |
| `test/gh202-wave-reconcile-issue-state.sh` | 40 / 40 PASS | Closing keyword parsing, mention handling, live/offline state drift |
| `test/gh280-jog-marathon-adapter.sh` | 217 / 217 PASS | Jog queue status updates, marathon execution, dashboard generation sync |
| `test/gh257-roadmap-ledger-fixes.sh` | ALL PASS | Ledger generation updates, dashboard staleness guard compatibility |
| `test/ci-route.sh` | 63 / 63 PASS | Fast routing, pdda subsystem suite coverage |
| `test/gh204-sed-portability.sh` | ALL PASS | BSD/GNU sed portability audits |
| `utils/pdda/pdda.sh run` | errors=0 | Full doc-hygiene and governance gate |
| `test/gh308-frozen-twin-guard.sh` | PASS | Zero frozen twin edits, zero new Bash scripts |
| `Codex Final QA Consult` | PASSED | Independent QA completed (`relay-system/2026-09-10/gh496-pr2-final-qa-100915`); all blocker & should recommendations resolved |
| Full `./validate.sh` | **ALL PASS** | All suites passed; 0 failed |
| `clone-identity-invariant` | PASS | `core.bare=false`, `origin` intact, `HEAD` unchanged |

## Phase 2 Governance & Invariant Attestation

1. **Single Reconciliation Owner**: Hosted `wave-reconcile.yml` is the sole default landing writer on `development`. Local reconciliation fails closed (exit 8) if a hosted run is queued or in-progress. `--force-local-reconcile` provides local override and is hard-rejected inside `GITHUB_ACTIONS=true` (exit 2).
2. **View Decoupling & Generation Stamping**: Routine task branches do not commit `ROADMAP-DASHBOARD.md` or `LEADERBOARD.md`. Line 1 embeds `<!-- releases-app generation: <N> -->`. Staleness guard enforces that view commits only accompany changes to renderers or run within `GITHUB_ACTIONS=true`.
3. **Deterministic Pre-Merge Closeout Checks**: Read-only `wave_reconcile.py --pre-merge` verifies closing active doc frontmatter (owner, status), substantive `## Lessons Learned` (exit 5), and committed test receipts in the git tree at HEAD (exit 6). Stale receipts where code changed after qualification are strictly rejected.
4. **Marathon Plan Fingerprinting**: `wave_reconcile.py` skips redundant `marathon-plan.sh` runs when canonical inputs match `.tick/marathon-plan.fingerprint`. Active doc contents are hashed into the fingerprint, generated plan files are excluded from input hashing, and the fingerprint artifact is tracked in `RollbackJournal`.
