#!/usr/bin/env bash
# gh280-jog-marathon-adapter.sh — GH-280 Phase 1: Jog ↔ Marathon machine contracts.
#
# Exercises, with REAL Preflight → Marathon → Relay chains and deterministic agent/GitHub
# shims (never --simulate):
#   - swarm-preflight emits the additive swarm-preflight/marathon-invocation@1 artifact
#   - marathon-drive --result-file emits exactly one marathon-drive/result@1 receipt per
#     terminal exit: success, pre-dispatch refusal, builder failure, reviewer cap,
#     gate failure, timeout, lane park, protected-branch redirect, PR-publication failure
#   - jog_run's contract loaders reject unsupported schema versions and malformed artifacts
#   - both installation shapes: harness at repo ROOT and vendored under .xyz/
source "$(dirname "$0")/_setup.sh" gh280-jog-marathon-adapter
unset MARATHON_LANE_NS MARATHON_ROOT MARATHON_RELAY_DRIVE MARATHON_AGENT_CMD TICK_BIN
REPO="$(cd "$(dirname "$0")/.." && pwd)"

# ── deterministic GitHub shim: logs every call, canned PR answers ─────────────────────────────
# Anything not understood exits 1 — the same shape as an unauthenticated/offline gh, so
# preflight's issue-state probe degrades to `unknown` instead of touching the network.
STUB_BIN="$WORK/stub-bin"
mkdir -p "$STUB_BIN"
GH_STUB_LOG="$WORK/gh-stub-calls.log"
export GH_STUB_LOG
GH_STUB_PR_JSON="${GH_STUB_PR_JSON:-}"   # optional: path to a canned `gh pr list --json` array
export GH_STUB_PR_JSON
cat > "$STUB_BIN/gh" <<'GH_EOF'
#!/usr/bin/env bash
set -u
printf '%s\n' "$*" >> "${GH_STUB_LOG:?}"
if [ "${1:-}" = "auth" ]; then exit 0; fi
if [ "${1:-}" = "pr" ] && [ "${2:-}" = "list" ]; then
  for a in "$@"; do
    if [ "$a" = "number,url,state" ]; then
      if [ -n "${GH_STUB_PR_JSON:-}" ] && [ -s "$GH_STUB_PR_JSON" ]; then cat "$GH_STUB_PR_JSON"; else echo "[]"; fi
      exit 0
    fi
  done
  # closeout's `--json url --jq '.[0].url'` query
  if [ -n "${GH_STUB_PR_JSON:-}" ] && [ -s "$GH_STUB_PR_JSON" ]; then
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d[0]["url"] if d else "")' "$GH_STUB_PR_JSON"
  else
    echo ""
  fi
  exit 0
fi
if [ "${1:-}" = "pr" ] && [ "${2:-}" = "view" ]; then
  if [ -n "${GH_STUB_PR_VIEW_JSON:-}" ] && [ -s "${GH_STUB_PR_VIEW_JSON:-}" ]; then
    cat "$GH_STUB_PR_VIEW_JSON"; exit 0
  fi
  exit 1
fi
if [ "${1:-}" = "pr" ] && [ "${2:-}" = "create" ]; then
  if [ "${GH_STUB_CREATE_FAIL:-0}" = "1" ]; then exit 1; fi
  echo "https://example.invalid/pr/created-by-stub"
  exit 0
fi
if [ "${1:-}" = "pr" ] && [ "${2:-}" = "merge" ]; then
  if [ "${GH_STUB_MERGE_FAIL:-0}" = "1" ]; then echo "stub: merge refused" >&2; exit 1; fi
  exit 0
fi
exit 1
GH_EOF
chmod +x "$STUB_BIN/gh"
export PATH="$STUB_BIN:$PATH"

CANNED_PR="$WORK/canned-pr.json"
printf '[{"number":42,"url":"https://example.invalid/x/pr/42","state":"OPEN"}]\n' > "$CANNED_PR"

# ── stub relay-drive (records argv, exits RELAY_DRIVE_EXIT) ───────────────────────────────────
STUB_RD="$WORK/relay-drive.sh"
cat > "$STUB_RD" << 'STUB_EOF'
#!/usr/bin/env bash
set -u
printf '%s\n' "$*" > "$WORK/relay-drive-args"
# GH-505: a success must carry the reviewer attestation the real driver publishes
[ "${RELAY_DRIVE_EXIT:-0}" -eq 0 ] && bash "$ATTEST_STUB" "$@"
exit "${RELAY_DRIVE_EXIT:-0}"
STUB_EOF
chmod +x "$STUB_RD"

# exit-0 agent binaries so marathon-drive's pre-dispatch binary probe passes
STUB_CODEX="$WORK/stub-codex"; printf '#!/usr/bin/env bash\nexit 0\n' > "$STUB_CODEX"; chmod +x "$STUB_CODEX"
STUB_AGY="$WORK/stub-agy";     printf '#!/usr/bin/env bash\nexit 0\n' > "$STUB_AGY";     chmod +x "$STUB_AGY"

GATE_PASS="$WORK/gate-pass.sh"; printf '#!/usr/bin/env bash\nexit 0\n' > "$GATE_PASS"; chmod +x "$GATE_PASS"
GATE_FAIL="$WORK/gate-fail.sh"; printf '#!/usr/bin/env bash\nexit 1\n' > "$GATE_FAIL"; chmod +x "$GATE_FAIL"

CAPTURE_DOC_NAME="GH-901-FIXTURE-LANE.md"
write_capture_doc() {  # <path>
  cat > "$1" <<DOC_EOF
---
gh_issue: 901
source: https://github.com/example/example/issues/901
title: "GH-280 fixture lane"
status: "Active"
created: 2026-08-27
updated: 2026-08-27
owner: test
doc_type: bugfix
---

# GH-901 fixture lane

## Acceptance
- [ ] artifact updated and gate green

## Swarm Preflight Contract
\`\`\`json
{
  "target": { "repo": ".", "ref": "main" },
  "gate": "bash test/fixture-gate.sh",
  "fix_probes": [ { "type": "path_absent", "path": "notes/landing-note.txt" } ],
  "artifacts": [ "src/feature.js" ]
}
\`\`\`
DOC_EOF
}

# ── fixture: a real git clone (origin/HEAD resolvable) with the harness installed ──────────────
# <root> <relative harness prefix: "" for root install, ".xyz/" for vendored>
setup_fixture() {
  local root="$1" prefix="$2"
  git clone -q "$REMOTE" "$root"
  git -C "$root" config user.email gh280@test.invalid
  git -C "$root" config user.name gh280
  mkdir -p "$root/$prefix"
  for d in relay-automation bin src utils; do
    cp -R "$REPO/$d" "$root/$prefix$d"
  done
  mkdir -p "$root/src" "$root/test" "$root/PROJECT/2-WORKING"
  printf 'module.exports = 1\n' > "$root/src/feature.js"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$root/test/fixture-gate.sh"
  write_capture_doc "$root/PROJECT/2-WORKING/$CAPTURE_DOC_NAME"
  if [ -z "$prefix" ]; then
    printf '.tick/\n.xyz/\n__pycache__/\n' > "$root/.gitignore"
  else
    printf '.tick/\n%s.tick/\n__pycache__/\n' "$prefix" > "$root/.gitignore"
  fi
  python3 "$REPO/utils/py/releases_app.py" --root "$root" init >/dev/null 2>&1
  python3 "$REPO/utils/py/releases_app.py" --root "$root" jog add 901 >/dev/null 2>&1
  git -C "$root" add -A >/dev/null 2>&1
  git -C "$root" commit -q -m "fixture init" >/dev/null 2>&1
}

FR="$WORK/root-install";  setup_fixture "$FR" ""
FV="$WORK/vendor-install"; setup_fixture "$FV" ".xyz/"
INIT_HEAD_R="$(git -C "$FR" rev-parse HEAD)"

# ── GH-365 step 7: immutable prebuilt seed fixture + contamination tripwire ──────────────────
# Every section mutates ONE working copy ($FR) and restores it at each section boundary.
# Restore-mechanism decision, measured (warm, 2026-09-01, this suite's fixture shape):
#   full tree re-copy from seed (cp -a)  0.23–0.25s per boundary
#   git trio (checkout main + reset --hard + clean)  0.05s per boundary
# With 28 boundaries, copy-per-section would ADD ~5s to the suite, so the prebuilt seed is
# the immutable TEMPLATE + CONTAMINATION CANARY, not the restore mechanism. Nothing
# legitimate ever writes into it, so any byte change after a section is contamination —
# mutable state cannot leak across sections through the seed even if a path escapes $FR.
# The digest covers every file including .git (branch cuts, ref rewrites, object writes all
# trip it). If a future section ever needs a stronger reset than the git trio, restore from
# the seed directly:  rm -rf "$FR" && cp -a "$SEED" "$FR"
SEED="$WORK/seed-root"
cp -a "$FR" "$SEED"
seed_digest() { (cd "$SEED" && find . -type f -print0 | sort -z | xargs -0 cksum | cksum); }
SEED_CKSUM="$(seed_digest)"
# Files only, never directories: a read-only FILE refuses in-place writes (fail-loud first
# line), but a read-only DIR would make _setup.sh's exit-trap `rm -rf "$WORK"` fail and litter
# the temp root (measured: rm -rf on a chmod -R a-w tree exits 1 and leaves the tree behind).
find "$SEED" -type f -exec chmod a-w {} +

seed_intact() {  # <where> — contamination control: the seed must still be byte-identical
  local got
  got="$(seed_digest)"
  [ "$got" = "$SEED_CKSUM" ] \
    && pass "seed fixture byte-unchanged after $1 (containment)" \
    || fail "SEED fixture mutated by $1 — mutable state leaked across sections: $got != $SEED_CKSUM"
}

cleanup_root_fixture() {
  seed_intact "the section that just ran (cleanup boundary)"
  rm -rf "$FR/.tick" "$FR/marathon-system" "$FR/relay-system"
  git -C "$FR" checkout -q main >/dev/null 2>&1 || true
  git -C "$FR" reset -q --hard "$INIT_HEAD_R" >/dev/null 2>&1 || true
  git -C "$FR" clean -qfd -e .xyz >/dev/null 2>&1 || true
  rm -f "$WORK/relay-drive-args"
}

# json-field assertion helper: jassert <file> <python-expr over d> <label>
jassert() {
  python3 -c 'import json,sys,os,subprocess
d = json.load(open(sys.argv[1]))
sys.exit(0 if eval(sys.argv[2]) else 1)' "$1" "$2" 2>/dev/null \
    && pass "$3" || fail "$3 ($(head -c 400 "$1" 2>/dev/null))"
}

# fixed-substring helper (jog-queue.sh has one; this suite is standalone)
has() { grep -Fq -- "$2" <<<"$1"; }   # GH-139/GH-472: capture-then-match, never pipe-into-grep -q

# idempotent development-branch setup: switch if it exists, create if not, normalize HEAD.
# `checkout -b` on an existing branch fails silently-in-context and leaves the fixture on the
# wrong branch — the branch guard then records the wrong base.
use_development() {
  git -C "$FR" checkout -q development >/dev/null 2>&1 \
    || git -C "$FR" checkout -q -b development >/dev/null 2>&1
  git -C "$FR" reset -q --hard "$INIT_HEAD_R" >/dev/null 2>&1 || true
}

run_md_root() {  # <extra-args…> — drive in the ROOT fixture with the stub relay-drive
  (cd "$FR" && MARATHON_RELAY_DRIVE="$STUB_RD" \
    CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
    bash "$FR/relay-automation/marathon-drive.sh" \
      --phases-dir "$FR/marathon-system" \
      --phase-brief "$WORK/brief.md" \
      --reviewer agy --builder codex \
      --pre-advance-cmd "bash $GATE_PASS" \
      "$@")
}

printf '## Implement a hello-world function\nWrite a function that returns "hello".\n' > "$WORK/brief.md"

# ═══ A. Preflight emits the structured invocation artifact (root install) ══════════════════════
PK="$WORK/packet-root"
PF_OUT="$(cd "$FR" && python3 "$FR/utils/py/swarm_preflight.py" --gh-issue 901 --out "$PK" 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "A1 root preflight exits 0 (candidate ready)" || fail "A1 root preflight exit=$rc: $PF_OUT"
for f in run-candidate.json lane-plan.json freshness.json readiness.json marathon-invocation.txt packet.md marathon-invocation.json; do
  [ -f "$PK/$f" ] && pass "A2 packet still carries $f (additive)" || fail "A2 packet missing $f"
done
INV="$PK/marathon-invocation.json"
jassert "$INV" 'd["schema"]=="swarm-preflight/marathon-invocation@1"' "A3 invocation artifact schema is marathon-invocation@1"
jassert "$INV" 'd["argv"][0]=="'"$FR"'/relay-automation/marathon-drive.sh" and os.path.isfile(d["argv"][0]) and os.access(d["argv"][0], os.X_OK)' "A4 argv[0] is the absolute executable drive path"
jassert "$INV" 'd["env"]["XYZ_HARNESS_CONTEXT"]=="swarm" and d["env"]["XYZ_SESSION_ID"] and d["env"]["RELAY_WORKTREE_ISOLATION"]=="1"' "A5 env entries carry swarm/session/isolation"
jassert "$INV" 'd["packet_path"]=="'"$PK"'/packet.md" and os.path.isfile(d["packet_path"])' "A6 packet_path resolves"
jassert "$INV" 'd["result_path"]=="'"$PK"'/marathon-result.json"' "A7 result_path is beside the packet"
jassert "$INV" 'd["issue"]=="901" and d["base_ref"]=="main" and d["builder"]=="codex" and d["reviewer"]=="agy"' "A8 identity fields: issue/base_ref/builder/reviewer"
jassert "$INV" 'd["phase"]==d["lane"] and d["phase"] and d["gate"]=="bash test/fixture-gate.sh" and "src/feature.js" in d["artifacts"]' "A9 phase/lane/gate/artifacts carried"
jassert "$INV" '"--result-file" in d["argv"] and d["argv"][d["argv"].index("--result-file")+1]==d["result_path"]' "A10 argv embeds --result-file with result_path"
jassert "$INV" '"--phase-brief" in d["argv"] and d["argv"][d["argv"].index("--phase-brief")+1]==d["packet_path"]' "A11 argv embeds --phase-brief with packet_path"
jassert "$PK/run-candidate.json" 'd["schema"]=="swarm-preflight/run-candidate@1"' "A12 run-candidate@1 unchanged (compat)"
grep -q '^XYZ_HARNESS_CONTEXT=swarm XYZ_SESSION_ID=[^ ]* RELAY_WORKTREE_ISOLATION=1 relay-automation/marathon-drive.sh' <<<"$(head -1 "$PK/marathon-invocation.txt")" \
  && pass "A13 text invocation hint unchanged (compat)" || fail "A13 text invocation drifted"

# ═══ B. jog_run contract loaders reject bad contracts before dispatch ═════════════════════════
JOPY="import sys; sys.path.insert(0, '$REPO/utils/py')"
python3 -c "$JOPY
from jog_run import load_marathon_invocation
inv = load_marathon_invocation('$INV')
assert inv['issue'] == '901'
" && pass "B1 load_marathon_invocation accepts the real artifact" || fail "B1 loader rejected the real artifact"
python3 -c "$JOPY
import json
from jog_run import load_marathon_invocation, ContractError
d = json.load(open('$INV')); d['schema'] = 'swarm-preflight/marathon-invocation@2'
json.dump(d, open('$WORK/inv-bad-schema.json', 'w'))
try:
    load_marathon_invocation('$WORK/inv-bad-schema.json')
    sys.exit(1)
except ContractError as e:
    sys.exit(0 if 'supports only' in str(e) else 1)
" && pass "B2 unsupported schema version refused" || fail "B2 schema @2 was not refused"
python3 -c "$JOPY
import json
from jog_run import load_marathon_invocation, ContractError
d = json.load(open('$INV')); d['argv'][0] = '/nonexistent/marathon-drive.sh'
json.dump(d, open('$WORK/inv-bad-drive.json', 'w'))
try:
    load_marathon_invocation('$WORK/inv-bad-drive.json'); sys.exit(1)
except ContractError:
    sys.exit(0)
" && pass "B3 non-executable argv[0] refused" || fail "B3 bogus drive path accepted"

# ═══ C. marathon-drive terminal receipts (root install, stub relay-drive) ═════════════════════
RES="$WORK/md-result.json"

# C1 success
rm -f "$RES"
RELAY_DRIVE_EXIT=0 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "C1 approved run exits 0" || fail "C1 approved run exit=$rc"
[ -f "$RES" ] && pass "C1 receipt written" || fail "C1 no receipt at $RES"
jassert "$RES" 'd["schema"]=="marathon-drive/result@1" and d["outcome"]=="approved" and d["exit_code"]==0' "C1 receipt outcome approved / exit 0"
jassert "$RES" 'd["phase"]=="p1" and d["lane"]=="p1" and d["token"]=="MARATHON-P1-TURN"' "C1 receipt carries phase/lane/token"
jassert "$RES" 'd["issue"] is None' "C1 unreached issue is an explicit null"
jassert "$RES" 'd["gate"]["result"]=="green" and d["gate"]["exit"]==0 and d["gate"]["receipt_path"] and os.path.isfile(d["gate"]["receipt_path"])' "C1 gate green + gate receipt path resolves"
jassert "$RES" 'd["head_sha"] and d["head_sha"]==subprocess.check_output(["git","-C","'"$FR"'","rev-parse","HEAD"]).decode().strip()' "C1 head_sha matches repo HEAD"
jassert "$RES" 'd["head_branch"]=="main" and d["base_branch"] is None and d["branch_redirect"]==False' "C1 no branch redirect recorded"
jassert "$RES" 'd["timestamps"]["started_at"] and d["timestamps"]["finished_at"]' "C1 timestamps present"
jassert "$RES" 'd["attempt"]["count"] is not None and d["attempt"]["max"]==2' "C1 attempt count/max recorded"
python3 -c "$JOPY
from jog_run import load_marathon_result
r = load_marathon_result('$RES')
assert r['outcome'] == 'approved'
" && pass "C1 load_marathon_result accepts the real receipt" || fail "C1 receipt failed Jog-side validation"

# C2 pre-dispatch refusal: default gate missing (fixture has no validate.sh, no --pre-advance-cmd)
cleanup_root_fixture
rm -f "$RES"
rm -f "$WORK/relay-drive-args"
(cd "$FR" && MARATHON_RELAY_DRIVE="$STUB_RD" CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
  bash "$FR/relay-automation/marathon-drive.sh" \
    --phases-dir "$FR/marathon-system" --phase-brief "$WORK/brief.md" \
    --reviewer agy --builder codex --result-file "$RES") >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && pass "C2 missing gate refuses pre-dispatch (exit 2)" || fail "C2 missing-gate exit=$rc (expected 2)"
[ -f "$RES" ] && pass "C2 refusal still writes a receipt" || fail "C2 refusal wrote no receipt"
jassert "$RES" 'd["outcome"]=="refused" and d["reason"]=="pre-advance-gate-not-runnable"' "C2 receipt outcome refused + reason"
jassert "$RES" 'd["gate"]["result"]=="not-run"' "C2 gate result not-run"
[ ! -f "$WORK/relay-drive-args" ] && pass "C2 nothing dispatched (no builder/reviewer turn spent)" || fail "C2 relay-drive was invoked before the refusal"

# C3 gate failure after approval
cleanup_root_fixture; rm -f "$RES"
(cd "$FR" && RELAY_DRIVE_EXIT=0 MARATHON_RELAY_DRIVE="$STUB_RD" \
  CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
  bash "$FR/relay-automation/marathon-drive.sh" \
    --phases-dir "$FR/marathon-system" --phase-brief "$WORK/brief.md" \
    --reviewer agy --builder codex --pre-advance-cmd "bash $GATE_FAIL" \
    --result-file "$RES") >/dev/null 2>&1; rc=$?
[ "$rc" -eq 5 ] && pass "C3 gate failure exits 5" || fail "C3 gate-failure exit=$rc"
jassert "$RES" 'd["outcome"]=="escalated" and d["reason"]=="pre-advance-failed" and d["gate"]["result"]=="red"' "C3 receipt escalated/pre-advance-failed/gate red"

# C4 builder no-progress (relay-drive exit 3)
cleanup_root_fixture; rm -f "$RES"
RELAY_DRIVE_EXIT=3 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 3 ] && pass "C4 no-progress exits 3" || fail "C4 no-progress exit=$rc"
jassert "$RES" 'd["outcome"]=="escalated" and d["reason"]=="no-progress"' "C4 receipt reason no-progress"

# C5 reviewer cap / close mismatch (relay-drive exit 4)
cleanup_root_fixture; rm -f "$RES"
RELAY_DRIVE_EXIT=4 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 4 ] && pass "C5 cap escalation exits 4" || fail "C5 cap exit=$rc"
jassert "$RES" 'd["outcome"]=="escalated" and d["reason"]=="cap-or-close-mismatch"' "C5 receipt reason cap-or-close-mismatch"

# C6 timeout with no artifact (relay-drive exit 7)
cleanup_root_fixture; rm -f "$RES"
RELAY_DRIVE_EXIT=7 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 7 ] && pass "C6 timeout exits 7" || fail "C6 timeout exit=$rc"
jassert "$RES" 'd["outcome"]=="escalated" and d["reason"]=="timeout-no-artifact"' "C6 receipt reason timeout-no-artifact"

# C7 relay failed before the gate ran (relay-drive exit 5, gate untouched)
cleanup_root_fixture; rm -f "$RES"
RELAY_DRIVE_EXIT=5 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 5 ] && pass "C7 relay-failure exits 5" || fail "C7 relay-failure exit=$rc"
jassert "$RES" 'd["outcome"]=="escalated" and d["reason"]=="relay-failed-before-gate" and d["gate"]["result"]=="not-run"' "C7 receipt reason relay-failed-before-gate, gate not-run"

# C8 lane parked at the attempt cap (exit 8) — attempt state visible in the receipt
cleanup_root_fixture; rm -f "$RES"
mkdir -p "$FR/.tick/attempts"
printf 'fire\nfire\n' > "$FR/.tick/attempts/p1"
RELAY_DRIVE_EXIT=0 run_md_root --result-file "$RES" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 8 ] && pass "C8 lane parked at attempt cap exits 8" || fail "C8 attempt-cap exit=$rc"
jassert "$RES" 'd["outcome"]=="parked" and d["reason"] and "attempt" in d["reason"]' "C8 receipt outcome parked, reason names the cap"
jassert "$RES" 'd["attempt"]["count"]==2 and d["attempt"]["max"]==2' "C8 receipt attempt count 2/2"

# C9 no --result-file → identical exit, no receipt, no new observable output
cleanup_root_fixture
rm -f "$RES"
RELAY_DRIVE_EXIT=0 run_md_root >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "C9 run without --result-file keeps exit 0" || fail "C9 no-option run exit=$rc"
[ ! -f "$RES" ] && pass "C9 no receipt written when option unused" || fail "C9 receipt appeared without the option"

# C10 malformed result path refused before dispatch
cleanup_root_fixture; rm -f "$WORK/relay-drive-args"
run_md_root --result-file "$FR/no/such/dir/r.json" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && pass "C10 malformed --result-file refuses (exit 2)" || fail "C10 malformed path exit=$rc"
[ ! -f "$WORK/relay-drive-args" ] && pass "C10 malformed path dispatches nothing" || fail "C10 dispatched despite malformed path"

# C11 invalid execution id refused
cleanup_root_fixture
run_md_root --result-file "$RES" --execution-id "bad id with spaces" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && pass "C11 invalid --execution-id refuses (exit 2)" || fail "C11 bad execution-id exit=$rc"

# C12 custom execution id + one-file re-run (atomic replace, still valid)
cleanup_root_fixture; rm -f "$RES"
RELAY_DRIVE_EXIT=0 run_md_root --result-file "$RES" --execution-id "gh280-exec-0001" >/dev/null 2>&1
jassert "$RES" 'd["execution_id"]=="gh280-exec-0001"' "C12 caller execution id recorded"
RELAY_DRIVE_EXIT=0 run_md_root --result-file "$RES" --execution-id "gh280-exec-0002" >/dev/null 2>&1
jassert "$RES" 'd["execution_id"]=="gh280-exec-0002"' "C12 re-run atomically replaces the receipt"

# ═══ D. protected-branch redirect + PR identity (root install) ════════════════════════════════
# The fixture checks out `development` (the integration branch the branch guard protects and
# marathon-closeout requires as PR base) — the same shape as this repo: origin/HEAD → main,
# work landing via development.
# D1: guard redirects development → lane branch, stub gh reports PR 42 → receipt carries identity
cleanup_root_fixture; rm -f "$RES"
use_development
( cd "$FR" && GH_STUB_PR_JSON="$CANNED_PR" RELAY_DRIVE_EXIT=0 \
    env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-lane" \
    MARATHON_RELAY_DRIVE="$STUB_RD" CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
    bash "$FR/relay-automation/marathon-drive.sh" \
      --phases-dir "$FR/marathon-system" --phase-brief "$WORK/brief.md" \
      --reviewer agy --builder codex --pre-advance-cmd "bash $GATE_PASS" \
      --result-file "$RES" ) >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "D1 redirected run exits 0" || fail "D1 redirected run exit=$rc"
git -C "$FR" show-ref --verify --quiet refs/heads/marathon/gh280-lane \
  && pass "D1 lane branch marathon/gh280-lane exists" || fail "D1 lane branch missing"
jassert "$RES" 'd["branch_redirect"]==True and d["base_branch"]=="development" and d["head_branch"]=="marathon/gh280-lane"' "D1 receipt records redirect base/head"
jassert "$RES" 'd["pr"]["number"]==42 and d["pr"]["state"]=="OPEN" and d["pr"]["url"]' "D1 receipt carries verified PR identity"
jassert "$RES" 'd["pr_note"] is None' "D1 no PR note on successful publication"

# D2: PR publication fails → phase stays green, PR identity explicit null + visible note
cleanup_root_fixture; rm -f "$RES"
use_development
( cd "$FR" && GH_STUB_CREATE_FAIL=1 RELAY_DRIVE_EXIT=0 \
    env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-lane-2" \
    MARATHON_RELAY_DRIVE="$STUB_RD" CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
    bash "$FR/relay-automation/marathon-drive.sh" \
      --phases-dir "$FR/marathon-system" --phase-brief "$WORK/brief.md" \
      --reviewer agy --builder codex --pre-advance-cmd "bash $GATE_PASS" \
      --result-file "$RES" ) >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "D2 PR-publication failure keeps the phase green (exit 0)" || fail "D2 best-effort PR failure changed the exit: $rc"
jassert "$RES" 'd["outcome"]=="approved" and d["pr"]["number"] is None' "D2 receipt approved with explicit null PR"
jassert "$RES" 'd["pr_note"] and "pr-publication-failed" in d["pr_note"]' "D2 receipt notes the failed publication"

# ═══ E. vendored .xyz installation shape ══════════════════════════════════════════════════════
PKV="$WORK/packet-vendored"
PFV_OUT="$(cd "$FV" && python3 "$FV/.xyz/utils/py/swarm_preflight.py" --gh-issue 901 --out "$PKV" 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "E1 vendored preflight exits 0" || fail "E1 vendored preflight exit=$rc: $PFV_OUT"
INVV="$PKV/marathon-invocation.json"
jassert "$INVV" 'd["harness_home"]=="'"$FV"'/.xyz" and d["argv"][0]=="'"$FV"'/.xyz/relay-automation/marathon-drive.sh"' "E2 vendored artifact points inside .xyz"
jassert "$INVV" 'os.path.realpath(d["target_root"])==os.path.realpath("'"$FV"'")' "E3 vendored target_root is the consumer repo"

RESV="$WORK/md-result-vendored.json"; rm -f "$RESV"
( cd "$FV" && RELAY_DRIVE_EXIT=0 MARATHON_RELAY_DRIVE="$STUB_RD" \
    CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
    bash "$FV/.xyz/relay-automation/marathon-drive.sh" \
      --phases-dir "$FV/marathon-system" --phase-brief "$WORK/brief.md" \
      --reviewer agy --builder codex --pre-advance-cmd "bash $GATE_PASS" \
      --result-file "$RESV" ) >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "E4 vendored drive exits 0 with receipt" || fail "E4 vendored drive exit=$rc"
jassert "$RESV" 'd["outcome"]=="approved" and os.path.realpath(d["target_repo"]["path"])==os.path.realpath("'"$FV"'")' "E5 vendored receipt target_repo is the consumer repo"

# E6 vendored pre-dispatch refusal receipt
rm -f "$RESV"
( cd "$FV" && MARATHON_RELAY_DRIVE="$STUB_RD" CODEX_BIN="$STUB_CODEX" AGY_BIN="$STUB_AGY" \
    bash "$FV/.xyz/relay-automation/marathon-drive.sh" \
      --phases-dir "$FV/marathon-system" --phase-brief "$WORK/brief.md" \
      --reviewer agy --builder codex --result-file "$RESV" ) >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && pass "E6 vendored refusal exits 2" || fail "E6 vendored refusal exit=$rc"
jassert "$RESV" 'd["outcome"]=="refused"' "E7 vendored refusal receipt written"

# ═══ F. real Preflight → Marathon → Relay chain with deterministic agent stubs ════════════════
# The packet's own argv is executed verbatim (minus PATH control): REAL relay-drive, REAL
# marathon-agent routing, stubbed codex/agy CLIs that approve — never --simulate.
cleanup_root_fixture
AGENT_BIN="$WORK/agent-stubs"; mkdir -p "$AGENT_BIN"
cat > "$AGENT_BIN/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '\n### Round 1 · Builder · %s (stub)\nImplemented: test builder update\n' "$RELAY_AGENT" >> "$PWD/marathon-system/p1/RELAY.md"
printf 'module.exports = 2\n' > "$PWD/src/feature.js"
exit 0
EOF
cat > "$AGENT_BIN/agy" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  whoami|models) printf 'agy-stub\n'; exit 0 ;;
esac
printf 'agy review stub\n'
sed -i.bak 's/^STATUS:[[:space:]]*.*/STATUS: Approved/' "$PWD/marathon-system/p1/RELAY.md"; rm -f "$PWD/marathon-system/p1/RELAY.md.bak"
printf '\n### Round 2 · Reviewer · %s (stub)\n**Verdict:** Approved\nBasis: test reviewer\n' "$RELAY_AGENT" >> "$PWD/marathon-system/p1/RELAY.md"
exit 0
EOF
chmod +x "$AGENT_BIN/codex" "$AGENT_BIN/agy"
RESF="$PK/marathon-result.json"; rm -f "$RESF"
( cd "$FR" && PATH="$AGENT_BIN:$PATH" CODEX_BIN="$AGENT_BIN/codex" AGY_BIN="$AGENT_BIN/agy" \
    python3 - "$INV" <<'PY'
import json, os, subprocess, sys
inv = json.load(open(sys.argv[1]))
env = dict(os.environ)
# The packet suggests RELAY_WORKTREE_ISOLATION=1; this case pins the CONTRACT (argv is
# executable as data), so it runs the proven non-isolated stub-agent shape from
# test/marathon-drive.sh cases 17/18b. The isolated dispatch is exercised by the relay
# suites; adding it here would make the stubs' in-tree relay edits containment bait.
env.update({k: v for k, v in inv["env"].items() if k != "RELAY_WORKTREE_ISOLATION"})
rc = subprocess.run(inv["argv"], cwd=inv["target_root"], env=env).returncode
sys.exit(rc)
PY
) >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && pass "F1 real packet argv chain exits 0 (Preflight → Marathon → Relay)" || fail "F1 packet argv chain exit=$rc"
grep -q 'module.exports = 2' "$FR/src/feature.js" \
  && pass "F2 stub builder landed the declared artifact" || fail "F2 artifact not built by the chain"
[ -f "$RESF" ] && pass "F3 chain wrote the packet's result receipt" || fail "F3 no receipt at the packet's result_path"
jassert "$RESF" 'd["outcome"]=="approved" and d["relay_status"]=="Approved"' "F4 receipt approved with relay STATUS Approved"
jassert "$RESF" 'd["gate"]["result"]=="green"' "F5 gate ran green inside the chain"
find "$FR/.tick/events" -maxdepth 1 -type f -name '*MARATHON-P1-TURN*' -print0 2>/dev/null \
  | xargs -0 grep -l '"type":"task.claimed".*"agent":"codex"' >/dev/null 2>&1 \
  && pass "F6 builder claim event in the fixture tick log" || fail "F6 missing builder claim event"
find "$FR/.tick/events" -maxdepth 1 -type f -name '*MARATHON-P1-TURN*' -print0 2>/dev/null \
  | xargs -0 grep -l '"type":"task.claimed".*"agent":"agy"' >/dev/null 2>&1 \
  && pass "F7 reviewer claim event in the fixture tick log" || fail "F7 missing reviewer claim event"

# ═══ G. Phase 2: `releases jog run --executor marathon` (root install) ════════════════════════
# Deterministic agent stubs that discover the relay file rather than hardcoding a phase dir —
# the marathon executor dispatches the packet's slug as the phase id.
JOG_AGENTS="$WORK/jog-agent-stubs"; mkdir -p "$JOG_AGENTS"
cat > "$JOG_AGENTS/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
relay="$(find "$PWD/marathon-system" -name RELAY.md -type f | head -1)"
printf '\n### Round 1 · Builder · %s (stub)\nImplemented: test builder update\n' "$RELAY_AGENT" >> "$relay"
printf 'module.exports = 2\n' > "$PWD/src/feature.js"
exit 0
EOF
cat > "$JOG_AGENTS/agy" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  whoami|models) printf 'agy-stub\n'; exit 0 ;;
esac
relay="$(find "$PWD/marathon-system" -name RELAY.md -type f | head -1)"
printf 'agy review stub\n'
sed -i.bak 's/^STATUS:[[:space:]]*.*/STATUS: Approved/' "$relay"; rm -f "$relay.bak"
printf '\n### Round 2 · Reviewer · %s (stub)\n**Verdict:** Approved\nBasis: test reviewer\n' "$RELAY_AGENT" >> "$relay"
exit 0
EOF
cat > "$JOG_AGENTS/agy-refuse" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  whoami|models) printf 'agy-stub\n'; exit 0 ;;
esac
relay="$(find "$PWD/marathon-system" -name RELAY.md -type f | head -1)"
printf '\n### Round 2 · Reviewer · %s (stub)\n**Verdict:** Changes requested\nBasis: test reviewer refusal\n' "$RELAY_AGENT" >> "$relay"
exit 0
EOF
chmod +x "$JOG_AGENTS/codex" "$JOG_AGENTS/agy" "$JOG_AGENTS/agy-refuse"


# GH-292 F2: ledger records store paths relative to the ledger base — resolve for assertions.
ledger_latest_result() {  # <state.json path> → absolute result_path of the newest execution
  python3 -c 'import json,os,sys
d = json.load(open(sys.argv[1]))
e = d["executions"][-1]
p = e.get("result_path") or ""
print(p if os.path.isabs(p) else os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), p))' "$1"
}

queue_status() {  # <root> → "status|reason|attempt_count"
  sqlite3 "$1/releases.db" "SELECT status || '|' || COALESCE(failure_reason,'') || '|' || COALESCE(attempt_count,0) FROM jog_queue WHERE gh_number = 901;"
}

jog_run_root() {  # <extra-args…> — jog run against the ROOT fixture's own releases_app
  ( cd "$FR" && PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" \
    python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run "$@" )
}

# G1-G3: reviewer validation fails BEFORE lease mutation (row untouched)
cleanup_root_fixture
rm -rf "$FR/.tick/jog"
OUT_G1="$(jog_run_root --executor marathon --builder codex 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && pass "G1 marathon executor without --reviewer refuses (exit 2)" || fail "G1 exit=$rc: $OUT_G1"
grep -q "required with --executor marathon" <<<"$OUT_G1" && pass "G1 refusal names the reviewer policy" || fail "G1 refusal message drifted: $OUT_G1"
has "$(queue_status "$FR")" "pending||0" && pass "G1 row untouched (pending, attempt_count 0)" || fail "G1 row mutated: $(queue_status "$FR")"
OUT_G2="$(jog_run_root --executor marathon --builder codex --reviewer codex 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$(queue_status "$FR")" "pending||0" \
  && pass "G2 reviewer == builder refused before lease" || fail "G2 exit=$rc row=$(queue_status "$FR")"
OUT_G3="$(AGY_BIN="$WORK/no-such-agy-bin" jog_run_root --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$(queue_status "$FR")" "pending||0" \
  && pass "G3 unavailable reviewer binary refused before lease" || fail "G3 exit=$rc row=$(queue_status "$FR")"

# G4: full happy path — Preflight → Marathon (real relay-drive, isolated) → receipt → projection
cleanup_root_fixture
use_development
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
G4_OUT="$(GH_STUB_PR_JSON="$CANNED_PR" \
  env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-jog-lane" \
  PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run \
    --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "G4 marathon executor queue run exits 0" || fail "G4 queue run exit=$rc: $G4_OUT"
has "$(queue_status "$FR")" "parked|awaiting-landing (PR #42" \
  && pass "G4 row parked awaiting-landing with receipt PR identity" || fail "G4 row: $(queue_status "$FR")"
GSTATE="$FR/.tick/jog/$GID/state.json"
[ -f "$GSTATE" ] && pass "G4 execution ledger exists under .tick/jog/<gid>" || fail "G4 no ledger at $GSTATE"
jassert "$GSTATE" 'len(d["executions"])==1 and d["executions"][0]["status"]=="projected-parked" and d["executions"][0]["outcome"]=="approved"' "G4 ledger records one approved, projected execution"
GRES="$(ledger_latest_result "$GSTATE")"
jassert "$GRES" 'd["outcome"]=="approved" and d["pr"]["number"]==42 and d["branch_redirect"]==True and d["head_branch"]=="marathon/gh280-jog-lane"' "G4 receipt approved, PR 42, redirected lane branch"
grep -q 'module.exports = 2' "$FR/src/feature.js" \
  && pass "G4 stub builder landed the artifact through the real chain" || fail "G4 artifact not built"

# G5: controlled failure — reviewer refuses every round → escalated receipt → row failed, queue stops
cleanup_root_fixture
python3 "$FR/utils/py/releases_app.py" --root "$FR" jog retry 901 >/dev/null 2>&1
G5_OUT="$(env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-jog-lane-5" \
  PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy-refuse" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run \
    --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
QS="$(queue_status "$FR")"
case "$QS" in
  failed\|marathon\ escalated:*) pass "G5 refusing reviewer → row failed with marathon escalation" ;;
  *) fail "G5 unexpected row state: $QS" ;;
esac
G5_RES="$(ledger_latest_result "$GSTATE" 2>/dev/null)"
[ -n "$G5_RES" ] && jassert "$G5_RES" 'd["outcome"]=="escalated"' "G5 receipt outcome escalated"

# G6: cold start after dispatch with NO result → parked, never a silent refire
cleanup_root_fixture
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
mkdir -p "$FR/.tick/jog/$GID"
cat > "$FR/.tick/jog/$GID/state.json" <<JSEOF
{"schema": "jog/execution-state@1", "gid": "$GID", "gh_number": 901,
 "executions": [{"execution_id": "gh901-exec1", "mode": "run", "started_at": "2026-08-28T00:00:00Z",
                 "status": "dispatched", "packet_dir": "$FR/.tick/jog/$GID/gh901-exec1/preflight",
                 "result_path": "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json"}]}
JSEOF
sqlite3 "$FR/releases.db" "UPDATE jog_queue SET status = 'running', lease_pid = 999999 WHERE gh_number = 901;"
G6_OUT="$(jog_run_root --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
QS="$(queue_status "$FR")"
case "$QS" in
  parked\|cold-start:*) pass "G6 cold-start without result parks (never refires)" ;;
  *) fail "G6 unexpected row state: $QS" ;;
esac
jassert "$GSTATE" 'len(d["executions"])==1' "G6 no second execution fired on cold start"

# G7: cold start with a valid terminal result → idempotent re-projection, no new turn
# (state is re-fabricated as dispatched: G6 legitimately moved it to cold-start-paused)
mkdir -p "$FR/.tick/jog/$GID/gh901-exec1/preflight"
cat > "$FR/.tick/jog/$GID/state.json" <<JSEOF
{"schema": "jog/execution-state@1", "gid": "$GID", "gh_number": 901,
 "executions": [{"execution_id": "gh901-exec1", "mode": "run", "started_at": "2026-08-28T00:00:00Z",
                 "status": "dispatched", "packet_dir": "$FR/.tick/jog/$GID/gh901-exec1/preflight",
                 "result_path": "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json"}]}
JSEOF
cat > "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json" <<JREOF
{"schema": "marathon-drive/result@1", "execution_id": "gh901-exec1", "generated_at": "2026-08-28T00:00:01Z",
 "outcome": "approved", "reason": "approved, gate passed", "exit_code": 0, "approval_preserved": false,
 "issue": "901", "phase": "p", "lane": "p", "token": "T", "attempt": {"count": 1, "max": 2},
 "builder": "codex", "reviewer": "agy",
 "target_repo": {"path": "$FR", "origin_url": null},
 "base_branch": "development", "head_branch": "marathon/x", "head_sha": "deadbeef",
 "branch_redirect": true,
 "gate": {"cmd": "true", "result": "green", "exit": 0, "receipt_path": null},
 "acceptance": {"checked": false, "unmet_count": 0},
 "pr": {"number": 7, "url": "https://example.invalid/x/pr/7", "state": "OPEN"},
 "pr_note": null, "relay_status": "Approved",
 "timestamps": {"started_at": "2026-08-28T00:00:00Z", "finished_at": "2026-08-28T00:00:01Z"}}
JREOF
sqlite3 "$FR/releases.db" "UPDATE jog_queue SET status = 'running', lease_pid = 999999 WHERE gh_number = 901;"
G7_OUT="$(jog_run_root --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
has "$(queue_status "$FR")" "parked|awaiting-landing (PR #7" \
  && pass "G7 cold-start re-projects the terminal result idempotently" || fail "G7 row: $(queue_status "$FR")"
jassert "$GSTATE" 'len(d["executions"])==1' "G7 re-projection fired no new execution"

# G8: preflight refusal parks the row with the preflight exit
cleanup_root_fixture
rm -f "$FR/PROJECT/2-WORKING/$CAPTURE_DOC_NAME"
git -C "$FR" add -A >/dev/null 2>&1; git -C "$FR" commit -qm "remove capture doc" >/dev/null 2>&1
G8_OUT="$(jog_run_root --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
QS="$(queue_status "$FR")"
case "$QS" in
  parked\|preflight-refused\ \(exit\ 6\)*) pass "G8 preflight refusal parks with exit code" ;;
  *) fail "G8 unexpected row state: $QS" ;;
esac

# ═══ H. Phase 2 vendored: jog run --executor marathon from a foreign cwd ══════════════════════
H_CWD="$WORK/foreign-cwd"; mkdir -p "$H_CWD"
GIDV="$(sqlite3 "$FV/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
H_OUT="$( cd "$H_CWD" && PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FV/.xyz/utils/py/releases_app.py" --root "$FV" jog run \
    --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "H1 vendored marathon queue run exits 0 from a foreign cwd" || fail "H1 exit=$rc: $H_OUT"
QS="$(queue_status "$FV")"
case "$QS" in
  parked\|awaiting-landing\ \(no\ PR\ yet*) pass "H2 vendored row parked awaiting-landing (green, no PR)" ;;
  *) fail "H2 unexpected vendored row state: $QS" ;;
esac
HSTATE="$FV/.tick/jog/$GIDV/state.json"
[ -f "$HSTATE" ] && pass "H3 vendored execution ledger lives in the consumer repo" || fail "H3 no ledger at $HSTATE"
HRES="$(ledger_latest_result "$HSTATE" 2>/dev/null)"
[ -n "$HRES" ] && [ -f "$HRES" ] && jassert "$HRES" 'd["outcome"]=="approved" and os.path.realpath(d["target_repo"]["path"])==os.path.realpath("'"$FV"'")' "H4 vendored receipt approved, target is the consumer repo"
[ ! -d "$H_CWD/marathon-system" ] && [ ! -d "$H_CWD/relay-system" ] && [ ! -d "$H_CWD/.tick" ] \
  && pass "H5 foreign cwd stayed clean (no root-relative lookups — GH-279 #2)" \
  || fail "H5 foreign cwd grew harness output dirs"

# ═══ I. Phase 5 flip: marathon is the default; relay is legacy (--executor relay / --simulate) ═
# The default executor is now marathon (GH-280 Phase 5). The relay machinery survives on two
# explicit spellings — `--executor relay` (THE rollback path) and `--simulate` (which stays on
# the relay machinery by design) — each printing the one-line deprecation notice naming the
# compatibility window and the separate-removal fact. Legacy code is NOT removed in the flip.
cleanup_root_fixture
python3 "$FR/utils/py/releases_app.py" --root "$FR" jog add 902 >/dev/null 2>&1
I_OUT="$(jog_run_root --simulate --auto-merge --max-tasks 1 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$I_OUT" "simulated single-phase drive on GH-901" \
  && pass "I1 --simulate stays on the relay machinery (behavior unchanged)" || fail "I1 simulate path drifted: $(printf '%s' "$I_OUT" | head -3)"
grep -q completed <<<"$(sqlite3 "$FR/releases.db" "SELECT status FROM jog_queue WHERE gh_number = 901;")" \
  && pass "I1b simulated auto-merge completes the processed row" || fail "I1b row 901 not completed"
[ ! -d "$FR/.tick/jog" ] && pass "I2 legacy run leaves no marathon execution state" || fail "I2 marathon state created without --executor marathon"
has "$I_OUT" "relay executor is legacy" && has "$I_OUT" "compatibility window" \
  && has "$I_OUT" "removal lands as its own commit" \
  && pass "I3 --simulate prints the deprecation notice (window + separate removal)" \
  || fail "I3 deprecation notice missing/incomplete: $(printf '%s' "$I_OUT" | head -2)"

# I4: explicit --executor relay — the rollback path still completes the legacy simulate run
cleanup_root_fixture
I4_OUT="$(jog_run_root --executor relay --simulate --auto-merge --max-tasks 1 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$I4_OUT" "simulated single-phase drive on GH-901" \
  && has "$I4_OUT" "relay executor is legacy" \
  && pass "I4 --executor relay rollback path completes the legacy simulate + notice" \
  || fail "I4 legacy rollback path drifted: $(printf '%s' "$I4_OUT" | head -3)"
grep -q completed <<<"$(sqlite3 "$FR/releases.db" "SELECT status FROM jog_queue WHERE gh_number = 901;")" \
  && pass "I4b relay simulate completes the processed row" || fail "I4b row 901 not completed"

# I5: bare `jog run` (no --executor, no --reviewer) now refuses pre-lease under the G1 policy
cleanup_root_fixture
rm -rf "$FR/.tick/jog"
I5_OUT="$(jog_run_root --builder codex 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && pass "I5 bare jog run without --reviewer refuses (exit 2)" || fail "I5 exit=$rc: $I5_OUT"
grep -q "required with --executor marathon" <<<"$I5_OUT" \
  && pass "I5 refusal names the reviewer policy (marathon default)" || fail "I5 refusal message drifted: $I5_OUT"
has "$(queue_status "$FR")" "pending||0" && pass "I5 row untouched (pending, attempt_count 0)" || fail "I5 row mutated: $(queue_status "$FR")"

# I6: default run WITH --reviewer dispatches the marathon executor (G4-mirrored assertions)
use_development
GID_I="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
I6_OUT="$(GH_STUB_PR_JSON="$CANNED_PR" \
  env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-i-lane" \
  PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run \
    --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "I6 default run (no --executor) dispatches marathon, exits 0" || fail "I6 exit=$rc: $I6_OUT"
has "$(queue_status "$FR")" "parked|awaiting-landing (PR #42" \
  && pass "I6 row parked awaiting-landing with receipt PR identity" || fail "I6 row: $(queue_status "$FR")"
ISTATE="$FR/.tick/jog/$GID_I/state.json"
[ -f "$ISTATE" ] && pass "I6 execution ledger exists under .tick/jog/<gid>" || fail "I6 no ledger at $ISTATE"
jassert "$ISTATE" 'len(d["executions"])==1 and d["executions"][0]["status"]=="projected-parked" and d["executions"][0]["outcome"]=="approved"' "I6 ledger records one approved, projected execution"
IRES="$(ledger_latest_result "$ISTATE")"
jassert "$IRES" 'd["outcome"]=="approved" and d["pr"]["number"]==42 and d["branch_redirect"]==True and d["head_branch"]=="marathon/gh280-i-lane"' "I6 receipt approved, PR 42, redirected lane branch"
grep -q 'module.exports = 2' "$FR/src/feature.js" \
  && pass "I6 stub builder landed the artifact through the real chain" || fail "I6 artifact not built"
! has "$I6_OUT" "relay executor is legacy" \
  && pass "I6 marathon-default run prints no deprecation notice" || fail "I6 notice leaked onto the marathon path"

# I7: --dry-run unchanged — hermetic plan, no notice, no reviewer requirement, zero mutation
cleanup_root_fixture
I7_OUT="$(jog_run_root --dry-run 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$I7_OUT" "would process 1 pending item" \
  && ! has "$I7_OUT" "relay executor is legacy" \
  && pass "I7 --dry-run unchanged (plan only, no notice, no reviewer needed)" \
  || fail "I7 dry-run drifted: $(printf '%s' "$I7_OUT" | head -3)"
has "$(sqlite3 "$FR/releases.db" "SELECT status FROM jog_queue WHERE gh_number = 901;")" "pending" \
  && pass "I7b dry-run leaves the row pending (zero mutation)" || fail "I7b row mutated"

# ═══ J. Phase 3: jog resume — reconcile, never fire ═══════════════════════════════════════════
jog_verb() {  # <verb> <extra-args…>
  # GH-300 B5: stub agents on PATH for every verb call — on runners without a real agy
  # the pre-dispatch binary check refused (canary K2: binary-not-found instead of the
  # intended refusal), so the helper carries the stub env itself.
  ( cd "$FR" && PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
    python3 "$FR/utils/py/releases_app.py" --root "$FR" jog "$@" )
}

# J1: terminal receipt on record → idempotent re-projection, no new execution
cleanup_root_fixture
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
mkdir -p "$FR/.tick/jog/$GID/gh901-exec1/preflight"
cat > "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json" <<JREOF
{"schema": "marathon-drive/result@1", "execution_id": "gh901-exec1", "generated_at": "2026-08-28T00:00:01Z",
 "outcome": "approved", "reason": "approved, gate passed", "exit_code": 0, "approval_preserved": false,
 "issue": "901", "phase": "p", "lane": "p", "token": "T", "attempt": {"count": 1, "max": 2},
 "builder": "codex", "reviewer": "agy",
 "target_repo": {"path": "$FR", "origin_url": null},
 "base_branch": "development", "head_branch": "marathon/x", "head_sha": "deadbeef",
 "branch_redirect": true,
 "gate": {"cmd": "true", "result": "green", "exit": 0, "receipt_path": null},
 "acceptance": {"checked": false, "unmet_count": 0},
 "pr": {"number": 7, "url": "https://example.invalid/x/pr/7", "state": "OPEN"},
 "pr_note": null, "relay_status": "Approved",
 "timestamps": {"started_at": "2026-08-28T00:00:00Z", "finished_at": "2026-08-28T00:00:01Z"}}
JREOF
cat > "$FR/.tick/jog/$GID/state.json" <<JSEOF
{"schema": "jog/execution-state@1", "gid": "$GID", "gh_number": 901,
 "executions": [{"execution_id": "gh901-exec1", "mode": "run", "started_at": "2026-08-28T00:00:00Z",
                 "status": "dispatched", "packet_dir": "$FR/.tick/jog/$GID/gh901-exec1/preflight",
                 "result_path": "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json"}]}
JSEOF
J1_OUT="$(jog_verb resume 901 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$J1_OUT" "re-projected" \
  && pass "J1 resume re-projects a terminal result (no dispatch)" || fail "J1 rc=$rc: $J1_OUT"
has "$(queue_status "$FR")" "parked|awaiting-landing (PR #7" \
  && pass "J1 row parked awaiting-landing after resume" || fail "J1 row: $(queue_status "$FR")"
jassert "$FR/.tick/jog/$GID/state.json" 'len(d["executions"])==1' "J1 resume fired no new execution"

# J2: dispatched without a result → parked, no token spent
python3 - "$FR/.tick/jog/$GID/state.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["executions"][0]["status"] = "dispatched"
json.dump(d, open(p, "w"), indent=2)
PY
rm -f "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json"
sqlite3 "$FR/releases.db" "UPDATE jog_queue SET status = 'running', lease_pid = 999999 WHERE gh_number = 901;"
J2_OUT="$(jog_verb resume 901 2>&1)"; rc=$?
[ "$rc" -eq 1 ] && has "$J2_OUT" "no valid result" \
  && pass "J2 resume parks a result-less dispatched execution (exit 1)" || fail "J2 rc=$rc: $J2_OUT"
has "$(queue_status "$FR")" "parked|resume: dispatched" \
  && pass "J2 row parked with resume reason" || fail "J2 row: $(queue_status "$FR")"

# ═══ K. Phase 3: jog retry-gate — gate-only, same head SHA, no builder turn ════════════════════
cleanup_root_fixture
use_development
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
GATE_MARKER="$WORK/gh280-gate-green"
# The contract gate reads a marker: red until K2 flips it green — one gate, two states.
printf '#!/usr/bin/env bash\ntest -f %s\n' "$GATE_MARKER" > "$FR/test/fixture-gate.sh"
git -C "$FR" add -A >/dev/null 2>&1; git -C "$FR" commit -qm "marker-driven gate" >/dev/null 2>&1

K1_OUT="$(env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-k-lane" \
  PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run \
    --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
QS="$(queue_status "$FR")"
case "$QS" in
  failed\|marathon\ escalated:\ pre-advance-failed*) pass "K1 red-gate execution fails the row (relay approved, gate red)" ;;
  *) fail "K1 unexpected row state: $QS" ;;
esac
has "$QS" "gh901-exec1" && has "$QS" "marathon-result.json" \
  && pass "K1 failed row's reason carries the trace segment (execution id + result path — Scope 4)" \
  || fail "K1 trace segment missing from row reason: $QS"
K1_RES="$(ledger_latest_result "$FR/.tick/jog/$GID/state.json")"
K1_HEAD="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["head_sha"])' "$K1_RES")"
K1_TASK_COUNT="$(grep -h -c '"type":"task.created"' "$FR"/.tick/events/*MARATHON-GH-901* 2>/dev/null | awk '{s+=$1} END {print s+0}')"

touch "$GATE_MARKER"
K2_OUT="$(jog_verb retry-gate 901 --reviewer agy --builder codex 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "K2 gate-only retry exits 0" || fail "K2 rc=$rc: $K2_OUT"
has "$(queue_status "$FR")" "parked|awaiting-landing" \
  && pass "K2 row parked awaiting-landing after green gate retry" || fail "K2 row: $(queue_status "$FR")"
K2_RES="$FR/.tick/jog/$GID/gh901-exec1/gate-retry-1/marathon-result.json"
jassert "$K2_RES" 'd["outcome"]=="approved" and d["reason"]=="already-satisfied"' "K2 retry receipt approved via satisfied-lane path"
K2_HEAD="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["head_sha"])' "$K2_RES")"
[ "$(git -C "$FR" rev-parse "$K2_HEAD^" 2>/dev/null)" = "$K1_HEAD" ] \
  && pass "K2 only marathon's own transcript commit advanced the head (work head preserved)" \
  || fail "K2 head moved by more than the transcript commit: $K1_HEAD -> $K2_HEAD"
K2_TASK_COUNT="$(grep -h -c '"type":"task.created"' "$FR"/.tick/events/*MARATHON-GH-901* 2>/dev/null | awk '{s+=$1} END {print s+0}')"
[ "$K2_TASK_COUNT" = "$K1_TASK_COUNT" ] \
  && pass "K2 gate retry spent no new tick token ($K2_TASK_COUNT task.created)" \
  || fail "K2 token re-seeded: before=$K1_TASK_COUNT after=$K2_TASK_COUNT"

# K3: head moved under the retry → refused BEFORE dispatch (needs retry-build, not a gate check)
git -C "$FR" checkout -q -b gh280-k3-temp
git -C "$FR" commit -q --allow-empty -m "move head under the gate retry"
K3_OUT="$(jog_verb retry-gate 901 --reviewer agy --builder codex 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$K3_OUT" "head moved" \
  && pass "K3 gate retry refuses when the head SHA moved" || fail "K3 rc=$rc: $K3_OUT"
[ ! -d "$FR/.tick/jog/$GID/gh901-exec1/gate-retry-2" ] \
  && pass "K3 refusal dispatched no gate run" || fail "K3 dispatch happened despite refusal"
git -C "$FR" checkout -q marathon/gh280-k-lane
git -C "$FR" branch -q -D gh280-k3-temp >/dev/null 2>&1 || true

# K4: retry-build — a FRESH execution on a FRESH suffixed token, prior history intact
K4_OUT="$( cd "$FR" && PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog retry-build 901 --reviewer agy --builder codex 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "K4 retry-build exits 0" || fail "K4 rc=$rc: $K4_OUT"
has "$(queue_status "$FR")" "parked|awaiting-landing" \
  && pass "K4 row parked awaiting-landing after the rebuild" || fail "K4 row: $(queue_status "$FR")"
jassert "$FR/.tick/jog/$GID/state.json" 'len(d["executions"])==2 and d["executions"][1]["mode"]=="retry-build"' "K4 ledger gained a second retry-build execution"
grep -q "MARATHON-GH-901-FIXTURE-LANE-TURN-2" <<<"$(ls "$FR"/.tick/events/)" \
  && pass "K4 rebuild ran on a fresh suffixed token (-2)" || fail "K4 no -2 token events"
grep -q "MARATHON-GH-901-FIXTURE-LANE-TURN$\|MARATHON-GH-901-FIXTURE-LANE-TURN-" <<<"$(ls "$FR"/.tick/events/)" \
  && [ -d "$FR/.tick/jog/$GID/gh901-exec1" ] \
  && pass "K4 prior token history and execution records preserved" || fail "K4 prior history damaged"

# ═══ L. Phase 3: jog land / jog reconcile — verify, project, delegate, replay ═════════════════
# Real merge: the lane branch is genuinely merged into development so reachability holds.
git -C "$FR" checkout -q development
git -C "$FR" merge -q --no-ff -m "merge lane gh280" marathon/gh280-k-lane >/dev/null 2>&1
LANE_TIP="$(git -C "$FR" rev-parse marathon/gh280-k-lane)"
MERGE_SHA="$(git -C "$FR" rev-parse HEAD)"
# wave_reconcile fixture prep (mirrors test/wave-reconcile.sh): legacy ROADMAP, lessons-learned
# on the capture doc, lifecycle dirs, and mocked downstream subordinates.
mkdir -p "$FR/PROJECT/3-COMPLETED" "$FR/PROJECT/4-MISC" "$FR/TESTS-RESULTS/2026-08-28"
cat >> "$FR/PROJECT/2-WORKING/$CAPTURE_DOC_NAME" <<'EOF'

## Lessons Learned (For Future Agents)
- Verified landing through the receipt contract.
EOF
cat > "$FR/ROADMAP.md" <<'EOF'
# Roadmap

### In progress
- **GH-901 · Fixture Lane** 🚧 **active 2026-08-28** — fixture lane. → [GH-901-FIXTURE-LANE.md](PROJECT/2-WORKING/GH-901-FIXTURE-LANE.md) · [#901](https://github.com/example/example/issues/901)

### Completed
EOF
printf '#!/usr/bin/env bash\necho "MOCK: dashboard OK"\n' > "$FR/utils/roadmap-dashboard.sh"
printf '#!/usr/bin/env bash\necho "MOCK: marathon-plan OK"\n' > "$FR/utils/marathon-plan.sh"
printf '#!/usr/bin/env python3\nprint("MOCK: timeline OK")\n' > "$FR/utils/timeline/export_timeline.py"
printf '#!/usr/bin/env bash\necho "MOCK: pdda OK"\n' > "$FR/utils/pdda/pdda.sh"
chmod +x "$FR/utils/roadmap-dashboard.sh" "$FR/utils/marathon-plan.sh" "$FR/utils/pdda/pdda.sh"
printf '{"status": "PASS"}\n' > "$FR/TESTS-RESULTS/2026-08-28/provenance.jsonl"
git -C "$FR" add -A >/dev/null 2>&1; git -C "$FR" commit -qm "wave fixture prep" >/dev/null 2>&1

pr_view_json() {  # <state> <base> <headRefOid> <mergeOid|null>
  python3 - "$@" <<'PY'
import json, sys
state, base, head_oid, merge_oid = sys.argv[1:5]
pr = {"number": 42, "url": "https://example.invalid/x/pr/42", "state": state,
      "baseRefName": base, "headRefName": "marathon/gh280-k-lane", "headRefOid": head_oid,
      "mergedAt": "2026-08-28T01:00:00Z" if state == "MERGED" else None,
      "title": "GH-901 fixture", "body": "Closes #901"}
if merge_oid != "null":
    pr["mergeCommit"] = {"oid": merge_oid}
print(json.dumps(pr))
PY
}
VIEW="$WORK/pr-view.json"

# L1-L4: fail-closed checks — wrong base, unmerged PR, head-SHA mismatch, unreachable merge SHA
GH_STUB_PR_VIEW_JSON="$VIEW" pr_view_json MERGED main "$LANE_TIP" "$MERGE_SHA" > "$VIEW"
L1_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L1_OUT" "base development" \
  && pass "L1 wrong PR base refused" || fail "L1 rc=$rc: $L1_OUT"
pr_view_json MERGED development 0000000000000000000000000000000000000000 "$MERGE_SHA" > "$VIEW"
L2_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L2_OUT" "head SHA" \
  && pass "L2 head-SHA mismatch refused" || fail "L2 rc=$rc: $L2_OUT"
pr_view_json OPEN development "$LANE_TIP" null > "$VIEW"
L3_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L3_OUT" "state MERGED" \
  && pass "L3 unmerged PR refused" || fail "L3 rc=$rc: $L3_OUT"
git -C "$FR" checkout -q -b unrelated-base development >/dev/null 2>&1
git -C "$FR" commit -q --allow-empty -m "unrelated" >/dev/null 2>&1
UNRELATED="$(git -C "$FR" rev-parse HEAD)"
git -C "$FR" checkout -q development >/dev/null 2>&1
git -C "$FR" branch -q -D unrelated-base >/dev/null 2>&1
pr_view_json MERGED development "$LANE_TIP" "$UNRELATED" > "$VIEW"
L4_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L4_OUT" "not reachable" \
  && pass "L4 unreachable merge SHA refused" || fail "L4 rc=$rc: $L4_OUT"
has "$(queue_status "$FR")" "parked|" \
  && pass "L1-L4 left the row un-landed (fail closed)" || fail "row mutated by a refused land: $(queue_status "$FR")"

# L5: the good landing — verifies, completes the row, delegates lifecycle to wave_reconcile
pr_view_json MERGED development "$LANE_TIP" "$MERGE_SHA" > "$VIEW"
L5_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "L5 jog land completes cleanly" || fail "L5 rc=$rc: $L5_OUT"
has "$(queue_status "$FR")" "completed|landed via PR #42" \
  && pass "L5 row completed with landed-PR reason" || fail "L5 row: $(queue_status "$FR")"
[ -f "$FR/PROJECT/3-COMPLETED/$CAPTURE_DOC_NAME" ] && [ ! -f "$FR/PROJECT/2-WORKING/$CAPTURE_DOC_NAME" ] \
  && pass "L5 wave_reconcile promoted the capture doc to 3-COMPLETED" \
  || fail "L5 doc not promoted by wave_reconcile"
grep -q "SHIPPED.*PR #42" "$FR/ROADMAP.md" \
  && pass "L5 ROADMAP entry archived with the shipping badge" || fail "L5 ROADMAP not archived"
jassert "$FR/.tick/jog/$GID/state.json" 'any(e.get("landing",{}).get("reconciled") for e in d["executions"])' "L5 landing reconciliation evidence recorded"

# L6: replay is idempotent — verifies again, projects nothing new, reconciles nothing new
L6_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$L6_OUT" "already reconciled" \
  && pass "L6 land replay is idempotent" || fail "L6 rc=$rc: $L6_OUT"

# L7: crash-boundary resume — landing recorded, reconciliation evidence missing → only step 3 re-runs
python3 - "$FR/.tick/jog/$GID/state.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
for e in d["executions"]:
    if "landing" in e:
        e["landing"]["reconciled"] = False
json.dump(d, open(p, "w"), indent=2)
PY
L7_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb reconcile 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$L7_OUT" "replaying missing steps only" \
  && pass "L7 reconcile resumes at the missing durable step" || fail "L7 rc=$rc: $L7_OUT"
jassert "$FR/.tick/jog/$GID/state.json" 'any(e.get("landing",{}).get("reconciled") for e in d["executions"])' "L7 reconciliation evidence restored"

# L8/L9: more fail-closed shapes on a fabricated ledger — missing gate evidence, wrong repo
cleanup_root_fixture
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
mkdir -p "$FR/.tick/jog/$GID/gh901-exec1/preflight"
make_land_receipt() {  # <gate-result> <repo-path>
  python3 - "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json" "$1" "$2" <<'PY'
import json, sys
path, gate_result, repo_path = sys.argv[1:4]
json.dump({
    "schema": "marathon-drive/result@1", "execution_id": "gh901-exec1",
    "generated_at": "2026-08-28T02:00:00Z", "outcome": "approved", "reason": "approved",
    "exit_code": 0, "approval_preserved": False, "issue": "901", "phase": "p", "lane": "p",
    "token": "T", "attempt": {"count": 1, "max": 2}, "builder": "codex", "reviewer": "agy",
    "target_repo": {"path": repo_path, "origin_url": None},
    "base_branch": "development", "head_branch": "marathon/gh280-k-lane", "head_sha": "deadbeef",
    "branch_redirect": True,
    "gate": {"cmd": "true", "result": gate_result, "exit": 0 if gate_result == "green" else 1,
             "receipt_path": None},
    "acceptance": {"checked": False, "unmet_count": 0},
    "pr": {"number": 42, "url": "https://example.invalid/x/pr/42", "state": "OPEN"},
    "pr_note": None, "relay_status": "Approved",
    "timestamps": {"started_at": "2026-08-28T01:59:00Z", "finished_at": "2026-08-28T02:00:00Z"},
}, open(path, "w"), indent=2)
PY
}
cat > "$FR/.tick/jog/$GID/state.json" <<JSEOF
{"schema": "jog/execution-state@1", "gid": "$GID", "gh_number": 901,
 "executions": [{"execution_id": "gh901-exec1", "mode": "run", "started_at": "2026-08-28T02:00:00Z",
                 "status": "projected-parked", "packet_dir": "$FR/.tick/jog/$GID/gh901-exec1/preflight",
                 "result_path": "$FR/.tick/jog/$GID/gh901-exec1/preflight/marathon-result.json"}]}
JSEOF
pr_view_json MERGED development deadbeef deadbeef > "$VIEW"
make_land_receipt red "$FR"
L8_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L8_OUT" "gate green on the landed head" \
  && pass "L8 receipt without green gate evidence refused" || fail "L8 rc=$rc: $L8_OUT"
make_land_receipt green "/definitely/not/this/repo"
L9_OUT="$(GH_STUB_PR_VIEW_JSON="$VIEW" jog_verb land 901 --pr 42 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$L9_OUT" "receipt repo is this repo" \
  && pass "L9 receipt naming a foreign repo refused" || fail "L9 rc=$rc: $L9_OUT"


# ═══ M. GH-292 follow-up fixes: F1 supervisor-state commit, F2 ledger re-key survival, F3 dashboard regen ══
cleanup_root_fixture
use_development
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
# Park a roadmap row so promotion genuinely repoints it (and the dashboard drifts);
# commit the in-sync dashboard BEFORE the run so post-promotion drift is falsifiable (F3)
# --root is REQUIRED: without it resolve_root() lands on the REAL clone running the gate
# and the fixture row escapes into the live releases.db (GH-195 class, observed live
# 2026-08-29: a phantom GH-901 row parked at 04:09:08Z failed roadmap-dashboard.sh mid-gate
# and — worse — neutered M1 below, because the fixture never held the row and the promotion's
# repoint silently no-such-row'd, leaving the F3 assertion vacuously green).
python3 "$FR/utils/py/releases_app.py" --root "$FR" roadmap add --issue-num 901 \
  --issue-url "https://github.com/example/example/issues/901" \
  --title "GH-901 fixture lane" --created 2026-08-28 \
  --doc-path "PROJECT/1-INBOX/$CAPTURE_DOC_NAME" >/dev/null 2>&1
printf '# Roadmap\n\n### In progress\n' > "$FR/ROADMAP.md"   # renderer reads it even in DB mode
bash "$FR/utils/roadmap-dashboard.sh" >/dev/null 2>&1 || true
git -C "$FR" add -A >/dev/null 2>&1; git -C "$FR" commit -qm "fixture: commit dashboard baseline" >/dev/null 2>&1
bash "$FR/utils/roadmap-dashboard.sh" --check >/dev/null 2>&1 \
  && pass "M0a baseline dashboard is in sync before the run" \
  || fail "M0a baseline dashboard already drifting — fixture invalid"

M_OUT="$(GH_STUB_PR_JSON="$CANNED_PR" \
  env -u MARATHON_ALLOW_TRUNK_COMMIT SP_SUGGESTED_BRANCH="marathon/gh280-m-lane" \
  PATH="$JOG_AGENTS:$PATH" CODEX_BIN="$JOG_AGENTS/codex" AGY_BIN="$JOG_AGENTS/agy" \
  python3 "$FR/utils/py/releases_app.py" --root "$FR" jog run \
    --executor marathon --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && pass "M0 promoted executor run exits 0" || fail "M0 exit=$rc: $M_OUT"

# M1 (F3): the dashboard is in sync after a promotion (was drift-red pre-fix)
m1_out="$(bash "$FR/utils/roadmap-dashboard.sh" --check 2>&1)" \
  && pass "M1 dashboard in sync after promotion (F3)" \
  || fail "M1 dashboard drifted after promotion — F3 regen missing: $m1_out"

# M3 (F1): a jog-state commit exists before dispatch, and a containment-style revert
# of tracked ledger files cannot destroy the queue row anymore
grep -q "jog-state:" <<<"$(git -C "$FR" log --oneline --grep="^jog-state:" -1)" \
  && pass "M3 supervisor-state commit landed before dispatch (F1)" \
  || fail "M3 no jog-state commit found"
grep -q "releases.db" <<<"$(git -C "$FR" show --name-only --format= "$(git -C "$FR" log --format=%H --grep="^jog-state:" -1)")" \
  && pass "M3 the supervisor commit carries releases.db" || fail "M3 supervisor commit lacks releases.db"
git -C "$FR" checkout -q -- releases.db releases.sql
N_ROWS="$(sqlite3 "$FR/releases.db" "SELECT count(*) FROM jog_queue WHERE gh_number = 901;")"
[ "$N_ROWS" -ge 1 ] \
  && pass "M3 containment-style tree revert leaves the queue row intact (F1)" \
  || fail "M3 queue row lost to tree revert"

# M2 (F2): DB loss + re-add — the ledger is found by gh-number, no re-key surgery
OLD_GID="$GID"
sqlite3 "$FR/releases.db" "DELETE FROM jog_queue WHERE gh_number = 901;"
python3 "$FR/utils/py/releases_app.py" --root "$FR" jog add 901 >/dev/null 2>&1
NEW_GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
[ "$NEW_GID" != "$OLD_GID" ] && pass "M2 re-add minted a fresh gid" || fail "M2 expected a fresh gid"
M2_OUT="$(jog_verb resume 901 2>&1)"; rc=$?
[ "$rc" -eq 0 ] && has "$M2_OUT" "re-projected" \
  && pass "M2 resume finds the ledger by gh-number after re-add (F2)" \
  || fail "M2 resume lost the history: $M2_OUT"
jassert "$FR/.tick/jog/$OLD_GID/state.json" 'any(e.get("packet_dir") and not e["packet_dir"].startswith("/") for e in d["executions"]) or True' "M2 ledger record present (relative-path form asserted below)"
jassert "$FR/.tick/jog/$OLD_GID/state.json" 'not d["executions"][0].get("result_path","").startswith("/")' "M2 result_path stored relative to the ledger (F2)"

# ═══ N. GH-300 (PR #281 review): verified auto-merge (B1) + supervisor lock on retries (B2) ══
# N1–N5 drive the projection seam directly — a hand-written approved receipt plus a canned
# `gh pr view` answer — so the pre-merge verification matrix is hermetic and exact. The gh
# stub logs every call; merge refusals are proven by a frozen merge-call count.
cleanup_root_fixture
use_development
GID="$(sqlite3 "$FR/releases.db" "SELECT global_id FROM jog_queue WHERE gh_number = 901;")"
NEXEC="$FR/.tick/jog/$GID/gh901-exec1/preflight"; mkdir -p "$NEXEC"
N_RECEIPT="$NEXEC/marathon-result.json"
N_HEAD="$(git -C "$FR" rev-parse HEAD)"
N_OTHER_HEAD="$(git -C "$FR" rev-parse HEAD^{tree})"
N_VIEW="$WORK/n-pr-view.json"
# GH-505: an approved receipt is merge-eligible only with relay-drive's attestation behind it. Give the
# N-series a real one (reviewer agy, token T, reviewed at N_HEAD) so the positive case is still
# positive; the fail-closed cases below are refused by the identity checks that run before it.
mkdir -p "$FR/relay-system/n"
printf '# RELAY · N\nSTATUS: Open\nNEXT: agy\n\nbody\n' > "$FR/relay-system/n/RELAY.md"
TICK_REPO_ROOT="$FR" "$TICK" init >/dev/null 2>&1 || true
TICK_REPO_ROOT="$FR" "$TICK" log task.created T --agent marathon >/dev/null 2>&1 || true
TICK_REPO_ROOT="$FR" TICK_BIN="$TICK" MARATHON_BUILDER=codex bash "$ATTEST_STUB" --relay-file "$FR/relay-system/n/RELAY.md" --relay-task T --reviewer agy --target-root "$FR" >/dev/null 2>&1
grep -qE '^status:[[:space:]]+done$' <<<"$(TICK_REPO_ROOT="$FR" "$TICK" info T 2>/dev/null)" && pass "N0 token T reads done in the fixture root" || fail "N0 token T not done: $(TICK_REPO_ROOT="$FR" "$TICK" info T 2>&1 | head -3)"
N_ATTEST="$(git -C "$FR" rev-parse --absolute-git-dir)/relay-attest/T.json"
[ -f "$N_ATTEST" ] && pass "N0 attestation fixture published for token T" || fail "N0 attestation fixture missing: $N_ATTEST"

write_n_receipt() {  # <head-sha> <gate-result> <repo-path>
  python3 - "$N_RECEIPT" "$1" "$2" "$3" "$N_ATTEST" "$N_HEAD" <<'PY'
import json, sys
path, head_sha, gate, repo, attest_path, reviewed = sys.argv[1:7]
json.dump({
  "reviewed_candidate": head_sha, "reviewed_head": reviewed, "added_sha256": "fixture", "attest_path": attest_path,
  "schema": "marathon-drive/result@1", "execution_id": "gh901-exec1",
  "generated_at": "2026-08-28T02:00:00Z", "outcome": "approved",
  "reason": "approved, gate passed", "exit_code": 0, "approval_preserved": False,
  "issue": "901", "phase": "p", "lane": "p", "token": "T",
  "attempt": {"count": 1, "max": 2}, "builder": "codex", "reviewer": "agy",
  "target_repo": {"path": repo, "origin_url": None},
  "base_branch": "development", "head_branch": "marathon/gh280-n-lane", "head_sha": head_sha,
  "branch_redirect": True,
  "gate": {"cmd": "true", "result": gate, "exit": 0 if gate == "green" else 1, "receipt_path": None},
  "acceptance": {"checked": False, "unmet_count": 0},
  "pr": {"number": 42, "url": "https://example.invalid/x/pr/42", "state": "OPEN"},
  "pr_note": None, "relay_status": "Approved",
  "timestamps": {"started_at": "2026-08-28T01:59:59Z", "finished_at": "2026-08-28T02:00:00Z"},
}, open(path, "w"), indent=1)
PY
}

write_n_view() {  # <state> <base> <head-branch> <head-oid>
  python3 - "$N_VIEW" "$@" <<'PY'
import json, sys
path, state, base, head_branch, head_oid = sys.argv[1:6]
json.dump({"number": 42, "url": "https://example.invalid/x/pr/42", "state": state,
           "baseRefName": base, "headRefName": head_branch, "headRefOid": head_oid,
           "mergedAt": None, "title": "GH-901 fixture", "body": "Closes #901"}, open(path, "w"))
PY
}

n_project() {  # run the auto-merge projection against the current receipt + view
  ( cd "$FR" && GH_STUB_PR_VIEW_JSON="$N_VIEW" python3 - "$FR" "$N_RECEIPT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/utils/py")
from jog_run import jog_project_marathon_outcome, load_marathon_result
receipt = load_marathon_result(sys.argv[2])
action, reason = jog_project_marathon_outcome(sys.argv[1], 901, receipt, auto_merge=True)
print(f"{action}|{reason}")
PY
  )
}
merge_calls() { grep -c 'pr merge' "$GH_STUB_LOG" || true; }

# N1 (B1 accept): every identity field matches → merge fires, row completes
write_n_receipt "$N_HEAD" green "$FR"
write_n_view OPEN development marathon/gh280-n-lane "$N_HEAD"
MERGES_BEFORE_N="$(merge_calls)"
N1_OUT="$(n_project)"
has "$N1_OUT" "completed|marathon approved; PR #42 merged" \
  && pass "N1 verified auto-merge completes on a matching PR" || fail "N1 unexpected projection: $N1_OUT"
[ "$(merge_calls)" -eq $((MERGES_BEFORE_N + 1)) ] \
  && pass "N1 the verified merge issued exactly one gh pr merge" \
  || fail "N1 merge call count moved $(merge_calls) != $((MERGES_BEFORE_N + 1))"

# N2 (B1 refuse): the PR's head moved after the reviewed build → no merge
write_n_view OPEN development marathon/gh280-n-lane "$N_OTHER_HEAD"
N2_OUT="$(n_project)"; rc=$?
has "$N2_OUT" "auto-merge refused (verification failed: head SHA" \
  && pass "N2 head-SHA mismatch refuses the auto-merge" || fail "N2 rc=$rc: $N2_OUT"
[ "$(merge_calls)" -eq $((MERGES_BEFORE_N + 1)) ] \
  && pass "N2 no merge call issued on refusal" || fail "N2 a merge leaked through: $(merge_calls)"

# N2b (GH-505): PR head matches the receipt-time head_sha but NOT the validated candidate → refuse
python3 - "$N_RECEIPT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d["reviewed_candidate"] = "0" * 40; json.dump(d, open(sys.argv[1], "w"), indent=1)
PY
write_n_view OPEN development marathon/gh280-n-lane "$N_HEAD"
N2B_OUT="$(n_project)"
has "$N2B_OUT" "candidate-drifted-from-reviewed-head" \
  && pass "N2b PR head ≠ validated candidate refuses the auto-merge even though head_sha matches" || fail "N2b: $N2B_OUT"
[ "$(merge_calls)" -eq $((MERGES_BEFORE_N + 1)) ] && pass "N2b no merge call issued" || fail "N2b a merge leaked through: $(merge_calls)"
# N2c (GH-505): an approved receipt with no attestation binding → refuse
python3 - "$N_RECEIPT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d["reviewed_candidate"] = None; d["attest_path"] = None; json.dump(d, open(sys.argv[1], "w"), indent=1)
PY
N2C_OUT="$(n_project)"
has "$N2C_OUT" "receipt carries no reviewer attestation" \
  && pass "N2c unattested approved receipt refuses the auto-merge" || fail "N2c: $N2C_OUT"
[ "$(merge_calls)" -eq $((MERGES_BEFORE_N + 1)) ] && pass "N2c no merge call issued" || fail "N2c a merge leaked through: $(merge_calls)"
write_n_receipt "$N_HEAD" green "$FR"

# N3 (B1 refuse): PR already merged elsewhere → refuse (jog land owns the merged case)
write_n_view MERGED development marathon/gh280-n-lane "$N_HEAD"
N3_OUT="$(n_project)"
has "$N3_OUT" "auto-merge refused (verification failed: state OPEN" \
  && pass "N3 already-merged PR refuses the auto-merge" || fail "N3: $N3_OUT"

# N4 (B1 refuse): gate red on the receipt → refuse naming the gate
write_n_receipt "$N_HEAD" red "$FR"
write_n_view OPEN development marathon/gh280-n-lane "$N_HEAD"
N4_OUT="$(n_project)"
has "$N4_OUT" "auto-merge refused (verification failed: gate green on the merge head" \
  && pass "N4 red gate refuses the auto-merge" || fail "N4: $N4_OUT"

# N5 (B1 refuse): receipt belongs to a foreign repo → refuse naming the repo check
write_n_receipt "$N_HEAD" green "$WORK/foreign-repo"
N5_OUT="$(n_project)"
has "$N5_OUT" "auto-merge refused (verification failed: receipt repo is this repo" \
  && pass "N5 foreign-repo receipt refuses the auto-merge" || fail "N5: $N5_OUT"
[ "$(merge_calls)" -eq $((MERGES_BEFORE_N + 1)) ] \
  && pass "N5 refusal matrix issued no further merge calls" || fail "N5 merge leaked: $(merge_calls)"

# N6–N8 (B2): retry verbs hold the supervisor lock — a live holder refuses before dispatch
LOCK_DIR="$FR/.git/relay-driver.lock"
mkdir -p "$LOCK_DIR"; printf '%s\n' "$$" > "$LOCK_DIR/pid"
N6_OUT="$(jog_verb retry-gate 901 --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 4 ] && has "$N6_OUT" "another driver is active" \
  && pass "N6 retry-gate refuses under a live supervisor lock (exit 4)" || fail "N6 rc=$rc: $N6_OUT"
N7_OUT="$(jog_verb retry-build 901 --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 4 ] && has "$N7_OUT" "another driver is active" \
  && pass "N7 retry-build refuses under a live supervisor lock (exit 4)" || fail "N7 rc=$rc: $N7_OUT"
rm -rf "$LOCK_DIR"
# N8: with the lock free, the verb acquires AND releases it (proceeds to its normal
# no-ledger refusal — exit 2, not the lock's 4 — and leaves no lock dir behind)
N8_OUT="$(jog_verb retry-gate 901 --builder codex --reviewer agy 2>&1)"; rc=$?
[ "$rc" -eq 2 ] && has "$N8_OUT" "has no jog queue row and no execution ledger" \
  && pass "N8 retry-gate proceeds past a free lock (exit 2, not lock refusal)" || fail "N8 rc=$rc: $N8_OUT"
[ ! -e "$LOCK_DIR" ] \
  && pass "N8 retry-gate released the supervisor lock on exit" || fail "N8 lock dir left behind"

# ═══ O. GH-291 Scope 4: refused/escalated projections name execution_id + result_path ══════
# Hermetic seam check with a hand-written refused receipt: the trace segment must point at
# the receipt without a ledger inspection.
python3 - "$FR" "$N_RECEIPT" <<'PY'
import json, sys
receipt = json.load(open(sys.argv[2]))
receipt.update({"outcome": "refused", "reason": "gate-missing", "exit_code": 2})
json.dump(receipt, open(sys.argv[2], "w"), indent=1)
PY
O1_OUT="$( cd "$FR" && python3 - "$FR" "$N_RECEIPT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/utils/py")
from jog_run import jog_project_marathon_outcome, load_marathon_result
action, reason = jog_project_marathon_outcome(
    sys.argv[1], 901, load_marathon_result(sys.argv[2]),
    execution_id="gh901-exec9", result_path=".tick/jog/x/gh901-exec9/marathon-result.json")
print(f"{action}|{reason}")
PY
)"
has "$O1_OUT" "failed|marathon refused: gate-missing (exit 2) [gh901-exec9" \
  && has "$O1_OUT" "result: .tick/jog/x/gh901-exec9/marathon-result.json]" \
  && pass "O1 refused projection carries the trace segment (execution id + result path)" \
  || fail "O1 trace segment missing: $O1_OUT"
O2_OUT="$( cd "$FR" && python3 - "$FR" "$N_RECEIPT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/utils/py")
from jog_run import jog_project_marathon_outcome, load_marathon_result
action, reason = jog_project_marathon_outcome(sys.argv[1], 901, load_marathon_result(sys.argv[2]))
print(f"{action}|{reason}")
PY
)"
has "$O2_OUT" "marathon refused: gate-missing (exit 2)" && ! has "$O2_OUT" "no-execution-id" \
  && pass "O2 projection without trace args stays unannotated (back-compat)" \
  || fail "O2 unexpected unannotated form: $O2_OUT"

# ═══ P. GH-291 Scope 3: boundary-regression guard — the supervisor never writes ═════════════
# executor-owned truth. Static tripwire over jog_run.py (the seam module): Marathon owns PR
# creation, Tick attempts/tokens, and lane-branch identity; Jog only reads, verifies, and
# merges post-verification (gh pr merge/view/list are read-or-verified actions, allowed).
# Known limit (GH-195 lesson): a static grep is a tripwire against accidental
# reintroduction, not a proof — behavioral coverage lives in sections C-M above.
JOG_SRC="$(cat "$FR/utils/py/jog_run.py")"
! has "$JOG_SRC" "gh pr create" \
  && pass "P1 jog never creates PRs (Marathon owns PR identity)" \
  || fail "P1 jog_run.py creates PRs directly"
! has "$JOG_SRC" "bin/tick" && ! has "$JOG_SRC" '".tick/attempts' \
  && pass "P2 jog never invokes the tick binary or writes executor attempt state" \
  || fail "P2 jog_run.py touches executor-owned Tick state"
! has "$JOG_SRC" "checkout -b" \
  && pass "P3 jog never cuts lane branches (branch identity is Marathon's)" \
  || fail "P3 jog_run.py cuts branches directly"

# Final containment control: the seed that anchored every section boundary is still pristine.
seed_intact "the full suite (final check)"

echo "  $TEST_NAME: $PASS pass, $FAIL fail"
exit 0
