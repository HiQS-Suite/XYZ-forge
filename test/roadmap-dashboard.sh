#!/usr/bin/env bash
# test/roadmap-dashboard.sh — regression lock for utils/roadmap-dashboard.sh (GH-27).
#
# GH-351: this file used to render the dashboard INTO THE REPO and then --check the copy it had
# just written, so the drift assertion could never fail. Three stale dashboards reached
# `development` under a green gate on 2026-07-30 alone, from three different authors. Two rules
# now hold, and the ordering of the cases below is load-bearing:
#
#   1. --check runs FIRST, against the COMMITTED artifact, before anything in this file writes.
#   2. Nothing here ever writes $ROOT/ROADMAP-DASHBOARD.md. Write-mode is exercised against a
#      temp path via ROADMAP_DASHBOARD_OUTPUT, which the renderer already supports.
#
# Case 4 is the one that keeps this honest: it proves --check ACTUALLY FAILS on a drifted
# artifact. Without it this file would just be a differently-shaped version of the same bug —
# an assertion that cannot distinguish the bug from the fix.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
RENDERER="$ROOT/utils/roadmap-dashboard.sh"
ARTIFACT="$ROOT/ROADMAP-DASHBOARD.md"
SOURCE="$ROOT/ROADMAP.md"

PASS=0
FAIL=0
SKIP=0
pass() { echo "  PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $*" >&2; FAIL=$((FAIL + 1)); }
skip() { echo "  SKIP: $*"; SKIP=$((SKIP + 1)); }

echo "== test: roadmap-dashboard =="

# GH-110 P2b: ROADMAP-DASHBOARD.md is a repo-root artifact that does not travel with a vendored
# install (VENDOR_DIRS mirrors relay-automation/bin/src/utils/test/skills only). In a vendored copy
# there is nothing here to render/check, so skip the whole ROADMAP-DASHBOARD.md-dependent case
# rather than dangle-fail — mirrors the guard already landed in test/oracle-guard.sh.
if [ -e "$ARTIFACT" ]; then

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/roadmap-dashboard-test.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

# Fingerprint the committed artifact up front. Case 7 re-checks it at the end to prove this file
# left the working tree alone — the side effect that made the old version destructive as well as
# tautological.
artifact_sum_before="$(cksum < "$ARTIFACT")"

# --- Case 1: THE GATE. --check against the committed artifact, before anything writes. --------
out="$(bash "$RENDERER" --check 2>&1)"; rc=$?
if [[ $rc -eq 0 ]]; then
  pass "--check passes on the COMMITTED artifact (nothing regenerated first)"
else
  fail "committed ROADMAP-DASHBOARD.md is stale — regenerate it with 'bash utils/roadmap-dashboard.sh'"$'\n'"$out"
fi

# --- Case 2: write-mode still works, redirected away from the repo -----------------------------
tmp_out="$TMP_ROOT/written.md"
out="$(ROADMAP_DASHBOARD_OUTPUT="$tmp_out" bash "$RENDERER" 2>&1)"; rc=$?
if [[ $rc -eq 0 && -s "$tmp_out" ]]; then
  pass "renderer writes a dashboard (to a temp path, never \$ROOT)"
else
  fail "renderer exited $rc or wrote nothing — $out"
fi

# --- Case 3: a fresh render of the current ROADMAP equals the committed artifact ---------------
# Same property as case 1, reached independently: byte-compare rather than trusting --check's rc.
if cmp -s "$tmp_out" "$ARTIFACT"; then
  pass "a fresh render is byte-identical to the committed artifact"
else
  fail "fresh render differs from the committed artifact:"$'\n'"$(diff -u "$ARTIFACT" "$tmp_out" | head -20)"
fi

# --- Case 4: THE MUTATION PROOF. --check must actually FAIL on drift. -------------------------
# Without this, cases 1 and 3 are unfalsifiable and this file repeats GH-351 in a new shape.
drift_art="$TMP_ROOT/drifted.md"
cp "$ARTIFACT" "$drift_art"
printf '\n| DRIFT-CANARY | injected-by-test | GH-351 |\n' >> "$drift_art"
out="$(ROADMAP_DASHBOARD_OUTPUT="$drift_art" bash "$RENDERER" --check 2>&1)"; rc=$?
if [[ $rc -ne 0 ]]; then
  pass "--check FAILS on a drifted artifact (rc=$rc) — the assertion is falsifiable"
else
  fail "--check passed a deliberately drifted artifact — GH-351 has regressed in a new shape"
fi

# --- Case 5: --check fails on a MISSING artifact, rather than passing vacuously ----------------
out="$(ROADMAP_DASHBOARD_OUTPUT="$TMP_ROOT/does-not-exist.md" bash "$RENDERER" --check 2>&1)"; rc=$?
if [[ $rc -ne 0 ]]; then
  pass "--check fails on a missing artifact (rc=$rc)"
else
  fail "--check passed with no artifact present — a vacuous green"
fi

# --- Case 6: drift in the SOURCE is detected, not just in the artifact -------------------------
# The real-world failure is always this direction: ROADMAP.md moves, the dashboard does not.
drift_src="$TMP_ROOT/ROADMAP-changed.md"
sed 's/^### Queue \/ parked intake$/### Queue \/ parked intake\n- **GH-000 · canary entry injected by test\*\* 🆕 — not a real item./' \
  "$SOURCE" > "$drift_src"
if cmp -s "$drift_src" "$SOURCE"; then
  skip "case 6: could not inject a source canary (ROADMAP.md layout changed)"
else
  out="$(ROADMAP_DASHBOARD_SOURCE="$drift_src" ROADMAP_DASHBOARD_OUTPUT="$ARTIFACT" bash "$RENDERER" --check 2>&1)"; rc=$?
  if [[ $rc -ne 0 ]]; then
    pass "--check FAILS when ROADMAP.md gains an item the dashboard lacks (the real-world case)"
  else
    fail "--check passed while the source had an extra entry — drift is undetectable"
  fi
fi

# --- Case 7: this test did not mutate the working tree ----------------------------------------
# The old version regenerated $ROOT/ROADMAP-DASHBOARD.md as a side effect, so `validate.sh` could
# silently un-stale a dashboard mid-run and hide the very drift it was meant to catch.
if [ "$(cksum < "$ARTIFACT")" = "$artifact_sum_before" ]; then
  pass "committed artifact is byte-unchanged — this test writes nothing into \$ROOT"
else
  fail "this test MUTATED \$ROOT/ROADMAP-DASHBOARD.md — the GH-351 side effect is back"
fi

# --- Case 8: the do-not-edit banner and generation marker --------------------------------------
if grep -q '<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT;' "$ARTIFACT"; then
  pass "artifact carries the do-not-edit banner"
else
  fail "artifact is missing the generated banner"
fi
if grep -Eq '^<!-- releases-app generation: [0-9]+ -->$' "$ARTIFACT"; then
  pass "artifact carries the releases-app generation marker"
fi

# --- Case 9: section counts match ROADMAP.md ---------------------------------------------------
# GH-243: in a releases-mode repo the dashboard renders from the RELEASES DB and ROADMAP.md is
# frozen legacy — the DB legitimately gains rows the frozen file never will, so text-parity is
# no longer an invariant. Cases 1/3/4/6 already pin artifact-vs-live-source fidelity via --check
# (which regenerates from the real source, DB included); this case guards legacy repos only.
if grep -q "ROADMAP_SOURCE=releases" "$ROOT/.pdda-mode" 2>/dev/null; then
  pass "case 9 skipped: releases-mode — dashboard parity is against the DB (covered by --check), not the frozen ROADMAP.md"
else
counts_out="$(SOURCE_PATH="$SOURCE" ARTIFACT_PATH="$ARTIFACT" node <<'NODE' 2>&1
const fs = require("fs");

const sourcePath = process.env.SOURCE_PATH;
const artifactPath = process.env.ARTIFACT_PATH;
const expectedSections = [
  "Queue / parked intake",
  "In progress",
  "Completed",
  "Deferred · vision",
];

const sourceLines = fs.readFileSync(sourcePath, "utf8").split(/\r?\n/);
const artifactLines = fs.readFileSync(artifactPath, "utf8").split(/\r?\n/);

function extractRoadmapCounts(lines) {
  const counts = {};
  let inLedger = false;
  let current = null;
  for (const section of expectedSections) counts[section] = 0;

  for (const line of lines) {
    if (!inLedger) {
      if (/^##\s+Ledger\s*$/.test(line.trim())) inLedger = true;
      continue;
    }
    if (/^##\s+/.test(line) && !/^##\s+Ledger\s*$/.test(line.trim())) break;
    const sectionMatch = line.match(/^###\s+(.+?)\s*$/);
    if (sectionMatch) {
      current = counts.hasOwnProperty(sectionMatch[1].trim()) ? sectionMatch[1].trim() : null;
      continue;
    }
    if (current && /^- \*\*/.test(line)) counts[current] += 1;
  }
  return counts;
}

function extractDashboardCounts(lines) {
  const counts = {};
  let current = null;

  for (const line of lines) {
    const sectionMatch = line.match(/^##\s+(.+?)\s*$/);
    if (sectionMatch) {
      current = sectionMatch[1].trim();
      continue;
    }
    const summaryMatch = line.match(/^Summary:\s+(\d+)\s+items\s+\|\s+Tally:/);
    if (current && summaryMatch) {
      counts[current] = Number(summaryMatch[1]);
    }
  }
  return counts;
}

const roadmapCounts = extractRoadmapCounts(sourceLines);
const dashboardCounts = extractDashboardCounts(artifactLines);

for (const section of expectedSections) {
  if (roadmapCounts[section] !== dashboardCounts[section]) {
    console.error(`${section}: roadmap=${roadmapCounts[section]} dashboard=${dashboardCounts[section]}`);
    process.exit(1);
  }
}
NODE
)"; rc=$?
if [[ $rc -eq 0 ]]; then
  pass "section counts match ROADMAP.md"
else
  fail "section counts drifted — $counts_out"
fi
fi

else
  skip "ROADMAP-DASHBOARD.md-dependent checks need \$ROOT/ROADMAP-DASHBOARD.md (absent in a vendored copy)"
fi

echo ""
echo "  roadmap-dashboard: $PASS passed, $FAIL failed, $SKIP skipped"
[[ $FAIL -eq 0 ]] || exit 1
