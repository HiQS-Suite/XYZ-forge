#!/usr/bin/env bash
# test/gh257-roadmap-ledger-fixes.sh — regression suite for GH-257:
# 1. validate --raw-text on roadmap add and update against renderer bold bullet shape (single line)
# 2. emit warning on dropped unparseable rows in roadmap-dashboard.sh
# 3. roadmap update subcommand for parked raw_text with auditable receipt and rating sync
# 4. staleness guard diagnostic guidance when regeneration yields no diff
set -euo pipefail
source test/_setup.sh "GH-257" || { echo "setup failed"; exit 1; }

root="$(cd "$HERE/.." && pwd)"
app() { python3 "$root/utils/py/releases_app.py" "$@"; }
RENDERER="$root/utils/roadmap-dashboard.sh"
GUARD="$root/githooks/dashboard-staleness-guard.sh"

R="$WORK/repo"
mkdir -p "$R/utils/py"
cp -r "$root/utils/"* "$R/utils/"
cd "$R"
git init -q .
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
echo "ROADMAP_SOURCE=releases" > .pdda-mode
mkdir -p PROJECT/1-INBOX
touch PROJECT/1-INBOX/GH-255-test.md

app --root "$R" init --slug "test-repo"

# -----------------------------------------------------------------------------
# Case 1: roadmap add with malformed --raw-text is REFUSED at step 1
# -----------------------------------------------------------------------------
for bad_input in \
  "- [ ] #255 malformed checkbox" \
  "-   **GH-255 · repeated spaces** 🆕" \
  "-	**GH-255 · tab after dash** 🆕" \
  "- **GH-255 unclosed bold" \
  "- **** empty title GH-255" \
  $'- **GH-255 · title**\n- [ ] #999 smuggled row' \
  $'- **GH-255 · title**\r\nmalformed continuation'
do
  rc=0
  out="$(app --root "$R" roadmap add --issue-num 255 --issue-url "https://github.com/org/repo/issues/255" \
    --title "test 255" --created "2026-08-26" --doc-path "PROJECT/1-INBOX/GH-255-test.md" \
    --raw-text "$bad_input" 2>&1)" || rc=$?

  [ "$rc" -ne 0 ] || fail "malformed raw_text '$bad_input' should be refused on add, got rc=0"
  case "$out" in
    *"rule=invalid-raw-text"*) pass "roadmap add refused malformed raw_text: '$bad_input'" ;;
    *) fail "expected invalid-raw-text rule for '$bad_input', got: $out" ;;
  esac
done

# -----------------------------------------------------------------------------
# Case 2: roadmap add with mismatched issue number in --raw-text is REFUSED
# -----------------------------------------------------------------------------
rc=0
out="$(app --root "$R" roadmap add --issue-num 255 --issue-url "https://github.com/org/repo/issues/255" \
  --title "test 255" --created "2026-08-26" --doc-path "PROJECT/1-INBOX/GH-255-test.md" \
  --raw-text "- **GH-999 · wrong issue** 🆕" 2>&1)" || rc=$?

[ "$rc" -ne 0 ] || fail "mismatched issue number in raw_text should be refused, got rc=0"
case "$out" in
  *"rule=invalid-raw-text"*"GH-255"*) pass "roadmap add refused mismatched issue number" ;;
  *) fail "expected issue number mismatch refusal, got: $out" ;;
esac

# -----------------------------------------------------------------------------
# Case 3: roadmap add with valid --raw-text SUCCEEDS
# -----------------------------------------------------------------------------
app --root "$R" roadmap add --issue-num 255 --issue-url "https://github.com/org/repo/issues/255" \
  --title "test 255" --created "2026-08-26" --doc-path "PROJECT/1-INBOX/GH-255-test.md" \
  --raw-text "- **GH-255 · valid initial title** 🆕 — [doc](PROJECT/1-INBOX/GH-255-test.md) · [#255](https://github.com/org/repo/issues/255)"
pass "roadmap add succeeded with valid raw_text"

# -----------------------------------------------------------------------------
# Case 4: roadmap update with symmetric negative controls is REFUSED
# -----------------------------------------------------------------------------
for bad_input in \
  "- [ ] #255 bad update" \
  "-   **GH-255 · extra spaces**" \
  "-	**GH-255 · tab after dash**" \
  "- **GH-255 unclosed title" \
  "- **** empty title GH-255" \
  $'- **GH-255 · title**\n- [ ] #999 bad line' \
  $'- **GH-255 · title**\r\ncontinuation'
do
  rc=0
  out="$(app --root "$R" roadmap update --issue-num 255 --raw-text "$bad_input" 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || fail "malformed raw_text '$bad_input' on update should be refused, got rc=0"
  case "$out" in
    *"rule=invalid-raw-text"*) pass "roadmap update refused malformed raw_text: '$bad_input'" ;;
    *) fail "expected invalid-raw-text on roadmap update for '$bad_input', got: $out" ;;
  esac
done

# -----------------------------------------------------------------------------
# Case 5: roadmap update --dry-run prints changes and PROVABLY mutates nothing
# -----------------------------------------------------------------------------
raw_before="$(sqlite3 "$R/releases.db" "SELECT raw_text FROM roadmap_items WHERE gh_number = 255")"
out="$(app --root "$R" roadmap update --issue-num 255 \
  --raw-text "- **GH-255 · dry run title** 🆕 — [doc](PROJECT/1-INBOX/GH-255-test.md) · [#255](https://github.com/org/repo/issues/255)" \
  --dry-run)"
case "$out" in
  *"raw_text: "*"- **GH-255 · dry run title**"*) pass "roadmap update --dry-run reported planned diff" ;;
  *) fail "expected dry-run diff output, got: $out" ;;
esac
raw_after="$(sqlite3 "$R/releases.db" "SELECT raw_text FROM roadmap_items WHERE gh_number = 255")"
[ "$raw_before" = "$raw_after" ] || fail "dry-run must not mutate database"
pass "dry-run verified non-mutating against database"

# -----------------------------------------------------------------------------
# Case 6: roadmap update SUCCEEDS and generates roadmap-update receipt
# -----------------------------------------------------------------------------
NEW_TEXT="- **GH-255 · updated title** 🆕 — [doc](PROJECT/1-INBOX/GH-255-test.md) · [#255](https://github.com/org/repo/issues/255)"
app --root "$R" roadmap update --issue-num 255 --raw-text "$NEW_TEXT"
pass "roadmap update succeeded for GH-255"

list_out="$(app --root "$R" roadmap list --json)"
case "$list_out" in
  *"- **GH-255 · updated title**"*) pass "roadmap list reflects updated raw_text" ;;
  *) fail "roadmap list did not show updated raw_text: $list_out" ;;
esac

grep -q "roadmap-update" "$R/releases.sql" || fail "releases.sql missing roadmap-update receipt event"
pass "releases.sql carries roadmap-update receipt"

# -----------------------------------------------------------------------------
# Case 7: roadmap update is IDEMPOTENT (no-op on unchanged text)
# -----------------------------------------------------------------------------
receipt_count_before="$(grep -c "roadmap-update" "$R/releases.sql" || true)"
out="$(app --root "$R" roadmap update --issue-num 255 --raw-text "$NEW_TEXT")"
case "$out" in
  *"unchanged; nothing written"*) pass "roadmap update idempotent when text unchanged" ;;
  *) fail "expected unchanged text report, got: $out" ;;
esac
receipt_count_after="$(grep -c "roadmap-update" "$R/releases.sql" || true)"
[ "$receipt_count_before" -eq "$receipt_count_after" ] || fail "idempotent update must not write extra receipts"
pass "idempotent update wrote zero additional receipts"

# -----------------------------------------------------------------------------
# Case 8: roadmap update synchronizes ALL FIVE rating columns
# -----------------------------------------------------------------------------
# Unrated -> Rated
RATED_TEXT="- **GH-255 · rated title** 🆕 (rated 80/70/90/60 ovr 320) — [#255](https://github.com/org/repo/issues/255)"
app --root "$R" roadmap update --issue-num 255 --raw-text "$RATED_TEXT"
read pri sev app_score eff ovr <<<"$(sqlite3 "$R/releases.db" "SELECT rating_pri, rating_sev, rating_appeal, rating_effort, rating_ovr FROM roadmap_items WHERE gh_number = 255" | tr '|' ' ')"
[ "$pri" = "80" ] && [ "$sev" = "70" ] && [ "$app_score" = "90" ] && [ "$eff" = "60" ] && [ "$ovr" = "320" ] \
  || fail "expected rating columns (80 70 90 60 320), got ($pri $sev $app_score $eff $ovr)"
pass "roadmap update correctly populated all 5 rating columns"

# Rated -> Unrated (must reset all 5 rating columns to NULL, not leave old scores)
UNRATED_TEXT="- **GH-255 · unrated again** 🆕 — [#255](https://github.com/org/repo/issues/255)"
app --root "$R" roadmap update --issue-num 255 --raw-text "$UNRATED_TEXT"
cleared_counts="$(sqlite3 "$R/releases.db" "SELECT COUNT(*) FROM roadmap_items WHERE gh_number = 255 AND (rating_pri IS NOT NULL OR rating_sev IS NOT NULL OR rating_appeal IS NOT NULL OR rating_effort IS NOT NULL OR rating_ovr IS NOT NULL)")"
[ "$cleared_counts" = "0" ] || fail "expected all rating columns to be NULL, found non-null values"
pass "roadmap update correctly cleared all 5 rating columns to NULL on unrated line"

# -----------------------------------------------------------------------------
# Case 9: schema-behind refusal on pre-migration ledger without rating columns
# -----------------------------------------------------------------------------
R_OLD="$WORK/pre_migration_repo"
mkdir -p "$R_OLD/utils/py"
cp -r "$root/utils/"* "$R_OLD/utils/"
cd "$R_OLD"
git init -q .
echo "ROADMAP_SOURCE=releases" > .pdda-mode
mkdir -p PROJECT/1-INBOX
touch PROJECT/1-INBOX/GH-100-test.md
app --root "$R_OLD" init --slug "old-repo"
app --root "$R_OLD" roadmap add --issue-num 100 --issue-url "https://github.com/org/repo/issues/100" \
  --title "old 100" --created "2026-08-26" --doc-path "PROJECT/1-INBOX/GH-100-test.md" \
  --raw-text "- **GH-100 · old initial** 🆕 — [#100](https://github.com/org/repo/issues/100)"

# Simulate pre-migration schema by dropping rating columns
sqlite3 "$R_OLD/releases.db" <<'EOSQL'
CREATE TABLE roadmap_items_old AS SELECT id, global_id, repo_id, gh_number, title, section, position, status_marker, complexity, risk, effort, doc_path, issue_url, raw_text, first_seen, updated_at FROM roadmap_items;
DROP TABLE roadmap_items;
ALTER TABLE roadmap_items_old RENAME TO roadmap_items;
EOSQL

rc=0
out="$(app --root "$R_OLD" roadmap update --issue-num 100 \
  --raw-text "- **GH-100 · rated line on old ledger** 🆕 (rated 80/70/90/60) — [#100](https://github.com/org/repo/issues/100)" 2>&1)" || rc=$?
[ "$rc" -ne 0 ] || fail "rated update against pre-migration ledger should be refused, got rc=0"
case "$out" in
  *"rule=schema-behind"*) pass "roadmap update refused rated line on pre-migration ledger with schema-behind" ;;
  *) fail "expected schema-behind refusal, got: $out" ;;
esac

# -----------------------------------------------------------------------------
# Case 10: renderer (utils/roadmap-dashboard.sh) emits stderr warning on dropped rows
# -----------------------------------------------------------------------------
MOCK_SRC="$WORK/mock_roadmap.md"
cat > "$MOCK_SRC" <<'EOFMOCK'
# ROADMAP
## Ledger
### Queue / parked intake
- **GH-1 · valid row** 🟢 — [doc](doc.md)
- [ ] #999 malformed row
- #1000 another dropped bullet
- **GH-1001 unclosed bold
EOFMOCK

MOCK_OUT="$WORK/mock_dashboard.md"
err_out="$(ROADMAP_DASHBOARD_SOURCE="$MOCK_SRC" ROADMAP_DASHBOARD_OUTPUT="$MOCK_OUT" bash "$RENDERER" 2>&1 >/dev/null)" || true
case "$err_out" in
  *"roadmap-dashboard: warning: dropped 3 unparseable row(s): #999, #1000, #1001"*)
    pass "renderer warned on dropped unparseable rows (including unclosed bold) on stderr"
    ;;
  *) fail "expected warning naming dropped rows #999, #1000, #1001, got: $err_out" ;;
esac

# -----------------------------------------------------------------------------
# Case 10b (GH-474): a WELL-FORMED row under an UNRECOGNISED section heading is also
# invisible, and must also be reported.
#
# This is the second way a roadmap row goes missing, and it is nastier than a malformed one:
# the row parses perfectly. The renderer simply has no bucket for its heading, so it is never
# emitted — and because it was never emitted, a fresh render still matches the committed file
# byte-for-byte. Drift detection cannot see it and, before this case, neither could stderr.
#
# Before GH-491 the public CLI wrote sections verbatim. Legacy or bypass writers can still
# supply unknown headings, so the renderer must keep diagnosing these historical rows.
UNSEC_SRC="$WORK/mock_unknown_section.md"
cat > "$UNSEC_SRC" <<'EOFUNSEC'
# ROADMAP
## Ledger
### Queue / parked intake
- **GH-1 · valid row in a known section** 🟢 — [doc](doc.md)
### Backlog
- **GH-4741 · well-formed row nobody will ever see** 🆕
- **GH-4742 · second invisible row** 🆕
  continuation line that rides with its bullet
EOFUNSEC

UNSEC_OUT="$WORK/mock_unknown_section_out.md"
unsec_err="$(ROADMAP_DASHBOARD_SOURCE="$UNSEC_SRC" ROADMAP_DASHBOARD_OUTPUT="$UNSEC_OUT" bash "$RENDERER" 2>&1 >/dev/null)" || true
case "$unsec_err" in
  *"warning: dropped 2 row(s) under unrecognised section heading(s) \"Backlog\": #4741, #4742"*)
    pass "GH-474: renderer names rows hidden by an unrecognised section heading (continuation not double-counted)"
    ;;
  *) fail "expected an unrecognised-section warning naming #4741 and #4742, got: $unsec_err" ;;
esac
# The prefix matters as much as the content: githooks/dashboard-staleness-guard.sh refuses on
# "warning: dropped ", so this new omission mode reaches the guard without the guard changing.
case "$unsec_err" in
  *"roadmap-dashboard: warning: dropped "*) pass "GH-474: the new warning carries the prefix the push guard matches on" ;;
  *) fail "unrecognised-section warning must share the 'warning: dropped ' prefix, got: $unsec_err" ;;
esac
# Red control on the finding itself: the hidden rows really are absent from the render, and the
# known-section row really is present — so this is reporting an omission, not inventing one.
grep -q "GH-4741" "$UNSEC_OUT" && fail "GH-4741 should NOT be rendered — the fixture's premise is wrong" \
  || pass "GH-474: the unrecognised-section rows are genuinely absent from the rendered view"
grep -q "valid row in a known section" "$UNSEC_OUT" \
  && pass "GH-474: a known-section row alongside them still renders (the warning is not a blanket failure)" \
  || fail "known-section row vanished too — the fix over-reached"

# -----------------------------------------------------------------------------
# Case 11: End-to-end historical reproduction of malformed row diagnosis & fix
# -----------------------------------------------------------------------------
cd "$R"
bash "$R/utils/roadmap-dashboard.sh"
git add .pdda-mode releases.db releases.sql ROADMAP-DASHBOARD.md utils/ PROJECT/
git -c user.email=t@t -c user.name=t commit -q -m "v1 clean base"
BASE_COMMIT="$(git rev-parse HEAD)"

# Simulate the historical bug: a malformed row (- [ ] #256 ...) is directly injected into ledger
sqlite3 "$R/releases.db" <<'EOSQL'
INSERT INTO roadmap_items (global_id, repo_id, gh_number, title, section, position, status_marker, doc_path, issue_url, raw_text, first_seen, updated_at)
VALUES ('rmi-01M0ZVV0000000000000000256', 1, 256, 'bad 256', 'Queue / parked intake', 99, '🆕', 'PROJECT/1-INBOX/GH-255-test.md', 'https://github.com/org/repo/issues/256', '- [ ] #256 historical malformed row', datetime('now'), datetime('now'));
EOSQL
python3 -c "import sys; sys.path.insert(0, '$root/utils/py'); import releases_app as rel; root = rel.resolve_root('$R'); conn = rel.connect(rel.artifact_paths(root)['db']); gen = rel.get_generation(conn); open(rel.artifact_paths(root)['dump'], 'w').write(rel.dump_text(conn, gen)); conn.close()"

# 1. Regenerating dashboard yields warnings and dropped row:
dash_warn="$(bash "$R/utils/roadmap-dashboard.sh" 2>&1 >/dev/null)" || true
case "$dash_warn" in
  *"warning: dropped 1 unparseable row(s): #256"*) pass "end-to-end: renderer detected injected malformed row #256" ;;
  *) fail "expected dropped row warning for #256, got: $dash_warn" ;;
esac

# 2. Commit the ledger change only (dashboard unchanged because row was dropped)
git add releases.db releases.sql
git -c user.email=t@t -c user.name=t commit -q -m "ledger has bad row #256, dashboard unchanged"
BAD_COMMIT="$(git rev-parse HEAD)"
cd "$root"

# 3. Staleness guard catches it and outputs no-diff diagnosis:
# Add uncommitted modification in working tree to PROVE guard is isolated to commit projection
echo "dirty working tree modification" >> "$R/ROADMAP-DASHBOARD.md"

GUARD_TMP="$WORK/guard_isolated_tmp"
mkdir -p "$GUARD_TMP"

rc=0
guard_out="$(TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$BAD_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "guard should refuse bad commit, got $rc"
case "$guard_out" in
  *"produces NO diff (GH-243 / GH-257)"*"releases roadmap update"*)
    pass "end-to-end: staleness guard accurately diagnosed no-diff dropped row (even with dirty working tree)"
    ;;
  *) fail "expected no-diff diagnostic output from guard, got: $guard_out" ;;
esac
# GH-474: the guard reads the RENDERER's dropped-row warning rather than inferring it from table
# names, and the renderer here is the real one, reached through the guard's `git archive`
# projection. Asserting the row id proves the signal survives that projection — if it did not,
# the guard would fall through to "allow" and this case would go red instead of quietly passing
# for the wrong reason. This is the runnable check the #474 recon listed as its one unknown.
case "$guard_out" in
  *"dropped 1 unparseable row(s): #256"*)
    pass "GH-474: refusal names the dropped row, so the renderer's warning survived the projection"
    ;;
  *) fail "expected the guard to name dropped row #256 from the renderer's own stderr, got: $guard_out" ;;
esac
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] || fail "expected no leftover guard roots in GUARD_TMP after no-diff refusal"
pass "guard cleaned up temporary root after no-diff refusal"

# Restore working tree
git -C "$R" checkout ROADMAP-DASHBOARD.md

# 4. Multi-ref push test with BAD_COMMIT FIRST and clean BASE_COMMIT LAST
# Proves per-ref evaluation does not merely inspect the last ref in the list
rc=0
guard_multi_out="$(TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$BAD_COMMIT" "$BASE_COMMIT" "$BASE_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "guard should refuse multi-ref push with bad commit first, got $rc"
case "$guard_multi_out" in
  *"produces NO diff (GH-243 / GH-257)"*)
    pass "end-to-end: multi-ref push correctly evaluates bad ref first and clean ref last"
    ;;
  *) fail "expected no-diff refusal in multi-ref push, got: $guard_multi_out" ;;
esac
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] || fail "expected no leftover guard roots in GUARD_TMP after multi-ref refusal"
pass "guard cleaned up temporary root after multi-ref refusal"

# Cross-ref test: Ref 1 touches ledger only (BAD_COMMIT), Ref 2 touches dashboard only
cd "$R"
git checkout -q -b branch-dash-only "$BASE_COMMIT"
echo "# modified dashboard" >> ROADMAP-DASHBOARD.md
git add ROADMAP-DASHBOARD.md
git -c user.email=t@t -c user.name=t commit -q -m "dashboard only commit"
DASH_ONLY_COMMIT="$(git rev-parse HEAD)"
git checkout -q -
cd "$root"

rc=0
guard_cross_out="$(TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$BAD_COMMIT" "$BASE_COMMIT" "$DASH_ONLY_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "cross-ref push should refuse bad ledger ref despite separate dashboard ref, got $rc"
case "$guard_cross_out" in
  *"produces NO diff (GH-243 / GH-257)"*)
    pass "end-to-end: cross-ref push enforces per-ref consistency and refuses stale ledger ref"
    ;;
  *) fail "expected refusal on cross-ref push, got: $guard_cross_out" ;;
esac
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] || fail "expected no leftover guard roots in GUARD_TMP after cross-ref refusal"
pass "guard cleaned up temporary root after cross-ref refusal"

# 5. Projection failure test:
# Create a commit where ledger is touched, but utils/roadmap-dashboard.sh is missing from that commit.
# The projection fails to run the script and must fail closed (drift_detected=1), refusing the push
# and cleaning up temporary directory without consulting working tree.
cd "$R"
git checkout -q -b branch-proj-fail "$BAD_COMMIT"
git rm -q utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "commit without renderer script"
PROJ_FAIL_COMMIT="$(git rev-parse HEAD)"
git checkout -q -
cd "$root"

rc=0
guard_fail_out="$(TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$PROJ_FAIL_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "guard should refuse when commit projection fails renderer lookup, got $rc"
case "$guard_fail_out" in
  *"without regenerating ROADMAP-DASHBOARD.md"*)
    pass "end-to-end: projection failure fails closed as drift and refuses without working tree fallback"
    ;;
  *) fail "expected drift refusal on projection failure, got: $guard_fail_out" ;;
esac
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] || fail "expected no leftover guard roots in GUARD_TMP after projection failure refusal"
pass "guard cleaned up temporary root after projection failure refusal"

# 6. Hostile root pivot/rename test:
# Create a commit where roadmap-dashboard.sh tries to replace the guard root with a symlink to VICTIM_DIR
VICTIM_DIR="$WORK/victim_dir"
mkdir -p "$VICTIM_DIR"
touch "$VICTIM_DIR/important_file"

cd "$R"
git checkout -q -b branch-hostile-pivot "$BAD_COMMIT"
cat > utils/roadmap-dashboard.sh <<'EOFPIVOT'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD_ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
rm -rf "$GUARD_ROOT_DIR" 2>/dev/null || true
ln -s "$VICTIM_DIR" "$GUARD_ROOT_DIR" 2>/dev/null || true
exit 0
EOFPIVOT
chmod +x utils/roadmap-dashboard.sh
git add utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "commit with hostile pivot script"
PIVOT_COMMIT="$(git rev-parse HEAD)"
git checkout -q "$BASE_COMMIT"
cd "$root"

rc=0
guard_pivot_out="$(TMPDIR="$GUARD_TMP" VICTIM_DIR="$VICTIM_DIR" bash "$GUARD" "$R" "$PIVOT_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "guard should refuse on pivot attempt, got $rc"
[ -f "$VICTIM_DIR/important_file" ] || fail "hostile pivot must not delete victim files"
pass "end-to-end: hostile root symlink pivot safely refused and protected external directories"

rm -rf "$GUARD_TMP"/staleness-guard.* 2>/dev/null || true

# 7. Hostile root rename replacement test (directory swap / inode mismatch):
# Create a commit where roadmap-dashboard.sh moves guard root aside and replaces it with a new real directory
VICTIM_DIR2="$WORK/victim_dir2"
mkdir -p "$VICTIM_DIR2"
touch "$VICTIM_DIR2/safe_file"

cd "$R"
git checkout -q -b branch-hostile-rename "$BAD_COMMIT"
cat > utils/roadmap-dashboard.sh <<'EOFRENAME'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD_ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
mv "$GUARD_ROOT_DIR" "$GUARD_ROOT_DIR.aside" 2>/dev/null || true
mv "$VICTIM_DIR2" "$GUARD_ROOT_DIR" 2>/dev/null || true
exit 0
EOFRENAME
chmod +x utils/roadmap-dashboard.sh
git add utils/roadmap-dashboard.sh
git -c user.email=t@t -c user.name=t commit -q -m "commit with hostile rename script"
RENAME_COMMIT="$(git rev-parse HEAD)"
git checkout -q "$BASE_COMMIT"
cd "$root"

rc=0
guard_rename_out="$(TMPDIR="$GUARD_TMP" VICTIM_DIR2="$VICTIM_DIR2" bash "$GUARD" "$R" "$RENAME_COMMIT" "$BASE_COMMIT" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "guard should refuse on rename attempt, got $rc"
case "$guard_rename_out" in
  *"identity mismatch"*) pass "end-to-end: hostile directory rename detected by device/inode mismatch" ;;
  *) fail "expected identity mismatch refusal, got: $guard_rename_out" ;;
esac

# Prove victim file was NOT deleted by the guard (it is preserved in the refused root)
# SC2144: -f does not work with a glob -- the shell expands it to N words and `[` sees too many
# arguments (or, with no match, tests the literal pattern). Iterate the expansion instead.
victim_preserved=0
for _safe in "$GUARD_TMP"/staleness-guard.*/safe_file; do
  if [ -f "$_safe" ]; then victim_preserved=1; break; fi
done
[ "$victim_preserved" -eq 1 ] || fail "victim file was deleted by guard"
pass "end-to-end: victim directory preserved and undeleted during hostile rename replacement attempt"

rm -rf "$GUARD_TMP"/staleness-guard.* "$GUARD_TMP"/staleness-guard.*.aside 2>/dev/null || true

# 8. Remediation: use roadmap update to fix raw_text
cd "$R"
git checkout -q "$BAD_COMMIT"
app --root "$R" roadmap update --issue-num 256 --raw-text "- **GH-256 · fixed title** 🆕 — [#256](https://github.com/org/repo/issues/256)"
bash "$R/utils/roadmap-dashboard.sh"
grep -q "GH-256 · fixed title" "$R/ROADMAP-DASHBOARD.md" || fail "remediated row not in dashboard"
pass "end-to-end: roadmap update remediated row and dashboard now includes it"

git add releases.db releases.sql ROADMAP-DASHBOARD.md
git -c user.email=t@t -c user.name=t commit -q -m "remediated row #256 and regenerated dashboard"
REMEDIATED_COMMIT="$(git rev-parse HEAD)"
cd "$root"

# 8. Staleness guard now passes cleanly and leaves no temporary files:
GITHUB_ACTIONS=true TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$REMEDIATED_COMMIT" "$BASE_COMMIT"
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] || fail "expected no leftover guard roots in GUARD_TMP after clean pass"
pass "end-to-end: staleness guard passes after roadmap update and leaves 0 temporary artifacts"

# -----------------------------------------------------------------------------
# Case 12 (GH-474): END-TO-END — a row hidden by an unrecognised section is REFUSED by the
# push guard, through the real renderer and the real git-archive projection.
#
# WHY THIS CASE EXISTS. GH-474 replaced the guard's table-name classifier with "ask the
# renderer". A cross-model review then falsified the premise behind that: "the renderer said
# nothing" did NOT mean "every row rendered", because a row under an unrecognised heading was
# skipped in silence. That was a FAIL-OPEN regression — the old classifier's catch-all refused
# this exact range, and the first version of the new guard allowed it.
#
# Case 10b proves the renderer now reports it. This proves the whole chain does: real ledger
# write -> real renderer -> git archive projection -> guard refusal naming the row.
cd "$R"
git checkout -q "$REMEDIATED_COMMIT"
CLEAN_BASE="$(git rev-parse HEAD)"

# The hazard is a row that lands in an unrecognised section and was NEVER visible. (MOVING an
# already-rendered row out of a known section does change the dashboard, so ordinary drift
# detection catches that one — measured while writing this case, and the reason it is worded
# this way.) Both steps run before a single regeneration, so the row never appears in the view.
# GH-491 now refuses this through the CLI. Inject historical corruption directly, as in case 11.
app --root "$R" roadmap add --issue-num 4741 \
  --issue-url "https://github.com/org/repo/issues/4741" --title "hidden row" \
  --created "2026-09-07" --doc-path "PROJECT/1-INBOX/GH-255-test.md" \
  --raw-text "- **GH-4741 · well-formed row nobody will ever see** 🆕" >/dev/null
require_fixture "$R" "historical-section ledger"
python3 - "$root/utils/py/releases_app.py" "$R" <<'PYHIDDEN'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("releases_app", sys.argv[1])
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)
paths = rel.artifact_paths(sys.argv[2])
conn = rel.connect(paths["db"])
conn.execute("UPDATE roadmap_items SET section = 'Backlog' WHERE gh_number = 4741")
conn.commit()
with open(paths["dump"], "w") as fh:
    fh.write(rel.dump_text(conn, rel.get_generation(conn)))
conn.close()
PYHIDDEN
bash "$R/utils/roadmap-dashboard.sh" >/dev/null 2>&1 || true

# THE PREMISE: the dashboard is byte-identical, which is exactly what makes this invisible to
# drift detection and why the guard needs a signal rather than a comparison.
if git diff --quiet -I '^<!-- releases-app generation:' -- ROADMAP-DASHBOARD.md; then
  pass "GH-474 e2e: a row added into an unrecognised section leaves the dashboard byte-identical"
else
  fail "fixture premise wrong: the hidden row changed the dashboard, so drift detection would already catch it"
fi

git add releases.db releases.sql
git -c user.email=t@t -c user.name=t commit -q -m "ledger gains #4741 in an unrecognised section; dashboard unchanged"
HIDDEN_COMMIT="$(git rev-parse HEAD)"
cd "$root"

rc=0
hidden_out="$(TMPDIR="$GUARD_TMP" bash "$GUARD" "$R" "$HIDDEN_COMMIT" "$CLEAN_BASE" 2>&1)" || rc=$?
[ "$rc" -eq 1 ] || fail "GH-474 e2e: guard must REFUSE a range that hides a row in an unrecognised section, got rc=$rc: $hidden_out"
pass "GH-474 e2e: guard refuses the range (fail-closed restored)"
case "$hidden_out" in
  *"unrecognised section heading"*"#4741"*)
    pass "GH-474 e2e: the refusal names the heading and the row, through the real projection"
    ;;
  *) fail "expected the refusal to name the unrecognised heading and #4741, got: $hidden_out" ;;
esac
[ "$(find "$GUARD_TMP" -maxdepth 1 -name "staleness-guard.*" | wc -l)" -eq 0 ] \
  || fail "expected no leftover guard roots after the unrecognised-section refusal"
pass "GH-474 e2e: guard cleaned up its temporary root"

echo "== GH-257 ALL PASSED =="
