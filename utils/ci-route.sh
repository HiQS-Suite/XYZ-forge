#!/usr/bin/env bash
# Classify a CI invocation as docs-only, fast, or full — and, since GH-35, answer a second,
# deliberately separate question: which local test-selection TIER the change belongs to.
# Pull-request paths are read from stdin.
#
#   route=docs|fast|full  — the CI job shape (GH-509 semantics, unchanged)
#   tier=1|2|3            — the local gate selection (GH-35): 1 docs, 2 subsystem, 3 full
#
# The two answers are kept separate on purpose (GH-35 review guardrail): test selection is
# deterministic policy owned by this registry; resource policy (worker count, nice) is
# validate.sh's business and never changes WHICH tests run. The tier fails closed — unknown
# paths, any test/* change, and every kernel/containment/gate surface are tier 3.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── GH-35 Tier-2 subsystem registry ──────────────────────────────────────────────────────────────
# The ONE mapping from changed paths to the focused suites that cover them, consumed by
# githooks/pre-push and validate.sh (--tier 2 / --subsystem). Extending it is a deliberate
# three-part act: name the subsystem in SUBSYSTEMS, add its path patterns to subsystem_of(),
# and list its suites in SUBSYSTEM_TESTS_<name>. Every listed suite must exist in test/ AND
# be registered in validate.sh's TESTS array — test/gh35-test-tiers.sh enforces both, because
# a registry naming a suite that never runs is a green lie (the releases-skill lesson).
SUBSYSTEMS="hq releases telemetry ate swe-diagram pdda agent-chorus standup skills-army-hq"
SUBSYSTEM_TESTS_hq="hq.sh hq-park.sh hq-park-synthesis.sh hq-dispatch.sh hq-next.sh hq-locator.sh hq-hardening.sh hq-promote.sh hq-marathon-scan.sh hq-rollup.sh hq-marathon-live.sh roadmap-dashboard.sh gh238-hq-releases-mode.sh gh239-hq-status-releases-mode.sh"
SUBSYSTEM_TESTS_releases="gh32-releases-app.sh gh103-timeline-exporter.sh gh32-releases-artifacts.sh gh53-releases-merge-resolve.sh gh54-merged-dump-refusals.sh gh57-live-merge-resolve.sh gh69-roadmap-shadow.sh gh32-release-target-advisory.sh gh39-releases-project-sync.sh gh153-releases-sidebar-rollup.sh releases-skill.sh gh284-p3-release-milestone.sh gh284-p4-release-lanes.sh litmus-release.sh nightwatch-release.sh meter-release.sh ballast-release.sh gh57-releases-fuzz.sh roadmap-dashboard.sh gh257-roadmap-ledger-fixes.sh gh269-roadmap-retired.sh"
SUBSYSTEM_TESTS_telemetry="xyz-completion.sh gh358-lock-instrumentation.sh archive-telemetry.sh gh496-telemetry-isolation.sh"
SUBSYSTEM_TESTS_ate="ate-run-variations.sh gh298-ate-gen4-ci-smoke.sh gh-gen4-phase1-domain-oracles.sh gh-gen4-phase2-adaptive-ate.sh gh-gen4-phase3-fuzz-engine.sh gh-gen4-phase4-repro-synth.sh gh-gen4-phase5-campaign.sh gh478-runaway-guard.sh"
SUBSYSTEM_TESTS_swe_diagram="swe-diagram.sh"
SUBSYSTEM_TESTS_pdda="pdda-roadmap-coverage.sh pdda-repo-contract.sh pdda-local-checks.sh gh400-acceptance-fidelity.sh gh400-source-url.sh gh422-backfill-source-url.sh gh425-source-url-slug.sh wave-reconcile.sh gh202-wave-reconcile-issue-state.sh gh232-wave-reconcile-multiphase.sh gh358-wave-reconcile-vendored-paths.sh gh496-phase2-reconciliation-views.sh"
SUBSYSTEM_TESTS_agent_chorus="agent-chorus.sh"
SUBSYSTEM_TESTS_standup="gh77-standup-triage.sh"
SUBSYSTEM_TESTS_skills_army_hq="skills-army-hq.sh"

subsystem_of() {  # <path> -> subsystem name, or nothing when unmapped
  case "$1" in
    utils/hq/*|skills/hq/*)                                                                printf '%s\n' hq ;;
    utils/py/releases_app.py|skills/releases/*|utils/release-lanes.sh|releases.sql|releases.db|utils/releases-merge-resolve.sh|utils/leaderboard.sh|utils/roadmap-dashboard.sh) printf '%s\n' releases ;;
    utils/telemetry/*|test/gh496-telemetry-isolation.sh)                                  printf '%s\n' telemetry ;;
    utils/ate/*|utils/fuzzing/*|utils/py/telemetry_schema.py|utils/py/domain_oracles.py|utils/py/adaptive_ate.py|utils/py/calibrate_tier1.py|utils/py/fuzz_engine.py|utils/py/repro_synth.py|utils/py/gen4_campaign.py|utils/py/proc_group.py|utils/py/ate_runaway_sweep.py) printf '%s\n' ate ;;
    utils/swe-diagram/*)                                                                   printf '%s\n' swe-diagram ;;
    utils/pdda/*|utils/pdda-local-checks.sh|utils/pdda-catchup.sh|utils/pdda-doc-ready.sh|utils/py/wave_reconcile.py) printf '%s\n' pdda ;;
    skills/agent-chorus/*)                                                                 printf '%s\n' agent-chorus ;;
    skills/standup/*)                                                                      printf '%s\n' standup ;;
    skills/skills-army-hq/*|test/test_deploy_skills.py|test/skills-army-hq.sh)             printf '%s\n' skills-army-hq ;;
  esac
}

event_name="${1:-}"

case "$event_name" in
  # Registry listing — the drift guard and `validate.sh --subsystem` read this instead of
  # re-deriving the mapping. A registered suite missing from disk fails LOUDLY here: a silent
  # skip would turn `--tier 2 --subsystem <name>` into a zero-test gate that exits green.
  subsystems)
    want="${2:-}"
    for s in $SUBSYSTEMS; do
      _tests="SUBSYSTEM_TESTS_${s//-/_}"
      for t in ${!_tests}; do
        [[ -f "$ROOT/test/$t" ]] || { echo "ci-route: subsystem $s registers missing test test/$t" >&2; exit 2; }
      done
    done
    found=0
    for s in $SUBSYSTEMS; do
      [ -z "$want" ] || [ "$want" = "$s" ] || continue
      found=1
      _tests="SUBSYSTEM_TESTS_${s//-/_}"
      if [ -n "$want" ]; then printf '%s\n' "${!_tests}"
      else printf '%s\t%s\n' "$s" "${!_tests}"; fi
    done
    if [ "$found" -eq 0 ]; then
      echo "ci-route: unknown subsystem: '${want}' (known: $(printf '%s' "$SUBSYSTEMS" | tr ' ' ','))" >&2
      exit 2
    fi
    exit 0
    ;;
  workflow_dispatch|schedule)
    # Deliberate, operator-initiated, and rare. These are the only unconditional full routes left:
    # a manual dispatch is someone asking for the whole gate, and answering it with a routed subset
    # would be answering a different question than the one asked.
    printf '%s\n' \
      'docs_only=false' \
      'pdda_needed=true' \
      'full_required=true' \
      'changed_tests=' \
      'route=full' \
      'tier=3' \
      'tier2_subsystems=' \
      'tier2_tests=' \
      'tier_reason=operator-initiated full run'
    exit 0
    ;;
  # GH-509 Phase 3 — `push` used to sit in the branch above, and that was 72% of the bill.
  #
  # Measured over 60 runs in ~24h: 37 pushes to `development`, EVERY ONE a full route, ~396 of ~551
  # billed minutes. Phase 1 routed pull requests and cut their average from ~16 min to 6.1 — it
  # worked, and it worked on the other 28%. The audit that opened this issue had already found the
  # same split (61/100 runs were pushes) and then exempted it.
  #
  # Pushes now classify from their pushed range exactly as a PR classifies from its diff. The caller
  # supplies the paths on stdin; a caller that cannot compute a range supplies NOTHING, and the
  # zero-path branch at the bottom of this file fails closed to full. That is deliberate reuse: the
  # fail-closed path is already tested, so a force-push or a new branch does not need its own.
  push|pull_request) ;;
  *)
    printf 'ci-route: unsupported event: %s\n' "${event_name:-<empty>}" >&2
    exit 2
    ;;
esac

docs_only=true
pdda_needed=false
full_required=false
changed_tests=""
tier2_subsystems=""
tier2_tests=""
test_touched=""
unmapped=""
claimed_test_subs=""
code_touched_subs=""
path_count=0

# Existence checks below are deliberately CWD-relative, not ROOT-relative: classification
# answers "which tests does THE REPO BEING CLASSIFIED have", and a push is classified with
# its own repo as the working directory (test/ci-route.sh's rename fixture depends on this —
# a deleted test must fail closed against the pushed repo, an edited one must not).

add_changed_test() {
  local candidate="$1"
  [[ -f "test/$candidate" ]] || return 0
  case ",$changed_tests," in
    *",$candidate,"*) return 0 ;;
  esac
  changed_tests="${changed_tests:+$changed_tests,}$candidate"
}

add_tier2_test() {  # <suite> — only suites that exist; a subsystem with none runnable on disk
  local candidate="$1"     # escalates to tier 3 at the end, never a zero-test green
  [[ -f "test/$candidate" ]] || return 0
  case ",$tier2_tests," in
    *",$candidate,"*) return 0 ;;
  esac
  tier2_tests="${tier2_tests:+$tier2_tests,}$candidate"
}

while IFS= read -r path || [[ -n "$path" ]]; do
  [[ -n "$path" ]] || continue
  path_count=$((path_count + 1))

  # Docs surfaces (GH-35 Phase 1 widened the GH-509 list): evidence, transcripts, notes, and
  # governance levers (*.txt anywhere, decisions/, .pdda-* levers, .xyz-launch-artifact).
  # GH-487: TESTS-RESULTS receipts join the evidence side — a provenance.jsonl follow-up used
  # to re-run the full gate as an unmapped path. skills/**/SKILL.md lands here via *.md —
  # explanatory markdown is a docs change; the skill's CODE paths route through the subsystem
  # registry instead.
  case "$path" in
    *.md|*.txt|PROJECT/*|docs/*|relay-system/*|decisions/*|.pdda-*|.xyz-launch-artifact|TESTS-RESULTS/*)
      pdda_needed=true
      ;;
    *)
      docs_only=false
      ;;
  esac

  # These surfaces own the coordination kernel, containment boundary, frozen twins,
  # worktree safety, or CI gate itself. They require the full suite before merge.
  # (GH-35 moved utils/pdda/** and skills/agent-chorus code off this list and into the
  # subsystem registry, per the issue's Tier-2 mapping; their focused suites run instead.)
  case "$path" in
    .github/workflows/*|validate.sh|utils/ci-route.sh|test/ci-route.sh|test/ci-workflow.sh)
      full_required=true
      ;;
    bin/tick|bin/validate-relay-block|src/*)
      full_required=true
      ;;
    relay-automation/*|skills/relay-automation/*|skills/relay-xyz/*)
      full_required=true
      ;;
    utils/py/*)
      # Subsystem code with focused suites (releases_app.py, wave_reconcile.py, ATE tools)
      # is not an authoritative twin; unmapped files under utils/py/ are kernel/twin surface.
      [ -n "$(subsystem_of "$path" || true)" ] || full_required=true
      ;;
    test/*worktree*|test/*containment*|test/tick-*|test/relay-*|test/agent-chorus.sh|test/marathon*.sh)
      full_required=true
      ;;
    test/gh308-*|test/mktemp-trap-guard.sh|test/path-integrity.sh)
      full_required=true
      ;;
  esac

  # A change to a test is a change to the routing contract's own evidence: tier 3 always
  # (GH-35 review guardrail — the contract must not be weakened unnoticed), while route stays
  # fast so CI keeps running the edited suite as a changed-area test (GH-509 behavior).
  case "$path" in
    test/*)
      # GH-487: a test path CLAIMED by a subsystem (listed in subsystem_of) is that subsystem's
      # dedicated evidence; it escalates only when the same push touches none of that
      # subsystem's code (co-touch resolved after the loop). A dedicated suite edited alone
      # would otherwise judge itself — the weakened artifact reporting a green nothing in the
      # push disagrees with. Unclaimed test paths keep the full GH-35 escalation.
      _dedicated_sub="$(subsystem_of "$path" || true)"
      if [ -n "$_dedicated_sub" ]; then
        case " $claimed_test_subs " in
          *" $_dedicated_sub "*) ;;
          *) claimed_test_subs="${claimed_test_subs:+$claimed_test_subs }$_dedicated_sub" ;;
        esac
      else
        test_touched=true
      fi
      ;;
  esac

  # Tier-2 membership: only explicitly registered subsystem paths qualify; every other
  # non-doc path fails closed to tier 3.
  case "$path" in
    *.md|*.txt|PROJECT/*|docs/*|relay-system/*|decisions/*|.pdda-*|.xyz-launch-artifact|TESTS-RESULTS/*)
      : # docs — neither disqualifies tier 1 nor joins a subsystem
      ;;
    *)
      sub="$(subsystem_of "$path" || true)"
      if [ -n "$sub" ]; then
        case " $tier2_subsystems " in
          *" $sub "*) ;;
          *) tier2_subsystems="${tier2_subsystems:+$tier2_subsystems }$sub" ;;
        esac
        # GH-487: remember which subsystems this push touches through NON-test code — the
        # co-touch half of the dedicated-test exemption.
        case "$path" in
          test/*) ;;
          *) code_touched_subs="${code_touched_subs:+$code_touched_subs }$sub" ;;
        esac
      else
        unmapped="$path"
      fi
      # PDDA-adjacent implementation still gets the PDDA gate even on tier 2.
      case "$path" in
        utils/pdda/*|utils/pdda-local-checks.sh|utils/pdda-catchup.sh|utils/pdda-doc-ready.sh|utils/py/wave_reconcile.py)
          pdda_needed=true
          ;;
      esac
      ;;
  esac

  case "$path" in
    test/*.sh)
      if [[ -f "$path" ]]; then
        add_changed_test "${path#test/}"
      else
        # A deleted/renamed regression cannot be exercised as a changed-area test.
        # Fail closed so test removal is reviewed against the complete inventory.
        full_required=true
      fi
      ;;
    *.sh|*.js|*.py)
      stem="${path##*/}"
      stem="${stem%.*}"
      add_changed_test "$stem.sh"
      normalized_stem="$(printf '%s' "$stem" | tr '_' '-')"
      add_changed_test "$normalized_stem.sh"
      ;;
  esac
done

# GH-487 co-touch resolution: a claimed dedicated test forces tier 3 when this push touches no
# code of its subsystem — the edited artifact is not coverage of anything else in the push.
for _s in $claimed_test_subs; do
  case " $code_touched_subs " in
    *" $_s "*) ;;
    *) test_touched=true ;;
  esac
done

# An empty or unreadable PR diff is not proof that the change is documentation-only.
if [[ "$path_count" -eq 0 ]]; then
  docs_only=false
  pdda_needed=true
  full_required=true
fi

if [[ "$full_required" == true ]]; then
  pdda_needed=true
  route=full
elif [[ "$docs_only" == true ]]; then
  route=docs
else
  route=fast
fi

# ── GH-35 tier resolution — fail closed ──────────────────────────────────────────────────────────
# tier 3 unless proven otherwise. Kernel/gate surfaces and docs-only are decided above; the
# remaining candidates must have EVERY non-doc path mapped to a subsystem and touch no test.
tier=3
tier_reason=""
if [[ "$full_required" == true ]]; then
  tier_reason="kernel/gate surface (route=full)"
elif [[ "$docs_only" == true ]]; then
  tier=1
  tier_reason="docs-only"
elif [[ "$test_touched" == true ]]; then
  tier_reason="test change — the routing contract's own evidence stays on the full gate"
elif [[ -n "$unmapped" ]]; then
  tier_reason="unmapped path: $unmapped"
else
  tier=2
  tier_reason="subsystems: $tier2_subsystems"
  for s in $tier2_subsystems; do
    _tests="SUBSYSTEM_TESTS_${s//-/_}"
    for t in ${!_tests}; do
      add_tier2_test "$t"
    done
  done
  # A subsystem whose suites are missing on disk (partial checkout, stripped fixture) must
  # escalate rather than hand back a tier-2 gate with nothing to run.
  if [[ -z "$tier2_tests" ]]; then
    tier=3
    tier_reason="subsystems [$tier2_subsystems] have no runnable tests here — failing closed"
  fi
fi

printf '%s\n' \
  "docs_only=$docs_only" \
  "pdda_needed=$pdda_needed" \
  "full_required=$full_required" \
  "changed_tests=$changed_tests" \
  "route=$route" \
  "tier=$tier" \
  "tier2_subsystems=$tier2_subsystems" \
  "tier2_tests=$tier2_tests" \
  "tier_reason=$tier_reason"
