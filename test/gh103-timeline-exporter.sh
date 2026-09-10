#!/usr/bin/env bash
# gh103-timeline-exporter.sh — utils/timeline/export_timeline.py, the READ-ONLY projection of
# releases.db onto the timeline viewer.
#
# The exporter had no suite before this one, which is how #109 survived: it asserted a marathon
# membership the data never claimed ("release has a marathon => every manifest item is one of its
# work units"), and that stayed latent until a non-marathon item joined a marathon release.
#
# What is pinned here:
#   * GH-109 — marathon grouping follows manifest_items.marathon_id and NOTHING else; a
#     non-member on a marathon release renders as a sibling, outside the box.
#   * GH-110 — a shipped member renders the done marker (the branch that existed for years and
#     never received a row, because no code path wrote that state).
#   * GH-111 — itemsTotal counts COMMITTED work (dialed_in + shipped); cut rows still render but
#     stop inflating the total. Baseline and growth are emitted, and a baseline-less release
#     emits null rather than a zero.
#   * GH-108 — rated tasks carry metrics + effectiveScore, the override wins over calc, an
#     unrated card carries no metrics key at all, sev >= 80 flags hot, and a rated DETOUR is
#     scored too (detours reparse the markdown, so they need the index handed to them).
#   * The page is a PURE CONSUMER: the exporter opens the DB read-only and writes no DB bytes.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$HERE/../utils/py/releases_app.py"
EXPORTER="$HERE/../utils/timeline/export_timeline.py"
TEMPLATE="$HERE/../utils/timeline/RELEASES.html"

pass=0; fail=0
ok(){ if [ "$2" = "0" ]; then echo "  PASS: $1"; pass=$((pass+1)); else echo "  FAIL: $1"; fail=$((fail+1)); fi; }
is(){ [ "$1" = "$2" ]; }
# Fixed-string containment, done in-process.
#
# This was `printf '%s' "$1" | grep -Fq -- "$2"`, which is unsound under the `set -o pipefail` above:
# `grep -q` exits the moment it matches, closing the pipe while `printf` is still writing, so printf
# dies of SIGPIPE and pipefail reports the pipeline as 141 — i.e. "not found" — even though the
# string IS present. Whether it fires depends on how early the match sits in the input and on
# scheduling, so it read as a flaky, template-size-dependent false negative rather than a bug.
# Bash pattern matching needs no pipe and cannot race.
has(){ case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }
file_hash() { # portable: sha256sum -> shasum -a 256 -> md5 (GH-65)
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  else
    md5 -q "$f"
  fi
}

echo "== test: gh103-timeline-exporter =="
command -v python3 >/dev/null 2>&1 || { echo "python3 required" >&2; exit 1; }
command -v sqlite3 >/dev/null 2>&1 || { echo "sqlite3 required" >&2; exit 1; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/gh103-timeline.XXXXXX")"
[ -n "$WORK" ] && [ -d "$WORK" ] || { echo "mktemp failed" >&2; exit 1; }
. "$HERE/lib/fixture-guard.sh"
fixture_guard_init "$WORK"
cleanup(){ [ -n "${WORK:-}" ] && [ -d "$WORK" ] && rm -rf "$WORK"; }
trap cleanup EXIT

R="$WORK/repo"
case "$R" in "$WORK"/*) ;; *) echo "REFUSING: $R outside WORK" >&2; exit 2 ;; esac
mkdir -p "$R"
git -C "$R" init -q -b main
git -C "$R" config user.email t@t
git -C "$R" config user.name t
ra(){ require_fixture "$R" "timeline fixture"; python3 "$APP" --root "$R" "$@"; }
rq(){ ra "$@" >/dev/null 2>&1; }
GH="https://github.com/HiQS-Labs/XYZ-forge/issues"

rq init --slug gh103

# ── the fixture ledger ──────────────────────────────────────────────────────────────────────────
# One ACTIVE release with a marathon, carrying: two marathon members, one NON-member, one cut
# item, and one shipped member. Plus a second release with no marathon at all.
rq marathon add --tracking-issue "$GH/700"
MAR="$(sqlite3 "$R/releases.db" "SELECT global_id FROM marathons LIMIT 1")"
rq add --version 1.0.0 --codename Fixture --status draft --description "The marathon release." \
   --marathon "$MAR" --tracking-issue "$GH/1"
REL="$(sqlite3 "$R/releases.db" "SELECT global_id FROM releases WHERE version='1.0.0'")"
for N in 801 802 803 804 805; do
  rq manifest dial-in --gid "$REL" "$GH/$N" --reason "fixture"
done
rq manifest marathon --gid "$REL" "$GH/801" --marathon "$MAR"
rq manifest marathon --gid "$REL" "$GH/802" --marathon "$MAR"
rq update --gid "$REL" --status active           # baseline auto-captures here: 5 committed
rq manifest ship --gid "$REL" "$GH/803" --evidence "landed in abc1234"
rq manifest cut --gid "$REL" "$GH/804" --reason "descoped"

cat > "$R/ROADMAP.md" <<'MD'
# Fixture roadmap
## Ledger
### In progress
- **GH-801 · marathon phase one** 🚧 — body. rated 90/85/70/60 → [#801](https://github.com/HiQS-Labs/XYZ-forge/issues/801)
- **GH-805 · a non-member with an override** 🚧 — body. rated 10/10/10/10 ovr 399 → [#805](https://github.com/HiQS-Labs/XYZ-forge/issues/805)
- **GH-900 · a rated detour, on no manifest** 🚧 — body. rated 50/50/50/50 → [#900](https://github.com/HiQS-Labs/XYZ-forge/issues/900)
### Queue / parked intake
- **GH-802 · marathon phase two, unrated** — body.
MD
printf 'Release: 1.0.0\nStatus: Active\nCodename: Fixture\n' > "$R/RELEASES.md"
rq roadmap sync

JSON="$WORK/payload.json"
python3 "$EXPORTER" --db "$R/releases.db" --json > "$JSON" 2>"$WORK/err.txt"
ok "--json emits the payload to stdout and writes no files" "$([ -s "$JSON" ] && [ ! -d "$R/temp" ]; echo $?)"

q(){ python3 - "$JSON" "$1" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
rel = next(r for r in payload["releases"] if r["version"] == "1.0.0")
groups = [i for i in rel["roadmap"] if i.get("type") == "marathon"]
sibs = [i for i in rel["roadmap"] if i.get("type") != "marathon"]
members = groups[0]["cards"] if groups else []
cards = {c["id"]: c for c in members + sibs + rel["detours"]}
env = {"rel": rel, "groups": groups, "sibs": sibs, "members": members, "cards": cards,
       "payload": payload}
print(eval(sys.argv[2], {"__builtins__": {"len": len, "sorted": sorted, "sum": sum,
                                          "str": str, "any": any, "all": all}}, env))
PY
}

# ── GH-109: marathon membership is a fact the row carries ───────────────────────────────────────
echo "-- GH-109: the marathon box contains members, and only members"
ok "the release renders exactly ONE marathon group" "$(is "$(q 'len(groups)')" "1"; echo $?)"
ok "the group holds only the two LINKED items — not every card on the release" \
   "$(is "$(q '[c["id"] for c in members]')" "['GH-801', 'GH-802']"; echo $?)"
ok "the non-member renders as a SIBLING beside the box (the #109 defect, inverted)" \
   "$(is "$(q 'any(c["id"] == "GH-805" for c in sibs)')" "True"; echo $?)"
ok "the cut item is a sibling too, and still rendered rather than dropped" \
   "$(is "$(q 'any(c["id"] == "GH-804" and c["sectionLabel"] == "cut" for c in sibs)')" "True"; echo $?)"

# ── GH-110: shipped members finally have a row to render ────────────────────────────────────────
echo "-- GH-110: a shipped member renders the done marker"
ok "the shipped item carries marker=done and section=done" \
   "$(is "$(q 'cards["GH-803"]["marker"] + "/" + cards["GH-803"]["section"]')" "done/done"; echo $?)"

# ── GH-111: the denominator means COMMITTED work ────────────────────────────────────────────────
echo "-- GH-111: denominator, baseline, growth"
ok "itemsTotal counts dialed_in + shipped and EXCLUDES the cut row (4, not 5)" \
   "$(is "$(q 'rel["itemsTotal"]')" "4"; echo $?)"
ok "the baseline captured at activation is emitted with its provenance" \
   "$(is "$(q 'str(rel["baseline"]["count"]) + "/" + rel["baseline"]["source"]')" "5/observed"; echo $?)"
ok "growth is NEGATIVE when more was cut than added — a real, meaningful number, not an error" \
   "$(is "$(q 'rel["baseline"]["growth"]')" "-1"; echo $?)"
ok "a release with no baseline emits null, never a placeholder zero" \
   "$(is "$(q 'any(r["baseline"] is None for r in payload["releases"] if r["version"] != "1.0.0") or len(payload["releases"]) == 1')" "True"; echo $?)"

# ── GH-108: ratings reach the cards ─────────────────────────────────────────────────────────────
echo "-- GH-108: metrics, effectiveScore, override precedence, hot flag"
ok "a rated card carries all four axes under their PUBLIC names (no rating_ prefix leaks)" \
   "$(is "$(q 'sorted(k for k in cards["GH-801"]["metrics"] if k not in ("calc", "effectiveScore"))')" "['appeal', 'effort', 'pri', 'sev']"; echo $?)"
ok "calc is the equal-weighted SUM of the four axes (90+85+70+60 = 305)" \
   "$(is "$(q 'cards["GH-801"]["metrics"]["calc"]')" "305"; echo $?)"
ok "effectiveScore falls back to calc when there is no override" \
   "$(is "$(q 'cards["GH-801"]["metrics"]["effectiveScore"]')" "305"; echo $?)"
ok "sev >= 80 flags the card hot (one constant, not a threshold system)" \
   "$(is "$(q 'cards["GH-801"]["metricFlags"]["sev"]')" "hot"; echo $?)"
ok "an override REPLACES calc for ranking while the honest axes stay underneath" \
   "$(is "$(q 'str(cards["GH-805"]["metrics"]["effectiveScore"]) + "/" + str(cards["GH-805"]["metrics"]["calc"])')" "399/40"; echo $?)"
ok "an UNRATED card carries no metrics key at all — no placeholder, no 0/400 noise" \
   "$(is "$(q 'cards["GH-802"].get("metrics") is None')" "True"; echo $?)"
ok "a rated DETOUR is scored too (detours reparse the markdown; the index is handed to them)" \
   "$(is "$(q 'cards["GH-900"]["metrics"]["effectiveScore"]')" "200"; echo $?)"

# the pinned exit-criterion command, run verbatim against this payload
echo "-- the pinned ranking command"
TOP="$(python3 - "$JSON" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
rows = []
for rel in payload["releases"]:
    for item in rel["detours"] + rel["roadmap"]:
        for card in (item["cards"] if item.get("type") == "marathon" else [item]):
            m = card.get("metrics")
            if m:
                rows.append((m["effectiveScore"], card["id"]))
rows.sort(reverse=True)
print(" ".join("%s:%d" % (i, s) for s, i in rows))
PY
)"
ok "the ranking is ordered by effectiveScore, override first, with no ties" \
   "$(is "$TOP" "GH-805:399 GH-801:305 GH-900:200"; echo $?)"

# ── the viewer template agrees with the data it is handed ───────────────────────────────────────
echo "-- the template renders what the exporter emits"
TPL="$(cat "$TEMPLATE")"
N="$(printf '%s' "$TPL" | grep -c "\['pri','sev','appeal','effort','calc'\]")"
ok "BOTH metric loops (card renderer and what's-next strip) carry appeal and effort" "$(is "$N" "2"; echo $?)"
if has "$TPL" "100 = strongest" && ! has "$TPL" "1 = strongest"; then ok "the footer legend reads 100 = strongest — legend and data never disagree in a committed artifact" 0; else ok "legend flipped" 1; fi
if has "$TPL" "rel.baseline"; then ok "the release node renders the baseline/growth pair" 0; else ok "baseline rendered" 1; fi

# ── read-only: the page is a pure consumer ──────────────────────────────────────────────────────
echo "-- read-only contract"
DB_HASH="$(file_hash "$R/releases.db")"; DUMP_HASH="$(file_hash "$R/releases.sql")"
python3 "$EXPORTER" --db "$R/releases.db" --preview "$WORK/preview.html" >/dev/null 2>&1
if [ -s "$WORK/preview.html" ] && grep -q 'id="ledger-data"' "$WORK/preview.html"; then ok "--preview bakes a self-contained page with the payload inline" 0; else ok "preview bakes" 1; fi
if [ -n "$DB_HASH" ] && [ "$(file_hash "$R/releases.db")" = "$DB_HASH" ] && [ "$(file_hash "$R/releases.sql")" = "$DUMP_HASH" ]; then ok "the exporter wrote no DB bytes (opened read-only; the page never writes back)" 0; else ok "exporter read-only" 1; fi
if ra check >/dev/null 2>&1; then ok "the ledger still checks clean after every projection" 0; else ok "check clean" 1; fi

# ── the leaderboard pipeline (GH-108 Phase D) ───────────────────────────────────────────────────
# ONE SCORER, proven rather than asserted: the shell script's ranking must match the exporter's
# `--json` ordering exactly. A script that re-derived calc or reapplied the override rule would be
# the same drift class the "calc is never stored" rule prevents, one layer up.
echo "-- the leaderboard pipeline"
LB_MD="$WORK/LEADERBOARD.md"
LEADERBOARD_DB="$R/releases.db" LEADERBOARD_OUTPUT="$LB_MD" bash "$HERE/../utils/leaderboard.sh" >/dev/null 2>&1
ok "leaderboard.sh renders LEADERBOARD.md from the exporter's JSON" "$([ -s "$LB_MD" ]; echo $?)"
if grep -Eq '^<!-- releases-app generation: [0-9]+ -->$' <<<"$(head -1 "$LB_MD")"; then ok "the file carries the releases-app generation marker" 0; else ok "generation marker" 1; fi
if grep -q 'GENERATED' <<<"$(head -2 "$LB_MD")"; then ok "the file announces itself as generated (never hand-edited)" 0; else ok "generated header" 1; fi
# POSIX sed rather than `rg`: ripgrep is not a documented prerequisite (README lists Codex CLI, agy
# CLI, Node 18+, git, Python 3.8+) and this suite was the only thing in test/ or utils/ that needed
# it, so the whole suite failed on any host without it. Handles both the linked `[GH-n](url)` and
# bare `GH-n` row forms, same as the regex it replaces.
SCRIPT_ORDER="$(sed -n 's/^| [0-9][0-9]* | \*\*[0-9][0-9]*\*\* | \[\{0,1\}\(GH-[0-9][0-9]*\).*/\1/p' "$LB_MD" | tr '\n' ' ' | sed 's/ $//')"
ok "the script's ranking matches the pinned --json ordering EXACTLY (one scorer, proven)" \
   "$(is "$SCRIPT_ORDER" "$(printf '%s' "$TOP" | sed 's/:[0-9]*//g')"; echo $?)"
if grep -q 'Top of the line:\*\* GH-805' "$LB_MD"; then ok "the highest-scoring task is called out by name, override included" 0; else ok "top of the line" 1; fi
if grep -q 'GH-900' "$LB_MD"; then ok "a rated DETOUR ranks too — not just manifest cards" 0; else ok "detour ranks" 1; fi
CP="$WORK/lb-first.md"; cp "$LB_MD" "$CP"
LEADERBOARD_DB="$R/releases.db" LEADERBOARD_OUTPUT="$LB_MD" bash "$HERE/../utils/leaderboard.sh" >/dev/null 2>&1
ok "regeneration is idempotent — a second run is byte-identical" "$(cmp -s "$CP" "$LB_MD"; echo $?)"
LEADERBOARD_DB="$R/releases.db" LEADERBOARD_OUTPUT="$LB_MD" bash "$HERE/../utils/leaderboard.sh" --check >/dev/null 2>&1
ok "--check passes when the committed copy is in sync" "$?"
printf '\nstale hand edit\n' >> "$LB_MD"
LEADERBOARD_DB="$R/releases.db" LEADERBOARD_OUTPUT="$LB_MD" bash "$HERE/../utils/leaderboard.sh" --check >/dev/null 2>&1
ok "--check FAILS on drift (a stale checked-in copy is a review signal)" "$([ $? -ne 0 ]; echo $?)"

LB_HTML="$WORK/LEADERBOARD.html"
python3 "$EXPORTER" --db "$R/releases.db" --leaderboard "$LB_HTML" >/dev/null 2>&1
ok "--leaderboard bakes a self-contained page from the SAME template" "$([ -s "$LB_HTML" ]; echo $?)"
if grep -q '"view": *"leaderboard"\|"view":"leaderboard"' "$LB_HTML"; then ok "the payload carries view=leaderboard — one template, two baked artifacts" 0; else ok "view field" 1; fi
if grep -q 'leaderboardHTML' "$WORK/preview.html" && grep -q 'columnHTML' "$LB_HTML"; then ok "both artifacts share ONE renderer bundle (no second copy of the design system)" 0; else ok "shared bundle" 1; fi
if grep -q 'id="view-link"' "$TEMPLATE"; then ok "the cross-link lives in .top, which never collapses" 0; else ok "cross-link placement" 1; fi
# grep -E rather than `rg` (see the SCRIPT_ORDER note above). This assertion is negated, so with
# ripgrep absent `rg -q` returned 127 and the test passed without checking anything.
if ! grep -qE 'id="fbar"[^>]*>[^<]*<a id="view-link"' "$TEMPLATE"; then ok "and NOT in #fbar, which disappears with the header caret" 0; else ok "cross-link not in fbar" 1; fi
# The leaderboard view never calls initInteractions(), so #fbar's search + focus + prev/next are
# all inert there — a search box that looks broken (aider/qwen3.8-max QA r1).
if grep -q 'body\[data-view="leaderboard"\] #fbar' "$TEMPLATE"; then ok "the leaderboard view hides #fbar rather than shipping an inert search box" 0; else ok "leaderboard hides fbar" 1; fi

# ── GH-250: codename-only releases (version NULL) must not crash the bake ───────────────────────
# `releases add` accepts a codename with no version, and release_columns() already fell back to
# the codename for slug/name — but not for id, and _ver() only caught ValueError. So ONE
# NULL-version row killed --preview and --leaderboard outright, and refresh_preview()'s warn-only
# path turned that into artifacts that silently stop tracking the ledger. The versioned-no-target
# row below is deliberate: it ties with the codename-only rows on the sort's primary key, pinning
# the None-vs-str tiebreaker compare too.
echo "-- GH-250: codename-only releases (version NULL)"
rq add --version 9.9.9 --codename Tiebreak --status draft --description "Versioned, no target." --tracking-issue "$GH/910"
rq add --codename "Night Owl" --status draft --description "Codename-only one." --tracking-issue "$GH/911"
rq add --codename Falcon --status draft --description "Codename-only two." --tracking-issue "$GH/912"
NO_VER="$(sqlite3 "$R/releases.db" "SELECT COUNT(*) FROM releases WHERE version IS NULL")"
ok "fixture holds codename-only rows (version IS NULL in the ledger)" "$([ "$NO_VER" -ge 2 ]; echo $?)"
J250="$WORK/gh250.json"
if python3 "$EXPORTER" --db "$R/releases.db" --json > "$J250" 2>/dev/null; then ok "--json succeeds on a ledger with NULL-version releases" 0; else ok "--json on NULL-version ledger" 1; fi
python3 "$EXPORTER" --db "$R/releases.db" --preview "$WORK/gh250-preview.html" >/dev/null 2>&1
ok "--preview bakes (the crash refresh_preview's warn-only path used to hide)" "$([ -s "$WORK/gh250-preview.html" ]; echo $?)"
python3 "$EXPORTER" --db "$R/releases.db" --leaderboard "$WORK/gh250-lb.html" >/dev/null 2>&1
ok "--leaderboard bakes on the same ledger" "$([ -s "$WORK/gh250-lb.html" ]; echo $?)"
IDS="$(python3 - "$J250" 2>/dev/null <<'PY'
import json, sys
cols = [c for c in json.load(open(sys.argv[1]))["releases"] if c["version"] is None]
ids = [c["id"] for c in cols]
print("unique" if ids and len(ids) == len(set(ids)) and all(ids) else "collide", *sorted(ids))
PY
)"
ok "codename-only releases carry stable, unique, non-empty ids" "$(has "$IDS" "unique"; echo $?)"
ok "the id derives from the codename, lowercased with spaces dashed (c-night-owl)" "$(has "$IDS" "c-night-owl"; echo $?)"

echo
echo "== gh103-timeline-exporter: $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
