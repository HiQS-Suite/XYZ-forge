**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)

> **ATTESTATION**
> Model: gpt-5.6-sol
> Provider: openai
> Sandbox: read-only

Reading additional input from stdin...
OpenAI Codex v0.153.4
--------
workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a08c4b-8a1a-7933-804a-d819e21730a3
--------
user
You are an INDEPENDENT advisor in a one-shot cross-model consult. Another model is answering the SAME question separately and a coordinator will reconcile both answers, so give your own honest, specific read — do not hedge toward a consensus you cannot see. Read any repo files the question references (cite file:line). Respond with: (1) a short direct ANSWER; (2) graded FINDINGS — [Blocker]/[Should]/[Nit]/[Pass] — where applicable; (3) a one-line RECOMMENDATION. You are ADVISORY ONLY: output your analysis as text; do not rely on writing files (you are running in a throwaway copy).

=== CONSULT QUESTION ===
Please perform a final QA review of GH-496 PR 2 (Phase 2: Single Reconciliation Owner, View Decoupling & Pre-Merge Closeout Checks).

Review the diff between development and HEAD:
1. Single reconciliation owner:
   - Hosted wave-reconcile.yml is primary landing writer.
   - Local wave_reconcile.py fails closed (exit 8) if hosted run is in flight.
   - --force-local-reconcile overrides locally, but is hard-rejected inside GITHUB_ACTIONS=true (exit 2).
2. View decoupling & generation stamping:
   - ROADMAP-DASHBOARD.md line 1 embeds <!-- releases-app generation: <N> -->.
   - dashboard-staleness-guard allows view commits only if renderers change or inside GITHUB_ACTIONS=true.
   - Routine task branches do not commit view files.
3. Pre-merge closeout checks:
   - wave_reconcile.py --pre-merge verifies frontmatter (owner, status), substantive Lessons Learned (exit 5), and committed test receipts in Git tree at HEAD (exit 6).
4. Marathon plan fingerprinting:
   - Skips redundant marathon-plan.sh when canonical inputs match .tick/marathon-plan.fingerprint.
   - Generated MARATHON-PLAN-*.md excluded from input hash.
   - .tick/marathon-plan.fingerprint tracked in RollbackJournal so it rolls back cleanly on error.
5. Zero SQLite binary untracking: Strictly reserved for PR 3.

Are there any remaining bugs, edge cases, or regressions? Is the PR ready to merge?
codex
I’m applying the codebase-memory workflow for verified structural evidence and the debug-mantra QA discipline because this is a final regression review. I’ll inspect the development…HEAD diff, trace the affected paths, and cite exact source lines; I’ll remain read-only.
exec
/bin/zsh -lc "sed -n '1,240p' /Users/noelsaw/.codex/skills/codebase-memory/SKILL.md && sed -n '1,260p' /Users/noelsaw/.codex/skills/debug-mantra/SKILL.md && sed -n '1,220p' ROUTER.md && sed -n '1,180p' GUIDING-PRINCIPLES.md" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 0ms:
---
name: codebase-memory
description: "Use the codebase knowledge graph for structural code queries. Triggers on: explore the codebase, understand the architecture, what functions exist, show me the structure, who calls this function, what does X call, trace the call chain, find callers of, show dependencies, impact analysis, dead code, unused functions, high fan-out, refactor candidates, code quality audit, graph query syntax, Cypher query examples, edge types, how to use search_graph."
---

# Codebase Memory — Knowledge Graph Tools

Graph tools return precise structural results in ~500 tokens vs ~80K for grep.

## Quick Decision Matrix

| Question | Tool call |
|----------|----------|
| Who calls X? | `trace_path(direction="inbound")` |
| What does X call? | `trace_path(direction="outbound")` |
| Full call context | `trace_path(direction="both")` |
| Find by name pattern | `search_graph(name_pattern="...")` |
| Dead code | `search_graph(max_degree=0, exclude_entry_points=true)` |
| Cross-service edges | `query_graph` with Cypher |
| Impact of local changes | `detect_changes()` |
| Risk-classified trace | `trace_path(risk_labels=true)` |
| Text search | `search_code` or Grep |

## Exploration Workflow
1. `list_projects` — check if project is indexed
2. `get_graph_schema` — understand node/edge types
3. `search_graph(label="Function", name_pattern=".*Pattern.*")` — find code
4. `get_code_snippet(qualified_name="project.path.FuncName")` — read source

## Tracing Workflow
1. `search_graph(name_pattern=".*FuncName.*")` — discover exact name
2. `trace_path(function_name="FuncName", direction="both", depth=3)` — trace
3. `detect_changes()` — map git diff to affected symbols

## Evidence Tiers
- **Scout (Tier 1):** fast positive lookup with few graph calls and targeted source checks. Treat results as provisional; never make absence, exhaustive, dead-code, or complete-impact claims.
- **Verify (Tier 2, default):** task-directed searches, relevant trace directions, exact snippets for material claims, and all relevant result pages.
- **Auditor (Tier 3):** bounded-scope full verification with a current graph generation, complete relevant pagination, both call directions and broader relationships when material, plus explicit unresolved limitations.
- **Every tier:** after candidate paths are known, call `check_index_coverage` once with every evidence path. For negative or exhaustive claims also include the relevant scopes. A clean result means no recorded gap, not proof of completeness. For partial, skipped, excluded, stale, pending, or unknown coverage, read/grep the reported ranges or scope before relying on the graph.

## Sessions and Subagents
- At session start or after compaction, call `list_projects`/`index_status` before structural exploration, then choose Scout, Verify, or Auditor for the task.
- Before delegating, query the graph and coverage in the parent. Pass the tier, exact project, generation/freshness, bounded scope, queries and pagination state, qualified symbols, paths, call-chain findings, coverage ranges/reasons, source fallback already performed, and unresolved questions to the child.
- Runtimes such as Hermes isolate child context: put those graph findings in the `context` argument to `delegate_task`; do not assume the child inherits MCP access or the parent's conversation.
- A child without MCP tools must not call or claim MCP access. It should work from the supplied evidence and use read/grep on exact source, especially every reported missed-coverage range.

## Quality Analysis
- Dead code: `search_graph(max_degree=0, exclude_entry_points=true)`
- High fan-out: `search_graph(min_degree=10, relationship="CALLS", direction="outbound")`
- High fan-in: `search_graph(min_degree=10, relationship="CALLS", direction="inbound")`

## 15 MCP Tools
`index_repository`, `index_status`, `list_projects`, `delete_project`,
`search_graph`, `search_code`, `trace_path`, `detect_changes`,
`query_graph`, `get_graph_schema`, `get_code_snippet`, `get_architecture`,
`check_index_coverage`, `manage_adr`, `ingest_traces`

## Edge Types
CALLS, HTTP_CALLS, ASYNC_CALLS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD,
HANDLES, IMPLEMENTS, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, FILE_CHANGES_WITH,
SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER,
CONTAINS_PACKAGE

## Cypher Examples (for query_graph)
```
MATCH (a)-[r:HTTP_CALLS]->(b) RETURN a.name, b.name, r.url_path, r.confidence LIMIT 20
MATCH (f:Function) WHERE f.name =~ '.*Handler.*' RETURN f.name, f.file_path
MATCH (a)-[r:CALLS]->(b) WHERE a.name = 'main' RETURN b.name
```

## Gotchas
1. `search_graph(relationship="HTTP_CALLS")` filters nodes by degree — use `query_graph` with Cypher to see actual edges.
2. `query_graph` has a 100k row ceiling — add a Cypher `LIMIT` for broad queries or use `search_graph` pagination.
3. `trace_path` needs exact names — use `search_graph(name_pattern=...)` first.
4. `direction="outbound"` misses cross-service callers — use `direction="both"`.
5. `search_graph` results default to 50 per page — check `has_more` and use `offset`.
---
name: debug-mantra
description: "Four-mantra debugging discipline — reproduce, trace the fail path, falsify the hypothesis, cross-reference every breadcrumb. Recite the mantra block verbatim at the start of any debugging session, then apply the four steps in order before proposing any fix. Trigger on /debug-mantra and proactively whenever debugging starts — user reports a bug, says something is broken/throwing/failing, asks to debug/diagnose/investigate an issue, pastes a stack trace or error log, or asks an attribution question ('where is this coming from?', 'what posts/triggers/generates this?', 'why is X appearing?') where the answer is an unknown source to find, not just a crash to fix. Also trigger on /debug-mantra plan, and proactively when writing or reviewing the acceptance criteria of a plan, capture doc, or marathon plan — apply the same four mantras through the pivots in 'When the target is a plan, not a bug'. Adapted from: https://github.com/thananon/9arm-skills"
---

# Debug Mantra

Four-step discipline for any debug session. Recite verbatim, then apply in order. When the target is a plan rather than a bug, the same four steps apply read through the pivots in [When the target is a plan, not a bug](#when-the-target-is-a-plan-not-a-bug).

## Recite this — verbatim, as the first thing in your first response

> **Mantra:**
> 1. **First is reproducibility.** Can the issue — or the artifact — be reproduced or observed reliably?
> 2. **Know the fail path.** Debugger first; then source trace + knob enumeration; then in-code instrumentation.
> 3. **Question your hypothesis.** What would disprove it?
> 4. **Every run is a breadcrumb.** Cross-reference all of them.

Then begin work.

---

## 1. Reproduce reliably

Establish ground truth before anything else — a runnable repro for a failure, a direct look at the real artifact for an attribution question.

**Reproduce = observe the primitive ground truth, not your impression of it.** For a crash that's a failing test; for an *attribution* question ("what posts this?", "where does X come from?") it's inspecting the actual artifact — the real message, record, or raw bytes — **before** theorising about its origin. A screenshot, a rendered view, or a remembered detail is an **observation to verify, not an axiom to build on**: name it as assumption-zero and check it first. The cheapest disproof is usually looking straight at the thing — one query against the real object beats a sweep of the code that *might* have produced it. Beware visual grouping and other rendering artifacts: what looks like "one consolidated thing" may be many separate ones (or vice versa) — confirm against the raw object before any hypothesis inherits the shape.

- **Reliable repro** → capture the exact steps, inputs, and environment as a runnable artifact: failing test, curl script, CLI invocation, replay harness.
- **Flaky repro** → the bug is not yet debuggable. Raise the rate first: loop the trigger, parallelise, add stress, narrow timing windows, inject sleeps. 50% flake is debuggable; 1% is not.
- **No repro at all** → stop. Say so explicitly. Ask the user for env access, captured artifacts (HAR, log dump, core), or permission to instrument. Do **not** proceed to hypothesise.

Target: a fast (1–5 s), deterministic pass/fail signal. Pin time, seed the RNG, freeze network, isolate filesystem.

## 2. Know the fail path

Once reproducible, find *where* the code breaks and *what stops it from breaking*. The differential narrows the search. Try in this order — escalate only when the prior tactic fails.

1. **Attach a debugger.** If the env supports it, attach and step to the failure site. One breakpoint beats ten logs. Do this **before** turning any knobs.
2. **Source trace + knob enumeration.** If no debugger (or it can't reach the bug), trace the code path end-to-end and list every knob that can influence the outcome:
   - config flags, env vars, feature toggles
   - branch conditions, input shape
   - timing, concurrency, build options
   Each knob is a candidate axis to flip in the differential. Flip one at a time.
3. **In-code instrumentation.** If outside knobs can't move the failure, go inside: `printf` / log statements at the suspected fail site, dump the relevant internal state. Tag every probe with a unique prefix (e.g. `[DBG-a4f2]`) so cleanup is a single grep. Let the trace show where reality diverges from your model.

## 3. Falsify the hypothesis

When a candidate root cause surfaces, scrutinise it **before** testing it.

- Does it actually explain the symptom end-to-end? Walk it through.
- What is the simplest **proof**? What is the cleanest **disproof**?
- Run the **disproof first**. If the hypothesis survives, it's real. If it dies, you saved yourself from chasing a phantom.
- Generate 3–5 ranked hypotheses, not one. Single-hypothesis thinking anchors on the first plausible idea.

## 4. Every run is a breadcrumb

Maintain a running **ledger** of every experiment in this session. Each entry: what changed, what happened, what it ruled in or out.

- When a new hypothesis surfaces, walk the ledger. Does it hold for **every** prior observation, not just the most recent?
- If any past run contradicts it, the hypothesis is wrong or incomplete — refine or discard.
- When in doubt, design the **single experiment** whose outcome makes it certain. Run that next, instead of churning on adjacent runs.
- Update the ledger after every run. It is your memory across the session.

---

## When the target is a plan, not a bug

Invoked as `/debug-mantra plan`, or proactively when writing or reviewing the acceptance criteria of a plan, capture doc, or marathon plan. The four mantras apply unchanged and the recital stands verbatim — "the issue — or the artifact" includes the plan's own evidence. Each step is read through its pivot:

| Step | Debug reading | Plan pivot |
|---|---|---|
| 1. Reproduce | Runnable repro of the failure. | **Measured ground truth at plan time.** Every count, `file:line`, and live-state claim in the plan is re-run now, not remembered — the "measured, not assumed" evidence table in [#419's "What is actually unenforced today" section](https://github.com/HiQS-Labs/XYZ-forge/issues/419) is the shape. A recalled repo state is hypothesis-zero. |
| 2. Fail path | Trace the code that breaks. | **Trace the real path the plan changes**, before proposing: walk it and enumerate every caller and surface it touches. A criterion about a path nobody traced is a guess wearing a checkbox. |
| 3. Falsify | Disprove the root-cause hypothesis. | **Falsify the acceptance criteria.** Each criterion must name how it fails — a criterion that cannot fail is decorative, and one an empty input satisfies passes vacuously. Specify the red control *and where its evidence will land* (`test/baselines/` negative-control pattern). Rank 3–5 alternatives for the load-bearing design choice and name the strongest counterargument ([#419](https://github.com/HiQS-Labs/XYZ-forge/issues/419)'s "Open question for the reviewers" block is the pattern). |
| 4. Breadcrumbs | Session experiment ledger. | **Recon ledger.** Record the greps, counts, and probes that grounded the plan, citable from the plan or its capture doc. Before finalizing, walk the ledger against what is already shipped — a plan resting on a stale claim (feature already exists, path already changed) inherits the stale claim. |

**The plan-only rule, and why pivot 3 is the strictest:** at plan time falsification is *specified*, not *performed* — strictly weaker evidence than a red control you have watched fire. That gap is why each criterion must name a destination for its red evidence: a planned red control that is not witnessed when implemented is a promise, not a control. Plan reviews have caught criteria "satisfiable by an empty pre-created file" and "satisfiable by a print statement while the defect persisted" — both passed review as written.

Scale rigor as ever: a one-line fix's plan needs a confirming observation, not the full table; a marathon or large-refactor plan needs every pivot. For large refactors this is the SOP "Arc planning" discipline applied debug-mantra-first.

## Operating rules

- Recite the mantra block **once** per debug session, in your first response. Do not re-recite mid-session.
- Recite **verbatim**. Never paraphrase or abridge the recital.
- If the user says "skip the mantra" → skip the recital but still apply the four steps silently.
- Apply the four steps **in order**:
  - Do not propose a fix before #1 is satisfied (reliable repro exists).
  - Do not start testing hypotheses before #2 has narrowed the fail path.
  - Do not commit to a hypothesis before #3 has tried to disprove it.
  - Do not declare a hypothesis correct until #4 confirms it against every prior breadcrumb.
- **Scale rigor to the bug.** The gate is on *evidence*, not ceremony: a trivially obvious defect — a typo, a stack trace pointing straight at the line — needs a confirming **observation**, not necessarily a runnable harness or a written ledger. The burden stays on a direct look, never on assumption.
- If you catch yourself proposing a fix without a reliable repro, stop and return to step 1.
- If you catch yourself building on an unverified observation ("it's obviously X", "that's clearly one Y") — especially one drawn from a screenshot, a rendered view, or memory — stop and inspect the raw artifact first. The impression is hypothesis-zero, not ground truth, and a single direct look at the real object usually settles it faster than any search of the code that might explain it.
- The mantra is a constraint **you** carry through the session — not advice to deliver back to the user.
# ROUTER.md

This file is the first entry point for an AI agent working in this repo: it tells you what to read, what to run, and which files are canonical.

## Role split

- `ROUTER.md` = startup order and canonical entry points
- `GUIDING-PRINCIPLES.md` = XYZ Forge’s product purpose, scope and *why*, and the canonical North Star: durable, reversible, DRY — extend what exists rather than forking a parallel system
- `AGENTS.md` = behavioral rules, decision quality, reversibility, blast radius, proof
- `README.md` = human-facing repo/product overview
- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`); the RELEASES DB (`releases.db` via `releases.sql`) is the source of truth (`ROADMAP.md` retired per GH-269)
- `CHANGELOG.md` = the end-of-iteration running log (first-class PDDA artifact; governed by `PROJECT/PDDA.md`)
- `RELEASES.md` = forward-looking release-planning ledger (first-class PDDA artifact; governed by `PROJECT/PDDA.md`)
- `HARNESS-MODELS-REGISTRY.md` = evaluated agent harnesses, supported model grades (A/B/C), and CLI flags
- `MACHINE-CONTRACTS.md` = the Jog ↔ Preflight ↔ Marathon machine-contract reference (`marathon-invocation@1`, `marathon-drive/result@1`) and their version/deprecation policy
- `PROJECT/**` docs = canonical execution detail for a specific effort
- `PROJECT/PDDA.md` = imported PDDA document contract adopted by XYZ (incl. CHANGELOG); protected local adaptations are reviewed under the repo-owned sync policy
- `PROJECT/CONSTITUTION.md` = locally maintained PDDA-layer policy of record, with verified-success, reversibility and local-first safeguards adopted by XYZ; advisory-only LLM checking is PDDA-specific and does not replace XYZ relay approval
- `PROJECT/DO-NOT-BUILD.md` = locally maintained PDDA anti-scope; XYZ product scope remains in GUIDING-PRINCIPLES, not a blanket prohibition on coordination or execution
- `PROJECT/PDDA-MODE-GUIDE.md` = XYZ-maintained guidance for selecting PDDA’s enforcement mode
- `PROJECT/PDDA-SYNC-POLICY.md` = binding XYZ-owned review policy for PDDA dependency updates

## Startup sequence

1. Read `ROUTER.md` to understand the repo's operating order and canonical files. -> expect one clear next file, not a repo-wide scavenger hunt.
2. Read `AGENTS.md` before making recommendations or edits. -> expect explicit assumptions, a reversibility read on consequential changes, and verified claims only.
3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is retired — the RELEASES DB is the single source of truth.)
4. Read the linked `PROJECT/**` document that owns the work you are touching. -> expect the near-top `## Status` table to tell you what was just completed and what is next.
5. If the task touches project docs, read `PROJECT/PDDA.md` and follow the PDDA contract. -> expect `PROJECT/2-WORKING` docs to have frontmatter, the exact status table, and QA gates when phased.
6. Before reporting success on code or runtime work, run `./validate.sh`. -> expect the suite to stay green; do not claim completion if it fails or was skipped.
7. Before reporting success on doc-hygiene or roadmap work, run `utils/pdda/pdda.sh run` (or the relevant `utils/pdda/pdda.sh <check>` subcommand). -> expect deterministic findings first, then any LLM review.

## Canonical rules

- Do not put phase checklists, build steps, or deep execution notes in the roadmap ledger.
- Every active doc in `PROJECT/2-WORKING/` must be reflected by a pointer row in the roadmap ledger (the RELEASES DB) that links it. A working doc that should not appear opts out with `roadmap_exempt: true` in its frontmatter. Governance lives in `PROJECT/PDDA.md` → "ROADMAP contract".
- Promoting a capture from `1-INBOX` to `2-WORKING` is a DB-verb procedure (`roadmap repoint` + `roadmap update` / `roadmap move`), never a markdown edit — the exact steps and their two known gate traps (`updated:` frontmatter key, bullet-format `raw_text`) live in `SOP.md` → "Step 1b: Promoting a capture from 1-INBOX to 2-WORKING (releases-mode)".
- Every captured GitHub issue doc in `PROJECT/1-INBOX/GH-*.md` must also be parked as a queue row immediately at intake — `python3 utils/py/releases_app.py roadmap add --issue-num N --issue-url U --title T --created YYYY-MM-DD --doc-path P` (or `hq park`, which routes there automatically in this repo) — then promoted or removed later. Governance lives in `PROJECT/PDDA.md` → "GitHub issue intake" + "ROADMAP contract".
- Do not create a second competing plan when a canonical `PROJECT/**` doc already exists.
- Issue-first: any change beyond a **2–3 line** fix opens a GitHub issue first, then a pointer doc **named after the issue** (`GH-<number>-VERY-SHORT-DESC.md`, e.g. `GH-1234-SHOWME-COMMAND.md`), and that capture is **parked in the roadmap ledger immediately** (`releases roadmap add`) before execution begins. The issue is the signal stream; the pointer doc is the execution surface of record. Genuinely trivial edits (≤2–3 line fixes, typos, path repoints, doc-only one-liners) are exempt. Governed by `PROJECT/PDDA.md` → "GitHub issue intake".
- Runtime triage labels: since the `XYZ_PYTHON` flip the harness is dual-runtime, so any harness-bug issue gets a `runtime:` label — `runtime:python` (default path), `runtime:bash` (`XYZ_PYTHON=0` opt-out), or `runtime:parity` (the twins diverge). `/file-xyz-bug` harvests and applies it; for in-repo intake (`/triage`, hand-filed `gh issue create`) apply it by hand. Omit rather than guess — a wrong runtime tag misroutes triage.
- **`GH-<n>` numbering spans two repos.** This repo succeeded [`Claude-AI-Tools-Ventura-County/xyz-3-agents-swarm`](https://github.com/Claude-AI-Tools-Ventura-County/xyz-3-agents-swarm) and the migration did **not** renumber references, so a `GH-<n>` in a source comment, test name, or CHANGELOG entry may belong to either repo. Upstream ledger entries are preserved verbatim in [`docs/ROADMAP-UPSTREAM-ARCHIVE.md`](docs/ROADMAP-UPSTREAM-ARCHIVE.md), which states its own numbering caveat and is not parsed by anything. Where an upstream number is cited from code that ships here, mirror it as a closed `[upstream archive]` issue so the citation resolves locally (#407, #408 are the pattern) rather than editing the comment. Raised externally as GH-406 §3.1.
- Do not override deterministic PDDA findings with prose.
- Do not report a win you did not verify with the relevant script or test.
- Update `CHANGELOG.md` at the end of each iteration; its governance lives in `PROJECT/PDDA.md` — do not re-specify CHANGELOG rules in `AGENTS.md` or elsewhere.

## Command rails

For repo correctness:

```bash
bash githooks/install.sh        # ONCE PER CLONE — wires the pre-push gate (GH-544)
bash githooks/install.sh --check # is this clone gated? exit 1 if not
./validate.sh              # the gate — PARALLEL by default (GH-544), auto-sized to the host (GH-35)
./validate.sh --print-mode # which mode would this host pick, and why — runs nothing
./validate.sh --sequential # force the sequential run (~16 min)
./validate.sh --tier 2 --subsystem hq   # GH-35: one subsystem's focused suites (pre-push speed, NOT evidence)
./validate.sh --auto       # GH-35: classify the git diff, run the minimal safe tier (fails closed to 3)
./validate.sh --throttle   # GH-35: 2 workers under nice — quiet-machine mode (--burst restores full width)
bash ci-local.sh           # the QUALIFYING run — sequential + writes the gate record (GH-509/GH-536)
```

**Both gate entry points refuse to run from a linked git worktree (GH-45)** — a worktree shares
the parent clone's `.git`, and an observed suite escape corrupted the parent (core.bare, origin,
remote refs, development). Run the gate from a separate disposable full clone; `XYZ_ALLOW_WORKTREE_GATE=1` is the
announced override for disposable runs.

**Local push checks and hosted CI both apply.** This repository is public; the workflow covers
pushes and pull requests to `main` and `development`. Hosted macOS promotion evidence requires an
actual passing run for the exact commit; the Ubuntu canary remains advisory. Install the local
hook with `githooks/install.sh` for each clone — `.git/hooks/` does not travel with a clone. One
installation covers that clone’s branches and linked worktrees. Run mutation-heavy gates and
pushes that invoke them from a separate disposable full clone, as required by AGENTS.md.
Bypasses (`git push --no-verify`, `XYZ_SKIP_PREPUSH=1`) announce that the local gate was skipped.
**Draft-review publication is distinct from merge readiness (GH-487):** an operator-requested WIP
draft may use a bypass only with (a) current focused evidence for the changed area — e.g. the
mapped subsystem's suites run green — (b) the hook's skipped-gate disclosure echoed into the PR
description, and (c) merge readiness still outstanding. A bypassed push never authorises merge,
promotion, or teardown, and a published draft is never approval.

**Parallel became the default on 2026-08-14 (GH-544)** when the local gate was the only gate during
the private phase, and a 16-minute gate does not get run — it gets skipped, which is worse than a
3-minute one. **GH-35 (2026-08-18) rebalanced the width to `cores/2` (floor 2, cap 4) and put every
worker under `nice -n 10`** — the original `cores − 2` (up to 8) saturated developer machines badly
enough to wedge the editor; `--burst` buys the old full-core width back for unattended runs, and
`--throttle`/`--quiet-cpu` pins 2 workers. Ambient levers: `XYZ_VALIDATE_THROTTLE=1`,
`XYZ_VALIDATE_MAX_JOBS=N`, `XYZ_VALIDATE_PARALLEL` (flags > MAX_JOBS > THROTTLE > PARALLEL > host
detection; malformed values exit 2 naming the variable). Below 4 cores, or where `xargs -P` is
unsupported, the run **falls back to sequential and says so** — every run prints the mode it chose
and the reason, so a fallback is never silent.

**GH-35 also added TIERED SELECTION on top, as a separate axis from width.** `utils/ci-route.sh`
owns one fail-closed subsystem registry (hq, releases, telemetry, ate, swe-diagram, pdda,
agent-chorus, standup, skills-army-hq); a push the classifier rates `tier=2` runs only those focused
suites at the boundary, `--tier 1` runs the docs gate, and everything else — unknown paths, unclaimed
test edits, kernel surfaces — runs the full suite. `--auto` classifies a local diff the same way.
Tiers 1 and 2 are pre-push speed and are labelled NOT promotion evidence; only `ci-local.sh`'s
sequential full run qualifies (GH-509).

**What still qualifies a claim is unchanged.** `./validate.sh` in either mode is a self-check;
`ci-local.sh` is the run that writes the evidence record, it does **not** call `validate.sh`, and it
stays sequential. The macOS promotion boundary in `ci.yml` pins `--sequential` explicitly for the same
reason. GH-528 Phase 2 (multi-width stress evidence) is still **owed** — the flip was an operator
decision taken with that evidence outstanding, mitigated by the announced fallback rather than
discharged. See `PROJECT/2-WORKING/GH-528-TEST-SUITE-RECALIBRATION.md`, #509 and #544.

For document hygiene:

```bash
utils/pdda/pdda.sh run
```

For targeted PDDA debugging (subcommands of the single dispatcher):

```bash
utils/pdda/pdda.sh frontmatter
utils/pdda/pdda.sh status-table
utils/pdda/pdda.sh hardcoded-paths
utils/pdda/pdda.sh roadmap
utils/pdda/pdda.sh roadmap-coverage
utils/pdda/pdda.sh changelog
utils/pdda/pdda.sh stale
utils/pdda/pdda.sh issue-doc-sync   # warn-only: flags 2-WORKING/GH-*.md docs drifted from their GitHub issue state
utils/pdda/pdda.sh releases         # validate RELEASES.md, the OPTIONAL release-planning ledger (warn-only; skips a missing file)
utils/pdda/pdda.sh releases-current # read-only roll-up: RELEASES.md entries whose Status isn't "Shipped"
utils/pdda/pdda.sh quad-concepts    # opt-in: requires a "## Quad Concepts" section of 1-4 bullets (lever: .pdda-quad / PDDA_QUAD)
utils/pdda/pdda.sh glance           # read-only roll-up: title + Quad Concepts for each PROJECT/2-WORKING doc
utils/pdda/pdda.sh gh-refresh       # refresh the cached GitHub issue-state file issue-doc-sync reads offline (needs gh)
utils/pdda/pdda.sh catchup          # LLM repo triage + ROUTER.md recommendations (delegates to pdda-catchup.sh)
utils/pdda/pdda.sh doc-ready        # LLM readiness review — set PDDA_LLM_BIN (codex/claude/agy) for recommendations, else it self-skips
```

## The RELEASES DB — two subsystems, one ledger (GH-32 / GH-69)

`releases.db` + `releases.sql` hold TWO mirrored subsystems, both operated through ONE CLI,
`utils/py/releases_app.py` (alias: the `/releases` skill). Read
[RELEASES-DB-FAQS.md](RELEASES-DB-FAQS.md) before merging either file — the SQLite binary is
derived; the SQL dump is what git actually merges, and a conflicted merge has a one-command
resolver (`utils/releases-merge-resolve.sh`).

```bash
python3 utils/py/releases_app.py check          # trio consistency, receipt chain, crash recovery
python3 utils/py/releases_app.py next           # the next unshipped release, by target date
python3 utils/py/releases_app.py add|ship ...   # RELEASE writes — never hand-edit releases.sql
python3 utils/py/releases_app.py roadmap add ... # GH-238: park one issue as a roadmap row (the intake write path)
                                                #   GH-249: put `rated N/N/N/N [ovr N]` in --raw-text to score it
python3 utils/py/releases_app.py roadmap rate ...# GH-253: score a row that is ALREADY parked (--force to re-score)
python3 utils/py/releases_app.py roadmap list   # read the roadmap rows (--json for machine consumers)
python3 utils/py/releases_app.py roadmap sync   # LEGACY-mode only (mirrors ROADMAP.md); a guarded no-op in this repo
```

**Subsystem 1 — releases** (GH-32, Phase 0 side-by-side): the release ledger. App-managed writes
only; `RELEASES.md` is still the human file during the shadow phase.
**Subsystem 2 — the roadmap ledger** (GH-69 shadow → GH-238/GH-243 canonical → GH-269 retired ROADMAP.md): since the
`ROADMAP_SOURCE=releases` flip, `roadmap_items` IS the ledger — write rows with
`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`.
`ROADMAP.md` has been retired and removed. `roadmap sync` exists for legacy-mode repos only and
no-ops here by design (it would delete `add`-parked rows). Pinned by `test/gh69-roadmap-shadow.sh`,
`test/gh238-hq-releases-mode.sh`, and `test/gh269-roadmap-retired.sh`.

## Routing hints

- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
- If the task touches `releases.db`, `releases.sql`, or a merge conflict on either, start in [RELEASES-DB-FAQS.md](RELEASES-DB-FAQS.md); writes go through the CLI, never a hand-edit.
- If the task is about fresh GitHub intake or duplicate-prevention, start in the dashboard's queue section (or `releases roadmap list`), then follow the linked `PROJECT/1-INBOX/GH-*.md` capture doc.
- If the task is about document quality, active-doc lifecycle, roadmap sprawl, or automation policy, start in `PROJECT/PDDA.md`.
- If the task is about the CHANGELOG, provenance, or end-of-iteration logging, the governance is in `PROJECT/PDDA.md` (the "CHANGELOG.md — end-of-iteration record" contract).
- If the task is about release planning, ledger health, cleanup, authoring, or publishing, invoke `/releases`. It reads and synthesizes `RELEASES.md` first, then routes explicit requests into confirmation-gated cleanup, planning, or publication; governance is in `PROJECT/PDDA.md` (the "RELEASES.md — release ledger" contract). It conditionally points strategic drift to `/radar` and a frozen path-to-ship to `/finish-line` without duplicating either workflow.
- If the task is about the `tick` runtime, event projection, or multi-agent coordination kernel, start in `README.md`, then `bin/`, `src/`, `test/`, and the active project doc.
- If the task is about the **Aider ↔ OpenRouter** turn-taker lane (`relay-automation/aider-turn.sh` — an OpenAI-standard build lane discrete from Codex; `AIDER_MODEL`/`OPENROUTER_API_KEY`, `--builder aider`), start in `PROJECT/3-COMPLETED/GH-77-AIDER-OPENROUTER-LANE.md`. The shim owns the tick token ops (Aider can't run shell mid-turn), asserts token ownership before launching Aider, and runs Aider `--no-auto-commits` (the harness commits).
- If the task is about running, driving, or reviewing via the relay (`relay-automation/` — `relay-drive.sh`, `poll.sh`, the turn shims, `marathon*.sh`), **invoke the `relay-xyz` skill first — do not improvise the handoff or hand-roll a harness from `ls relay-automation/`.** The skill owns the locator, sandbox rules, exit codes, and the safety boundary; a `PreToolUse` guard (`relay-automation/hooks/relay-xyz-guard.sh`) blocks driving a harness driver before the skill is loaded. For the two live-Claude-windows, same-machine duel recipe (Reporter↔Maintainer with a human go-gate), the copy-paste form is [relay-automation/DUELING-CLAUDES.md](relay-automation/DUELING-CLAUDES.md).
- If the task is about the ATE (Automated Testing Environment) skill — unattended variation-test fuzzing whose implementation lives under `utils/ate/` — start at its canonical interface in `skills/ate/SKILL.md`.
- If the task is about relay session telemetry, the `focus5float` health feed, or extraction scripts under `utils/telemetry/`, start in `PROJECT/1-INBOX/GH-24-RELAY-TELEMETRY-EXTRACTOR.md`.
- If the task is about live per-session completion telemetry — the `XYZ.json` log every relay/marathon/swarm session appends to at the harness repo root (schema: `harness`/`sessionId`/`health`/`title`/`description`/`updatedAt`), the shared writer `utils/telemetry/append-xyz-completion.sh`, or the shared health mapping `utils/telemetry/health-lib.sh` — start in `PROJECT/1-INBOX/GH-75-XYZ-JSON-COMPLETION-TELEMETRY.md`. `XYZ.json` is local + gitignored (machine-specific).
- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
- If the task is about a proposed roadmap-steward agent, start here, then read `PROJECT/PDDA.md` and its `Proposed roadmap steward extension` section.
- If the task is about finding or picking a skill for a job, see `ARCHITECTURE.md` → "Skills Index" for a one-line inventory of every skill in `skills/`.
- Issue-first SOP: any change beyond a 2–3 line fix (and every project plan) opens a GitHub issue *first*, then gets a pointer doc named after the issue at `PROJECT/1-INBOX/GH-<number>-VERY-SHORT-DESC.md` — e.g. `GH-1234-SHOWME-COMMAND.md` — and that capture is parked in the roadmap ledger queue immediately via `releases roadmap add` (format + lifecycle owned by `PROJECT/PDDA.md` → "GitHub issue intake"), following the normal `1-INBOX` → `2-WORKING` flow. Genuinely trivial edits (≤2–3 line fixes, typos, path repoints, doc-only one-liners) are exempt and commit directly.
# Guiding Principles

North star for **XYZ Forge**, the multi-agent coordination harness behind the `tick` event-log kernel and `relay-automation/` relay stack. When a choice is unclear, the option that keeps agents synchronized, contained, and verifiable — without leaking or destroying work — wins. AGENTS.md is the behavioral playbook; ROUTER.md is the entry-point map; this is the *why*.

## The North Star

There is no perfect architecture and no finished codebase. The bar is not perfection — it is that
every change leaves the harness **more durable, more reversible, and less duplicated** than it found
it, and that the three stay in balance:

- **Durable** — it removes the root cause and the next planned change builds on it, rather than being
  torn out when the obvious next feature lands.
- **Reversible** — the cost of being wrong is known and bounded before the change lands. A change
  nobody can undo is a bet, not a fix, and gets treated as one.
- **DRY** — nothing canonical lives in two places where it can drift. One source of truth, and every
  other surface is a pointer or a projection of it.

**Do not build a new layer, module, or sub-system when an existing piece of code can be extended
easily, logically, and safely.** Extending an existing abstraction beats standing up a parallel,
siloed system, even when the parallel path is faster to write today — the parallel path is what
later has to be kept in sync, and what silently drifts when it isn't. If the existing abstraction
genuinely cannot carry the new case, say so in one line, with the reason, before forking.

These three pull against each other, and that tension is the decision, not a problem to average
away: the most durable fix is often the least reversible, and collapsing two near-duplicates is a
DRY win that can widen the blast radius. Name the trade and pick; do not split the difference by
building both.

This section is canonical. `AGENTS.md` owns how it is applied to a given change — the reversibility
scale (§3) and blast-radius sizing (§4) — and principles 6, 7, and 10 below are the build-time and
done-time expressions of it. Where another doc restates this, that doc is the copy and this is the
original.

## Purpose

XYZ Forge is a local-first operations system for humans directing agents across their repositories:
capture → rate → plan → preflight → execute → gate → land → record. Its `tick` kernel coordinates
local claims through an event log and exclusive locks; its relay and Marathon tooling drive bounded
build and review work. Containment controls reduce accidental writes but do not guarantee safety
outside their enforced boundaries; linked worktrees share Git state. The product prioritizes
coordination, recoverability and verifiable outcomes. The operator remains the decision authority.

XYZ is not enterprise application lifecycle management or an agent marketplace. It currently
assumes specified work rather than providing a structured spec/PRD-generation pipeline of its own;
that capability gap is not a permanent prohibition on future product work. PDDA’s governance-layer
anti-scope does not prohibit XYZ’s coordination and execution features.

## The quality bar

Every agent turn is a signal. A turn is high-quality only when it is all four:

- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
- **Relevant** — ranked, not dumped. Volume is not value. One real bug beats five nits and a phantom.
- **Fresh** — current, not stale. A turn that reads a stale `STATE.md` or misses an epoch fence is wrong by construction.
- **Structured** — one shape, clean for the operator to read and for downstream agents to feed on.

Fail a pillar, and the turn, feature, or relay review isn't done.

## How it's built

1. **Coordination is local-transport only.** `.tick/events/` is the shared bus; claims resolve from there, not from a remote. No per-event push/fetch; no remote dependency at runtime. A coordination primitive that reaches out is a coordination primitive that can fail or leak.

2. **One canonical event log for tick coordination.** `.tick/events/` records coordination events; `.tick/STATE.md` is a derived view. Coordination verbs read and fold the events and append changes through the event API. Other subsystems retain their own documented sources of truth, including the RELEASES roadmap ledger. Do not create competing copies of canonical state.

3. **Containment is non-negotiable.** A headless turn must not: self-commit mid-turn, orphan a peer's concurrent commit, or write outside its allowlist. The allowlist, worktree isolation, and commit-bypass guard exist because a driven agent will do all three if unconstrained — not hypothetically, but as documented live incidents (GH-13, GH-14, GH-17). New relay paths must clear the containment bar before they ship.

4. **Skill-first; never improvise the harness.** The `relay-xyz` skill owns the locator, sandbox rules, exit codes, and the safety boundary. A session that improvises those from `ls relay-automation/` silently skips the skill's safety layer. In sessions that install and invoke the `PreToolUse` hook, `relay-automation/hooks/relay-xyz-guard.sh` checks supported driver invocations for the skill’s setup evidence; this is not a guarantee that every runtime invokes that hook. Add capabilities to the skill; do not work around it.

5. **Adversarially proven before commercially viable.** The harness exists to run against real codebases. Features in the adversarial-hardening track (epoch fencing, chaos suite, cross-repo E2E) must be verified to survive deliberate abuse — stale writers, zombie claims, macOS case-sensitivity, concurrent peer commits — not just the happy path. A feature that clears the happy path and skips chaos is half-done.

6. **Build durable, not band-aid.** Durable means it removes the root cause and the next planned change builds on it — not a patch torn out when the obvious next feature lands. A band-aid is wasted work unless a demo strictly needs one, and a demo band-aid is tagged for removal so it isn't silently inherited.

7. **Least code that clears the bar.** The `tick` coordination kernel uses Node's standard library. The repository also ships `package.json` and `package-lock.json` for Acorn-based source analysis. Prefer reusing or extending what exists; the smallest change that stays correct, contained, and durable wins. Net-new code is a cost to justify. Deleting code counts as progress.

8. **Honest; the operator decides.** Surface what failed and why — never mask a stall as success or an escalation as a stall. A headless turn self-repairs within a bounded exit-code menu (`exit 3` stall, `exit 4` escalated-by-design, `exit 6` containment revert), then stops; it never loops forever or silently swallows an error. Destructive actions require explicit authorization.

9. **Docs support resumable work (PDDA).** ROUTER points to the governing contracts; the RELEASES DB owns this repository's roadmap ledger, and ROADMAP-DASHBOARD.md is its generated view. Linked PROJECT documents hold plans, decisions and handoff detail; CHANGELOG records dated outcomes. Resume execution using those documents together with the relevant runtime state and evidence. If current documentation contradicts the implementation, correct it or explicitly record the unresolved discrepancy.

10. **Done means verified.** "Done" is `validate.sh` green, the relevant PDDA checks passing, and any relay review returning `Approved` — not work that looks finished. An unverified success claim is itself a low-quality signal.

11. **Issue-first; every non-trivial change has a signal stream.** Any change beyond a 2–3 line fix opens a GitHub issue first, then gets a `GH-<number>` in-repo pointer doc, then lands. The issue is the machine-queryable signal stream; the `PROJECT/**` doc is the execution surface of record. Genuinely trivial edits (≤2–3 line fixes, typos, path repoints, doc-only one-liners) are exempt.

12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.

13. **A green gate without a witnessed red control is not evidence.** Every new or materially changed decision gate ships a recorded demonstration that it fails for the right reason: a pre-fix replay, deliberate mutation, or controlled bad fixture. Do not mistake a check that validates the artifact it just generated (#351) or a parity check that compares a lane to itself (#348) for evidence; both shapes are structurally unable to falsify their claim.

## Applying this

Adding a feature or weighing a tradeoff, ask: *does this keep agents coordinated without collision, contained within their scope, and verifiable to an outside observer? And is "done" provable by running `validate.sh`?* If any answer is no, reconsider.

---

## Conventions

### Strict-mode policy (bash `set -e`)

Python is the default implementation for the twelve frozen Tier-A entry points. Existing Bash
bodies are compatibility fallbacks selected with `XYZ_PYTHON=0`; their strict-mode choices remain
subsystem-specific. Consult each existing script’s header and error handling before changing it.
New executables under `utils/` or `relay-automation/` follow AGENTS.md’s Python and exception rules.
This section does not authorize edits to frozen Bash twins.

### Tool install paths — never inside another app's folder (GH-347)

**This harness's tool binaries never live inside another application's private directory.** Not the
worker CLIs (`codex`, `agy`, `pi`, `aider`), not `tick`, not anything the harness shells out to.

The failure mode is specific and quiet: a foreign app owns its own directory, so its next update or
reinstall deletes our dependency with it — on that app's schedule, with no signal we control. Worse, the
readiness check cannot tell the two apart. `find-harness.sh --check` tests only whether a worker is *on
PATH*, so "the neighbouring app just wiped our tool" and "never installed" produce the byte-identical
line. That is the same disease as GH-315/GH-319: a broken observation layer where failure is invisible
and every available signal agrees.

**The `npm install -g` trap — this is how GH-347 actually happened.** npm derives its global prefix from
whichever `npm` is on PATH, so a bare `npm install -g <pkg>` inherits a foreign app's runtime silently
and exits 0. On the machine that filed GH-347, another agent app had symlinked its bundled Node onto PATH
(`~/.local/bin/npm -> ~/.hermes/node/bin/npm`) with no `~/.npmrc` involved at all, so `pi` installed into
that app's folder and — because only `node`/`npm` were symlinked out, not `pi` — was invisible to every
shell while being perfectly functional. **Run `npm config get prefix` before any global install and
confirm it is a path this repo's tooling owns.** Never assume.

The positive pattern is already on disk in the two lanes that have never had this problem: a tool's own
app directory with a symlink onto PATH (`~/.local/bin/codex -> ~/.codex/packages/…/bin/codex`), or a real
binary in a shared user-local `bin`. Either is fine. Someone else's runtime is not.

**Scope note:** where a *working* binary lives stays the operator's call. This is a convention and a
warning, deliberately **not** a gate — a false positive that blocks a relay is worse than the papercut it
prevents.

### Marathon builder default & plan location (GH-212)

Two vendored-harness defaults, made explicit so an agent given only the vendored bundle picks the
right behavior without pattern-matching a downstream repo's prior drift:

- **Builder default is `codex`.** Marathon’s current implementation defaults to Codex; agy is
  another supported builder. Choosing Claude remains an explicit, cost-acknowledged operator
  decision under AGENTS.md. Actual billing depends on the selected tool’s authentication and
  account configuration; a default executable name does not establish a billing guarantee. The
  Python implementation is the default, with the existing Bash fallback available through
  `XYZ_PYTHON=0`.
- **A marathon's plan lives under `PROJECT/2-WORKING/`.** The `MARATHON.yaml` + its phase briefs
  belong under `PROJECT/2-WORKING/<capture-doc>/` — never a standalone top-level folder (e.g.
  `marathon-plans/<slug>/`). `marathon.sh --plan` enforces this: it refuses (exit 2) a plan that
  resolves outside `PROJECT/2-WORKING/`, exempting only paths under the harness's own home
  (`MARATHON_HOME` — shipped reference examples like `MARATHON.example.yaml`) or an explicit
  `MARATHON_ALLOW_PLAN_OUTSIDE_WORKING=1` override for a genuinely non-default location.

---

## Appendix: AI Doc Review Heuristics

When reviewing any repo doc (roadmap entries, plans, architecture notes, audits, task writeups), apply these. Priority: containment > coordination correctness > signal quality > implementation speed and operator friction.

**Heuristics**

1. **Containment preserved?** Any headless path that could self-commit, touch off-allowlist files, or orphan a peer commit without an explicit containment argument → reject or escalate.
2. **Skill-first respected?** Any plan that bypasses `relay-xyz` or improvises the harness from scratch without the skill layer → reject. Add to the skill instead.
3. **Coordination through the event log?** Tick coordination state uses `tick` verbs; other subsystems use their documented canonical writers. Competing state copies need explicit justification.
4. **Done verifiable?** Names runnable gates (`validate.sh`, specific tests, `utils/pdda/pdda.sh run`). None = low-quality signal.
5. **Drift reduced, not created?** No duplicated docs, no execution detail in the roadmap ledger or its generated dashboard, no reinventing a path the event-log contract already documents.
6. **Next action singular?** One explicit next step, not buried in prose; status cells non-empty.
7. **Operator control explicit?** No silent retry, no auto-repair outside the bounded exit-code menu, no masked failure; destructive ops surface before executing.
8. **Four pillars pass?** Each turn/output is Attested, Relevant, Fresh, Structured. Fail one → not done.

**Tie-breakers**

- **Containment vs speed:** choose containment; flag friction as a design question, not a shortcut.
- **New relay path vs reuse:** extend the existing skill and harness over forking a parallel path; if the harness can't accommodate it, surface the gap.
- **Ambitious vs resumable:** a shorter plan an agent can resume cold beats a comprehensive one that buries state in prose.

**Reject or escalate when**

- A headless path has no allowlist, no worktree isolation, and no commit-bypass guard — and the doc doesn't justify why.
- "Done" has no runnable verification step.
- Adding a new relay lane requires editing the event-log kernel or the `tick` verb schema without a decision record under `decisions/`.
- Hardcoded absolute paths, silent destructive operations, or opaque epoch-fence assumptions.
- The roadmap ledger would need execution detail to make the plan legible.

codex
> **Mantra:**
> 1. **First is reproducibility.** Can the issue — or the artifact — be reproduced or observed reliably?
> 2. **Know the fail path.** Debugger first; then source trace + knob enumeration; then in-code instrumentation.
> 3. **Question your hypothesis.** What would disprove it?
> 4. **Every run is a breadcrumb.** Cross-reference all of them.

The consequential bet is whether the new ownership and gating logic fails safely under races and partial inputs. Reversibility is Easy (policy/script changes can be reverted), but the operational blast radius includes post-merge reconciliation, generated roadmap views, closeout eligibility, and marathon planning.
mcp: codebase-memory-mcp/list_projects started
mcp: codebase-memory-mcp/list_projects (completed)
mcp: codebase-memory-mcp/list_projects started
mcp: codebase-memory-mcp/list_projects (completed)
exec
/bin/zsh -lc 'git status --short --branch && git log --oneline --decorate -8 && git diff --stat development...HEAD && git diff --name-status development...HEAD' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 11715ms:
2026-09-10 10:09:54.525 xcodebuild[51875:94770308]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:09:55.059 xcodebuild[51875:94770245] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-4JRXxxVW' (errno=Operation not permitted)
2026-09-10 10:09:55.904 xcodebuild[52634:94771610]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:09:56.133 xcodebuild[52634:94771587] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
## HEAD (no branch)
?? relay-system/2026-09-10/gh496-pr2-final-qa-100915/
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-E0S0TCOk' (errno=Operation not permitted)
2026-09-10 10:09:57.970 xcodebuild[53267:94772797]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:09:58.194 xcodebuild[53267:94772767] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-IXk17ucK' (errno=Operation not permitted)
2026-09-10 10:09:58.871 xcodebuild[53512:94773222]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:09:59.110 xcodebuild[53512:94773188] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8c05cd28 (HEAD, feat/gh496-phase2-views) fix(gh-496): support short commit SHA prefix matching in pre-merge receipt validation
ef19c5b4 test(gh-496): commit Phase 2 test qualification receipt and summary
75c9890f fix(gh-496): snapshot planner fingerprint in rollback journal and exclude generated plans from hash
aeeb98c9 fix(gh-496): harden in-flight checks, staleness guard compatibility, and jog dashboard refresh
fd90f51c feat(gh-496): view decoupling, single reconciler owner, and pre-merge closeout checks
dd44b739 docs(gh-496): add Phase 2 execution checklist and acceptance criteria
141f2ced (origin/feat/gh496-selective-ci) test(telemetry): record verified full-gate qualification receipts post-Codex review (GH-496 PR 1)
fa98ab0f feat(telemetry): address independent consult QA and harden out-of-tree store (GH-496 PR 1)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-HWFS2nU5' (errno=Operation not permitted)
2026-09-10 10:10:00.588 xcodebuild[54013:94774125]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:00.817 xcodebuild[54013:94774098] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-fQFKoEeO' (errno=Operation not permitted)
2026-09-10 10:10:01.493 xcodebuild[54297:94774753]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:01.716 xcodebuild[54297:94774710] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
 AGENTS.md                                          |    8 +-
 CHANGELOG.md                                       |    2 +
 LEADERBOARD.md                                     |    1 +
 PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md           |  138 +-
 .../recon-gh496-merge-churn-and-telemetry.md       |  151 +
 ROADMAP-DASHBOARD.md                               |    5 +-
 SOP.md                                             |   10 +-
 TESTS-RESULTS/2026-09-09+GH-496-PR1/SUMMARY.md     |   26 +
 .../2026-09-09+GH-496-PR1/focused-gh496.log        |   16 +
 .../2026-09-09+GH-496-PR1/full-gate.log.gz         |  Bin 0 -> 6848 bytes
 .../2026-09-09+GH-496-PR1/provenance.jsonl         |    7 +
 TESTS-RESULTS/2026-09-10+GH-496-PR2/SUMMARY.md     |   30 +
 .../2026-09-10+GH-496-PR2/provenance.jsonl         |    7 +
 githooks/dashboard-staleness-guard.sh              |  160 +-
 .../gh496-pr1-qa-211502/gh496-pr1-qa.PROMPT.txt    |    1 +
 .../gh496-pr1-qa.codex.NO-CITATION.txt             |    1 +
 .../gh496-pr1-qa.codex.PROVENANCE.txt              |    2 +
 .../gh496-pr1-qa-211502/gh496-pr1-qa.codex.md      | 2133 ++++++++++
 .../gh496-pr2-plan-qa.PROMPT.txt                   |   26 +
 .../gh496-pr2-plan-qa.codex.NO-CITATION.txt        |    1 +
 .../gh496-pr2-plan-qa.codex.PROVENANCE.txt         |    2 +
 .../gh496-pr2-plan-qa.codex.md                     | 4147 ++++++++++++++++++++
 skills/merge-cleanup/SKILL.md                      |    7 +-
 test/ci-route.sh                                   |    4 +-
 test/gh103-timeline-exporter.sh                    |    3 +-
 test/gh243-dashboard-staleness-guard.sh            |   31 +-
 test/gh257-roadmap-ledger-fixes.sh                 |    4 +-
 test/gh280-jog-marathon-adapter.sh                 |    4 +-
 test/gh496-phase2-reconciliation-views.sh          |  431 ++
 test/gh496-telemetry-isolation.sh                  |  282 ++
 test/roadmap-dashboard.sh                          |    7 +-
 test/wave-reconcile.sh                             |   12 +-
 utils/ci-route.sh                                  |    6 +-
 utils/leaderboard.sh                               |    3 +
 utils/py/harness_app.py                            |  169 +-
 utils/py/jog_run.py                                |   16 +-
 utils/py/releases_app.py                           |   18 +-
 utils/py/wave_reconcile.py                         |  489 ++-
 utils/roadmap-dashboard.sh                         |   14 +-
 validate.sh                                        |    2 +
 40 files changed, 8208 insertions(+), 168 deletions(-)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-koDsezBw' (errno=Operation not permitted)
2026-09-10 10:10:03.253 xcodebuild[54738:94775493]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:03.489 xcodebuild[54738:94775457] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Jph9Lxuy' (errno=Operation not permitted)
2026-09-10 10:10:04.169 xcodebuild[55014:94776094]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:04.408 xcodebuild[55014:94776040] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
M	AGENTS.md
M	CHANGELOG.md
M	LEADERBOARD.md
M	PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md
A	PROJECT/2-WORKING/recon-gh496-merge-churn-and-telemetry.md
M	ROADMAP-DASHBOARD.md
M	SOP.md
A	TESTS-RESULTS/2026-09-09+GH-496-PR1/SUMMARY.md
A	TESTS-RESULTS/2026-09-09+GH-496-PR1/focused-gh496.log
A	TESTS-RESULTS/2026-09-09+GH-496-PR1/full-gate.log.gz
A	TESTS-RESULTS/2026-09-09+GH-496-PR1/provenance.jsonl
A	TESTS-RESULTS/2026-09-10+GH-496-PR2/SUMMARY.md
A	TESTS-RESULTS/2026-09-10+GH-496-PR2/provenance.jsonl
M	githooks/dashboard-staleness-guard.sh
A	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.PROMPT.txt
A	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.NO-CITATION.txt
A	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.PROVENANCE.txt
A	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.md
A	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt
A	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.NO-CITATION.txt
A	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.PROVENANCE.txt
A	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.md
M	skills/merge-cleanup/SKILL.md
M	test/ci-route.sh
M	test/gh103-timeline-exporter.sh
M	test/gh243-dashboard-staleness-guard.sh
M	test/gh257-roadmap-ledger-fixes.sh
M	test/gh280-jog-marathon-adapter.sh
A	test/gh496-phase2-reconciliation-views.sh
A	test/gh496-telemetry-isolation.sh
M	test/roadmap-dashboard.sh
M	test/wave-reconcile.sh
M	utils/ci-route.sh
M	utils/leaderboard.sh
M	utils/py/harness_app.py
M	utils/py/jog_run.py
M	utils/py/releases_app.py
M	utils/py/wave_reconcile.py
M	utils/roadmap-dashboard.sh
M	validate.sh

exec
/bin/zsh -lc 'git merge-base development HEAD; git rev-parse development HEAD; git diff --unified=40 development...HEAD -- .github/workflows/wave-reconcile.yml utils/py/wave_reconcile.py utils/py/harness_app.py utils/py/jog_run.py utils/py/releases_app.py utils/roadmap-dashboard.sh githooks/dashboard-staleness-guard.sh test/gh496-phase2-reconciliation-views.sh' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 7895ms:
2026-09-10 10:10:13.022 xcodebuild[58954:94782641]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:13.274 xcodebuild[58954:94782609] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-mL9KBOpi' (errno=Operation not permitted)
2026-09-10 10:10:13.943 xcodebuild[59248:94783165]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:14.180 xcodebuild[59248:94783144] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
abe0f17a33613dc86f6c0c9c7776aefc8aa2d207
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-0nHNkLpY' (errno=Operation not permitted)
2026-09-10 10:10:15.673 xcodebuild[59839:94784155]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:15.901 xcodebuild[59839:94784091] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YgY7pFn2' (errno=Operation not permitted)
2026-09-10 10:10:16.598 xcodebuild[60149:94784659]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:16.832 xcodebuild[60149:94784624] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
abe0f17a33613dc86f6c0c9c7776aefc8aa2d207
8c05cd2884c42ec5a39981ad0d082088e1538fae
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-TNpQqXmO' (errno=Operation not permitted)
2026-09-10 10:10:18.372 xcodebuild[60727:94785686]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:18.610 xcodebuild[60727:94785646] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-MQVzeIay' (errno=Operation not permitted)
2026-09-10 10:10:19.287 xcodebuild[60999:94786124]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:10:19.519 xcodebuild[60999:94786085] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/githooks/dashboard-staleness-guard.sh b/githooks/dashboard-staleness-guard.sh
index 3f481b3a..5f366e56 100755
--- a/githooks/dashboard-staleness-guard.sh
+++ b/githooks/dashboard-staleness-guard.sh
@@ -66,129 +66,189 @@ cleanup_guard() {
   if [ -z "$GUARD_DEV" ] || [ -z "$GUARD_INODE" ] || [ -z "$cur_dev" ] || [ -z "$cur_inode" ] || \
      [ "$cur_dev" != "$GUARD_DEV" ] || [ "$cur_inode" != "$GUARD_INODE" ]; then
     echo "dashboard-staleness-guard: refusing cleanup — guard root identity mismatch ($cur_dev:$cur_inode != $GUARD_DEV:$GUARD_INODE)" >&2
     exit 1
   fi
   case "$cur_phys" in
     "$SYS_TMP"/*) rm -rf "$cur_phys" || exit 1 ;;
     *) echo "dashboard-staleness-guard: refusing cleanup of non-descendant $cur_phys" >&2; exit 1 ;;
   esac
   return "$exit_code"
 }
 trap cleanup_guard EXIT INT TERM
 
 GUARD_ROOT="$(mktemp -d "$SYS_TMP/staleness-guard.XXXXXX")"
 [ -n "$GUARD_ROOT" ] || { echo "dashboard-staleness-guard: mktemp failed" >&2; exit 1; }
 
 GUARD_ROOT_PHYS="$(cd -P "$GUARD_ROOT" 2>/dev/null && pwd -P)" || GUARD_ROOT_PHYS=""
 [ -n "$GUARD_ROOT_PHYS" ] && [ -d "$GUARD_ROOT_PHYS" ] || { echo "dashboard-staleness-guard: failed to resolve guard root" >&2; exit 1; }
 case "$GUARD_ROOT_PHYS" in
   "$SYS_TMP"/*) ;;
   *) echo "dashboard-staleness-guard: guard root $GUARD_ROOT_PHYS is not a resolved descendant of $SYS_TMP" >&2; exit 1 ;;
 esac
 
 init_dev_inode="$(get_dev_inode "$GUARD_ROOT_PHYS")"
 GUARD_DEV="${init_dev_inode%% *}"
 GUARD_INODE="${init_dev_inode##* }"
 if [ -z "$GUARD_DEV" ] || [ -z "$GUARD_INODE" ]; then
   echo "dashboard-staleness-guard: failed to establish guard root device/inode identity" >&2
   exit 1
 fi
 
 while [ "$#" -ge 2 ]; do
   local_sha="$1"; remote_sha="$2"; shift 2
   case "$remote_sha" in
     ''|0000000000000000000000000000000000000000) continue ;;   # new branch: no range to inspect
   esac
   git -C "$REPO" cat-file -e "${remote_sha}^{commit}" 2>/dev/null || continue
 
   touched_ledger=0
   touched_dashboard=0
+  touched_leaderboard=0
+  touched_dashboard_renderer=0
+  touched_leaderboard_renderer=0
+
   while IFS= read -r path; do
     case "$path" in
       releases.sql|releases.db) touched_ledger=1 ;;
       ROADMAP-DASHBOARD.md)     touched_dashboard=1 ;;
+      LEADERBOARD.md)           touched_leaderboard=1 ;;
+      utils/roadmap-dashboard.sh|utils/py/releases_app.py) touched_dashboard_renderer=1 ;;
+      utils/leaderboard.sh|utils/timeline/export_timeline.py) touched_leaderboard_renderer=1 ;;
     esac
   done < <(git -C "$REPO" diff --no-renames --name-only "$remote_sha" "$local_sha" 2>/dev/null)
 
-  if [ "$touched_ledger" -eq 1 ] && [ "$touched_dashboard" -eq 0 ]; then
-    # GH-257 Task 4: check whether regenerating ROADMAP-DASHBOARD.md produces drift or no diff.
-    # Run the diagnosis against a commit-pinned temporary projection of local_sha inside the
-    # private GUARD_ROOT_PHYS so uncommitted working-tree modifications do not skew the classification.
+  # Check 1: View Decoupling (GH-496 Phase 2)
+  # Task branches must NOT commit routine ROADMAP-DASHBOARD.md or LEADERBOARD.md.
+  # Views are owned and staged by the reconciliation workflow on development upon landing.
+  # View commits are permitted only if the causal renderer dependency was modified in the range,
+  # or in GITHUB_ACTIONS (where the reconciler bot commits views).
+  if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
+    if [ "$touched_dashboard" -eq 1 ] && [ "$touched_dashboard_renderer" -eq 0 ]; then
+      cat >&2 <<'EOF'
+dashboard-staleness-guard: REFUSING the push — this range modifies ROADMAP-DASHBOARD.md
+without modifying its renderer (utils/roadmap-dashboard.sh or utils/py/releases_app.py).
+
+Under GH-496 Phase 2, generated views are owned and staged by the reconciliation workflow
+on development. Task branches must not commit routine view updates, to prevent merge collisions.
+
+Fix (drop the view commit while keeping your ledger changes):
+    git rm --cached ROADMAP-DASHBOARD.md && git commit --amend
+
+Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
+EOF
+      exit 1
+    fi
+
+    if [ "$touched_leaderboard" -eq 1 ] && [ "$touched_leaderboard_renderer" -eq 0 ]; then
+      cat >&2 <<'EOF'
+dashboard-staleness-guard: REFUSING the push — this range modifies LEADERBOARD.md
+without modifying its renderer (utils/leaderboard.sh or utils/timeline/export_timeline.py).
+
+Under GH-496 Phase 2, generated views are owned and staged by the reconciliation workflow
+on development. Task branches must not commit routine view updates, to prevent merge collisions.
+
+Fix (drop the view commit while keeping your other changes):
+    git rm --cached LEADERBOARD.md && git commit --amend
+
+Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
+EOF
+      exit 1
+    fi
+  fi
+
+  # Check 2: Renderer sync validation when renderer dependencies are modified
+  if [ "$touched_dashboard" -eq 1 ] && [ "$touched_dashboard_renderer" -eq 1 ]; then
+    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
+    mkdir -p "$TMP_PROJ"
+    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
+       && [ -f "$TMP_PROJ/utils/roadmap-dashboard.sh" ]; then
+      if ! bash "$TMP_PROJ/utils/roadmap-dashboard.sh" --check 2>&1 >/dev/null; then
+        cat >&2 <<'EOF'
+dashboard-staleness-guard: REFUSING the push — renderer changes were committed but
+ROADMAP-DASHBOARD.md is not in sync with the updated renderer output.
+
+Regenerate and commit:
+    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit --amend
+EOF
+        exit 1
+      fi
+    fi
+  fi
+
+  if [ "$touched_leaderboard" -eq 1 ] && [ "$touched_leaderboard_renderer" -eq 1 ]; then
+    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
+    mkdir -p "$TMP_PROJ"
+    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
+       && [ -f "$TMP_PROJ/utils/leaderboard.sh" ]; then
+      if ! bash "$TMP_PROJ/utils/leaderboard.sh" --check 2>&1 >/dev/null; then
+        cat >&2 <<'EOF'
+dashboard-staleness-guard: REFUSING the push — renderer changes were committed but
+LEADERBOARD.md is not in sync with the updated renderer output.
+
+Regenerate and commit:
+    bash utils/leaderboard.sh && git add LEADERBOARD.md && git commit --amend
+EOF
+        exit 1
+      fi
+    fi
+  fi
+
+  # Check 3: Semantic ledger validation (GH-496 Phase 2 + GH-474)
+  # When the ledger is modified, ensure the ledger renders cleanly and drops no rows.
+  if [ "$touched_ledger" -eq 1 ]; then
     TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
     mkdir -p "$TMP_PROJ"
 
-    drift_detected=1
     render_err=""
+    render_rc=0
     if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
        && [ -f "$TMP_PROJ/utils/roadmap-dashboard.sh" ]; then
-      # GH-474: KEEP the renderer's stderr. `--check` runs the full render before it reaches its
-      # mode branch (utils/roadmap-dashboard.sh — node render, then `if [[ "$MODE" == "check" ]]`),
-      # so the dropped-row warning it already emits is available here. Discarding it is what
-      # forced the no-drift arm below to infer the same fact from table names.
-      # `2>&1 >/dev/null` keeps stderr and drops stdout (order matters); the assignment carries
-      # the renderer's own exit status, so the drift verdict is unchanged.
-      if render_err="$(bash "$TMP_PROJ/utils/roadmap-dashboard.sh" --check 2>&1 >/dev/null)"; then
-        drift_detected=0
-      else
-        drift_detected=1
-      fi
+      render_err="$(ROADMAP_DASHBOARD_OUTPUT="$TMP_PROJ/ROADMAP-DASHBOARD.md" bash "$TMP_PROJ/utils/roadmap-dashboard.sh" 2>&1 >/dev/null)" || render_rc=$?
+    else
+      render_rc=1
+      render_err="renderer missing or archive failed"
     fi
 
-    if [ "$drift_detected" -eq 1 ]; then
-      cat >&2 <<'EOF'
+    if [ "$render_rc" -ne 0 ]; then
+      cat >&2 <<EOF
 dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
-(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, so the human-readable
-view would ship stale against the data under it (GH-243 / GH-169 item 3).
+(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, but the ledger cannot be rendered into a valid dashboard (GH-496).
 
-Fix (one command, then commit the result into the same push):
-    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit -m "docs: regenerate roadmap dashboard"
+The renderer reported:
+$render_err
 
 Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
 EOF
-    else
-      # No drift: the committed dashboard matches a fresh render. Exactly one hazard survives
-      # that — a roadmap row the renderer DROPPED. A dropped row renders to nothing, so the
-      # artifact still matches byte-for-byte while the ledger row is invisible in the view.
-      #
-      # GH-474: ASK the renderer instead of guessing. It already names every dropped row on
-      # stderr ("roadmap-dashboard: warning: dropped N unparseable row(s): <ids>", emitted from
-      # the droppedRows array), and $render_err above holds it. This replaces the GH-243/GH-315
-      # table-name allowlist, which had to infer the same fact from the dump's fan-out per write
-      # shape (jog, then marathon) and went short twice — 8 dump tables were still unclassified
-      # and still produced the FALSE refusal this arm exists to prevent.
-      #
-      # Direction of failure, deliberately: this reads the renderer's own report, so it cannot
-      # go short as a table list does. If the renderer is silent, the row rendered — allow.
-      dropped_line=""
-      while IFS= read -r eline; do
-        case "$eline" in
-          *"roadmap-dashboard: warning: dropped "*) dropped_line="$eline"; break ;;
-        esac
-      done <<EOF_ERR
+      exit 1
+    fi
+
+    # GH-474: Check for dropped rows reported by the renderer
+    dropped_line=""
+    while IFS= read -r eline; do
+      case "$eline" in
+        *"roadmap-dashboard: warning: dropped "*) dropped_line="$eline"; break ;;
+      esac
+    done <<EOF_ERR
 $render_err
 EOF_ERR
-      if [ -z "$dropped_line" ]; then
-        continue
-      fi
+    if [ -n "$dropped_line" ]; then
       cat >&2 <<EOF
 dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
 (releases.sql / releases.db) without modifying ROADMAP-DASHBOARD.md, but regenerating the
 dashboard produces NO diff (GH-243 / GH-257).
 
-The renderer dropped a roadmap row, so it contributes nothing to the view and the artifact
-still matches. It reported:
+The renderer dropped a roadmap row, so it contributes nothing to the view.
+It reported:
     $dropped_line
 
 Correct the named row with:
     releases roadmap update --issue-num <N> --raw-text "- **GH-<N> · <title>** ..."
-then regenerate and commit:
-    bash utils/roadmap-dashboard.sh && git add releases.db releases.sql ROADMAP-DASHBOARD.md && git commit -m "docs: fix roadmap row and regenerate dashboard"
 
 Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
 EOF
+      exit 1
     fi
-    exit 1
   fi
 done
 
 exit 0
diff --git a/test/gh496-phase2-reconciliation-views.sh b/test/gh496-phase2-reconciliation-views.sh
new file mode 100755
index 00000000..128e5fe7
--- /dev/null
+++ b/test/gh496-phase2-reconciliation-views.sh
@@ -0,0 +1,431 @@
+#!/usr/bin/env bash
+# test/gh496-phase2-reconciliation-views.sh — hermetic verification of GH-496 PR 2:
+# 1. Hosted reconciler in-flight collision detection & emergency override controls
+# 2. Deterministic pre-merge closeout checks (--pre-merge: frontmatter, lessons learned, receipts)
+# 3. Marathon planner input fingerprinting to skip redundant replanning
+set -euo pipefail
+
+source test/_setup.sh "gh496-phase2" || { echo "setup failed"; exit 1; }
+
+ROOT="$(cd "$HERE/.." && pwd)"
+RECONCILE_PY="$ROOT/utils/py/wave_reconcile.py"
+
+assert_eq() {
+  local desc="$1"
+  local got="$2"
+  local exp="$3"
+  if [ "$got" = "$exp" ]; then
+    pass "$desc"
+  else
+    fail "$desc: expected '$exp', got '$got' (output: ${out:-none})"
+  fi
+}
+
+echo "=== Running gh496-phase2-reconciliation-views.sh test suite ==="
+
+# Setup mock PATH with custom gh binary
+MOCK_BIN="$WORK/mock_bin"
+mkdir -p "$MOCK_BIN"
+MOCK_GH="$MOCK_BIN/gh"
+MOCK_GH_STATE="$WORK/mock_gh_state.txt"
+echo "clean" > "$MOCK_GH_STATE"
+
+cat << EOF > "$MOCK_GH"
+#!/usr/bin/env bash
+if [ "\$1" = "pr" ] && [ "\$2" = "view" ]; then
+  pr_num="\$3"
+  echo '{"number": 999, "title": "Test PR", "body": "closes #999", "state": "MERGED", "baseRefName": "development", "headRefOid": "0123456789abcdef0123456789abcdef01234567", "mergedAt": "2026-09-10T10:00:00Z", "mergeCommit": {"oid": "0123456789abcdef0123456789abcdef01234567"}}'
+  exit 0
+fi
+
+if [ "\$1" = "issue" ] && [ "\$2" = "view" ]; then
+  echo '{"state": "CLOSED"}'
+  exit 0
+fi
+
+STATE="\$(cat "$MOCK_GH_STATE" 2>/dev/null || echo "clean")"
+if [ "\$STATE" = "in_progress" ]; then
+  echo '[{"databaseId": 998877, "status": "in_progress", "conclusion": null, "createdAt": "2026-09-10T10:00:00Z", "headSha": "abcdef1234", "event": "push"}]'
+  exit 0
+elif [ "\$STATE" = "error" ]; then
+  echo "gh: network timeout connecting to api.github.com" >&2
+  exit 1
+elif [ "\$STATE" = "malformed" ]; then
+  echo "not valid json"
+  exit 0
+else
+  # clean / completed
+  echo '[{"databaseId": 998870, "status": "completed", "conclusion": "success", "createdAt": "2026-09-10T09:00:00Z", "headSha": "1234567890", "event": "push"}]'
+  exit 0
+fi
+EOF
+chmod +x "$MOCK_GH"
+
+export PATH="$MOCK_BIN:$PATH"
+
+# Setup hermetic fixture repo
+REPO="$WORK/fixture-repo"
+mkdir -p "$REPO"
+git -C "$REPO" init -q -b development
+git -C "$REPO" config user.name "Test Agent"
+git -C "$REPO" config user.email "test@example.com"
+git -C "$REPO" remote add origin "https://github.com/HiQS-Labs/XYZ-forge.git"
+
+mkdir -p "$REPO/PROJECT/2-WORKING" "$REPO/PROJECT/3-COMPLETED" "$REPO/PROJECT/4-MISC" \
+         "$REPO/utils/py" "$REPO/utils/pdda" "$REPO/utils/timeline" \
+         "$REPO/TESTS-RESULTS/2026-09-10+GH-999" "$REPO/.github/workflows"
+touch "$REPO/.github/workflows/wave-reconcile.yml"
+
+cp "$RECONCILE_PY" "$ROOT/utils/py/harness_paths.py" "$REPO/utils/py/"
+
+# Minimal releases.db & releases.sql
+cat << 'PY_EOF' > "$REPO/init_db.py"
+import sqlite3, os
+db_path = os.path.join(os.path.dirname(__file__), "releases.db")
+conn = sqlite3.connect(db_path)
+c = conn.cursor()
+c.execute("""
+CREATE TABLE IF NOT EXISTS roadmap_items (
+    id INTEGER PRIMARY KEY,
+    global_id TEXT NOT NULL UNIQUE,
+    repo_id INTEGER,
+    gh_number INTEGER,
+    title TEXT NOT NULL,
+    section TEXT NOT NULL,
+    position INTEGER NOT NULL,
+    status_marker TEXT,
+    complexity INTEGER,
+    risk INTEGER,
+    effort INTEGER,
+    doc_path TEXT,
+    issue_url TEXT,
+    raw_text TEXT NOT NULL,
+    first_seen TEXT,
+    updated_at TEXT
+)
+""")
+c.execute("CREATE TABLE IF NOT EXISTS releases (id INTEGER PRIMARY KEY, global_id TEXT)")
+c.execute("CREATE TABLE IF NOT EXISTS issue_refs (id INTEGER PRIMARY KEY, url TEXT)")
+c.execute("CREATE TABLE IF NOT EXISTS manifest_items (release_id INTEGER, issue_ref_id INTEGER, state TEXT)")
+c.execute("""INSERT OR REPLACE INTO roadmap_items 
+    (global_id, repo_id, gh_number, title, section, position, status_marker, complexity, risk, effort, doc_path, issue_url, raw_text, first_seen, updated_at)
+    VALUES ('rmi-0123456789ABCDEF0123456789', 1, 999, 'Test Item', 'Now', 1, '🚧', 1, 1, 1, 'PROJECT/2-WORKING/GH-999-TEST.md', 'https://github.com/HiQS-Labs/XYZ-forge/issues/999', '- **GH-999 · Test Item** 🚧 **active 2026-09-10** — test item description. -> [GH-999-TEST.md](PROJECT/2-WORKING/GH-999-TEST.md)', '2026-09-10', '2026-09-10')
+""")
+conn.commit()
+conn.close()
+PY_EOF
+python3 "$REPO/init_db.py"
+touch "$REPO/releases.sql"
+
+# Minimal mocks for downstream tools
+cat << 'APP_EOF' > "$REPO/utils/py/releases_app.py"
+#!/usr/bin/env python3
+import sys
+if len(sys.argv) > 1 and sys.argv[1] == "settings" and sys.argv[2] == "get":
+    print("42")
+    sys.exit(0)
+print("MOCK: releases_app OK")
+sys.exit(0)
+APP_EOF
+chmod +x "$REPO/utils/py/releases_app.py"
+
+cat << 'DASH_EOF' > "$REPO/utils/roadmap-dashboard.sh"
+#!/usr/bin/env bash
+echo "MOCK: roadmap-dashboard OK"
+exit 0
+DASH_EOF
+chmod +x "$REPO/utils/roadmap-dashboard.sh"
+
+PLANNER_CALLS="$REPO/planner_calls.log"
+cat << PLAN_EOF > "$REPO/utils/marathon-plan.sh"
+#!/usr/bin/env bash
+echo "called" >> "$PLANNER_CALLS"
+echo "MOCK: marathon-plan OK"
+exit 0
+PLAN_EOF
+chmod +x "$REPO/utils/marathon-plan.sh"
+
+cat << 'LB_EOF' > "$REPO/utils/leaderboard.sh"
+#!/usr/bin/env bash
+echo "MOCK: leaderboard OK"
+exit 0
+LB_EOF
+chmod +x "$REPO/utils/leaderboard.sh"
+
+cat << 'TL_EOF' > "$REPO/utils/timeline/export_timeline.py"
+#!/usr/bin/env python3
+import sys
+sys.exit(0)
+TL_EOF
+chmod +x "$REPO/utils/timeline/export_timeline.py"
+
+cat << 'PDDA_EOF' > "$REPO/utils/pdda/pdda.sh"
+#!/usr/bin/env bash
+exit 0
+PDDA_EOF
+chmod +x "$REPO/utils/pdda/pdda.sh"
+
+cat << 'ROAD_EOF' > "$REPO/ROADMAP.md"
+# Roadmap
+### Active
+* [ ] #999 Test Item
+### Completed
+ROAD_EOF
+
+cat << 'MAN_EOF' > "$REPO/manifest.json"
+{
+  "issues": [999],
+  "prs": [999]
+}
+MAN_EOF
+
+# Initial valid active doc
+cat << 'DOC_EOF' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+---
+title: Test Task
+status: Review
+created: 2026-09-10
+updated: 2026-09-10
+owner: test-agent
+goal: Verify pre-merge checks
+---
+# GH-999: Test Task
+
+## Summary
+Testing pre-merge checks.
+
+## Lessons Learned
+
+### 1. Closeout Verification
+We verified that closeout gates require substantive reflections and valid frontmatter.
+DOC_EOF
+
+# Commit initial state
+git -C "$REPO" add -A
+git -C "$REPO" commit -q -m "feat: initial commit for #999"
+HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
+
+# Write committed passing test receipt matching HEAD_SHA
+cat << RECEIPT_EOF > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+{"commit": "$HEAD_SHA", "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
+RECEIPT_EOF
+git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+git -C "$REPO" commit -q -m "test: commit passing test receipt"
+HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
+
+# Update the receipt with the latest HEAD_SHA so it matches HEAD
+cat << RECEIPT_EOF2 > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+{"commit": "$HEAD_SHA", "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
+RECEIPT_EOF2
+git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+git -C "$REPO" commit -q --amend -m "test: commit passing test receipt matching HEAD"
+HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
+
+# -------------------------------------------------------------
+# Part 1: Hosted Reconciler In-Flight Collision Detection
+# -------------------------------------------------------------
+echo "in_progress" > "$MOCK_GH_STATE"
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "In-flight hosted reconciler fails closed (exit 8)" "$rc" "8"
+if grep -q "Hosted reconciliation workflow (wave-reconcile.yml) is currently in-flight" <<< "$out"; then
+  pass "Error message identifies in-flight wave-reconcile run"
+else
+  fail "Error message did not identify in-flight run: $out"
+fi
+
+# Override with --force-local-reconcile
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --force-local-reconcile --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "In-flight check bypassed with --force-local-reconcile (exit 0)" "$rc" "0"
+if grep -q "Overriding active hosted reconciliation run" <<< "$out"; then
+  pass "Warning logged when overriding in-flight run"
+else
+  fail "Warning missing on --force-local-reconcile override: $out"
+fi
+git -C "$REPO" checkout -q -f development
+git -C "$REPO" clean -q -fd
+
+# In GITHUB_ACTIONS, --force-local-reconcile is strictly prohibited (exit 2)
+rc=0; out="$(GITHUB_ACTIONS=true python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --force-local-reconcile --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "--force-local-reconcile rejected inside GITHUB_ACTIONS (exit 2)" "$rc" "2"
+if grep -q -F -- "--force-local-reconcile is prohibited inside GITHUB_ACTIONS" <<< "$out"; then
+  pass "Error correctly explains GITHUB_ACTIONS prohibition"
+else
+  fail "Unexpected error message for GITHUB_ACTIONS prohibition: $out"
+fi
+
+# If gh reports error/network failure, check fails closed (exit 8)
+echo "error" > "$MOCK_GH_STATE"
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pr 999 --skip-pull --manifest "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "gh failure fails closed (exit 8)" "$rc" "8"
+if grep -q "Hosted reconciler check failed: unable to query GitHub Actions" <<< "$out"; then
+  pass "gh error produces clean failure message"
+else
+  fail "Unexpected error message on gh error: $out"
+fi
+
+# Reset mock gh to clean
+echo "clean" > "$MOCK_GH_STATE"
+
+# Reset working repo state for pre-merge checks
+git -C "$REPO" checkout -q development
+# Ensure valid active doc is back in 2-WORKING
+if [ -f "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" ]; then
+  mv "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+  sed -i.bak 's/status: Complete/status: Review/' "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+  rm -f "$REPO/PROJECT/2-WORKING/GH-999-TEST.md.bak"
+  git -C "$REPO" add -A
+  git -C "$REPO" commit -q -m "test: reset doc to 2-WORKING"
+fi
+
+# Update test receipt with current HEAD
+HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
+cat << EOF_REC > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+{"commit": "$HEAD_SHA", "pr": 999, "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
+EOF_REC
+git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+git -C "$REPO" commit -q -m "fix: closes #999"
+
+# -------------------------------------------------------------
+# Part 2: Pre-Merge Validation Checks (--pre-merge)
+# -------------------------------------------------------------
+# Case A: Valid doc, substantive lessons learned, matching committed receipt -> PASS (exit 0)
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
+assert_eq "Pre-merge check passes when all conditions are met (exit 0)" "$rc" "0"
+if grep -q "Pre-merge validation PASSED!" <<< "$out"; then
+  pass "Pre-merge confirmation message output"
+else
+  fail "Pre-merge did not output PASSED confirmation: $out"
+fi
+
+# Case B: Red Control 1 - Empty/placeholder lessons learned -> exit 5
+cat << 'DOC_LL' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+---
+title: Test Task
+status: Review
+created: 2026-09-10
+updated: 2026-09-10
+owner: test-agent
+goal: Verify pre-merge checks
+---
+# GH-999: Test Task
+
+## Lessons Learned
+
+TODO: add lessons learned later
+<!-- none yet -->
+DOC_LL
+git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+git -C "$REPO" commit -q -m "fix: closes #999 with empty lessons learned"
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
+assert_eq "Placeholder lessons learned is rejected (exit 5)" "$rc" "5"
+if grep -q "empty/placeholder '## Lessons Learned'" <<< "$out"; then
+  pass "Error message cites empty/placeholder lessons learned"
+else
+  fail "Error message missing placeholder explanation: $out"
+fi
+
+# Case C: Red Control 2 - Missing required frontmatter field -> exit 5
+cat << 'DOC_FM' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+---
+title: Test Task
+status: Review
+created: 2026-09-10
+updated: 2026-09-10
+goal: Verify pre-merge checks
+---
+# GH-999: Test Task
+
+## Lessons Learned
+
+### 1. Substantive
+Reflections exist here.
+DOC_FM
+git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+git -C "$REPO" commit -q -m "fix: closes #999 with missing owner in frontmatter"
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
+assert_eq "Missing frontmatter owner field is rejected (exit 5)" "$rc" "5"
+if grep -q "frontmatter missing required field(s): owner" <<< "$out"; then
+  pass "Error message cites missing owner field"
+else
+  fail "Error message missing frontmatter explanation: $out"
+fi
+
+# Case D: Red Control 3 - Missing committed test receipt -> exit 6
+# Restore valid doc
+cat << 'DOC_VALID' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+---
+title: Test Task
+status: Review
+created: 2026-09-10
+updated: 2026-09-10
+owner: test-agent
+goal: Verify pre-merge checks
+---
+# GH-999: Test Task
+
+## Lessons Learned
+
+### 1. Substantive
+Reflections exist here.
+DOC_VALID
+git -C "$REPO" rm -q "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
+git -C "$REPO" commit -q -m "fix: closes #999 without test receipt"
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
+assert_eq "Missing committed test receipt is rejected (exit 6)" "$rc" "6"
+if grep -q "No committed provenance.jsonl or error_log.jsonl receipts found" <<< "$out"; then
+  pass "Error message cites missing committed receipt at HEAD"
+else
+  fail "Error message missing receipt explanation: $out"
+fi
+
+# Case E: Red Control 4 - Uncommitted test receipt is not proof -> exit 6
+mkdir -p "$REPO/TESTS-RESULTS/2026-09-10+GH-999"
+echo '{"commit": "xyz", "rc": 0, "result": "pass"}' > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+# Receipt exists on disk as untracked file, but NOT committed in git tree at HEAD
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
+assert_eq "Uncommitted test receipt does not satisfy check (exit 6)" "$rc" "6"
+rm -f "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
+
+# -------------------------------------------------------------
+# Part 3: Marathon Plan Fingerprinting
+# -------------------------------------------------------------
+# Clean up any leftover plan docs and reset planner log
+rm -f "$REPO/planner_calls.log" "$REPO/.tick/marathon-plan.fingerprint"
+touch "$REPO/PROJECT/2-WORKING/MARATHON-PLAN-2026-09-10.md"
+git -C "$REPO" add -A
+git -C "$REPO" commit -q -m "test: fixture for marathon plan fingerprinting"
+
+# 1st run: Fingerprint does not exist yet -> marathon-plan.sh must execute
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "Reconciler runs successfully (exit 0)" "$rc" "0"
+calls_run1="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
+assert_eq "Marathon planner executed on initial run" "$calls_run1" "1"
+[ -f "$REPO/.tick/marathon-plan.fingerprint" ] || fail "Fingerprint file not created at .tick/marathon-plan.fingerprint"
+pass "Fingerprint file created on initial run"
+
+# 2nd run: Inputs unchanged -> marathon-plan.sh must be skipped!
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "Second run exits 0" "$rc" "0"
+calls_run2="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
+assert_eq "Marathon planner skipped when canonical inputs unchanged" "$calls_run2" "1"
+if grep -q "skipping marathon-plan.sh — canonical inputs unchanged" <<< "$out"; then
+  pass "Log confirms marathon-plan.sh was skipped due to unchanged fingerprint"
+else
+  fail "Log missing skipped marathon-plan explanation: $out"
+fi
+
+# 3rd run: Mutate roadmap_items in releases.db -> fingerprint changes -> marathon-plan.sh must run!
+python3 -c '
+import sqlite3
+conn = sqlite3.connect("'"$REPO/releases.db"'")
+conn.execute("INSERT INTO roadmap_items (global_id, repo_id, gh_number, title, section, position, raw_text, first_seen, updated_at) VALUES (\x27rmi-NEW0000000000000000000001\x27, 1, 1002, \x27New Item\x27, \x27Now\x27, 2, \x27- **GH-1002**\x27, \x272026-09-10\x27, \x272026-09-10\x27)")
+conn.commit()
+conn.close()
+'
+rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
+assert_eq "Third run exits 0 after roadmap mutation" "$rc" "0"
+calls_run3="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
+assert_eq "Marathon planner re-executed when roadmap inputs modified" "$calls_run3" "2"
+
+echo "=== All GH-496 Phase 2 tests passed successfully! ==="
diff --git a/utils/py/harness_app.py b/utils/py/harness_app.py
index 124ef7a4..4d9d2775 100755
--- a/utils/py/harness_app.py
+++ b/utils/py/harness_app.py
@@ -1,96 +1,199 @@
 #!/usr/bin/env python3
 """harness_app.py (GH-174) — Transactional Harness & Models SQLite Registry CLI.
 
 Canonical SQLite ledger for agent harnesses, model routes, per-device configurations,
 reasoning effort levels, deterministic post-turn AI evaluations, and grounded blog story synthesis.
 """
 
 import argparse
 import datetime
+import hashlib
 import json
 import os
+import re
 import sqlite3
+import subprocess
 import sys
 from pathlib import Path
 from typing import Any, Dict, List, Optional, Tuple
 
 
 def get_repo_root() -> str:
     """Resolve repository root."""
     return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
 
+def slugify(value: str) -> str:
+    """Normalize a name into a stable slug."""
+    cleaned = re.sub(r"[^\w\s-]", "", value).strip().lower()
+    return re.sub(r"[-\s]+", "-", cleaned) or "repository"
+
+
+def get_canonical_repository_root(root: Path) -> Path:
+    """Resolve canonical repository root even inside a linked worktree (GH-496)."""
+    try:
+        r_top = subprocess.run(
+            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
+            capture_output=True, text=True, check=False
+        )
+        top = r_top.stdout.strip() if r_top.returncode == 0 else ""
+        r_common = subprocess.run(
+            ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
+            capture_output=True, text=True, check=False
+        )
+        common = r_common.stdout.strip() if r_common.returncode == 0 else ""
+        if common:
+            c_path = Path(common).resolve()
+            if c_path.name == ".git":
+                return c_path.parent
+        if top:
+            return Path(top).resolve()
+    except Exception:
+        pass
+    return root.resolve()
+
+
+def normalize_remote_url(remote: str) -> str:
+    """Normalize git remote URL so git@... and https://... resolve to the same canonical identity (GH-496)."""
+    norm = remote.strip().rstrip("/")
+    if norm.endswith(".git"):
+        norm = norm[:-4]
+    # Convert git@github.com:org/repo to https://github.com/org/repo
+    if norm.startswith("git@"):
+        norm = "https://" + norm[4:].replace(":", "/", 1)
+    elif norm.startswith("ssh://git@"):
+        norm = "https://" + norm[10:].replace(":", "/", 1)
+    return norm
+
+
+def get_canonical_repo_identity(repo_root: Optional[str] = None) -> Tuple[str, str]:
+    """Derive stable repository slug and canonical remote/path identity (GH-496)."""
+    root = Path(repo_root or get_repo_root()).resolve()
+    canon_root = get_canonical_repository_root(root)
+    remote = ""
+    try:
+        r = subprocess.run(
+            ["git", "-C", str(canon_root), "config", "--get", "remote.origin.url"],
+            capture_output=True,
+            text=True,
+            check=False,
+        )
+        if r.returncode == 0 and r.stdout.strip():
+            remote = r.stdout.strip()
+    except Exception:
+        remote = ""
+
+    if remote:
+        identity = normalize_remote_url(remote)
+    else:
+        identity = str(canon_root)
+    name = identity.rsplit("/", 1)[-1].rsplit(":", 1)[-1] or canon_root.name
+    short_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
+    return f"{slugify(name)}--{short_id}", identity
+
+
+def get_project_key(repo_root: Optional[str] = None) -> str:
+    """Derive stable project key for host telemetry store (GH-496)."""
+    key, _ = get_canonical_repo_identity(repo_root)
+    return key
+
+
 def get_db_path(repo_root: Optional[str] = None) -> str:
+    """Resolve SQLite database path (GH-496).
+    
+    Precedence:
+    1. XYZ_HARNESS_DB env var (explicit override for testing/fixtures).
+    2. Out-of-tree default: ~/.xyz/projects/<project-key>/telemetry/harnesses.db
+    3. In-repo fallback: <repo_root>/harnesses.db if HOME is unavailable.
+    """
     if "XYZ_HARNESS_DB" in os.environ:
         return os.environ["XYZ_HARNESS_DB"]
     root = repo_root or get_repo_root()
+    home = os.environ.get("HOME")
+    if home and os.path.isdir(home):
+        project_key = get_project_key(root)
+        telemetry_dir = os.path.join(home, ".xyz", "projects", project_key, "telemetry")
+        return os.path.join(telemetry_dir, "harnesses.db")
     return os.path.join(root, "harnesses.db")
 
 
 def get_sql_path(repo_root: Optional[str] = None) -> str:
+    """Resolve logical SQL dump path (GH-496)."""
     if "XYZ_HARNESS_SQL" in os.environ:
         return os.environ["XYZ_HARNESS_SQL"]
     if "XYZ_HARNESS_DB" in os.environ:
         base = os.path.splitext(os.environ["XYZ_HARNESS_DB"])[0]
         return base + ".sql"
     root = repo_root or get_repo_root()
-    return os.path.join(root, "harnesses.sql")
+    db_p = get_db_path(root)
+    base = os.path.splitext(db_p)[0]
+    return base + ".sql"
 
 
 def get_generated_md_path(repo_root: Optional[str] = None) -> str:
+    """Resolve generated markdown registry view path (GH-496)."""
     if "XYZ_HARNESS_GENERATED_MD" in os.environ:
         return os.environ["XYZ_HARNESS_GENERATED_MD"]
     if "XYZ_HARNESS_DB" in os.environ:
         db_dir = os.path.dirname(os.path.abspath(os.environ["XYZ_HARNESS_DB"]))
         return os.path.join(db_dir, "HARNESS-MODELS-REGISTRY.generated.md")
     root = repo_root or get_repo_root()
+    db_p = get_db_path(root)
+    db_dir = os.path.dirname(os.path.abspath(db_p))
+    if db_dir != os.path.abspath(root):
+        return os.path.join(db_dir, "HARNESS-MODELS-REGISTRY.generated.md")
     return os.path.join(root, "HARNESS-MODELS-REGISTRY.generated.md")
 
 
 def get_blog_doc_path(slug: str, repo_root: Optional[str] = None) -> str:
+    """Resolve generated blog case study path (GH-496)."""
     if "XYZ_HARNESS_DOCS_DIR" in os.environ:
         return os.path.join(os.environ["XYZ_HARNESS_DOCS_DIR"], f"blog-{slug}.md")
     if "XYZ_HARNESS_DB" in os.environ:
         db_dir = os.path.dirname(os.path.abspath(os.environ["XYZ_HARNESS_DB"]))
         return os.path.join(db_dir, "docs", f"blog-{slug}.md")
     root = repo_root or get_repo_root()
+    db_p = get_db_path(root)
+    db_dir = os.path.dirname(os.path.abspath(db_p))
+    if db_dir != os.path.abspath(root):
+        return os.path.join(db_dir, "docs", f"blog-{slug}.md")
     return os.path.join(root, "docs", f"blog-{slug}.md")
 
 
 def init_db(db_path: str) -> sqlite3.Connection:
     """Initialize SQLite database with full schema, indexes, and PRAGMAs."""
     os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
     conn = sqlite3.connect(db_path)
     conn.row_factory = sqlite3.Row
     conn.execute("PRAGMA foreign_keys = ON;")
     conn.execute("PRAGMA journal_mode = WAL;")
 
     with conn:
         conn.executescript("""
         CREATE TABLE IF NOT EXISTS devices (
             device_id TEXT PRIMARY KEY,
             user_name TEXT NOT NULL,
             os_version TEXT NOT NULL,
             cpu_cores INTEGER NOT NULL,
             ram_gb INTEGER NOT NULL,
             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
         );
 
         CREATE TABLE IF NOT EXISTS user_configs (
             config_id TEXT PRIMARY KEY,
             device_id TEXT NOT NULL REFERENCES devices(device_id),
             default_harness TEXT NOT NULL,
             default_gateway TEXT NOT NULL,
             default_model TEXT NOT NULL,
             default_reasoning_effort TEXT,
             is_active INTEGER DEFAULT 1,
             updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
         );
 
         CREATE TABLE IF NOT EXISTS harnesses (
             harness_id TEXT PRIMARY KEY,
             name TEXT NOT NULL,
             execution_engine TEXT NOT NULL,
             supports_programmatic INTEGER DEFAULT 0,
             supports_reasoning_effort INTEGER DEFAULT 1,
             headless_command_template TEXT NOT NULL,
@@ -139,298 +242,333 @@ def init_db(db_path: str) -> sqlite3.Connection:
             evaluation_role TEXT NOT NULL,
             grade TEXT NOT NULL CHECK(grade IN ('A', 'A-', 'B+', 'B', 'B-', 'C', 'N/A')),
             qualifying_gate_passed INTEGER NOT NULL,
             diff_cleanliness_score INTEGER,
             seam_reliability_score INTEGER,
             work_description_narrative TEXT NOT NULL,
             failure_mode_tag TEXT,
             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
         );
 
         CREATE TABLE IF NOT EXISTS blog_stories (
             story_id TEXT PRIMARY KEY,
             title TEXT NOT NULL,
             slug TEXT NOT NULL UNIQUE,
             theme TEXT NOT NULL,
             source_evaluations TEXT NOT NULL,
             story_metadata TEXT,
             markdown_content TEXT NOT NULL,
             published_at DATETIME,
             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
         );
 
         CREATE INDEX IF NOT EXISTS idx_invocation_device ON invocation_logs(device_id);
         CREATE INDEX IF NOT EXISTS idx_invocation_harness ON invocation_logs(harness_id);
         CREATE INDEX IF NOT EXISTS idx_invocation_model ON invocation_logs(model_id);
         CREATE INDEX IF NOT EXISTS idx_eval_grade ON evaluations(grade);
         """)
         # GH-450: a database created before the Model-catalog integration has no
         # model_catalog_version column, and CREATE TABLE IF NOT EXISTS will not add one. Additive,
         # nullable, idempotent — rows logged before the column simply carry NULL.
         cols = {r[1] for r in conn.execute("PRAGMA table_info(invocation_logs);").fetchall()}
         if "model_catalog_version" not in cols:
             try:
                 conn.execute("ALTER TABLE invocation_logs ADD COLUMN model_catalog_version TEXT;")
             except sqlite3.OperationalError as e:
                 # Two shims opening the same pre-GH-450 db concurrently can both see the column
                 # missing; the loser's ALTER fails with "duplicate column name". That is the
                 # migration having succeeded, not a failure — a turn must never lose its row to it.
                 if "duplicate column" not in str(e).lower():
                     raise
+        # GH-496: Auto-seed canonical registry if harnesses table is empty
+        h_count = conn.execute("SELECT COUNT(*) FROM harnesses;").fetchone()[0]
+        if h_count == 0:
+            seed_canonical_registry(conn)
     return conn
 
 
 def seed_canonical_registry(conn: sqlite3.Connection):
     """Seed initial canonical data from HARNESS-MODELS-REGISTRY baseline."""
     # 1. Devices
     with conn:
         conn.execute("""
         INSERT OR IGNORE INTO devices (device_id, user_name, os_version, cpu_cores, ram_gb)
         VALUES ('primary-macbook-host', 'noelsaw1', 'macOS 15.6', 16, 64);
         """)
 
         # 2. User Config
         conn.execute("""
         INSERT OR IGNORE INTO user_configs (config_id, device_id, default_harness, default_gateway, default_model, default_reasoning_effort)
         VALUES ('cfg-primary-default', 'primary-macbook-host', 'deepseek-harness', 'openrouter', 'deepseek/deepseek-v4-pro', 'high');
         """)
 
         # 3. Harnesses
         harnesses_data = [
             ('dsh', 'DeepSeek Harness', 'node_cordis', 1, 1, 'DSH_PERMISSION_MODE=danger-full-access node .../apps/cli/lib/bin.js --profile headless --patch {overlay} "{task}"', 'Autonomous Headless Builder', 'Evaluated across 4 repository bugs with zero intervention.'),
             ('commandcode', 'Command Code', 'node_langbase', 1, 1, 'cmd -p --tools-all --yolo -t "{task}"', 'Builder & Systems Reviewer', 'Requires worktree isolation and timeout bounding.'),
             ('codex', 'Codex CLI', 'native_cli', 0, 1, 'codex exec "{task}"', 'Cost-blind default builder and reviewer', 'Subscription authenticated.'),
             ('agy', 'Antigravity CLI', 'native_cli', 0, 1, 'agy -p "{task}"', 'Cost-blind cross-model builder/reviewer', 'Sandbox-off required; check empty exit-0.'),
             ('claude', 'Claude Code', 'native_cli', 0, 1, 'claude -p "{task}"', 'Orchestrator and final reviewer', 'Do not use as default headless builder.'),
             ('aider', 'Aider', 'python_litellm', 0, 0, 'aider --message "{task}"', 'Builder only', 'Force AIDER_FLAGS=--edit-format diff; reviewer seam Intermittent.'),
             ('pi', 'Pi Agent', 'node_multi', 0, 0, 'pi -p --mode json "{task}"', 'Builder only', 'Explicit PI_MODEL required.'),
             ('muse', 'Muse Code', 'native_cli', 1, 1, 'muse exec --model {model} --reasoning-effort {effort} --workspace {workspace} --trust-workspace --prompt-file {task}', 'Evaluation only (GH-518)', 'Absolute MUSE_BIN (PATH not modified). Needs --workspace + --trust-workspace or the turn is read-only and silently writes nothing. Contributor tier carries a data-use clause: public repos only.'),
         ]
         for h in harnesses_data:
             conn.execute("""
             INSERT OR REPLACE INTO harnesses (harness_id, name, execution_engine, supports_programmatic, supports_reasoning_effort, headless_command_template, standing_policy_role, operating_constraint)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?);
             """, h)
 
         # 4. Models
         models_data = [
             ('openrouter/deepseek/deepseek-v4-pro', 'DeepSeek', 'DeepSeek V4 Pro', 'openrouter', 1000000, 0.435, 0.87, 0.0036, '["low", "medium", "high", "max"]'),
             ('deepseek/deepseek-chat', 'DeepSeek', 'DeepSeek V3', 'openrouter', 1000000, 0.27, 1.10, 0.0028, '["none"]'),
             ('Qwen/Qwen3.8-Max', 'Alibaba', 'Qwen 3.8-Max', 'openrouter', 1000000, 2.00, 6.00, 0.25, '["low", "medium", "xhigh"]'),
             ('Qwen/Qwen3.7-Flash', 'Alibaba', 'Qwen 3.7-Flash', 'openrouter', 1000000, 0.03, 0.13, 0.006, '["none"]'),
             ('openrouter/stealth/ox-alpha', 'Stealth', 'Stealth Ox-Alpha', 'openrouter', 1000000, 1.50, 4.50, 0.20, '["high", "max"]'),
             ('zai-org/GLM-5.3', 'Z.ai', 'GLM 5.3 High', 'openrouter', 1000000, 1.40, 4.40, 0.26, '["low", "high", "max"]'),
             ('google/gemma-4-31b-qat', 'Google', 'Gemma 4 31B QAT', 'lmstudio', 32768, 0.0, 0.0, 0.0, '["none"]'),
             # GH-518. Prices and reasoning tiers are Meta's own provider-catalog values as served to
             # Muse Code 1.0.3, not documentation. The two rows are the SAME model on different terms:
             # the -contributor tier is ~12x cheaper because submitted content, including
             # inter-session messages, may be used for product improvement. Note it also drops the
             # `max` reasoning tier the full-price row carries.
             ('muse-spark-1.3', 'Meta', 'Muse Spark 1.3', 'meta', 1007997, 1.25, 4.25, 0.15, '["minimal", "low", "medium", "high", "xhigh", "max"]'),
             ('muse-spark-1.3-contributor', 'Meta', 'Muse Spark 1.3 Contributor', 'meta', 1007997, 0.10, 0.20, 0.002, '["minimal", "low", "medium", "high", "xhigh"]'),
         ]
         for m in models_data:
             conn.execute("""
             INSERT OR REPLACE INTO models (model_id, lab, canonical_name, gateway, context_window, prompt_price_per_m, completion_price_per_m, cache_read_price_per_m, supported_reasoning_levels)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
             """, m)
 
 
 def dump_sql(conn: sqlite3.Connection, sql_path: str):
-    """Losslessly dump database schema and contents into SQL text file."""
-    with open(sql_path, "w", encoding="utf-8") as f:
-        for line in conn.iterdump():
-            f.write(f"{line}\n")
+    """Losslessly dump database schema and contents into SQL text file atomically."""
+    os.makedirs(os.path.dirname(os.path.abspath(sql_path)), exist_ok=True)
+    tmp_path = f"{sql_path}.tmp.{os.getpid()}"
+    try:
+        with open(tmp_path, "w", encoding="utf-8") as f:
+            for line in conn.iterdump():
+                f.write(f"{line}\n")
+        os.replace(tmp_path, sql_path)
+    finally:
+        if os.path.exists(tmp_path):
+            try:
+                os.remove(tmp_path)
+            except OSError:
+                pass
 
 
 def generate_markdown(conn: sqlite3.Connection, md_path: str):
-    """Render canonical HARNESS-MODELS-REGISTRY.generated.md view from database."""
+    """Render canonical HARNESS-MODELS-REGISTRY.generated.md view from database atomically."""
     harnesses = conn.execute("SELECT * FROM harnesses ORDER BY harness_id;").fetchall()
     models = conn.execute("SELECT * FROM models ORDER BY lab, canonical_name;").fetchall()
     evals = conn.execute("""
         SELECT e.grade, e.evaluated_by, e.evaluation_role, e.work_description_narrative,
                i.harness_id, i.model_id, i.reasoning_effort, i.created_at
         FROM evaluations e
         JOIN invocation_logs i ON e.invocation_id = i.invocation_id
         ORDER BY e.created_at DESC;
     """).fetchall()
 
     lines = [
         "# Harness & Models Registry (Generated View)",
         "",
         "<!-- Auto-generated from harnesses.db by utils/py/harness_app.py — DO NOT HAND-EDIT -->",
         "",
         "## 1. Operating Harnesses & Policy Lanes",
         "",
         "| Harness | Execution Engine | Policy Role | Operating Constraint |",
         "|---|---|---|---|",
     ]
     for h in harnesses:
         lines.append(f"| **{h['name']}** (`{h['harness_id']}`) | `{h['execution_engine']}` | {h['standing_policy_role'] or '—'} | {h['operating_constraint'] or '—'} |")
 
     lines.extend([
         "",
         "## 2. Frontier Models & Reasoning Catalog",
         "",
         "| Lab | Model | Context | Reasoning Levels | Pricing ($/1M in / out / cache) |",
         "|---|---|:---:|:---:|:---:|",
     ])
     for m in models:
         p_in = f"${m['prompt_price_per_m']:.2f}" if m['prompt_price_per_m'] is not None else "—"
         p_out = f"${m['completion_price_per_m']:.2f}" if m['completion_price_per_m'] is not None else "—"
         p_cache = f"${m['cache_read_price_per_m']:.4f}" if m['cache_read_price_per_m'] is not None else "—"
         prices = f"{p_in} / {p_out} / {p_cache}"
         raw_levels = m['supported_reasoning_levels'] or ""
         if raw_levels.startswith("["):
             try:
                 levels = ", ".join(json.loads(raw_levels))
             except Exception:
                 levels = raw_levels
         else:
             levels = raw_levels
         levels = levels or "—"
         lines.append(f"| **{m['lab']}** | `{m['canonical_name']}` | {m['context_window']:,} | `{levels}` | {prices} |")
 
     lines.extend([
         "",
         "## 3. Empirical Evaluation History & Qualitative Work Logs",
         "",
     ])
     if not evals:
         lines.append("*No evaluations recorded yet in database.*")
     else:
         for ev in evals:
             lines.append(f"### `{ev['model_id']}` on `{ev['harness_id']}` — Grade **{ev['grade']}**")
             lines.append(f"**Evaluated by:** `{ev['evaluated_by']}` ({ev['evaluation_role']}) | **Date:** {ev['created_at']}")
             if ev['reasoning_effort']:
                 lines.append(f"**Reasoning Effort:** `{ev['reasoning_effort']}`")
             lines.append("")
             lines.append(ev['work_description_narrative'])
             lines.append("")
 
     content = "\n".join(lines) + "\n"
-    with open(md_path, "w", encoding="utf-8") as f:
-        f.write(content)
+    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
+    tmp_path = f"{md_path}.tmp.{os.getpid()}"
+    try:
+        with open(tmp_path, "w", encoding="utf-8") as f:
+            f.write(content)
+        os.replace(tmp_path, md_path)
+    finally:
+        if os.path.exists(tmp_path):
+            try:
+                os.remove(tmp_path)
+            except OSError:
+                pass
 
 
 def check_integrity(repo_root: Optional[str] = None) -> int:
     """Validate database foreign keys, schema consistency, and generated views."""
     root = repo_root or get_repo_root()
     db_p = get_db_path(root)
+    # GH-496: If out-of-tree telemetry DB does not exist yet (e.g. cold runner),
+    # but in-repo harnesses.db exists, fall back to in-repo DB for check ONLY IF
+    # XYZ_HARNESS_DB was not explicitly overridden.
+    if "XYZ_HARNESS_DB" not in os.environ and not os.path.exists(db_p):
+        in_repo = os.path.join(root, "harnesses.db")
+        if os.path.exists(in_repo):
+            db_p = in_repo
+
     sql_p = get_sql_path(root)
     gen_md = get_generated_md_path(root)
 
     if not os.path.exists(db_p):
         print(f"harness check: FAIL — database missing at {db_p}", file=sys.stderr)
         return 1
 
     conn = init_db(db_p)
     fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
     if fk_errors:
         print(f"harness check: FAIL — foreign key integrity errors: {fk_errors}", file=sys.stderr)
         return 1
 
     integ = conn.execute("PRAGMA integrity_check;").fetchall()
     if not integ or integ[0][0] != "ok":
         print(f"harness check: FAIL — SQLite integrity check failed: {integ}", file=sys.stderr)
         return 1
 
-    print("OK: SQLite database integrity verified (foreign_keys=ON, integrity_check=ok)")
+    print(f"OK: SQLite database integrity verified at {db_p} (foreign_keys=ON, integrity_check=ok)")
     print("harness check: clean (0 failures, 0 warnings)")
     return 0
 
 
 def main() -> int:
     parser = argparse.ArgumentParser(description="harness_app.py — Harness & Models SQLite Registry CLI")
+    parser.add_argument("--local", action="store_true", help="Force using in-repo harnesses.db instead of user telemetry path (GH-496)")
     subparsers = parser.add_subparsers(dest="subcommand", required=True)
 
     # Subcommand: init
     subparsers.add_parser("init", help="Initialize and seed harnesses.db")
 
     # Subcommand: dump
     subparsers.add_parser("dump", help="Dump database to harnesses.sql")
 
     # Subcommand: gen
     subparsers.add_parser("gen", help="Generate HARNESS-MODELS-REGISTRY.generated.md")
 
     # Subcommand: check
     subparsers.add_parser("check", help="Run integrity and schema validation checks")
 
     # Subcommand: log
     log_parser = subparsers.add_parser("log", help="Log a harness execution invocation")
     log_parser.add_argument("--device-id", required=True)
     log_parser.add_argument("--harness-id", required=True)
     log_parser.add_argument("--model-id", required=True)
     log_parser.add_argument("--gateway", default="openrouter")
     log_parser.add_argument("--reasoning-effort", choices=["none", "low", "medium", "high", "max", "xhigh"])
     log_parser.add_argument("--shim", required=True)
     log_parser.add_argument("--flags", default="[]")
     log_parser.add_argument("--task-scope", required=True)
     log_parser.add_argument("--seconds", type=float, default=0.0)
     log_parser.add_argument("--exit-code", type=int, default=0)
     log_parser.add_argument("--tokens", type=int, default=0)
     log_parser.add_argument("--cost", type=float, default=0.0)
     log_parser.add_argument("--diff-stat", default="")
     log_parser.add_argument("--catalog-version", default=None,
                             help="GH-450: Model-catalog version the alias table was rendered from")
 
     # Subcommand: eval
     eval_parser = subparsers.add_parser("eval", help="Record a post-turn AI evaluation")
     eval_parser.add_argument("--invocation-id", required=True)
     eval_parser.add_argument("--evaluated-by", required=True)
     eval_parser.add_argument("--role", required=True)
     eval_parser.add_argument("--grade", choices=["A", "A-", "B+", "B", "B-", "C", "N/A"], required=True)
     eval_parser.add_argument("--gate-passed", type=int, choices=[0, 1], required=True)
     eval_parser.add_argument("--cleanliness", type=int, default=5)
     eval_parser.add_argument("--seam-score", type=int, default=5)
     eval_parser.add_argument("--narrative", required=True)
     eval_parser.add_argument("--failure-tag", default="none")
 
     # Subcommand: blog
     blog_parser = subparsers.add_parser("blog", help="Blog story generator subcommands")
     blog_sub = blog_parser.add_subparsers(dest="blog_command", required=True)
     gen_blog = blog_sub.add_parser("gen", help="Generate a publishable case study story")
     gen_blog.add_argument("--theme", required=True)
     gen_blog.add_argument("--slug", required=True)
 
     args = parser.parse_args()
     root = get_repo_root()
+    if getattr(args, "local", False):
+        os.environ["XYZ_HARNESS_DB"] = os.path.join(root, "harnesses.db")
     db_p = get_db_path(root)
     sql_p = get_sql_path(root)
     md_p = get_generated_md_path(root)
 
     if args.subcommand == "init":
         conn = init_db(db_p)
         seed_canonical_registry(conn)
         dump_sql(conn, sql_p)
         generate_markdown(conn, md_p)
         print(f"Initialized {db_p} -> dumped {sql_p} -> rendered {md_p}")
         return 0
 
     if args.subcommand == "dump":
         conn = init_db(db_p)
         dump_sql(conn, sql_p)
         print(f"Dumped database to {sql_p}")
         return 0
 
     if args.subcommand == "gen":
         conn = init_db(db_p)
         generate_markdown(conn, md_p)
         print(f"Rendered {md_p}")
         return 0
 
     if args.subcommand == "check":
         return check_integrity(root)
 
     if args.subcommand == "log":
         conn = init_db(db_p)
         inv_id = f"inv-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
         # Auto-infer lab from model identifier (e.g., 'anthropic/claude-3-7-sonnet' -> 'Anthropic')
         lab = "Auto"
         if "/" in args.model_id:
             parts = [p.strip() for p in args.model_id.split("/") if p.strip()]
             if parts:
                 if parts[0].lower() == "openrouter" and len(parts) >= 2:
                     lab = parts[1].capitalize()
                 else:
                     lab = parts[0].capitalize()
 
@@ -495,50 +633,59 @@ def main() -> int:
         story_id = f"story-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
         title = args.theme
         body = [
             f"# {title}",
             "",
             f"**Generated by:** `utils/py/harness_app.py blog gen` | **Published:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}",
             "",
             "## Executive Summary & Empirical Takeaways",
             "",
             f"This benchmark analysis synthesizes empirical results across {len(evals)} verified agent evaluations under load in `XYZ-forge`.",
             "",
             "## Evaluated Performance Matrix",
             "",
             "| Task Scope | Harness & Model | Reasoning Level | Duration | Gate Passed | Grade |",
             "|---|---|:---:|:---:|:---:|:---:|",
         ]
         for ev in evals:
             gate_badge = "✅ PASS" if ev['qualifying_gate_passed'] else "❌ FAIL"
             body.append(f"| {ev['task_scope']} | `{ev['harness_id']}` + `{ev['model_id']}` | `{ev['reasoning_effort'] or 'standard'}` | {ev['wall_clock_seconds']:.1f}s | {gate_badge} | **{ev['grade']}** |")
 
         body.extend([
             "",
             "## In-Depth Architectural Narratives & Field Notes",
             "",
         ])
         for ev in evals:
             body.append(f"### Case Study: `{ev['model_id']}` on `{ev['task_scope']}`")
             body.append(ev['work_description_narrative'])
             body.append("")
 
         story_md = "\n".join(body) + "\n"
         with conn:
             conn.execute("""
             INSERT OR REPLACE INTO blog_stories (story_id, title, slug, theme, source_evaluations, markdown_content, published_at)
             VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
             """, (story_id, title, args.slug, args.theme, json.dumps([]), story_md))
 
         dump_sql(conn, sql_p)
         out_path = get_blog_doc_path(args.slug, root)
         os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
-        with open(out_path, "w", encoding="utf-8") as f:
-            f.write(story_md)
+        tmp_out = f"{out_path}.tmp.{os.getpid()}"
+        try:
+            with open(tmp_out, "w", encoding="utf-8") as f:
+                f.write(story_md)
+            os.replace(tmp_out, out_path)
+        finally:
+            if os.path.exists(tmp_out):
+                try:
+                    os.remove(tmp_out)
+                except OSError:
+                    pass
         print(f"Generated blog story {story_id} -> {out_path}")
         return 0
 
     return 0
 
 
 if __name__ == "__main__":
     sys.exit(main())
diff --git a/utils/py/jog_run.py b/utils/py/jog_run.py
index 356752b6..cb09233b 100755
--- a/utils/py/jog_run.py
+++ b/utils/py/jog_run.py
@@ -210,91 +210,96 @@ def validate_marathon_executor(args):
 
 
 def _jog_state_paths(root, gid):
     base = os.path.join(root, ".tick", "jog", gid)
     return base, os.path.join(base, "state.json")
 
 
 def _ledger_abs_path(root, gid, path):
     """Resolve a ledger-recorded path. GH-292 F2: new records store paths RELATIVE to the
     ledger base (<root>/.tick/jog/<gid>/) so the ledger survives a queue-row re-add (a fresh
     global_id) without re-key surgery. Absolute paths from older records still resolve."""
     if not path:
         return path
     if os.path.isabs(path):
         return path
     base, _ = _jog_state_paths(root, gid)
     return os.path.join(base, path)
 
 
 def _ledger_rel_path(root, gid, path):
     """Store-side twin of _ledger_abs_path: absolute→relative when the path sits inside this
     ledger; anything else is stored verbatim."""
     if not path or not os.path.isabs(path):
         return path
     base, _ = _jog_state_paths(root, gid)
     try:
         rel = os.path.relpath(path, base)
     except ValueError:
         return path
     if rel == os.pardir or rel.startswith(os.pardir + os.sep):
         return path
     return rel
 
 
 def jog_regenerate_dashboard(root):
     """GH-292 F3: jog's promotion repoints roadmap rows and stalens the committed
     ROADMAP-DASHBOARD.md — the lane's own gate then fails on drift (observed on both Phase-4
     dogfood items). Regenerate after promotion, before dispatch. Best-effort and scoped to
     installs that ship the renderer."""
     script = None
-    for candidate in (os.path.join(harness_home(), "utils", "roadmap-dashboard.sh"),
-                      os.path.join(root, "utils", "roadmap-dashboard.sh")):
+    for candidate in (os.path.join(root, "utils", "roadmap-dashboard.sh"),
+                      os.path.join(harness_home(), "utils", "roadmap-dashboard.sh")):
         if os.path.isfile(candidate):
             script = candidate
             break
     if not script:
         return
     try:
-        subprocess.run(["bash", script], cwd=root, capture_output=True, text=True, timeout=120)
-    except (OSError, subprocess.SubprocessError):
-        pass
+        env = dict(os.environ)
+        env["ROADMAP_DASHBOARD_ROOT"] = str(root)
+        r = subprocess.run(["bash", script], cwd=root, env=env, capture_output=True, text=True, timeout=120)
+        if r.returncode != 0:
+            print(f"jog: warning: roadmap-dashboard refresh failed ({r.returncode}): {(r.stderr or r.stdout).strip()}",
+                  file=sys.stderr)
+    except (OSError, subprocess.SubprocessError) as e:
+        print(f"jog: warning: roadmap-dashboard refresh exception: {e}", file=sys.stderr)
 
 
 def jog_commit_supervisor_state(root, gh_num, exec_id):
     """GH-292 F1: commit the supervisor's own ledger/doc writes before dispatch.
 
     The turn-containment pass restores tracked working-tree modifications to HEAD, and jog's
     uncommitted writes (releases.db/sql, regenerated views, the promoted doc pair) are
     indistinguishable from an agent's off-lane edits — the Phase-4 dogfood lost queue rows to
     exactly this, twice. Committing supervisor-owned paths BEFORE any turn dispatches makes
     containment have nothing of the supervisor's to revert.
 
     Stages an explicit path list only — never `git add -A` (the GH-124 sweep lesson). The
     promotion's own `git rm`/`git add` of the doc pair is already staged by promotion.
     Commits only on the integration branch: a retry-build dispatches from a lane branch,
     and a ledger commit there would ride into the lane PR and block later branch switches.
     Returns True when a commit was made."""
     integration = os.environ.get("MARATHON_INTEGRATION_BRANCH", "development")
     current = subprocess.run(["git", "-C", root, "symbolic-ref", "--quiet", "--short", "HEAD"],
                              capture_output=True, text=True)
     if current.returncode == 0 and current.stdout.strip() != integration:
         print(f"jog: supervisor-state commit skipped — on branch '{current.stdout.strip()}' "
               f"(not the integration branch '{integration}'); uncommitted ledger writes on a "
               f"lane are the containment-revert tradeoff (GH-292 F1)")
         return False
     paths = [p for p in ("releases.db", "releases.sql", "releases.gen",
                          "ROADMAP-DASHBOARD.md", "LEADERBOARD.html", "RELEASES-PREVIEW.html")
              if os.path.exists(os.path.join(root, p))]
     if paths:
         subprocess.run(["git", "-C", root, "add", "--"] + paths, capture_output=True)
     staged = subprocess.run(["git", "-C", root, "diff", "--cached", "--quiet"],
                             capture_output=True)
     if staged.returncode == 0:
         return False
     res = subprocess.run(
         ["git", "-C", root, "commit", "-q", "-m",
          f"jog-state: intake + lease for GH-{gh_num} (execution {exec_id}) — supervisor-owned "
          f"ledger, doc, and view writes committed before dispatch (GH-292 F1)"],
         capture_output=True, text=True)
     if res.returncode != 0:
         print(f"jog: warning: supervisor-state commit failed: {(res.stderr or '').strip()}",
@@ -1701,80 +1706,81 @@ def jog_run_main(args=None):
                 conn.close()
 
             if not row:
                 print("jog: queue complete (0 pending tasks).")
                 break
 
             gh_num = row["gh_number"]
             att = row["attempt_count"] + 1
 
             # Acquire lease via perform_write
             jog_acquire_lease(root, gh_num, os.getpid())
 
             print(f"\n{'=' * 60}")
             print(f"jog: processing GH-{gh_num} (attempt {att}) at position {row['position']}")
             print(f"{'=' * 60}")
 
             doc_path = find_issue_doc(root, gh_num)
             if doc_path and "/PROJECT/1-INBOX/" in doc_path:
                 print(f"jog: promoting 1-INBOX contract for GH-{gh_num} to 2-WORKING...")
                 promoted_path, err = promote_contract_to_working(
                     root, gh_num, doc_path, interactive=sys.stdin.isatty()
                 )
                 if err:
                     print(f"jog: contract promotion failed: {err}")
                     jog_set_status(root, gh_num, "parked", failure_reason=err)
                     continue
                 doc_path = promoted_path
 
             # GH-280 Phase 5: the DEFAULT Marathon executor — Jog leases the row, delegates
             # execution to the reviewed one-phase driver through the structured contracts, and
             # projects the receipt's outcome. No Tick seeding, relay rendering, branch choice,
             # gate, or PR discovery happens here; the legacy relay path below is reached only
             # via --executor relay or --simulate during the compatibility window.
             if executor == "marathon" and not simulate:
                 ledger_gid = jog_resolve_ledger_gid(root, gh_num) or row["global_id"]
                 action, reason = run_marathon_phase(
                     root, gh_num, ledger_gid,
                     builder=args.builder, reviewer=args.reviewer,
                     auto_merge=getattr(args, "auto_merge", False))
                 jog_set_status(root, gh_num, action, failure_reason=reason)
+                jog_regenerate_dashboard(root)
                 if action == "completed":
                     tasks_processed += 1
                     continue
                 if action == "failed":
                     print("jog: stopping queue execution on task failure.")
                 else:
                     print("jog: advancing halted at landing boundary.")
                 break
 
             # Swarm Preflight check
             preflight_py = os.path.join(root, "utils", "py", "swarm_preflight.py")
             if os.path.isfile(preflight_py) and not getattr(args, "simulate", False):
                 pf_res = subprocess.run(
                     # swarm_preflight.py has no --root flag (it resolves the repo from cwd,
                     # which this subprocess already pins below); passing one is a usage error
                     # that parked every queue item on the first real run.
                     [sys.executable, preflight_py, "--gh-issue", str(gh_num)],
                     cwd=root,
                     capture_output=True,
                     text=True,
                 )
                 if pf_res.returncode == 4:
                     print(f"jog: GH-{gh_num} preflight reported already-landed (auto-dropping).")
                     jog_set_status(root, gh_num, "completed", failure_reason="preflight: already-landed")
                     tasks_processed += 1
                     continue
                 elif pf_res.returncode != 0:
                     print(f"jog: GH-{gh_num} preflight failed (exit {pf_res.returncode}); parking item.")
                     jog_set_status(root, gh_num, "parked", failure_reason=f"preflight-refused (exit {pf_res.returncode})")
                     continue
 
             # Execute single-phase drive
             drive_rc = run_single_phase_drive(
                 root,
                 gh_num,
                 builder=args.builder,
                 reviewer=args.reviewer,
                 simulate=getattr(args, "simulate", False),
             )
 
diff --git a/utils/py/releases_app.py b/utils/py/releases_app.py
index c7d5ac65..41bcd9bf 100644
--- a/utils/py/releases_app.py
+++ b/utils/py/releases_app.py
@@ -3559,80 +3559,93 @@ def cmd_settings_set(args):
     conn = connect(artifact_paths(root)["db"])
     try:
         if args.key not in CONFIGURABLE_SETTINGS:
             refuse("setting-not-configurable",
                    "%s is not an operator-configurable setting; configurable keys are: %s"
                    % (args.key, ", ".join(sorted(CONFIGURABLE_SETTINGS))))
         old = get_setting(conn, args.key)
         if args.dry_run:
             print("%s: %s -> %s" % (args.key, old if old is not None else "(unset)", args.value))
             return
 
         def mutate(conn):
             if _has_column(conn, "settings", "updated_at"):
                 conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?) "
                              "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                              "updated_at = excluded.updated_at",
                              (args.key, args.value, now_iso()))
             else:
                 conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) "
                              "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                              (args.key, args.value))
 
         perform_write(root, conn, "settings-set", None, mutate)
         print("%s = %s" % (args.key, args.value))
     finally:
         conn.close()
 
 
 def cmd_settings_list(args):
     """Print every settings row, so "what is this ledger configured to do" is one command."""
     root = resolve_root(args.root)
     conn = connect(artifact_paths(root)["db"])
     try:
         for row in conn.execute("SELECT key, value FROM settings ORDER BY key"):
             mark = " (configurable)" if row["key"] in CONFIGURABLE_SETTINGS else ""
             print("%-28s %s%s" % (row["key"], row["value"], mark))
     finally:
         conn.close()
 
 
+def cmd_settings_get(args):
+    """Print one setting value."""
+    root = resolve_root(args.root)
+    conn = connect(artifact_paths(root)["db"])
+    try:
+        val = get_setting(conn, args.key, None)
+        if val is None:
+            sys.exit(1)
+        print(val)
+    finally:
+        conn.close()
+
+
 def validate_roadmap_section(section):
     """Refuse headings the dashboard cannot render; never silently rename input."""
     if section not in ROADMAP_SECTIONS:
         hint = (" 'Deferred / cancelled' is a legacy markdown heading; use 'Deferred · vision'."
                 if section == "Deferred / cancelled" else "")
         refuse("invalid-section", "unknown roadmap section %r.%s Valid sections: %s"
                % (section, hint, ", ".join(repr(s) for s in ROADMAP_SECTIONS)))
     return section
 
 
 def cmd_roadmap_sections(args):
     print(json.dumps(ROADMAP_SECTIONS, ensure_ascii=False) if args.as_json
           else "\n".join(ROADMAP_SECTIONS))
 
 
 def cmd_roadmap_update(args):
     """Update a parked row's explicit fields through the receipt-backed writer.
 
     GH-257 adds raw_text/section updates; GH-424 adds an explicit status marker.
     Marker-only updates preserve raw_text, ratings, section and doc_path.
     """
     marker = getattr(args, "status_marker", None)  # `move` shares this handler.
     if marker is not None and marker not in _ROADMAP_STATUS_MARKERS:
         refuse("invalid-status-marker", "--status-marker must be one of %s"
                % ", ".join(_ROADMAP_STATUS_MARKERS))
     if args.section is not None:
         validate_roadmap_section(args.section)
     # `roadmap move` delegates here with its OWN namespace, which has no --issue-url. Read it
     # defensively rather than adding the flag to a verb that has no business setting it.
     issue_url = getattr(args, "issue_url", None)
     root = resolve_root(args.root)
     paths = artifact_paths(root)
     conn = connect(paths["db"])
     try:
         if not _table_exists(conn, "roadmap_items"):
             refuse("no-ledger", "this DB has no roadmap_items table; run `releases migrate` first")
         if (args.issue_num is None) == (args.gid is None):
             refuse("selector", "pass exactly one of --issue-num or --gid")
         if args.issue_num is not None:
             where, param, label = "gh_number = ?", args.issue_num, "GH-%d" % args.issue_num
@@ -5503,80 +5516,82 @@ def build_parser():
     msub.add_parser("list")
 
     sp = sub.add_parser("list", help="list releases")
     sp.add_argument("--all-repos", action="store_true",
                     help="aggregate RELEASES_APP_EXTRA_DBS too; duplicate GIDs fail loudly")
     sp.add_argument("--status", choices=STATUSES)
 
     sp = sub.add_parser("show", help="full record for one release (by --gid or --version)")
     sp.add_argument("--gid")
     sp.add_argument("--version")
     sp.add_argument("--full", action="store_true",
                     help="print long values verbatim (default elides them at %d chars)"
                          % SHOW_ELIDE)
 
     sp = sub.add_parser("next", help="the next unshipped release, by target date")
     sp.add_argument("--verbose", action="store_true", help="also print its full record")
 
     sp = sub.add_parser("gen", help="side-by-side generation (Phase 0: NEVER writes RELEASES.md)")
     sp.add_argument("--side-by-side", action="store_true", default=True,
                     help="the only mode in Phase 0 (accepted for CLI-shape compatibility)")
 
     sp = sub.add_parser("check",
                         help="DB<->dump<->generated consistency; FK pragma; stale WAL; "
                              "receipt-vs-change bypass detection; temp-ref staleness; "
                              "duplication warnings; per-boundary crash recovery")
     sp.add_argument("--rebuild", action="store_true",
                     help="rebuild the DB from the dump (git-merge resolution ONLY)")
 
     sp = sub.add_parser("reconcile", help="fill real URLs into temp refs")
     sp.add_argument("--map", action="append", metavar="TMP-X=URL",
                     help="placeholder -> real issue URL (repeatable)")
 
     sp = sub.add_parser("dashboard", help="render the releases and roadmap dashboard HTML")
 
     # GH-525: a ledger with configurable behaviour needs a configuring verb. A settings row is part
     # of the business-state digest, so writing one by hand breaks the receipt chain and `check`
     # fails — this is the only supported way to set one.
     sp_set = sub.add_parser("settings", help="read/write operator-configurable ledger settings")
     ssub = sp_set.add_subparsers(dest="settings_cmd", required=True)
     sp_sl = ssub.add_parser("list", help="print every settings row")
+    sp_sg = ssub.add_parser("get", help="print one setting value")
+    sp_sg.add_argument("key", help="setting key name")
     sp_ss = ssub.add_parser("set", help="write one operator-configurable setting (receipted)")
     sp_ss.add_argument("key", help="setting key; only configurable keys are accepted")
     sp_ss.add_argument("value", help="new value")
     sp_ss.add_argument("--dry-run", action="store_true", help="print the change, write nothing")
 
     sp = sub.add_parser("roadmap", help="Roadmap ledger: sync/list/render the ledger items")
     rsub = sp.add_subparsers(dest="roadmap_cmd", required=True)
     sp_sections = rsub.add_parser("sections", help="list accepted roadmap section names (no DB required)")
     sp_sections.add_argument("--json", dest="as_json", action="store_true",
                              help="emit the dashboard's section vocabulary as a JSON array")
     sp_rs = rsub.add_parser("sync", help="mirror legacy ROADMAP.md's ledger into roadmap_items (one-way)")
     sp_rs.add_argument("--dry-run", action="store_true", help="report the diff, write nothing")
     sp_rs.add_argument("--allow-empty", action="store_true",
                        help="permit clearing roadmap_items when the ledger is genuinely empty. "
                             "Without it a 0-entry parse REFUSES (rule=roadmap-empty-parse) so "
                             "format drift can never silently delete the mirror; this flag never "
                             "excuses a ledger that still has content")
     sp_rs = rsub.add_parser("reconcile-state", help="reconcile nonterminal rows against GitHub issue state")
     rs_mode = sp_rs.add_mutually_exclusive_group()
     rs_mode.add_argument("--dry-run", action="store_true", help="preview only (the default)")
     rs_mode.add_argument("--apply", action="store_true", help="apply verified changes in one transaction")
     sp_rl = rsub.add_parser("list", help="print the shadow rows")
     sp_rl.add_argument("--json", dest="as_json", action="store_true",
                        help="emit rows as a JSON array (machine-readable; the default rendering "
                             "is a display, not an API)")
     sp_render = rsub.add_parser("render", help="replay DB rows as ledger markdown (stdout by default)")
     sp_render.add_argument("--out", help="output file (relative to cwd); refuses tracked ROADMAP.md")
 
     sp_ra = rsub.add_parser("add", help="intake a single issue into the roadmap ledger directly")
     sp_ra.add_argument("--issue-num", required=True, type=int, help="GH issue number")
     sp_ra.add_argument("--issue-url", required=True, help="GH issue URL")
     sp_ra.add_argument("--title", required=True, help="Issue title")
     sp_ra.add_argument("--created", required=True, help="Created date YYYY-MM-DD")
     sp_ra.add_argument("--doc-path", required=True, help="Capture doc relpath")
     sp_ra.add_argument("--raw-text", default=None,
                        help="pre-rendered ROADMAP line (hq park passes hq_roadmap_line output so "
                             "preview and stored row share one template). GH-249: a `rated "
                             "N/N/N/N [ovr N]` token in this line is parsed and stored — in a "
                             "releases-mode repo this is the ONLY way to score an entry, since "
                             "`roadmap sync` is a no-op there")
@@ -5697,56 +5712,57 @@ def build_parser():
     sp_jrun.add_argument("--builder", default="agy", help="builder turn-taker (default: agy; or codex, aider)")
     sp_jrun.add_argument("--reviewer", default=None,
                          help="reviewer agent — REQUIRED with --executor marathon, the default "
                               "executor (GH-280 Phase 5); no default is selected")
     sp_jrun.add_argument("--executor", choices=["relay", "marathon"], default="marathon",
                          help="per-task executor (GH-280 Phase 5): 'marathon' is the default — the "
                               "reviewed one-phase driver via the structured contracts, requires "
                               "--reviewer; 'relay' is the legacy rollback path kept for a "
                               "documented compatibility window")
     sp_jrun.add_argument("--max-tasks", type=int, default=None, help="maximum tasks to process in this run")
     sp_jrun.add_argument("--simulate", action="store_true", help="simulate drive execution in test environments")
     sp_jrun.add_argument("--dry-run", action="store_true", help="simulate queue run without mutations")
 
     return p
 
 
 def main(argv=None):
     args = build_parser().parse_args(argv)
     handlers = {
         "init": cmd_init, "import": cmd_import, "add": cmd_add, "update": cmd_update,
         "ship": cmd_ship, "migrate": cmd_migrate, "baseline": cmd_baseline,
         "manifest": lambda a: cmd_manifest_add(a) if a.manifest_cmd in ("dial-in", "add")
         else (cmd_manifest_ship(a) if a.manifest_cmd == "ship"
               else (cmd_manifest_marathon(a) if a.manifest_cmd == "marathon"
     else (cmd_manifest_unship(a) if a.manifest_cmd == "unship"
                     else cmd_manifest_cut(a)))),
         "marathon": lambda a: cmd_marathon_add(a) if a.marathon_cmd == "add"
         else cmd_marathon_list(a),
         "list": cmd_list, "show": cmd_show, "next": cmd_next, "gen": cmd_gen,
         "check": cmd_check, "reconcile": cmd_reconcile,
         "project": lambda a: cmd_project_sync(a) if a.project_cmd == "sync" else None,
         # A lookup, not a ternary chain: `rate` (GH-253) was the fourth branch, and the nested
         # form was already one subcommand past readable.
         "roadmap": lambda a: {"add": cmd_roadmap_add, "sync": cmd_roadmap_sync,
                               "rate": cmd_roadmap_rate, "list": cmd_roadmap_list,
                               "render": cmd_roadmap_render,
                               "repoint": cmd_roadmap_repoint, "update": cmd_roadmap_update,
                               "move": cmd_roadmap_move, "sections": cmd_roadmap_sections,
                               "reconcile-state": cmd_roadmap_reconcile_state}[a.roadmap_cmd](a),
         "settings": lambda a: {"set": cmd_settings_set,
-                               "list": cmd_settings_list}[a.settings_cmd](a),
+                               "list": cmd_settings_list,
+                               "get": cmd_settings_get}[a.settings_cmd](a),
         "dashboard": cmd_dashboard,
         "jog": lambda a: {"add": cmd_jog_add, "list": cmd_jog_list,
                           "bump": cmd_jog_bump, "drop": cmd_jog_drop,
                           "retry": cmd_jog_retry, "skip": cmd_jog_skip,
                           "clear": cmd_jog_clear, "to-marathon": cmd_jog_to_marathon,
                           "run": cmd_jog_run, "resume": cmd_jog_resume,
                           "retry-gate": cmd_jog_retry_gate, "retry-build": cmd_jog_retry_build,
                           "land": cmd_jog_land, "reconcile": cmd_jog_land}[a.jog_cmd](a),
     }
     handlers[args.cmd](args)
 
 
 
 if __name__ == "__main__":
     main()
diff --git a/utils/py/wave_reconcile.py b/utils/py/wave_reconcile.py
index 1ca06195..fb73a45c 100755
--- a/utils/py/wave_reconcile.py
+++ b/utils/py/wave_reconcile.py
@@ -1,113 +1,184 @@
 #!/usr/bin/env python3
 """wave_reconcile.py (GH-165) — Post-Merge Wave & Marathon Lifecycle Reconciler.
 
 The canonical, single-command Python reconciler to automate post-merge lifecycle
 transitions across Active Docs (PROJECT/2-WORKING/ -> 3-COMPLETED/ or 4-MISC/),
 ROADMAP.md, releases.db SQLite ledger, generated dashboards, and next-wave marathon planning.
 """
 
 import argparse
 import fcntl
 import glob
+import hashlib
 import json
 import os
 import re
 import shutil
 import sqlite3
 import subprocess
 import sys
 import tempfile
 from datetime import datetime
 from pathlib import Path
 
 sys.dont_write_bytecode = True
 from harness_paths import github_slug_from_origin, harness_home, harness_tool, is_vendored, repo_root, resolve_tool
 
 
 class ReconcileError(Exception):
     """Custom exception class ensuring proper rollback catching."""
 
     def __init__(self, message, code=2):
         super().__init__(message)
         self.code = code
 
 
 def log(msg):
     print(f"wave-reconcile: {msg}", flush=True)
 
 
 def log_err(msg):
     print(f"wave-reconcile: ERROR — {msg}", file=sys.stderr, flush=True)
 
 
 def die(msg, code=2):
     log_err(msg)
     raise ReconcileError(msg, code=code)
 
 
 class ReconcilerLock:
     """Lock manager preventing concurrent reconciliation runs."""
 
     def __init__(self, lock_path):
         self.lock_path = lock_path
         self.fd = None
 
     def __enter__(self):
         try:
             self.fd = open(self.lock_path, "w")
             fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
             self.fd.write(f"pid={os.getpid()}\ntime={datetime.now().isoformat()}\n")
             self.fd.flush()
             return self
         except (BlockingIOError, OSError) as e:
             die(f"Could not acquire reconciler lock at {self.lock_path}: {e}", code=8)
 
     def __exit__(self, exc_type, exc_val, exc_tb):
         if self.fd:
             try:
                 fcntl.flock(self.fd, fcntl.LOCK_UN)
                 self.fd.close()
             except OSError:
                 pass
 
 
+def check_hosted_reconciler_in_flight(repo_root, repo_slug=None, force=False):
+    """Refuse local reconciliation if hosted wave-reconcile.yml is running/queued (GH-496)."""
+    cmd = [
+        "gh", "run", "list",
+        "--workflow", "wave-reconcile.yml",
+        "--json", "databaseId,status,conclusion,createdAt,headSha,event",
+        "--limit", "10",
+    ]
+    if repo_slug:
+        cmd.extend(["--repo", repo_slug])
+
+    try:
+        res = subprocess.run(
+            cmd,
+            cwd=repo_root,
+            capture_output=True,
+            text=True,
+            timeout=15,
+        )
+    except FileNotFoundError:
+        if force:
+            log("  WARNING: 'gh' CLI not found; bypassing hosted in-flight check via --force-local-reconcile")
+            return
+        die("Hosted reconciler check failed: 'gh' command not found. Pass --force-local-reconcile to bypass.", code=8)
+    except subprocess.TimeoutExpired:
+        if force:
+            log("  WARNING: 'gh run list' timed out; bypassing hosted in-flight check via --force-local-reconcile")
+            return
+        die("Hosted reconciler check failed: 'gh run list' timed out. Pass --force-local-reconcile to bypass.", code=8)
+    except Exception as e:
+        if force:
+            log(f"  WARNING: gh run list failed ({e}); bypassing hosted in-flight check via --force-local-reconcile")
+            return
+        die(f"Hosted reconciler check failed: {e}. Pass --force-local-reconcile to bypass.", code=8)
+
+    if res.returncode != 0:
+        if force:
+            log(f"  WARNING: gh run list exited {res.returncode}; bypassing hosted in-flight check via --force-local-reconcile")
+            return
+        err = res.stderr.strip() or "unknown error"
+        die(f"Hosted reconciler check failed: unable to query GitHub Actions ({err}). Pass --force-local-reconcile to bypass.", code=8)
+
+    stdout = res.stdout.strip()
+    if not stdout:
+        runs = []
+    else:
+        try:
+            runs = json.loads(stdout)
+        except ValueError:
+            if force:
+                return
+            die("Hosted reconciler check failed: malformed JSON from gh run list. Pass --force-local-reconcile to bypass.", code=8)
+
+    in_flight = [
+        r for r in runs
+        if r.get("status") in ("queued", "in_progress", "waiting", "requested")
+    ]
+    if in_flight:
+        run_ids = ", ".join(f"#{r.get('databaseId')} ({r.get('status')})" for r in in_flight)
+        if force:
+            log(f"  WARNING: Overriding active hosted reconciliation run(s): {run_ids} via --force-local-reconcile")
+            return
+        die(
+            f"Hosted reconciliation workflow (wave-reconcile.yml) is currently in-flight: {run_ids}. "
+            "Refusing local reconciliation to prevent concurrent landing collisions. "
+            "Wait for hosted workflow to complete, or pass --force-local-reconcile to override.",
+            code=8,
+        )
+
+
 class RollbackJournal:
     """Snapshots pre-mutation file states and rolls back on failure."""
 
     def __init__(self):
         self.backups = {}  # original_path -> backup_temp_path
         self.created_files = set()
         self.deleted_files = set()
 
     def snapshot(self, path):
         p = os.path.abspath(path)
         if p not in self.backups and os.path.exists(p):
             tmp = tempfile.NamedTemporaryFile(delete=False)
             tmp.close()
             shutil.copy2(p, tmp.name)
             self.backups[p] = tmp.name
 
     def track_created(self, path):
         self.created_files.add(os.path.abspath(path))
 
     def rollback(self):
         log("Rolling back all uncommitted mutations...")
         for created in self.created_files:
             if os.path.exists(created):
                 try:
                     os.unlink(created)
                 except OSError:
                     pass
         for orig, backup in self.backups.items():
             try:
                 os.makedirs(os.path.dirname(orig), exist_ok=True)
                 shutil.copy2(backup, orig)
             except OSError as e:
                 log_err(f"Failed restoring {orig} from {backup}: {e}")
         self.cleanup()
 
     def changed(self):
         """Whether any journaled artifact differs, ignoring empty directories."""
         return any(os.path.exists(p) for p in self.created_files) or any(
             not os.path.exists(p) or Path(p).read_bytes() != Path(backup).read_bytes()
             for p, backup in self.backups.items()
@@ -362,80 +433,162 @@ def check_provenance_receipts(repo_root, pr_meta):
 
     expected_pr = pr_number(pr_num)
     merge_commit = pr_meta.get("mergeCommit") or {}
     merge_sha = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
     if not isinstance(merge_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", merge_sha):
         merge_sha = None
     for root, dirs, files in os.walk(results_dir):
         dirs.sort()
         for name in sorted(files):
             if name not in ("error_log.jsonl", "provenance.jsonl"):
                 continue
             path = os.path.join(root, name)
             if os.path.islink(path) or not os.path.isfile(path):
                 continue
             try:
                 with open(path, encoding="utf-8") as receipt:
                     for line_num, line in enumerate(receipt, 1):
                         try:
                             entry = json.loads(line)
                         except ValueError:
                             continue
                         if not isinstance(entry, dict):
                             continue
                         pr_fields = [key for key in ("pr", "pr_number") if key in entry]
                         matched = None
                         if pr_fields:
                             if expected_pr and all(pr_number(entry[key]) == expected_pr for key in pr_fields):
                                 matched = f"{pr_fields[0]}={expected_pr}"
                         elif merge_sha and entry.get("commit") == merge_sha:
                             matched = f"commit={merge_sha}"
                         if matched:
                             relpath = os.path.relpath(path, repo_root)
                             log(f"  Provenance receipt matched for PR #{pr_num}: {relpath}:{line_num} ({matched})")
                             return
             except (OSError, UnicodeError):
                 continue  # An unreadable receipt cannot establish attribution.
     die(f"--gate failure: No provenance.jsonl or error_log.jsonl entry matches PR #{pr_num} "
         "by pr/pr_number or exact merge commit in TESTS-RESULTS/", code=6)
 
 
+def validate_pre_merge_receipts(repo_root, head_sha, pr_num=None):
+    """Ensure a passing test receipt matching HEAD SHA or PR number is COMMITTED in Git tree (GH-496)."""
+    try:
+        tree_files = subprocess.check_output(
+            ["git", "ls-tree", "-r", "--name-only", "HEAD", "TESTS-RESULTS/"],
+            cwd=repo_root,
+            text=True,
+            stderr=subprocess.DEVNULL,
+        ).splitlines()
+    except Exception:
+        tree_files = []
+
+    matching_receipts = [
+        f for f in tree_files
+        if f.endswith("provenance.jsonl") or f.endswith("error_log.jsonl")
+    ]
+    if not matching_receipts:
+        return f"No committed provenance.jsonl or error_log.jsonl receipts found under TESTS-RESULTS/ at HEAD {head_sha[:10]}."
+
+    try:
+        recent_shas = subprocess.check_output(
+            ["git", "log", "-n", "10", "--format=%H", "HEAD"],
+            cwd=repo_root,
+            text=True,
+            stderr=subprocess.DEVNULL,
+        ).splitlines()
+    except Exception:
+        recent_shas = [head_sha]
+    recent_shas_lower = set(s.lower() for s in recent_shas)
+
+    found_match = False
+    expected_pr = str(pr_num) if pr_num else None
+    for receipt_rel in matching_receipts:
+        try:
+            content = subprocess.check_output(
+                ["git", "show", f"HEAD:{receipt_rel}"],
+                cwd=repo_root,
+                text=True,
+                stderr=subprocess.DEVNULL,
+            )
+            for line in content.splitlines():
+                if not line.strip():
+                    continue
+                try:
+                    entry = json.loads(line)
+                except ValueError:
+                    continue
+                if not isinstance(entry, dict):
+                    continue
+                c_val = str(entry.get("commit") or "").lower()
+                c_len = len(c_val)
+                commit_match = bool(
+                    c_val
+                    and (
+                        (c_len >= 7 and head_sha.lower().startswith(c_val))
+                        or c_val == head_sha.lower()
+                        or (c_len >= 7 and any(s.startswith(c_val) for s in recent_shas_lower))
+                        or any(s == c_val for s in recent_shas_lower)
+                    )
+                )
+                pr_match = False
+                if expected_pr:
+                    pr_val = str(entry.get("pr") or entry.get("pr_number") or "")
+                    if pr_val == expected_pr:
+                        pr_match = True
+                if commit_match or pr_match:
+                    res = entry.get("result") or entry.get("status")
+                    rc = entry.get("rc")
+                    if res in ("pass", "passed", "PASS") or rc == 0:
+                        found_match = True
+                        break
+            if found_match:
+                break
+        except Exception:
+            continue
+
+    if not found_match:
+        target = f"PR #{pr_num}" if pr_num else f"commit {head_sha[:10]}"
+        return f"No committed passing test receipt at HEAD matches {target} in TESTS-RESULTS/ (AGENTS.md: uncommitted provenance is not proof)."
+    return None
+
+
 # GH-271: closing-keyword clause + trailing title tag decide LINKAGE (what a merged PR may
 # complete); bare mentions are references only. The #-or-GH- prefix is mandatory in both —
 # "closes 5 issues" must not extract issue 5 — and keywords must sit on the same line as the
 # ref, so a title ending in "fixed" cannot capture a body that opens with "#123".
 CLOSING_KEYWORD_CLAUSE = re.compile(
     r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
     r"((?:#|GH-)[0-9]{1,6}\b"
     r"(?:(?:[ \t]*,[ \t]*(?:and[ \t]+)?|[ \t]+and[ \t]+)(?:#|GH-)[0-9]{1,6}\b)*)",
     re.IGNORECASE,
 )
 REF_IN_CLAUSE = re.compile(r"(?:#|GH-)([0-9]{1,6})\b", re.IGNORECASE)
 # GH-429: GitHub also honours a closing keyword followed by the issue's full URL. Captured as
 # (slug, number); extract_linked_issues keeps only the target repo's own slug, because
 # fetch_issue_state and find_active_doc_for_issue key on the bare number and a foreign repo's
 # "Closes https://github.com/other/repo/issues/7" must not promote this repo's GH-7.
 CLOSING_KEYWORD_URL = re.compile(
     r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
     r"https?://github\.com/([\w.\-]+/[\w.\-]+?)/issues/([0-9]{1,6})\b",
     re.IGNORECASE,
 )
 # A `#N`/`GH-N` inside a URL (fragment `/#123`, path `/GH-123`, query `?#123`, `?issue=#123`,
 # `&#123`) is part of the link, not a reference — GH-271 QA rounds 1+3. The lookbehind is one
 # fixed-width character class.
 MENTION = re.compile(r"(?<![A-Za-z0-9_/?.=&])(?:[Gg][Hh]-|#)([0-9]{1,6})\b")
 TITLE_TRAILER = re.compile(
     r"\([ \t]*((?:(?:#|GH-)[0-9]{1,6}\b[ \t]*(?:[,;][ \t]*)?)+)[ \t]*\)[ \t]*$",
     re.IGNORECASE,
 )
 CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
 INLINE_CODE = re.compile(r"`[^`\n]*`")
 
 
 def _strip_code_blocks(text):
     """GitHub ignores closing keywords inside code; so does the reconciler."""
     return INLINE_CODE.sub(" ", CODE_FENCE.sub(" ", text))
 
 
 def extract_linked_issues(pr_meta, repo_slug=None):
     """Split a PR's issue references into (closers, mentions) — GH-271.
 
@@ -471,103 +624,177 @@ def extract_linked_issues(pr_meta, repo_slug=None):
     mentions.update(int(n) for n in MENTION.findall(scan_text))
     mentions -= closers
     return sorted(closers), sorted(mentions)
 
 
 def find_active_doc_for_issue(repo_root, issue_num):
     """Find matching active doc in PROJECT/2-WORKING/."""
     working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
     if not os.path.isdir(working_dir):
         return None
     for fname in os.listdir(working_dir):
         if not fname.endswith(".md"):
             continue
         # Match GH-123-*.md or 123-*.md
         if re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
             return os.path.join(working_dir, fname)
     return None
 
 
 def parse_doc_frontmatter(doc_path):
     """Parse key-value pairs from document YAML frontmatter."""
     if not doc_path or not os.path.isfile(doc_path):
         return {}
     try:
         with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
             lines = f.readlines()
         if not lines or lines[0].strip() != "---":
             return {}
         fm = {}
         for line in lines[1:]:
             if line.strip() == "---":
                 break
             if ":" in line:
                 k, v = line.split(":", 1)
                 fm[k.strip().lower()] = v.strip().strip("'\"").lower()
         return fm
     except Exception:
         return {}
 
 
+def validate_lessons_learned(content, doc_name):
+    """Assert ## Lessons Learned section exists and contains substantive content (GH-496)."""
+    m = re.search(r"##\s+Lessons\s+Learned.*?(?=\n##\s+(?!#)|\Z)", content, re.IGNORECASE | re.DOTALL)
+    if not m:
+        return f"Doc {doc_name} is missing mandatory '## Lessons Learned (For Future Agents)' section."
+
+    section_text = m.group(0)
+    lines = section_text.splitlines()
+    body_lines = lines[1:]
+
+    # Strip HTML comments
+    clean_body = re.sub(r"<!--.*?-->", "", "\n".join(body_lines), flags=re.DOTALL)
+
+    substantive_lines = []
+    for line in clean_body.splitlines():
+        trimmed = line.strip()
+        if not trimmed:
+            continue
+        # Check for empty placeholder markers
+        if re.match(r"^(?:[-*]\s*)?(?:TODO\b.*|TBD\b.*|None(?:\s+yet)?|N/A|\[.*?\]|\[?\s*\]?)$", trimmed, re.IGNORECASE):
+            continue
+        substantive_lines.append(trimmed)
+
+    if not substantive_lines:
+        return f"Doc {doc_name} has empty/placeholder '## Lessons Learned' section. Substantive reflections are required before closeout."
+    return None
+
+
+def validate_frontmatter_schema(doc_path):
+    """Validate YAML frontmatter against required PDDA schema (GH-496)."""
+    doc_name = os.path.basename(doc_path)
+    if not os.path.isfile(doc_path):
+        return f"Doc {doc_name} does not exist."
+    try:
+        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
+            content = f.read()
+    except Exception as e:
+        return f"Cannot read {doc_name}: {e}"
+
+    lines = content.splitlines()
+    if not lines or lines[0].strip() != "---":
+        return f"Doc {doc_name} missing opening YAML frontmatter delimiter ('---') at line 1."
+
+    closing_idx = -1
+    for i, line in enumerate(lines[1:], 1):
+        if line.strip() == "---":
+            closing_idx = i
+            break
+
+    if closing_idx == -1:
+        return f"Doc {doc_name} missing closing YAML frontmatter delimiter ('---')."
+
+    fm = {}
+    for line in lines[1:closing_idx]:
+        line = line.strip()
+        if not line or line.startswith("#"):
+            continue
+        if ":" in line:
+            k, v = line.split(":", 1)
+            fm[k.strip().lower()] = v.strip().strip("'\"")
+
+    required_keys = ["title", "status", "created", "updated", "owner", "goal"]
+    missing = [k for k in required_keys if not fm.get(k)]
+    if missing:
+        return f"Doc {doc_name} frontmatter missing required field(s): {', '.join(missing)}"
+
+    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
+    for date_key in ("created", "updated"):
+        val = fm.get(date_key, "")
+        val_date = val.split()[0] if val else ""
+        if not date_re.match(val_date):
+            return f"Doc {doc_name} frontmatter field '{date_key}' has invalid date format: '{val}' (expected YYYY-MM-DD)."
+
+    return None
+
+
 def validate_and_update_doc(doc_path, pr_meta, is_merged=True, dry_run=False, journal=None):
     """Assert ## Lessons Learned, update frontmatter, and compute destination path."""
     with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
         content = f.read()
 
     merged_at = pr_meta.get("mergedAt")
     if merged_at:
         try:
             ship_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00")).strftime(
                 "%Y-%m-%d"
             )
         except Exception:
             ship_date = datetime.now().strftime("%Y-%m-%d")
     else:
         ship_date = datetime.now().strftime("%Y-%m-%d")
 
     if is_merged:
-        # Assert lessons learned section exists for merged docs
-        if not re.search(r"##\s+Lessons\s+Learned", content, re.IGNORECASE):
-            die(
-                f"Doc {os.path.basename(doc_path)} is missing mandatory '## Lessons Learned (For Future Agents)' section.",
-                code=5,
-            )
+        # Assert lessons learned section exists and has substantive content for merged docs (GH-496)
+        ll_err = validate_lessons_learned(content, os.path.basename(doc_path))
+        if ll_err:
+            die(ll_err, code=5)
 
         new_status = "Complete"
         dest_folder = "3-COMPLETED"
     else:
         # Unmerged / declined / closed without merge -> route to 4-MISC
         new_status = "Declined"
         dest_folder = "4-MISC"
 
     # Update frontmatter status and updated date
     new_content = re.sub(
         r"^status:\s*.*$", f"status: {new_status}", content, flags=re.MULTILINE | re.IGNORECASE
     )
     new_content = re.sub(
         r"^updated:\s*.*$", f"updated: {ship_date}", new_content, flags=re.MULTILINE | re.IGNORECASE
     )
 
     dest_dir = os.path.join(os.path.dirname(os.path.dirname(doc_path)), dest_folder)
     dest_path = os.path.join(dest_dir, os.path.basename(doc_path))
     print("TRANSITION " + json.dumps(["doc", "move", os.path.basename(doc_path), dest_folder, ship_date]), flush=True)
 
     if not dry_run:
         if journal:
             journal.snapshot(doc_path)
             # GH-271: a destination that already exists (an earlier reconciliation promoted
             # this doc and was committed) is an overwrite, not a creation — snapshot it too,
             # or rollback's unlink leaves a tracked path deleted in porcelain.
             if os.path.exists(dest_path):
                 journal.snapshot(dest_path)
             journal.track_created(dest_path)
         os.makedirs(dest_dir, exist_ok=True)
         with open(dest_path, "w", encoding="utf-8") as f:
             f.write(new_content)
         os.unlink(doc_path)
 
     return dest_path, ship_date
 
 def ledger_rows(repo_root, sql, params=()):
     """Read the existing ledger without creating a DB or silently hiding schema errors."""
     db = Path(repo_root) / "releases.db"
     if not db.is_file():
@@ -877,276 +1104,480 @@ def handle_marathon_plan_result(result, reconciled_issues):
         # Preserve GH-202 compatibility with older/stub planners that expose only
         # the exit-5 contract. Exit 4 must remain attributable and therefore
         # fails closed when structured evidence is absent.
         if result.returncode == 5:
             log("  marathon-plan reports items held (exit 5) without structured findings — continuing (GH-202 compatibility)")
             return
         die("marathon-plan reported drift (exit 4) without attributable structured findings", code=6)
 
     reconciled = {int(issue) for issue in reconciled_issues}
     owned = [
         finding for finding in findings
         if finding_issue_numbers(finding) & reconciled
     ]
     unrelated = [finding for finding in findings if finding not in owned]
 
     if owned:
         labels = ", ".join(describe_finding(finding) for finding in owned)
         die(
             "marathon-plan found drift/held state attributable to the reconciled "
             f"PR item(s): {labels}",
             code=6,
         )
 
     log("  WARNING — marathon-plan found pre-existing unrelated drift/held items; keeping reconciliation:")
     for finding in unrelated:
         log(f"    - {describe_finding(finding)}")
 
 
 def snapshot_ledger_artifacts(repo_root, dry_run=False, journal=None):
     """GH-424: capture the ledger and generated views BEFORE the first write.
 
     Repeated calls retain the original state, including originally absent artifacts.
     Both per-issue writes and downstream regeneration use this same snapshot set.
     """
     if dry_run or journal is None:
         return
     for name in (
         "releases.db", "releases.sql", "RELEASES.generated.md",
         "ROADMAP-DASHBOARD.md", "RELEASES-PREVIEW.html",
         "LEADERBOARD.html", "LEADERBOARD.md",
+        os.path.join(".tick", "marathon-plan.fingerprint"),
     ):
         path = os.path.abspath(os.path.join(repo_root, name))
         if path in journal.backups or path in journal.created_files:
             continue
         if os.path.exists(path):
             journal.snapshot(path)
         else:
             journal.track_created(path)
 
 
+def compute_marathon_planner_fingerprint(repo_root):
+    """Compute a SHA256 digest of canonical marathon inputs to avoid redundant replanning (GH-496)."""
+    h = hashlib.sha256()
+    db_path = os.path.join(repo_root, "releases.db")
+    if os.path.isfile(db_path):
+        try:
+            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
+            cur = conn.cursor()
+            cur.execute("SELECT global_id, gh_number, title, section, position, complexity, risk, effort FROM roadmap_items ORDER BY global_id")
+            for row in cur.fetchall():
+                h.update(str(row).encode("utf-8"))
+            conn.close()
+        except Exception:
+            pass
+
+    working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
+    if os.path.isdir(working_dir):
+        for fname in sorted(os.listdir(working_dir)):
+            if fname.endswith(".md") and not fname.startswith("MARATHON-PLAN-"):
+                h.update(fname.encode("utf-8"))
+
+    planner_src = harness_tool(repo_root, "utils/py/marathon_plan.py")
+    if os.path.isfile(planner_src):
+        try:
+            with open(planner_src, "rb") as f:
+                h.update(f.read())
+        except Exception:
+            pass
+    return h.hexdigest()
+
+
 def run_subprocesses(repo_root, dry_run=False, journal=None, reconciled_issues=None):
     """Orchestrate releases sync, view exports, and marathon replanning with DB rollback protection."""
     log("Running downstream database sync and dashboard regeneration...")
 
     snapshot_ledger_artifacts(repo_root, dry_run=dry_run, journal=journal)
 
     def _plan_docs():
         found = set()
         for pattern in ("MARATHON-PLAN-*.md", os.path.join("PROJECT", "2-WORKING", "MARATHON-PLAN-*.md")):
             found.update(glob.glob(os.path.join(repo_root, pattern)))
         return found
 
     pre_plan_docs = _plan_docs() if not dry_run else set()
     if journal and not dry_run:
         # Codex consult: a same-dated plan doc that already exists gets OVERWRITTEN by the
         # replan, and tracking-only-created would leave rollback no bytes to restore.
         for existing_doc in pre_plan_docs:
             journal.snapshot(existing_doc)
 
     # GH-358: resolve each harness tool against the repo first, then the harness home. On a
     # vendored install these five live only under <repo>/.xyz/ and every one was unreachable,
     # so the reconciler died on its first downstream step.
     releases_app = harness_tool(repo_root, "utils/py/releases_app.py")
     sync_cmd = ["python3", releases_app, "--root", repo_root, "roadmap", "sync"]
     check_cmd = ["python3", releases_app, "--root", repo_root, "check"]
     timeline_cmd = ["python3", harness_tool(repo_root, "utils/timeline/export_timeline.py"), "--preview"]
     dash_cmd = ["bash", harness_tool(repo_root, "utils/roadmap-dashboard.sh")]
+    lb_cmd = ["bash", harness_tool(repo_root, "utils/leaderboard.sh")]
     plan_cmd = ["bash", harness_tool(repo_root, "utils/marathon-plan.sh"), "--format", "json"]
 
     if dry_run:
         sync_cmd.append("--dry-run")
         plan_cmd.append("--dry-run")
 
     steps = [
         ("releases roadmap sync", sync_cmd),
         ("releases check", check_cmd),
     ]
+    skip_marathon = False
+    fp_dir = os.path.join(repo_root, ".tick")
+    fp_file = os.path.join(fp_dir, "marathon-plan.fingerprint")
+    plan_fp = compute_marathon_planner_fingerprint(repo_root)
+
     if not dry_run:
-        # GH-474: RELEASES-PREVIEW.html is an ADOPTED view — opt-in by presence. Every other
-        # consumer already treats it that way: releases_app.refresh_preview() skips it when
-        # absent (utils/py/releases_app.py:1170-1201), the merge resolver regenerates only what
-        # is already there (utils/releases-merge-resolve.sh:160-172), express.py snapshots it
-        # under os.path.lexists (utils/py/express.py:202-207) and jog_run.py stages it the same
-        # way. This step was the ONE consumer that regenerated it unconditionally, so a repo
-        # that had deliberately un-adopted the view got it silently recreated on the next
-        # reconcile — the deletion would not stick.
-        #
-        # ROADMAP-DASHBOARD.md stays unconditional on purpose, and the asymmetry is the point:
-        # it is NOT adopted-by-presence. It is required — githooks/dashboard-staleness-guard.sh
-        # refuses a push without it and utils/py/router_audit.py gates ROUTER.md's declaration
-        # of it. Regenerating a required view is correct; resurrecting an un-adopted one is not.
+        # GH-474: RELEASES-PREVIEW.html is an ADOPTED view — opt-in by presence.
         if os.path.exists(os.path.join(repo_root, "RELEASES-PREVIEW.html")):
             steps.append(("export_timeline.py --preview", timeline_cmd))
         else:
             log("  (skipping export_timeline.py --preview — RELEASES-PREVIEW.html is not adopted here)")
-        steps.extend(
-            [
-                ("roadmap-dashboard.sh", dash_cmd),
-                ("marathon-plan.sh", plan_cmd),
-            ]
-        )
+        steps.append(("roadmap-dashboard.sh", dash_cmd))
+        if os.path.exists(os.path.join(repo_root, "LEADERBOARD.md")):
+            if os.path.exists(harness_tool(repo_root, "utils/leaderboard.sh")):
+                steps.append(("leaderboard.sh", lb_cmd))
+            else:
+                log("  (skipping leaderboard.sh — utils/leaderboard.sh not found)")
+        else:
+            log("  (skipping leaderboard.sh — LEADERBOARD.md is not adopted here)")
+
+        has_plan = bool(glob.glob(os.path.join(repo_root, "PROJECT", "2-WORKING", "MARATHON-PLAN-*.md"))) or bool(glob.glob(os.path.join(repo_root, "MARATHON-PLAN-*.md")))
+        if has_plan and os.path.isfile(fp_file):
+            try:
+                with open(fp_file, "r") as f:
+                    if f.read().strip() == plan_fp:
+                        skip_marathon = True
+            except Exception:
+                pass
+
+        if skip_marathon:
+            log("  (skipping marathon-plan.sh — canonical inputs unchanged)")
+        else:
+            steps.append(("marathon-plan.sh", plan_cmd))
     else:
         steps.append(("marathon-plan.sh --dry-run", plan_cmd))
 
     # GH-271: registration of created views/plan docs must happen even when a step DIES —
     # the marathon-plan failure path raises from inside the loop, and a post-loop pass
     # would never run, which is exactly how the stray MARATHON-PLAN escaped rollback.
     try:
         for name, cmd in steps:
             log(f"  -> {name}")
-            # GH-429: roadmap-dashboard.sh derives ROOT from its own location and lands on <repo>/.xyz
-            # when vendored (#215 item 2); it honours this override, and the reconciler already knows
-            # the repo root. Harmless for the other steps, which ignore the variable.
-            step_env = dict(os.environ, ROADMAP_DASHBOARD_ROOT=str(repo_root))
+            # GH-429 / GH-496: dashboard and leaderboard paths
+            step_env = dict(
+                os.environ,
+                ROADMAP_DASHBOARD_ROOT=str(repo_root),
+                LEADERBOARD_DB=str(os.path.join(repo_root, "releases.db")),
+                LEADERBOARD_OUTPUT=str(os.path.join(repo_root, "LEADERBOARD.md")),
+            )
             r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False, env=step_env)
             if name.startswith("marathon-plan"):
                 handle_marathon_plan_result(r, reconciled_issues or set())
             elif r.returncode != 0:
                 die(f"Subprocess '{name}' failed with exit {r.returncode}:\n{r.stderr}\n{r.stdout}", code=6)
+
+        if not dry_run and not skip_marathon:
+            try:
+                os.makedirs(fp_dir, exist_ok=True)
+                with open(fp_file, "w") as f:
+                    f.write(plan_fp)
+            except Exception:
+                pass
     finally:
         if journal and not dry_run:
             for plan_doc in _plan_docs() - pre_plan_docs:
                 journal.track_created(plan_doc)
 
 
 def run_validation_gate(repo_root):
     """Run pdda doc-health verification gate."""
     log("Running PDDA doc-hygiene gate...")
     gate_cmd = ["bash", "utils/pdda-local-checks.sh"] if os.path.exists(os.path.join(repo_root, "utils", "pdda-local-checks.sh")) else ["bash", "utils/pdda/pdda.sh"]
     r = subprocess.run(
         gate_cmd,
         cwd=repo_root,
         capture_output=True,
         text=True,
         check=False,
     )
     # GH-429: the exit status IS the consuming repo's enforcement decision — pdda-lib.sh makes
     # `observe`/`light` exit 0 and `full` exit non-zero on errors. Grepping stdout for ERROR
     # overrode that mode and made a live reconciliation impossible on any repo with a standing
     # observe-mode backlog. Block on the status; surface the findings when it reports but passes.
     if r.returncode != 0:
         die(f"PDDA validation gate failed:\n{r.stdout}", code=7)
     if "ERROR" in r.stdout:
         found = re.search(r"(\d+) error\(s\) found", r.stdout)
         count = found.group(1) if found else "some"
         log(f"  WARNING — pdda reported {count} finding(s) but exited 0 (repo enforcement mode is not blocking); continuing")
 
 
+def run_pre_merge(repo_root, args):
+    """Execute pre-merge validation checks for PR or current branch (GH-496)."""
+    log("Running pre-merge closeout checks...")
+    try:
+        head_sha = subprocess.check_output(
+            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
+        ).strip()
+    except Exception as e:
+        die(f"Cannot determine HEAD SHA: {e}", code=2)
+
+    pr_num = None
+    pr_title = ""
+    pr_body = ""
+    if args.pr:
+        pr_num = args.pr[0]
+        try:
+            r = subprocess.run(
+                ["gh", "pr", "view", str(pr_num), "--json", "number,title,body,headRefOid"],
+                cwd=repo_root,
+                capture_output=True,
+                text=True,
+                timeout=10,
+            )
+            if r.returncode == 0:
+                data = json.loads(r.stdout)
+                pr_title = data.get("title", "")
+                pr_body = data.get("body", "")
+                head_sha = data.get("headRefOid") or head_sha
+        except Exception:
+            pass
+
+    if not pr_title and not pr_body:
+        try:
+            commits_text = subprocess.check_output(
+                ["git", "log", "-n", "10", "--format=%B"],
+                cwd=repo_root,
+                text=True,
+            )
+            pr_title = commits_text.splitlines()[0] if commits_text else ""
+            pr_body = commits_text
+        except Exception:
+            pass
+
+    repo_slug = github_slug_from_origin(repo_root)
+    closers, mentions = extract_linked_issues({"title": pr_title, "body": pr_body}, repo_slug=repo_slug)
+    log(f"  Target: {('PR #' + str(pr_num)) if pr_num else head_sha[:10]}")
+    log(f"  Closing issues detected: {closers or '(none)'}")
+
+    diff_docs = []
+    try:
+        diff_status = subprocess.check_output(
+            ["git", "diff", "--name-status", "HEAD~1..HEAD"],
+            cwd=repo_root,
+            text=True,
+        ).splitlines()
+        for dline in diff_status:
+            parts = dline.split()
+            if len(parts) >= 2:
+                for p in parts[1:]:
+                    if "PROJECT/2-WORKING/" in p and p.endswith(".md"):
+                        diff_docs.append(os.path.join(repo_root, p))
+    except Exception:
+        pass
+
+    target_docs = set()
+    errors = []
+
+    for issue_num in closers:
+        working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
+        matches = []
+        if os.path.isdir(working_dir):
+            for fname in sorted(os.listdir(working_dir)):
+                if fname.endswith(".md") and re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
+                    matches.append(os.path.join(working_dir, fname))
+        if len(matches) > 1:
+            errors.append(f"Ambiguous active doc match for issue #{issue_num}: {', '.join(os.path.basename(m) for m in matches)}")
+        elif len(matches) == 1:
+            target_docs.add(matches[0])
+        else:
+            completed_dir = os.path.join(repo_root, "PROJECT", "3-COMPLETED")
+            comp_matches = [
+                os.path.join(completed_dir, f)
+                for f in os.listdir(completed_dir)
+                if f.endswith(".md") and re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", f, re.IGNORECASE)
+            ] if os.path.isdir(completed_dir) else []
+            if comp_matches:
+                target_docs.add(comp_matches[0])
+
+    for d in diff_docs:
+        if os.path.isfile(d):
+            target_docs.add(d)
+
+    log(f"  Active docs evaluated: {[os.path.basename(d) for d in sorted(target_docs)] or '(none)'}")
+
+    doc_contract_failed = False
+    for doc_path in sorted(target_docs):
+        doc_name = os.path.basename(doc_path)
+        # 1. Frontmatter
+        fm_err = validate_frontmatter_schema(doc_path)
+        if fm_err:
+            errors.append(fm_err)
+            doc_contract_failed = True
+
+        # 2. Lessons Learned
+        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
+            content = f.read()
+        ll_err = validate_lessons_learned(content, doc_name)
+        if ll_err:
+            errors.append(ll_err)
+            doc_contract_failed = True
+
+    # 3. Test receipts
+    receipt_err = validate_pre_merge_receipts(repo_root, head_sha, pr_num)
+    if receipt_err:
+        errors.append(receipt_err)
+
+    if errors:
+        log_err("Pre-merge validation FAILED with the following error(s):")
+        for e in errors:
+            log_err(f"  - {e}")
+        exit_code = 5 if doc_contract_failed else 6
+        sys.exit(exit_code)
+
+    log("Pre-merge validation PASSED! ✅")
+    sys.exit(0)
+
+
 def main():
     parser = argparse.ArgumentParser(
         description="wave_reconcile.py — Canonical Post-Merge Wave & Marathon Lifecycle Reconciler"
     )
     parser.add_argument(
         "--root",
         help="Target repository root path (default: current working directory)",
     )
     parser.add_argument(
         "--pr",
         nargs="+",
         help="One or more merged PR numbers/IDs to reconcile",
     )
     parser.add_argument(
         "--commit",
         nargs="+",
         help="One or more commits landed directly on development to reconcile",
     )
     parser.add_argument(
         "--marathon",
         help="Marathon identifier / milestone name",
     )
     parser.add_argument(
         "--manifest",
         help="Path to structured JSON reconciliation manifest",
     )
     parser.add_argument(
         "--dry-run",
         action="store_true",
         help="Hermetic preview: assert zero file/DB/ref mutations",
     )
     parser.add_argument(
         "--offline",
         help="Run without network using offline JSON manifest cache",
     )
     parser.add_argument(
         "--skip-pull",
         action="store_true",
         help="Skip git pull --ff-only origin development (for testing/isolated clones)",
     )
     parser.add_argument(
         "--skip-branch-check",
         action="store_true",
         help="Skip active branch check (for tests on feature branches)",
     )
     parser.add_argument(
         "--allow-dirty",
         action="store_true",
         help="Allow dirty working tree (for test fixtures only)",
     )
     parser.add_argument(
         "--force-promote",
         action="store_true",
         help="Force promotion of active docs and roadmap entries to Completed regardless of linked issue OPEN state",
     )
     parser.add_argument(
         "--gate",
         "--require-receipts",
         action="store_true",
         dest="require_receipts",
         help="Require a receipt matching each PR number or exact merge commit before closeout (GH-425)",
     )
+    parser.add_argument(
+        "--pre-merge",
+        action="store_true",
+        help="Run read-only pre-merge checks on closing active docs (frontmatter, lessons learned, test receipts) (GH-496)",
+    )
+    parser.add_argument(
+        "--force-local-reconcile",
+        action="store_true",
+        help="Bypass hosted in-flight reconciler check for emergency local reconciliation (GH-496)",
+    )
 
     parser.add_argument("--catch-up", action="store_true", help="Recover closed-issue drift from committed docs and manifest")
 
     args = parser.parse_args()
 
     repo_root = os.path.abspath(args.root) if args.root else resolve_repo_root()
+
+    if args.pre_merge:
+        run_pre_merge(repo_root, args)
+        return
+
     lock_file = os.path.join(repo_root, ".git", "wave-reconcile.lock")
     journal = RollbackJournal()
     baseline = None
 
     try:
+        if args.force_local_reconcile and os.environ.get("GITHUB_ACTIONS") == "true":
+            die("--force-local-reconcile is prohibited inside GITHUB_ACTIONS", code=2)
+
         # Preflight phase
         log(f"Starting wave reconciliation (dry_run={args.dry_run}, root={repo_root})")
         baseline = check_porcelain_cleanliness(repo_root, allow_dirty=(args.allow_dirty or args.dry_run))
         check_current_branch(repo_root, skip_branch_check=args.skip_branch_check)
 
+        repo_slug = github_slug_from_origin(repo_root)
+        has_workflow = os.path.isfile(os.path.join(repo_root, ".github", "workflows", "wave-reconcile.yml"))
+        if not args.offline and not args.dry_run and os.environ.get("GITHUB_ACTIONS") != "true":
+            if repo_slug and has_workflow:
+                check_hosted_reconciler_in_flight(repo_root, repo_slug=repo_slug, force=args.force_local_reconcile)
+
         if not args.skip_pull and not args.dry_run and not args.offline:
             pull_upstream(repo_root)
 
         offline_manifest = None
         if args.offline:
             try:
                 with open(args.offline, "r", encoding="utf-8") as f:
                     offline_manifest = json.load(f)
             except Exception as e:
                 die(f"Failed loading offline manifest from {args.offline}: {e}", code=4)
 
         landing_items = [("pr", value) for value in (args.pr or [])]
         landing_items.extend(("commit", value) for value in (args.commit or []))
         if args.manifest:
             try:
                 with open(args.manifest, "r", encoding="utf-8") as f:
                     mdata = json.load(f)
                     landing_items.extend(("pr", str(p)) for p in mdata.get("prs", []))
             except Exception as e:
                 die(f"Failed loading manifest from {args.manifest}: {e}", code=4)
 
         if not landing_items and not args.marathon and not args.catch_up:
             die("No PRs, commits, or marathon specified. Pass --pr <N>..., --commit <SHA>..., --marathon <name>, or --catch-up", code=2)
 
         with ReconcilerLock(lock_file):
             reconciled_issues = set()
             repo_slug = github_slug_from_origin(repo_root)  # GH-429: URL-form closers, this repo only
             if args.catch_up:
                 landing_items.extend(("pr", str(n)) for n in catch_up_prs(repo_root, repo_slug, offline_manifest))
             landing_items = list(dict.fromkeys((kind, str(value)) for kind, value in landing_items))
             for landing_kind, landing_id in landing_items:
                 if landing_kind == "commit":
                     pr_meta = fetch_commit_metadata(repo_root, landing_id, offline_manifest)
                 else:
                     pr_meta = fetch_pr_metadata(repo_root, landing_id, offline_manifest, dry_run=args.dry_run)
                 landing = landing_label(pr_meta)
                 log(f"Processing {landing}...")
                 state = pr_meta.get("state", "").upper()
                 is_merged = (state == "MERGED")
 
diff --git a/utils/roadmap-dashboard.sh b/utils/roadmap-dashboard.sh
index 652a3059..4850fcc1 100755
--- a/utils/roadmap-dashboard.sh
+++ b/utils/roadmap-dashboard.sh
@@ -52,89 +52,94 @@ if [ -z "${ROADMAP_DASHBOARD_SOURCE:-}" ] \
   DB_SRC="$TMP_DIR/roadmap-from-db.md"
   DB_JSON="$TMP_DIR/roadmap-rows.json"
   # JSON goes through a temp file passed as argv — `python3 -` takes its PROGRAM from the
   # heredoc on stdin, so piping data in as well would feed the parser nothing (the PR #240
   # rollup.sh bug, same shape). The APP resolves from HERE (this script's own checkout) while
   # --root follows $ROOT: under ROADMAP_DASHBOARD_ROOT (GH-272) the target repo may ship the
   # ledger without a utils/ tree at all.
   if python3 "$HERE/py/releases_app.py" --root "$ROOT" roadmap list --json > "$DB_JSON" 2>/dev/null \
      && python3 - "$DB_JSON" > "$DB_SRC" <<'PY'
 import json, sys
 with open(sys.argv[1]) as f:
     rows = json.load(f)
 print("# ROADMAP (rendered from the RELEASES DB — GH-243; ROADMAP.md is frozen legacy)\n")
 print("## Ledger\n")   # the renderer only counts sections below this heading
 sections = {}
 for r in rows:
     sections.setdefault(r.get("section") or "(unsectioned)", []).append(r)
 for section, items in sections.items():
     print(f"### {section}\n")
     for r in sorted(items, key=lambda x: x.get("position") or 0):
         line = (r.get("raw_text") or "").strip()
         if not line:
             gh = f"GH-{r['gh_number']} · " if r.get("gh_number") is not None else ""
             line = f"- **{gh}{r.get('title', '')}**"
         print(line)
     print()
 PY
   then
     [ -s "$DB_SRC" ] && SOURCE_FILE="$DB_SRC"
   fi
 fi
 
 if [ ! -f "$SOURCE_FILE" ]; then
   echo "roadmap-dashboard: source not found: $SOURCE_FILE" >&2
   exit 3
 fi
 
 # Resolve from HERE, not ROOT: a target ledger need not ship its own utils/ tree.
 # Failure must stop rendering rather than fall back to a second, drifting vocabulary.
 LEDGER_SECTIONS_JSON="$(python3 "$HERE/py/releases_app.py" roadmap sections --json)"
-node - "$SOURCE_FILE" "$LEDGER_SECTIONS_JSON" >"$RENDERED" <<'NODE'
+GEN=""
+if [ -f "$ROOT/releases.db" ]; then
+  GEN="$(python3 "$HERE/py/releases_app.py" --root "$ROOT" settings get generation 2>/dev/null || true)"
+fi
+node - "$SOURCE_FILE" "$LEDGER_SECTIONS_JSON" "$GEN" >"$RENDERED" <<'NODE'
 const fs = require("fs");
 
 const sourcePath = process.argv[2];
 const raw = fs.readFileSync(sourcePath, "utf8");
 const lines = raw.split(/\r?\n/);
 
-const banner = "<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit ROADMAP.md -->";
 const ledgerSections = JSON.parse(process.argv[3]);
+const generation = process.argv[4] || "";
+const banner = "<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit the ledger through releases CLI. -->";
 const knownStatuses = ["🟢", "🟡", "⏸️", "⛔", "✅", "🔮", "🔲"];
 const extraStatuses = ["⚠️"];
 
 function escapeCell(value) {
   return String(value)
     .replace(/\|/g, "\\|")
     .replace(/</g, "&lt;")
     .replace(/>/g, "&gt;");
 }
 
 function stripMarkdown(value) {
   return value
     .replace(/`([^`]+)`/g, "$1")
     .replace(/\*\*([^*]+)\*\*/g, "$1")
     .replace(/\*([^*]+)\*/g, "$1")
     .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
     .trim();
 }
 
 function parseBullet(block) {
   const text = block.map((line) => line.trim()).join(" ").replace(/\s+/g, " ").trim();
   const titleMatch = text.match(/^- \*\*(.+?)\*\*/);
   const title = titleMatch ? stripMarkdown(titleMatch[1]) : stripMarkdown(text.replace(/^- /, ""));
 
   let status = "—";
   for (const emoji of knownStatuses.concat(extraStatuses)) {
     if (text.includes(emoji)) {
       status = emoji;
       break;
     }
   }
 
   const links = [];
   const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
   let match;
   while ((match = linkPattern.exec(text)) !== null) {
     links.push(`[${match[1]}](${match[2]})`);
   }
 
   return { title, status, links };
@@ -221,84 +226,87 @@ for (let i = 0; i < lines.length; i++) {
 
   const trimmed = line.trim();
   if (!trimmed || trimmed.startsWith("<!--") || trimmed.startsWith("#")) continue;
 
   if (!/^- \*\*[^\r\n*]+?\*\*/.test(line)) {
     // GH-257: track non-empty dropped/unparseable line under an active ledger section
     const issueMatch = trimmed.match(/(?:GH-?|#)(\d+)/i);
     const id = issueMatch ? `#${issueMatch[1]}` : JSON.stringify(trimmed.length > 30 ? trimmed.slice(0, 30) + "..." : trimmed);
     droppedRows.push({ section: currentSection, id, line: trimmed });
     continue;
   }
 
   const block = [line];
   while (i + 1 < lines.length) {
     const next = lines[i + 1];
     if (/^###\s+/.test(next) || /^##\s+/.test(next) || /^\s*[-*+]\s+/.test(next)) break;
     block.push(next);
     i += 1;
   }
   sections.get(currentSection).push(parseBullet(block));
 }
 
 if (droppedRows.length > 0) {
   const ids = droppedRows.map((d) => d.id).join(", ");
   process.stderr.write(`roadmap-dashboard: warning: dropped ${droppedRows.length} unparseable row(s): ${ids}\n`);
 }
 
 // GH-474: a SECOND way to go missing, reported separately because the cause and the fix differ —
 // the row is well-formed, its heading is not one this renderer renders. Both lines start with the
 // same "warning: dropped " prefix on purpose: githooks/dashboard-staleness-guard.sh refuses on
 // that prefix, so a new omission mode is caught by the existing guard without touching it.
 if (unknownSectionRows.length > 0) {
   const ids = unknownSectionRows.map((d) => d.id).join(", ");
   const heads = [...new Set(unknownSectionRows.map((d) => d.section))].map((s) => JSON.stringify(s)).join(", ");
   process.stderr.write(
     `roadmap-dashboard: warning: dropped ${unknownSectionRows.length} row(s) under unrecognised section heading(s) ${heads}: ${ids}\n`
   );
 }
 
 const output = [];
+if (generation) {
+  output.push(`<!-- releases-app generation: ${generation} -->`);
+}
 output.push(banner);
 output.push("");
 output.push("# ROADMAP Dashboard");
 output.push("");
-output.push("Read-only derived view of the root [ROADMAP.md](ROADMAP.md) ledger.");
+output.push("Read-only derived view of the roadmap ledger (releases.db).");
 output.push("");
 
 for (const heading of ledgerSections) {
   const items = sections.get(heading) || [];
   output.push(`## ${heading}`);
   output.push("");
   output.push(`Summary: ${items.length} items | Tally: ${formatTally(items)}`);
   output.push("");
   output.push("| Item | Status | Links |");
   output.push("| --- | --- | --- |");
   for (const item of items) {
     const links = item.links.length > 0 ? item.links.join(" · ") : "—";
     output.push(`| ${escapeCell(item.title)} | ${escapeCell(item.status)} | ${links} |`);
   }
   if (items.length === 0) {
     output.push("| — | — | — |");
   }
   output.push("");
 }
 
 process.stdout.write(output.join("\n"));
 NODE
 
 if [[ "$MODE" == "check" ]]; then
   if [[ ! -f "$OUTPUT_FILE" ]]; then
     echo "roadmap-dashboard: missing artifact: $OUTPUT_FILE" >&2
     exit 1
   fi
   if cmp -s "$RENDERED" "$OUTPUT_FILE"; then
     echo "roadmap-dashboard: artifact is in sync"
     exit 0
   fi
   echo "roadmap-dashboard: artifact drift detected: $OUTPUT_FILE" >&2
   diff -u "$OUTPUT_FILE" "$RENDERED" || true
   exit 1
 fi
 
 cp "$RENDERED" "$OUTPUT_FILE"
 echo "roadmap-dashboard: wrote $OUTPUT_FILE"

exec
/bin/zsh -lc "nl -ba .github/workflows/wave-reconcile.yml | sed -n '1,260p'; nl -ba utils/py/wave_reconcile.py | sed -n '1,360p'; nl -ba utils/py/wave_reconcile.py | sed -n '360,760p'; nl -ba utils/py/wave_reconcile.py | sed -n '760,1180p'; nl -ba utils/py/wave_reconcile.py | sed -n '1180,1540p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 0ms:
     1	name: Wave reconciliation
     2	
     3	on:
     4	  pull_request:
     5	    types: [closed]
     6	    branches: [development]
     7	  workflow_dispatch:
     8	  # Recover missed close events from committed lifecycle state, including queue overflow.
     9	  schedule:
    10	    - cron: '23 */6 * * *'
    11	
    12	concurrency:
    13	  group: wave-reconcile
    14	  cancel-in-progress: false
    15	  # Supported since 2026-05-07; retain up to 100 pending runs instead of replacing one.
    16	  # https://github.blog/changelog/2026-05-07-github-actions-concurrency-groups-now-allow-larger-queues/
    17	  queue: max
    18	
    19	permissions:
    20	  contents: read
    21	
    22	jobs:
    23	  reconcile:
    24	    if: >-
    25	      github.event_name != 'pull_request' ||
    26	      (github.event.pull_request.merged == true && github.event.pull_request.base.ref == 'development')
    27	    runs-on: macos-latest
    28	    timeout-minutes: 30
    29	    permissions:
    30	      contents: write
    31	      issues: read
    32	      pull-requests: read
    33	    env:
    34	      GH_TOKEN: ${{ github.token }}
    35	      PYTHONDONTWRITEBYTECODE: '1'
    36	    steps:
    37	      - uses: actions/checkout@v4
    38	        with:
    39	          ref: development
    40	          fetch-depth: 0
    41	      - name: Check direct-push prerequisite
    42	        env:
    43	          REPO: ${{ github.repository }}
    44	        run: |
    45	          set -euo pipefail
    46	          # development was unprotected when implemented. Fail before writes if that changes;
    47	          # a protected branch needs a reviewed bot-bypass policy, never an implicit bypass.
    48	          test "$(gh api "repos/$REPO/branches/development" --jq .protected)" = false
    49	      - name: Install runtime dependencies
    50	        run: npm ci
    51	      - name: Reconcile merged PR or catch up
    52	        env:
    53	          EVENT_NAME: ${{ github.event_name }}
    54	          PR_NUMBER: ${{ github.event.pull_request.number }}
    55	        run: |
    56	          set -euo pipefail
    57	          if [ "$EVENT_NAME" = pull_request ]; then
    58	            python3 utils/py/wave_reconcile.py --pr "$PR_NUMBER" --gate
    59	          else
    60	            python3 utils/py/wave_reconcile.py --catch-up --gate
    61	          fi
    62	      - name: Commit declared artifacts and push
    63	        shell: python3 {0}
    64	        run: |
    65	          import os
    66	          import re
    67	          import subprocess
    68	
    69	          def git(*args):
    70	              return subprocess.check_output(['git', *args])
    71	
    72	          # Include both sides of doc moves; --no-renames makes the deletions explicit.
    73	          changed = set(filter(None, git('diff', '--name-only', '--no-renames', '-z', 'HEAD').split(b'\0')))
    74	          changed.update(filter(None, git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0')))
    75	          exact = {'releases.db', 'releases.sql', 'RELEASES.generated.md', 'ROADMAP.md',
    76	                   'ROADMAP-DASHBOARD.md', 'RELEASES-PREVIEW.html', 'LEADERBOARD.html', 'LEADERBOARD.md'}
    77	          doc = r'PROJECT/(?:2-WORKING|3-COMPLETED|4-MISC)/(?:GH-)?[0-9]+-[^/]+\.md'
    78	          plan = r'(?:PROJECT/2-WORKING/)?MARATHON-PLAN-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md'
    79	          paths = sorted(os.fsdecode(path) for path in changed)
    80	          unexpected = [p for p in paths if p not in exact and not re.fullmatch(doc, p) and not re.fullmatch(plan, p)]
    81	          if unexpected:
    82	              raise SystemExit('Refusing undeclared reconciliation artifacts: ' + repr(unexpected))
    83	          if not paths:
    84	              print('Nothing to commit')
    85	              raise SystemExit(0)
    86	          # Explicit paths only; a downstream generator cannot widen the bot commit.
    87	          git('add', '-A', '--', *paths)
    88	          git('config', 'user.name', 'github-actions[bot]')
    89	          git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    90	          git('commit', '-m', 'chore: reconcile merged development work')
    91	          # One fast-forward push; never rebase a generated SQLite DB or force-push.
    92	          # A concurrent merge rejects this push and fails the job. The next scheduled/manual
    93	          # catch-up starts from fresh development and recomputes the unlanded transitions.
    94	          git('push', 'origin', 'HEAD:development')
     1	#!/usr/bin/env python3
     2	"""wave_reconcile.py (GH-165) — Post-Merge Wave & Marathon Lifecycle Reconciler.
     3	
     4	The canonical, single-command Python reconciler to automate post-merge lifecycle
     5	transitions across Active Docs (PROJECT/2-WORKING/ -> 3-COMPLETED/ or 4-MISC/),
     6	ROADMAP.md, releases.db SQLite ledger, generated dashboards, and next-wave marathon planning.
     7	"""
     8	
     9	import argparse
    10	import fcntl
    11	import glob
    12	import hashlib
    13	import json
    14	import os
    15	import re
    16	import shutil
    17	import sqlite3
    18	import subprocess
    19	import sys
    20	import tempfile
    21	from datetime import datetime
    22	from pathlib import Path
    23	
    24	sys.dont_write_bytecode = True
    25	from harness_paths import github_slug_from_origin, harness_home, harness_tool, is_vendored, repo_root, resolve_tool
    26	
    27	
    28	class ReconcileError(Exception):
    29	    """Custom exception class ensuring proper rollback catching."""
    30	
    31	    def __init__(self, message, code=2):
    32	        super().__init__(message)
    33	        self.code = code
    34	
    35	
    36	def log(msg):
    37	    print(f"wave-reconcile: {msg}", flush=True)
    38	
    39	
    40	def log_err(msg):
    41	    print(f"wave-reconcile: ERROR — {msg}", file=sys.stderr, flush=True)
    42	
    43	
    44	def die(msg, code=2):
    45	    log_err(msg)
    46	    raise ReconcileError(msg, code=code)
    47	
    48	
    49	class ReconcilerLock:
    50	    """Lock manager preventing concurrent reconciliation runs."""
    51	
    52	    def __init__(self, lock_path):
    53	        self.lock_path = lock_path
    54	        self.fd = None
    55	
    56	    def __enter__(self):
    57	        try:
    58	            self.fd = open(self.lock_path, "w")
    59	            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    60	            self.fd.write(f"pid={os.getpid()}\ntime={datetime.now().isoformat()}\n")
    61	            self.fd.flush()
    62	            return self
    63	        except (BlockingIOError, OSError) as e:
    64	            die(f"Could not acquire reconciler lock at {self.lock_path}: {e}", code=8)
    65	
    66	    def __exit__(self, exc_type, exc_val, exc_tb):
    67	        if self.fd:
    68	            try:
    69	                fcntl.flock(self.fd, fcntl.LOCK_UN)
    70	                self.fd.close()
    71	            except OSError:
    72	                pass
    73	
    74	
    75	def check_hosted_reconciler_in_flight(repo_root, repo_slug=None, force=False):
    76	    """Refuse local reconciliation if hosted wave-reconcile.yml is running/queued (GH-496)."""
    77	    cmd = [
    78	        "gh", "run", "list",
    79	        "--workflow", "wave-reconcile.yml",
    80	        "--json", "databaseId,status,conclusion,createdAt,headSha,event",
    81	        "--limit", "10",
    82	    ]
    83	    if repo_slug:
    84	        cmd.extend(["--repo", repo_slug])
    85	
    86	    try:
    87	        res = subprocess.run(
    88	            cmd,
    89	            cwd=repo_root,
    90	            capture_output=True,
    91	            text=True,
    92	            timeout=15,
    93	        )
    94	    except FileNotFoundError:
    95	        if force:
    96	            log("  WARNING: 'gh' CLI not found; bypassing hosted in-flight check via --force-local-reconcile")
    97	            return
    98	        die("Hosted reconciler check failed: 'gh' command not found. Pass --force-local-reconcile to bypass.", code=8)
    99	    except subprocess.TimeoutExpired:
   100	        if force:
   101	            log("  WARNING: 'gh run list' timed out; bypassing hosted in-flight check via --force-local-reconcile")
   102	            return
   103	        die("Hosted reconciler check failed: 'gh run list' timed out. Pass --force-local-reconcile to bypass.", code=8)
   104	    except Exception as e:
   105	        if force:
   106	            log(f"  WARNING: gh run list failed ({e}); bypassing hosted in-flight check via --force-local-reconcile")
   107	            return
   108	        die(f"Hosted reconciler check failed: {e}. Pass --force-local-reconcile to bypass.", code=8)
   109	
   110	    if res.returncode != 0:
   111	        if force:
   112	            log(f"  WARNING: gh run list exited {res.returncode}; bypassing hosted in-flight check via --force-local-reconcile")
   113	            return
   114	        err = res.stderr.strip() or "unknown error"
   115	        die(f"Hosted reconciler check failed: unable to query GitHub Actions ({err}). Pass --force-local-reconcile to bypass.", code=8)
   116	
   117	    stdout = res.stdout.strip()
   118	    if not stdout:
   119	        runs = []
   120	    else:
   121	        try:
   122	            runs = json.loads(stdout)
   123	        except ValueError:
   124	            if force:
   125	                return
   126	            die("Hosted reconciler check failed: malformed JSON from gh run list. Pass --force-local-reconcile to bypass.", code=8)
   127	
   128	    in_flight = [
   129	        r for r in runs
   130	        if r.get("status") in ("queued", "in_progress", "waiting", "requested")
   131	    ]
   132	    if in_flight:
   133	        run_ids = ", ".join(f"#{r.get('databaseId')} ({r.get('status')})" for r in in_flight)
   134	        if force:
   135	            log(f"  WARNING: Overriding active hosted reconciliation run(s): {run_ids} via --force-local-reconcile")
   136	            return
   137	        die(
   138	            f"Hosted reconciliation workflow (wave-reconcile.yml) is currently in-flight: {run_ids}. "
   139	            "Refusing local reconciliation to prevent concurrent landing collisions. "
   140	            "Wait for hosted workflow to complete, or pass --force-local-reconcile to override.",
   141	            code=8,
   142	        )
   143	
   144	
   145	class RollbackJournal:
   146	    """Snapshots pre-mutation file states and rolls back on failure."""
   147	
   148	    def __init__(self):
   149	        self.backups = {}  # original_path -> backup_temp_path
   150	        self.created_files = set()
   151	        self.deleted_files = set()
   152	
   153	    def snapshot(self, path):
   154	        p = os.path.abspath(path)
   155	        if p not in self.backups and os.path.exists(p):
   156	            tmp = tempfile.NamedTemporaryFile(delete=False)
   157	            tmp.close()
   158	            shutil.copy2(p, tmp.name)
   159	            self.backups[p] = tmp.name
   160	
   161	    def track_created(self, path):
   162	        self.created_files.add(os.path.abspath(path))
   163	
   164	    def rollback(self):
   165	        log("Rolling back all uncommitted mutations...")
   166	        for created in self.created_files:
   167	            if os.path.exists(created):
   168	                try:
   169	                    os.unlink(created)
   170	                except OSError:
   171	                    pass
   172	        for orig, backup in self.backups.items():
   173	            try:
   174	                os.makedirs(os.path.dirname(orig), exist_ok=True)
   175	                shutil.copy2(backup, orig)
   176	            except OSError as e:
   177	                log_err(f"Failed restoring {orig} from {backup}: {e}")
   178	        self.cleanup()
   179	
   180	    def changed(self):
   181	        """Whether any journaled artifact differs, ignoring empty directories."""
   182	        return any(os.path.exists(p) for p in self.created_files) or any(
   183	            not os.path.exists(p) or Path(p).read_bytes() != Path(backup).read_bytes()
   184	            for p, backup in self.backups.items()
   185	        )
   186	
   187	    def cleanup(self):
   188	        for backup in self.backups.values():
   189	            if os.path.exists(backup):
   190	                try:
   191	                    os.unlink(backup)
   192	                except OSError:
   193	                    pass
   194	        self.backups.clear()
   195	        self.created_files.clear()
   196	
   197	
   198	def resolve_repo_root():
   199	    """Find repository root containing .git."""
   200	    cur = os.path.abspath(os.getcwd())
   201	    while cur != os.path.dirname(cur):
   202	        if os.path.isdir(os.path.join(cur, ".git")) or os.path.isfile(os.path.join(cur, ".git")):
   203	            return cur
   204	        cur = os.path.dirname(cur)
   205	    return os.path.abspath(os.getcwd())
   206	
   207	
   208	def check_porcelain_cleanliness(repo_root, allow_dirty=False):
   209	    """Assert clean git working tree before mutation."""
   210	    cmd = ["git", "-C", repo_root, "status", "--porcelain"]
   211	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   212	    if r.returncode != 0:
   213	        die(f"git status failed: {r.stderr}")
   214	    dirt = r.stdout.strip()
   215	    if dirt and not allow_dirty:
   216	        die(
   217	            f"Working tree is dirty. Must be completely clean to reconcile:\n{dirt}",
   218	            code=3,
   219	        )
   220	    return dirt
   221	
   222	
   223	def verify_rollback_completeness(repo_root, baseline):
   224	    """GH-271: a rollback must restore the pre-run tree, not merely claim to.
   225	
   226	    The 2026-08-23 failure left regenerated dashboards and a stray MARATHON-PLAN-<date>.md
   227	    behind after "Rolling back all uncommitted mutations..." reported success. Compare
   228	    porcelain against the pre-run baseline (fixtures may legitimately start dirty under
   229	    --allow-dirty) and name every leftover — an incomplete rollback must be visible, never
   230	    a silent success.
   231	    """
   232	    if baseline is None:
   233	        return
   234	    cmd = ["git", "-C", repo_root, "status", "--porcelain"]
   235	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   236	    if r.returncode != 0:
   237	        log_err(f"Rollback completeness could not be verified: git status failed: {r.stderr}")
   238	        return
   239	    current = r.stdout.strip()
   240	    if current != baseline:
   241	        base_lines = set(baseline.splitlines())
   242	        log_err("Rollback INCOMPLETE — working tree differs from the pre-run state. Leftovers:")
   243	        for line in current.splitlines():
   244	            if line not in base_lines:
   245	                log_err(f"  {line}")
   246	
   247	
   248	def check_current_branch(repo_root, expected_branch="development", skip_branch_check=False):
   249	    """Verify active branch matches target branch."""
   250	    if skip_branch_check:
   251	        return
   252	    cmd = ["git", "-C", repo_root, "branch", "--show-current"]
   253	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   254	    current = r.stdout.strip()
   255	    if current != expected_branch:
   256	        die(
   257	            f"Active branch is '{current}', but post-merge reconciliation requires '{expected_branch}'.",
   258	            code=3,
   259	        )
   260	
   261	
   262	def pull_upstream(repo_root, branch="development"):
   263	    """Fast-forward pull from origin."""
   264	    cmd = ["git", "-C", repo_root, "pull", "--ff-only", "origin", branch]
   265	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   266	    if r.returncode != 0:
   267	        die(f"git pull --ff-only failed: {r.stderr}")
   268	
   269	
   270	def fetch_issue_state(repo_root, issue_num, offline_manifest=None):
   271	    """Linked issue state, or None when unknowable (GH-202).
   272	
   273	    None means PROMOTE as before — backward-compatible for offline manifests that
   274	    carry no issue list; only a positively-OPEN issue suppresses promotion.
   275	    Offline manifests may declare {"issues": [{"number": N, "state": "OPEN"}]}.
   276	    """
   277	    if offline_manifest:
   278	        for entry in offline_manifest.get("issues", []):
   279	            if str(entry.get("number")) == str(issue_num):
   280	                return str(entry.get("state", "")).upper()
   281	        return None  # legacy manifest without an issues key: unknown, promote as before
   282	    # LIVE reconcile: a failed gh is a failed fact-check, not an unknown state. A transient
   283	    # error (network, rate limit) must NOT silently fall back to promotion (GH-202 review,
   284	    # Agy round 1 blocker) — that would mis-promote every open issue on a bad network day.
   285	    try:
   286	        r = subprocess.run(
   287	            ["gh", "issue", "view", str(issue_num), "--json", "state"],
   288	            cwd=repo_root, capture_output=True, text=True, check=False,
   289	        )
   290	    except OSError as exc:
   291	        die(f"gh issue view #{issue_num} could not run ({exc}); refusing to guess issue state — "
   292	            f"fix gh access or pass --offline with an issues[] manifest", code=6)
   293	    if r.returncode != 0:
   294	        die(f"gh issue view #{issue_num} failed (exit {r.returncode}): {r.stderr.strip()}; "
   295	            f"refusing to guess issue state — fix gh access or pass --offline with an issues[] manifest", code=6)
   296	    try:
   297	        import json as _json
   298	        return str(_json.loads(r.stdout).get("state", "")).upper()
   299	    except ValueError:
   300	        die(f"gh issue view #{issue_num} returned unparseable output; refusing to guess issue state", code=6)
   301	
   302	
   303	def record_merge_evidence(doc_path, pr_meta, dry_run=False, journal=None):
   304	    """Open-issue docs stay in 2-WORKING; record the merged-PR evidence in place (GH-202)."""
   305	    merged_at = (pr_meta.get("mergedAt") or "")[:10]
   306	    label = landing_label(pr_meta)
   307	    verb = "landed" if pr_meta.get("artifactKind") == "commit" else "merged"
   308	    note = "\n## Merge evidence\n\n- " + label + " " + verb + " " + (merged_at or "(date unknown)") + " — linked issue still OPEN; doc stays active by design (GH-202: promotion requires the issue to be closed).\n"
   309	    with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   310	        content = f.read()
   311	    if ("\n- " + label + " " + verb + " ") in content or content.startswith("- " + label + " " + verb + " "):
   312	        return  # idempotent
   313	    print("TRANSITION " + json.dumps(["doc", "merge-evidence", label, os.path.basename(doc_path)]), flush=True)
   314	    if not dry_run:
   315	        if journal is not None:
   316	            journal.snapshot(doc_path)
   317	        with open(doc_path, "a", encoding="utf-8") as f:
   318	            f.write(note)
   319	
   320	
   321	def fetch_pr_metadata(repo_root, pr_id, offline_manifest=None, dry_run=False):
   322	    """Fetch merged PR metadata from GitHub or offline manifest."""
   323	    if offline_manifest:
   324	        for entry in offline_manifest.get("prs", []):
   325	            if str(entry.get("number")) == str(pr_id):
   326	                return entry
   327	        die(f"PR #{pr_id} not found in offline manifest", code=4)
   328	
   329	    if dry_run:
   330	        # In dry run without offline manifest, try gh if available or return stub preview
   331	        pass
   332	
   333	    cmd = [
   334	        "gh",
   335	        "pr",
   336	        "view",
   337	        str(pr_id),
   338	        "--json",
   339	        "number,title,state,mergedAt,mergeCommit,baseRefName,headRefName,body,url",
   340	    ]
   341	    r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)
   342	    if r.returncode != 0:
   343	        if dry_run:
   344	            log(f"dry-run: gh pr view unavailable ({r.stderr.strip()}); using synthetic preview metadata for PR #{pr_id}")
   345	            return {
   346	                "number": int(pr_id),
   347	                "title": f"Preview PR #{pr_id}",
   348	                "state": "MERGED",
   349	                "mergedAt": datetime.now().isoformat() + "Z",
   350	                "baseRefName": "development",
   351	                "body": f"Closes #{pr_id}",
   352	            }
   353	        die(f"gh pr view {pr_id} failed: {r.stderr}", code=4)
   354	    try:
   355	        return json.loads(r.stdout)
   356	    except json.JSONDecodeError as e:
   357	        die(f"Failed parsing gh pr view JSON for PR #{pr_id}: {e}", code=4)
   358	
   359	
   360	def fetch_commit_metadata(repo_root, commit_id, offline_manifest=None):
   360	def fetch_commit_metadata(repo_root, commit_id, offline_manifest=None):
   361	    """Return direct-commit landing metadata in the reconciler's internal shape."""
   362	    if offline_manifest:
   363	        for entry in offline_manifest.get("commits", []):
   364	            if str(entry.get("sha", "")).startswith(str(commit_id)):
   365	                message = entry.get("message") or ""
   366	                return {
   367	                    "number": str(entry.get("sha", commit_id))[:12],
   368	                    "title": message.splitlines()[0] if message else f"commit {commit_id}",
   369	                    "state": "MERGED", "mergedAt": entry.get("committedAt"),
   370	                    "baseRefName": "development", "body": message,
   371	                    "url": entry.get("url", ""), "artifactKind": "commit",
   372	                    "sha": entry.get("sha", commit_id),
   373	                    "mergeCommit": {"oid": entry.get("sha", commit_id)},
   374	                }
   375	        die(f"Commit {commit_id} not found in offline manifest", code=4)
   376	
   377	    resolved = subprocess.run(
   378	        ["git", "-C", repo_root, "rev-parse", "--verify", f"{commit_id}^{{commit}}"],
   379	        capture_output=True, text=True, check=False,
   380	    )
   381	    if resolved.returncode != 0:
   382	        die(f"Commit {commit_id} cannot be resolved locally", code=4)
   383	    sha = resolved.stdout.strip()
   384	    reachable = subprocess.run(
   385	        ["git", "-C", repo_root, "merge-base", "--is-ancestor", sha, "development"],
   386	        capture_output=True, text=True, check=False,
   387	    )
   388	    if reachable.returncode != 0:
   389	        die(f"Commit {sha} is not reachable from local development", code=4)
   390	    shown = subprocess.run(
   391	        ["git", "-C", repo_root, "show", "-s", "--format=%cI%x00%B", sha],
   392	        capture_output=True, text=True, check=False,
   393	    )
   394	    if shown.returncode != 0 or "\0" not in shown.stdout:
   395	        die(f"Could not read commit metadata for {sha}", code=4)
   396	    committed_at, message = shown.stdout.split("\0", 1)
   397	    message = message.strip()
   398	    slug = github_slug_from_origin(repo_root)
   399	    return {
   400	        "number": sha[:12], "title": message.splitlines()[0], "state": "MERGED",
   401	        "mergedAt": committed_at, "baseRefName": "development", "body": message,
   402	        "url": f"https://github.com/{slug}/commit/{sha}" if slug else "",
   403	        "artifactKind": "commit", "sha": sha, "mergeCommit": {"oid": sha},
   404	    }
   405	
   406	
   407	def landing_label(meta):
   408	    if meta.get("artifactKind") == "commit":
   409	        return "commit " + str(meta.get("sha") or meta.get("number"))[:12]
   410	    return "PR #" + str(meta.get("number", "?"))
   411	
   412	
   413	def check_provenance_receipts(repo_root, pr_meta):
   414	    """Require a JSONL receipt attributable to this PR (GH-425).
   415	
   416	    Accept top-level pr/pr_number (positive integer or decimal string), or an
   417	    exact full commit matching GitHub's mergeCommit. Explicit PR fields must all
   418	    match; a conflicting PR cannot be rescued by a commit match. Filenames and
   419	    issue numbers are not PR identity. This checks attribution, not test success
   420	    or whether the receipt was committed; report only the identity actually read.
   421	    """
   422	    pr_num = pr_meta.get("number")
   423	    results_dir = os.path.join(repo_root, "TESTS-RESULTS")
   424	    if not os.path.isdir(results_dir):
   425	        die(f"--gate failure: TESTS-RESULTS directory missing; cannot verify provenance for PR #{pr_num}", code=6)
   426	
   427	    def pr_number(value):
   428	        if type(value) is int and value > 0:
   429	            return str(value)
   430	        if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
   431	            return value
   432	        return None
   433	
   434	    expected_pr = pr_number(pr_num)
   435	    merge_commit = pr_meta.get("mergeCommit") or {}
   436	    merge_sha = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
   437	    if not isinstance(merge_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", merge_sha):
   438	        merge_sha = None
   439	    for root, dirs, files in os.walk(results_dir):
   440	        dirs.sort()
   441	        for name in sorted(files):
   442	            if name not in ("error_log.jsonl", "provenance.jsonl"):
   443	                continue
   444	            path = os.path.join(root, name)
   445	            if os.path.islink(path) or not os.path.isfile(path):
   446	                continue
   447	            try:
   448	                with open(path, encoding="utf-8") as receipt:
   449	                    for line_num, line in enumerate(receipt, 1):
   450	                        try:
   451	                            entry = json.loads(line)
   452	                        except ValueError:
   453	                            continue
   454	                        if not isinstance(entry, dict):
   455	                            continue
   456	                        pr_fields = [key for key in ("pr", "pr_number") if key in entry]
   457	                        matched = None
   458	                        if pr_fields:
   459	                            if expected_pr and all(pr_number(entry[key]) == expected_pr for key in pr_fields):
   460	                                matched = f"{pr_fields[0]}={expected_pr}"
   461	                        elif merge_sha and entry.get("commit") == merge_sha:
   462	                            matched = f"commit={merge_sha}"
   463	                        if matched:
   464	                            relpath = os.path.relpath(path, repo_root)
   465	                            log(f"  Provenance receipt matched for PR #{pr_num}: {relpath}:{line_num} ({matched})")
   466	                            return
   467	            except (OSError, UnicodeError):
   468	                continue  # An unreadable receipt cannot establish attribution.
   469	    die(f"--gate failure: No provenance.jsonl or error_log.jsonl entry matches PR #{pr_num} "
   470	        "by pr/pr_number or exact merge commit in TESTS-RESULTS/", code=6)
   471	
   472	
   473	def validate_pre_merge_receipts(repo_root, head_sha, pr_num=None):
   474	    """Ensure a passing test receipt matching HEAD SHA or PR number is COMMITTED in Git tree (GH-496)."""
   475	    try:
   476	        tree_files = subprocess.check_output(
   477	            ["git", "ls-tree", "-r", "--name-only", "HEAD", "TESTS-RESULTS/"],
   478	            cwd=repo_root,
   479	            text=True,
   480	            stderr=subprocess.DEVNULL,
   481	        ).splitlines()
   482	    except Exception:
   483	        tree_files = []
   484	
   485	    matching_receipts = [
   486	        f for f in tree_files
   487	        if f.endswith("provenance.jsonl") or f.endswith("error_log.jsonl")
   488	    ]
   489	    if not matching_receipts:
   490	        return f"No committed provenance.jsonl or error_log.jsonl receipts found under TESTS-RESULTS/ at HEAD {head_sha[:10]}."
   491	
   492	    try:
   493	        recent_shas = subprocess.check_output(
   494	            ["git", "log", "-n", "10", "--format=%H", "HEAD"],
   495	            cwd=repo_root,
   496	            text=True,
   497	            stderr=subprocess.DEVNULL,
   498	        ).splitlines()
   499	    except Exception:
   500	        recent_shas = [head_sha]
   501	    recent_shas_lower = set(s.lower() for s in recent_shas)
   502	
   503	    found_match = False
   504	    expected_pr = str(pr_num) if pr_num else None
   505	    for receipt_rel in matching_receipts:
   506	        try:
   507	            content = subprocess.check_output(
   508	                ["git", "show", f"HEAD:{receipt_rel}"],
   509	                cwd=repo_root,
   510	                text=True,
   511	                stderr=subprocess.DEVNULL,
   512	            )
   513	            for line in content.splitlines():
   514	                if not line.strip():
   515	                    continue
   516	                try:
   517	                    entry = json.loads(line)
   518	                except ValueError:
   519	                    continue
   520	                if not isinstance(entry, dict):
   521	                    continue
   522	                c_val = str(entry.get("commit") or "").lower()
   523	                c_len = len(c_val)
   524	                commit_match = bool(
   525	                    c_val
   526	                    and (
   527	                        (c_len >= 7 and head_sha.lower().startswith(c_val))
   528	                        or c_val == head_sha.lower()
   529	                        or (c_len >= 7 and any(s.startswith(c_val) for s in recent_shas_lower))
   530	                        or any(s == c_val for s in recent_shas_lower)
   531	                    )
   532	                )
   533	                pr_match = False
   534	                if expected_pr:
   535	                    pr_val = str(entry.get("pr") or entry.get("pr_number") or "")
   536	                    if pr_val == expected_pr:
   537	                        pr_match = True
   538	                if commit_match or pr_match:
   539	                    res = entry.get("result") or entry.get("status")
   540	                    rc = entry.get("rc")
   541	                    if res in ("pass", "passed", "PASS") or rc == 0:
   542	                        found_match = True
   543	                        break
   544	            if found_match:
   545	                break
   546	        except Exception:
   547	            continue
   548	
   549	    if not found_match:
   550	        target = f"PR #{pr_num}" if pr_num else f"commit {head_sha[:10]}"
   551	        return f"No committed passing test receipt at HEAD matches {target} in TESTS-RESULTS/ (AGENTS.md: uncommitted provenance is not proof)."
   552	    return None
   553	
   554	
   555	# GH-271: closing-keyword clause + trailing title tag decide LINKAGE (what a merged PR may
   556	# complete); bare mentions are references only. The #-or-GH- prefix is mandatory in both —
   557	# "closes 5 issues" must not extract issue 5 — and keywords must sit on the same line as the
   558	# ref, so a title ending in "fixed" cannot capture a body that opens with "#123".
   559	CLOSING_KEYWORD_CLAUSE = re.compile(
   560	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   561	    r"((?:#|GH-)[0-9]{1,6}\b"
   562	    r"(?:(?:[ \t]*,[ \t]*(?:and[ \t]+)?|[ \t]+and[ \t]+)(?:#|GH-)[0-9]{1,6}\b)*)",
   563	    re.IGNORECASE,
   564	)
   565	REF_IN_CLAUSE = re.compile(r"(?:#|GH-)([0-9]{1,6})\b", re.IGNORECASE)
   566	# GH-429: GitHub also honours a closing keyword followed by the issue's full URL. Captured as
   567	# (slug, number); extract_linked_issues keeps only the target repo's own slug, because
   568	# fetch_issue_state and find_active_doc_for_issue key on the bare number and a foreign repo's
   569	# "Closes https://github.com/other/repo/issues/7" must not promote this repo's GH-7.
   570	CLOSING_KEYWORD_URL = re.compile(
   571	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   572	    r"https?://github\.com/([\w.\-]+/[\w.\-]+?)/issues/([0-9]{1,6})\b",
   573	    re.IGNORECASE,
   574	)
   575	# A `#N`/`GH-N` inside a URL (fragment `/#123`, path `/GH-123`, query `?#123`, `?issue=#123`,
   576	# `&#123`) is part of the link, not a reference — GH-271 QA rounds 1+3. The lookbehind is one
   577	# fixed-width character class.
   578	MENTION = re.compile(r"(?<![A-Za-z0-9_/?.=&])(?:[Gg][Hh]-|#)([0-9]{1,6})\b")
   579	TITLE_TRAILER = re.compile(
   580	    r"\([ \t]*((?:(?:#|GH-)[0-9]{1,6}\b[ \t]*(?:[,;][ \t]*)?)+)[ \t]*\)[ \t]*$",
   581	    re.IGNORECASE,
   582	)
   583	CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
   584	INLINE_CODE = re.compile(r"`[^`\n]*`")
   585	
   586	
   587	def _strip_code_blocks(text):
   588	    """GitHub ignores closing keywords inside code; so does the reconciler."""
   589	    return INLINE_CODE.sub(" ", CODE_FENCE.sub(" ", text))
   590	
   591	
   592	def extract_linked_issues(pr_meta, repo_slug=None):
   593	    """Split a PR's issue references into (closers, mentions) — GH-271.
   594	
   595	    closers: refs introduced by a GitHub closing keyword (close/closes/closed/fix/fixes/
   596	    fixed/resolve/resolves/resolved) before a #- or GH--prefixed number, comma lists
   597	    included, plus a trailing "(#N)"/"(GH-N)" title tag. These mirror GitHub's own linking
   598	    rules — extended to the repo's GH-N spelling, since PRs merge into `development` and
   599	    the reconciler parses text rather than relying on default-branch auto-close — and are
   600	    eligible for every reconciler action (promotion when the issue is closed, evidence +
   601	    stays-active when open).
   602	
   603	    mentions: bare GH-N/#N references in prose. The old extractor treated every mention as
   604	    a link (PR #185's body yielded ten "linked" issues, two of them live active lanes), so
   605	    a mention now only ever records merge evidence on an OPEN issue's active doc — never a
   606	    promotion, ROADMAP move, or doc relocation.
   607	
   608	    Both lists are deduplicated and sorted.
   609	    """
   610	    title = _strip_code_blocks(pr_meta.get("title") or "").strip()
   611	    body = _strip_code_blocks(pr_meta.get("body") or "")
   612	    closers, mentions = set(), set()
   613	
   614	    scan_text = title + "\n" + body
   615	    for m in CLOSING_KEYWORD_CLAUSE.finditer(scan_text):
   616	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(m.group(1)))
   617	    if repo_slug:
   618	        closers.update(int(n) for slug, n in CLOSING_KEYWORD_URL.findall(scan_text)
   619	                       if slug.lower() == repo_slug.lower())
   620	    trailer = TITLE_TRAILER.search(title)
   621	    if trailer:
   622	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(trailer.group(1)))
   623	
   624	    mentions.update(int(n) for n in MENTION.findall(scan_text))
   625	    mentions -= closers
   626	    return sorted(closers), sorted(mentions)
   627	
   628	
   629	def find_active_doc_for_issue(repo_root, issue_num):
   630	    """Find matching active doc in PROJECT/2-WORKING/."""
   631	    working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
   632	    if not os.path.isdir(working_dir):
   633	        return None
   634	    for fname in os.listdir(working_dir):
   635	        if not fname.endswith(".md"):
   636	            continue
   637	        # Match GH-123-*.md or 123-*.md
   638	        if re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
   639	            return os.path.join(working_dir, fname)
   640	    return None
   641	
   642	
   643	def parse_doc_frontmatter(doc_path):
   644	    """Parse key-value pairs from document YAML frontmatter."""
   645	    if not doc_path or not os.path.isfile(doc_path):
   646	        return {}
   647	    try:
   648	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   649	            lines = f.readlines()
   650	        if not lines or lines[0].strip() != "---":
   651	            return {}
   652	        fm = {}
   653	        for line in lines[1:]:
   654	            if line.strip() == "---":
   655	                break
   656	            if ":" in line:
   657	                k, v = line.split(":", 1)
   658	                fm[k.strip().lower()] = v.strip().strip("'\"").lower()
   659	        return fm
   660	    except Exception:
   661	        return {}
   662	
   663	
   664	def validate_lessons_learned(content, doc_name):
   665	    """Assert ## Lessons Learned section exists and contains substantive content (GH-496)."""
   666	    m = re.search(r"##\s+Lessons\s+Learned.*?(?=\n##\s+(?!#)|\Z)", content, re.IGNORECASE | re.DOTALL)
   667	    if not m:
   668	        return f"Doc {doc_name} is missing mandatory '## Lessons Learned (For Future Agents)' section."
   669	
   670	    section_text = m.group(0)
   671	    lines = section_text.splitlines()
   672	    body_lines = lines[1:]
   673	
   674	    # Strip HTML comments
   675	    clean_body = re.sub(r"<!--.*?-->", "", "\n".join(body_lines), flags=re.DOTALL)
   676	
   677	    substantive_lines = []
   678	    for line in clean_body.splitlines():
   679	        trimmed = line.strip()
   680	        if not trimmed:
   681	            continue
   682	        # Check for empty placeholder markers
   683	        if re.match(r"^(?:[-*]\s*)?(?:TODO\b.*|TBD\b.*|None(?:\s+yet)?|N/A|\[.*?\]|\[?\s*\]?)$", trimmed, re.IGNORECASE):
   684	            continue
   685	        substantive_lines.append(trimmed)
   686	
   687	    if not substantive_lines:
   688	        return f"Doc {doc_name} has empty/placeholder '## Lessons Learned' section. Substantive reflections are required before closeout."
   689	    return None
   690	
   691	
   692	def validate_frontmatter_schema(doc_path):
   693	    """Validate YAML frontmatter against required PDDA schema (GH-496)."""
   694	    doc_name = os.path.basename(doc_path)
   695	    if not os.path.isfile(doc_path):
   696	        return f"Doc {doc_name} does not exist."
   697	    try:
   698	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   699	            content = f.read()
   700	    except Exception as e:
   701	        return f"Cannot read {doc_name}: {e}"
   702	
   703	    lines = content.splitlines()
   704	    if not lines or lines[0].strip() != "---":
   705	        return f"Doc {doc_name} missing opening YAML frontmatter delimiter ('---') at line 1."
   706	
   707	    closing_idx = -1
   708	    for i, line in enumerate(lines[1:], 1):
   709	        if line.strip() == "---":
   710	            closing_idx = i
   711	            break
   712	
   713	    if closing_idx == -1:
   714	        return f"Doc {doc_name} missing closing YAML frontmatter delimiter ('---')."
   715	
   716	    fm = {}
   717	    for line in lines[1:closing_idx]:
   718	        line = line.strip()
   719	        if not line or line.startswith("#"):
   720	            continue
   721	        if ":" in line:
   722	            k, v = line.split(":", 1)
   723	            fm[k.strip().lower()] = v.strip().strip("'\"")
   724	
   725	    required_keys = ["title", "status", "created", "updated", "owner", "goal"]
   726	    missing = [k for k in required_keys if not fm.get(k)]
   727	    if missing:
   728	        return f"Doc {doc_name} frontmatter missing required field(s): {', '.join(missing)}"
   729	
   730	    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
   731	    for date_key in ("created", "updated"):
   732	        val = fm.get(date_key, "")
   733	        val_date = val.split()[0] if val else ""
   734	        if not date_re.match(val_date):
   735	            return f"Doc {doc_name} frontmatter field '{date_key}' has invalid date format: '{val}' (expected YYYY-MM-DD)."
   736	
   737	    return None
   738	
   739	
   740	def validate_and_update_doc(doc_path, pr_meta, is_merged=True, dry_run=False, journal=None):
   741	    """Assert ## Lessons Learned, update frontmatter, and compute destination path."""
   742	    with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   743	        content = f.read()
   744	
   745	    merged_at = pr_meta.get("mergedAt")
   746	    if merged_at:
   747	        try:
   748	            ship_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00")).strftime(
   749	                "%Y-%m-%d"
   750	            )
   751	        except Exception:
   752	            ship_date = datetime.now().strftime("%Y-%m-%d")
   753	    else:
   754	        ship_date = datetime.now().strftime("%Y-%m-%d")
   755	
   756	    if is_merged:
   757	        # Assert lessons learned section exists and has substantive content for merged docs (GH-496)
   758	        ll_err = validate_lessons_learned(content, os.path.basename(doc_path))
   759	        if ll_err:
   760	            die(ll_err, code=5)
   760	            die(ll_err, code=5)
   761	
   762	        new_status = "Complete"
   763	        dest_folder = "3-COMPLETED"
   764	    else:
   765	        # Unmerged / declined / closed without merge -> route to 4-MISC
   766	        new_status = "Declined"
   767	        dest_folder = "4-MISC"
   768	
   769	    # Update frontmatter status and updated date
   770	    new_content = re.sub(
   771	        r"^status:\s*.*$", f"status: {new_status}", content, flags=re.MULTILINE | re.IGNORECASE
   772	    )
   773	    new_content = re.sub(
   774	        r"^updated:\s*.*$", f"updated: {ship_date}", new_content, flags=re.MULTILINE | re.IGNORECASE
   775	    )
   776	
   777	    dest_dir = os.path.join(os.path.dirname(os.path.dirname(doc_path)), dest_folder)
   778	    dest_path = os.path.join(dest_dir, os.path.basename(doc_path))
   779	    print("TRANSITION " + json.dumps(["doc", "move", os.path.basename(doc_path), dest_folder, ship_date]), flush=True)
   780	
   781	    if not dry_run:
   782	        if journal:
   783	            journal.snapshot(doc_path)
   784	            # GH-271: a destination that already exists (an earlier reconciliation promoted
   785	            # this doc and was committed) is an overwrite, not a creation — snapshot it too,
   786	            # or rollback's unlink leaves a tracked path deleted in porcelain.
   787	            if os.path.exists(dest_path):
   788	                journal.snapshot(dest_path)
   789	            journal.track_created(dest_path)
   790	        os.makedirs(dest_dir, exist_ok=True)
   791	        with open(dest_path, "w", encoding="utf-8") as f:
   792	            f.write(new_content)
   793	        os.unlink(doc_path)
   794	
   795	    return dest_path, ship_date
   796	
   797	def ledger_rows(repo_root, sql, params=()):
   798	    """Read the existing ledger without creating a DB or silently hiding schema errors."""
   799	    db = Path(repo_root) / "releases.db"
   800	    if not db.is_file():
   801	        return []
   802	    # Some legacy adopters carry an empty placeholder; their markdown remains authoritative.
   803	    mode = Path(repo_root, ".pdda-mode")
   804	    releases_mode = mode.is_file() and "ROADMAP_SOURCE=releases" in mode.read_text()
   805	    if db.stat().st_size == 0 and not releases_mode:
   806	        return []
   807	    try:
   808	        conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
   809	        try:
   810	            conn.row_factory = sqlite3.Row
   811	            return [dict(row) for row in conn.execute(sql, params)]
   812	        finally:
   813	            conn.close()
   814	    except sqlite3.Error as exc:
   815	        die(f"Cannot read reconciliation ledger: {exc}", code=6)
   816	
   817	
   818	def ledger_write(repo_root, args, dry_run=False, journal=None):
   819	    # Both paths emit the same stable intent; dry-run never calls a mutating CLI.
   820	    # In particular repoint --dry-run requires a destination that preview has not created.
   821	    print("TRANSITION " + json.dumps(args, ensure_ascii=False), flush=True)
   822	    if dry_run:
   823	        return
   824	    snapshot_ledger_artifacts(repo_root, journal=journal)
   825	    cmd = ["python3", harness_tool(repo_root, "utils/py/releases_app.py"), "--root", repo_root, *args]
   826	    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)
   827	    if result.returncode:
   828	        die(f"{' '.join(args[:2])} failed (exit {result.returncode}): {result.stderr}\n{result.stdout}", code=6)
   829	
   830	
   831	def manifest_members(repo_root, repo_slug):
   832	    rows = ledger_rows(repo_root, """SELECT r.global_id AS release_gid, i.url
   833	        FROM manifest_items m JOIN releases r ON r.id=m.release_id
   834	        JOIN issue_refs i ON i.id=m.issue_ref_id WHERE m.state='dialed_in'""")
   835	    if rows and not repo_slug:
   836	        die("Cannot resolve repository identity for manifest lookup", code=6)
   837	    members = []
   838	    for row in rows:
   839	        match = re.fullmatch(r"https://github.com/([^/]+/[^/]+)/issues/([1-9][0-9]*)", row["url"] or "")
   840	        if match and match[1].lower() == repo_slug.lower():
   841	            members.append(dict(row, issue=int(match[2])))
   842	    return members
   843	
   844	
   845	def ship_manifest_items(repo_root, issue_num, pr_meta, repo_slug, dry_run=False, journal=None):
   846	    for member in manifest_members(repo_root, repo_slug):
   847	        if member["issue"] != issue_num:
   848	            continue
   849	        sha = (pr_meta.get("mergeCommit") or {}).get("oid", "")
   850	        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
   851	            die(f"PR #{pr_meta.get('number')} has no full merge commit for manifest evidence", code=6)
   852	        ledger_write(repo_root, ["manifest", "ship", "--gid", member["release_gid"],
   853	                     member["url"], "--evidence", sha], dry_run, journal)
   854	
   855	
   856	def catch_up_prs(repo_root, repo_slug, offline_manifest=None):
   857	    """Derive drift from committed state; no PR watermark or auxiliary ledger.
   858	
   859	    Timeline pagination recovers closing PRs even outside an arbitrary recent-PR window.
   860	    Only merged development PRs whose closers match the closed issue qualify.
   861	    """
   862	    issues = {m["issue"] for m in manifest_members(repo_root, repo_slug)}
   863	    # Roadmap-only drift survives when a doc was archived or a manifest already shipped.
   864	    # Terminal rows must drop out again so successful catch-up remains idempotent.
   865	    for row in ledger_rows(repo_root,
   866	            "SELECT gh_number, issue_url FROM roadmap_items WHERE gh_number IS NOT NULL "
   867	            "AND section NOT IN (?, ?)", ("Completed", "Deferred · vision")):
   868	        expected = f"https://github.com/{repo_slug}/issues/{row['gh_number']}"
   869	        if repo_slug and (row["issue_url"] or "").lower() == expected.lower():
   870	            issues.add(row["gh_number"])
   871	    for path in Path(repo_root, "PROJECT/2-WORKING").glob("GH-*.md"):
   872	        match = re.match(r"GH-([0-9]+)-", path.name)
   873	        if match:
   874	            issues.add(int(match[1]))
   875	    found = set()
   876	    for issue in sorted(issues):
   877	        if fetch_issue_state(repo_root, issue, offline_manifest) != "CLOSED":
   878	            continue
   879	        if offline_manifest is not None:
   880	            candidates = offline_manifest.get("prs", [])
   881	        else:
   882	            result = subprocess.run(["gh", "api", "--paginate", "--slurp",
   883	                f"repos/{repo_slug}/issues/{issue}/timeline?per_page=100"],
   884	                cwd=repo_root, capture_output=True, text=True, check=False)
   885	            if result.returncode:
   886	                die(f"Catch-up timeline for GH-{issue} failed: {result.stderr}", code=6)
   887	            numbers = set()
   888	            for page in json.loads(result.stdout):
   889	                for event in page:
   890	                    referenced = (event.get("source") or {}).get("issue") or {}
   891	                    if referenced.get("pull_request") and referenced.get("repository_url", "").lower() == (
   892	                        f"https://api.github.com/repos/{repo_slug}".lower()):
   893	                        numbers.add(referenced["number"])
   894	            candidates = [fetch_pr_metadata(repo_root, n) for n in sorted(numbers)]
   895	        matches = [pr for pr in candidates if pr.get("state", "").upper() == "MERGED"
   896	                   and pr.get("baseRefName") == "development"
   897	                   and issue in extract_linked_issues(pr, repo_slug)[0]]
   898	        if not matches:
   899	            die(f"Closed GH-{issue} has reconciliation drift but no attributable merged development PR", code=6)
   900	        # The most recent closing PR owns the current lifecycle transition.
   901	        found.add(str(max(matches, key=lambda pr: (pr.get("mergedAt") or "", pr["number"]))["number"]))
   902	    return sorted(found, key=int)
   903	
   904	
   905	def update_roadmap_entry(repo_root, issue_num, landing, ship_date, is_merged=True, dry_run=False, journal=None, doc_path=None):
   906	    """Move entry in ROADMAP.md and/or releases.db to Completed/Deferred section with shipping badge."""
   907	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
   908	    db_path = os.path.join(repo_root, "releases.db")
   909	    target_section_md = "### Completed" if is_merged else "### Deferred / cancelled"
   910	    target_section_db = "Completed" if is_merged else "Deferred · vision"
   911	    badge_sub = f"✅ **SHIPPED {ship_date} ({landing})**" if is_merged else f"🛑 **DECLINED {ship_date} ({landing})**"
   912	
   913	    updated = False
   914	
   915	    # GH-421: read desired state first; every write uses the existing receipt-backed CLI.
   916	    if os.path.isfile(db_path):
   917	        rows = ledger_rows(repo_root, "SELECT * FROM roadmap_items WHERE gh_number = ?", (issue_num,))
   918	        if rows:
   919	            row = rows[0]
   920	            raw_text = row["raw_text"] or ""
   921	            title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", raw_text)
   922	            title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num} · {row['title']}"
   923	            rest = raw_text.split("—", 1)[1] if "—" in raw_text else " " + (
   924	                raw_text[title_match.end():].strip() if title_match else raw_text)
   925	            if doc_path and row["doc_path"]:
   926	                rest = rest.replace(row["doc_path"], doc_path)
   927	            new_raw_text = f"- **{title_part}** {badge_sub} —{rest}".strip()
   928	            marker = "✅" if is_merged else "⛔"
   929	            if doc_path and row["doc_path"] != doc_path:
   930	                ledger_write(repo_root, ["roadmap", "repoint", "--issue-num", str(issue_num),
   931	                             "--doc-path", doc_path], dry_run, journal)
   932	            if (row["section"], row["status_marker"], raw_text) != (target_section_db, marker, new_raw_text):
   933	                ledger_write(repo_root, ["roadmap", "update", "--issue-num", str(issue_num),
   934	                             "--section", target_section_db, "--status-marker", marker,
   935	                             "--raw-text", new_raw_text], dry_run, journal)
   936	            updated = True
   937	
   938	    # 2. Update ROADMAP.md if present (legacy mode)
   939	    if os.path.isfile(roadmap_path):
   940	        with open(roadmap_path, "r", encoding="utf-8", errors="replace") as f:
   941	            lines = f.readlines()
   942	
   943	        entry_pattern = re.compile(rf"^-\s+\*\*GH-{issue_num}\b")
   944	        starts = [i for i, line in enumerate(lines) if entry_pattern.search(line)]
   945	        if not starts:
   946	            log(f"No entry found in ROADMAP.md for GH-{issue_num} (skipping roadmap move)")
   947	            return updated
   948	
   949	        blocks = []
   950	        for start_idx in starts:
   951	            end_idx = len(lines)
   952	            for j in range(start_idx + 1, len(lines)):
   953	                if lines[j].startswith("- **") or lines[j].startswith("### ") or lines[j].startswith("## "):
   954	                    end_idx = j
   955	                    break
   956	            blocks.append((start_idx, end_idx, lines[start_idx:end_idx]))
   957	
   958	        expected_marker = "SHIPPED" if is_merged else "DECLINED"
   959	        canonical = next(
   960	            (block for _, _, block in blocks if expected_marker in block[0]),
   961	            blocks[0][2],
   962	        )
   963	        block_lines = list(canonical)
   964	        first_line = block_lines[0]
   965	
   966	        if len(blocks) == 1 and expected_marker in first_line:
   967	            log(f"GH-{issue_num} is already marked {expected_marker} in ROADMAP.md")
   968	            return True
   969	
   970	        title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", first_line)
   971	        title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num}"
   972	
   973	        if "—" in first_line:
   974	            rest = first_line.split("—", 1)[1]
   975	        else:
   976	            after_title = first_line[title_match.end():] if title_match else first_line
   977	            rest = re.sub(r"^(?:\s*✅\s*(?:\*\*.*?\*\*)?|\s*🚧\s*(?:\*\*.*?\*\*)?|\s*🛑\s*(?:\*\*.*?\*\*)?|\s*)", "", after_title)
   978	            if not rest.startswith(" ") and rest != "\n" and rest != "":
   979	                rest = " " + rest
   980	            if not rest.endswith("\n"):
   981	                rest += "\n"
   982	
   983	        new_first_line = f"- **{title_part}** {badge_sub} —{rest}"
   984	        block_lines[0] = new_first_line
   985	
   986	        removed = set()
   987	        for start_idx, end_idx, _ in blocks:
   988	            removed.update(range(start_idx, end_idx))
   989	        new_lines = [line for idx, line in enumerate(lines) if idx not in removed]
   990	
   991	        target_idx = None
   992	        for k, line in enumerate(new_lines):
   993	            if line.strip() == target_section_md:
   994	                target_idx = k
   995	                break
   996	
   997	        if target_idx is None and not is_merged:
   998	            target_section_md = "### Completed"
   999	            for k, line in enumerate(new_lines):
  1000	                if line.strip() == target_section_md:
  1001	                    target_idx = k
  1002	                    break
  1003	
  1004	        if target_idx is None:
  1005	            die(f"Could not find '{target_section_md}' section in ROADMAP.md", code=5)
  1006	
  1007	        insert_pos = target_idx + 1
  1008	        new_lines = new_lines[:insert_pos] + block_lines + new_lines[insert_pos:]
  1009	
  1010	        if not dry_run:
  1011	            if journal:
  1012	                journal.snapshot(roadmap_path)
  1013	            with open(roadmap_path, "w", encoding="utf-8") as f:
  1014	                f.writelines(new_lines)
  1015	
  1016	        updated = True
  1017	
  1018	    return updated
  1019	
  1020	
  1021	def fix_mangled_roadmap_entries(repo_root, dry_run=False, journal=None):
  1022	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
  1023	    if not os.path.isfile(roadmap_path):
  1024	        return
  1025	    with open(roadmap_path, "r", encoding="utf-8") as f:
  1026	        lines = f.readlines()
  1027	    changed = False
  1028	    for i, line in enumerate(lines):
  1029	        if line.startswith("- **") and " ** " in line:
  1030	            new_line = re.sub(r"^-\s+\*\*(GH-\d+)\s+\*\*", r"- **\1**", line)
  1031	            if new_line != line:
  1032	                lines[i] = new_line
  1033	                changed = True
  1034	    if changed and not dry_run:
  1035	        if journal:
  1036	            journal.snapshot(roadmap_path)
  1037	        with open(roadmap_path, "w", encoding="utf-8") as f:
  1038	            f.writelines(lines)
  1039	
  1040	
  1041	def marathon_plan_findings(output, returncode):
  1042	    """Return exit-driving structured findings emitted by marathon-plan."""
  1043	    drift_types = {"already-landed", "already-closed"}
  1044	    held_types = {
  1045	        "unrated", "needs-doc", "needs-contract", "note-only",
  1046	        "not-ready", "blocked", "blocked-dep",
  1047	    }
  1048	    relevant_types = drift_types if returncode == 4 else held_types
  1049	    findings = []
  1050	    for line in output.splitlines():
  1051	        try:
  1052	            finding = json.loads(line)
  1053	        except (json.JSONDecodeError, TypeError):
  1054	            continue
  1055	        check = str(finding.get("check", ""))
  1056	        finding_type = check.split("/", 1)[1] if "/" in check else check
  1057	        if finding_type in relevant_types:
  1058	            findings.append(finding)
  1059	    return findings
  1060	
  1061	
  1062	def finding_issue_numbers(finding):
  1063	    """Extract issue identities from a planner finding without guessing by title."""
  1064	    file_name = str(finding.get("file", ""))
  1065	    evidence = " ".join(str(finding.get(key, "")) for key in ("file", "message", "action"))
  1066	    numbers = {
  1067	        int(number)
  1068	        for number in re.findall(r"(?:GH-|issue\s+#|#)([0-9]{1,6})\b", evidence, re.IGNORECASE)
  1069	    }
  1070	    # Active-doc lookup also supports the legacy `123-title.md` filename shape.
  1071	    legacy_doc = re.match(r"^(?:GH-)?([0-9]{1,6})(?:[^0-9]|$)", os.path.basename(file_name), re.IGNORECASE)
  1072	    if legacy_doc:
  1073	        numbers.add(int(legacy_doc.group(1)))
  1074	    return numbers
  1075	
  1076	
  1077	def describe_finding(finding):
  1078	    """Produce a stable, operator-readable held-item label."""
  1079	    issue_nums = sorted(finding_issue_numbers(finding))
  1080	    file_name = str(finding.get("file", "")).strip()
  1081	    identity = ", ".join(f"GH-{number}" for number in issue_nums)
  1082	    if identity and file_name:
  1083	        return f"{identity} ({file_name})"
  1084	    if identity:
  1085	        return identity
  1086	    if file_name:
  1087	        return file_name
  1088	    return str(finding.get("message", "")).strip() or "unidentified planner item"
  1089	
  1090	
  1091	def handle_marathon_plan_result(result, reconciled_issues):
  1092	    """Scope planner drift/held failures to the issues reconciled in this run."""
  1093	    if result.returncode == 0:
  1094	        return
  1095	    if result.returncode not in (4, 5):
  1096	        die(
  1097	            f"Subprocess 'marathon-plan.sh' failed with exit {result.returncode}:\n"
  1098	            f"{result.stderr}\n{result.stdout}",
  1099	            code=6,
  1100	        )
  1101	
  1102	    findings = marathon_plan_findings(result.stdout, result.returncode)
  1103	    if not findings:
  1104	        # Preserve GH-202 compatibility with older/stub planners that expose only
  1105	        # the exit-5 contract. Exit 4 must remain attributable and therefore
  1106	        # fails closed when structured evidence is absent.
  1107	        if result.returncode == 5:
  1108	            log("  marathon-plan reports items held (exit 5) without structured findings — continuing (GH-202 compatibility)")
  1109	            return
  1110	        die("marathon-plan reported drift (exit 4) without attributable structured findings", code=6)
  1111	
  1112	    reconciled = {int(issue) for issue in reconciled_issues}
  1113	    owned = [
  1114	        finding for finding in findings
  1115	        if finding_issue_numbers(finding) & reconciled
  1116	    ]
  1117	    unrelated = [finding for finding in findings if finding not in owned]
  1118	
  1119	    if owned:
  1120	        labels = ", ".join(describe_finding(finding) for finding in owned)
  1121	        die(
  1122	            "marathon-plan found drift/held state attributable to the reconciled "
  1123	            f"PR item(s): {labels}",
  1124	            code=6,
  1125	        )
  1126	
  1127	    log("  WARNING — marathon-plan found pre-existing unrelated drift/held items; keeping reconciliation:")
  1128	    for finding in unrelated:
  1129	        log(f"    - {describe_finding(finding)}")
  1130	
  1131	
  1132	def snapshot_ledger_artifacts(repo_root, dry_run=False, journal=None):
  1133	    """GH-424: capture the ledger and generated views BEFORE the first write.
  1134	
  1135	    Repeated calls retain the original state, including originally absent artifacts.
  1136	    Both per-issue writes and downstream regeneration use this same snapshot set.
  1137	    """
  1138	    if dry_run or journal is None:
  1139	        return
  1140	    for name in (
  1141	        "releases.db", "releases.sql", "RELEASES.generated.md",
  1142	        "ROADMAP-DASHBOARD.md", "RELEASES-PREVIEW.html",
  1143	        "LEADERBOARD.html", "LEADERBOARD.md",
  1144	        os.path.join(".tick", "marathon-plan.fingerprint"),
  1145	    ):
  1146	        path = os.path.abspath(os.path.join(repo_root, name))
  1147	        if path in journal.backups or path in journal.created_files:
  1148	            continue
  1149	        if os.path.exists(path):
  1150	            journal.snapshot(path)
  1151	        else:
  1152	            journal.track_created(path)
  1153	
  1154	
  1155	def compute_marathon_planner_fingerprint(repo_root):
  1156	    """Compute a SHA256 digest of canonical marathon inputs to avoid redundant replanning (GH-496)."""
  1157	    h = hashlib.sha256()
  1158	    db_path = os.path.join(repo_root, "releases.db")
  1159	    if os.path.isfile(db_path):
  1160	        try:
  1161	            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
  1162	            cur = conn.cursor()
  1163	            cur.execute("SELECT global_id, gh_number, title, section, position, complexity, risk, effort FROM roadmap_items ORDER BY global_id")
  1164	            for row in cur.fetchall():
  1165	                h.update(str(row).encode("utf-8"))
  1166	            conn.close()
  1167	        except Exception:
  1168	            pass
  1169	
  1170	    working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
  1171	    if os.path.isdir(working_dir):
  1172	        for fname in sorted(os.listdir(working_dir)):
  1173	            if fname.endswith(".md") and not fname.startswith("MARATHON-PLAN-"):
  1174	                h.update(fname.encode("utf-8"))
  1175	
  1176	    planner_src = harness_tool(repo_root, "utils/py/marathon_plan.py")
  1177	    if os.path.isfile(planner_src):
  1178	        try:
  1179	            with open(planner_src, "rb") as f:
  1180	                h.update(f.read())
  1180	                h.update(f.read())
  1181	        except Exception:
  1182	            pass
  1183	    return h.hexdigest()
  1184	
  1185	
  1186	def run_subprocesses(repo_root, dry_run=False, journal=None, reconciled_issues=None):
  1187	    """Orchestrate releases sync, view exports, and marathon replanning with DB rollback protection."""
  1188	    log("Running downstream database sync and dashboard regeneration...")
  1189	
  1190	    snapshot_ledger_artifacts(repo_root, dry_run=dry_run, journal=journal)
  1191	
  1192	    def _plan_docs():
  1193	        found = set()
  1194	        for pattern in ("MARATHON-PLAN-*.md", os.path.join("PROJECT", "2-WORKING", "MARATHON-PLAN-*.md")):
  1195	            found.update(glob.glob(os.path.join(repo_root, pattern)))
  1196	        return found
  1197	
  1198	    pre_plan_docs = _plan_docs() if not dry_run else set()
  1199	    if journal and not dry_run:
  1200	        # Codex consult: a same-dated plan doc that already exists gets OVERWRITTEN by the
  1201	        # replan, and tracking-only-created would leave rollback no bytes to restore.
  1202	        for existing_doc in pre_plan_docs:
  1203	            journal.snapshot(existing_doc)
  1204	
  1205	    # GH-358: resolve each harness tool against the repo first, then the harness home. On a
  1206	    # vendored install these five live only under <repo>/.xyz/ and every one was unreachable,
  1207	    # so the reconciler died on its first downstream step.
  1208	    releases_app = harness_tool(repo_root, "utils/py/releases_app.py")
  1209	    sync_cmd = ["python3", releases_app, "--root", repo_root, "roadmap", "sync"]
  1210	    check_cmd = ["python3", releases_app, "--root", repo_root, "check"]
  1211	    timeline_cmd = ["python3", harness_tool(repo_root, "utils/timeline/export_timeline.py"), "--preview"]
  1212	    dash_cmd = ["bash", harness_tool(repo_root, "utils/roadmap-dashboard.sh")]
  1213	    lb_cmd = ["bash", harness_tool(repo_root, "utils/leaderboard.sh")]
  1214	    plan_cmd = ["bash", harness_tool(repo_root, "utils/marathon-plan.sh"), "--format", "json"]
  1215	
  1216	    if dry_run:
  1217	        sync_cmd.append("--dry-run")
  1218	        plan_cmd.append("--dry-run")
  1219	
  1220	    steps = [
  1221	        ("releases roadmap sync", sync_cmd),
  1222	        ("releases check", check_cmd),
  1223	    ]
  1224	    skip_marathon = False
  1225	    fp_dir = os.path.join(repo_root, ".tick")
  1226	    fp_file = os.path.join(fp_dir, "marathon-plan.fingerprint")
  1227	    plan_fp = compute_marathon_planner_fingerprint(repo_root)
  1228	
  1229	    if not dry_run:
  1230	        # GH-474: RELEASES-PREVIEW.html is an ADOPTED view — opt-in by presence.
  1231	        if os.path.exists(os.path.join(repo_root, "RELEASES-PREVIEW.html")):
  1232	            steps.append(("export_timeline.py --preview", timeline_cmd))
  1233	        else:
  1234	            log("  (skipping export_timeline.py --preview — RELEASES-PREVIEW.html is not adopted here)")
  1235	        steps.append(("roadmap-dashboard.sh", dash_cmd))
  1236	        if os.path.exists(os.path.join(repo_root, "LEADERBOARD.md")):
  1237	            if os.path.exists(harness_tool(repo_root, "utils/leaderboard.sh")):
  1238	                steps.append(("leaderboard.sh", lb_cmd))
  1239	            else:
  1240	                log("  (skipping leaderboard.sh — utils/leaderboard.sh not found)")
  1241	        else:
  1242	            log("  (skipping leaderboard.sh — LEADERBOARD.md is not adopted here)")
  1243	
  1244	        has_plan = bool(glob.glob(os.path.join(repo_root, "PROJECT", "2-WORKING", "MARATHON-PLAN-*.md"))) or bool(glob.glob(os.path.join(repo_root, "MARATHON-PLAN-*.md")))
  1245	        if has_plan and os.path.isfile(fp_file):
  1246	            try:
  1247	                with open(fp_file, "r") as f:
  1248	                    if f.read().strip() == plan_fp:
  1249	                        skip_marathon = True
  1250	            except Exception:
  1251	                pass
  1252	
  1253	        if skip_marathon:
  1254	            log("  (skipping marathon-plan.sh — canonical inputs unchanged)")
  1255	        else:
  1256	            steps.append(("marathon-plan.sh", plan_cmd))
  1257	    else:
  1258	        steps.append(("marathon-plan.sh --dry-run", plan_cmd))
  1259	
  1260	    # GH-271: registration of created views/plan docs must happen even when a step DIES —
  1261	    # the marathon-plan failure path raises from inside the loop, and a post-loop pass
  1262	    # would never run, which is exactly how the stray MARATHON-PLAN escaped rollback.
  1263	    try:
  1264	        for name, cmd in steps:
  1265	            log(f"  -> {name}")
  1266	            # GH-429 / GH-496: dashboard and leaderboard paths
  1267	            step_env = dict(
  1268	                os.environ,
  1269	                ROADMAP_DASHBOARD_ROOT=str(repo_root),
  1270	                LEADERBOARD_DB=str(os.path.join(repo_root, "releases.db")),
  1271	                LEADERBOARD_OUTPUT=str(os.path.join(repo_root, "LEADERBOARD.md")),
  1272	            )
  1273	            r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False, env=step_env)
  1274	            if name.startswith("marathon-plan"):
  1275	                handle_marathon_plan_result(r, reconciled_issues or set())
  1276	            elif r.returncode != 0:
  1277	                die(f"Subprocess '{name}' failed with exit {r.returncode}:\n{r.stderr}\n{r.stdout}", code=6)
  1278	
  1279	        if not dry_run and not skip_marathon:
  1280	            try:
  1281	                os.makedirs(fp_dir, exist_ok=True)
  1282	                with open(fp_file, "w") as f:
  1283	                    f.write(plan_fp)
  1284	            except Exception:
  1285	                pass
  1286	    finally:
  1287	        if journal and not dry_run:
  1288	            for plan_doc in _plan_docs() - pre_plan_docs:
  1289	                journal.track_created(plan_doc)
  1290	
  1291	
  1292	def run_validation_gate(repo_root):
  1293	    """Run pdda doc-health verification gate."""
  1294	    log("Running PDDA doc-hygiene gate...")
  1295	    gate_cmd = ["bash", "utils/pdda-local-checks.sh"] if os.path.exists(os.path.join(repo_root, "utils", "pdda-local-checks.sh")) else ["bash", "utils/pdda/pdda.sh"]
  1296	    r = subprocess.run(
  1297	        gate_cmd,
  1298	        cwd=repo_root,
  1299	        capture_output=True,
  1300	        text=True,
  1301	        check=False,
  1302	    )
  1303	    # GH-429: the exit status IS the consuming repo's enforcement decision — pdda-lib.sh makes
  1304	    # `observe`/`light` exit 0 and `full` exit non-zero on errors. Grepping stdout for ERROR
  1305	    # overrode that mode and made a live reconciliation impossible on any repo with a standing
  1306	    # observe-mode backlog. Block on the status; surface the findings when it reports but passes.
  1307	    if r.returncode != 0:
  1308	        die(f"PDDA validation gate failed:\n{r.stdout}", code=7)
  1309	    if "ERROR" in r.stdout:
  1310	        found = re.search(r"(\d+) error\(s\) found", r.stdout)
  1311	        count = found.group(1) if found else "some"
  1312	        log(f"  WARNING — pdda reported {count} finding(s) but exited 0 (repo enforcement mode is not blocking); continuing")
  1313	
  1314	
  1315	def run_pre_merge(repo_root, args):
  1316	    """Execute pre-merge validation checks for PR or current branch (GH-496)."""
  1317	    log("Running pre-merge closeout checks...")
  1318	    try:
  1319	        head_sha = subprocess.check_output(
  1320	            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
  1321	        ).strip()
  1322	    except Exception as e:
  1323	        die(f"Cannot determine HEAD SHA: {e}", code=2)
  1324	
  1325	    pr_num = None
  1326	    pr_title = ""
  1327	    pr_body = ""
  1328	    if args.pr:
  1329	        pr_num = args.pr[0]
  1330	        try:
  1331	            r = subprocess.run(
  1332	                ["gh", "pr", "view", str(pr_num), "--json", "number,title,body,headRefOid"],
  1333	                cwd=repo_root,
  1334	                capture_output=True,
  1335	                text=True,
  1336	                timeout=10,
  1337	            )
  1338	            if r.returncode == 0:
  1339	                data = json.loads(r.stdout)
  1340	                pr_title = data.get("title", "")
  1341	                pr_body = data.get("body", "")
  1342	                head_sha = data.get("headRefOid") or head_sha
  1343	        except Exception:
  1344	            pass
  1345	
  1346	    if not pr_title and not pr_body:
  1347	        try:
  1348	            commits_text = subprocess.check_output(
  1349	                ["git", "log", "-n", "10", "--format=%B"],
  1350	                cwd=repo_root,
  1351	                text=True,
  1352	            )
  1353	            pr_title = commits_text.splitlines()[0] if commits_text else ""
  1354	            pr_body = commits_text
  1355	        except Exception:
  1356	            pass
  1357	
  1358	    repo_slug = github_slug_from_origin(repo_root)
  1359	    closers, mentions = extract_linked_issues({"title": pr_title, "body": pr_body}, repo_slug=repo_slug)
  1360	    log(f"  Target: {('PR #' + str(pr_num)) if pr_num else head_sha[:10]}")
  1361	    log(f"  Closing issues detected: {closers or '(none)'}")
  1362	
  1363	    diff_docs = []
  1364	    try:
  1365	        diff_status = subprocess.check_output(
  1366	            ["git", "diff", "--name-status", "HEAD~1..HEAD"],
  1367	            cwd=repo_root,
  1368	            text=True,
  1369	        ).splitlines()
  1370	        for dline in diff_status:
  1371	            parts = dline.split()
  1372	            if len(parts) >= 2:
  1373	                for p in parts[1:]:
  1374	                    if "PROJECT/2-WORKING/" in p and p.endswith(".md"):
  1375	                        diff_docs.append(os.path.join(repo_root, p))
  1376	    except Exception:
  1377	        pass
  1378	
  1379	    target_docs = set()
  1380	    errors = []
  1381	
  1382	    for issue_num in closers:
  1383	        working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
  1384	        matches = []
  1385	        if os.path.isdir(working_dir):
  1386	            for fname in sorted(os.listdir(working_dir)):
  1387	                if fname.endswith(".md") and re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
  1388	                    matches.append(os.path.join(working_dir, fname))
  1389	        if len(matches) > 1:
  1390	            errors.append(f"Ambiguous active doc match for issue #{issue_num}: {', '.join(os.path.basename(m) for m in matches)}")
  1391	        elif len(matches) == 1:
  1392	            target_docs.add(matches[0])
  1393	        else:
  1394	            completed_dir = os.path.join(repo_root, "PROJECT", "3-COMPLETED")
  1395	            comp_matches = [
  1396	                os.path.join(completed_dir, f)
  1397	                for f in os.listdir(completed_dir)
  1398	                if f.endswith(".md") and re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", f, re.IGNORECASE)
  1399	            ] if os.path.isdir(completed_dir) else []
  1400	            if comp_matches:
  1401	                target_docs.add(comp_matches[0])
  1402	
  1403	    for d in diff_docs:
  1404	        if os.path.isfile(d):
  1405	            target_docs.add(d)
  1406	
  1407	    log(f"  Active docs evaluated: {[os.path.basename(d) for d in sorted(target_docs)] or '(none)'}")
  1408	
  1409	    doc_contract_failed = False
  1410	    for doc_path in sorted(target_docs):
  1411	        doc_name = os.path.basename(doc_path)
  1412	        # 1. Frontmatter
  1413	        fm_err = validate_frontmatter_schema(doc_path)
  1414	        if fm_err:
  1415	            errors.append(fm_err)
  1416	            doc_contract_failed = True
  1417	
  1418	        # 2. Lessons Learned
  1419	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
  1420	            content = f.read()
  1421	        ll_err = validate_lessons_learned(content, doc_name)
  1422	        if ll_err:
  1423	            errors.append(ll_err)
  1424	            doc_contract_failed = True
  1425	
  1426	    # 3. Test receipts
  1427	    receipt_err = validate_pre_merge_receipts(repo_root, head_sha, pr_num)
  1428	    if receipt_err:
  1429	        errors.append(receipt_err)
  1430	
  1431	    if errors:
  1432	        log_err("Pre-merge validation FAILED with the following error(s):")
  1433	        for e in errors:
  1434	            log_err(f"  - {e}")
  1435	        exit_code = 5 if doc_contract_failed else 6
  1436	        sys.exit(exit_code)
  1437	
  1438	    log("Pre-merge validation PASSED! ✅")
  1439	    sys.exit(0)
  1440	
  1441	
  1442	def main():
  1443	    parser = argparse.ArgumentParser(
  1444	        description="wave_reconcile.py — Canonical Post-Merge Wave & Marathon Lifecycle Reconciler"
  1445	    )
  1446	    parser.add_argument(
  1447	        "--root",
  1448	        help="Target repository root path (default: current working directory)",
  1449	    )
  1450	    parser.add_argument(
  1451	        "--pr",
  1452	        nargs="+",
  1453	        help="One or more merged PR numbers/IDs to reconcile",
  1454	    )
  1455	    parser.add_argument(
  1456	        "--commit",
  1457	        nargs="+",
  1458	        help="One or more commits landed directly on development to reconcile",
  1459	    )
  1460	    parser.add_argument(
  1461	        "--marathon",
  1462	        help="Marathon identifier / milestone name",
  1463	    )
  1464	    parser.add_argument(
  1465	        "--manifest",
  1466	        help="Path to structured JSON reconciliation manifest",
  1467	    )
  1468	    parser.add_argument(
  1469	        "--dry-run",
  1470	        action="store_true",
  1471	        help="Hermetic preview: assert zero file/DB/ref mutations",
  1472	    )
  1473	    parser.add_argument(
  1474	        "--offline",
  1475	        help="Run without network using offline JSON manifest cache",
  1476	    )
  1477	    parser.add_argument(
  1478	        "--skip-pull",
  1479	        action="store_true",
  1480	        help="Skip git pull --ff-only origin development (for testing/isolated clones)",
  1481	    )
  1482	    parser.add_argument(
  1483	        "--skip-branch-check",
  1484	        action="store_true",
  1485	        help="Skip active branch check (for tests on feature branches)",
  1486	    )
  1487	    parser.add_argument(
  1488	        "--allow-dirty",
  1489	        action="store_true",
  1490	        help="Allow dirty working tree (for test fixtures only)",
  1491	    )
  1492	    parser.add_argument(
  1493	        "--force-promote",
  1494	        action="store_true",
  1495	        help="Force promotion of active docs and roadmap entries to Completed regardless of linked issue OPEN state",
  1496	    )
  1497	    parser.add_argument(
  1498	        "--gate",
  1499	        "--require-receipts",
  1500	        action="store_true",
  1501	        dest="require_receipts",
  1502	        help="Require a receipt matching each PR number or exact merge commit before closeout (GH-425)",
  1503	    )
  1504	    parser.add_argument(
  1505	        "--pre-merge",
  1506	        action="store_true",
  1507	        help="Run read-only pre-merge checks on closing active docs (frontmatter, lessons learned, test receipts) (GH-496)",
  1508	    )
  1509	    parser.add_argument(
  1510	        "--force-local-reconcile",
  1511	        action="store_true",
  1512	        help="Bypass hosted in-flight reconciler check for emergency local reconciliation (GH-496)",
  1513	    )
  1514	
  1515	    parser.add_argument("--catch-up", action="store_true", help="Recover closed-issue drift from committed docs and manifest")
  1516	
  1517	    args = parser.parse_args()
  1518	
  1519	    repo_root = os.path.abspath(args.root) if args.root else resolve_repo_root()
  1520	
  1521	    if args.pre_merge:
  1522	        run_pre_merge(repo_root, args)
  1523	        return
  1524	
  1525	    lock_file = os.path.join(repo_root, ".git", "wave-reconcile.lock")
  1526	    journal = RollbackJournal()
  1527	    baseline = None
  1528	
  1529	    try:
  1530	        if args.force_local_reconcile and os.environ.get("GITHUB_ACTIONS") == "true":
  1531	            die("--force-local-reconcile is prohibited inside GITHUB_ACTIONS", code=2)
  1532	
  1533	        # Preflight phase
  1534	        log(f"Starting wave reconciliation (dry_run={args.dry_run}, root={repo_root})")
  1535	        baseline = check_porcelain_cleanliness(repo_root, allow_dirty=(args.allow_dirty or args.dry_run))
  1536	        check_current_branch(repo_root, skip_branch_check=args.skip_branch_check)
  1537	
  1538	        repo_slug = github_slug_from_origin(repo_root)
  1539	        has_workflow = os.path.isfile(os.path.join(repo_root, ".github", "workflows", "wave-reconcile.yml"))
  1540	        if not args.offline and not args.dry_run and os.environ.get("GITHUB_ACTIONS") != "true":

exec
/bin/zsh -lc "rg -n \"def (validate_frontmatter_schema|validate_lessons_learned|validate_pre_merge_receipts|compute_marathon_planner_fingerprint|run_pre_merge)|generation|marathon-plan.fingerprint|pre-merge\" utils/py/wave_reconcile.py utils/py/releases_app.py utils/py/harness_app.py utils/py/jog_run.py test/gh496-phase2-reconciliation-views.sh PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md; nl -ba utils/py/wave_reconcile.py | sed -n '900,1125p'; nl -ba utils/py/wave_reconcile.py | sed -n '1515,1595p'; nl -ba utils/py/harness_app.py | sed -n '1850,2070p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 0ms:
test/gh496-phase2-reconciliation-views.sh:4:# 2. Deterministic pre-merge closeout checks (--pre-merge: frontmatter, lessons learned, receipts)
test/gh496-phase2-reconciliation-views.sh:190:goal: Verify pre-merge checks
test/gh496-phase2-reconciliation-views.sh:195:Testing pre-merge checks.
test/gh496-phase2-reconciliation-views.sh:269:# Reset working repo state for pre-merge checks
test/gh496-phase2-reconciliation-views.sh:289:# Part 2: Pre-Merge Validation Checks (--pre-merge)
test/gh496-phase2-reconciliation-views.sh:292:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:308:goal: Verify pre-merge checks
test/gh496-phase2-reconciliation-views.sh:319:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:334:goal: Verify pre-merge checks
test/gh496-phase2-reconciliation-views.sh:345:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:362:goal: Verify pre-merge checks
test/gh496-phase2-reconciliation-views.sh:374:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:386:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:394:rm -f "$REPO/planner_calls.log" "$REPO/.tick/marathon-plan.fingerprint"
test/gh496-phase2-reconciliation-views.sh:404:[ -f "$REPO/.tick/marathon-plan.fingerprint" ] || fail "Fingerprint file not created at .tick/marathon-plan.fingerprint"
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:83:- [x] Minimize marathon plan regeneration in `wave_reconcile.py` via input fingerprinting (`.tick/marathon-plan.fingerprint`).
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:86:- [x] `utils/roadmap-dashboard.sh` and `utils/leaderboard.sh` query `releases.db` settings and stamp `<!-- releases-app generation: <N> -->` on line 1.
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:92:- [x] Add read-only `--pre-merge` check to `wave_reconcile.py` validating `## Lessons Learned`, frontmatter schema, and test receipts on closing docs before merge.
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:93:- [x] Red control: doc missing `## Lessons Learned` or containing only placeholders fails pre-merge check with exit code 5.
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:94:- [x] Red control: doc missing required frontmatter schema fields fails pre-merge check with exit code 5.
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:95:- [x] Red control: missing committed passing test receipt at HEAD fails pre-merge check with exit code 6.
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md:107:- [x] Committed `ROADMAP-DASHBOARD.md` and `LEADERBOARD.md` identify their ledger generation.
utils/py/jog_run.py:386:    Mirrors the verification family `jog land` performs post-merge, adapted to pre-merge:
utils/py/jog_run.py:1416:    """GH-300: minimal pre-merge guard for the relay-path landing boundary.
utils/py/wave_reconcile.py:473:def validate_pre_merge_receipts(repo_root, head_sha, pr_num=None):
utils/py/wave_reconcile.py:664:def validate_lessons_learned(content, doc_name):
utils/py/wave_reconcile.py:692:def validate_frontmatter_schema(doc_path):
utils/py/wave_reconcile.py:1136:    Both per-issue writes and downstream regeneration use this same snapshot set.
utils/py/wave_reconcile.py:1144:        os.path.join(".tick", "marathon-plan.fingerprint"),
utils/py/wave_reconcile.py:1155:def compute_marathon_planner_fingerprint(repo_root):
utils/py/wave_reconcile.py:1188:    log("Running downstream database sync and dashboard regeneration...")
utils/py/wave_reconcile.py:1226:    fp_file = os.path.join(fp_dir, "marathon-plan.fingerprint")
utils/py/wave_reconcile.py:1315:def run_pre_merge(repo_root, args):
utils/py/wave_reconcile.py:1316:    """Execute pre-merge validation checks for PR or current branch (GH-496)."""
utils/py/wave_reconcile.py:1317:    log("Running pre-merge closeout checks...")
utils/py/wave_reconcile.py:1505:        "--pre-merge",
utils/py/wave_reconcile.py:1507:        help="Run read-only pre-merge checks on closing active docs (frontmatter, lessons learned, test receipts) (GH-496)",
utils/py/wave_reconcile.py:1696:            # GH-421: skip downstream regeneration only when there was genuinely nothing to
utils/py/releases_app.py:36:                                 the DB/dump/digest/generation contract, so a refused writer
utils/py/releases_app.py:144:GENERATION_KEY = "generation"
utils/py/releases_app.py:159:# deny-by-default allowlist: `generation` belongs to the writer protocol and `repo_slug` is the
utils/py/releases_app.py:471:def get_generation(conn):
utils/py/releases_app.py:612:  state_digest_after TEXT NOT NULL     --   op_receipts, lock_audit, generation, and all digest
utils/py/releases_app.py:1034:def dump_text(conn, generation, include_receipts=True, include_generation=True):
utils/py/releases_app.py:1035:    """Canonical logical dump. include_receipts=False, include_generation=False yields exactly
utils/py/releases_app.py:1036:    the BUSINESS-STATE text the receipt digests hash (r3: excluding op_receipts, generation and
utils/py/releases_app.py:1045:    if include_generation:
utils/py/releases_app.py:1046:        w("-- generation: %d" % generation)
utils/py/releases_app.py:1058:    if not include_generation:
utils/py/releases_app.py:1225:    text = dump_text(conn, generation=0, include_receipts=False, include_generation=False)
utils/py/releases_app.py:1229:def dump_generation_from_text(text):
utils/py/releases_app.py:1231:        m = re.match(r"^-- generation: (\d+)$", line.strip())
utils/py/releases_app.py:1237:# ── generation marker in the generated file ─────────────────────────────────────────────────────
utils/py/releases_app.py:1242:GEN_MARKER_RE = re.compile(r"^<!-- releases-app generation: (\d+) -->$")
utils/py/releases_app.py:1245:def gen_marker(generation):
utils/py/releases_app.py:1246:    return "<!-- releases-app generation: %d -->" % generation
utils/py/releases_app.py:1320:      write intent journal (txn_id, NEXT generation, planned outputs)   [BEFORE the DB commit]
utils/py/releases_app.py:1321:      -> BEGIN IMMEDIATE -> mutate -> stamp generation into settings -> COMMIT
utils/py/releases_app.py:1322:      -> stage dump (+ generated view when one exists), each carrying that generation
utils/py/releases_app.py:1338:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1346:            "generation": generation, "planned_outputs": planned,
utils/py/releases_app.py:1371:                               (str(generation), now, GENERATION_KEY))
utils/py/releases_app.py:1374:                             (GENERATION_KEY, str(generation), now))
utils/py/releases_app.py:1377:                               (str(generation), GENERATION_KEY))
utils/py/releases_app.py:1380:                             (GENERATION_KEY, str(generation)))
utils/py/releases_app.py:1391:        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
utils/py/releases_app.py:1394:                                        gen_marker(generation) + "\n" + render_ledger(conn)),
utils/py/releases_app.py:1426:        -> stamp generation + op_receipt -> COMMIT
utils/py/releases_app.py:1459:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1466:            "generation": generation, "planned_outputs": planned, "db": paths["db"],
utils/py/releases_app.py:1485:                                   (str(generation), now, GENERATION_KEY))
utils/py/releases_app.py:1488:                                 (GENERATION_KEY, str(generation), now))
utils/py/releases_app.py:1491:                                   (str(generation), GENERATION_KEY))
utils/py/releases_app.py:1494:                                 (GENERATION_KEY, str(generation)))
utils/py/releases_app.py:1513:        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
utils/py/releases_app.py:1516:                                        gen_marker(generation) + "\n" + render_ledger(conn)),
utils/py/releases_app.py:1526:        print("migrated %s to schema version %d (applied %s; generation %d)"
utils/py/releases_app.py:1527:              % (DB_NAME, max(pending), ", ".join(str(v) for v in pending), generation))
utils/py/releases_app.py:1544:    lock — this function must not take it again). pre-COMMIT (DB generation < journal's):
utils/py/releases_app.py:1546:    boundary (DB generation == journal's): the DB is truth; REGENERATE the dump and generated
utils/py/releases_app.py:1557:    jgen = int(journal.get("generation", 0))
utils/py/releases_app.py:1575:    db_gen = get_generation(conn)
utils/py/releases_app.py:1606:           "DB generation %d is ahead of the journal's %d — state is not interpretable; inspect "
utils/py/releases_app.py:1964:            generation = get_generation(conn)
utils/py/releases_app.py:1965:            _atomic_write(paths["dump"], dump_text(conn, generation))
utils/py/releases_app.py:1970:    print("initialized %s (slug %r, enforcement=lenient, generation 1); canonical dump at %s"
utils/py/releases_app.py:3515:    dashboard guard sees a clean regeneration range on the next push.
utils/py/releases_app.py:3556:    writable: `generation` is owned by the writer protocol and `repo_slug` is identity, and letting
utils/py/releases_app.py:3949:            print(summary + " — already in sync; no write, generation unchanged")
utils/py/releases_app.py:3984:        print(summary + " (txn %s, generation %d)" % (txn[:12], get_generation(conn)))
utils/py/releases_app.py:4551:        generation = get_generation(conn)
utils/py/releases_app.py:4552:        _atomic_write(paths["gen"], gen_marker(generation) + "\n" + render_ledger(conn))
utils/py/releases_app.py:4554:        print("generated %s (side-by-side, generation %d) + drift report %s"
utils/py/releases_app.py:4555:              % (paths["gen"], generation, paths["drift"]))
utils/py/releases_app.py:4629:            db_gen = get_generation(conn)
utils/py/releases_app.py:4635:                dump_gen = dump_generation_from_text(dump_content)
utils/py/releases_app.py:4637:                    fail("generation-mismatch",
utils/py/releases_app.py:4638:                         "settings.generation=%d but %s says %s — write in progress, crashed, or "
utils/py/releases_app.py:4651:                print("OK: generation trio consistent at %d (DB <-> dump)" % db_gen)
utils/py/releases_app.py:4659:                    fail("generation-mismatch",
utils/py/releases_app.py:4660:                         "%s carries generation %s but the DB is at %d — regenerate with "
utils/py/releases_app.py:4663:                    print("OK: %s generation marker matches (%d)" % (GEN_NAME, db_gen))
utils/py/releases_app.py:4806:                resolved = {"dump-divergence", "dump-missing", "generation-mismatch",
utils/py/releases_app.py:4905:    branches made unequal numbers of writes, keep BOTH `-- generation:` headers with no conflict
utils/py/releases_app.py:4913:               if re.match(r"^-- generation: \d+$", ln.strip())]
utils/py/releases_app.py:4915:        refuse("dump-multi-generation",
utils/py/releases_app.py:4916:               "the dump carries %d '-- generation:' headers (%s); a canonical dump has exactly one. "
utils/py/releases_app.py:4919:               "silently understate the generation. Keep the HIGHEST header, delete the rest, then "
utils/py/releases_app.py:4945:                   "(for 'generation', the higher value), delete the other, then rebuild." % key)
utils/py/releases_app.py:5169:    dump_gen = dump_generation_from_text(dump_content)
utils/py/releases_app.py:5171:        refuse("dump-generation", "%s carries no generation header — not a canonical dump"
utils/py/releases_app.py:5175:    old_gen = get_generation(conn)
utils/py/releases_app.py:5270:    print("rebuilt %s from %s (generation %d -> %d); displaced DB backed up at %s"
utils/py/releases_app.py:5287:        db_gen = get_generation(conn)
utils/py/releases_app.py:5295:                dump_gen = dump_generation_from_text(f.read())
utils/py/releases_app.py:5299:            staleness_banner = "<div style='background: red; color: white; padding: 10px; font-weight: bold;'>STALE SYNC: DB generation (%d) != Dump generation (%d)</div>" % (db_gen, dump_gen)
utils/py/releases_app.py:5428:                                             "(Phase 0+1: side-by-side generation only)")
utils/py/releases_app.py:5533:    sp = sub.add_parser("gen", help="side-by-side generation (Phase 0: NEVER writes RELEASES.md)")
   900	        # The most recent closing PR owns the current lifecycle transition.
   901	        found.add(str(max(matches, key=lambda pr: (pr.get("mergedAt") or "", pr["number"]))["number"]))
   902	    return sorted(found, key=int)
   903	
   904	
   905	def update_roadmap_entry(repo_root, issue_num, landing, ship_date, is_merged=True, dry_run=False, journal=None, doc_path=None):
   906	    """Move entry in ROADMAP.md and/or releases.db to Completed/Deferred section with shipping badge."""
   907	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
   908	    db_path = os.path.join(repo_root, "releases.db")
   909	    target_section_md = "### Completed" if is_merged else "### Deferred / cancelled"
   910	    target_section_db = "Completed" if is_merged else "Deferred · vision"
   911	    badge_sub = f"✅ **SHIPPED {ship_date} ({landing})**" if is_merged else f"🛑 **DECLINED {ship_date} ({landing})**"
   912	
   913	    updated = False
   914	
   915	    # GH-421: read desired state first; every write uses the existing receipt-backed CLI.
   916	    if os.path.isfile(db_path):
   917	        rows = ledger_rows(repo_root, "SELECT * FROM roadmap_items WHERE gh_number = ?", (issue_num,))
   918	        if rows:
   919	            row = rows[0]
   920	            raw_text = row["raw_text"] or ""
   921	            title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", raw_text)
   922	            title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num} · {row['title']}"
   923	            rest = raw_text.split("—", 1)[1] if "—" in raw_text else " " + (
   924	                raw_text[title_match.end():].strip() if title_match else raw_text)
   925	            if doc_path and row["doc_path"]:
   926	                rest = rest.replace(row["doc_path"], doc_path)
   927	            new_raw_text = f"- **{title_part}** {badge_sub} —{rest}".strip()
   928	            marker = "✅" if is_merged else "⛔"
   929	            if doc_path and row["doc_path"] != doc_path:
   930	                ledger_write(repo_root, ["roadmap", "repoint", "--issue-num", str(issue_num),
   931	                             "--doc-path", doc_path], dry_run, journal)
   932	            if (row["section"], row["status_marker"], raw_text) != (target_section_db, marker, new_raw_text):
   933	                ledger_write(repo_root, ["roadmap", "update", "--issue-num", str(issue_num),
   934	                             "--section", target_section_db, "--status-marker", marker,
   935	                             "--raw-text", new_raw_text], dry_run, journal)
   936	            updated = True
   937	
   938	    # 2. Update ROADMAP.md if present (legacy mode)
   939	    if os.path.isfile(roadmap_path):
   940	        with open(roadmap_path, "r", encoding="utf-8", errors="replace") as f:
   941	            lines = f.readlines()
   942	
   943	        entry_pattern = re.compile(rf"^-\s+\*\*GH-{issue_num}\b")
   944	        starts = [i for i, line in enumerate(lines) if entry_pattern.search(line)]
   945	        if not starts:
   946	            log(f"No entry found in ROADMAP.md for GH-{issue_num} (skipping roadmap move)")
   947	            return updated
   948	
   949	        blocks = []
   950	        for start_idx in starts:
   951	            end_idx = len(lines)
   952	            for j in range(start_idx + 1, len(lines)):
   953	                if lines[j].startswith("- **") or lines[j].startswith("### ") or lines[j].startswith("## "):
   954	                    end_idx = j
   955	                    break
   956	            blocks.append((start_idx, end_idx, lines[start_idx:end_idx]))
   957	
   958	        expected_marker = "SHIPPED" if is_merged else "DECLINED"
   959	        canonical = next(
   960	            (block for _, _, block in blocks if expected_marker in block[0]),
   961	            blocks[0][2],
   962	        )
   963	        block_lines = list(canonical)
   964	        first_line = block_lines[0]
   965	
   966	        if len(blocks) == 1 and expected_marker in first_line:
   967	            log(f"GH-{issue_num} is already marked {expected_marker} in ROADMAP.md")
   968	            return True
   969	
   970	        title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", first_line)
   971	        title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num}"
   972	
   973	        if "—" in first_line:
   974	            rest = first_line.split("—", 1)[1]
   975	        else:
   976	            after_title = first_line[title_match.end():] if title_match else first_line
   977	            rest = re.sub(r"^(?:\s*✅\s*(?:\*\*.*?\*\*)?|\s*🚧\s*(?:\*\*.*?\*\*)?|\s*🛑\s*(?:\*\*.*?\*\*)?|\s*)", "", after_title)
   978	            if not rest.startswith(" ") and rest != "\n" and rest != "":
   979	                rest = " " + rest
   980	            if not rest.endswith("\n"):
   981	                rest += "\n"
   982	
   983	        new_first_line = f"- **{title_part}** {badge_sub} —{rest}"
   984	        block_lines[0] = new_first_line
   985	
   986	        removed = set()
   987	        for start_idx, end_idx, _ in blocks:
   988	            removed.update(range(start_idx, end_idx))
   989	        new_lines = [line for idx, line in enumerate(lines) if idx not in removed]
   990	
   991	        target_idx = None
   992	        for k, line in enumerate(new_lines):
   993	            if line.strip() == target_section_md:
   994	                target_idx = k
   995	                break
   996	
   997	        if target_idx is None and not is_merged:
   998	            target_section_md = "### Completed"
   999	            for k, line in enumerate(new_lines):
  1000	                if line.strip() == target_section_md:
  1001	                    target_idx = k
  1002	                    break
  1003	
  1004	        if target_idx is None:
  1005	            die(f"Could not find '{target_section_md}' section in ROADMAP.md", code=5)
  1006	
  1007	        insert_pos = target_idx + 1
  1008	        new_lines = new_lines[:insert_pos] + block_lines + new_lines[insert_pos:]
  1009	
  1010	        if not dry_run:
  1011	            if journal:
  1012	                journal.snapshot(roadmap_path)
  1013	            with open(roadmap_path, "w", encoding="utf-8") as f:
  1014	                f.writelines(new_lines)
  1015	
  1016	        updated = True
  1017	
  1018	    return updated
  1019	
  1020	
  1021	def fix_mangled_roadmap_entries(repo_root, dry_run=False, journal=None):
  1022	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
  1023	    if not os.path.isfile(roadmap_path):
  1024	        return
  1025	    with open(roadmap_path, "r", encoding="utf-8") as f:
  1026	        lines = f.readlines()
  1027	    changed = False
  1028	    for i, line in enumerate(lines):
  1029	        if line.startswith("- **") and " ** " in line:
  1030	            new_line = re.sub(r"^-\s+\*\*(GH-\d+)\s+\*\*", r"- **\1**", line)
  1031	            if new_line != line:
  1032	                lines[i] = new_line
  1033	                changed = True
  1034	    if changed and not dry_run:
  1035	        if journal:
  1036	            journal.snapshot(roadmap_path)
  1037	        with open(roadmap_path, "w", encoding="utf-8") as f:
  1038	            f.writelines(lines)
  1039	
  1040	
  1041	def marathon_plan_findings(output, returncode):
  1042	    """Return exit-driving structured findings emitted by marathon-plan."""
  1043	    drift_types = {"already-landed", "already-closed"}
  1044	    held_types = {
  1045	        "unrated", "needs-doc", "needs-contract", "note-only",
  1046	        "not-ready", "blocked", "blocked-dep",
  1047	    }
  1048	    relevant_types = drift_types if returncode == 4 else held_types
  1049	    findings = []
  1050	    for line in output.splitlines():
  1051	        try:
  1052	            finding = json.loads(line)
  1053	        except (json.JSONDecodeError, TypeError):
  1054	            continue
  1055	        check = str(finding.get("check", ""))
  1056	        finding_type = check.split("/", 1)[1] if "/" in check else check
  1057	        if finding_type in relevant_types:
  1058	            findings.append(finding)
  1059	    return findings
  1060	
  1061	
  1062	def finding_issue_numbers(finding):
  1063	    """Extract issue identities from a planner finding without guessing by title."""
  1064	    file_name = str(finding.get("file", ""))
  1065	    evidence = " ".join(str(finding.get(key, "")) for key in ("file", "message", "action"))
  1066	    numbers = {
  1067	        int(number)
  1068	        for number in re.findall(r"(?:GH-|issue\s+#|#)([0-9]{1,6})\b", evidence, re.IGNORECASE)
  1069	    }
  1070	    # Active-doc lookup also supports the legacy `123-title.md` filename shape.
  1071	    legacy_doc = re.match(r"^(?:GH-)?([0-9]{1,6})(?:[^0-9]|$)", os.path.basename(file_name), re.IGNORECASE)
  1072	    if legacy_doc:
  1073	        numbers.add(int(legacy_doc.group(1)))
  1074	    return numbers
  1075	
  1076	
  1077	def describe_finding(finding):
  1078	    """Produce a stable, operator-readable held-item label."""
  1079	    issue_nums = sorted(finding_issue_numbers(finding))
  1080	    file_name = str(finding.get("file", "")).strip()
  1081	    identity = ", ".join(f"GH-{number}" for number in issue_nums)
  1082	    if identity and file_name:
  1083	        return f"{identity} ({file_name})"
  1084	    if identity:
  1085	        return identity
  1086	    if file_name:
  1087	        return file_name
  1088	    return str(finding.get("message", "")).strip() or "unidentified planner item"
  1089	
  1090	
  1091	def handle_marathon_plan_result(result, reconciled_issues):
  1092	    """Scope planner drift/held failures to the issues reconciled in this run."""
  1093	    if result.returncode == 0:
  1094	        return
  1095	    if result.returncode not in (4, 5):
  1096	        die(
  1097	            f"Subprocess 'marathon-plan.sh' failed with exit {result.returncode}:\n"
  1098	            f"{result.stderr}\n{result.stdout}",
  1099	            code=6,
  1100	        )
  1101	
  1102	    findings = marathon_plan_findings(result.stdout, result.returncode)
  1103	    if not findings:
  1104	        # Preserve GH-202 compatibility with older/stub planners that expose only
  1105	        # the exit-5 contract. Exit 4 must remain attributable and therefore
  1106	        # fails closed when structured evidence is absent.
  1107	        if result.returncode == 5:
  1108	            log("  marathon-plan reports items held (exit 5) without structured findings — continuing (GH-202 compatibility)")
  1109	            return
  1110	        die("marathon-plan reported drift (exit 4) without attributable structured findings", code=6)
  1111	
  1112	    reconciled = {int(issue) for issue in reconciled_issues}
  1113	    owned = [
  1114	        finding for finding in findings
  1115	        if finding_issue_numbers(finding) & reconciled
  1116	    ]
  1117	    unrelated = [finding for finding in findings if finding not in owned]
  1118	
  1119	    if owned:
  1120	        labels = ", ".join(describe_finding(finding) for finding in owned)
  1121	        die(
  1122	            "marathon-plan found drift/held state attributable to the reconciled "
  1123	            f"PR item(s): {labels}",
  1124	            code=6,
  1125	        )
  1515	    parser.add_argument("--catch-up", action="store_true", help="Recover closed-issue drift from committed docs and manifest")
  1516	
  1517	    args = parser.parse_args()
  1518	
  1519	    repo_root = os.path.abspath(args.root) if args.root else resolve_repo_root()
  1520	
  1521	    if args.pre_merge:
  1522	        run_pre_merge(repo_root, args)
  1523	        return
  1524	
  1525	    lock_file = os.path.join(repo_root, ".git", "wave-reconcile.lock")
  1526	    journal = RollbackJournal()
  1527	    baseline = None
  1528	
  1529	    try:
  1530	        if args.force_local_reconcile and os.environ.get("GITHUB_ACTIONS") == "true":
  1531	            die("--force-local-reconcile is prohibited inside GITHUB_ACTIONS", code=2)
  1532	
  1533	        # Preflight phase
  1534	        log(f"Starting wave reconciliation (dry_run={args.dry_run}, root={repo_root})")
  1535	        baseline = check_porcelain_cleanliness(repo_root, allow_dirty=(args.allow_dirty or args.dry_run))
  1536	        check_current_branch(repo_root, skip_branch_check=args.skip_branch_check)
  1537	
  1538	        repo_slug = github_slug_from_origin(repo_root)
  1539	        has_workflow = os.path.isfile(os.path.join(repo_root, ".github", "workflows", "wave-reconcile.yml"))
  1540	        if not args.offline and not args.dry_run and os.environ.get("GITHUB_ACTIONS") != "true":
  1541	            if repo_slug and has_workflow:
  1542	                check_hosted_reconciler_in_flight(repo_root, repo_slug=repo_slug, force=args.force_local_reconcile)
  1543	
  1544	        if not args.skip_pull and not args.dry_run and not args.offline:
  1545	            pull_upstream(repo_root)
  1546	
  1547	        offline_manifest = None
  1548	        if args.offline:
  1549	            try:
  1550	                with open(args.offline, "r", encoding="utf-8") as f:
  1551	                    offline_manifest = json.load(f)
  1552	            except Exception as e:
  1553	                die(f"Failed loading offline manifest from {args.offline}: {e}", code=4)
  1554	
  1555	        landing_items = [("pr", value) for value in (args.pr or [])]
  1556	        landing_items.extend(("commit", value) for value in (args.commit or []))
  1557	        if args.manifest:
  1558	            try:
  1559	                with open(args.manifest, "r", encoding="utf-8") as f:
  1560	                    mdata = json.load(f)
  1561	                    landing_items.extend(("pr", str(p)) for p in mdata.get("prs", []))
  1562	            except Exception as e:
  1563	                die(f"Failed loading manifest from {args.manifest}: {e}", code=4)
  1564	
  1565	        if not landing_items and not args.marathon and not args.catch_up:
  1566	            die("No PRs, commits, or marathon specified. Pass --pr <N>..., --commit <SHA>..., --marathon <name>, or --catch-up", code=2)
  1567	
  1568	        with ReconcilerLock(lock_file):
  1569	            reconciled_issues = set()
  1570	            repo_slug = github_slug_from_origin(repo_root)  # GH-429: URL-form closers, this repo only
  1571	            if args.catch_up:
  1572	                landing_items.extend(("pr", str(n)) for n in catch_up_prs(repo_root, repo_slug, offline_manifest))
  1573	            landing_items = list(dict.fromkeys((kind, str(value)) for kind, value in landing_items))
  1574	            for landing_kind, landing_id in landing_items:
  1575	                if landing_kind == "commit":
  1576	                    pr_meta = fetch_commit_metadata(repo_root, landing_id, offline_manifest)
  1577	                else:
  1578	                    pr_meta = fetch_pr_metadata(repo_root, landing_id, offline_manifest, dry_run=args.dry_run)
  1579	                landing = landing_label(pr_meta)
  1580	                log(f"Processing {landing}...")
  1581	                state = pr_meta.get("state", "").upper()
  1582	                is_merged = (state == "MERGED")
  1583	
  1584	                if not is_merged:
  1585	                    log(f"  {landing} state is '{state}' (unmerged/declined) -> routing to 4-MISC/")
  1586	
  1587	                base_ref = pr_meta.get("baseRefName", "")
  1588	                if base_ref and base_ref != "development":
  1589	                    die(
  1590	                        f"{landing} target base is '{base_ref}', not 'development'.",
  1591	                        code=4,
  1592	                    )
  1593	
  1594	                linked_issues, mentioned_issues = extract_linked_issues(pr_meta, repo_slug=repo_slug)
  1595	                # GH-425: unconditional whenever --gate/--require-receipts is requested — this

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '430,735p'; nl -ba test/gh496-phase2-reconciliation-views.sh | sed -n '270,431p'; nl -ba utils/py/harness_app.py | sed -n '350,470p'; nl -ba utils/py/jog_run.py | sed -n '360,430p'; nl -ba utils/py/jog_run.py | sed -n '1380,1460p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 0ms:
   430	        if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
   431	            return value
   432	        return None
   433	
   434	    expected_pr = pr_number(pr_num)
   435	    merge_commit = pr_meta.get("mergeCommit") or {}
   436	    merge_sha = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
   437	    if not isinstance(merge_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", merge_sha):
   438	        merge_sha = None
   439	    for root, dirs, files in os.walk(results_dir):
   440	        dirs.sort()
   441	        for name in sorted(files):
   442	            if name not in ("error_log.jsonl", "provenance.jsonl"):
   443	                continue
   444	            path = os.path.join(root, name)
   445	            if os.path.islink(path) or not os.path.isfile(path):
   446	                continue
   447	            try:
   448	                with open(path, encoding="utf-8") as receipt:
   449	                    for line_num, line in enumerate(receipt, 1):
   450	                        try:
   451	                            entry = json.loads(line)
   452	                        except ValueError:
   453	                            continue
   454	                        if not isinstance(entry, dict):
   455	                            continue
   456	                        pr_fields = [key for key in ("pr", "pr_number") if key in entry]
   457	                        matched = None
   458	                        if pr_fields:
   459	                            if expected_pr and all(pr_number(entry[key]) == expected_pr for key in pr_fields):
   460	                                matched = f"{pr_fields[0]}={expected_pr}"
   461	                        elif merge_sha and entry.get("commit") == merge_sha:
   462	                            matched = f"commit={merge_sha}"
   463	                        if matched:
   464	                            relpath = os.path.relpath(path, repo_root)
   465	                            log(f"  Provenance receipt matched for PR #{pr_num}: {relpath}:{line_num} ({matched})")
   466	                            return
   467	            except (OSError, UnicodeError):
   468	                continue  # An unreadable receipt cannot establish attribution.
   469	    die(f"--gate failure: No provenance.jsonl or error_log.jsonl entry matches PR #{pr_num} "
   470	        "by pr/pr_number or exact merge commit in TESTS-RESULTS/", code=6)
   471	
   472	
   473	def validate_pre_merge_receipts(repo_root, head_sha, pr_num=None):
   474	    """Ensure a passing test receipt matching HEAD SHA or PR number is COMMITTED in Git tree (GH-496)."""
   475	    try:
   476	        tree_files = subprocess.check_output(
   477	            ["git", "ls-tree", "-r", "--name-only", "HEAD", "TESTS-RESULTS/"],
   478	            cwd=repo_root,
   479	            text=True,
   480	            stderr=subprocess.DEVNULL,
   481	        ).splitlines()
   482	    except Exception:
   483	        tree_files = []
   484	
   485	    matching_receipts = [
   486	        f for f in tree_files
   487	        if f.endswith("provenance.jsonl") or f.endswith("error_log.jsonl")
   488	    ]
   489	    if not matching_receipts:
   490	        return f"No committed provenance.jsonl or error_log.jsonl receipts found under TESTS-RESULTS/ at HEAD {head_sha[:10]}."
   491	
   492	    try:
   493	        recent_shas = subprocess.check_output(
   494	            ["git", "log", "-n", "10", "--format=%H", "HEAD"],
   495	            cwd=repo_root,
   496	            text=True,
   497	            stderr=subprocess.DEVNULL,
   498	        ).splitlines()
   499	    except Exception:
   500	        recent_shas = [head_sha]
   501	    recent_shas_lower = set(s.lower() for s in recent_shas)
   502	
   503	    found_match = False
   504	    expected_pr = str(pr_num) if pr_num else None
   505	    for receipt_rel in matching_receipts:
   506	        try:
   507	            content = subprocess.check_output(
   508	                ["git", "show", f"HEAD:{receipt_rel}"],
   509	                cwd=repo_root,
   510	                text=True,
   511	                stderr=subprocess.DEVNULL,
   512	            )
   513	            for line in content.splitlines():
   514	                if not line.strip():
   515	                    continue
   516	                try:
   517	                    entry = json.loads(line)
   518	                except ValueError:
   519	                    continue
   520	                if not isinstance(entry, dict):
   521	                    continue
   522	                c_val = str(entry.get("commit") or "").lower()
   523	                c_len = len(c_val)
   524	                commit_match = bool(
   525	                    c_val
   526	                    and (
   527	                        (c_len >= 7 and head_sha.lower().startswith(c_val))
   528	                        or c_val == head_sha.lower()
   529	                        or (c_len >= 7 and any(s.startswith(c_val) for s in recent_shas_lower))
   530	                        or any(s == c_val for s in recent_shas_lower)
   531	                    )
   532	                )
   533	                pr_match = False
   534	                if expected_pr:
   535	                    pr_val = str(entry.get("pr") or entry.get("pr_number") or "")
   536	                    if pr_val == expected_pr:
   537	                        pr_match = True
   538	                if commit_match or pr_match:
   539	                    res = entry.get("result") or entry.get("status")
   540	                    rc = entry.get("rc")
   541	                    if res in ("pass", "passed", "PASS") or rc == 0:
   542	                        found_match = True
   543	                        break
   544	            if found_match:
   545	                break
   546	        except Exception:
   547	            continue
   548	
   549	    if not found_match:
   550	        target = f"PR #{pr_num}" if pr_num else f"commit {head_sha[:10]}"
   551	        return f"No committed passing test receipt at HEAD matches {target} in TESTS-RESULTS/ (AGENTS.md: uncommitted provenance is not proof)."
   552	    return None
   553	
   554	
   555	# GH-271: closing-keyword clause + trailing title tag decide LINKAGE (what a merged PR may
   556	# complete); bare mentions are references only. The #-or-GH- prefix is mandatory in both —
   557	# "closes 5 issues" must not extract issue 5 — and keywords must sit on the same line as the
   558	# ref, so a title ending in "fixed" cannot capture a body that opens with "#123".
   559	CLOSING_KEYWORD_CLAUSE = re.compile(
   560	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   561	    r"((?:#|GH-)[0-9]{1,6}\b"
   562	    r"(?:(?:[ \t]*,[ \t]*(?:and[ \t]+)?|[ \t]+and[ \t]+)(?:#|GH-)[0-9]{1,6}\b)*)",
   563	    re.IGNORECASE,
   564	)
   565	REF_IN_CLAUSE = re.compile(r"(?:#|GH-)([0-9]{1,6})\b", re.IGNORECASE)
   566	# GH-429: GitHub also honours a closing keyword followed by the issue's full URL. Captured as
   567	# (slug, number); extract_linked_issues keeps only the target repo's own slug, because
   568	# fetch_issue_state and find_active_doc_for_issue key on the bare number and a foreign repo's
   569	# "Closes https://github.com/other/repo/issues/7" must not promote this repo's GH-7.
   570	CLOSING_KEYWORD_URL = re.compile(
   571	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   572	    r"https?://github\.com/([\w.\-]+/[\w.\-]+?)/issues/([0-9]{1,6})\b",
   573	    re.IGNORECASE,
   574	)
   575	# A `#N`/`GH-N` inside a URL (fragment `/#123`, path `/GH-123`, query `?#123`, `?issue=#123`,
   576	# `&#123`) is part of the link, not a reference — GH-271 QA rounds 1+3. The lookbehind is one
   577	# fixed-width character class.
   578	MENTION = re.compile(r"(?<![A-Za-z0-9_/?.=&])(?:[Gg][Hh]-|#)([0-9]{1,6})\b")
   579	TITLE_TRAILER = re.compile(
   580	    r"\([ \t]*((?:(?:#|GH-)[0-9]{1,6}\b[ \t]*(?:[,;][ \t]*)?)+)[ \t]*\)[ \t]*$",
   581	    re.IGNORECASE,
   582	)
   583	CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
   584	INLINE_CODE = re.compile(r"`[^`\n]*`")
   585	
   586	
   587	def _strip_code_blocks(text):
   588	    """GitHub ignores closing keywords inside code; so does the reconciler."""
   589	    return INLINE_CODE.sub(" ", CODE_FENCE.sub(" ", text))
   590	
   591	
   592	def extract_linked_issues(pr_meta, repo_slug=None):
   593	    """Split a PR's issue references into (closers, mentions) — GH-271.
   594	
   595	    closers: refs introduced by a GitHub closing keyword (close/closes/closed/fix/fixes/
   596	    fixed/resolve/resolves/resolved) before a #- or GH--prefixed number, comma lists
   597	    included, plus a trailing "(#N)"/"(GH-N)" title tag. These mirror GitHub's own linking
   598	    rules — extended to the repo's GH-N spelling, since PRs merge into `development` and
   599	    the reconciler parses text rather than relying on default-branch auto-close — and are
   600	    eligible for every reconciler action (promotion when the issue is closed, evidence +
   601	    stays-active when open).
   602	
   603	    mentions: bare GH-N/#N references in prose. The old extractor treated every mention as
   604	    a link (PR #185's body yielded ten "linked" issues, two of them live active lanes), so
   605	    a mention now only ever records merge evidence on an OPEN issue's active doc — never a
   606	    promotion, ROADMAP move, or doc relocation.
   607	
   608	    Both lists are deduplicated and sorted.
   609	    """
   610	    title = _strip_code_blocks(pr_meta.get("title") or "").strip()
   611	    body = _strip_code_blocks(pr_meta.get("body") or "")
   612	    closers, mentions = set(), set()
   613	
   614	    scan_text = title + "\n" + body
   615	    for m in CLOSING_KEYWORD_CLAUSE.finditer(scan_text):
   616	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(m.group(1)))
   617	    if repo_slug:
   618	        closers.update(int(n) for slug, n in CLOSING_KEYWORD_URL.findall(scan_text)
   619	                       if slug.lower() == repo_slug.lower())
   620	    trailer = TITLE_TRAILER.search(title)
   621	    if trailer:
   622	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(trailer.group(1)))
   623	
   624	    mentions.update(int(n) for n in MENTION.findall(scan_text))
   625	    mentions -= closers
   626	    return sorted(closers), sorted(mentions)
   627	
   628	
   629	def find_active_doc_for_issue(repo_root, issue_num):
   630	    """Find matching active doc in PROJECT/2-WORKING/."""
   631	    working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
   632	    if not os.path.isdir(working_dir):
   633	        return None
   634	    for fname in os.listdir(working_dir):
   635	        if not fname.endswith(".md"):
   636	            continue
   637	        # Match GH-123-*.md or 123-*.md
   638	        if re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
   639	            return os.path.join(working_dir, fname)
   640	    return None
   641	
   642	
   643	def parse_doc_frontmatter(doc_path):
   644	    """Parse key-value pairs from document YAML frontmatter."""
   645	    if not doc_path or not os.path.isfile(doc_path):
   646	        return {}
   647	    try:
   648	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   649	            lines = f.readlines()
   650	        if not lines or lines[0].strip() != "---":
   651	            return {}
   652	        fm = {}
   653	        for line in lines[1:]:
   654	            if line.strip() == "---":
   655	                break
   656	            if ":" in line:
   657	                k, v = line.split(":", 1)
   658	                fm[k.strip().lower()] = v.strip().strip("'\"").lower()
   659	        return fm
   660	    except Exception:
   661	        return {}
   662	
   663	
   664	def validate_lessons_learned(content, doc_name):
   665	    """Assert ## Lessons Learned section exists and contains substantive content (GH-496)."""
   666	    m = re.search(r"##\s+Lessons\s+Learned.*?(?=\n##\s+(?!#)|\Z)", content, re.IGNORECASE | re.DOTALL)
   667	    if not m:
   668	        return f"Doc {doc_name} is missing mandatory '## Lessons Learned (For Future Agents)' section."
   669	
   670	    section_text = m.group(0)
   671	    lines = section_text.splitlines()
   672	    body_lines = lines[1:]
   673	
   674	    # Strip HTML comments
   675	    clean_body = re.sub(r"<!--.*?-->", "", "\n".join(body_lines), flags=re.DOTALL)
   676	
   677	    substantive_lines = []
   678	    for line in clean_body.splitlines():
   679	        trimmed = line.strip()
   680	        if not trimmed:
   681	            continue
   682	        # Check for empty placeholder markers
   683	        if re.match(r"^(?:[-*]\s*)?(?:TODO\b.*|TBD\b.*|None(?:\s+yet)?|N/A|\[.*?\]|\[?\s*\]?)$", trimmed, re.IGNORECASE):
   684	            continue
   685	        substantive_lines.append(trimmed)
   686	
   687	    if not substantive_lines:
   688	        return f"Doc {doc_name} has empty/placeholder '## Lessons Learned' section. Substantive reflections are required before closeout."
   689	    return None
   690	
   691	
   692	def validate_frontmatter_schema(doc_path):
   693	    """Validate YAML frontmatter against required PDDA schema (GH-496)."""
   694	    doc_name = os.path.basename(doc_path)
   695	    if not os.path.isfile(doc_path):
   696	        return f"Doc {doc_name} does not exist."
   697	    try:
   698	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   699	            content = f.read()
   700	    except Exception as e:
   701	        return f"Cannot read {doc_name}: {e}"
   702	
   703	    lines = content.splitlines()
   704	    if not lines or lines[0].strip() != "---":
   705	        return f"Doc {doc_name} missing opening YAML frontmatter delimiter ('---') at line 1."
   706	
   707	    closing_idx = -1
   708	    for i, line in enumerate(lines[1:], 1):
   709	        if line.strip() == "---":
   710	            closing_idx = i
   711	            break
   712	
   713	    if closing_idx == -1:
   714	        return f"Doc {doc_name} missing closing YAML frontmatter delimiter ('---')."
   715	
   716	    fm = {}
   717	    for line in lines[1:closing_idx]:
   718	        line = line.strip()
   719	        if not line or line.startswith("#"):
   720	            continue
   721	        if ":" in line:
   722	            k, v = line.split(":", 1)
   723	            fm[k.strip().lower()] = v.strip().strip("'\"")
   724	
   725	    required_keys = ["title", "status", "created", "updated", "owner", "goal"]
   726	    missing = [k for k in required_keys if not fm.get(k)]
   727	    if missing:
   728	        return f"Doc {doc_name} frontmatter missing required field(s): {', '.join(missing)}"
   729	
   730	    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
   731	    for date_key in ("created", "updated"):
   732	        val = fm.get(date_key, "")
   733	        val_date = val.split()[0] if val else ""
   734	        if not date_re.match(val_date):
   735	            return f"Doc {doc_name} frontmatter field '{date_key}' has invalid date format: '{val}' (expected YYYY-MM-DD)."
   270	git -C "$REPO" checkout -q development
   271	# Ensure valid active doc is back in 2-WORKING
   272	if [ -f "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" ]; then
   273	  mv "$REPO/PROJECT/3-COMPLETED/GH-999-TEST.md" "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   274	  sed -i.bak 's/status: Complete/status: Review/' "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   275	  rm -f "$REPO/PROJECT/2-WORKING/GH-999-TEST.md.bak"
   276	  git -C "$REPO" add -A
   277	  git -C "$REPO" commit -q -m "test: reset doc to 2-WORKING"
   278	fi
   279	
   280	# Update test receipt with current HEAD
   281	HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
   282	cat << EOF_REC > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
   283	{"commit": "$HEAD_SHA", "pr": 999, "rc": 0, "result": "pass", "timestamp": "2026-09-10T10:00:00Z"}
   284	EOF_REC
   285	git -C "$REPO" add "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
   286	git -C "$REPO" commit -q -m "fix: closes #999"
   287	
   288	# -------------------------------------------------------------
   289	# Part 2: Pre-Merge Validation Checks (--pre-merge)
   290	# -------------------------------------------------------------
   291	# Case A: Valid doc, substantive lessons learned, matching committed receipt -> PASS (exit 0)
   292	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
   293	assert_eq "Pre-merge check passes when all conditions are met (exit 0)" "$rc" "0"
   294	if grep -q "Pre-merge validation PASSED!" <<< "$out"; then
   295	  pass "Pre-merge confirmation message output"
   296	else
   297	  fail "Pre-merge did not output PASSED confirmation: $out"
   298	fi
   299	
   300	# Case B: Red Control 1 - Empty/placeholder lessons learned -> exit 5
   301	cat << 'DOC_LL' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   302	---
   303	title: Test Task
   304	status: Review
   305	created: 2026-09-10
   306	updated: 2026-09-10
   307	owner: test-agent
   308	goal: Verify pre-merge checks
   309	---
   310	# GH-999: Test Task
   311	
   312	## Lessons Learned
   313	
   314	TODO: add lessons learned later
   315	<!-- none yet -->
   316	DOC_LL
   317	git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   318	git -C "$REPO" commit -q -m "fix: closes #999 with empty lessons learned"
   319	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
   320	assert_eq "Placeholder lessons learned is rejected (exit 5)" "$rc" "5"
   321	if grep -q "empty/placeholder '## Lessons Learned'" <<< "$out"; then
   322	  pass "Error message cites empty/placeholder lessons learned"
   323	else
   324	  fail "Error message missing placeholder explanation: $out"
   325	fi
   326	
   327	# Case C: Red Control 2 - Missing required frontmatter field -> exit 5
   328	cat << 'DOC_FM' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   329	---
   330	title: Test Task
   331	status: Review
   332	created: 2026-09-10
   333	updated: 2026-09-10
   334	goal: Verify pre-merge checks
   335	---
   336	# GH-999: Test Task
   337	
   338	## Lessons Learned
   339	
   340	### 1. Substantive
   341	Reflections exist here.
   342	DOC_FM
   343	git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   344	git -C "$REPO" commit -q -m "fix: closes #999 with missing owner in frontmatter"
   345	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
   346	assert_eq "Missing frontmatter owner field is rejected (exit 5)" "$rc" "5"
   347	if grep -q "frontmatter missing required field(s): owner" <<< "$out"; then
   348	  pass "Error message cites missing owner field"
   349	else
   350	  fail "Error message missing frontmatter explanation: $out"
   351	fi
   352	
   353	# Case D: Red Control 3 - Missing committed test receipt -> exit 6
   354	# Restore valid doc
   355	cat << 'DOC_VALID' > "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   356	---
   357	title: Test Task
   358	status: Review
   359	created: 2026-09-10
   360	updated: 2026-09-10
   361	owner: test-agent
   362	goal: Verify pre-merge checks
   363	---
   364	# GH-999: Test Task
   365	
   366	## Lessons Learned
   367	
   368	### 1. Substantive
   369	Reflections exist here.
   370	DOC_VALID
   371	git -C "$REPO" rm -q "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
   372	git -C "$REPO" add "$REPO/PROJECT/2-WORKING/GH-999-TEST.md"
   373	git -C "$REPO" commit -q -m "fix: closes #999 without test receipt"
   374	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
   375	assert_eq "Missing committed test receipt is rejected (exit 6)" "$rc" "6"
   376	if grep -q "No committed provenance.jsonl or error_log.jsonl receipts found" <<< "$out"; then
   377	  pass "Error message cites missing committed receipt at HEAD"
   378	else
   379	  fail "Error message missing receipt explanation: $out"
   380	fi
   381	
   382	# Case E: Red Control 4 - Uncommitted test receipt is not proof -> exit 6
   383	mkdir -p "$REPO/TESTS-RESULTS/2026-09-10+GH-999"
   384	echo '{"commit": "xyz", "rc": 0, "result": "pass"}' > "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
   385	# Receipt exists on disk as untracked file, but NOT committed in git tree at HEAD
   386	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
   387	assert_eq "Uncommitted test receipt does not satisfy check (exit 6)" "$rc" "6"
   388	rm -f "$REPO/TESTS-RESULTS/2026-09-10+GH-999/provenance.jsonl"
   389	
   390	# -------------------------------------------------------------
   391	# Part 3: Marathon Plan Fingerprinting
   392	# -------------------------------------------------------------
   393	# Clean up any leftover plan docs and reset planner log
   394	rm -f "$REPO/planner_calls.log" "$REPO/.tick/marathon-plan.fingerprint"
   395	touch "$REPO/PROJECT/2-WORKING/MARATHON-PLAN-2026-09-10.md"
   396	git -C "$REPO" add -A
   397	git -C "$REPO" commit -q -m "test: fixture for marathon plan fingerprinting"
   398	
   399	# 1st run: Fingerprint does not exist yet -> marathon-plan.sh must execute
   400	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
   401	assert_eq "Reconciler runs successfully (exit 0)" "$rc" "0"
   402	calls_run1="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
   403	assert_eq "Marathon planner executed on initial run" "$calls_run1" "1"
   404	[ -f "$REPO/.tick/marathon-plan.fingerprint" ] || fail "Fingerprint file not created at .tick/marathon-plan.fingerprint"
   405	pass "Fingerprint file created on initial run"
   406	
   407	# 2nd run: Inputs unchanged -> marathon-plan.sh must be skipped!
   408	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
   409	assert_eq "Second run exits 0" "$rc" "0"
   410	calls_run2="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
   411	assert_eq "Marathon planner skipped when canonical inputs unchanged" "$calls_run2" "1"
   412	if grep -q "skipping marathon-plan.sh — canonical inputs unchanged" <<< "$out"; then
   413	  pass "Log confirms marathon-plan.sh was skipped due to unchanged fingerprint"
   414	else
   415	  fail "Log missing skipped marathon-plan explanation: $out"
   416	fi
   417	
   418	# 3rd run: Mutate roadmap_items in releases.db -> fingerprint changes -> marathon-plan.sh must run!
   419	python3 -c '
   420	import sqlite3
   421	conn = sqlite3.connect("'"$REPO/releases.db"'")
   422	conn.execute("INSERT INTO roadmap_items (global_id, repo_id, gh_number, title, section, position, raw_text, first_seen, updated_at) VALUES (\x27rmi-NEW0000000000000000000001\x27, 1, 1002, \x27New Item\x27, \x27Now\x27, 2, \x27- **GH-1002**\x27, \x272026-09-10\x27, \x272026-09-10\x27)")
   423	conn.commit()
   424	conn.close()
   425	'
   426	rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --marathon test-wave --allow-dirty --skip-branch-check --offline "$REPO/manifest.json" 2>&1)" || rc=$?
   427	assert_eq "Third run exits 0 after roadmap mutation" "$rc" "0"
   428	calls_run3="$(wc -l < "$REPO/planner_calls.log" | tr -d ' ')"
   429	assert_eq "Marathon planner re-executed when roadmap inputs modified" "$calls_run3" "2"
   430	
   431	echo "=== All GH-496 Phase 2 tests passed successfully! ==="
   350	        with open(tmp_path, "w", encoding="utf-8") as f:
   351	            for line in conn.iterdump():
   352	                f.write(f"{line}\n")
   353	        os.replace(tmp_path, sql_path)
   354	    finally:
   355	        if os.path.exists(tmp_path):
   356	            try:
   357	                os.remove(tmp_path)
   358	            except OSError:
   359	                pass
   360	
   361	
   362	def generate_markdown(conn: sqlite3.Connection, md_path: str):
   363	    """Render canonical HARNESS-MODELS-REGISTRY.generated.md view from database atomically."""
   364	    harnesses = conn.execute("SELECT * FROM harnesses ORDER BY harness_id;").fetchall()
   365	    models = conn.execute("SELECT * FROM models ORDER BY lab, canonical_name;").fetchall()
   366	    evals = conn.execute("""
   367	        SELECT e.grade, e.evaluated_by, e.evaluation_role, e.work_description_narrative,
   368	               i.harness_id, i.model_id, i.reasoning_effort, i.created_at
   369	        FROM evaluations e
   370	        JOIN invocation_logs i ON e.invocation_id = i.invocation_id
   371	        ORDER BY e.created_at DESC;
   372	    """).fetchall()
   373	
   374	    lines = [
   375	        "# Harness & Models Registry (Generated View)",
   376	        "",
   377	        "<!-- Auto-generated from harnesses.db by utils/py/harness_app.py — DO NOT HAND-EDIT -->",
   378	        "",
   379	        "## 1. Operating Harnesses & Policy Lanes",
   380	        "",
   381	        "| Harness | Execution Engine | Policy Role | Operating Constraint |",
   382	        "|---|---|---|---|",
   383	    ]
   384	    for h in harnesses:
   385	        lines.append(f"| **{h['name']}** (`{h['harness_id']}`) | `{h['execution_engine']}` | {h['standing_policy_role'] or '—'} | {h['operating_constraint'] or '—'} |")
   386	
   387	    lines.extend([
   388	        "",
   389	        "## 2. Frontier Models & Reasoning Catalog",
   390	        "",
   391	        "| Lab | Model | Context | Reasoning Levels | Pricing ($/1M in / out / cache) |",
   392	        "|---|---|:---:|:---:|:---:|",
   393	    ])
   394	    for m in models:
   395	        p_in = f"${m['prompt_price_per_m']:.2f}" if m['prompt_price_per_m'] is not None else "—"
   396	        p_out = f"${m['completion_price_per_m']:.2f}" if m['completion_price_per_m'] is not None else "—"
   397	        p_cache = f"${m['cache_read_price_per_m']:.4f}" if m['cache_read_price_per_m'] is not None else "—"
   398	        prices = f"{p_in} / {p_out} / {p_cache}"
   399	        raw_levels = m['supported_reasoning_levels'] or ""
   400	        if raw_levels.startswith("["):
   401	            try:
   402	                levels = ", ".join(json.loads(raw_levels))
   403	            except Exception:
   404	                levels = raw_levels
   405	        else:
   406	            levels = raw_levels
   407	        levels = levels or "—"
   408	        lines.append(f"| **{m['lab']}** | `{m['canonical_name']}` | {m['context_window']:,} | `{levels}` | {prices} |")
   409	
   410	    lines.extend([
   411	        "",
   412	        "## 3. Empirical Evaluation History & Qualitative Work Logs",
   413	        "",
   414	    ])
   415	    if not evals:
   416	        lines.append("*No evaluations recorded yet in database.*")
   417	    else:
   418	        for ev in evals:
   419	            lines.append(f"### `{ev['model_id']}` on `{ev['harness_id']}` — Grade **{ev['grade']}**")
   420	            lines.append(f"**Evaluated by:** `{ev['evaluated_by']}` ({ev['evaluation_role']}) | **Date:** {ev['created_at']}")
   421	            if ev['reasoning_effort']:
   422	                lines.append(f"**Reasoning Effort:** `{ev['reasoning_effort']}`")
   423	            lines.append("")
   424	            lines.append(ev['work_description_narrative'])
   425	            lines.append("")
   426	
   427	    content = "\n".join(lines) + "\n"
   428	    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
   429	    tmp_path = f"{md_path}.tmp.{os.getpid()}"
   430	    try:
   431	        with open(tmp_path, "w", encoding="utf-8") as f:
   432	            f.write(content)
   433	        os.replace(tmp_path, md_path)
   434	    finally:
   435	        if os.path.exists(tmp_path):
   436	            try:
   437	                os.remove(tmp_path)
   438	            except OSError:
   439	                pass
   440	
   441	
   442	def check_integrity(repo_root: Optional[str] = None) -> int:
   443	    """Validate database foreign keys, schema consistency, and generated views."""
   444	    root = repo_root or get_repo_root()
   445	    db_p = get_db_path(root)
   446	    # GH-496: If out-of-tree telemetry DB does not exist yet (e.g. cold runner),
   447	    # but in-repo harnesses.db exists, fall back to in-repo DB for check ONLY IF
   448	    # XYZ_HARNESS_DB was not explicitly overridden.
   449	    if "XYZ_HARNESS_DB" not in os.environ and not os.path.exists(db_p):
   450	        in_repo = os.path.join(root, "harnesses.db")
   451	        if os.path.exists(in_repo):
   452	            db_p = in_repo
   453	
   454	    sql_p = get_sql_path(root)
   455	    gen_md = get_generated_md_path(root)
   456	
   457	    if not os.path.exists(db_p):
   458	        print(f"harness check: FAIL — database missing at {db_p}", file=sys.stderr)
   459	        return 1
   460	
   461	    conn = init_db(db_p)
   462	    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
   463	    if fk_errors:
   464	        print(f"harness check: FAIL — foreign key integrity errors: {fk_errors}", file=sys.stderr)
   465	        return 1
   466	
   467	    integ = conn.execute("PRAGMA integrity_check;").fetchall()
   468	    if not integ or integ[0][0] != "ok":
   469	        print(f"harness check: FAIL — SQLite integrity check failed: {integ}", file=sys.stderr)
   470	        return 1
   360	    os.makedirs(_base, exist_ok=True)
   361	    tmp = path + f".tmp.{os.getpid()}"
   362	    with open(tmp, "w", encoding="utf-8") as f:
   363	        json.dump(state, f, indent=2)
   364	        f.write("\n")
   365	    os.replace(tmp, path)
   366	
   367	
   368	def jog_current_gid(root, gh_num):
   369	    """The queue row's global_id (its durable identity across retries)."""
   370	    conn = sqlite3.connect(os.path.join(root, "releases.db"))
   371	    conn.row_factory = sqlite3.Row
   372	    try:
   373	        row = conn.execute("SELECT global_id FROM jog_queue WHERE gh_number = ? "
   374	                           "ORDER BY id DESC LIMIT 1", (gh_num,)).fetchone()
   375	        return row["global_id"] if row else None
   376	    finally:
   377	        conn.close()
   378	
   379	
   380	def jog_verify_pr_before_merge(root, receipt, pr_number):
   381	    """GH-300 (PR #281 review B1): verify GitHub truth against the receipt BEFORE merging.
   382	
   383	    An approved receipt's PR identity is Marathon-owned and trusted as a record, but the
   384	    merge must not act on it blind: a stale PR number that happens to resolve in this repo
   385	    (or a PR whose head moved after the reviewed build) would otherwise be merged as-is.
   386	    Mirrors the verification family `jog land` performs post-merge, adapted to pre-merge:
   387	    the PR must still be OPEN with the receipt's base/head/head-SHA, the receipt must name
   388	    this repo, and the gate must be green for that head. Returns (failures, pr); an empty
   389	    failures list means the merge may proceed.
   390	    """
   391	    pr, err = _gh_pr_view(root, pr_number)
   392	    if pr is None:
   393	        return [f"pr view failed: {err}"], None
   394	    checks = [
   395	        ("state OPEN", pr.get("state") == "OPEN"),
   396	        (f"base {receipt.get('base_branch')}", pr.get("baseRefName") == receipt.get("base_branch")),
   397	        (f"head {receipt.get('head_branch')}", pr.get("headRefName") == receipt.get("head_branch")),
   398	        (f"head SHA {str(receipt.get('head_sha') or '')[:8]}",
   399	         pr.get("headRefOid") == receipt.get("head_sha")),
   400	        ("receipt repo is this repo",
   401	         not receipt.get("target_repo", {}).get("path")
   402	         or os.path.realpath(receipt["target_repo"]["path"]) == os.path.realpath(root)),
   403	    ]
   404	    gate = receipt.get("gate") or {}
   405	    checks.append(("gate green on the merge head",
   406	                   gate.get("result") == "green"
   407	                   and (not gate.get("receipt_path") or os.path.isfile(gate["receipt_path"]))))
   408	    return [name for name, ok in checks if not ok], pr
   409	
   410	
   411	def jog_project_marathon_outcome(root, gh_num, receipt, auto_merge=False,
   412	                                 execution_id=None, result_path=None):
   413	    """Project a validated Marathon result receipt into the queue via perform_write.
   414	
   415	    Marathon owns the outcome; this only records it. Returns the queue action taken
   416	    ("completed", "parked", "failed") plus a human reason. Never guesses a branch or PR:
   417	    landing identity comes from the receipt, and a green phase without a PR is parked with
   418	    the receipt's branch fields — it is never a global failure.
   419	
   420	    GH-291 Scope 4: refused/escalated/parked reasons carry a trace segment naming the
   421	    execution_id and result_path when the caller provides them, so a failed row points at
   422	    its receipt without a ledger inspection.
   423	    """
   424	    outcome = receipt.get("outcome")
   425	    reason = receipt.get("reason")
   426	    if outcome == "approved":
   427	        pr = receipt.get("pr") or {}
   428	        pr_number = pr.get("number")
   429	        if pr_number:
   430	            note = f"awaiting-landing (PR #{pr_number}: {pr.get('url') or 'url unavailable'})"
  1380	    ]
  1381	    env = dict(os.environ)
  1382	    env["RELAY_DRIVER_LOCKED"] = "1"
  1383	    env["XYZ_ROOT"] = root
  1384	    env["MARATHON_BUILDER"] = builder
  1385	    env["MARATHON_REVIEWER"] = reviewer
  1386	    env[f"{reviewer.upper()}_AGENT"] = reviewer
  1387	    env.setdefault(f"{reviewer.upper()}_LOG",
  1388	                   os.path.join(tempfile.gettempdir(), f"{reviewer}-turn-jog-{os.getpid()}.log"))
  1389	    # Turn-taker shim env contract (relay-xyz Path A): <BUILDER>_AGENT selects the
  1390	    # dispatching actor (must match the tick token's handoff target above), ALLOW_PATHS
  1391	    # (comma-separated) grants the contract's artifact paths for a build turn, and
  1392	    # <BUILDER>_LOG keeps concurrent runs from sharing one log. Without these the shim
  1393	    # dies at startup ("AGY_AGENT required") before any turn runs.
  1394	    env[f"{builder.upper()}_AGENT"] = builder
  1395	    env.setdefault(f"{builder.upper()}_LOG",
  1396	                   os.path.join(tempfile.gettempdir(), f"{builder}-turn-jog-{os.getpid()}.log"))
  1397	    doc = find_issue_doc(root, gh_num)
  1398	    artifacts = []
  1399	    if doc:
  1400	        m = re.search(r"##\s*Swarm Preflight Contract\s*\n+```json\n(.*?)\n```", open(doc).read(), re.S)
  1401	        if m:
  1402	            try:
  1403	                artifacts = [a for a in json.loads(m.group(1)).get("artifacts", []) if isinstance(a, str)]
  1404	            except Exception:
  1405	                pass
  1406	    env["ALLOW_PATHS"] = ",".join(artifacts)
  1407	
  1408	    proc = subprocess.run(cmd, cwd=root, env=env)
  1409	    # GH-505: the driver's exit IS the verdict. The override that used to live here read the
  1410	    # relay file's STATUS word and turned a non-zero driver exit into 0 when it said Approved —
  1411	    # the exact word a builder turn can write. Deleted; relay-drive now attests approvals itself.
  1412	    return proc.returncode
  1413	
  1414	
  1415	def _verify_legacy_pr_before_merge(root, pr_num):
  1416	    """GH-300: minimal pre-merge guard for the relay-path landing boundary.
  1417	
  1418	    The legacy path has no marathon receipt to verify against — it discovers its PR by
  1419	    branch-name convention — so the guard is the subset that convention can support: the
  1420	    discovered PR must be OPEN and based on development before it is merged. Returns None
  1421	    when the merge may proceed, else the failed-check names.
  1422	    """
  1423	    pr, err = _gh_pr_view(root, pr_num)
  1424	    if pr is None:
  1425	        return [f"pr view failed: {err}"]
  1426	    return [name for name, ok in [
  1427	        ("state OPEN", pr.get("state") == "OPEN"),
  1428	        ("base development", pr.get("baseRefName") == "development"),
  1429	    ] if not ok]
  1430	
  1431	
  1432	def _tick_bin(root):
  1433	    for cand in (os.environ.get("TICK_BIN"), os.path.join(root, "bin", "tick"),
  1434	                 os.path.join(harness_home(), "bin", "tick")):
  1435	        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
  1436	            return cand
  1437	    return None
  1438	
  1439	
  1440	def _token_done(root, task):
  1441	    """GH-505: the relay token must READ done in the pinned tick root — a record alone is not a
  1442	    verdict. Returns (ok, reason)."""
  1443	    tick = _tick_bin(root)
  1444	    if not tick:
  1445	        return False, "tick CLI not found"
  1446	    # The token lives in the repo jog operates on — never an ambient TICK_REPO_ROOT from a parent shell.
  1447	    env = dict(os.environ); env["TICK_REPO_ROOT"] = root
  1448	    info = subprocess.run([tick, "info", task], cwd=root, env=env, capture_output=True, text=True)
  1449	    if info.returncode != 0:
  1450	        return False, f"token {task} unreadable ({(info.stderr or '').strip() or 'tick info failed'})"
  1451	    for line in (info.stdout or "").splitlines():
  1452	        if line.startswith("status:"):
  1453	            st = line.split(":", 1)[1].strip()
  1454	            return (st == "done"), (None if st == "done" else f"token {task} reads {st or 'unknown'}, not done")
  1455	    return False, f"token {task} not found"
  1456	
  1457	
  1458	def _merge_reviewed_pr(root, pr_num, record, expected_candidate=None):
  1459	    """GH-505/GH-509/GH-510: the ONE merge step for every jog landing branch.
  1460	

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '725,785p'; git diff --unified=8 development...HEAD -- .github/workflows/ci.yml .github/workflows/wave-reconcile.yml utils/ci-route.sh test/ci-route.sh validate.sh; git show --stat --oneline fd90f51c; git show --format= --name-only fd90f51c | sed '/"'^$/d'"'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 7785ms:
2026-09-10 10:11:00.486 xcodebuild[77067:94820416]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:00.724 xcodebuild[77067:94820322] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-jFsez2K8' (errno=Operation not permitted)
2026-09-10 10:11:01.425 xcodebuild[77503:94821352]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:01.649 xcodebuild[77503:94821303] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/test/ci-route.sh b/test/ci-route.sh
index 996b49f0..6031de11 100755
--- a/test/ci-route.sh
+++ b/test/ci-route.sh
@@ -231,18 +231,18 @@ out="$(bash "$ROUTER" subsystems hq)"
 [[ "$(wc -w <<<"$out")" -eq 14 ]] \
   && pass "subsystems hq lists its 14 suites" \
   || fail "subsystems hq listed $(wc -w <<<"$out") suites: $out"
 out="$(bash "$ROUTER" subsystems releases)"
 [[ "$(wc -w <<<"$out")" -eq 21 ]] \
   && pass "subsystems releases lists its 21 suites (GH-496)" \
   || fail "subsystems releases listed $(wc -w <<<"$out") suites: $out"
 out="$(bash "$ROUTER" subsystems pdda)"
-[[ "$(wc -w <<<"$out")" -eq 11 ]] \
-  && pass "subsystems pdda lists its 11 suites (GH-496)" \
+[[ "$(wc -w <<<"$out")" -eq 12 ]] \
+  && pass "subsystems pdda lists its 12 suites (GH-496)" \
   || fail "subsystems pdda listed $(wc -w <<<"$out") suites: $out"
 out="$(bash "$ROUTER" subsystems skills-army-hq)"
 [[ "$out" == "skills-army-hq.sh" ]] \
   && pass "subsystems skills-army-hq lists its dedicated suite (GH-487)" \
   || fail "subsystems skills-army-hq listing: $out"
 
 echo "  ci-route: $PASS pass, $FAIL fail"
 exit "$FAIL"
diff --git a/utils/ci-route.sh b/utils/ci-route.sh
index e218c0f8..b10330ff 100755
--- a/utils/ci-route.sh
+++ b/utils/ci-route.sh
@@ -19,29 +19,29 @@ ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
 # githooks/pre-push and validate.sh (--tier 2 / --subsystem). Extending it is a deliberate
 # three-part act: name the subsystem in SUBSYSTEMS, add its path patterns to subsystem_of(),
 # and list its suites in SUBSYSTEM_TESTS_<name>. Every listed suite must exist in test/ AND
 # be registered in validate.sh's TESTS array — test/gh35-test-tiers.sh enforces both, because
 # a registry naming a suite that never runs is a green lie (the releases-skill lesson).
 SUBSYSTEMS="hq releases telemetry ate swe-diagram pdda agent-chorus standup skills-army-hq"
 SUBSYSTEM_TESTS_hq="hq.sh hq-park.sh hq-park-synthesis.sh hq-dispatch.sh hq-next.sh hq-locator.sh hq-hardening.sh hq-promote.sh hq-marathon-scan.sh hq-rollup.sh hq-marathon-live.sh roadmap-dashboard.sh gh238-hq-releases-mode.sh gh239-hq-status-releases-mode.sh"
 SUBSYSTEM_TESTS_releases="gh32-releases-app.sh gh103-timeline-exporter.sh gh32-releases-artifacts.sh gh53-releases-merge-resolve.sh gh54-merged-dump-refusals.sh gh57-live-merge-resolve.sh gh69-roadmap-shadow.sh gh32-release-target-advisory.sh gh39-releases-project-sync.sh gh153-releases-sidebar-rollup.sh releases-skill.sh gh284-p3-release-milestone.sh gh284-p4-release-lanes.sh litmus-release.sh nightwatch-release.sh meter-release.sh ballast-release.sh gh57-releases-fuzz.sh roadmap-dashboard.sh gh257-roadmap-ledger-fixes.sh gh269-roadmap-retired.sh"
-SUBSYSTEM_TESTS_telemetry="xyz-completion.sh gh358-lock-instrumentation.sh archive-telemetry.sh"
+SUBSYSTEM_TESTS_telemetry="xyz-completion.sh gh358-lock-instrumentation.sh archive-telemetry.sh gh496-telemetry-isolation.sh"
 SUBSYSTEM_TESTS_ate="ate-run-variations.sh gh298-ate-gen4-ci-smoke.sh gh-gen4-phase1-domain-oracles.sh gh-gen4-phase2-adaptive-ate.sh gh-gen4-phase3-fuzz-engine.sh gh-gen4-phase4-repro-synth.sh gh-gen4-phase5-campaign.sh gh478-runaway-guard.sh"
 SUBSYSTEM_TESTS_swe_diagram="swe-diagram.sh"
-SUBSYSTEM_TESTS_pdda="pdda-roadmap-coverage.sh pdda-repo-contract.sh pdda-local-checks.sh gh400-acceptance-fidelity.sh gh400-source-url.sh gh422-backfill-source-url.sh gh425-source-url-slug.sh wave-reconcile.sh gh202-wave-reconcile-issue-state.sh gh232-wave-reconcile-multiphase.sh gh358-wave-reconcile-vendored-paths.sh"
+SUBSYSTEM_TESTS_pdda="pdda-roadmap-coverage.sh pdda-repo-contract.sh pdda-local-checks.sh gh400-acceptance-fidelity.sh gh400-source-url.sh gh422-backfill-source-url.sh gh425-source-url-slug.sh wave-reconcile.sh gh202-wave-reconcile-issue-state.sh gh232-wave-reconcile-multiphase.sh gh358-wave-reconcile-vendored-paths.sh gh496-phase2-reconciliation-views.sh"
 SUBSYSTEM_TESTS_agent_chorus="agent-chorus.sh"
 SUBSYSTEM_TESTS_standup="gh77-standup-triage.sh"
 SUBSYSTEM_TESTS_skills_army_hq="skills-army-hq.sh"
 
 subsystem_of() {  # <path> -> subsystem name, or nothing when unmapped
   case "$1" in
     utils/hq/*|skills/hq/*)                                                                printf '%s\n' hq ;;
     utils/py/releases_app.py|skills/releases/*|utils/release-lanes.sh|releases.sql|releases.db|utils/releases-merge-resolve.sh|utils/leaderboard.sh|utils/roadmap-dashboard.sh) printf '%s\n' releases ;;
-    utils/telemetry/*)                                                                     printf '%s\n' telemetry ;;
+    utils/telemetry/*|test/gh496-telemetry-isolation.sh)                                  printf '%s\n' telemetry ;;
     utils/ate/*|utils/fuzzing/*|utils/py/telemetry_schema.py|utils/py/domain_oracles.py|utils/py/adaptive_ate.py|utils/py/calibrate_tier1.py|utils/py/fuzz_engine.py|utils/py/repro_synth.py|utils/py/gen4_campaign.py|utils/py/proc_group.py|utils/py/ate_runaway_sweep.py) printf '%s\n' ate ;;
     utils/swe-diagram/*)                                                                   printf '%s\n' swe-diagram ;;
     utils/pdda/*|utils/pdda-local-checks.sh|utils/pdda-catchup.sh|utils/pdda-doc-ready.sh|utils/py/wave_reconcile.py) printf '%s\n' pdda ;;
     skills/agent-chorus/*)                                                                 printf '%s\n' agent-chorus ;;
     skills/standup/*)                                                                      printf '%s\n' standup ;;
     skills/skills-army-hq/*|test/test_deploy_skills.py|test/skills-army-hq.sh)             printf '%s\n' skills-army-hq ;;
   esac
 }
diff --git a/validate.sh b/validate.sh
index 32efdf25..a31e5b62 100755
--- a/validate.sh
+++ b/validate.sh
@@ -103,16 +103,17 @@ TESTS=(
   "model-alias.sh"              # GH-120 (OpenRouter model-alias fuzzy lookup) + GH-450 (tier-4 post-correction guard, terminal-refusal control)
   "gh450-model-catalog-pin.sh"  # GH-450 (vendored Model-catalog pin: tag+sha256 record, YAML byte-equality drift check, catalog version in invocation telemetry)
   "gh460-fuzz-resolver-smoke.sh" # GH-460 (standing fuzz smoke: resolver structural contract via Gen4 engine)
   "gh346-model-telemetry-honesty.sh" # GH-346 Phase 0 (a shim may not log a model id no dispatch path can produce)
   "gh518-muse-model-policy.sh"  # GH-518 (muse-turn model policy fails closed: only a confirmed-public repo reaches the data-clause tier)
   "gh518-muse-adapter-containment.sh" # GH-518 (adapter-level: execution-vs-coordination root classification, process-group reap on timeout)
   "gh346-resolver-fallback.sh"  # GH-346 Phase 1 (alias resolver is an enhancement over a literal floor, never a dependency)
   "gh346-telemetry-row-written.sh" # GH-346 Phase 0 checkbox 0.5 (a row actually lands, with the dispatched model)
+  "gh496-telemetry-isolation.sh"   # GH-496 Phase 1 (routine telemetry written out-of-tree to ~/.xyz/projects/<key>/telemetry/)
   "gh346-registry-view-freshness.sh" # GH-346 (the generated registry view must match harnesses.db)
   "gh346-gateway-allowlists.sh" # GH-346 Phase 2 (every agent-id allowlist agrees on the shipped gateway set)
   "gh346-profile-resolve.sh"    # GH-346 Phase 3a (one name -> harness/gateway/model; no tier may block a turn)
   "gh368-same-lane-routing.sh"  # GH-368 (same-lane builder/reviewer routing)
   "gh373-reviewer-validation.sh" # GH-373 (reviewer validation alignment)
   "gh369-group-kill.sh"         # GH-369 (process-group kill for turn cap)
   "gh370-progress-telemetry.sh" # GH-370 (worktree progress telemetry in supervisor poll)
   "gh371-interrupt-snapshot.sh" # GH-371 (snapshot uncommitted tree on interruption)
@@ -590,16 +591,17 @@ TESTS=(
   "gh107-timeline-json-seam.sh"     # GH-107 (export_timeline.py --json seam)
   "gh132-review-xyz-skill.sh"       # GH-132 (/review-xyz skill + multi-model review harness)
   "gh165-governance-canonical-paths-guard.sh" # GH-165 (canonical wave-reconciler paths + GH-551 anti-sprawl static guard)
   "gh197-vendor-tier-split.sh"      # GH-197 (two-tier vendor: core default + opt-in RELEASES overlay)
   "gh273-marathon-root-audit-python-shape.sh" # GH-273 (root audit matches python3-spelled driver calls — the GH-195 blind spot)
   "gh312-vendor-preserves-state.sh" # GH-312 (vendor/sync must not destroy the target's runtime state)
   "relay-uncited-findings.sh"       # GH-173 B3 (rtl_check_uncited_findings downgrades uncited review claims)
   "wave-reconcile.sh"               # GH-165 (canonical post-merge reconciler behavior)
+  "gh496-phase2-reconciliation-views.sh" # GH-496 (hosted reconciler in-flight collision detection, pre-merge checks, marathon plan fingerprinting)
   "gh306-registry-bidirectional.sh" # GH-306 (exists→registered registry half; self-demonstrating — see the suite header)
   "gh298-ate-gen4-ci-smoke.sh"      # GH-298 (ATE Gen 4 CI smoke — fuzz/oracle wiring against the real runner)
   "gh-gen4-phase1-domain-oracles.sh" # GH-299 Phase 1 (Gen 4 semantic domain oracles: zero-state, containment, idempotence, crash-recovery; +/- controls)
   "gh-gen4-phase2-adaptive-ate.sh"   # GH-299 Phase 2 (Gen 4 constraint-aware pairwise ATE + calibrated $0 Tier-1 triage; independent coverage walk)
   "gh-gen4-phase3-fuzz-engine.sh"    # GH-299 Phase 3 (Gen 4 seeded mutational fuzz engine: replay, novelty-capped corpus, cross-twin parity)
   "gh-gen4-phase4-repro-synth.sh"    # GH-299 Phase 4 (Gen 4 clustered reproducer synthesis: 1 suite per root cause, ddmin, falsification)
   "gh-gen4-phase5-campaign.sh"       # GH-299 Phase 5 (Gen 4 sandboxed campaign: bounded soak in a disposable clone, 0 host contamination, poison control)
   "gh396-find-harness-roots.sh"     # GH-396 (find-harness two-roots contract: #395 ×5 topologies, #394 warn-under-override + runnable remedy, --quiet)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-6Dl8w5mx' (errno=Operation not permitted)
2026-09-10 10:11:03.132 xcodebuild[78341:94823356]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:03.355 xcodebuild[78341:94823304] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-fUk8IOGE' (errno=Operation not permitted)
2026-09-10 10:11:04.021 xcodebuild[78744:94824308]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:04.254 xcodebuild[78744:94824228] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
fd90f51c feat(gh-496): view decoupling, single reconciler owner, and pre-merge closeout checks
 AGENTS.md                                          |    8 +-
 LEADERBOARD.md                                     |    1 +
 PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md           |   50 +-
 ROADMAP-DASHBOARD.md                               |    5 +-
 SOP.md                                             |   10 +-
 githooks/dashboard-staleness-guard.sh              |  162 +-
 .../gh496-pr2-plan-qa.PROMPT.txt                   |   26 +
 .../gh496-pr2-plan-qa.codex.NO-CITATION.txt        |    1 +
 .../gh496-pr2-plan-qa.codex.PROVENANCE.txt         |    2 +
 .../gh496-pr2-plan-qa.codex.md                     | 4147 ++++++++++++++++++++
 skills/merge-cleanup/SKILL.md                      |    7 +-
 test/gh103-timeline-exporter.sh                    |    3 +-
 test/gh243-dashboard-staleness-guard.sh            |   31 +-
 test/gh496-phase2-reconciliation-views.sh          |  430 ++
 test/roadmap-dashboard.sh                          |    7 +-
 test/wave-reconcile.sh                             |   12 +-
 utils/ci-route.sh                                  |    2 +-
 utils/leaderboard.sh                               |    3 +
 utils/py/releases_app.py                           |   18 +-
 utils/py/wave_reconcile.py                         |  473 ++-
 utils/roadmap-dashboard.sh                         |   14 +-
 validate.sh                                        |    1 +
 22 files changed, 5290 insertions(+), 123 deletions(-)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-olvcFsis' (errno=Operation not permitted)
2026-09-10 10:11:05.762 xcodebuild[79596:94826312]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:06.002 xcodebuild[79596:94826244] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-QVfWIUob' (errno=Operation not permitted)
2026-09-10 10:11:06.671 xcodebuild[80058:94827492]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:06.898 xcodebuild[80058:94827449] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
AGENTS.md
LEADERBOARD.md
PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md
ROADMAP-DASHBOARD.md
SOP.md
githooks/dashboard-staleness-guard.sh
relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt
relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.NO-CITATION.txt
relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.PROVENANCE.txt
relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.md
skills/merge-cleanup/SKILL.md
test/gh103-timeline-exporter.sh
test/gh243-dashboard-staleness-guard.sh
test/gh496-phase2-reconciliation-views.sh
test/roadmap-dashboard.sh
test/wave-reconcile.sh
utils/ci-route.sh
utils/leaderboard.sh
utils/py/releases_app.py
utils/py/wave_reconcile.py
utils/roadmap-dashboard.sh
validate.sh

codex
The first concrete defect is now reproduced from source: the planner fingerprint hashes roadmap DB fields and active-doc filenames, but not active-doc contents. Editing an existing task’s readiness/preflight content leaves the fingerprint unchanged, so a stale marathon plan can be incorrectly reused. I’m checking whether the pre-merge and reconciliation ownership tests have similar vacuous-pass gaps.
mcp: codebase-memory-mcp/index_status started
mcp: codebase-memory-mcp/index_status (completed)
mcp: codebase-memory-mcp/search_graph started
mcp: codebase-memory-mcp/search_graph (completed)
exec
/bin/zsh -lc "nl -ba PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md | sed -n '55,125p'; rg -n -- \"--pre-merge|wave_reconcile.py --pre-merge\" .github githooks utils skills test | head -80; nl -ba TESTS-RESULTS/2026-09-10+GH-496-PR2/SUMMARY.md; nl -ba TESTS-RESULTS/2026-09-10+GH-496-PR2/provenance.jsonl; nl -ba githooks/dashboard-staleness-guard.sh | sed -n '95,250p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 0ms:
    55	### Phase 0: Baseline Freeze, Recon Map, and Preservation Spikes
    56	- [x] Create fresh full clone at `~/marathon-clones/xyz-gh496-build` on `feat/gh496-selective-ci`.
    57	- [x] Install and verify git hooks (`bash githooks/install.sh --check`).
    58	- [x] Grounded recon of `harness_app.py`, writers, readers, callers, and runtime paths.
    59	- [x] Isolated preservation spikes: verify existing path overrides, assert no writes to tracked repo during turns, ensure model/device registry reads remain intact.
    60	- [x] Baseline replay of changed-file sets from #495, #526, #531.
    61	
    62	### Phase 1: Stop Routine Telemetry from Rewriting Task Branches
    63	- [x] Update `harness_app.py` path resolution to default runtime telemetry to `~/.xyz/projects/<stable-project-key>/telemetry/harnesses.db` when not overridden.
    64	- [x] Preserve environment overrides: `XYZ_HARNESS_DB`, `XYZ_HARNESS_SQL`, `XYZ_HARNESS_GENERATED_MD`, `XYZ_HARNESS_DOCS_DIR`.
    65	- [x] Keep versioned model/harness registry inputs intact in git while runtime logs append to external store.
    66	- [x] Concurrency, migration, and idempotent import tests with fixture-contained paths (`test/gh496-telemetry-isolation.sh`).
    67	- [x] Witnessed red controls: dropped row, writer directed to checkout, conflicting ID, foreign key validation.
    68	- [x] Verify clean git status on ordinary harness/relay turns.
    69	
    70	## Acceptance Criteria (PR 1)
    71	- [x] Live harness turns write invocation logs and evaluations to external runtime store without modifying tracked files in task clone.
    72	- [x] Tests hermetically contain all telemetry writes to fixture directories with zero writes to real home directory.
    73	- [x] Curated model registry configurations and benchmarks remain versioned and accessible in git.
    74	- [x] Full gate passes in a disposable clone with committed provenance and test logs.
    75	
    76	---
    77	
    78	## PR 2 Execution Checklist (Phase 2 — Single Reconciliation Owner, View Decoupling & Pre-Merge Closeout Checks)
    79	
    80	### Single Reconciliation Owner & Automation Protection
    81	- [x] Keep hosted `wave-reconcile.yml` as the single normal landing writer; protect local execution with workflow in-flight checks (`gh run list`).
    82	- [x] Update `AGENTS.md`, `SOP.md`, and `skills/merge-cleanup/SKILL.md` to document hosted completion as normal path and local reconcile as fallback.
    83	- [x] Minimize marathon plan regeneration in `wave_reconcile.py` via input fingerprinting (`.tick/marathon-plan.fingerprint`).
    84	
    85	### Generated Views Decoupling & Generation Stamping
    86	- [x] `utils/roadmap-dashboard.sh` and `utils/leaderboard.sh` query `releases.db` settings and stamp `<!-- releases-app generation: <N> -->` on line 1.
    87	- [x] Task branches render disposable previews (`--preview`) but stop committing routine dashboard outputs.
    88	- [x] `githooks/dashboard-staleness-guard.sh`: semantic validation of task-branch ledger writes (allowing clean renders without committed dashboards; refusing dropped rows).
    89	- [x] Refuse unauthorized routine dashboard commits on task branches that do not modify renderer source code (causal allowlist).
    90	
    91	### Deterministic Pre-Merge Closeout Checks
    92	- [x] Add read-only `--pre-merge` check to `wave_reconcile.py` validating `## Lessons Learned`, frontmatter schema, and test receipts on closing docs before merge.
    93	- [x] Red control: doc missing `## Lessons Learned` or containing only placeholders fails pre-merge check with exit code 5.
    94	- [x] Red control: doc missing required frontmatter schema fields fails pre-merge check with exit code 5.
    95	- [x] Red control: missing committed passing test receipt at HEAD fails pre-merge check with exit code 6.
    96	
    97	### Verification & Gate Qualification
    98	- [x] Build hermetic test suite `test/gh496-phase2-reconciliation-views.sh`.
    99	- [x] Update `test/gh243-dashboard-staleness-guard.sh`, `test/roadmap-dashboard.sh`, `test/gh103-timeline-exporter.sh`, and `test/wave-reconcile.sh`.
   100	- [x] Register new suite in `validate.sh` and `utils/ci-route.sh`.
   101	- [x] Verify PDDA hygiene suite (`utils/pdda/pdda.sh run`).
   102	- [ ] Run full `./validate.sh` in disposable clone `~/marathon-clones/xyz-gh496-gate-pr2`.
   103	- [ ] Independent Codex QA review via `relay-automation/consult.sh --models codex`.
   104	
   105	## Acceptance Criteria (PR 2)
   106	- [x] Two concurrent task branches with distinct ledger writes land without dashboard merge collisions.
   107	- [x] Committed `ROADMAP-DASHBOARD.md` and `LEADERBOARD.md` identify their ledger generation.
   108	- [x] Pre-merge closeout check catches missing `## Lessons Learned` before merge.
   109	- [x] Local reconciliation refuses execution while a hosted workflow is in progress.
   110	- [ ] Full gate passes in a disposable clone with committed receipts and zero uncommitted churn.
   111	
   112	## Lessons Learned (For Future Agents)
   113	
   114	### 1. View Decoupling & Push Boundaries
   115	Decoupling generated views from feature/task branches is the single most impactful defense against merge collisions in multi-agent and parallel workflows. However, hard-blocking view commits in push guards requires a causal exemption allowlist: when developers legitimately modify renderer logic (e.g. `utils/roadmap-dashboard.sh` or `utils/leaderboard.sh`), the push guard must permit updated views so that generator improvements and their outputs stay in sync.
   116	
   117	### 2. Regex Heading Boundaries in Markdown Parsers
   118	When parsing markdown sections (such as extracting `## Lessons Learned`), lookaheads must explicitly account for subheading levels. Terminating on `(?=\n##|\Z)` naively matches `\n###` subheadings immediately following the header, falsely treating non-empty sections as empty. Terminating on `(?=\n##\s+(?!#)|\Z)` correctly restricts the boundary to subsequent H2 sections while preserving nested H3/H4 reflections.
   119	
   120	### 3. Resolving the Git Receipt Bootstrap Paradox
   121	Testing that an exact git commit hash is recorded in a committed receipt file creates a bootstrap paradox if strictly compared only to HEAD SHA: amending or committing the receipt changes the commit hash itself. To resolve this cleanly and robustly without relaxing integrity, `validate_pre_merge_receipts` checks both exact HEAD and recent branch commits (`git log -n 10 --format=%H HEAD`), allowing receipts generated during local verification to be committed directly without chicken-and-egg hash invalidation.
   122	
   123	### 4. Hermetic Mock Isolation
   124	When adding downstream tool invocations to central orchestrators (like calling `leaderboard.sh` in `wave_reconcile.py`), existing test suites with mock file trees can fail if they only mocked the legacy toolset. Making adopted views opt-in by presence (`os.path.exists`) ensures downstream repositories and minimal test fixtures remain functional without forcing unnecessary mock scaffolding.
test/gh496-phase2-reconciliation-views.sh:4:# 2. Deterministic pre-merge closeout checks (--pre-merge: frontmatter, lessons learned, receipts)
test/gh496-phase2-reconciliation-views.sh:289:# Part 2: Pre-Merge Validation Checks (--pre-merge)
test/gh496-phase2-reconciliation-views.sh:292:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:319:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:345:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:374:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
test/gh496-phase2-reconciliation-views.sh:386:rc=0; out="$(python3 "$RECONCILE_PY" --root "$REPO" --pre-merge 2>&1)" || rc=$?
utils/py/wave_reconcile.py:1505:        "--pre-merge",
     1	# GH-496 PR 2 — Gate Provenance & Test Results Summary
     2	
     3	Branch: `feat/gh496-phase2-views`
     4	Target Commit: `75c9890f`
     5	Qualification Environment: Disposable full clone `~/marathon-clones/xyz-gh496-gate-pr2` (un-sandboxed, independent `.git`)
     6	Gate: `./validate.sh` (368+ parallel test suites + pytest layer + clone invariants)
     7	
     8	## Gate Results Summary
     9	
    10	| Suite / Check | Result | Detail |
    11	|---|---|---|
    12	| `test/gh496-phase2-reconciliation-views.sh` | 25 / 25 PASS | Single reconciler in-flight check, GITHUB_ACTIONS enforcement, pre-merge checks, marathon plan fingerprinting |
    13	| `test/gh421-auto-wave-reconcile.sh` | 17 / 17 PASS | Catch-up, lifecycle, second apply idempotency, rollback boundaries |
    14	| `test/wave-reconcile.sh` | 16 / 16 PASS | Core wave reconciliation suite, promotion, archive formatting |
    15	| `test/gh202-wave-reconcile-issue-state.sh` | 40 / 40 PASS | Closing keyword parsing, mention handling, live/offline state drift |
    16	| `test/gh280-jog-marathon-adapter.sh` | 217 / 217 PASS | Jog queue status updates, marathon execution, dashboard generation sync |
    17	| `test/gh257-roadmap-ledger-fixes.sh` | ALL PASS | Ledger generation updates, dashboard staleness guard compatibility |
    18	| `test/ci-route.sh` | 63 / 63 PASS | Fast routing, pdda subsystem suite coverage |
    19	| `test/gh204-sed-portability.sh` | ALL PASS | BSD/GNU sed portability audits |
    20	| `utils/pdda/pdda.sh run` | errors=0 | Full doc-hygiene and governance gate |
    21	| `test/gh308-frozen-twin-guard.sh` | PASS | Zero frozen twin edits, zero new Bash scripts |
    22	| Full `./validate.sh` | **ALL PASS** | All suites passed; 0 failed |
    23	| `clone-identity-invariant` | PASS | `core.bare=false`, `origin` intact, `HEAD` unchanged |
    24	
    25	## Phase 2 Governance & Invariant Attestation
    26	
    27	1. **Single Reconciliation Owner**: Hosted `wave-reconcile.yml` is the sole default landing writer on `development`. Local reconciliation fails closed (exit 8) if a hosted run is queued or in-progress. `--force-local-reconcile` provides local override and is hard-rejected inside `GITHUB_ACTIONS=true` (exit 2).
    28	2. **View Decoupling & Generation Stamping**: Routine task branches do not commit `ROADMAP-DASHBOARD.md` or `LEADERBOARD.md`. Line 1 embeds `<!-- releases-app generation: <N> -->`. Staleness guard enforces that view commits only accompany changes to renderers or run within `GITHUB_ACTIONS=true`.
    29	3. **Deterministic Pre-Merge Closeout Checks**: Read-only `wave_reconcile.py --pre-merge` verifies closing active doc frontmatter (owner, status), substantive `## Lessons Learned` (exit 5), and committed test receipts in the git tree at HEAD (exit 6).
    30	4. **Marathon Plan Fingerprinting**: `wave_reconcile.py` skips redundant `marathon-plan.sh` runs when canonical inputs match `.tick/marathon-plan.fingerprint`.
     1	{"timestamp": "2026-09-10T17:08:14.000000+00:00", "case": "full-gate-qualification", "command": "./validate.sh", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "passed: all parallel test suites; failed: 0", "environment": "un-sandboxed shell, disposable full clone ~/marathon-clones/xyz-gh496-gate-pr2; identity read before and after", "identity_unchanged": true, "identity_before": "75c9890faab372fe1161a64c8264b6536a23ef01", "identity_after": "75c9890faab372fe1161a64c8264b6536a23ef01", "dirty_after": 0, "note": "GH-496 PR 2 full validation gate clean"}
     2	{"timestamp": "2026-09-10T17:00:00.000000+00:00", "case": "phase2-reconciliation-views-focused", "command": "bash test/gh496-phase2-reconciliation-views.sh", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "25 pass, 0 fail", "environment": "un-sandboxed shell, disposable full clone ~/marathon-clones/xyz-gh496-gate-pr2", "identity_unchanged": true, "note": "GH-496 Phase 2 hermetic regression suite"}
     3	{"timestamp": "2026-09-10T16:53:00.000000+00:00", "case": "auto-wave-reconcile-focused", "command": "bash test/gh421-auto-wave-reconcile.sh", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "17 pass, 0 fail", "environment": "un-sandboxed shell, disposable full clone ~/marathon-clones/xyz-gh496-gate-pr2", "identity_unchanged": true, "note": "Wave reconcile idempotency and rollback verification"}
     4	{"timestamp": "2026-09-10T16:51:50.000000+00:00", "case": "wave-reconcile-core-focused", "command": "bash test/wave-reconcile.sh && bash test/gh202-wave-reconcile-issue-state.sh", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "56 pass, 0 fail", "environment": "un-sandboxed shell, disposable full clone ~/marathon-clones/xyz-gh496-gate-pr2", "identity_unchanged": true, "note": "Core wave reconciliation suite and issue state handling"}
     5	{"timestamp": "2026-09-10T16:45:00.000000+00:00", "case": "jog-marathon-adapter-focused", "command": "bash test/gh280-jog-marathon-adapter.sh", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "217 pass, 0 fail", "environment": "un-sandboxed shell, build clone ~/marathon-clones/xyz-gh496-pr2-build", "identity_unchanged": true, "note": "Jog queue and marathon adapter test suite"}
     6	{"timestamp": "2026-09-10T16:52:48.000000+00:00", "case": "pdda-local-checks", "command": "bash utils/pdda/pdda.sh run", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "errors=0", "environment": "un-sandboxed shell, build clone ~/marathon-clones/xyz-gh496-pr2-build", "identity_unchanged": true, "note": "PDDA doc-hygiene gate"}
     7	{"timestamp": "2026-09-10T16:52:02.000000+00:00", "case": "frozen-twin-guard", "command": "bash test/gh308-frozen-twin-guard.sh --check --base origin/development", "commit": "75c9890f", "rc": 0, "result": "pass", "exit_code": 0, "output": "no frozen Bash twin changed; no new Bash under utils/ or relay-automation/", "environment": "un-sandboxed shell, build clone ~/marathon-clones/xyz-gh496-pr2-build", "identity_unchanged": true, "note": "GH-308 / GH-551 frozen twin guard"}
    95	fi
    96	
    97	while [ "$#" -ge 2 ]; do
    98	  local_sha="$1"; remote_sha="$2"; shift 2
    99	  case "$remote_sha" in
   100	    ''|0000000000000000000000000000000000000000) continue ;;   # new branch: no range to inspect
   101	  esac
   102	  git -C "$REPO" cat-file -e "${remote_sha}^{commit}" 2>/dev/null || continue
   103	
   104	  touched_ledger=0
   105	  touched_dashboard=0
   106	  touched_leaderboard=0
   107	  touched_dashboard_renderer=0
   108	  touched_leaderboard_renderer=0
   109	
   110	  while IFS= read -r path; do
   111	    case "$path" in
   112	      releases.sql|releases.db) touched_ledger=1 ;;
   113	      ROADMAP-DASHBOARD.md)     touched_dashboard=1 ;;
   114	      LEADERBOARD.md)           touched_leaderboard=1 ;;
   115	      utils/roadmap-dashboard.sh|utils/py/releases_app.py) touched_dashboard_renderer=1 ;;
   116	      utils/leaderboard.sh|utils/timeline/export_timeline.py) touched_leaderboard_renderer=1 ;;
   117	    esac
   118	  done < <(git -C "$REPO" diff --no-renames --name-only "$remote_sha" "$local_sha" 2>/dev/null)
   119	
   120	  # Check 1: View Decoupling (GH-496 Phase 2)
   121	  # Task branches must NOT commit routine ROADMAP-DASHBOARD.md or LEADERBOARD.md.
   122	  # Views are owned and staged by the reconciliation workflow on development upon landing.
   123	  # View commits are permitted only if the causal renderer dependency was modified in the range,
   124	  # or in GITHUB_ACTIONS (where the reconciler bot commits views).
   125	  if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
   126	    if [ "$touched_dashboard" -eq 1 ] && [ "$touched_dashboard_renderer" -eq 0 ]; then
   127	      cat >&2 <<'EOF'
   128	dashboard-staleness-guard: REFUSING the push — this range modifies ROADMAP-DASHBOARD.md
   129	without modifying its renderer (utils/roadmap-dashboard.sh or utils/py/releases_app.py).
   130	
   131	Under GH-496 Phase 2, generated views are owned and staged by the reconciliation workflow
   132	on development. Task branches must not commit routine view updates, to prevent merge collisions.
   133	
   134	Fix (drop the view commit while keeping your ledger changes):
   135	    git rm --cached ROADMAP-DASHBOARD.md && git commit --amend
   136	
   137	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   138	EOF
   139	      exit 1
   140	    fi
   141	
   142	    if [ "$touched_leaderboard" -eq 1 ] && [ "$touched_leaderboard_renderer" -eq 0 ]; then
   143	      cat >&2 <<'EOF'
   144	dashboard-staleness-guard: REFUSING the push — this range modifies LEADERBOARD.md
   145	without modifying its renderer (utils/leaderboard.sh or utils/timeline/export_timeline.py).
   146	
   147	Under GH-496 Phase 2, generated views are owned and staged by the reconciliation workflow
   148	on development. Task branches must not commit routine view updates, to prevent merge collisions.
   149	
   150	Fix (drop the view commit while keeping your other changes):
   151	    git rm --cached LEADERBOARD.md && git commit --amend
   152	
   153	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   154	EOF
   155	      exit 1
   156	    fi
   157	  fi
   158	
   159	  # Check 2: Renderer sync validation when renderer dependencies are modified
   160	  if [ "$touched_dashboard" -eq 1 ] && [ "$touched_dashboard_renderer" -eq 1 ]; then
   161	    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
   162	    mkdir -p "$TMP_PROJ"
   163	    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
   164	       && [ -f "$TMP_PROJ/utils/roadmap-dashboard.sh" ]; then
   165	      if ! bash "$TMP_PROJ/utils/roadmap-dashboard.sh" --check 2>&1 >/dev/null; then
   166	        cat >&2 <<'EOF'
   167	dashboard-staleness-guard: REFUSING the push — renderer changes were committed but
   168	ROADMAP-DASHBOARD.md is not in sync with the updated renderer output.
   169	
   170	Regenerate and commit:
   171	    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit --amend
   172	EOF
   173	        exit 1
   174	      fi
   175	    fi
   176	  fi
   177	
   178	  if [ "$touched_leaderboard" -eq 1 ] && [ "$touched_leaderboard_renderer" -eq 1 ]; then
   179	    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
   180	    mkdir -p "$TMP_PROJ"
   181	    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
   182	       && [ -f "$TMP_PROJ/utils/leaderboard.sh" ]; then
   183	      if ! bash "$TMP_PROJ/utils/leaderboard.sh" --check 2>&1 >/dev/null; then
   184	        cat >&2 <<'EOF'
   185	dashboard-staleness-guard: REFUSING the push — renderer changes were committed but
   186	LEADERBOARD.md is not in sync with the updated renderer output.
   187	
   188	Regenerate and commit:
   189	    bash utils/leaderboard.sh && git add LEADERBOARD.md && git commit --amend
   190	EOF
   191	        exit 1
   192	      fi
   193	    fi
   194	  fi
   195	
   196	  # Check 3: Semantic ledger validation (GH-496 Phase 2 + GH-474)
   197	  # When the ledger is modified, ensure the ledger renders cleanly and drops no rows.
   198	  if [ "$touched_ledger" -eq 1 ]; then
   199	    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
   200	    mkdir -p "$TMP_PROJ"
   201	
   202	    render_err=""
   203	    render_rc=0
   204	    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
   205	       && [ -f "$TMP_PROJ/utils/roadmap-dashboard.sh" ]; then
   206	      render_err="$(ROADMAP_DASHBOARD_OUTPUT="$TMP_PROJ/ROADMAP-DASHBOARD.md" bash "$TMP_PROJ/utils/roadmap-dashboard.sh" 2>&1 >/dev/null)" || render_rc=$?
   207	    else
   208	      render_rc=1
   209	      render_err="renderer missing or archive failed"
   210	    fi
   211	
   212	    if [ "$render_rc" -ne 0 ]; then
   213	      cat >&2 <<EOF
   214	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
   215	(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, but the ledger cannot be rendered into a valid dashboard (GH-496).
   216	
   217	The renderer reported:
   218	$render_err
   219	
   220	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   221	EOF
   222	      exit 1
   223	    fi
   224	
   225	    # GH-474: Check for dropped rows reported by the renderer
   226	    dropped_line=""
   227	    while IFS= read -r eline; do
   228	      case "$eline" in
   229	        *"roadmap-dashboard: warning: dropped "*) dropped_line="$eline"; break ;;
   230	      esac
   231	    done <<EOF_ERR
   232	$render_err
   233	EOF_ERR
   234	    if [ -n "$dropped_line" ]; then
   235	      cat >&2 <<EOF
   236	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
   237	(releases.sql / releases.db) without modifying ROADMAP-DASHBOARD.md, but regenerating the
   238	dashboard produces NO diff (GH-243 / GH-257).
   239	
   240	The renderer dropped a roadmap row, so it contributes nothing to the view.
   241	It reported:
   242	    $dropped_line
   243	
   244	Correct the named row with:
   245	    releases roadmap update --issue-num <N> --raw-text "- **GH-<N> · <title>** ..."
   246	
   247	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   248	EOF
   249	      exit 1
   250	    fi

exec
/bin/zsh -lc "head -3 ROADMAP-DASHBOARD.md; head -3 LEADERBOARD.md; git ls-files releases.db releases.sql .tick/marathon-plan.fingerprint; git status --short; git diff --numstat development...HEAD | tail -50; git show --format='%H %P' --no-patch HEAD; git log --oneline development..HEAD" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-31762-wal40lwl
 succeeded in 13477ms:
2026-09-10 10:11:42.668 xcodebuild[94573:94857101]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:42.932 xcodebuild[94573:94857066] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YLrMMG7o' (errno=Operation not permitted)
2026-09-10 10:11:43.618 xcodebuild[94841:94857560]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:43.857 xcodebuild[94841:94857553] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
releases.db
releases.sql
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Aj4mZliZ' (errno=Operation not permitted)
2026-09-10 10:11:45.431 xcodebuild[95261:94858328]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:45.656 xcodebuild[95261:94858300] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-gu99Xba0' (errno=Operation not permitted)
2026-09-10 10:11:46.313 xcodebuild[95477:94858814]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:46.533 xcodebuild[95477:94858773] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
?? relay-system/2026-09-10/gh496-pr2-final-qa-100915/
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Ty33xA6R' (errno=Operation not permitted)
2026-09-10 10:11:48.380 xcodebuild[95919:94859592]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:48.627 xcodebuild[95919:94859560] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-arVz04NN' (errno=Operation not permitted)
2026-09-10 10:11:49.297 xcodebuild[96146:94860094]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:49.519 xcodebuild[96146:94860054] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
5	3	AGENTS.md
2	0	CHANGELOG.md
1	0	LEADERBOARD.md
100	38	PROJECT/2-WORKING/GH-496-SHARPEN-CICD.md
151	0	PROJECT/2-WORKING/recon-gh496-merge-churn-and-telemetry.md
3	2	ROADMAP-DASHBOARD.md
6	4	SOP.md
26	0	TESTS-RESULTS/2026-09-09+GH-496-PR1/SUMMARY.md
16	0	TESTS-RESULTS/2026-09-09+GH-496-PR1/focused-gh496.log
-	-	TESTS-RESULTS/2026-09-09+GH-496-PR1/full-gate.log.gz
7	0	TESTS-RESULTS/2026-09-09+GH-496-PR1/provenance.jsonl
30	0	TESTS-RESULTS/2026-09-10+GH-496-PR2/SUMMARY.md
7	0	TESTS-RESULTS/2026-09-10+GH-496-PR2/provenance.jsonl
110	50	githooks/dashboard-staleness-guard.sh
1	0	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.PROMPT.txt
1	0	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.NO-CITATION.txt
2	0	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.PROVENANCE.txt
2133	0	relay-system/2026-09-09/gh496-pr1-qa-211502/gh496-pr1-qa.codex.md
26	0	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt
1	0	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.NO-CITATION.txt
2	0	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.PROVENANCE.txt
4147	0	relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.codex.md
4	3	skills/merge-cleanup/SKILL.md
2	2	test/ci-route.sh
2	1	test/gh103-timeline-exporter.sh
25	6	test/gh243-dashboard-staleness-guard.sh
2	2	test/gh257-roadmap-ledger-fixes.sh
2	2	test/gh280-jog-marathon-adapter.sh
431	0	test/gh496-phase2-reconciliation-views.sh
282	0	test/gh496-telemetry-isolation.sh
5	2	test/roadmap-dashboard.sh
11	1	test/wave-reconcile.sh
3	3	utils/ci-route.sh
3	0	utils/leaderboard.sh
158	11	utils/py/harness_app.py
11	5	utils/py/jog_run.py
17	1	utils/py/releases_app.py
460	29	utils/py/wave_reconcile.py
11	3	utils/roadmap-dashboard.sh
2	0	validate.sh
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-cQAAHP3z' (errno=Operation not permitted)
2026-09-10 10:11:50.999 xcodebuild[96811:94861129]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:51.226 xcodebuild[96811:94861068] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-raeHf4xD' (errno=Operation not permitted)
2026-09-10 10:11:51.883 xcodebuild[97194:94861625]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:52.101 xcodebuild[97194:94861595] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8c05cd2884c42ec5a39981ad0d082088e1538fae ef19c5b40e622037edfee84e0ded3b291427a007
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-kPnvWZl8' (errno=Operation not permitted)
2026-09-10 10:11:53.652 xcodebuild[97674:94862458]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:53.887 xcodebuild[97674:94862416] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-DofERCfT' (errno=Operation not permitted)
2026-09-10 10:11:54.546 xcodebuild[97928:94862878]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-09-10 10:11:54.767 xcodebuild[97928:94862854] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8c05cd28 fix(gh-496): support short commit SHA prefix matching in pre-merge receipt validation
ef19c5b4 test(gh-496): commit Phase 2 test qualification receipt and summary
75c9890f fix(gh-496): snapshot planner fingerprint in rollback journal and exclude generated plans from hash
aeeb98c9 fix(gh-496): harden in-flight checks, staleness guard compatibility, and jog dashboard refresh
fd90f51c feat(gh-496): view decoupling, single reconciler owner, and pre-merge closeout checks
dd44b739 docs(gh-496): add Phase 2 execution checklist and acceptance criteria
141f2ced test(telemetry): record verified full-gate qualification receipts post-Codex review (GH-496 PR 1)
fa98ab0f feat(telemetry): address independent consult QA and harden out-of-tree store (GH-496 PR 1)
ee4038f0 feat(telemetry): relocate routine harness telemetry out-of-tree (GH-496 PR 1)

mcp: codebase-memory-mcp/check_index_coverage started
mcp: codebase-memory-mcp/check_index_coverage (completed)
codex
ANSWER: No. The PR is not ready to merge; two correctness blockers remain, and HEAD lacks final-state gate evidence.

FINDINGS

- [Blocker] Marathon fingerprint ignores active-document contents. It hashes each active doc’s filename only, so changing readiness, dependencies, or preflight contracts inside an existing doc will incorrectly reuse the old plan. The test mutates only `roadmap_items`, so it never exercises this case. `utils/py/wave_reconcile.py:1170-1175`; `test/gh496-phase2-reconciliation-views.sh:418-429`.

- [Blocker] Receipt validation accepts stale evidence. With `--pr`, any passing receipt carrying that PR number succeeds regardless of its commit; without `--pr`, any receipt matching one of the last ten commits succeeds. Subsequent code changes therefore need not be tested. `utils/py/wave_reconcile.py:492-542`. This is currently observable: the committed full-gate receipt targets `75c9890f`, while reviewed HEAD is `8c05cd28`; the receipt predates the final short-SHA validation fix. `TESTS-RESULTS/2026-09-10+GH-496-PR2/provenance.jsonl:1-2`.

- [Should] `--pre-merge --pr` silently falls back to recent local commit messages if `gh pr view` fails, and document discovery examines only `HEAD~1..HEAD`. A network/auth failure can consequently omit docs changed earlier in the PR instead of failing closed. `utils/py/wave_reconcile.py:1328-1377`.

- [Should] The in-flight query is a TOCTOU guard, not strict mutual exclusion: a hosted run may start after the local query and before local writes. The hosted workflow’s rejected fast-forward push limits damage, but “single owner” is stronger than the implementation guarantees. `utils/py/wave_reconcile.py:1538-1545`; `.github/workflows/wave-reconcile.yml:91-94`.

- [Pass] Hosted reconciliation is serialized and pushes only declared artifacts; forced local reconciliation is rejected under `GITHUB_ACTIONS=true`. `.github/workflows/wave-reconcile.yml:12-17,62-94`; `utils/py/wave_reconcile.py:1529-1542`.

- [Pass] Both generated views carry the generation marker on line 1, and SQLite binaries remain tracked as required for PR 2.

RECOMMENDATION: Hash active-doc bytes, require receipts for the exact final tested commit, fail closed when requested PR metadata cannot be read, add corresponding red controls, then rerun and commit the full gate at the resulting HEAD.
tokens used
123,975
ANSWER: No. The PR is not ready to merge; two correctness blockers remain, and HEAD lacks final-state gate evidence.

FINDINGS

- [Blocker] Marathon fingerprint ignores active-document contents. It hashes each active doc’s filename only, so changing readiness, dependencies, or preflight contracts inside an existing doc will incorrectly reuse the old plan. The test mutates only `roadmap_items`, so it never exercises this case. `utils/py/wave_reconcile.py:1170-1175`; `test/gh496-phase2-reconciliation-views.sh:418-429`.

- [Blocker] Receipt validation accepts stale evidence. With `--pr`, any passing receipt carrying that PR number succeeds regardless of its commit; without `--pr`, any receipt matching one of the last ten commits succeeds. Subsequent code changes therefore need not be tested. `utils/py/wave_reconcile.py:492-542`. This is currently observable: the committed full-gate receipt targets `75c9890f`, while reviewed HEAD is `8c05cd28`; the receipt predates the final short-SHA validation fix. `TESTS-RESULTS/2026-09-10+GH-496-PR2/provenance.jsonl:1-2`.

- [Should] `--pre-merge --pr` silently falls back to recent local commit messages if `gh pr view` fails, and document discovery examines only `HEAD~1..HEAD`. A network/auth failure can consequently omit docs changed earlier in the PR instead of failing closed. `utils/py/wave_reconcile.py:1328-1377`.

- [Should] The in-flight query is a TOCTOU guard, not strict mutual exclusion: a hosted run may start after the local query and before local writes. The hosted workflow’s rejected fast-forward push limits damage, but “single owner” is stronger than the implementation guarantees. `utils/py/wave_reconcile.py:1538-1545`; `.github/workflows/wave-reconcile.yml:91-94`.

- [Pass] Hosted reconciliation is serialized and pushes only declared artifacts; forced local reconciliation is rejected under `GITHUB_ACTIONS=true`. `.github/workflows/wave-reconcile.yml:12-17,62-94`; `utils/py/wave_reconcile.py:1529-1542`.

- [Pass] Both generated views carry the generation marker on line 1, and SQLite binaries remain tracked as required for PR 2.

RECOMMENDATION: Hash active-doc bytes, require receipts for the exact final tested commit, fail closed when requested PR metadata cannot be read, add corresponding red controls, then rerun and commit the full gate at the resulting HEAD.
