#!/usr/bin/env bash
# test/gh496-phase2-reconciliation-views.sh — hermetic verification of GH-496 PR 2:
# 1. Hosted reconciler in-flight collision detection & emergency override controls
# 2. Deterministic pre-merge closeout checks (--pre-merge: frontmatter, lessons learned, receipts)
# 3. Marathon planner input fingerprinting to skip redundant replanning
set -euo pipefail

source test/_setup.sh "gh496-phase2" || { echo "setup failed"; exit 1; }

ROOT="$(cd "$HERE/.." && pwd)"
RECONCILE_PY="$ROOT/utils/py/wave_reconcile.py"

assert_eq() {
  local desc="$1"
  local got="$2"
  local exp="$3"
  if [ "$got" = "$exp" ]; then
    pass "$desc"
  else
    fail "$desc: expected '$exp', got '$got' (output: ${out:-none})"
  fi
}

echo "=== Running gh496-phase2-reconciliation-views.sh test suite ==="

# Setup mock PATH with custom gh binary
MOCK_BIN="$WORK/mock_bin"
mkdir -p "$MOCK_BIN"
MOCK_GH="$MOCK_BIN/gh"
MOCK_GH_STATE="$WORK/mock_gh_state.txt"
echo "clean" > "$MOCK_GH_STATE"

cat << EOF > "$MOCK_GH"
#!/usr/bin/env bash
STATE="\$(cat "$MOCK_GH_STATE" 2>/dev/null || echo "clean")"
if [ "\$STATE" = "error" ]; then
  echo "gh: network timeout connecting to api.github.com" >&2
  exit 1
fi

if [ "\$1" = "pr" ] && [ "\$2" = "view" ]; then
  pr_num="\$3"
  echo '{"number": 999, "title": "Test PR", "body": "closes #999", "state": "MERGED", "baseRefName": "development", "headRefOid": "0123456789abcdef0123456789abcdef01234567", "mergedAt": "2026-09-10T10:00:00Z", "mergeCommit": {"oid": "0123456789abcdef0123456789abcdef01234567"}}'
  exit 0
fi

if [ "\$1" = "issue" ] && [ "\$2" = "view" ]; then
  echo '{"state": "CLOSED"}'
  exit 0
fi

if [ "\$STATE" = "in_progress" ]; then
  echo '[{"databaseId": 998877, "status": "in_progress", "conclusion": null, "createdAt": "2026-09-10T10:00:00Z", "headSha": "abcdef1234", "event": "push"}]'
  exit 0
elif [ "\$STATE" = "malformed" ]; then
  echo "not valid json"
  exit 0
else
  # clean / completed
  echo '[{"databaseId": 998870, "status": "completed", "conclusion": "success", "createdAt": "2026-09-10T09:00:00Z", "headSha": "1234567890", "event": "push"}]'
  exit 0
fi
EOF
chmod +x "$MOCK_GH"

export PATH="$MOCK_BIN:$PATH"

# Setup hermetic fixture repo
REPO="$WORK/fixture-repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b development
git -C "$REPO" config user.name "Test Agent"
git -C "$REPO" config user.email "test@example.com"
git -C "$REPO" remote add origin "https://github.com/HiQS-Labs/XYZ-forge.git"

mkdir -p "$REPO/PROJECT/2-WORKING" "$REPO/PROJECT/3-COMPLETED" "$REPO/PROJECT/4-MISC" \
         "$REPO/utils/py" "$REPO/utils/pdda" "$REPO/utils/timeline" \
         "$REPO/TESTS-RESULTS/2026-09-10+GH-999" "$REPO/.github/workflows"
touch "$REPO/.github/workflows/wave-reconcile.yml"

cp "$RECONCILE_PY" "$ROOT/utils/py/harness_paths.py" "$REPO/utils/py/"

# Minimal releases.db & releases.sql
cat << 'PY_EOF' > "$REPO/init_db.py"
import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), "releases.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS roadmap_items (
    id INTEGER PRIMARY KEY,
    global_id TEXT NOT NULL UNIQUE,
    repo_id INTEGER,
    gh_number INTEGER,
    title TEXT NOT NULL,
    section TEXT NOT NULL,
    position INTEGER NOT NULL,
    status_marker TEXT,
    complexity INTEGER,
    risk INTEGER,
    effort INTEGER,
    doc_path TEXT,
    issue_url TEXT,
    raw_text TEXT NOT NULL,
    first_seen TEXT,
    updated_at TEXT
)
""")
c.execute("CREATE TABLE IF NOT EXISTS releases (id INTEGER PRIMARY KEY, global_id TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS issue_refs (id INTEGER PRIMARY KEY, url TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS manifest_items (release_id INTEGER, issue_ref_id INTEGER, state TEXT)")
c.execute("""INSERT OR REPLACE INTO roadmap_items 
    (global_id, repo_id, gh_number, title, section, position, status_marker, complexity, risk, effort, doc_path, issue_url, raw_text, first_seen, updated_at)
    VALUES ('rmi-0123456789ABCDEF0123456789', 1, 999, 'Test Item', 'Now', 1, '🚧', 1, 1, 1, 'PROJECT/2-WORKING/GH-999-TEST.md', 'https://github.com/HiQS-Labs/XYZ-forge/issues/999', '- **GH-999 · Test Item** 🚧 **active 2026-09-10** — test item description. -> [GH-999-TEST.md](PROJECT/2-WORKING/GH-999-TEST.md)', '2026-09-10', '2026-09-10')
""")
conn.commit()
conn.close()
PY_EOF
python3 "$REPO/init_db.py"
touch "$REPO/releases.sql"

# Minimal mocks for downstream tools
cat << 'APP_EOF' > "$REPO/utils/py/releases_app.py"
#!/usr/bin/env python3
import sys
if len(sys.argv) > 1 and sys.argv[1] == "settings" and sys.argv[2] == "get":
    print("42")
    sys.exit(0)
print("MOCK: releases_app OK")
sys.exit(0)
APP_EOF
chmod +x "$REPO/utils/py/releases_app.py"

cat << 'DASH_EOF' > "$REPO/utils/roadmap-dashboard.sh"
#!/usr/bin/env bash
echo "MOCK: roadmap-dashboard OK"
exit 0
DASH_EOF
chmod +x "$REPO/utils/roadmap-dashboard.sh"

PLANNER_CALLS="$REPO/planner_calls.log"
cat << PLAN_EOF > "$REPO/utils/marathon-plan.sh"
#!/usr/bin/env bash
echo "called" >> "$PLANNER_CALLS"
echo "MOCK: marathon-plan OK"
exit 0
PLAN_EOF
chmod +x "$REPO/utils/marathon-plan.sh"

cat << 'LB_EOF' > "$REPO/utils/leaderboard.sh"
#!/usr/bin/env bash
echo "MOCK: leaderboard OK"
exit 0
LB_EOF
chmod +x "$REPO/utils/leaderboard.sh"

cat << 'TL_EOF' > "$REPO/utils/timeline/export_timeline.py"
#!/usr/bin/env python3
import sys
sys.exit(0)
TL_EOF
chmod +x "$REPO/utils/timeline/export_timeline.py"

cat << 'PDDA_EOF' > "$REPO/utils/pdda/pdda.sh"
#!/usr/bin/env bash
exit 0
PDDA_EOF
chmod +x "$REPO/utils/pdda/pdda.sh"

cat << 'ROAD_EOF' > "$REPO/ROADMAP.md"
# Roadmap
### Active
* [ ] #999 Test Item
### Completed
ROAD_EOF

cat << 'MAN_EOF' > "$REPO/manifest.json"
{
  "issues": [999],
  "prs": [999]
}
MAN_EOF

# Initial valid active doc
cat << 'DOC_EOF' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
---
title: Test Task
status: Review
created: 2026-09-10
updated: 2026-09-10
owner: test-agent
goal: Verify pre-merge checks
---
# GH-999: Test Task

## Summary
Testing pre-merge checks.

## Lessons Learned

### 1. Closeout Verification
We verified that closeout gates require substantive reflections and valid frontmatter.
DOC_EOF

# Commit initial state
git -C "$REPO" add -A
git -C "$REPO" commit -q -m "feat: initial commit for #999"
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"

# Write committed passing test receipt matching HEAD_SHA
cat << RECEIPT_EOF > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
{"commit": "$HEAD_SHA", "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
RECEIPT_EOF
git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" commit -q -m "test: commit passing test receipt"
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"

# Update the receipt with the latest HEAD_SHA so it matches HEAD
cat << RECEIPT_EOF2 > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
{"commit": "$HEAD_SHA", "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
RECEIPT_EOF2
git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" commit -q --amend -m "test: commit passing test receipt matching HEAD"
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"

# -------------------------------------------------------------
# Part 1: Hosted Reconciler In-Flight Collision Detection
# -------------------------------------------------------------
echo "in_progress" > "$MOCK_GH_STATE"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "In-flight hosted reconciler fails closed (exit 8)" "$rc" "8"
if grep -q "Hosted reconciliation workflow (wave-reconcile.yml) is currently in-flight" <<< "$out"; then
  pass "Error message identifies in-flight wave-reconcile run"
else
  fail "Error message did not identify in-flight run: $out"
fi

# Override with --force-local-reconcile
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --force-local-reconcile --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "In-flight check bypassed with --force-local-reconcile (exit 0)" "$rc" "0"
if grep -q "Overriding active hosted reconciliation run" <<< "$out"; then
  pass "Warning logged when overriding in-flight run"
else
  fail "Warning missing on --force-local-reconcile override: $out"
fi
git -C "$REPO" checkout -q -f development
git -C "$REPO" clean -q -fd

# In GITHUB_ACTIONS, --force-local-reconcile is strictly prohibited (exit 2)
rc=0; out="$(GITHUB_ACTIONS=true python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --force-local-reconcile --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "--force-local-reconcile rejected inside GITHUB_ACTIONS (exit 2)" "$rc" "2"
if grep -q -F -- "--force-local-reconcile is prohibited inside GITHUB_ACTIONS" <<< "$out"; then
  pass "Error correctly explains GITHUB_ACTIONS prohibition"
else
  fail "Unexpected error message for GITHUB_ACTIONS prohibition: $out"
fi

# If gh reports error/network failure, check fails closed (exit 8)
echo "error" > "$MOCK_GH_STATE"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "gh failure fails closed (exit 8)" "$rc" "8"
if grep -q "Hosted reconciler check failed: unable to query GitHub Actions" <<< "$out"; then
  pass "gh error produces clean failure message"
else
  fail "Unexpected error message on gh error: $out"
fi

# Reset mock gh to clean
echo "clean" > "$MOCK_GH_STATE"

# Reset working repo state for pre-merge checks
git -C "$REPO" checkout -q development
# Ensure valid active doc is back in 2-WORKING
if [ -f "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" ]; then
  mv "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
  sed -i.bak 's/status: Complete/status: Review/' "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
  rm -f "$REPO/PROJECT/2-WORKING/GH-999-TEST.md.bak"
  git -C "$REPO" add -A
  git -C "$REPO" commit -q -m "test: reset doc to 2-WORKING"
fi

# Update test receipt with current HEAD
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
cat << EOF_REC > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
{"commit": "$HEAD_SHA", "pr": 999, "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
EOF_REC
git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" commit -q -m "fix: closes #999"

# -------------------------------------------------------------
# Part 2: Pre-Merge Validation Checks (--pre-merge)
# -------------------------------------------------------------
# Case A: Valid doc, substantive lessons learned, matching committed receipt -> PASS (exit 0)
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Pre-merge check passes when all conditions are met (exit 0)" "$rc" "0"
if grep -q "Pre-merge validation PASSED!" <<< "$out"; then
  pass "Pre-merge confirmation message output"
else
  fail "Pre-merge did not output PASSED confirmation: $out"
fi

# Case B: Red Control 1 - Empty/placeholder lessons learned -> exit 5
cat << 'DOC_LL' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
---
title: Test Task
status: Review
created: 2026-09-10
updated: 2026-09-10
owner: test-agent
goal: Verify pre-merge checks
---
# GH-999: Test Task

## Lessons Learned

TODO: add lessons learned later
<!-- none yet -->
DOC_LL
git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
git -C "$REPO" commit -q -m "fix: closes #999 with empty lessons learned"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Placeholder lessons learned is rejected (exit 5)" "$rc" "5"
if grep -q "empty/placeholder '## Lessons Learned'" <<< "$out"; then
  pass "Error message cites empty/placeholder lessons learned"
else
  fail "Error message missing placeholder explanation: $out"
fi

# Case C: Red Control 2 - Missing required frontmatter field -> exit 5
cat << 'DOC_FM' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
---
title: Test Task
status: Review
created: 2026-09-10
updated: 2026-09-10
goal: Verify pre-merge checks
---
# GH-999: Test Task

## Lessons Learned

### 1. Substantive
Reflections exist here.
DOC_FM
git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
git -C "$REPO" commit -q -m "fix: closes #999 with missing owner in frontmatter"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Missing frontmatter owner field is rejected (exit 5)" "$rc" "5"
if grep -q "frontmatter missing required field(s): owner" <<< "$out"; then
  pass "Error message cites missing owner field"
else
  fail "Error message missing frontmatter explanation: $out"
fi

# Case D: Red Control 3 - Missing committed test receipt -> exit 6
# Restore valid doc
cat << 'DOC_VALID' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
---
title: Test Task
status: Review
created: 2026-09-10
updated: 2026-09-10
owner: test-agent
goal: Verify pre-merge checks
---
# GH-999: Test Task

## Lessons Learned

### 1. Substantive
Reflections exist here.
DOC_VALID
git -C "$REPO" rm -q "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
git -C "$REPO" commit -q -m "fix: closes #999 without test receipt"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Missing committed test receipt is rejected (exit 6)" "$rc" "6"
if grep -q "No committed provenance.jsonl or error_log.jsonl receipts found" <<< "$out"; then
  pass "Error message cites missing committed receipt at HEAD"
else
  fail "Error message missing receipt explanation: $out"
fi

# Case E: Red Control 4 - Uncommitted test receipt is not proof -> exit 6
mkdir -p "$REPO/TESTS-RESULTS/2026-09-10+GH-999"
echo '{"commit": "xyz", "rc": 0, "result": "pass"}' > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
# Receipt exists on disk as untracked file, but NOT committed in git tree at HEAD
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Uncommitted test receipt does not satisfy check (exit 6)" "$rc" "6"
rm -rf "$REPO/TESTS-RESULTS/2026-09-10+GH-999"

# Case F: Red Control 5 - Stale test receipt rejected when code changes after test -> exit 6
head_commit="$(git -C "$REPO" rev-parse HEAD)"
mkdir -p "$REPO/TESTS-RESULTS/2026-09-10+GH-999"
printf '{"commit": "%s", "rc": 0, "result": "pass"}\n' "$head_commit" > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
git -C "$REPO" commit -q -m "test: commit receipt for previous commit"
# Now make a code change without re-running tests
echo "# code modification" >> "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
git -C "$REPO" commit -q -am "fix: code change after receipt was generated"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
assert_eq "Stale test receipt with code changes is rejected (exit 6)" "$rc" "6"
if grep -q "No committed passing test receipt at HEAD matches" <<< "$out"; then
  pass "Error confirms stale receipt rejected"
else
  fail "Error missing stale receipt explanation: $out"
fi

# Case G: Red Control 6 - Pre-merge fails closed when PR metadata cannot be fetched -> exit 2
echo "error" > "$MOCK_GH_STATE"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge --pr 999 2>&1)" || rc=$?
assert_eq "Pre-merge fails closed when PR metadata cannot be fetched (exit 2)" "$rc" "2"
if grep -q "Failed to query PR #999 via gh pr view" <<< "$out"; then
  pass "Error message explains PR query failure"
else
  fail "Error missing PR query failure explanation: $out"
fi
echo "clean" > "$MOCK_GH_STATE"

# -------------------------------------------------------------
# Part 3: Marathon Plan Fingerprinting
# -------------------------------------------------------------
# Clean up any leftover plan docs and reset planner log
rm -f "$REPO/planner_calls.log" "$REPO/.tick/marathon-plan.fingerprint"
touch "$REPO/PROJECT/2-WORKING/MARATHON-PLAN-2026-09-10.md"
git -C "$REPO" add -A
git -C "$REPO" commit -q -m "test: fixture for marathon plan fingerprinting"

# 1st run: Fingerprint does not exist yet -> marathon-plan.sh must execute
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "Reconciler runs successfully (exit 0)" "$rc" "0"
calls_run1="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
assert_eq "Marathon planner executed on initial run" "$calls_run1" "1"
[ -f "$REPO/.tick/marathon-plan.fingerprint" ] || fail "Fingerprint file not created at .tick/marathon-plan.fingerprint"
pass "Fingerprint file created on initial run"

# 2nd run: Inputs unchanged -> marathon-plan.sh must be skipped!
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "Second run exits 0" "$rc" "0"
calls_run2="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
assert_eq "Marathon planner skipped when canonical inputs unchanged" "$calls_run2" "1"
if grep -q "skipping marathon-plan.sh — canonical inputs unchanged" <<< "$out"; then
  pass "Log confirms marathon-plan.sh was skipped due to unchanged fingerprint"
else
  fail "Log missing skipped marathon-plan explanation: $out"
fi

# 3rd run: Mutate roadmap_items in releases.db -> fingerprint changes -> marathon-plan.sh must run!
python3 -c '
import sqlite3
conn = sqlite3.connect("'"$REPO/releases.db"'")
conn.execute("INSERT INTO roadmap_items (global_id, repo_id, gh_number, title, section, position, raw_text, first_seen, updated_at) VALUES (\x27rmi-NEW0000000000000000000001\x27, 1, 1002, \x27New Item\x27, \x27Now\x27, 2, \x27- **GH-1002**\x27, \x272026-09-10\x27, \x272026-09-10\x27)")
conn.commit()
conn.close()
'
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "Third run exits 0 after roadmap mutation" "$rc" "0"
calls_run3="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
assert_eq "Marathon planner re-executed when roadmap inputs modified" "$calls_run3" "2"

# 4th run: Mutate active working document contents -> fingerprint changes -> marathon-plan.sh must run!
echo "Updated requirement content in active doc" >> "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
assert_eq "Fourth run exits 0 after active doc content mutation" "$rc" "0"
calls_run4="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
assert_eq "Marathon planner re-executed when active doc contents modified" "$calls_run4" "3"

echo "=== All GH-496 Phase 2 tests passed successfully! ==="
