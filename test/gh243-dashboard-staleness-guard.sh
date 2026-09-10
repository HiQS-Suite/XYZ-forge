#!/bin/bash
# test/gh243-dashboard-staleness-guard.sh — the GH-243 push guard: a roadmap-ledger write without a
# dashboard regeneration is refused, releases-mode only, and only when a real range exists.
set -eu
source test/_setup.sh "GH-243" || { echo "setup failed"; exit 1; }

root="$(cd "$HERE/.." && pwd)"
GUARD="$root/githooks/dashboard-staleness-guard.sh"

# Fixture: a releases-mode repo with a base commit, then a ledger-only commit on top.
R="$WORK/fixture"
mkdir -p "$R"
cd "$R"
git init -q .
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
echo "ROADMAP_SOURCE=releases" > .pdda-mode
echo "-- dump v1" > releases.sql
echo "dash v1" > ROADMAP-DASHBOARD.md
git add .pdda-mode releases.sql ROADMAP-DASHBOARD.md
git -c user.email=t@t -c user.name=t commit -q -m "v1"
BASE="$(git rev-parse HEAD)"

echo "-- dump v2" > releases.sql
git add releases.sql
git -c user.email=t@t -c user.name=t commit -q -m "ledger write, no dashboard"
LEDGER_ONLY="$(git rev-parse HEAD)"
cd "$root"

# 1. Ledger write without dashboard when renderer cannot run -> refuse (exit 1).
rc=0; out="$(bash "$GUARD" "$R" "$LEDGER_ONLY" "$BASE" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "expected refusal (1), got $rc"
grep -q "cannot be rendered into a valid dashboard" <<<"$out" || fail "refusal missing the renderer failure explanation"

# 2. Committing dashboard without modifying renderer -> refuse (exit 1) (GH-496 Phase 2 View Decoupling).
cd "$R"
echo "dash v2" > ROADMAP-DASHBOARD.md
git add ROADMAP-DASHBOARD.md
git -c user.email=t@t -c user.name=t commit -q -m "unauthorized routine dashboard commit"
UNAUTH="$(git rev-parse HEAD)"
cd "$root"
rc=0; out="$(bash "$GUARD" "$R" "$UNAUTH" "$BASE" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "expected refusal (1) for routine view commit, got $rc"
grep -q "Under GH-496 Phase 2" <<<"$out" || fail "expected Phase 2 view decoupling explanation"
FIXED="$UNAUTH"

# 3. Legacy-mode repo (no releases marker) -> guard is inert even on a ledger-only range.
cd "$R"; : > .pdda-mode; cd "$root"
bash "$GUARD" "$R" "$LEDGER_ONLY" "$BASE" || fail "legacy-mode repo must not be guarded, got $?"
cd "$R"; echo "ROADMAP_SOURCE=releases" > .pdda-mode; cd "$root"

# 4. New branch (all-zero remote sha) -> no range, no refusal.
bash "$GUARD" "$R" "$LEDGER_ONLY" "0000000000000000000000000000000000000000" \
  || fail "new-branch push must fall through, got $?"

# 5. Non-ledger range (docs commit only) -> pass.
cd "$R"
echo "readme" > README.md
git add README.md
git -c user.email=t@t -c user.name=t commit -q -m docs
DOCS="$(git rev-parse HEAD)"
cd "$root"
bash "$GUARD" "$R" "$DOCS" "$FIXED" || fail "non-ledger range must pass, got $?"

# 6. Usage error -> exit 2.
rc=0; bash "$GUARD" >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "expected usage exit 2, got $rc"


# 7. GH-474: a ledger write the renderer renders cleanly -> ALLOW, whatever table it touched.
# The guard no longer classifies by table name; it asks the renderer whether it dropped a row.
# `jog_queue` is the GH-315 shape that first exposed the old allowlist going short. The fixture
# needs a renderer whose --check passes to reach the guard's no-drift branch at all; this stub
# exits 0 and says nothing on stderr, which is exactly "rendered fine, dropped nothing".
mkdir -p "$R/utils"
printf '#!/usr/bin/env bash\nexit 0\n' > "$R/utils/roadmap-dashboard.sh"
chmod +x "$R/utils/roadmap-dashboard.sh"
cd "$R"
git add utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "add passing renderer"
RENDERED="$(git rev-parse HEAD)"
{ echo "-- dump v3"
  echo "INSERT INTO settings(key, value) VALUES('generation', '9');"
  echo "INSERT INTO jog_queue VALUES('seed');"
  echo "INSERT INTO op_receipts(op, target_gid) VALUES('jog-add', 'seed');"
} > releases.sql
git add releases.sql
git -c user.email=t@t -c user.name=t commit -q -m "jog-only ledger write"
JOG_ONLY="$(git rev-parse HEAD)"
cd "$root"
bash "$GUARD" "$R" "$JOG_ONLY" "$RENDERED" \
  || fail "jog-queue-only ledger write must pass the no-drift branch (GH-315), got $?"

# 7b. THE REGRESSION THIS CHANGE FIXES. Every one of these tables hit the old allowlist's
# catch-all and produced a FALSE refusal — `releases add` alone tripped it. They are not
# enumerated anywhere in the guard any more, which is the point: the guard reads the renderer's
# report, so a table it has never heard of cannot make it go short.
cd "$R"
{ echo "-- dump v3b"
  echo "INSERT INTO settings(key, value) VALUES('generation', '10');"
  echo "INSERT INTO releases(global_id, name) VALUES('rel-1', 'v9');"
  echo "INSERT INTO repos(repo_id, name) VALUES(2, 'other');"
  echo "INSERT INTO manifest_items(global_id) VALUES('mi-1');"
  echo "INSERT INTO doc_lines(global_id) VALUES('dl-1');"
  echo "INSERT INTO schema_migrations(version) VALUES('077');"
  echo "INSERT INTO totally_new_table_v9(global_id) VALUES('nt-1');"
} > releases.sql
git add releases.sql
git -c user.email=t@t -c user.name=t commit -q -m "previously-unclassified ledger write"
UNCLASSIFIED="$(git rev-parse HEAD)"
cd "$root"
bash "$GUARD" "$R" "$UNCLASSIFIED" "$RENDERED" \
  || fail "GH-474: a clean render must allow any table, including ones no allowlist knows, got $?"

# 8. RED CONTROL for 7 and 7b. Same no-drift shape, same tables 7b just allowed — but now the
# renderer reports a dropped row. The guard must refuse AND name the row it was told about.
# This is what proves 7/7b pass because the renderer said "clean", not because the arm is inert.
cd "$R"
cat > utils/roadmap-dashboard.sh <<'EOFSTUB'
#!/usr/bin/env bash
echo "roadmap-dashboard: warning: dropped 1 unparseable row(s): #256" >&2
exit 0
EOFSTUB
chmod +x utils/roadmap-dashboard.sh
git add utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "renderer drops a row"
DROPPED="$(git rev-parse HEAD)"
cd "$root"
rc=0; out="$(bash "$GUARD" "$R" "$DROPPED" "$RENDERED" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "expected no-drift refusal (1) when the renderer drops a row, got $rc"
grep -q "NO diff" <<<"$out" || fail "expected the no-diff refusal message"
grep -q "dropped 1 unparseable row(s): #256" <<<"$out" \
  || fail "GH-474: refusal must NAME the dropped row the renderer reported, got: $out"

# 8b. Negative control on the signal itself: renderer exits 0 with unrelated stderr chatter ->
# ALLOW. Guards against matching any stderr output rather than the dropped-row warning.
cd "$R"
cat > utils/roadmap-dashboard.sh <<'EOFSTUB2'
#!/usr/bin/env bash
echo "roadmap-dashboard: note: rendered 41 rows" >&2
exit 0
EOFSTUB2
chmod +x utils/roadmap-dashboard.sh
git add utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "renderer chatters but drops nothing"
CHATTY="$(git rev-parse HEAD)"
cd "$root"
bash "$GUARD" "$R" "$CHATTY" "$RENDERED" \
  || fail "unrelated renderer stderr must not be read as a dropped row, got $?"

# 9. Unauthorized LEADERBOARD.md commit without modifying renderer -> refuse (exit 1) (GH-496 Phase 2).
cd "$R"
echo "leaderboard v1" > LEADERBOARD.md
git add LEADERBOARD.md
git -c user.email=t@t -c user.name=t commit -q -m "unauthorized leaderboard commit"
UNAUTH_LB="$(git rev-parse HEAD)"
cd "$root"
rc=0; out="$(bash "$GUARD" "$R" "$UNAUTH_LB" "$CHATTY" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "expected refusal (1) for routine leaderboard commit, got $rc"
grep -q "Under GH-496 Phase 2" <<<"$out" || fail "expected Phase 2 view decoupling explanation for leaderboard"

# 10. GITHUB_ACTIONS=true bypasses the view refusal (reconciler bot on development).
cd "$root"
GITHUB_ACTIONS=true bash "$GUARD" "$R" "$UNAUTH_LB" "$CHATTY" \
  || fail "GITHUB_ACTIONS=true must permit reconciler view commits, got $?"

echo "== GH-243 ALL PASSED =="
