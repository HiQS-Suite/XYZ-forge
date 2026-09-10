**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)

> **ATTESTATION**
> Model: gpt-5.6-sol
> Provider: openai
> Sandbox: read-only

Reading additional input from stdin...
OpenAI Codex v0.153.4
--------
workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a08bf0-341c-79e2-91c3-1ebcbd8e9ee9
--------
user
You are an INDEPENDENT advisor in a one-shot cross-model consult. Another model is answering the SAME question separately and a coordinator will reconcile both answers, so give your own honest, specific read — do not hedge toward a consensus you cannot see. Read any repo files the question references (cite file:line). Respond with: (1) a short direct ANSWER; (2) graded FINDINGS — [Blocker]/[Should]/[Nit]/[Pass] — where applicable; (3) a one-line RECOMMENDATION. You are ADVISORY ONLY: output your analysis as text; do not rely on writing files (you are running in a throwaway copy).

=== CONSULT QUESTION ===
Plan QA review for GH-496 PR 2 (Phase 2): Single Reconciliation Owner, View Decoupling & Pre-Merge Closeout Checks.

Context:
PR 1 (selective CI baseline & telemetry externalization) has been completed and opened as PR #548.
PR 2 tackles:
1. Reconciler single-writer protection:
   - Hosted wave-reconcile.yml is the single normal landing writer for development.
   - Local wave_reconcile.py becomes a protected fallback. Before execution, check if hosted workflow wave-reconcile.yml is in-flight (using gh run list --workflow wave-reconcile.yml) to prevent concurrent write races.
   - Avoid redundant marathon plan generation in wave_reconcile.py when inputs are unchanged.
2. View decoupling & generation stamping:
   - Task branches stop committing routine ROADMAP-DASHBOARD.md and LEADERBOARD.md outputs.
   - Committed views are owned and staged by reconciliation on development.
   - Embed exact generation metadata from releases.db settings into ROADMAP-DASHBOARD.md and LEADERBOARD.md headers so view consumers can verify freshness.
   - githooks/dashboard-staleness-guard.sh: semantic validation of task-branch ledger writes (allowing clean renders without committed dashboards; refusing dropped/corrupted rows; and refusing routine dashboard commits on task branches unless renderer source is modified).
3. Deterministic pre-merge closeout check:
   - Add --pre-merge flag to wave_reconcile.py to validate closing active docs (under PROJECT/2-WORKING/) have non-empty ## Lessons Learned, valid frontmatter, and test receipts BEFORE merge.
   - Red control: doc missing ## Lessons Learned fails pre-merge check with exit code 5.
4. Governance doc alignment:
   - Update AGENTS.md, SOP.md, and skills/merge-cleanup/SKILL.md to establish hosted reconciliation as normal path and local reconcile as fallback.

Please review this plan against XYZ-forge architecture and Phase 2 requirements:
1. Are there edge cases or failure modes with the reconciler in-flight check? (e.g. offline gh, rate limits, non-interactive environments, force bypass flag?)
2. How should githooks/dashboard-staleness-guard.sh distinguish between legitimate renderer changes (where committing dashboard is expected/required) vs routine task branches (where committing dashboard causes merge collisions and should be refused)?
3. What is the cleanest backward-compatible syntax for generation stamping in ROADMAP-DASHBOARD.md and LEADERBOARD.md?
4. Are there subtle traps with wave_reconcile.py --pre-merge doc discovery or test receipt verification?
Provide actionable feedback and concrete recommendations.
codex
I’m applying the codebase-memory and SWE planning-review skills because this is architecture-grounded plan QA. I’ll verify the actual reconciliation, rendering, hook, and PDDA contracts before grading the proposal.
exec
/bin/zsh -lc "sed -n '1,240p' /Users/noelsaw/.codex/skills/codebase-memory/SKILL.md && sed -n '1,260p' /Users/noelsaw/.codex/skills/swe/SKILL.md" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
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
name: swe
description: Apply software-engineering standards when authoring or reviewing project plans, build/spec/PRD documents, architecture RFCs, or agent governance. Use for "write a plan", "review this build doc", "apply our SWE standards", or "is this plan ready to build"; also apply before drafting a project plan. Grades grounded recon, minimal scope, diagnosis, blast radius, and verifiable acceptance. This is a planning rubric, not a debugging or execution pipeline.
---

# SWE

Vibe the build; engineer the plan. This lens is the discipline that lets a fast v1.x ship without becoming a liability.

A governance overlay for **build/spec documents** — the "build v1.x" doc, the implementation spec, the architecture RFC. It does not debug code or pick a tradeoff in the moment; it reads the *plan* and asks whether the plan already embodies the engineering standards before a single line is written. Run it two ways: as an **authoring gate** (write the doc against it) or as a **review rubric** (read a doc, emit findings + a verdict). The whole bet: most plans fail not on the feature but on the five things below, smuggled past in prose — starting with Pillar 0, where the plan is grounded (or not) in the system as it actually exists.

## Pillar 0: Recon — is the plan grounded in a system anyone actually read?

The four pillars grade what the document *says*. Pillar 0 grades its **provenance**: was it written against the system as it exists, or from the prompt plus three grepped files? This pillar is about evidence, not consequences — what breaks when a *step* runs is Blast's job, below.

- [ ] The current system was traced before the first plan heading: entry points and call paths in, every read *and write* site of the state involved, the contracts crossed, the failure and rollback paths today.
- [ ] Claims about what the change touches cite code somebody read — `file:line`, not "various downstream."
- [ ] What could not be verified is listed as an explicit unknown with the command or file that would settle it, never smoothed into the findings.

**Applicability first.** Pillar 0 does not apply to greenfield work, a non-code plan, or a change contained to files the doc already quotes — mark it N/A and say why. Where it does apply, grade the *evidence*, not the artifact: a [recon](../recon/SKILL.md) Recon Map is the standard form, but a trace embedded in the doc or supplied by the author counts. **Block** only when the doc makes claims about an existing system that nothing behind it verifies; a thin trace on a genuinely small change is a **Fix**, not a Block.

**Pillar 0 feeds Blast; it does not satisfy it.** The trace establishes the *current-state* radius — who depends today on what the plan touches. Blast then asks what each proposed step *adds*: new systems, new data, new people, the shield, the tripwire, the undo class. Copying the map's radius into the Blast section unchanged understates the plan's own impact and fails Blast on its own terms.

## The four pillars

Each pillar is a lens on the document. A v1.x doc that satisfies a pillar contains the thing explicitly; a doc that "implies" it fails the pillar — implied is unbuilt.

### 1. Minimal (Ponytail) — does the plan earn each part it adds?

The plan's default answer to "add a thing" is *no*. Scope, dependencies, and abstractions are all liabilities until justified in the doc.

- [ ] Every new component answers "does this need to exist?" (YAGNI) — speculative scope is cut or deferred, not built.
- [ ] Sourcing ladder is honored to minimize mechanism, not requirements: stdlib → native platform feature → already-installed dep → one line of our own. A new dep names what it buys that the rung above does not. (Security and observability requirements are never simplified away, only implemented via the laziest viable mechanism).
- [ ] No premature abstraction — the plugin layer / framework / generic engine is justified by ≥2 concrete present uses, not one hypothetical future one.
- [ ] Bias is stated: delete > add, boring > clever, shortest diff that works. A complexity cap is named (e.g. stdlib-only, ~600-line ceiling) where it applies.

*Planning translation:* this is the editor pass on scope. Most v1.x bloat is decided here, in the doc, long before code.

### 2. Diagnosable (Mantra) — does the plan say how it will fail and be found?

A build doc that provisions zero observability is a debugging session deferred to production. Bake the diagnosis path into v1.x, not v1.next.

- [ ] Instrumentation is right-sized but explicit: a single actionable error log is better than an unread ELK stack, but silent failures are blocked. The plan names the exact log, metric, or alert that fires when it breaks.
- [ ] Every iterate/retry loop has a **stop condition** (e.g. 5-failure hard stop, 10-total cap). An unbounded "retry until it works" is a defect in the plan.
- [ ] Failures are made reproducible: the plan names how a failure is repro'd, and treats intermittent failure as a *signal* (concurrency / ordering / env / TOCTOU), not noise to retry away.
- [ ] State changes are auditable — append-only event log over in-place mutation where the history matters.
- [ ] **The plan names debug-mantra as its execution-time debugging protocol** — "we'll figure it out when it breaks" is a Diagnosable failure.

*Planning translation:* the runtime debugging ritual, pulled forward. If the doc can't say how you'll see it break, you'll see it break in prod.

### 3. Blast — does the plan price its irreversible moves before committing?

For every wide-impact or hard-to-undo step, the doc must already carry the cost. Don't dress a one-way door as a tweak.

- [ ] Each risky step names its **undo class**: easy / costly / one-way door. One-way doors are flagged, never silent.
- [ ] **Blast radius** is named — the exact systems, data, and people that break if this step goes wrong (not "various downstream").
- [ ] A **shield** is specified — flag, adapter, pilot/canary, dual-write, or an explicit "none."
- [ ] A **tripwire** exists for anything costly or one-way: *how* you'll know to pull it and *by when* (the point of no return). A shield with no tripwire is a brake with no warning light.

For the full per-decision accounting, defer to the **blast-radius** skill — this pillar only enforces that the v1.x doc *contains* that accounting for its irreversible steps.

### 4. Proof (Done) — can the plan prove it's finished, separately from claiming it?

Editor and grader are different roles. The plan must define "done" in terms something other than the author can check.

- [ ] Every task has a **measurable done-criterion** — a checkable output or metric, not "works" / "improved" / "robust."
- [ ] Tests are specified *and the plan requires they actually run* — "tests pass" means an execution artifact, not an assertion.
- [ ] **No orphan tasks**: every step maps to a success criterion, and every success criterion is covered by a step.
- [ ] **Closed loop**: For medium/large efforts, backend/data work must explicitly connect to a user-facing UI plane or final consumer. Fetching data without surfacing it to the user is an incomplete loop.
- [ ] **Observed vs. predicted is kept separate** — the doc never launders a projection ("this will reduce load 40%") as evidence. Predictions are labeled as such.

*Planning translation:* PlanProof's editor/grader separation at document scale. The grader reads only what's written, not what the author meant.

## House invariants

Non-negotiable conventions a v1.x doc must satisfy regardless of pillar. These are cheap to check and expensive to skip.

- [ ] **FSM threshold** — model an explicit state machine only past ~4 states; below that a flag or enum is leaner. Past it, an ad-hoc tangle of booleans is the defect.
- [ ] **Single write path** — one writer per piece of state. Multiple write paths to the same table/file are a race waiting to happen; name the single path.
- [ ] **Append-only event log** only when audit or history is an explicit business requirement (JSONL or equivalent); otherwise, simple in-place updates are the default.
- [ ] **UTC-only** time handling end to end; local time only at the display edge. "Nightly," "daily," "expires in 24h" all imply a timezone — pin it.
- [ ] **Crash-safe / idempotent jobs** — cron and background work are resumable and safe to run twice. A job that corrupts state on a mid-run crash is unshipped.
- [ ] **Checklist standard** — actionable items use the `- [ ]` hyphen prefix in GitHub-flavored Markdown, never bare `[ ]` in tables or lists.
- [ ] **Agent contract current** — for agent-built work, AGENTS.md / CLAUDE.md exists and matches the plan (conventions, loop caps, honesty constraints). The project's AGENTS.md must name SOLID compliance as a coding standard; if it doesn't, the plan has no enforceable code-design contract.

## How this differs from the sibling skills

- **swe** — "Does this *plan* embody our engineering standards before we build?" The standard/rubric, applied to a whole document.
- **recon** — "What is actually there?" The read-only trace of the current system that Pillar 0 grades the doc against. It supplies the current-state radius; Blast extends that radius per proposed step. Run recon first in author mode when the plan changes an existing system.
- **phase-0-spike** (an external workflow at `~/.claude/workflows/phase-0-spike.js`, not a skill in this repo) — the deep seam map, contract owners, and rollout invariants for a refactor that is already committed to. `recon` is the cheap universal pass before any plan; phase-0-spike is the expensive one after the refactor is approved. A v1.x doc for a subsystem refactor cites one or the other, never neither.
- **plan-adversarial-serial** — the *pipeline* (generate → review → revise → review → judge). It is the machinery; `swe` is one of the standards the machinery can enforce. Compose them: run the adversarial pipeline with `swe` as the lens content.
- **blast-radius** — "How big is *this one decision* and what breaks?" `swe`'s Blast pillar defers per-decision accounting to it.
- **iron-triangle** — "Which of speed/cost/quality is *this choice* trading?" When a plan forces fast/cheap/good tension, hand that node to it.
- **debug-mantra** — the four-step runtime debugging discipline (reproduce → fail path → falsify → breadcrumb). Diagnosable enforces the plan names it; debug-mantra governs live execution — composing across the doc/session boundary.
- **take-a-step-back** — "Is this the right problem/frame at all?" Runs *before* there is a plan to govern.
- **bottom-line** / **linear** — compress or sequence output. `swe` evaluates a plan's substance; those reshape its presentation.

Reach for `swe` the moment there is a build/spec document to hold to a standard — authoring one or judging one.

## How to apply

**Author mode** — you are writing the v1.x doc. Clear Pillar 0 first (run recon, or state why it was skipped), then use the four pillars and house invariants as the doc's skeleton: each feature passes Minimal before it earns a section; each risky step ships with its Blast block; each task ships with its Proof criterion. The lens is the gate, not a later edit.

**Review mode** — you are handed a v1.x doc. Walk Pillar 0, then the four pillars, then the invariants. For each gap, emit one finding keyed to the doc location (`§section`, or `file:line` for code-adjacent specs), tagged by severity, with the *cheapest* fix first. Close with a verdict. Do not rewrite the doc unless asked — surface the checkable gaps and let the author act.

## Project plan scaffold (Author mode)

When the ask is "write a project plan" / "write a plan" (authoring, not reviewing), clear Pillar 0 first, build the doc against the four pillars **and** lay it out in the fixed structure below. The structure is load-bearing, not decoration: the status table forces an honest "where are we" at a glance, the Table of contents keeps a long plan navigable, observable checklist items *are* the Proof done-criteria, and the per-phase QA checklist is the grader pass made mechanical. Implied is unbuilt — so every field below is written down, not assumed.

Required order, top to bottom: **frontmatter → status table → table of contents → phases (each with observable todos) → per-phase QA checklist**.

````markdown
---
title: <Project> — Build Plan
status: Not started | In progress | Blocked | Shipped
owner: <name>
created: <YYYY-MM-DD>   # UTC
updated: <YYYY-MM-DD>   # UTC — bump every time the plan changes
reversibility: Easy | Costly | One-way door — <one line of why>
---

# <Project> — Build Plan

| Most recently completed phase | What's next |
| --- | --- |
| — (not started) | Phase 1: <name> |

## Table of contents
- [Phase 1: <name>](#phase-1-name)
- [Phase 2: <name>](#phase-2-name)
- [Phase 3: <name>](#phase-3-name)

## Phase 1: <name>
**Goal:** <one observable outcome this phase delivers — not "work on X">

- [ ] <observable todo: names a checkable output or artifact>
- [ ] <observable todo>
- [ ] <observable todo>

### Phase 1 — QA checklist
- [ ] Every todo above produced its checkable output (no orphan tasks)
- [ ] Tests written **and run** — point to the execution artifact, not an assertion
- [ ] Diagnosable: logs + correlation id present; every loop has a stop condition
- [ ] Blast: each risky step names undo-class + shield + tripwire (or explicit "none")
- [ ] Status table and `updated:` date refreshed before this phase is marked done

## Phase 2: <name>
...
````

Filling it:

- **Frontmatter** — the at-a-glance contract. Keep `status`, `updated`, and `reversibility` honest; a stale `updated` date is the first sign the plan drifted from reality.
- **Status table** — exactly two columns, one row. It is the single source of truth for "where are we"; update it as the *last* step of finishing a phase, never before. Don't expand it into a multi-row log — that's what phases are for.
- **Phases** — split by observable milestone, not by calendar. Apply the Minimal pillar to phase count too: only as many phases as the work earns. Each phase has one `**Goal:**` line stating the outcome it delivers.
- **Observable todos** — every `- [ ]` names a checkable output, not an activity. "Add retry cap of 5 to the reconciler loop" passes; "improve reliability" fails. Use the `- [ ]` hyphen prefix (house Checklist standard), never bare `[ ]`.
- **Per-phase QA checklist** — closes each phase against the four pillars. It is Proof's editor/grader separation per phase: the boxes are checked by running things, not by the author asserting done. A phase isn't complete until its QA checklist is.

## Output format (Review mode)

Lead with the verdict in one line. Then findings, ordered by severity, then quick wins first within a severity. Keep it tight — clean plans get a short list, not a manufactured one.

**Verdict:** **Ship** · **Ship with conditions** · **Block** — [one sentence: the load-bearing reason].

**Findings:**

| Loc | Pillar | Severity | What breaks | Cheapest fix |
| --- | --- | --- | --- | --- |
| §x.y | Blast | Block | One-way migration with no rollback named | Add a dual-write window + a row-count tripwire before cutover |
| §x.z | Proof | Fix | "Improves sync" has no done-criterion | State the measurable signal (e.g. drift count → 0 over 3 runs) |

Severity: **Block** (cannot build safely as written — unguarded one-way door, no done-criteria, unbounded loop) · **Fix** (change before v1.x ships) · **Note** (improvement, optional).

**Quick wins:** [the 1–3 findings fixable in a line of doc, listed as `- [ ]` so the author can tick them off.]

## Principles

**Implied is unbuilt.** A plan gets credit only for what it states. "Obviously we'll log it" is a Diagnosable failure; write it down or it won't exist.

**Editor and grader are different roles.** The strongest constraint in the whole lens is Proof's separation: done is defined by something the author can't fudge. Keep them apart.

**Price the one-way doors loudest.** Reversible mistakes are cheap; irreversible ones are the only ones worth slowing down for. A tweak that can't be undone is not a tweak.

**Cut scope before breaking a corner.** When the plan is overloaded, the Minimal pillar and scope-reduction beat heroics. Defer to `iron-triangle` when the tension is explicitly fast/cheap/good.

**Stop conditions are not optional.** Any loop in the plan — retry, fix-iterate, agent relay — names its cap. Unbounded means undefined.

**Separate what you saw from what you expect.** Observed evidence and predicted behavior are different epistemic objects; a plan that blends them is lying to its future reader.

**Don't manufacture findings.** A genuinely clean v1.x doc gets "Ship" and a short list. The lens enforces a standard, not a quota of objections.

## Example — reviewing a v1.x build doc excerpt

Input (abridged):

> **§3 Nightly order reconciler.** A cron job runs each night to reconcile order state against the upstream system. For each order it pulls upstream status and updates `wp_orders` to match. On mismatch it retries until the write succeeds. This makes order state reliable.

Output:

> **Verdict:** **Block** — a nightly DELETE/UPDATE against the orders table with an unbounded retry, no tripwire, and no measurable "reliable" can corrupt order state with no way to know or stop it.
>
> **Findings:**
>
> | Loc | Pillar | Severity | What breaks | Cheapest fix |
> | --- | --- | --- | --- | --- |
> | §3 | Diagnosable | Block | "retries until the write succeeds" is an unbounded loop | Add a 5-failure hard stop / 10-total cap, then dead-letter the order |
> | §3 | Blast | Block | Bulk overwrite of `wp_orders` is costly-to-one-way with no shield/tripwire | Run in observe mode first; add a row-count + mismatch-rate tripwire before any write mode |
> | §3 | Proof | Fix | "makes order state reliable" has no done-criterion | Define it: drift count → 0 across 3 consecutive runs, logged |
> | §3 | House (UTC) | Fix | "each night" has no timezone | Pin the schedule to UTC; document the local display offset separately |
> | §3 | House (write path) | Note | Reconciler is a second writer to `wp_orders` | Name the single write path, or gate the reconciler behind the same one |
>
> **Quick wins:**
> - [ ] Add the loop cap (§3) — one clause.
> - [ ] Pin "each night" to UTC (§3) — one word.
> - [ ] Replace "reliable" with the drift-count criterion (§3) — one sentence.

## What success looks like

The author sees, before any code exists, exactly where the plan is a wish rather than a build: the loop with no cap, the migration with no rollback, the task that can't prove it's done. The best outcome is a v1.x doc that ships fast *because* its risky parts were priced up front — not one that ships fast and pays later.

codex
The graph service isn’t exposed in this consult runtime, so I’m using its mandated fallback: targeted source reads and literal searches, with exact line citations. The key bet I’m testing is whether “hosted is the single writer” is actually enforced atomically, rather than merely observed before a local writer starts.
exec
/bin/zsh -lc "rg -n \"wave[_-]reconcile|ROADMAP-DASHBOARD|LEADERBOARD|Lessons Learned|test receipt|receipts|generation|settings|dashboard-staleness\" --glob '"'!releases.sql'"' --glob '"'!*.db'"' . | head -n 500" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
./HARNESS-MODELS-REGISTRY.md:88:- For model IDs absent from Aider's model settings, `whole` format can silently discard a valid unified
./HARNESS-MODELS-REGISTRY.md:175:| **2026-08-22** | Aider + OpenRouter + `stealth/ox-alpha`, **reviewer role** | Added **C** | First use of this route, driven via `relay-drive.sh --review-once`, `ALLOW_PATHS=""`, worktree isolation ON, against `skills/ci-doctor/benchmark-runners.sh` (GH-161, PR #162). **R1: Blocked, correctly.** The turn-taker's `--artifact-file` seeding hadn't landed in the reviewer's context yet; the model declared `swept file: no` and refused to fabricate `[Pass]` findings against code it hadn't read — the honest failure mode, not a hallucination. **R2 (re-run after the artifact was seeded): the strongest first-attempt content seen from a new route.** Full 162-line static read, `swept file: yes`, verdict *Changes requested* with 2 `[Blocker]`, 4 `[Should]`, 5 `[Nit]`, 5 cited `[Pass]`. **Every finding verified true** against the real file before the operator acted: a `sed`-vs-literal mismatch that could silently commit a byte-identical no-op benchmark (undermining the tool's entire premise — GH-161's own header claims this exact failure mode impossible), and an unfiltered `gh run list --branch` pickup that could grab a wrong (push-triggered fast-lane, or cancelled) run instead of the dispatched one. Both confirmed by direct code inspection plus a targeted smoke test reproducing the reviewer's exact repro case (`runs-on: [self-hosted, linux]`) before fixing. Zero hallucinated findings; zero uncited Passes. **Delivery — mixed, root cause identified, not a model defect.** R1→R2 required a manual re-seed (environment/tooling gap). The R3 re-sweep (verifying the Producer's fixes) **timed out at the 900s wall-clock cap** (`aider-turn` exit 7) — but the turn's own log shows the model generated a full, well-formed second review in one clean LLM call (8.4k sent / 29k received, no retries) before the kill. Root cause: `aider-turn` ran `openrouter/stealth/ox-alpha` under Aider's default `whole` edit format (not in Aider's `model-settings.yml`), and the model wrote its response in diff-style (`+`-prefixed) lines, which `whole` format cannot parse as a file replacement — no error, no reflection, the turn simply idled with a correct response already sitting unused in the log until the wall-clock kill. This is the pre-existing, already-documented GH-118 edit-format quirk (see `skills/open-router/SKILL.md` and `relay-automation/README.md`, now updated with this model), not a reasoning or reliability failure of the model itself — the fix is `AIDER_FLAGS=--edit-format diff`, applied proactively for any new/unlisted OpenRouter model going forward. **Net: content quality is the strongest first-attempt showing of any route in this registry (2 real Blockers, zero hallucination, zero uncited Passes, twice); the one incomplete turn was a known, fixed harness-configuration gap, not the model.** Fixes verified independently (`bash -n`, `shellcheck -S error`, targeted smoke tests) rather than by the stalled R3 turn. **R3 re-run with `AIDER_FLAGS=--edit-format diff` applied: a second, different delivery failure.** Edit format was no longer the blocker, but the model then attempted an off-lane edit (outside the reviewer's `ALLOW_PATHS=""` scope) — `relay-turn-lib.sh`'s containment correctly discarded it and failed the turn (exit 6). Safety boundary held; nothing was lost or corrupted. **Closing the loop here** (operator-set boundary, no further root-causing): two independent delivery failures across three turns (timeout, then a containment violation) against one clean, high-quality review (R2) is not yet a route to trust unattended. Grade holds at **C** — real intelligence, unproven delivery, now on its second distinct failure mode rather than a resolved one. Verification of PR #162's actual code fixes stands independently of this stalled automated loop and does not depend on it closing. [#161](https://github.com/HiQS-Labs/XYZ-forge/issues/161), [#162](https://github.com/HiQS-Labs/XYZ-forge/pull/162); relay `relay-system/2026-08-22/ci-doctor-qa-gh-161-pr-162.md`. |
./HARNESS-MODELS-REGISTRY.md:177:| **2026-08-22** | ATE 1-Hour Fuzz Campaign (GH-141 soak) | Policy & benchmark baseline recorded | Executed 60.0-minute automated testing campaign across all 7 turn shims with local Gemma 4 31B triage on LM Studio. Completed 143 full execution-and-classification cycles with zero crashes, hangs, or memory leaks; telemetry receipts archived to `TESTS-RESULTS/2026-08-22+GH-141/error_log.jsonl`. |
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:7:   - Hosted wave-reconcile.yml is the single normal landing writer for development.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:8:   - Local wave_reconcile.py becomes a protected fallback. Before execution, check if hosted workflow wave-reconcile.yml is in-flight (using gh run list --workflow wave-reconcile.yml) to prevent concurrent write races.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:9:   - Avoid redundant marathon plan generation in wave_reconcile.py when inputs are unchanged.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:10:2. View decoupling & generation stamping:
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:11:   - Task branches stop committing routine ROADMAP-DASHBOARD.md and LEADERBOARD.md outputs.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:13:   - Embed exact generation metadata from releases.db settings into ROADMAP-DASHBOARD.md and LEADERBOARD.md headers so view consumers can verify freshness.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:14:   - githooks/dashboard-staleness-guard.sh: semantic validation of task-branch ledger writes (allowing clean renders without committed dashboards; refusing dropped/corrupted rows; and refusing routine dashboard commits on task branches unless renderer source is modified).
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:16:   - Add --pre-merge flag to wave_reconcile.py to validate closing active docs (under PROJECT/2-WORKING/) have non-empty ## Lessons Learned, valid frontmatter, and test receipts BEFORE merge.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:17:   - Red control: doc missing ## Lessons Learned fails pre-merge check with exit code 5.
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:23:2. How should githooks/dashboard-staleness-guard.sh distinguish between legitimate renderer changes (where committing dashboard is expected/required) vs routine task branches (where committing dashboard causes merge collisions and should be refused)?
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:24:3. What is the cleanest backward-compatible syntax for generation stamping in ROADMAP-DASHBOARD.md and LEADERBOARD.md?
./relay-system/2026-09-10/gh496-pr2-plan-qa-082928/gh496-pr2-plan-qa.PROMPT.txt:25:4. Are there subtle traps with wave_reconcile.py --pre-merge doc discovery or test receipt verification?
./relay-system/2026-09-02/gh399-plan-qa-codex.md:59:- [Blocker] Phase 2 is not buildable as written against the present control flow. `deepseek-turn.py:177` rejects every provider absent from `PROVIDER_ROUTES` *before* the token claim, and `:209`/`:212` call `provider_route()` again before key loading and overlay generation; `generate_patch_overlay()` also obtains its URL from that table at `:97-100`. “Unknown table provider + both profile fields is accepted” therefore needs one specified route-resolution contract, its call sites (including the pre-claim guard), and its key-file behavior. Otherwise a perfectly plausible overlay-only change still exits 2.
./relay-system/2026-08-27/gh75-jog-drive.md:26:Verified: `bash test/gh75-dashboard.sh` all pass independently; dashboard renders both panels + trust header, read-only (no generation bump). Follow-up nit: issue asked for `--out PATH`/`--open` flags and a docs/dashboard.html default — verb currently prints to stdout only.
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:209:- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`)
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:224:3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is the frozen legacy file — do not read it for current state or edit it.)
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:347:`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`, and
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:354:- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:355:- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:367:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:1360:     7	.claude/settings.local.json
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:2095:   158	  with `releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`,
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:2199:    42	- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-09-03/consult-427-crash-233636/consult-427-crash.codex.md:2230:    73	12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-09-02/gh123-cancel-linux-rc-qa.md:15:Diff: `LEADERBOARD.html`, `LEADERBOARD.md`, `RELEASES-PREVIEW.html`, `releases.db`, `releases.sql`.
./relay-system/2026-09-02/gh123-cancel-linux-rc-qa.md:66:   `[Nit]` It is harmless and should be left as honest history. The `releases check` validation enforces `before == previous after`. A contentless update simply produces a receipt where the `before` and `after` digests are identical (as seen in `op_receipts` row 390: `5ec15...4617` -> `5ec15...4617`). Scrubbing it manually would require forging the receipt chain. 
./relay-system/2026-09-02/gh123-cancel-linux-rc-qa.md:72:   Yes. Because no `roadmap_items` rows were modified, `ROADMAP-DASHBOARD.md` did not need regeneration and is perfectly consistent with the DB. The generated views are not stale.
./relay-system/2026-08-18/merge-order-230056/merge-order.PROMPT.txt:21:| **#44** | `feat(GH-42)`: add Commandcode relay turn-taker | development | 11 | +371/−2 | Touches `validate.sh`, `ROADMAP.md`, `ROADMAP-DASHBOARD.md`, `CHANGELOG.md`, **`relay-pkg.tar.gz`**, new `relay-automation/commandcode-turn.sh` + `utils/py/commandcode-turn.py` + `test/commandcode-turn.sh`. |
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:47:- Definition of Done: the plan (issue #402 body, revision v4) is sound enough to build against — every load-bearing claim is verified or explicitly marked unverified; no architectural defect in the catch system, settings unification, GitHub API usage, failure semantics, or security posture; the phasing is executable as ordered.  [Unverified — no citation]
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:58:8. **Security:** public repo + fine-grained PAT + fork-PR reachability — anything in the plan that could leak the token, the settings, or operator-private data (clone-dir names, board contents)?
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:78:`wave_reconcile.py`). Pre-existing defects found in the artifact beyond the findings below: none.
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:113:8. **Security:** no leak path found — settings/state/plist all live in `$HOME` or gitignored
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:167:  handling) — before any token choice is baked into settings or plist.
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:198:- `[Pass]` RELEASES DB inventory is accurate — probe: 99 rows, ✅47 / 🆕36 / 🚧11; `op_receipts`
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:200:  (`state_digest_before/after`, 403 receipts); `jog_queue` has `gh_number/status/attempt_count/
./relay-system/2026-09-02/gh402-board-sync-plan-qa.md:212:Producer round; the architecture itself (union catch + sensitive-sensors/precise-writer + settings
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:82:- **Auditor (Tier 3):** bounded-scope full verification with a current graph generation, complete relevant pagination, both call directions and broader relationships when material, plus explicit unresolved limitations.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:87:- Before delegating, query the graph and coverage in the parent. Pass the tier, exact project, generation/freshness, bounded scope, queries and pagination state, qualified symbols, paths, call-chain findings, coverage ranges/reasons, source fallback already performed, and unresolved questions to the child.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:131:- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`); the RELEASES DB (`releases.db` via `releases.sql`) is the source of truth (`ROADMAP.md` retired per GH-269)
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:145:3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is retired — the RELEASES DB is the single source of truth.)
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:268:`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:275:- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:276:- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:288:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:500:    65	## Lessons Learned (For Future Agents)
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:681:   179	   - *Doc Promotion:* If a working doc was created, update frontmatter to `status: completed` and move to `PROJECT/3-COMPLETED/` (or let `wave_reconcile` handle it).
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:816:    42	- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:847:    73	12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:950:    66	8. before moving to `PROJECT/3-COMPLETED`, a `## Lessons Learned (For Future Agents)` section appended to capture quirks and gotchas
./relay-system/2026-09-06/gh473-unstuck-architecture-164154/gh473-unstuck-architecture.codex.md:1110:    72	## Lessons Learned (For Future Agents)
./relay-system/2026-08-31/gh349-phase2-review-qa.md:166:- Widening `URL_EXTRACT_RE` to accept PR URLs (`pull`/`pulls`) allows legacy blocks that recorded PR URLs in `GH_URL:` to populate `gh_release_url` rather than being dropped to `gh-url-unparsed`. Because PR URLs represent valid GitHub release pointers and `cmd_import` records grandfather receipts for normalization, this change is a clean and safe improvement with zero adverse impact on existing tables.
./relay-system/2026-08-31/gh123-sleep-readiness-audit.md:123:| [test/gh239-hq-status-releases-mode.sh:31](test/gh239-hq-status-releases-mode.sh#L31) | `1` | Forces `ROADMAP-DASHBOARD.md` mtime strictly newer than `releases.db`. Filesystem clock granularity — a poll cannot make the second tick. |
./relay-system/2026-08-27/gh267-express-qa.md:22:2. **Order integrity.** Are the writes ordered so the documented traps are structurally impossible: evidence sha exists before `manifest ship` (step 9 after merge), issue closed before reconcile (step 10 before 11), capture doc born complete matching `wave_reconcile.py`'s promotion regex (`##\s+Lessons\s+Learned`, case-insensitive — check `validate_and_update_doc`)? Cite line numbers.
./relay-system/2026-08-27/gh267-express-qa.md:27:7. **Anything else** wrong, missing, mis-scoped, or over/under-engineered vs the #267 v2 spec — including the `build_offline_manifest` fallback (does it correctly omit unresolvable numbers so wave_reconcile treats them as unknown?) and the `.tick` telemetry shape.
./relay-system/2026-08-27/gh267-express-qa.md:95:**express.py:58–59** lists: `CHANGELOG.md`, `PROJECT/`, `ROADMAP.md`, `ROADMAP-DASHBOARD.md`, `RELEASES.generated.md`, `LEADERBOARD`, `RELEASES-PREVIEW`.
./relay-system/2026-08-27/gh267-express-qa.md:131:The reasoning (keeping wave_reconcile --pr alive, auto-closing the linked issue) is sound and consistent. No issue here.
./relay-system/2026-08-27/gh267-express-qa.md:147:**express.py:396–416** — issues resolvable via `gh issue view` carry live state; unresolvable ones are omitted. Per wave_reconcile's GH-202 contract, unknown numbers = "promote as before" (no state assertion). This is correct.
./relay-system/2026-08-27/gh267-express-qa.md:161:| Doc born complete matching wave_reconcile | Capture doc template at 314 has `## Lessons Learned (For Future Agents)`; wave_reconcile's `validate_and_update_doc` at **wave_reconcile.py:339** uses `re.search(r"##\s+Lessons\s+Learned", content, re.IGNORECASE)` — matches. | express.py:314 matches wave_reconcile.py:339 |
./relay-system/2026-08-27/gh280-jog-marathon-plan-qa.md:48:  (1) the Jog/Preflight/Marathon/wave-reconcile ownership split against the cited code and Recon Map;
./relay-system/2026-08-27/gh280-jog-marathon-plan-qa.md:75:- `[Pass]` The Jog/Preflight/Marathon/wave-reconcile ownership split aligns with the Recon Map. Verified via "Marathon becomes the only owner of reviewed execution... Jog records a receipt-backed projection" (`GH-280-JOG-MARATHON-RECALIBRATION.md:55-57`).
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1667:    15	  - id: gh168-wave-reconcile-scope
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1668:    16	    name: "GH-168: wave_reconcile — unrelated pre-existing drift warns, PR-attributable drift stays fatal, idempotent double-run"
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1670:    18	    brief: PROJECT/2-WORKING/MARATHON-2026-08-24-GH2-50-168/brief-gh168-wave-reconcile-scope.md
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1671:    19	    artifact: utils/py/wave_reconcile.py,test/gh168-wave-reconcile-scope.sh,validate.sh
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1679:    27	    depends_on: gh168-wave-reconcile-scope
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1794:  4815	                                             "(Phase 0+1: side-by-side generation only)")
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1798:  4819	    sp = sub.add_parser("init", help="create the DB + dump; settings default lenient")
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1859:  4880	                         help="commit, PR, or test receipt (empty is refused)")
./relay-system/2026-09-03/gh419-enforcement-120203/gh419-enforcement.codex.md:1899:  4920	    sp = sub.add_parser("gen", help="side-by-side generation (Phase 0: NEVER writes RELEASES.md)")
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:62:- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`); the RELEASES DB (`releases.db` via `releases.sql`) is the source of truth (`ROADMAP.md` retired per GH-269)
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:76:3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is retired — the RELEASES DB is the single source of truth.)
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:199:`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:206:- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:207:- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:219:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:264:- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:295:12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:432:PROJECT/2-WORKING/GH-299-GEN4-FUZZING-ATE.md:130:- **Idempotence & Monotonicity Oracle**: Identical state and zero duplicate receipts on repeated execution.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:454:PROJECT/1-INBOX/GH-446-MARATHON-PLAN-WRITE-GUARD.md:31:Zero-State Oracle), and causes `wave_reconcile` runs to leave an untracked plan file in clean clones.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:460:/bin/zsh -lc "rg -n -i 'needle|rebalanceos|XYZ.CLIO|orion' ROADMAP-DASHBOARD.md PROJECT/1-INBOX releases.sql | head -55; nl -ba GUIDING-PRINCIPLES.md | head -65; rg --files | rg -i 'clio|467|needle'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-86231-968w76hh
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:469:releases.sql:513:INSERT INTO roadmap_items(global_id, repo_gid, gh_number, title, section, position, status_marker, complexity, risk, effort, doc_path, issue_url, raw_text, first_seen, updated_at, rating_pri, rating_sev, rating_appeal, rating_effort, rating_ovr) VALUES('rmi-01M1T8H5J5P8TZ9Y5M194E91JN', 'repo-01M0BTBRJ0PZF51EK6PCRJ20FS', '454', 'wave_reconcile dies on an unnamed release, and enforces PDDA full-mode on an observe-mode repo', 'Queue / parked intake', '54', '🆕', NULL, NULL, NULL, 'PROJECT/1-INBOX/GH-454-RECONCILE-GATE-DEFECTS.md', 'https://github.com/HiQS-Labs/XYZ-forge/issues/454', '- **GH-454 · wave_reconcile dies on an unnamed release, and enforces PDDA full-mode on an observe-mode repo** 🆕 **captured 2026-09-05 via /file-xyz-bug from `rebalanceOS`** — two defects, one run, each rolling the whole wave back: `export_timeline.py:278` does `(codename or version).lower()` and raises on a release row with both NULL; `run_validation_gate()` fails on any stdout line containing `ERROR`, ignoring `pdda.sh`''s mode-aware exit code and so enforcing `full` on a repo that declares `observe`. Both have workarounds the caller must already know. With GH-215''s surviving half, this is what blocks GH-421 unattended operation. rated 72/78/80/78 — [GH-454-RECONCILE-GATE-DEFECTS.md](PROJECT/1-INBOX/GH-454-RECONCILE-GATE-DEFECTS.md)', '2026-09-06T02:25:03Z', '2026-09-06T02:25:03Z', '72', '78', '80', '78', NULL);
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:472:PROJECT/1-INBOX/recon-harness-root-resolution.md:132:Every shell that `eval`s `find-harness.sh --env` (operators, all relay/consult/hq/file-xyz-bug/marathon-triage/10days skill sessions, 8 script callers), the 5 Python turn shims via `rtl.resolve_turn_root`, `wave_reconcile`/`jog_run`/`marathon_plan`/`swarm_preflight`/`marathon_drive` via four ad-hoc `harness_home` derivations, `bin/tick`'s event-log location, and the three consumer repos (`rebalanceOS` ×5, `LTVera-Pandas` ×4, `aegis-sleuth-slack-bot` ×3) that run all of the above from a `.xyz/` copy stamped by `xyz-vendor.sh` and audited by two disagreeing staleness checks.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:522:    42	- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:558:- **[Pass] Full argument generation is unnecessary for an advisory classifier.** A context → action-category model can provide useful suggestions without emitting executable JSON. That is consistent with “least code that clears the bar,” which explicitly retains correctness as a requirement (`GUIDING-PRINCIPLES.md:63`). Neither full schema validation nor arbitrary argument generation must be part of this first experiment.
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.codex.md:583:- **[Pass] Full argument generation is unnecessary for an advisory classifier.** A context → action-category model can provide useful suggestions without emitting executable JSON. That is consistent with “least code that clears the bar,” which explicitly retains correctness as a requirement (`GUIDING-PRINCIPLES.md:63`). Neither full schema validation nor arbitrary argument generation must be part of this first experiment.
./relay-system/consult-gh234-question.md:22:- `releases.sql` (skim structure: how mergeable is the text dump really — INSERT ordering, autoincrement ids, position-UNIQUE tables like doc_lines/legacy_lines, append-only trigger tables like op_receipts)
./relay-system/2026-09-06/needle-oracle-140920/needle-oracle.agy.md:2:No, stripping the tool arguments does not fundamentally break the Oracle's usefulness as a "what to do next" sentinel, and it is likely the only realistic path for a model of this size. A 45M parameter model lacks the capacity to reliably generate syntactically valid, context-accurate JSON arguments without hallucination. By reducing the problem to predicting just the tool name string, you convert a highly complex generation task into a much simpler sequence-to-sequence or classification task, which is perfectly suited for a fast, low-latency edge model running on the ANE.
./relay-system/2026-08-31/gh353-router-audit-qa.md:49:  2. For releases mode repos, detects stale `ROUTER.md` files where `ROADMAP.md` is treated as active or `ROADMAP-DASHBOARD.md` is missing.
./relay-system/2026-08-31/gh353-router-audit-qa.md:72:- [Blocker] Releases-mode validation is not scoped to the required blocks and can report a stale router as clean. A `ROADMAP-DASHBOARD.md` mention anywhere satisfies `has_dashboard`, while an omitted `ROADMAP.md = ...` role entry skips the frozen check entirely; startup detection only recognizes one exact numbered `Read ROADMAP.md` spelling (`.relay-artifacts/router_audit.py:71-103`). Fix: parse the bounded `## Role split` and `## Startup sequence` sections, require the dashboard and frozen/source-of-truth declarations in Role split, reject active roadmap reads in Startup, and add negative tests for mentions outside those sections, missing role entries, case/format variants, and absent Startup guidance.
./relay-system/2026-08-31/gh353-router-audit-qa.md:90:  - Required `ROADMAP-DASHBOARD.md` and frozen/legacy/DB declaration specifically within `## Role split`.
./relay-system/2026-08-31/gh353-router-audit-qa.md:91:  - Required `ROADMAP-DASHBOARD.md` and rejected active roadmap reads within `## Startup sequence`.
./relay-system/2026-08-31/gh353-router-audit-qa.md:94:  - Rejects `ROADMAP-DASHBOARD.md` in `Role split` and `Startup sequence` as well as false-frozen `ROADMAP.md` declarations regardless of filesystem leftovers.
./relay-system/2026-08-31/gh353-router-audit-qa.md:119:- [Blocker] Legacy auditing does not enforce its own active-roadmap contract and still misses false-frozen Startup references. Missing Role split/Startup sections are accepted, and Startup checks only for `ROADMAP-DASHBOARD.md`, so a Startup line declaring `ROADMAP.md` frozen passes (`.relay-artifacts/router_audit.py:184-219`). Remediation correspondingly never creates missing legacy sections or inserts an active ROADMAP step, yet the weak post-audit can certify that incomplete result (`.relay-artifacts/router_audit.py:337-367`, `.relay-artifacts/router_audit.py:392-395`). Fix: require both bounded sections in legacy mode, require an active `ROADMAP.md` role and Startup directive, reject frozen/legacy/releases-source declarations in both, and create/repair missing sections under `--fix`; cover each false-clean and remediation path.
./relay-system/2026-08-31/gh353-router-audit-qa.md:185:  - Rejected all releases-mode tokens (`releases.db`, `releases.sql`, `ROADMAP_SOURCE=releases`, `ROADMAP-DASHBOARD.md`, `frozen`, `legacy`) in both sections.
./relay-system/2026-08-31/gh353-router-audit-qa.md:252:- [Blocker] Releases-mode auditing does not require affirmative dashboard guidance. A Role split declaration such as ``ROADMAP-DASHBOARD.md = obsolete; do not read`` satisfies `has_dashboard`, and a Startup line saying `Do not read ROADMAP-DASHBOARD.md` satisfies `has_dashboard_startup`; neither predicate evaluates polarity or active/current-work semantics (`.relay-artifacts/router_audit.py:174-186`, `.relay-artifacts/router_audit.py:204-215`). Fix: require a non-negated dashboard/release-ledger source-of-truth declaration in Role split and a non-negated current-work directive in Startup, then cover obsolete/do-not-read false-clean cases and their remediation.
./relay-system/2026-08-31/gh353-router-audit-qa.md:271:  - Startup sequence requires affirmative non-negated directive to read/consult `ROADMAP-DASHBOARD.md` (`has_affirmative_dashboard_startup`), rejecting `do not read` directives.
./relay-system/2026-08-31/gh353-router-audit-qa.md:294:- [Blocker] Dashboard “affirmative” checks do not establish current-work guidance. A Role declaration such as ``ROADMAP-DASHBOARD.md = historical archive only`` passes the short denylist, and Startup text such as `Read ROADMAP-DASHBOARD.md only for historical reference` satisfies the verb regex; together they can report clean even though neither directs the operator to the dashboard for current state (`.relay-artifacts/router_audit.py:116-122`, `.relay-artifacts/router_audit.py:185-219`). Fix: require affirmative current-work/generated-ledger semantics with clause-scoped polarity in both sections, reject historical-only/not-source-of-truth contradictions even when a separate positive mention exists, and add paired false-clean/remediation tests.
./relay-system/2026-08-31/gh353-router-audit-qa.md:338:- [Blocker] Releases-mode dashboard validation still does not establish current-state guidance. `is_affirmative_dashboard_role_line` accepts any non-denylisted declaration because its positive `dashboard` alternative matches the filename itself, so ``- `ROADMAP-DASHBOARD.md` = historical archive`` passes; Startup likewise accepts `Read ROADMAP-DASHBOARD.md for historical context` because it requires only a read verb and excludes a few exact historical phrases (`.relay-artifacts/router_audit.py:121-148`). Together with a canonical frozen `ROADMAP.md` declaration, those stale instructions can audit clean. Fix: evaluate the declaration text after the filename and require explicit generated/current-roadmap semantics in Role split plus explicit current-work/current-state semantics in Startup; reject historical/archive/context semantics clause-wide and add these exact paired audit/fix regressions.
./relay-system/2026-08-31/gh353-router-audit-qa.md:379:- [Blocker] The claimed affirmative dashboard check accepts a directly negated generated-view declaration. For example, ``ROADMAP-DASHBOARD.md = not generated; current view lives elsewhere`` passes because `not generated` is absent from the denylist while both `generated` and `current view` independently satisfy the positive regex (`.relay-artifacts/router_audit.py:120-132`). Fix: evaluate dashboard clauses and polarity before accepting generated/current-state semantics, reject contradictions such as `not generated`, `not current`, and “source lives elsewhere,” and test initial audit plus post-fix canonicalization.
./relay-system/2026-08-31/gh353-router-audit-qa.md:400:  - Added test case verifying `ROADMAP-DASHBOARD.md = not generated; current view lives elsewhere` is rejected.
./relay-system/2026-08-31/gh353-router-audit-qa.md:422:- [Should] The dashboard Startup predicate does not actually require current-work/current-state semantics: any non-denylisted read verb passes, so `Read ROADMAP-DASHBOARD.md for deployment instructions` satisfies the purported current-work contract (`.relay-artifacts/router_audit.py:138-152`, `.relay-artifacts/router_audit.py:278-287`). Fix: require an affirmative current-work/current-state/active-effort purpose, rather than inferring it from a filename and verb, and add negative audit + canonicalization coverage.
./relay-system/2026-08-31/gh353-router-audit-qa.md:435:  - Scoped declaration parsing to lines where `ROADMAP.md` / `ROADMAP-DASHBOARD.md` is the declared subject (`OWNED_ROADMAP_DECL_RE`, `OWNED_DASHBOARD_DECL_RE`).
./relay-system/2026-08-31/gh353-router-audit-qa.md:462:- [Blocker] Releases dashboard polarity still has direct false-clean forms. ``ROADMAP-DASHBOARD.md = not a generated view`` evades the exact `not generated` denylist while `generated` satisfies the positive test, and `Read ROADMAP-DASHBOARD.md for not current state` likewise satisfies the Startup purpose regex because Startup has no `not current` polarity check (`.relay-artifacts/router_audit.py:132-162`). Fix: parse the semantic clause after the dashboard subject, including intervening articles and negated purpose phrases, and require an affirmative generated/current-state claim before accepting it; cover both exact examples through audit and canonical post-fix output.
./relay-system/2026-08-31/gh353-router-audit-qa.md:463:- [Blocker] `--fix` still deletes valid custom Startup guidance merely because it mentions a roadmap filename. Releases remediation consumes every line containing `ROADMAP.md` or `ROADMAP-DASHBOARD.md`, while legacy remediation does the same for any roadmap-bearing line; thus a custom step such as ``4. Read `PROJECT/PDDA.md` for the `ROADMAP.md` governance contract.`` is silently replaced or dropped whenever unrelated drift triggers a fix (`.relay-artifacts/router_audit.py:468-478`, `.relay-artifacts/router_audit.py:534-550`). Fix: classify and replace only owned current-state roadmap directives, preserve non-owned/historical/governance lines byte-for-byte, and add the exact custom-step regression in both modes with before/after `cmp` assertions.
./relay-system/2026-08-31/gh353-router-audit-qa.md:484:  - Added test cases covering `ROADMAP-DASHBOARD.md = not a generated view` and `Read ROADMAP-DASHBOARD.md for not current state`.
./relay-system/2026-08-31/gh353-router-audit-qa.md:508:- [Blocker] The releases Role-split predicates still accept keywords without the required affirmative relationships. `ROADMAP.md = frozen legacy; releases.db is present for compatibility` passes because any non-negated DB token sets `has_affirmative_db_clause`, and `ROADMAP-DASHBOARD.md = generated deployment manifest` passes because the bare word `generated` establishes the dashboard contract (`.relay-artifacts/router_audit.py:156-167`, `.relay-artifacts/router_audit.py:285-315`). Fix: require an affirmative releases-DB source-of-truth assignment and an affirmative generated *roadmap-ledger view* declaration, not token presence; add both exact false-clean cases through `--check` and canonical `--fix` regressions.
./relay-system/2026-08-31/gh353-router-audit-qa.md:525:  - Required affirmative declaration of `ROADMAP-DASHBOARD.md` as generated view of the roadmap ledger, rejecting bare keyword hits (`generated deployment manifest`).
./relay-system/2026-08-31/gh353-router-audit-qa.md:592:- [Blocker] Dashboard Startup purpose remains line-scoped rather than directive-clause-scoped. In `Read ROADMAP-DASHBOARD.md for deployment instructions; TEAM.md tracks current work`, the dashboard clause passes the verb checks and the unrelated second clause supplies `current work` because the positive-purpose regex searches `line`, not `clause`; the stale guidance can therefore audit clean (`.relay-artifacts/router_audit.py:199-215`, `.relay-artifacts/router_audit.py:354-370`). Fix: require the current-work/current-state purpose in the same dashboard-bearing affirmative clause, and test initial failure plus canonical repair.
./relay-system/2026-08-31/gh353-router-audit-qa.md:616:  - Added test case covering `Read ROADMAP-DASHBOARD.md for deployment instructions; TEAM.md tracks current work`.
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:57:- `PROJECT/2-WORKING/GH-402-BOARD-SYNC.md` — execution record + receipts (Phase 0 spike, first live write)
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:63:   empty-input refusal; settings via the `device_config.json` `board_sync` object with the
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:102:   empty-input refusal ✅ but with a residual void gap (S-3 below); settings via `board_sync` object +
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:115:   receipts at `GH-402-BOARD-SYNC.md:55-61`. Gaps: S-4 (core invariant unpinned), S-5 (BSD-only sed), N-2.
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:122:   multiplies these paths across ~7 adapters; receipts-only evidence does not scale to that. (B-1 must
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:178:- **[Nit] N-5 — `adapters` key from the plan's sample settings object (plan line 110) is absent from
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:186:- **[Pass] P-4 — N3 settings tier:** env > `board_sync` object > defaults implemented in-tool
./relay-system/2026-09-02/gh402-board-sync-impl-qa.md:197:  witnessed red genuinely fails the suite if the mutation doesn't take (`test:132-138`); live-write receipts
./ci-local.sh:213:settings_json_valid() {
./ci-local.sh:218:  done < <(git ls-files -- '.claude/settings*.json')
./ci-local.sh:378:step "settings JSON"                settings_json_valid
./relay-system/2026-08-31/cleanup-runbook-sharpen.md:214:Note: turn 1 technically failed exit 6 (off-lane artifact regeneration inside the isolated
./relay-system/2026-09-06/gh460-plan-qa.md:82:Scope: read the entire GH-460 plan and all four source/test files named in Setup. Static review only; no resolver, campaign, mutation, test suite, or git command executed. MCP list_projects returned no index for this worktree or its GH-460 parent clone; exact local source reads are the fallback, with no graph-generation/completeness claim. The issue/comment and referenced primary-clone recon are not available here, so historical run/commit claims remain unverified.
./relay-system/2026-09-06/gh460-plan-qa.md:86:- [Should] **Make the red control attributable and restoration unconditional.** Plan `:93`–`:95` says sed-inject on miss and expect any nonzero exit, but does not guarantee a seeded mutant reaches `resolve-model-alias.sh:128`; usage exits earlier at `:52`, and substring matches exit at `:121`. Fix: pin a witnessed miss in the same smoke input set, assert the replacement changes exactly the terminal miss exit, install cp-backup restoration before mutation (including failure/interruption), and require telemetry showing the oracle caught rc 3 for that input. A syntax error, timeout, or missing JSON must not qualify as the red witness. Fresh equivalent corpus/environment for baseline, red, and restored green is required: existing corpus seeds affect generation (`fuzz_engine.py:298`, `:122`). Resolver execution has no explicit git writes in its full 128-line body, but a `test/*.sh` run still belongs in a disposable full clone; the plan's task-clone blanket safety claim is insufficient.
./relay-system/2026-09-06/gh460-plan-qa.md:122:Scope: whole revised plan, recon and all four source/test files named in Setup read; registry/caller spans also inspected. Static review only; no artifact/source execution, mutations, tests, campaign or git commands. MCP list_projects (50/50, has_more=false) has no index for this worktree or its GH-460 parent; exact-source fallback used, without borrowing another checkout's generation or claiming graph completeness. Historical commits, external issue discussion and prior runs remain unverified. Plan citations below mean PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:157:Scope: whole plan, recon, resolver, wrapper, fuzz engine and existing gh346 fallback test read; registry and caller spans inspected. Static review only: no artifact/source execution, campaign, mutation, test suite or git commands. MCP list_projects returned all 50 entries (has_more=false), with no project for this worktree or its GH-460 parent; exact-source fallback used, no borrowed generation or graph completeness claim. External issue, historical commits and producer run claims remain unverified. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:161:- [Should] **Finish the local campaign recipe and green criteria.** Plan :78's “base argv = one placeholder” does not specify the mutable `--base` value; the placeholder belongs to the fixed target, while the engine separately shell-splits --base (utils/py/fuzz_engine.py:423,465). R3 :104–112 still lacks pinned seed values, a wrapper executed >=300 assertion, and explicit engine-success / fail-closed JSON / zero fail+anomaly requirements for green campaigns. Fix: provide one reusable invocation recipe with actual base value, resolver seeds, wrapper seed, repo-root cwd, timeout, LC_ALL value, fresh corpus and telemetry/summary paths; apply parsed executed floors and green criteria to every run. The engine's exit status alone is insufficient because :330–335 distinguishes counted failures from counterexamples and :470 exits on counterexamples only. Capturing these settings later in R3b is useful evidence, but does not define the recipe now.
./relay-system/2026-09-06/gh460-plan-qa.md:194:Scope: whole plan, recon, resolver, wrapper, fuzz engine and gh346 fallback test read; registry and caller spans inspected. Static review only; no artifact/source execution, tests, mutation, campaigns or git commands. MCP list_projects returned all 50 entries (has_more=false), with no index for this worktree or its GH-460 parent; exact-source fallback used, without a borrowed generation or graph-completeness claim. External issue, historical commits and producer run claims remain unverified. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:231:Scope: whole plan, recon, resolver, wrapper, fuzz engine and gh346 fallback test read; registry, shipped table and caller spans inspected. No artifact/source execution, campaign, mutation, test suite or git commands. One read-only system-utility probe used `/usr/bin/wc -c </dev/null`, yielding `<       0>` when bracketed for visibility; no probe file was created. MCP list_projects returned all 50 entries (has_more=false), with no index for this worktree or its GH-460 parent; exact-source fallback used, with no borrowed generation or graph-completeness claim. External issue, historical commits and producer run claims remain unverified. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:265:Scope: whole plan, recon, resolver, wrapper, fuzz engine and gh346 fallback test read; registry, shipped table and caller spans inspected. Static review only; no artifact/source execution, probes, campaigns, mutations, tests or git commands. MCP list_projects returned all 50 entries (has_more=false), with no index for this worktree or its GH-460 parent; exact-source fallback used without a borrowed generation or graph-completeness claim. External issue, historical commits and producer run claims remain unverified. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:361:Scope: whole current plan and relay history read, with review focused on the amendment and preservation of adopted requirements. Recon, resolver, wrapper, existing fallback test and relevant engine/registry/caller source inspected. Static review only: no artifact/source execution, probes, mutations, campaigns, tests or git commands. MCP list_projects returned 50/50 entries (has_more=false), without an index for this worktree or its GH-460 parent; exact-source fallback used, no borrowed generation or completeness claim. Historical commits, external issue and producer run claims remain unverified; without git comparison I cannot attest that no unrelated file changed. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:367:- [Should] **Make the shared run contract explicit after deleting the recipe.** R1 (:95–98) omits engine exit 0; R3 (:118–123) preserves seeds/floors but no longer pins base or timeout or explicitly requires the JSON flag. Fix: one shared behavior paragraph applying fuzz mode, base glm-5.2, repo-root cwd, timeout-budget 30, JSON capture, fresh empty corpus, shipped table/unset override and LC_ALL=C to smoke and both campaigns; require engine exit 0 plus valid nonempty summary and the respective floors/zero fail+anomaly for all. Also apply the environment policy to raw preconditions and wrapper observations, not only inside the resolver oracle. The CLI defaults to suite mode (fuzz_engine.py:421) and emits JSON only with the flag (:466–469), so these are substantive run settings, not serializer details.
./relay-system/2026-09-06/gh460-plan-qa.md:397:Scope: whole current plan and relay history read; focused on preservation of the adopted contracts. Recon, all four Setup source/test files, and relevant registry/table/caller spans inspected. Static review only; no artifact/source execution, probes, mutations, campaigns, tests or git commands. MCP list_projects returned 50/50 entries (has_more=false), with no index for this worktree or its GH-460 parent; exact-source fallback used, without borrowing another checkout's generation or claiming graph completeness. Historical commits, external issue and producer run claims remain unverified. Without git comparison, no assertion that unrelated files stayed unchanged is possible. Plan citations below mean PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:399:- [Pass] **Shared settings, oracle measurements and witnesses are restored.** Plan :77–106 now requires fuzz mode, base/cwd/timeout/JSON, fresh corpus, common environment, engine success plus parsed floors/zero fail+anomaly, first/absent/extra oracle argument mapping, byte-exact capture, strict measurement and stderr diagnostics. R2 :117–130 requires cp-backed restoration before exact one-site mutation and separate rc-3, LEAK, bare-newline, HIT-EMPTY, failed-wc/split-digit/empty-output witnesses plus padded-count acceptance. These align with the engine's argv insertion, stderr capture and JSON path (utils/py/fuzz_engine.py:223–244,326,466–470). Preserve these behavior contracts; no return to the inline Bash body is needed.
./relay-system/2026-09-06/gh460-plan-qa.md:428:Scope: whole current plan and relay history read; focused on the three round-8 restorations and preservation of adopted requirements. Recon, all four Setup source/test files, and relevant registry/caller spans inspected. Static review only: no artifact/source execution, probes, mutations, campaigns, tests or git commands. MCP list_projects returned all 50 entries (has_more=false), without an index for this worktree or its GH-460 parent; exact-source fallback used, with no borrowed generation or graph-completeness claim. External issue, historical commits and producer run claims remain unverified. Without git comparison, no assertion that unrelated files stayed unchanged is possible. Plan citations below refer to PROJECT/2-WORKING/GH-460-ATE-FUZZ-RESOLVER-CAMPAIGN.md.
./relay-system/2026-09-06/gh460-plan-qa.md:432:- [Pass] **The script disposition and adopted acceptance contracts survive the sweep.** Plan :25 now names the committed test oracle, consistent with :87–88. Shared run settings and fail-closed green criteria remain at :77–85; byte-exact measurement and stderr diagnostics at :95–107; registration and the >=20 floor at :109–116; attributable red/measurement/newline witnesses at :118–131; seeds and 500/300 campaign floors at :133–134; durable per-run evidence/provenance at :148–154. These match engine argv/telemetry/summary behavior at fuzz_engine.py:223–244,326,339,466–470 and the registry consumed at ci-local.sh:269. Preserve them; their presence is a specification pass, not witnessed runtime success.
./relay-system/2026-08-31/gh346-phase0-2-qa.md:307:- **[Pass]** Commit hygiene: the releases.sql/ROADMAP-DASHBOARD/LEADERBOARD churn is the roadmap
./relay-system/2026-08-31/gh346-phase0-2-qa.md:308:  intake row (`rmi-01M1CRE…`, properly receipted in `op_receipts`) per the AGENTS.md ledger rule;
./relay-system/2026-09-02/gh396-plan-review-qwen.md:28:4. `skills/relay-xyz/find-harness.sh` (whole file), `utils/py/wave_reconcile.py:25-70`,
./relay-system/2026-09-02/gh396-plan-review-qwen.md:32:   `test/gh358-wave-reconcile-vendored-paths.sh`.
./relay-system/2026-09-02/gh396-plan-review-qwen.md:62:11. **Repo-first `harness_tool` in a consumer that has its own `utils/`.** `wave_reconcile.harness_tool`
./relay-system/2026-09-02/gh396-plan-review-qwen.md:63:    (`utils/py/wave_reconcile.py:31-68`) returns `$REPO/utils/…` when it exists, else the harness copy.
./relay-system/2026-09-02/gh396-plan-review-qwen.md:144:`wave_reconcile.py:31-37` (`harness_home`) and `:40-70` (`harness_tool`) already have separate, documented precedence rules. The plan's Phase 2 extracts both into one `harness_paths.py` module. DeepSeek is right that a single module with "one documented precedence" risks conflating them. The docstring must explicitly state:
./relay-system/2026-09-02/gh396-plan-review-qwen.md:199:`wave_reconcile.py:40-70` (`harness_tool`) returns `$REPO/utils/…` when it exists, else the harness copy. The plan's Phase 2 extracts this as `resolve_tool(rel_path)` with the same repo-first order. A consumer repo that carries its own `utils/py/releases_app.py` or `utils/roadmap-dashboard.sh` — unrelated to the harness, same filename — would silently shadow the harness tool.
./relay-system/2026-09-02/gh396-plan-review-qwen.md:201:**Is this a real risk for the three consumer repos (rebalanceOS, LTVera-Pandas, aegis-sleuth-slack-bot)?** Low but non-zero. None of them ships `releases_app.py` at their root. However, the shared module's adoption surface is wider than three known consumers, and `test/gh358-wave-reconcile-vendored-paths.sh:128-131` explicitly pins the repo-first behaviour ("a canonical checkout must prefer its own copy") — that test deliberately expects a local `releases_app.py` to win over the harness copy. This is the existing contract for **harness tools** (the five files that live in both places).
./relay-system/2026-09-02/gh396-plan-review-qwen.md:205:- Or split into `resolve_tool(rel_path)` (repo-first, for wave_reconcile) and `resolve_harness_tool(rel_path)` (harness-first, for new consumers).
./relay-system/2026-09-06/gh457-model-aliasing-improvements.md:116:Review limits: the entire 44-line artifact was swept, including its pre-existing claims; the issues above are the substantive omissions/errors found. No source, resolver, test, gate, or git command was executed. Therefore the historical incident, exact local-profile export, and claimed live probes were not independently reproduced; retain them as dated producer observations, not reviewer-verified runs. The linked Model-catalog comment could not be retrieved, so its r2 quotation and #450's current scope remain unverified. Graph discovery used `XYZ-forge`, generation `2026-09-01T15:54:30Z`; no index exists for this worktree, and coverage reported changed/untracked evidence paths. Findings therefore rely on direct worktree source reads and bounded literal searches, not an exhaustive graph claim.
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:22:3. **Legacy Backwards Compatibility**: Does `cmd_check` handle legacy `merge-rebuild` receipts where `target_gid IS NULL` correctly by tolerating breaks up to that receipt point while catching subsequent breaks?
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:34:3. **F — Legacy backwards compatibility.** Legacy NULL receipts are not scoped to their receipt point. `has_merge_rebuild = any(...)` grants history-wide tolerance, including breaks after the legacy receipt (`utils/py/releases_app.py:4146-4151`), contrary to the requested "up to that receipt point" behavior.
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:80:4. **F — Malformed non-NULL scope rejection is not canonical or fully pinned.** `_parse_reanchor_breaks` still accepts raw integers/digit strings, `breaks:N`, `breaks=N`, case variants, and any larger string containing one of those tokens because it uses special cases plus `re.search` (`utils/py/releases_app.py:4046-4053`). Those values are non-NULL and are not the canonical `reanchor:N` written by `_rebuild`, yet they silently authorize break tolerance despite the diagnostic promising that only `reanchor:N` or NULL is valid (`utils/py/releases_app.py:4160-4166`). Restrict parsing to a full exact match for `reanchor:<nonnegative integer>` (plus actual SQL NULL for legacy receipts). The test only mutates the scope to the plainly unparsable `reanchor:bogus` (`test/gh360-scoped-receipt-chain-rebuild.sh:260-280`), so add a regression proving that a currently accepted non-canonical value such as `breaks:999` or `prefix reanchor:999 suffix` fails with `rule=malformed-reanchor-receipt`, then update the registered assertion count (`validate.sh:348`).
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:110:1. **Canonical Dump Regeneration in Test Fixtures**:
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:111:   - Replaced indiscriminate sed string replacements with `set_rebuild_target_gid()`, which mutates `target_gid` on `merge-rebuild` receipts in `releases.db` and immediately regenerates `releases.sql` via `releases_app.dump_text(conn, gen)`.
./relay-system/2026-08-31/gh360-scoped-receipt-chain-rebuild-qa.md:129:4. **P — Test coverage and invariants.** The suite covers clean state, un-reanchored break and wording, first rebuild, post-rebuild break, second rebuild, canonical/malformed scopes, legacy NULL compatibility, and a post-legacy break. `set_rebuild_target_gid` updates only merge-rebuild receipts and immediately writes `dump_text(...)`, eliminating the prior blanket-NULL substitution and stale-dump carryover (`test/gh360-scoped-receipt-chain-rebuild.sh:43-65`, `test/gh360-scoped-receipt-chain-rebuild.sh:268-355`). Each relevant fixture asserts absence of `rule=dump-divergence`, and the gate registration matches the stated 27 assertions (`validate.sh:348-350`).
./relay-system/2026-08-29/gh280-phase5-vendored-default/marathon-result.json:31:    "receipt_path": "/private/tmp/p5-vendored.AoymO5/consumer/.xyz/receipts/0869fdf1723a0b6f048008c2e6d6fff68cc53e5c.json"
./relay-system/2026-09-02/gh396-plan-review-deepseek.md:26:   `utils/py/wave_reconcile.py:25-70`, `utils/py/rtl.py:275-320`, `utils/py/device_config.py`,
./relay-system/2026-09-02/gh396-plan-review-deepseek.md:51:4. **Precedence conflict.** `find-harness.sh` is env-override-**first**. `wave_reconcile.harness_tool`
./relay-system/2026-09-02/gh396-plan-review-deepseek.md:52:   (`utils/py/wave_reconcile.py:31-68`, the PR #359 pattern the plan extracts) is repo-**first**,
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:25:- `githooks/dashboard-staleness-guard.sh` — the guard. The block in question is at lines 147-158.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:26:- `test/gh243-dashboard-staleness-guard.sh` — its suite; tests 7 and 8 are the matched pair from GH-315.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:40:`dashboard-staleness-guard.sh` refuses a push whose commit range writes `releases.sql`/`releases.db`
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:41:without also modifying `ROADMAP-DASHBOARD.md`. GH-243 built that for one cause: a parked roadmap row
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:47:literal INSERT prefixes — `jog_queue`, `op_receipts`, and the `settings` generation counter — with
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:51:branch. The marathon write's dump fan-out is `marathons` + `issue_refs` + `op_receipts` + the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:52:generation counter. The last two are allowlisted; the first two are not, so the range hits the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:68:Plus a new test 7b in `test/gh243-dashboard-staleness-guard.sh`, mirroring test 7 exactly but with a
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:84:   prose in issue titles, e.g. "GH-202 · wave_reconcile aborts on marathon-plan exit 5".
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:88:- Is there any path by which a `marathons` or `issue_refs` row reaches `ROADMAP-DASHBOARD.md`?
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:92:- Does anything else the guard protects — not just `ROADMAP-DASHBOARD.md` — consume these tables?
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:169:- **Auditor (Tier 3):** bounded-scope full verification with a current graph generation, complete relevant pagination, both call directions and broader relationships when material, plus explicit unresolved limitations.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:174:- Before delegating, query the graph and coverage in the parent. Pass the tier, exact project, generation/freshness, bounded scope, queries and pagination state, qualified symbols, paths, call-chain findings, coverage ranges/reasons, source fallback already performed, and unresolved questions to the child.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:221:/bin/zsh -lc "nl -ba githooks/dashboard-staleness-guard.sh | sed -n '1,230p'
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:222:nl -ba test/gh243-dashboard-staleness-guard.sh | sed -n '1,360p'
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:225:rg -n \"marathons|issue_refs|roadmap_items|roadmap list|ROADMAP-DASHBOARD\" utils/py/releases_app.py utils/roadmap-dashboard.sh githooks/dashboard-staleness-guard.sh test/gh243-dashboard-staleness-guard.sh" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-24846-s8q1x7m2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:228:     2	# dashboard-staleness-guard.sh — refuse a push whose range writes the roadmap ledger but not the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:231:     5	# WHY: since the ROADMAP_SOURCE=releases flip, ROADMAP-DASHBOARD.md is the ONLY human-readable
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:233:     7	# view. A ledger write (releases.sql / releases.db) that ships without a dashboard regeneration
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:246:    20	# Usage: dashboard-staleness-guard.sh <repo_root> <local_sha> <remote_sha> [<local_sha> <remote_sha>...]
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:251:    25	[ -n "$REPO" ] && [ -d "$REPO" ] || { echo "dashboard-staleness-guard: usage: <repo_root> <local_sha> <remote_sha>..." >&2; exit 2; }
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:276:    50	    echo "dashboard-staleness-guard: refusing cleanup — guard root is a symlink" >&2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:281:    55	    echo "dashboard-staleness-guard: failed to resolve guard root physical path" >&2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:285:    59	    echo "dashboard-staleness-guard: refusing cleanup — guard root path drifted ($cur_phys != $GUARD_ROOT_PHYS)" >&2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:294:    68	    echo "dashboard-staleness-guard: refusing cleanup — guard root identity mismatch ($cur_dev:$cur_inode != $GUARD_DEV:$GUARD_INODE)" >&2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:299:    73	    *) echo "dashboard-staleness-guard: refusing cleanup of non-descendant $cur_phys" >&2; exit 1 ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:306:    80	[ -n "$GUARD_ROOT" ] || { echo "dashboard-staleness-guard: mktemp failed" >&2; exit 1; }
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:309:    83	[ -n "$GUARD_ROOT_PHYS" ] && [ -d "$GUARD_ROOT_PHYS" ] || { echo "dashboard-staleness-guard: failed to resolve guard root" >&2; exit 1; }
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:312:    86	  *) echo "dashboard-staleness-guard: guard root $GUARD_ROOT_PHYS is not a resolved descendant of $SYS_TMP" >&2; exit 1 ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:319:    93	  echo "dashboard-staleness-guard: failed to establish guard root device/inode identity" >&2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:335:   109	      ROADMAP-DASHBOARD.md)     touched_dashboard=1 ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:340:   114	    # GH-257 Task 4: check whether regenerating ROADMAP-DASHBOARD.md produces drift or no diff.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:358:   132	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:359:   133	(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, so the human-readable
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:363:   137	    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit -m "docs: regenerate roadmap dashboard"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:370:   144	      # jog_queue + its op_receipts audit rows + the settings generation counter — none of
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:377:   151	          '-'INSERT\ INTO\ op_receipts*|'+'INSERT\ INTO\ op_receipts*) ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:378:   152	          *INSERT\ INTO\ settings*generation*) ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:386:   160	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:387:   161	(releases.sql / releases.db) without modifying ROADMAP-DASHBOARD.md, but regenerating the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:396:   170	    bash utils/roadmap-dashboard.sh && git add releases.db releases.sql ROADMAP-DASHBOARD.md && git commit -m "docs: fix roadmap row and regenerate dashboard"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:407:     2	# test/gh243-dashboard-staleness-guard.sh — the GH-243 push guard: a roadmap-ledger write without a
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:408:     3	# dashboard regeneration is refused, releases-mode only, and only when a real range exists.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:413:     8	GUARD="$root/githooks/dashboard-staleness-guard.sh"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:423:    18	echo "dash v1" > ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:424:    19	git add .pdda-mode releases.sql ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:437:    32	grep -q "roadmap-dashboard.sh" <<<"$out" || fail "refusal missing the regeneration instruction"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:441:    36	echo "dash v2" > ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:442:    37	git add ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:483:    78	  echo "INSERT INTO settings(key, value) VALUES('generation', '9');"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:485:    80	  echo "INSERT INTO op_receipts(op, target_gid) VALUES('jog-add', 'seed');"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:517:    12	OUTPUT_FILE="${ROADMAP_DASHBOARD_OUTPUT:-"$ROOT/ROADMAP-DASHBOARD.md"}"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:523:    18	  Default: render ROADMAP-DASHBOARD.md from the canonical root ROADMAP.md.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:524:    19	  --check: exit 0 when ROADMAP-DASHBOARD.md is in sync; non-zero on drift.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:548:    43	RENDERED="$TMP_DIR/ROADMAP-DASHBOARD.md"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1175:  3540	        print(summary + " (txn %s, generation %d)" % (txn[:12], get_generation(conn)))
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1226:githooks/dashboard-staleness-guard.sh:5:# WHY: since the ROADMAP_SOURCE=releases flip, ROADMAP-DASHBOARD.md is the ONLY human-readable
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1227:githooks/dashboard-staleness-guard.sh:109:      ROADMAP-DASHBOARD.md)     touched_dashboard=1 ;;
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1228:githooks/dashboard-staleness-guard.sh:114:    # GH-257 Task 4: check whether regenerating ROADMAP-DASHBOARD.md produces drift or no diff.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1229:githooks/dashboard-staleness-guard.sh:133:(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, so the human-readable
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1230:githooks/dashboard-staleness-guard.sh:137:    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit -m "docs: regenerate roadmap dashboard"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1231:githooks/dashboard-staleness-guard.sh:161:(releases.sql / releases.db) without modifying ROADMAP-DASHBOARD.md, but regenerating the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1232:githooks/dashboard-staleness-guard.sh:170:    bash utils/roadmap-dashboard.sh && git add releases.db releases.sql ROADMAP-DASHBOARD.md && git commit -m "docs: fix roadmap row and regenerate dashboard"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1233:test/gh243-dashboard-staleness-guard.sh:18:echo "dash v1" > ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1234:test/gh243-dashboard-staleness-guard.sh:19:git add .pdda-mode releases.sql ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1235:test/gh243-dashboard-staleness-guard.sh:36:echo "dash v2" > ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1236:test/gh243-dashboard-staleness-guard.sh:37:git add ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1237:test/gh243-dashboard-staleness-guard.sh:89:# 8. Control: a roadmap_items data change in the same no-drift shape still refuses.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1238:test/gh243-dashboard-staleness-guard.sh:91:{ echo "-- dump v4"; echo "INSERT INTO roadmap_items VALUES('r1');"; } > releases.sql
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1239:utils/roadmap-dashboard.sh:12:OUTPUT_FILE="${ROADMAP_DASHBOARD_OUTPUT:-"$ROOT/ROADMAP-DASHBOARD.md"}"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1240:utils/roadmap-dashboard.sh:18:  Default: render ROADMAP-DASHBOARD.md from the canonical root ROADMAP.md.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1241:utils/roadmap-dashboard.sh:19:  --check: exit 0 when ROADMAP-DASHBOARD.md is in sync; non-zero on drift.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1242:utils/roadmap-dashboard.sh:43:RENDERED="$TMP_DIR/ROADMAP-DASHBOARD.md"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1384:rg -n \"dashboard-staleness-guard|gh243-dashboard\" githooks/pre-push validate.sh ci-local.sh test utils .github 2>/dev/null" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-24846-s8q1x7m2
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1613:githooks/pre-push:87:if [ -x "$REPO/githooks/dashboard-staleness-guard.sh" ] && [ "${#_real_ref_pairs[@]}" -gt 0 ]; then
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1614:githooks/pre-push:93:  bash "$REPO/githooks/dashboard-staleness-guard.sh" "$REPO" "${_guard_args[@]}" || exit 1
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1615:validate.sh:519:  "gh243-dashboard-staleness-guard.sh" # GH-243 (push guard: ledger write without dashboard regen is refused)
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1616:test/gh257-roadmap-ledger-fixes.sh:13:GUARD="$root/githooks/dashboard-staleness-guard.sh"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1617:test/gh243-dashboard-staleness-guard.sh:2:# test/gh243-dashboard-staleness-guard.sh — the GH-243 push guard: a roadmap-ledger write without a
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1618:test/gh243-dashboard-staleness-guard.sh:8:GUARD="$root/githooks/dashboard-staleness-guard.sh"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1680:     6	# 4. staleness guard diagnostic guidance when regeneration yields no diff
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1687:    13	GUARD="$root/githooks/dashboard-staleness-guard.sh"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1809:   135	[ "$receipt_count_before" -eq "$receipt_count_after" ] || fail "idempotent update must not write extra receipts"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1810:   136	pass "idempotent update wrote zero additional receipts"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1890:   216	git add .pdda-mode releases.db releases.sql ROADMAP-DASHBOARD.md utils/ PROJECT/
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1899:   225	python3 -c "import sys; sys.path.insert(0, '$root/utils/py'); import releases_app as rel; root = rel.resolve_root('$R'); conn = rel.connect(rel.artifact_paths(root)['db']); gen = rel.get_generation(conn); open(rel.artifact_paths(root)['dump'], 'w').write(rel.dump_text(conn, gen)); conn.close()"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1916:   242	echo "dirty working tree modification" >> "$R/ROADMAP-DASHBOARD.md"
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1934:   260	git -C "$R" checkout ROADMAP-DASHBOARD.md
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1948:    83	# GH-243: deterministic dashboard-staleness guard — a roadmap-ledger write (releases.sql/.db)
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1949:    84	# without a ROADMAP-DASHBOARD.md regeneration is refused before any suite spends a second.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1952:    87	if [ -x "$REPO/githooks/dashboard-staleness-guard.sh" ] && [ "${#_real_ref_pairs[@]}" -gt 0 ]; then
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.codex.md:1958:    93	  bash "$REPO/githooks/dashboard-staleness-guard.sh" "$REPO" "${_guard_args[@]}" || exit 1
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:38:| **#44** | `feat(GH-42)`: add Commandcode relay turn-taker | development | 11 | +371/−2 | Touches `validate.sh`, `ROADMAP.md`, `ROADMAP-DASHBOARD.md`, `CHANGELOG.md`, **`relay-pkg.tar.gz`**, new `relay-automation/commandcode-turn.sh` + `utils/py/commandcode-turn.py` + `test/commandcode-turn.sh`. |
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:513:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:528:- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:559:12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:730:8. before moving to `PROJECT/3-COMPLETED`, a `## Lessons Learned (For Future Agents)` section appended to capture quirks and gotchas
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:1299:     7	.claude/settings.local.json
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:1398:ROADMAP-DASHBOARD.md
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:1730:M	ROADMAP-DASHBOARD.md
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:2260:/bin/zsh -lc 'for r in origin/feat/gh42-commandcode-turn origin/feat/gh39-releases-project-sync origin/fix/gh-23-kernel-overlap-enforcement; do echo "--- $r docs"; git diff --unified=3 origin/development..."$r" -- ROADMAP.md CHANGELOG.md ROADMAP-DASHBOARD.md | sed -n '"'1,260p'; done
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:2296:diff --git a/ROADMAP-DASHBOARD.md b/ROADMAP-DASHBOARD.md
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:2298:--- a/ROADMAP-DASHBOARD.md
./relay-system/2026-08-18/merge-order-230056/merge-order.codex.md:2299:+++ b/ROADMAP-DASHBOARD.md
./relay-system/2026-09-05/gh453-stage2-plan-qa.md:65:  README describes spec generation as a current capability gap, not a permanent prohibition, and the
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:48:  2. **Phase 0 transition realism**: is lenient-mode (warn-and-write on legacy debt, refuse new structural corruption) drawn at the right line? Is the 2-week dogfood exit gate meaningful or theater? Does side-by-side generation (RELEASES.generated.md, no overwrite) actually protect the current consumers?
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:49:  3. **Consumer-compatibility claim**: the PRD claims pdda.sh releases, ballast-release.sh Half A, and /releases keep working with zero changes because the generator emits the existing block format. Verify against the actual parser (pdda-lib.sh's field parser) — is byte-stable regeneration of the CURRENT file's blocks actually achievable given multi-paragraph Description continuations (Sundown block), or does the round-trip claim need qualification?
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:97:  settings schema, a one-shot import path that records each grandfathered violation and its disposition,
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:121:  generation, and atomic replacements; use optimistic preimage checks; reject leftover WAL/journal or
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:149:  claim in the doc is now split schema-enforced vs CLI-enforced, with bypass DETECTION (op_receipts
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:154:- **[Blocker] Phase 0 contradictions** — **Implemented.** `settings` table added (per-repo
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:158:  `op_receipts` append-only log added; exit gate rewritten: sole-writer proof via receipts + an
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:208:  set an item to `cut` without any reason event; and `op_receipts(op,target_gid,at)` contains no parent or
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:215:- **[Blocker] Byte-stable regeneration and zero-change consumer compatibility remain impossible as
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:233:  validate the git common-dir for the lock; make readers lock/retry against a committed generation marker;
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:259:Schema (issue_refs, triggers, doc_lines, op_receipts digest chain, GID shape note), Git story
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:268:  RAISE(ABORT) triggers on manifest_state_events AND op_receipts; from/to state enums CHECKed;
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:270:  op_receipts gained txn_id + before/after canonical-dump digests so `check` proves receipt-less
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:279:  the existing GH-448 resolver idiom (linked-worktree safe); reader consistency via a generation
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:320:  written.** `op_receipts` stores the SHA-256 of the canonical dump, while the canonical dump explicitly
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:321:  contains `op_receipts`; therefore the after-digest would have to hash a serialization containing that
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:323:  receipts prove two distinct sessions and a refused/retried contention case, but receipts contain no
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:326:  *business-state* digest that excludes receipts, generation markers, and digest fields; require the
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:327:  latest receipt's after-digest to equal that state and its before-digest to equal the previous receipt's
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:336:  operation (`PROJECT/1-INBOX/GH-32-RELEASES-APP-SQLITE.md:46-53,238-252`). The generation bump is also
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:338:  that generation (`PROJECT/1-INBOX/GH-32-RELEASES-APP-SQLITE.md:241-247`). **Concrete fix:** make a
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:339:  durable intent/recovery record exist before the authoritative DB commit and include the next generation;
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:347:  leaving the DB, dump, receipts, and side-by-side output stale; the two-week dogfood can no longer
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:350:  to the CLI at the Phase-0 entry while keeping generation side-by-side, forbid legacy Markdown writes
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:387:  digests (canonical dump EXCLUDING op_receipts, lock_audit, generation, digest fields), chain rule
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:392:  written BEFORE the authoritative COMMIT and carries txn_id + next generation; the generation is
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:393:  stamped into settings within the transaction; recovery is specified per boundary — pre-COMMIT:
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:428:  canonical dump, so generations can still match while DB and dump differ
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:432:  atomic sidecar that is outside the DB/dump/generation contract; add a negative control proving a
./relay-system/2026-08-18/gh32-releases-app-prd-review.md:483:  in the git common-dir, outside the dump/digest/generation contract; negative control added
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.agy.md:8:You are correct that `marathons` and `issue_refs` do not reach `ROADMAP-DASHBOARD.md`. Tracing `cmd_roadmap_list` (`utils/py/releases_app.py:3545-3581`) shows it performs a flat `SELECT * FROM roadmap_items` with no joins or subqueries. Furthermore, `issue_url` is a plain `TEXT` column (`releases_app.py:605`), not a foreign key, making `issue_refs` completely separable from `marathons`. Finally, the guard protects nothing else but `ROADMAP-DASHBOARD.md` (`dashboard-staleness-guard.sh:108-109`). 
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.agy.md:13:A guard that cries wolf on every non-roadmap DB write isn't failing closed; it's broken. The catch-all branch at `dashboard-staleness-guard.sh:162` is specifically meant to catch malformed `roadmap_items` rows that the renderer dropped. By triggering on *any* unclassified DB change, it misdiagnoses completely unrelated operations. Inverting the check to trigger *only* when `roadmap_items` changes accurately targets the only table the renderer consumes.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.agy.md:16:Replace lines 147-158 in `dashboard-staleness-guard.sh` with a single check for `roadmap_items`. This is the option I would ship because it structurally matches the renderer's sole input, requires no external dependencies (unlike asking the app), and eliminates endless allowlist maintenance:
./relay-system/2026-08-18/merge-order-v2-230654/merge-order-v2.codex.md:246:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-08-18/merge-order-v2-230654/merge-order-v2.codex.md:481:- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-08-18/merge-order-v2-230654/merge-order-v2.codex.md:512:12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-08-18/merge-order-v2-230654/merge-order-v2.codex.md:910:M	ROADMAP-DASHBOARD.md
./relay-system/2026-08-18/105406-agent2agent-gh-32-releases-app-phase-0-1-build-glm-5-3-builder-repor.md:48:  verified as the read-only contract on the real file; the generation marker in the generated copy
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:20:- Artifacts: utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:22:- Auto-included covering tests/helpers: test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:38:- Edit ONLY: `utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh` (plus the relay file). Any other edit is reverted and FAILS the turn.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:39:- Do NOT run ANY test or gate yourself — not `bash validate.sh`, and NOT `test/gh32-releases-app.sh,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/_setup.sh,test/lib/fixture-guard.sh` either. Those tests create temporary git fixtures/files inside your isolated worktree, which containment treats as off-lane edits and can discard your whole turn. Read them as specs instead; the harness runs the real gate after your turn, outside the worktree.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:49:  --artifact utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh \
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:68:1. Implement the brief by creating/editing the artifact file(s): utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:71:   - /Users/noelsaw/Documents/GH Repos/XYZ-forge-gh222/bin/tick claim MARATHON-GH-222-RELEASES-TRACKING-REPOINT-TURN --agent agy --paths "marathon-system/gh-222-releases-tracking-repoint/RELAY.md,utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh"
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:74:4. Edit ONLY these paths: marathon-system/gh-222-releases-tracking-repoint/RELAY.md and utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh. Do NOT run git. Do NOT touch any other file — the harness commits for you.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:84:You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:106:2. Modified `utils/py/releases_app.py` in `cmd_update` to remove the `refuse` for `--tracking-issue`. It now calls `issue_ref_for_token` and updates `tracking_ref_id` in the `releases` table. The change runs within `mutate()` which automatically gets verified and signed into `op_receipts` by `perform_write()`.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:117:1. Make the regression prove the complete mutable-tracker contract, rather than only the joined DB value. In section K, create the generated view before the repoint and assert that the post-update view contains the replacement tracker; run `releases check` and assert it is clean; and assert an `op_receipts` row with `op='update'` and this release GID exists. The current `COUNT(DISTINCT op) >= 2` can pass without proving that the repoint generated a receipt.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:125:1. Updated section K of `test/gh32-releases-app.sh` to prove the complete mutable-tracker contract. The test now asserts that `rout gen` creates a view with the replacement tracker, `releases check` remains clean, and an `op_receipts` row is explicitly created for the update operation on the given release GID.
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:139:`COUNT(*) FROM op_receipts WHERE op='update' AND target_gid='$K1' >= 1` can be satisfied even if
./relay-system/2026-08-29/gh222-executor-dogfood/marathon-gh-222-releases-tracking-repoint-040924.md:149:I fixed the remaining regression gap in `test/gh32-releases-app.sh`. Section K now captures the receipt count before the repoint by assigning `PRE_UPD="$(sql "SELECT COUNT(*) FROM op_receipts WHERE op='update' AND target_gid='$K1'")"` immediately before the `--tracking-issue` command, and then verifies that the count increases by exactly one (`"$N_UPD" -eq "$((PRE_UPD + 1))"`). This proves that the acceptance criterion's receipt is for the repoint itself.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:9:- `githooks/dashboard-staleness-guard.sh` — the guard. The block in question is at lines 147-158.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:10:- `test/gh243-dashboard-staleness-guard.sh` — its suite; tests 7 and 8 are the matched pair from GH-315.
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:24:`dashboard-staleness-guard.sh` refuses a push whose commit range writes `releases.sql`/`releases.db`
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:25:without also modifying `ROADMAP-DASHBOARD.md`. GH-243 built that for one cause: a parked roadmap row
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:31:literal INSERT prefixes — `jog_queue`, `op_receipts`, and the `settings` generation counter — with
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:35:branch. The marathon write's dump fan-out is `marathons` + `issue_refs` + `op_receipts` + the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:36:generation counter. The last two are allowlisted; the first two are not, so the range hits the
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:52:Plus a new test 7b in `test/gh243-dashboard-staleness-guard.sh`, mirroring test 7 exactly but with a
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:68:   prose in issue titles, e.g. "GH-202 · wave_reconcile aborts on marathon-plan exit 5".
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:72:- Is there any path by which a `marathons` or `issue_refs` row reaches `ROADMAP-DASHBOARD.md`?
./relay-system/2026-09-06/gh243-marathon-allowlist-173919/gh243-marathon-allowlist.PROMPT.txt:76:- Does anything else the guard protects — not just `ROADMAP-DASHBOARD.md` — consume these tables?
./relay-system/2026-09-05/gh453-stage2-final-qa.md:22:- Scope: ten documentation/config-comment files, audit/intake, ledger views, changelog and receipts;
./relay-system/2026-09-05/gh453-stage2-final-qa.md:33:**Verify:** Read stage2 evidence and report receipts for exact commands, statuses and limitations.
./relay-system/2026-09-05/gh453-stage2-final-qa.md:38:No source changes are planned after this review, only completed test receipts/status.
./relay-system/2026-09-05/gh453-stage2-final-qa.md:52:Basis: Reviewed the final-QA relay instructions, Stage 2 plan, Stage 2 execution receipts, the four
./relay-system/2026-09-05/gh453-stage2-final-qa.md:70:  record its exit/status in the Stage 2 execution receipts, and only then request final PASS.
./relay-system/2026-09-05/gh453-stage2-final-qa.md:82:  record, narrows containment guarantees, and keeps spec/PRD generation as a current capability gap
./relay-system/2026-09-05/gh453-stage2-final-qa.md:133:(`TESTS-RESULTS/2026-09-05+GH-453/provenance.jsonl:8`). The identity receipts match exactly:
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:212:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:217:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:218:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:291:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:336: | GH-215 — wave_reconcile.py and roadmap-dashboard.sh hardcode pre-vendoring path depth | — | [#215](https://github.com/HiQS-Labs/XYZ-forge/issues/215) · [PROJECT/1-INBOX/GH-215-RECONCILER-VENDOR-PATHS.md](PROJECT/1-INBOX/GH-215-RECONCILER-VENDOR-PATHS.md) |
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:348:--- /Users/noelsaw/Documents/GH Repos/XYZ-forge-gh222/ROADMAP-DASHBOARD.md	2026-08-28 20:23:40
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:363: | GH-215 — wave_reconcile.py and roadmap-dashboard.sh hardcode pre-vendoring path depth | — | [#215](https://github.com/HiQS-Labs/XYZ-forge/issues/215) · [PROJECT/1-INBOX/GH-215-RECONCILER-VENDOR-PATHS.md](PROJECT/1-INBOX/GH-215-RECONCILER-VENDOR-PATHS.md) |
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:618:  + gh168-wave-reconcile-scope.sh
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:623:  + gh232-wave-reconcile-multiphase.sh
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:624:  + gh202-wave-reconcile-issue-state.sh
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-jog-run2.log:696:  + gh243-dashboard-staleness-guard.sh
./relay-system/2026-09-05/model-catalog-plan-qa-qwen.md:122:   default; flagged→null (plan:103) is right for `unverified-generation` (see F11 for `disputed`). → F1.
./relay-system/2026-09-05/model-catalog-plan-qa-qwen.md:228:- [Nit] F11 — flagged ⇒ `verified_on: null` (plan:103) is right for `unverified-generation` but
./relay-system/2026-09-05/model-catalog-plan-qa-qwen.md:230:  date. Scope the null-rule to `unverified-generation`, or keep it and note the dispute date lives in
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/marathon-invocation.json:17:    "utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/marathon-invocation.json:38:    "test/gh168-wave-reconcile-scope.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/marathon-invocation.json:40:    "test/gh202-wave-reconcile-issue-state.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/marathon-invocation.json:41:    "test/gh232-wave-reconcile-multiphase.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/marathon-invocation.json:58:    "test/wave-reconcile.sh",
./relay-system/2026-09-05/model-catalog-coordination-qa.md:105:- [Pass] P2 — **Numeric claims exact.** Row 18 "60 rows (53 native / 7 openrouter)": catalog.json:3 `"version": "1.0.0"`; grep counts = 60 `"match"` rows, 53 `"target": "native"`, 7 `"target": "openrouter"`; XYZ `openrouter-model-aliases.yml` holds exactly 7 alias rows; exactly 2 flagged rows (`gemini 2.5 pro`, `gemini pro` → `gemini-2.5-pro`), both `unverified-generation` with `verified_on: null` ≡ umbrella:21.
./relay-system/2026-09-05/model-catalog-coordination-qa.md:162:- [Pass] P9 — **S1–S3, N1, N2 closed.** S1: PROJECT.md:103 totals now match the data exactly (31 dated / 6 pins ↔ 6 URLs / 29 null — probe above; residual breakdown defect = S4). S2: README "Known deviations carried as data" note is accurate against the data (`gpt`→`gpt-5.6-terra`; `gpt-6-astra` has its own explicit rows; gemini rows flagged `unverified-generation`). S3: README Consumer-contract item 6 ≡ PROJECT.md:142-145 ≡ umbrella item 6 ≡ COORDINATION decision 4. N1: PROJECT.md:31-32 "**shipped 2026-09-05** (issue closed completed)" ≡ #168 `closed_at 2026-09-05T04:28:22Z`, and :260-261 refreshed. N2: comment `5554093429` names the real control (`test/model-alias.sh` miss assertions — verified in-tree at :83-86) plus the Phase-1 terminal-refusal control.
./relay-system/2026-08-27/gh275-writeops-agy-qa.md:30:Medium-level durable logging of the **disk-write commands agents execute** — worktree teardowns, clone deletions, `rm -rf`, destructive git — across Claude Code and the harnesses, so "what deleted that?" has an answer with a timestamp. Not full exec auditing; a receipts trail for destructive writes.
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-retry-build3.log:2:marathon-drive:   • LEADERBOARD.html
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/packet.md:12:- Artifacts: utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/packet.md:14:- Auto-included covering tests/helpers: test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/packet.md:30:- Edit ONLY: `utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh` (plus the relay file). Any other edit is reverted and FAILS the turn.
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/packet.md:31:- Do NOT run ANY test or gate yourself — not `bash validate.sh`, and NOT `test/gh32-releases-app.sh,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/_setup.sh,test/lib/fixture-guard.sh` either. Those tests create temporary git fixtures/files inside your isolated worktree, which containment treats as off-lane edits and can discard your whole turn. Read them as specs instead; the harness runs the real gate after your turn, outside the worktree.
./relay-system/2026-08-29/gh222-executor-dogfood/exec2/packet.md:41:  --artifact utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh \
./relay-system/2026-09-05/gh452-release-tags-plan-qa.md:93:swept file: yes — artifact in full; GH-452 doc; `githooks/pre-push` (all 210 lines); `githooks/dashboard-staleness-guard.sh`; `releases.sql` (schema + all release rows); `releases_app.py` (schema, update/check/gen/project/ship, import validation 1875–1912); README.md:34; PAGES/ (grep sweep + generator); `relay-automation/xyz-vendor.sh` (stamping region); AGENTS.md rails cited below. Pre-existing defect found in the swept surface: exactly one — the `gh_release_url` column already carries legacy old-org **issue** URLs on 4 rows (S1), which the plan's false "NULL on all rows" claim papered over. (The ungated delete-only arm, pre-push:53–75, is pre-existing, commented, and by design — not a defect.)
./relay-system/2026-09-05/gh452-release-tags-plan-qa.md:106:5. **Execution order: correctly ordered and safe** [Pass] — renderer + carve-out (Phase A) precede backfill; operator go sits between dry-run manifest and the costly push (step 5); tags are cut before the dev→main merge so step 6's `--is-ancestor` can pass; steady state last. Missing duties: GH-243 dump/dashboard regeneration on the step-5 ledger write → S4; evidence record + `wave_reconcile` → S5; PAGES/ scope misstated → N3; step-6 promotion expectations → N5.
./relay-system/2026-09-05/gh452-release-tags-plan-qa.md:114:- [Should] S4 — Step 5 write-back trips the GH-243 guard: `releases update --gh-release-url` mutates releases.db and the canonical releases.sql dump; `.pdda-mode:11` declares `ROADMAP_SOURCE=releases`, so the pre-push dashboard-staleness-guard (pre-push:87–93; guard header: "A ledger write (releases.sql / releases.db) that ships without a dashboard regeneration … refused") REFUSES the next push unless ROADMAP-DASHBOARD.md regeneration rides it (renderer `utils/roadmap-dashboard.sh`, cited at releases_app.py:3263). Fix: step 5 commits the regenerated dump and regenerates the dashboard in the same push — otherwise the plan's own step 6 push fails closed mid-execution.
./relay-system/2026-09-05/gh452-release-tags-plan-qa.md:115:- [Should] S5 — Evidence + post-merge duties missing: step 3's "expect full local gate green" is a gate claim cited in a PR → its `provenance.jsonl`/evidence record must be committed in the same PR (AGENTS.md:96 "An uncommitted `provenance.jsonl` is not proof (GH-430)"; ci-local.sh is the qualifying run that writes the record, AGENTS.md:179–181). After the Phase A PR merges into development: `python3 utils/py/wave_reconcile.py --pr <N>` (AGENTS.md:52 — "nothing triggers it for you"). Fix: name both in step 3's expects / a post-merge line.
./relay-system/2026-09-05/model-catalog-plan-qa-agy.md:99:    *   *Fix:* Set `verified_on: null` for any row with the `unverified-generation` flag.
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:20:- Artifacts: utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:22:- Auto-included covering tests/helpers: test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:38:- Edit ONLY: `utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh` (plus the relay file). Any other edit is reverted and FAILS the turn.
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:39:- Do NOT run ANY test or gate yourself — not `bash validate.sh`, and NOT `test/gh32-releases-app.sh,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/_setup.sh,test/lib/fixture-guard.sh` either. Those tests create temporary git fixtures/files inside your isolated worktree, which containment treats as off-lane edits and can discard your whole turn. Read them as specs instead; the harness runs the real gate after your turn, outside the worktree.
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:49:  --artifact utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh \
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:73:1. Implement the brief by creating/editing the artifact file(s): utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:76:   - /Users/noelsaw/Documents/GH Repos/XYZ-forge-gh222/bin/tick claim MARATHON-GH-222-RELEASES-TRACKING-REPOINT-TURN-3-4 --agent agy --paths "marathon-system/gh-222-releases-tracking-repoint/RELAY.md,utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh"
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:79:4. Edit ONLY these paths: marathon-system/gh-222-releases-tracking-repoint/RELAY.md and utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh. Do NOT run git. Do NOT touch any other file — the harness commits for you.
./relay-system/2026-08-29/gh222-executor-dogfood/RELAY.md:89:You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
./relay-system/2026-08-29/gh222-executor-dogfood/exec4/marathon-invocation.json:17:    "utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec4/marathon-invocation.json:38:    "test/gh168-wave-reconcile-scope.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec4/marathon-invocation.json:40:    "test/gh202-wave-reconcile-issue-state.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec4/marathon-invocation.json:41:    "test/gh232-wave-reconcile-multiphase.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec4/marathon-invocation.json:58:    "test/wave-reconcile.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:8:--- generation: 292
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:9:+-- generation: 296
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:15: -- table: settings
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:16: INSERT INTO settings(key, value) VALUES('enforcement', 'lenient');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:17:-INSERT INTO settings(key, value) VALUES('generation', '292');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:18:+INSERT INTO settings(key, value) VALUES('generation', '296');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:19: INSERT INTO settings(key, value) VALUES('repo_slug', 'XYZ-forge');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:28: -- table: op_receipts
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:29: INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('manifest-add', 'mfi-01M0S1Y11AJ61R3EPCRWC3D38C', '2026-08-24T04:54:48Z', '3aee86638e5d4473a2abe1f8fb4b0b19', 'default', 'ac8a63c51ea4914af4101aa35818b48aed210782b74ae7a9a1d6177c6b93ba82', '5fd156215d06c3f939206f0ff19912555c3cd282b1e433c1432159161aab3825');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:30: INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('manifest-add', 'mfi-01M0RX41NEHE20D35E98NQ1V4X', '2026-08-24T03:30:42Z', '92e9b15d774544fa9a9ad655a2f5d41f', 'default', '58747aa4883fa59713ada3bb41f4f1aed2a2db70121457454729b7bd749f367d', 'f52dab03607c5e97e257e7adcc7548110ef1d2d2a480101ff9607a6c68e8c261');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:31:@@ -768,3 +768,7 @@ INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_bef
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:32: INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-completed', 'GH-222', '2026-08-29T03:44:45Z', '84df8123c3594f2f9a775741f9ac5707', 'default', '3009febf7476205e0751f0803ab4d41a6a6e9f8cb39a58076feabc726aca35ea', '336061b00871f06cde553f409b36bf52a02f723d04d8140041ccc087b7f93367');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:33: INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-add', 'jog-01M15SYSNVBYQMK99W05N0DM06', '2026-08-29T03:45:32Z', '6dda105ced9e469892d7824641406c40', 'default', '336061b00871f06cde553f409b36bf52a02f723d04d8140041ccc087b7f93367', '5c9d3f326b58b822c6f58fc23955ddca600ab165b2473b93e9450fe5252ec5c0');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:34: INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-lease', 'GH-222', '2026-08-29T03:45:38Z', 'a31532766ecb4a0c8c6929d5be340aa2', 'default', '5c9d3f326b58b822c6f58fc23955ddca600ab165b2473b93e9450fe5252ec5c0', 'cc0951029fb4d001cb7cdec0be483c4b1310fdef3b08416c1a97aa9eb8938ce3');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:35:+INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-failed', 'GH-222', '2026-08-29T04:46:30Z', 'b1aa173bdab644a9b8a96337ec38e885', 'default', 'cc0951029fb4d001cb7cdec0be483c4b1310fdef3b08416c1a97aa9eb8938ce3', 'dec344d57c34ae9559f64c2f2e176cdefcdcfced2510bb4a0f6257486aa95cc5');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:36:+INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-failed', 'GH-222', '2026-08-29T04:48:39Z', 'e675cc3b77e84647b9083b3e65ee29db', 'default', 'dec344d57c34ae9559f64c2f2e176cdefcdcfced2510bb4a0f6257486aa95cc5', 'deef16392ef5a18192c68dc84f267f7f00ca5ae0f670ead988eeb71c6b299284');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:37:+INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-lease', 'GH-222', '2026-08-29T04:48:39Z', '9ee0309ff6b74a27aadd1b0ac396e5c9', 'default', 'deef16392ef5a18192c68dc84f267f7f00ca5ae0f670ead988eeb71c6b299284', '7aa7fa8d6aee8d4d5f2246b52e5a1443fd0f8db4154ed3a77269bd69780bd7eb');
./relay-system/2026-08-29/gh222-executor-dogfood/queue-state-vs-committed.patch:38:+INSERT INTO op_receipts(op, target_gid, at, txn_id, session_id, state_digest_before, state_digest_after) VALUES('jog-parked', 'GH-222', '2026-08-29T04:48:43Z', '4066ad7ae9a64d21ab1282b287722726', 'default', '7aa7fa8d6aee8d4d5f2246b52e5a1443fd0f8db4154ed3a77269bd69780bd7eb', '76ee514a486fdd76f8e27f745946660d6d6f59a4e2b95fc79518041e86a1ccf4');
./relay-system/2026-08-29/gh222-executor-dogfood/exec3/marathon-invocation.json:17:    "utils/py/releases_app.py,test/gh32-releases-app.sh,RELEASES-DB-FAQS.md,test/gh103-timeline-exporter.sh,test/gh105-vendor-releases-addon.sh,test/gh168-wave-reconcile-scope.sh,test/gh197-vendor-tier-split.sh,test/gh202-wave-reconcile-issue-state.sh,test/gh232-wave-reconcile-multiphase.sh,test/gh238-hq-releases-mode.sh,test/gh239-hq-status-releases-mode.sh,test/gh257-roadmap-ledger-fixes.sh,test/gh267-express-skill.sh,test/gh280-jog-marathon-adapter.sh,test/gh290-ate-variation-grid.sh,test/gh32-release-target-advisory.sh,test/gh32-releases-artifacts.sh,test/gh39-releases-project-sync.sh,test/gh53-releases-merge-resolve.sh,test/gh54-merged-dump-refusals.sh,test/gh57-live-merge-resolve.sh,test/gh57-releases-fuzz.sh,test/gh69-roadmap-shadow.sh,test/gh75-dashboard.sh,test/jog-queue.sh,test/wave-reconcile.sh,test/xyz-vendor.sh,test/baselines/GH-32-negative-control.md,test/baselines/GH-52-negative-control.md,test/_setup.sh,test/lib/fixture-guard.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec3/marathon-invocation.json:38:    "test/gh168-wave-reconcile-scope.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec3/marathon-invocation.json:40:    "test/gh202-wave-reconcile-issue-state.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec3/marathon-invocation.json:41:    "test/gh232-wave-reconcile-multiphase.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/exec3/marathon-invocation.json:58:    "test/wave-reconcile.sh",
./relay-system/2026-08-29/gh222-executor-dogfood/gh222-retry-build2.log:4:marathon-drive:   • LEADERBOARD.html
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:202:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:207:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:208:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:226:[parallel] gh358-wave-reconcile-vendored-paths.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:286:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:321:[parallel] wave-reconcile.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:565:  + gh168-wave-reconcile-scope.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:570:  + gh232-wave-reconcile-multiphase.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:571:  + gh202-wave-reconcile-issue-state.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:589:  + gh358-wave-reconcile-vendored-paths.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:649:  + gh243-dashboard-staleness-guard.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:684:  + wave-reconcile.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:895:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:901:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:902:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:920:[parallel] gh358-wave-reconcile-vendored-paths.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:980:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1015:[parallel] wave-reconcile.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1258:  + gh168-wave-reconcile-scope.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1264:  + gh232-wave-reconcile-multiphase.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1265:  + gh202-wave-reconcile-issue-state.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1283:  + gh358-wave-reconcile-vendored-paths.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1343:  + gh243-dashboard-staleness-guard.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1378:  + wave-reconcile.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1611:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1617:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1618:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1636:[parallel] gh358-wave-reconcile-vendored-paths.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1696:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1730:[parallel] wave-reconcile.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1993:  + gh168-wave-reconcile-scope.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:1999:  + gh232-wave-reconcile-multiphase.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:2000:  + gh202-wave-reconcile-issue-state.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:2018:  + gh358-wave-reconcile-vendored-paths.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:2078:  + gh243-dashboard-staleness-guard.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-203338-53738.log:2112:  + wave-reconcile.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:199:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:205:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:206:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:224:[parallel] gh358-wave-reconcile-vendored-paths.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:285:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:319:[parallel] wave-reconcile.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:560:  + gh168-wave-reconcile-scope.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:566:  + gh232-wave-reconcile-multiphase.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:567:  + gh202-wave-reconcile-issue-state.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:585:  + gh358-wave-reconcile-vendored-paths.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:646:  + gh243-dashboard-staleness-guard.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:680:  + wave-reconcile.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:907:[parallel] gh168-wave-reconcile-scope.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:913:[parallel] gh232-wave-reconcile-multiphase.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:914:[parallel] gh202-wave-reconcile-issue-state.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:932:[parallel] gh358-wave-reconcile-vendored-paths.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:993:[parallel] gh243-dashboard-staleness-guard.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1027:[parallel] wave-reconcile.sh rc=0
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1298:  + gh168-wave-reconcile-scope.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1304:  + gh232-wave-reconcile-multiphase.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1305:  + gh202-wave-reconcile-issue-state.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1322:  + gh358-wave-reconcile-vendored-paths.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1383:  + gh243-dashboard-staleness-guard.sh
./relay-system/run-logs/2026-09-01/marathon-MARATHON_-200611-23406.log:1417:  + wave-reconcile.sh
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:151:- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`)
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:166:3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is the frozen legacy file — do not read it for current state or edit it.)
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:288:`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`, and
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:295:- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:296:- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:308:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:314:/bin/zsh -lc 'rg -n "GH-327|agent-chorus|chorus telemetry" ROADMAP-DASHBOARD.md PROJECT skills/agent-chorus/SKILL.md skills/agent-chorus/TELEMETRY.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-63630-ha2yhrnd
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:332:rg -n -C 2 "agent.?chorus|GH-193|GH-327" ROADMAP-DASHBOARD.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-63630-ha2yhrnd
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:952:    43	## Note on wave_reconcile (2026-08-24)
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:962:80-| GH-202 · wave_reconcile aborts on marathon-plan exit 5 (items held) and promotes capture docs for OPEN issues | ✅ | [GH-202-WAVE-RECONCILER-STATE.md](PROJECT/2-WORKING/GH-202-WAVE-RECONCILER-STATE.md) · [#202](https://github.com/HiQS-Labs/XYZ-forge/issues/202) |
./relay-system/2026-08-30/gh327-sidecar-root-120236/gh327-sidecar-root.codex.md:3508:   465	# --- GH-231 pilot findings: close semantics, liveness, invitation trigger, receipts, telemetry ---
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:47:Medium-level durable logging of the **disk-write commands agents execute** — worktree teardowns, clone deletions, `rm -rf`, destructive git — across Claude Code and the harnesses, so "what deleted that?" has an answer with a timestamp. Not full exec auditing; a receipts trail for destructive writes.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:487:- `ROADMAP-DASHBOARD.md` = the generated, human-readable view of the roadmap ledger (read this; regenerate with `utils/roadmap-dashboard.sh`)
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:501:3. Read `ROADMAP-DASHBOARD.md` (or `python3 utils/py/releases_app.py roadmap list`) to find the active effort or parked intake. -> expect links outward to the canonical `PROJECT/**` docs; the roadmap is a pointer ledger, not a plan body. (`ROADMAP.md` is the frozen legacy file — do not read it for current state or edit it.)
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:623:`releases roadmap add` (or `hq park`), read with `roadmap list` / `ROADMAP-DASHBOARD.md`, and
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:630:- If the task is about current priorities or active work, start in `ROADMAP-DASHBOARD.md` (or `releases roadmap list`), then follow the linked `PROJECT/**` doc.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:631:- If the task changes the roadmap ledger, write through the CLI (`releases roadmap add` for intake; `hq park` routes there automatically) and finish by regenerating `ROADMAP-DASHBOARD.md` (`utils/roadmap-dashboard.sh`) — the push gate refuses a ledger write with a stale dashboard (GH-243).
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:643:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:659:- **Attested** — carries its receipts: source, evidence, confidence. Never a bare verdict. A relay review names which claim is wrong and why; a build turn names the seam it touched.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:690:12. **Independent Verification (Separated Grading)** — The agent that produces a turn must not be the sole grader of its own quality. Verification must be performed by an independent deterministic check or a separate reviewing agent before the lock releases. Applies to: the relay's structural block validator (`bin/validate-relay-block` — Phase 1 of GH-21), consult-verify diversity (Phase 3), and any other post-generation quality gate.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:830:    14	#      modifications plus .claude/settings.json, which never came back.
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:1219:/bin/zsh -lc "rg -n --no-heading 'worktree (remove|prune)|rm -rf|xyz_debug_log_append|XYZ_DEBUG_LOG|DEBUG_LOG_FILE' utils/py/relay_drive.py utils/py/marathon_drive.py relay-automation/xyz-sync.sh relay-automation/*.sh test relay-automation/hooks .claude/settings.json 2>/dev/null" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-54680-c807n60b
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:1321:test/gh232-wave-reconcile-multiphase.sh:16:cleanup() { [ -n "${WORK:-}" ] && [ -d "$WORK" ] && rm -rf "$WORK"; }
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:1438:test/gh168-wave-reconcile-scope.sh:15:cleanup() { [ -n "${WORK:-}" ] && [ -d "$WORK" ] && rm -rf "$WORK"; }
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:1592:test/gh202-wave-reconcile-issue-state.sh:16:cleanup() { [ -n "${WORK:-}" ] && [ -d "$WORK" ] && rm -rf "$WORK"; }
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2460:/bin/zsh -lc "nl -ba .claude/settings.json | sed -n '1,260p' && rg -n --no-heading 'gh527-destructive|PreToolUse|hooks/' .claude relay-automation utils test README.md AGENTS.md | head -n 260 && nl -ba test/gh527-destructive-git-guard.sh | sed -n '1,175p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-54680-c807n60b
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2547:.claude/settings.json:23:    "PreToolUse": [
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2548:.claude/settings.json:29:            "command": "bash relay-automation/hooks/relay-xyz-guard.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2549:.claude/settings.json:38:            "command": "bash relay-automation/hooks/gh177-sandbox-test-guard.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2550:.claude/settings.json:47:            "command": "bash relay-automation/hooks/gh527-destructive-git-guard.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2551:.claude/settings.json:57:            "command": "bash relay-automation/hooks/xyz-vendor-reminder.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2552:.claude/settings.json:67:            "command": "bash relay-automation/hooks/skill-nudge.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2560:test/gh257-roadmap-ledger-fixes.sh:13:GUARD="$root/githooks/dashboard-staleness-guard.sh"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2567:test/gh527-destructive-git-guard.sh:148:   "grep -q 'gh527-destructive-git-guard' '$REPO/.claude/settings.json'"
./relay-system/2026-08-27/gh275-writeops-081831/gh275-writeops.codex.md:2610:test/gh243-dashboard-staleness-guard.sh:8:GUARD="$root/githooks/dashboard-staleness-guard.sh"

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '1,360p'
nl -ba githooks/dashboard-staleness-guard.sh | sed -n '1,280p'
nl -ba .github/workflows/wave-reconcile.yml | sed -n '1,260p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
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
    12	import json
    13	import os
    14	import re
    15	import shutil
    16	import sqlite3
    17	import subprocess
    18	import sys
    19	import tempfile
    20	from datetime import datetime
    21	from pathlib import Path
    22	
    23	sys.dont_write_bytecode = True
    24	from harness_paths import github_slug_from_origin, harness_home, harness_tool, is_vendored, repo_root, resolve_tool
    25	
    26	
    27	class ReconcileError(Exception):
    28	    """Custom exception class ensuring proper rollback catching."""
    29	
    30	    def __init__(self, message, code=2):
    31	        super().__init__(message)
    32	        self.code = code
    33	
    34	
    35	def log(msg):
    36	    print(f"wave-reconcile: {msg}", flush=True)
    37	
    38	
    39	def log_err(msg):
    40	    print(f"wave-reconcile: ERROR — {msg}", file=sys.stderr, flush=True)
    41	
    42	
    43	def die(msg, code=2):
    44	    log_err(msg)
    45	    raise ReconcileError(msg, code=code)
    46	
    47	
    48	class ReconcilerLock:
    49	    """Lock manager preventing concurrent reconciliation runs."""
    50	
    51	    def __init__(self, lock_path):
    52	        self.lock_path = lock_path
    53	        self.fd = None
    54	
    55	    def __enter__(self):
    56	        try:
    57	            self.fd = open(self.lock_path, "w")
    58	            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    59	            self.fd.write(f"pid={os.getpid()}\ntime={datetime.now().isoformat()}\n")
    60	            self.fd.flush()
    61	            return self
    62	        except (BlockingIOError, OSError) as e:
    63	            die(f"Could not acquire reconciler lock at {self.lock_path}: {e}", code=8)
    64	
    65	    def __exit__(self, exc_type, exc_val, exc_tb):
    66	        if self.fd:
    67	            try:
    68	                fcntl.flock(self.fd, fcntl.LOCK_UN)
    69	                self.fd.close()
    70	            except OSError:
    71	                pass
    72	
    73	
    74	class RollbackJournal:
    75	    """Snapshots pre-mutation file states and rolls back on failure."""
    76	
    77	    def __init__(self):
    78	        self.backups = {}  # original_path -> backup_temp_path
    79	        self.created_files = set()
    80	        self.deleted_files = set()
    81	
    82	    def snapshot(self, path):
    83	        p = os.path.abspath(path)
    84	        if p not in self.backups and os.path.exists(p):
    85	            tmp = tempfile.NamedTemporaryFile(delete=False)
    86	            tmp.close()
    87	            shutil.copy2(p, tmp.name)
    88	            self.backups[p] = tmp.name
    89	
    90	    def track_created(self, path):
    91	        self.created_files.add(os.path.abspath(path))
    92	
    93	    def rollback(self):
    94	        log("Rolling back all uncommitted mutations...")
    95	        for created in self.created_files:
    96	            if os.path.exists(created):
    97	                try:
    98	                    os.unlink(created)
    99	                except OSError:
   100	                    pass
   101	        for orig, backup in self.backups.items():
   102	            try:
   103	                os.makedirs(os.path.dirname(orig), exist_ok=True)
   104	                shutil.copy2(backup, orig)
   105	            except OSError as e:
   106	                log_err(f"Failed restoring {orig} from {backup}: {e}")
   107	        self.cleanup()
   108	
   109	    def changed(self):
   110	        """Whether any journaled artifact differs, ignoring empty directories."""
   111	        return any(os.path.exists(p) for p in self.created_files) or any(
   112	            not os.path.exists(p) or Path(p).read_bytes() != Path(backup).read_bytes()
   113	            for p, backup in self.backups.items()
   114	        )
   115	
   116	    def cleanup(self):
   117	        for backup in self.backups.values():
   118	            if os.path.exists(backup):
   119	                try:
   120	                    os.unlink(backup)
   121	                except OSError:
   122	                    pass
   123	        self.backups.clear()
   124	        self.created_files.clear()
   125	
   126	
   127	def resolve_repo_root():
   128	    """Find repository root containing .git."""
   129	    cur = os.path.abspath(os.getcwd())
   130	    while cur != os.path.dirname(cur):
   131	        if os.path.isdir(os.path.join(cur, ".git")) or os.path.isfile(os.path.join(cur, ".git")):
   132	            return cur
   133	        cur = os.path.dirname(cur)
   134	    return os.path.abspath(os.getcwd())
   135	
   136	
   137	def check_porcelain_cleanliness(repo_root, allow_dirty=False):
   138	    """Assert clean git working tree before mutation."""
   139	    cmd = ["git", "-C", repo_root, "status", "--porcelain"]
   140	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   141	    if r.returncode != 0:
   142	        die(f"git status failed: {r.stderr}")
   143	    dirt = r.stdout.strip()
   144	    if dirt and not allow_dirty:
   145	        die(
   146	            f"Working tree is dirty. Must be completely clean to reconcile:\n{dirt}",
   147	            code=3,
   148	        )
   149	    return dirt
   150	
   151	
   152	def verify_rollback_completeness(repo_root, baseline):
   153	    """GH-271: a rollback must restore the pre-run tree, not merely claim to.
   154	
   155	    The 2026-08-23 failure left regenerated dashboards and a stray MARATHON-PLAN-<date>.md
   156	    behind after "Rolling back all uncommitted mutations..." reported success. Compare
   157	    porcelain against the pre-run baseline (fixtures may legitimately start dirty under
   158	    --allow-dirty) and name every leftover — an incomplete rollback must be visible, never
   159	    a silent success.
   160	    """
   161	    if baseline is None:
   162	        return
   163	    cmd = ["git", "-C", repo_root, "status", "--porcelain"]
   164	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   165	    if r.returncode != 0:
   166	        log_err(f"Rollback completeness could not be verified: git status failed: {r.stderr}")
   167	        return
   168	    current = r.stdout.strip()
   169	    if current != baseline:
   170	        base_lines = set(baseline.splitlines())
   171	        log_err("Rollback INCOMPLETE — working tree differs from the pre-run state. Leftovers:")
   172	        for line in current.splitlines():
   173	            if line not in base_lines:
   174	                log_err(f"  {line}")
   175	
   176	
   177	def check_current_branch(repo_root, expected_branch="development", skip_branch_check=False):
   178	    """Verify active branch matches target branch."""
   179	    if skip_branch_check:
   180	        return
   181	    cmd = ["git", "-C", repo_root, "branch", "--show-current"]
   182	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   183	    current = r.stdout.strip()
   184	    if current != expected_branch:
   185	        die(
   186	            f"Active branch is '{current}', but post-merge reconciliation requires '{expected_branch}'.",
   187	            code=3,
   188	        )
   189	
   190	
   191	def pull_upstream(repo_root, branch="development"):
   192	    """Fast-forward pull from origin."""
   193	    cmd = ["git", "-C", repo_root, "pull", "--ff-only", "origin", branch]
   194	    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
   195	    if r.returncode != 0:
   196	        die(f"git pull --ff-only failed: {r.stderr}")
   197	
   198	
   199	def fetch_issue_state(repo_root, issue_num, offline_manifest=None):
   200	    """Linked issue state, or None when unknowable (GH-202).
   201	
   202	    None means PROMOTE as before — backward-compatible for offline manifests that
   203	    carry no issue list; only a positively-OPEN issue suppresses promotion.
   204	    Offline manifests may declare {"issues": [{"number": N, "state": "OPEN"}]}.
   205	    """
   206	    if offline_manifest:
   207	        for entry in offline_manifest.get("issues", []):
   208	            if str(entry.get("number")) == str(issue_num):
   209	                return str(entry.get("state", "")).upper()
   210	        return None  # legacy manifest without an issues key: unknown, promote as before
   211	    # LIVE reconcile: a failed gh is a failed fact-check, not an unknown state. A transient
   212	    # error (network, rate limit) must NOT silently fall back to promotion (GH-202 review,
   213	    # Agy round 1 blocker) — that would mis-promote every open issue on a bad network day.
   214	    try:
   215	        r = subprocess.run(
   216	            ["gh", "issue", "view", str(issue_num), "--json", "state"],
   217	            cwd=repo_root, capture_output=True, text=True, check=False,
   218	        )
   219	    except OSError as exc:
   220	        die(f"gh issue view #{issue_num} could not run ({exc}); refusing to guess issue state — "
   221	            f"fix gh access or pass --offline with an issues[] manifest", code=6)
   222	    if r.returncode != 0:
   223	        die(f"gh issue view #{issue_num} failed (exit {r.returncode}): {r.stderr.strip()}; "
   224	            f"refusing to guess issue state — fix gh access or pass --offline with an issues[] manifest", code=6)
   225	    try:
   226	        import json as _json
   227	        return str(_json.loads(r.stdout).get("state", "")).upper()
   228	    except ValueError:
   229	        die(f"gh issue view #{issue_num} returned unparseable output; refusing to guess issue state", code=6)
   230	
   231	
   232	def record_merge_evidence(doc_path, pr_meta, dry_run=False, journal=None):
   233	    """Open-issue docs stay in 2-WORKING; record the merged-PR evidence in place (GH-202)."""
   234	    merged_at = (pr_meta.get("mergedAt") or "")[:10]
   235	    label = landing_label(pr_meta)
   236	    verb = "landed" if pr_meta.get("artifactKind") == "commit" else "merged"
   237	    note = "\n## Merge evidence\n\n- " + label + " " + verb + " " + (merged_at or "(date unknown)") + " — linked issue still OPEN; doc stays active by design (GH-202: promotion requires the issue to be closed).\n"
   238	    with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   239	        content = f.read()
   240	    if ("\n- " + label + " " + verb + " ") in content or content.startswith("- " + label + " " + verb + " "):
   241	        return  # idempotent
   242	    print("TRANSITION " + json.dumps(["doc", "merge-evidence", label, os.path.basename(doc_path)]), flush=True)
   243	    if not dry_run:
   244	        if journal is not None:
   245	            journal.snapshot(doc_path)
   246	        with open(doc_path, "a", encoding="utf-8") as f:
   247	            f.write(note)
   248	
   249	
   250	def fetch_pr_metadata(repo_root, pr_id, offline_manifest=None, dry_run=False):
   251	    """Fetch merged PR metadata from GitHub or offline manifest."""
   252	    if offline_manifest:
   253	        for entry in offline_manifest.get("prs", []):
   254	            if str(entry.get("number")) == str(pr_id):
   255	                return entry
   256	        die(f"PR #{pr_id} not found in offline manifest", code=4)
   257	
   258	    if dry_run:
   259	        # In dry run without offline manifest, try gh if available or return stub preview
   260	        pass
   261	
   262	    cmd = [
   263	        "gh",
   264	        "pr",
   265	        "view",
   266	        str(pr_id),
   267	        "--json",
   268	        "number,title,state,mergedAt,mergeCommit,baseRefName,headRefName,body,url",
   269	    ]
   270	    r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)
   271	    if r.returncode != 0:
   272	        if dry_run:
   273	            log(f"dry-run: gh pr view unavailable ({r.stderr.strip()}); using synthetic preview metadata for PR #{pr_id}")
   274	            return {
   275	                "number": int(pr_id),
   276	                "title": f"Preview PR #{pr_id}",
   277	                "state": "MERGED",
   278	                "mergedAt": datetime.now().isoformat() + "Z",
   279	                "baseRefName": "development",
   280	                "body": f"Closes #{pr_id}",
   281	            }
   282	        die(f"gh pr view {pr_id} failed: {r.stderr}", code=4)
   283	    try:
   284	        return json.loads(r.stdout)
   285	    except json.JSONDecodeError as e:
   286	        die(f"Failed parsing gh pr view JSON for PR #{pr_id}: {e}", code=4)
   287	
   288	
   289	def fetch_commit_metadata(repo_root, commit_id, offline_manifest=None):
   290	    """Return direct-commit landing metadata in the reconciler's internal shape."""
   291	    if offline_manifest:
   292	        for entry in offline_manifest.get("commits", []):
   293	            if str(entry.get("sha", "")).startswith(str(commit_id)):
   294	                message = entry.get("message") or ""
   295	                return {
   296	                    "number": str(entry.get("sha", commit_id))[:12],
   297	                    "title": message.splitlines()[0] if message else f"commit {commit_id}",
   298	                    "state": "MERGED", "mergedAt": entry.get("committedAt"),
   299	                    "baseRefName": "development", "body": message,
   300	                    "url": entry.get("url", ""), "artifactKind": "commit",
   301	                    "sha": entry.get("sha", commit_id),
   302	                    "mergeCommit": {"oid": entry.get("sha", commit_id)},
   303	                }
   304	        die(f"Commit {commit_id} not found in offline manifest", code=4)
   305	
   306	    resolved = subprocess.run(
   307	        ["git", "-C", repo_root, "rev-parse", "--verify", f"{commit_id}^{{commit}}"],
   308	        capture_output=True, text=True, check=False,
   309	    )
   310	    if resolved.returncode != 0:
   311	        die(f"Commit {commit_id} cannot be resolved locally", code=4)
   312	    sha = resolved.stdout.strip()
   313	    reachable = subprocess.run(
   314	        ["git", "-C", repo_root, "merge-base", "--is-ancestor", sha, "development"],
   315	        capture_output=True, text=True, check=False,
   316	    )
   317	    if reachable.returncode != 0:
   318	        die(f"Commit {sha} is not reachable from local development", code=4)
   319	    shown = subprocess.run(
   320	        ["git", "-C", repo_root, "show", "-s", "--format=%cI%x00%B", sha],
   321	        capture_output=True, text=True, check=False,
   322	    )
   323	    if shown.returncode != 0 or "\0" not in shown.stdout:
   324	        die(f"Could not read commit metadata for {sha}", code=4)
   325	    committed_at, message = shown.stdout.split("\0", 1)
   326	    message = message.strip()
   327	    slug = github_slug_from_origin(repo_root)
   328	    return {
   329	        "number": sha[:12], "title": message.splitlines()[0], "state": "MERGED",
   330	        "mergedAt": committed_at, "baseRefName": "development", "body": message,
   331	        "url": f"https://github.com/{slug}/commit/{sha}" if slug else "",
   332	        "artifactKind": "commit", "sha": sha, "mergeCommit": {"oid": sha},
   333	    }
   334	
   335	
   336	def landing_label(meta):
   337	    if meta.get("artifactKind") == "commit":
   338	        return "commit " + str(meta.get("sha") or meta.get("number"))[:12]
   339	    return "PR #" + str(meta.get("number", "?"))
   340	
   341	
   342	def check_provenance_receipts(repo_root, pr_meta):
   343	    """Require a JSONL receipt attributable to this PR (GH-425).
   344	
   345	    Accept top-level pr/pr_number (positive integer or decimal string), or an
   346	    exact full commit matching GitHub's mergeCommit. Explicit PR fields must all
   347	    match; a conflicting PR cannot be rescued by a commit match. Filenames and
   348	    issue numbers are not PR identity. This checks attribution, not test success
   349	    or whether the receipt was committed; report only the identity actually read.
   350	    """
   351	    pr_num = pr_meta.get("number")
   352	    results_dir = os.path.join(repo_root, "TESTS-RESULTS")
   353	    if not os.path.isdir(results_dir):
   354	        die(f"--gate failure: TESTS-RESULTS directory missing; cannot verify provenance for PR #{pr_num}", code=6)
   355	
   356	    def pr_number(value):
   357	        if type(value) is int and value > 0:
   358	            return str(value)
   359	        if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
   360	            return value
     1	#!/usr/bin/env bash
     2	# dashboard-staleness-guard.sh — refuse a push whose range writes the roadmap ledger but not the
     3	# dashboard (GH-243, the enforcement half of GH-169 item 3).
     4	#
     5	# WHY: since the ROADMAP_SOURCE=releases flip, ROADMAP-DASHBOARD.md is the ONLY human-readable
     6	# view of the roadmap ledger — the DB is what every tool trusts, and nothing else re-renders the
     7	# view. A ledger write (releases.sql / releases.db) that ships without a dashboard regeneration
     8	# publishes a web/agent view that silently disagrees with the data under it.
     9	#
    10	# WHERE IT RUNS: called by githooks/pre-push with the same "<local_sha> <remote_sha>" ref pairs
    11	# the gate already parses — the push boundary is this repo's one wired, branch-independent
    12	# enforcement point (GH-549); a pre-commit hook would need a second stub wiring that does not
    13	# exist. Local commits stay free and ungated on purpose.
    14	#
    15	# SCOPE: applies only when the repo being pushed declares ROADMAP_SOURCE=releases in .pdda-mode.
    16	# Legacy-mode repos and branches predating the flip are untouched. A new branch (all-zero remote
    17	# sha) has no computable range; it falls through to the full gate like every other unclassifiable
    18	# push — this guard only ever ADDS a refusal, never replaces the gate.
    19	#
    20	# Usage: dashboard-staleness-guard.sh <repo_root> <local_sha> <remote_sha> [<local_sha> <remote_sha>...]
    21	# Exit:  0 ok (guard passed or not applicable) · 1 refuse the push · 2 usage.
    22	set -uo pipefail
    23	
    24	REPO="${1:-}"; shift || true
    25	[ -n "$REPO" ] && [ -d "$REPO" ] || { echo "dashboard-staleness-guard: usage: <repo_root> <local_sha> <remote_sha>..." >&2; exit 2; }
    26	
    27	grep -q "ROADMAP_SOURCE=releases" "$REPO/.pdda-mode" 2>/dev/null || exit 0
    28	
    29	SYS_TMP="$(cd -P "${TMPDIR:-/tmp}" 2>/dev/null && pwd -P)" || SYS_TMP="/tmp"
    30	GUARD_ROOT=""
    31	GUARD_ROOT_PHYS=""
    32	GUARD_INODE=""
    33	GUARD_DEV=""
    34	
    35	get_dev_inode() {
    36	  local target="$1"
    37	  # GNU coreutils spells --format as -c and uses -f for --file-system; BSD spells --format as -f.
    38	  # Probing BSD-first therefore SUCCEEDS on Linux for the wrong reason: `-f` is accepted, "%d %i"
    39	  # is read as a filename, and stdout gets a multi-line filesystem block instead of "<dev> <inode>".
    40	  # The caller's "${x%% *}" then yields an empty device and the guard reports an identity mismatch
    41	  # between two identical inodes. `-c` is not a BSD flag, so probing GNU-first fails cleanly there.
    42	  stat -c "%d %i" "$target" 2>/dev/null || stat -f "%d %i" "$target" 2>/dev/null || true
    43	}
    44	
    45	cleanup_guard() {
    46	  local exit_code=$?
    47	  [ -n "$GUARD_ROOT" ] || return "$exit_code"
    48	  [ -e "$GUARD_ROOT" ] || return "$exit_code"
    49	  if [ -L "$GUARD_ROOT" ]; then
    50	    echo "dashboard-staleness-guard: refusing cleanup — guard root is a symlink" >&2
    51	    exit 1
    52	  fi
    53	  local cur_phys
    54	  cur_phys="$(cd -P "$GUARD_ROOT" 2>/dev/null && pwd -P)" || {
    55	    echo "dashboard-staleness-guard: failed to resolve guard root physical path" >&2
    56	    exit 1
    57	  }
    58	  if [ -n "$GUARD_ROOT_PHYS" ] && [ "$cur_phys" != "$GUARD_ROOT_PHYS" ]; then
    59	    echo "dashboard-staleness-guard: refusing cleanup — guard root path drifted ($cur_phys != $GUARD_ROOT_PHYS)" >&2
    60	    exit 1
    61	  fi
    62	  local cur_dev_inode
    63	  cur_dev_inode="$(get_dev_inode "$cur_phys")"
    64	  local cur_dev="${cur_dev_inode%% *}"
    65	  local cur_inode="${cur_dev_inode##* }"
    66	  if [ -z "$GUARD_DEV" ] || [ -z "$GUARD_INODE" ] || [ -z "$cur_dev" ] || [ -z "$cur_inode" ] || \
    67	     [ "$cur_dev" != "$GUARD_DEV" ] || [ "$cur_inode" != "$GUARD_INODE" ]; then
    68	    echo "dashboard-staleness-guard: refusing cleanup — guard root identity mismatch ($cur_dev:$cur_inode != $GUARD_DEV:$GUARD_INODE)" >&2
    69	    exit 1
    70	  fi
    71	  case "$cur_phys" in
    72	    "$SYS_TMP"/*) rm -rf "$cur_phys" || exit 1 ;;
    73	    *) echo "dashboard-staleness-guard: refusing cleanup of non-descendant $cur_phys" >&2; exit 1 ;;
    74	  esac
    75	  return "$exit_code"
    76	}
    77	trap cleanup_guard EXIT INT TERM
    78	
    79	GUARD_ROOT="$(mktemp -d "$SYS_TMP/staleness-guard.XXXXXX")"
    80	[ -n "$GUARD_ROOT" ] || { echo "dashboard-staleness-guard: mktemp failed" >&2; exit 1; }
    81	
    82	GUARD_ROOT_PHYS="$(cd -P "$GUARD_ROOT" 2>/dev/null && pwd -P)" || GUARD_ROOT_PHYS=""
    83	[ -n "$GUARD_ROOT_PHYS" ] && [ -d "$GUARD_ROOT_PHYS" ] || { echo "dashboard-staleness-guard: failed to resolve guard root" >&2; exit 1; }
    84	case "$GUARD_ROOT_PHYS" in
    85	  "$SYS_TMP"/*) ;;
    86	  *) echo "dashboard-staleness-guard: guard root $GUARD_ROOT_PHYS is not a resolved descendant of $SYS_TMP" >&2; exit 1 ;;
    87	esac
    88	
    89	init_dev_inode="$(get_dev_inode "$GUARD_ROOT_PHYS")"
    90	GUARD_DEV="${init_dev_inode%% *}"
    91	GUARD_INODE="${init_dev_inode##* }"
    92	if [ -z "$GUARD_DEV" ] || [ -z "$GUARD_INODE" ]; then
    93	  echo "dashboard-staleness-guard: failed to establish guard root device/inode identity" >&2
    94	  exit 1
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
   106	  while IFS= read -r path; do
   107	    case "$path" in
   108	      releases.sql|releases.db) touched_ledger=1 ;;
   109	      ROADMAP-DASHBOARD.md)     touched_dashboard=1 ;;
   110	    esac
   111	  done < <(git -C "$REPO" diff --no-renames --name-only "$remote_sha" "$local_sha" 2>/dev/null)
   112	
   113	  if [ "$touched_ledger" -eq 1 ] && [ "$touched_dashboard" -eq 0 ]; then
   114	    # GH-257 Task 4: check whether regenerating ROADMAP-DASHBOARD.md produces drift or no diff.
   115	    # Run the diagnosis against a commit-pinned temporary projection of local_sha inside the
   116	    # private GUARD_ROOT_PHYS so uncommitted working-tree modifications do not skew the classification.
   117	    TMP_PROJ="$GUARD_ROOT_PHYS/proj-$local_sha"
   118	    mkdir -p "$TMP_PROJ"
   119	
   120	    drift_detected=1
   121	    render_err=""
   122	    if git -C "$REPO" archive "$local_sha" 2>/dev/null | tar -x -C "$TMP_PROJ" 2>/dev/null \
   123	       && [ -f "$TMP_PROJ/utils/roadmap-dashboard.sh" ]; then
   124	      # GH-474: KEEP the renderer's stderr. `--check` runs the full render before it reaches its
   125	      # mode branch (utils/roadmap-dashboard.sh — node render, then `if [[ "$MODE" == "check" ]]`),
   126	      # so the dropped-row warning it already emits is available here. Discarding it is what
   127	      # forced the no-drift arm below to infer the same fact from table names.
   128	      # `2>&1 >/dev/null` keeps stderr and drops stdout (order matters); the assignment carries
   129	      # the renderer's own exit status, so the drift verdict is unchanged.
   130	      if render_err="$(bash "$TMP_PROJ/utils/roadmap-dashboard.sh" --check 2>&1 >/dev/null)"; then
   131	        drift_detected=0
   132	      else
   133	        drift_detected=1
   134	      fi
   135	    fi
   136	
   137	    if [ "$drift_detected" -eq 1 ]; then
   138	      cat >&2 <<'EOF'
   139	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
   140	(releases.sql / releases.db) without regenerating ROADMAP-DASHBOARD.md, so the human-readable
   141	view would ship stale against the data under it (GH-243 / GH-169 item 3).
   142	
   143	Fix (one command, then commit the result into the same push):
   144	    bash utils/roadmap-dashboard.sh && git add ROADMAP-DASHBOARD.md && git commit -m "docs: regenerate roadmap dashboard"
   145	
   146	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   147	EOF
   148	    else
   149	      # No drift: the committed dashboard matches a fresh render. Exactly one hazard survives
   150	      # that — a roadmap row the renderer DROPPED. A dropped row renders to nothing, so the
   151	      # artifact still matches byte-for-byte while the ledger row is invisible in the view.
   152	      #
   153	      # GH-474: ASK the renderer instead of guessing. It already names every dropped row on
   154	      # stderr ("roadmap-dashboard: warning: dropped N unparseable row(s): <ids>", emitted from
   155	      # the droppedRows array), and $render_err above holds it. This replaces the GH-243/GH-315
   156	      # table-name allowlist, which had to infer the same fact from the dump's fan-out per write
   157	      # shape (jog, then marathon) and went short twice — 8 dump tables were still unclassified
   158	      # and still produced the FALSE refusal this arm exists to prevent.
   159	      #
   160	      # Direction of failure, deliberately: this reads the renderer's own report, so it cannot
   161	      # go short as a table list does. If the renderer is silent, the row rendered — allow.
   162	      dropped_line=""
   163	      while IFS= read -r eline; do
   164	        case "$eline" in
   165	          *"roadmap-dashboard: warning: dropped "*) dropped_line="$eline"; break ;;
   166	        esac
   167	      done <<EOF_ERR
   168	$render_err
   169	EOF_ERR
   170	      if [ -z "$dropped_line" ]; then
   171	        continue
   172	      fi
   173	      cat >&2 <<EOF
   174	dashboard-staleness-guard: REFUSING the push — this range writes the roadmap ledger
   175	(releases.sql / releases.db) without modifying ROADMAP-DASHBOARD.md, but regenerating the
   176	dashboard produces NO diff (GH-243 / GH-257).
   177	
   178	The renderer dropped a roadmap row, so it contributes nothing to the view and the artifact
   179	still matches. It reported:
   180	    $dropped_line
   181	
   182	Correct the named row with:
   183	    releases roadmap update --issue-num <N> --raw-text "- **GH-<N> · <title>** ..."
   184	then regenerate and commit:
   185	    bash utils/roadmap-dashboard.sh && git add releases.db releases.sql ROADMAP-DASHBOARD.md && git commit -m "docs: fix roadmap row and regenerate dashboard"
   186	
   187	Bypass (deliberately loud, e.g. a WIP branch): git push --no-verify
   188	EOF
   189	    fi
   190	    exit 1
   191	  fi
   192	done
   193	
   194	exit 0
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

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '336,780p'
nl -ba utils/py/wave_reconcile.py | sed -n '780,1220p'
nl -ba utils/roadmap-dashboard.sh | sed -n '1,220p'
rg -n \"LEADERBOARD.md|CREATE TABLE settings|settings\\b|generation\" utils/py/releases_app.py utils -g '*.py' -g '*.js' -g '*.sh' | head -n 240" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
   336	def landing_label(meta):
   337	    if meta.get("artifactKind") == "commit":
   338	        return "commit " + str(meta.get("sha") or meta.get("number"))[:12]
   339	    return "PR #" + str(meta.get("number", "?"))
   340	
   341	
   342	def check_provenance_receipts(repo_root, pr_meta):
   343	    """Require a JSONL receipt attributable to this PR (GH-425).
   344	
   345	    Accept top-level pr/pr_number (positive integer or decimal string), or an
   346	    exact full commit matching GitHub's mergeCommit. Explicit PR fields must all
   347	    match; a conflicting PR cannot be rescued by a commit match. Filenames and
   348	    issue numbers are not PR identity. This checks attribution, not test success
   349	    or whether the receipt was committed; report only the identity actually read.
   350	    """
   351	    pr_num = pr_meta.get("number")
   352	    results_dir = os.path.join(repo_root, "TESTS-RESULTS")
   353	    if not os.path.isdir(results_dir):
   354	        die(f"--gate failure: TESTS-RESULTS directory missing; cannot verify provenance for PR #{pr_num}", code=6)
   355	
   356	    def pr_number(value):
   357	        if type(value) is int and value > 0:
   358	            return str(value)
   359	        if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
   360	            return value
   361	        return None
   362	
   363	    expected_pr = pr_number(pr_num)
   364	    merge_commit = pr_meta.get("mergeCommit") or {}
   365	    merge_sha = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
   366	    if not isinstance(merge_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", merge_sha):
   367	        merge_sha = None
   368	    for root, dirs, files in os.walk(results_dir):
   369	        dirs.sort()
   370	        for name in sorted(files):
   371	            if name not in ("error_log.jsonl", "provenance.jsonl"):
   372	                continue
   373	            path = os.path.join(root, name)
   374	            if os.path.islink(path) or not os.path.isfile(path):
   375	                continue
   376	            try:
   377	                with open(path, encoding="utf-8") as receipt:
   378	                    for line_num, line in enumerate(receipt, 1):
   379	                        try:
   380	                            entry = json.loads(line)
   381	                        except ValueError:
   382	                            continue
   383	                        if not isinstance(entry, dict):
   384	                            continue
   385	                        pr_fields = [key for key in ("pr", "pr_number") if key in entry]
   386	                        matched = None
   387	                        if pr_fields:
   388	                            if expected_pr and all(pr_number(entry[key]) == expected_pr for key in pr_fields):
   389	                                matched = f"{pr_fields[0]}={expected_pr}"
   390	                        elif merge_sha and entry.get("commit") == merge_sha:
   391	                            matched = f"commit={merge_sha}"
   392	                        if matched:
   393	                            relpath = os.path.relpath(path, repo_root)
   394	                            log(f"  Provenance receipt matched for PR #{pr_num}: {relpath}:{line_num} ({matched})")
   395	                            return
   396	            except (OSError, UnicodeError):
   397	                continue  # An unreadable receipt cannot establish attribution.
   398	    die(f"--gate failure: No provenance.jsonl or error_log.jsonl entry matches PR #{pr_num} "
   399	        "by pr/pr_number or exact merge commit in TESTS-RESULTS/", code=6)
   400	
   401	
   402	# GH-271: closing-keyword clause + trailing title tag decide LINKAGE (what a merged PR may
   403	# complete); bare mentions are references only. The #-or-GH- prefix is mandatory in both —
   404	# "closes 5 issues" must not extract issue 5 — and keywords must sit on the same line as the
   405	# ref, so a title ending in "fixed" cannot capture a body that opens with "#123".
   406	CLOSING_KEYWORD_CLAUSE = re.compile(
   407	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   408	    r"((?:#|GH-)[0-9]{1,6}\b"
   409	    r"(?:(?:[ \t]*,[ \t]*(?:and[ \t]+)?|[ \t]+and[ \t]+)(?:#|GH-)[0-9]{1,6}\b)*)",
   410	    re.IGNORECASE,
   411	)
   412	REF_IN_CLAUSE = re.compile(r"(?:#|GH-)([0-9]{1,6})\b", re.IGNORECASE)
   413	# GH-429: GitHub also honours a closing keyword followed by the issue's full URL. Captured as
   414	# (slug, number); extract_linked_issues keeps only the target repo's own slug, because
   415	# fetch_issue_state and find_active_doc_for_issue key on the bare number and a foreign repo's
   416	# "Closes https://github.com/other/repo/issues/7" must not promote this repo's GH-7.
   417	CLOSING_KEYWORD_URL = re.compile(
   418	    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)[ \t]*:?[ \t]+"
   419	    r"https?://github\.com/([\w.\-]+/[\w.\-]+?)/issues/([0-9]{1,6})\b",
   420	    re.IGNORECASE,
   421	)
   422	# A `#N`/`GH-N` inside a URL (fragment `/#123`, path `/GH-123`, query `?#123`, `?issue=#123`,
   423	# `&#123`) is part of the link, not a reference — GH-271 QA rounds 1+3. The lookbehind is one
   424	# fixed-width character class.
   425	MENTION = re.compile(r"(?<![A-Za-z0-9_/?.=&])(?:[Gg][Hh]-|#)([0-9]{1,6})\b")
   426	TITLE_TRAILER = re.compile(
   427	    r"\([ \t]*((?:(?:#|GH-)[0-9]{1,6}\b[ \t]*(?:[,;][ \t]*)?)+)[ \t]*\)[ \t]*$",
   428	    re.IGNORECASE,
   429	)
   430	CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
   431	INLINE_CODE = re.compile(r"`[^`\n]*`")
   432	
   433	
   434	def _strip_code_blocks(text):
   435	    """GitHub ignores closing keywords inside code; so does the reconciler."""
   436	    return INLINE_CODE.sub(" ", CODE_FENCE.sub(" ", text))
   437	
   438	
   439	def extract_linked_issues(pr_meta, repo_slug=None):
   440	    """Split a PR's issue references into (closers, mentions) — GH-271.
   441	
   442	    closers: refs introduced by a GitHub closing keyword (close/closes/closed/fix/fixes/
   443	    fixed/resolve/resolves/resolved) before a #- or GH--prefixed number, comma lists
   444	    included, plus a trailing "(#N)"/"(GH-N)" title tag. These mirror GitHub's own linking
   445	    rules — extended to the repo's GH-N spelling, since PRs merge into `development` and
   446	    the reconciler parses text rather than relying on default-branch auto-close — and are
   447	    eligible for every reconciler action (promotion when the issue is closed, evidence +
   448	    stays-active when open).
   449	
   450	    mentions: bare GH-N/#N references in prose. The old extractor treated every mention as
   451	    a link (PR #185's body yielded ten "linked" issues, two of them live active lanes), so
   452	    a mention now only ever records merge evidence on an OPEN issue's active doc — never a
   453	    promotion, ROADMAP move, or doc relocation.
   454	
   455	    Both lists are deduplicated and sorted.
   456	    """
   457	    title = _strip_code_blocks(pr_meta.get("title") or "").strip()
   458	    body = _strip_code_blocks(pr_meta.get("body") or "")
   459	    closers, mentions = set(), set()
   460	
   461	    scan_text = title + "\n" + body
   462	    for m in CLOSING_KEYWORD_CLAUSE.finditer(scan_text):
   463	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(m.group(1)))
   464	    if repo_slug:
   465	        closers.update(int(n) for slug, n in CLOSING_KEYWORD_URL.findall(scan_text)
   466	                       if slug.lower() == repo_slug.lower())
   467	    trailer = TITLE_TRAILER.search(title)
   468	    if trailer:
   469	        closers.update(int(n) for n in REF_IN_CLAUSE.findall(trailer.group(1)))
   470	
   471	    mentions.update(int(n) for n in MENTION.findall(scan_text))
   472	    mentions -= closers
   473	    return sorted(closers), sorted(mentions)
   474	
   475	
   476	def find_active_doc_for_issue(repo_root, issue_num):
   477	    """Find matching active doc in PROJECT/2-WORKING/."""
   478	    working_dir = os.path.join(repo_root, "PROJECT", "2-WORKING")
   479	    if not os.path.isdir(working_dir):
   480	        return None
   481	    for fname in os.listdir(working_dir):
   482	        if not fname.endswith(".md"):
   483	            continue
   484	        # Match GH-123-*.md or 123-*.md
   485	        if re.search(rf"(?:^|[^\d])(GH-)?{issue_num}(?:[^\d]|$)", fname, re.IGNORECASE):
   486	            return os.path.join(working_dir, fname)
   487	    return None
   488	
   489	
   490	def parse_doc_frontmatter(doc_path):
   491	    """Parse key-value pairs from document YAML frontmatter."""
   492	    if not doc_path or not os.path.isfile(doc_path):
   493	        return {}
   494	    try:
   495	        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   496	            lines = f.readlines()
   497	        if not lines or lines[0].strip() != "---":
   498	            return {}
   499	        fm = {}
   500	        for line in lines[1:]:
   501	            if line.strip() == "---":
   502	                break
   503	            if ":" in line:
   504	                k, v = line.split(":", 1)
   505	                fm[k.strip().lower()] = v.strip().strip("'\"").lower()
   506	        return fm
   507	    except Exception:
   508	        return {}
   509	
   510	
   511	def validate_and_update_doc(doc_path, pr_meta, is_merged=True, dry_run=False, journal=None):
   512	    """Assert ## Lessons Learned, update frontmatter, and compute destination path."""
   513	    with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
   514	        content = f.read()
   515	
   516	    merged_at = pr_meta.get("mergedAt")
   517	    if merged_at:
   518	        try:
   519	            ship_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00")).strftime(
   520	                "%Y-%m-%d"
   521	            )
   522	        except Exception:
   523	            ship_date = datetime.now().strftime("%Y-%m-%d")
   524	    else:
   525	        ship_date = datetime.now().strftime("%Y-%m-%d")
   526	
   527	    if is_merged:
   528	        # Assert lessons learned section exists for merged docs
   529	        if not re.search(r"##\s+Lessons\s+Learned", content, re.IGNORECASE):
   530	            die(
   531	                f"Doc {os.path.basename(doc_path)} is missing mandatory '## Lessons Learned (For Future Agents)' section.",
   532	                code=5,
   533	            )
   534	
   535	        new_status = "Complete"
   536	        dest_folder = "3-COMPLETED"
   537	    else:
   538	        # Unmerged / declined / closed without merge -> route to 4-MISC
   539	        new_status = "Declined"
   540	        dest_folder = "4-MISC"
   541	
   542	    # Update frontmatter status and updated date
   543	    new_content = re.sub(
   544	        r"^status:\s*.*$", f"status: {new_status}", content, flags=re.MULTILINE | re.IGNORECASE
   545	    )
   546	    new_content = re.sub(
   547	        r"^updated:\s*.*$", f"updated: {ship_date}", new_content, flags=re.MULTILINE | re.IGNORECASE
   548	    )
   549	
   550	    dest_dir = os.path.join(os.path.dirname(os.path.dirname(doc_path)), dest_folder)
   551	    dest_path = os.path.join(dest_dir, os.path.basename(doc_path))
   552	    print("TRANSITION " + json.dumps(["doc", "move", os.path.basename(doc_path), dest_folder, ship_date]), flush=True)
   553	
   554	    if not dry_run:
   555	        if journal:
   556	            journal.snapshot(doc_path)
   557	            # GH-271: a destination that already exists (an earlier reconciliation promoted
   558	            # this doc and was committed) is an overwrite, not a creation — snapshot it too,
   559	            # or rollback's unlink leaves a tracked path deleted in porcelain.
   560	            if os.path.exists(dest_path):
   561	                journal.snapshot(dest_path)
   562	            journal.track_created(dest_path)
   563	        os.makedirs(dest_dir, exist_ok=True)
   564	        with open(dest_path, "w", encoding="utf-8") as f:
   565	            f.write(new_content)
   566	        os.unlink(doc_path)
   567	
   568	    return dest_path, ship_date
   569	
   570	def ledger_rows(repo_root, sql, params=()):
   571	    """Read the existing ledger without creating a DB or silently hiding schema errors."""
   572	    db = Path(repo_root) / "releases.db"
   573	    if not db.is_file():
   574	        return []
   575	    # Some legacy adopters carry an empty placeholder; their markdown remains authoritative.
   576	    mode = Path(repo_root, ".pdda-mode")
   577	    releases_mode = mode.is_file() and "ROADMAP_SOURCE=releases" in mode.read_text()
   578	    if db.stat().st_size == 0 and not releases_mode:
   579	        return []
   580	    try:
   581	        conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
   582	        try:
   583	            conn.row_factory = sqlite3.Row
   584	            return [dict(row) for row in conn.execute(sql, params)]
   585	        finally:
   586	            conn.close()
   587	    except sqlite3.Error as exc:
   588	        die(f"Cannot read reconciliation ledger: {exc}", code=6)
   589	
   590	
   591	def ledger_write(repo_root, args, dry_run=False, journal=None):
   592	    # Both paths emit the same stable intent; dry-run never calls a mutating CLI.
   593	    # In particular repoint --dry-run requires a destination that preview has not created.
   594	    print("TRANSITION " + json.dumps(args, ensure_ascii=False), flush=True)
   595	    if dry_run:
   596	        return
   597	    snapshot_ledger_artifacts(repo_root, journal=journal)
   598	    cmd = ["python3", harness_tool(repo_root, "utils/py/releases_app.py"), "--root", repo_root, *args]
   599	    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)
   600	    if result.returncode:
   601	        die(f"{' '.join(args[:2])} failed (exit {result.returncode}): {result.stderr}\n{result.stdout}", code=6)
   602	
   603	
   604	def manifest_members(repo_root, repo_slug):
   605	    rows = ledger_rows(repo_root, """SELECT r.global_id AS release_gid, i.url
   606	        FROM manifest_items m JOIN releases r ON r.id=m.release_id
   607	        JOIN issue_refs i ON i.id=m.issue_ref_id WHERE m.state='dialed_in'""")
   608	    if rows and not repo_slug:
   609	        die("Cannot resolve repository identity for manifest lookup", code=6)
   610	    members = []
   611	    for row in rows:
   612	        match = re.fullmatch(r"https://github.com/([^/]+/[^/]+)/issues/([1-9][0-9]*)", row["url"] or "")
   613	        if match and match[1].lower() == repo_slug.lower():
   614	            members.append(dict(row, issue=int(match[2])))
   615	    return members
   616	
   617	
   618	def ship_manifest_items(repo_root, issue_num, pr_meta, repo_slug, dry_run=False, journal=None):
   619	    for member in manifest_members(repo_root, repo_slug):
   620	        if member["issue"] != issue_num:
   621	            continue
   622	        sha = (pr_meta.get("mergeCommit") or {}).get("oid", "")
   623	        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
   624	            die(f"PR #{pr_meta.get('number')} has no full merge commit for manifest evidence", code=6)
   625	        ledger_write(repo_root, ["manifest", "ship", "--gid", member["release_gid"],
   626	                     member["url"], "--evidence", sha], dry_run, journal)
   627	
   628	
   629	def catch_up_prs(repo_root, repo_slug, offline_manifest=None):
   630	    """Derive drift from committed state; no PR watermark or auxiliary ledger.
   631	
   632	    Timeline pagination recovers closing PRs even outside an arbitrary recent-PR window.
   633	    Only merged development PRs whose closers match the closed issue qualify.
   634	    """
   635	    issues = {m["issue"] for m in manifest_members(repo_root, repo_slug)}
   636	    # Roadmap-only drift survives when a doc was archived or a manifest already shipped.
   637	    # Terminal rows must drop out again so successful catch-up remains idempotent.
   638	    for row in ledger_rows(repo_root,
   639	            "SELECT gh_number, issue_url FROM roadmap_items WHERE gh_number IS NOT NULL "
   640	            "AND section NOT IN (?, ?)", ("Completed", "Deferred · vision")):
   641	        expected = f"https://github.com/{repo_slug}/issues/{row['gh_number']}"
   642	        if repo_slug and (row["issue_url"] or "").lower() == expected.lower():
   643	            issues.add(row["gh_number"])
   644	    for path in Path(repo_root, "PROJECT/2-WORKING").glob("GH-*.md"):
   645	        match = re.match(r"GH-([0-9]+)-", path.name)
   646	        if match:
   647	            issues.add(int(match[1]))
   648	    found = set()
   649	    for issue in sorted(issues):
   650	        if fetch_issue_state(repo_root, issue, offline_manifest) != "CLOSED":
   651	            continue
   652	        if offline_manifest is not None:
   653	            candidates = offline_manifest.get("prs", [])
   654	        else:
   655	            result = subprocess.run(["gh", "api", "--paginate", "--slurp",
   656	                f"repos/{repo_slug}/issues/{issue}/timeline?per_page=100"],
   657	                cwd=repo_root, capture_output=True, text=True, check=False)
   658	            if result.returncode:
   659	                die(f"Catch-up timeline for GH-{issue} failed: {result.stderr}", code=6)
   660	            numbers = set()
   661	            for page in json.loads(result.stdout):
   662	                for event in page:
   663	                    referenced = (event.get("source") or {}).get("issue") or {}
   664	                    if referenced.get("pull_request") and referenced.get("repository_url", "").lower() == (
   665	                        f"https://api.github.com/repos/{repo_slug}".lower()):
   666	                        numbers.add(referenced["number"])
   667	            candidates = [fetch_pr_metadata(repo_root, n) for n in sorted(numbers)]
   668	        matches = [pr for pr in candidates if pr.get("state", "").upper() == "MERGED"
   669	                   and pr.get("baseRefName") == "development"
   670	                   and issue in extract_linked_issues(pr, repo_slug)[0]]
   671	        if not matches:
   672	            die(f"Closed GH-{issue} has reconciliation drift but no attributable merged development PR", code=6)
   673	        # The most recent closing PR owns the current lifecycle transition.
   674	        found.add(str(max(matches, key=lambda pr: (pr.get("mergedAt") or "", pr["number"]))["number"]))
   675	    return sorted(found, key=int)
   676	
   677	
   678	def update_roadmap_entry(repo_root, issue_num, landing, ship_date, is_merged=True, dry_run=False, journal=None, doc_path=None):
   679	    """Move entry in ROADMAP.md and/or releases.db to Completed/Deferred section with shipping badge."""
   680	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
   681	    db_path = os.path.join(repo_root, "releases.db")
   682	    target_section_md = "### Completed" if is_merged else "### Deferred / cancelled"
   683	    target_section_db = "Completed" if is_merged else "Deferred · vision"
   684	    badge_sub = f"✅ **SHIPPED {ship_date} ({landing})**" if is_merged else f"🛑 **DECLINED {ship_date} ({landing})**"
   685	
   686	    updated = False
   687	
   688	    # GH-421: read desired state first; every write uses the existing receipt-backed CLI.
   689	    if os.path.isfile(db_path):
   690	        rows = ledger_rows(repo_root, "SELECT * FROM roadmap_items WHERE gh_number = ?", (issue_num,))
   691	        if rows:
   692	            row = rows[0]
   693	            raw_text = row["raw_text"] or ""
   694	            title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", raw_text)
   695	            title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num} · {row['title']}"
   696	            rest = raw_text.split("—", 1)[1] if "—" in raw_text else " " + (
   697	                raw_text[title_match.end():].strip() if title_match else raw_text)
   698	            if doc_path and row["doc_path"]:
   699	                rest = rest.replace(row["doc_path"], doc_path)
   700	            new_raw_text = f"- **{title_part}** {badge_sub} —{rest}".strip()
   701	            marker = "✅" if is_merged else "⛔"
   702	            if doc_path and row["doc_path"] != doc_path:
   703	                ledger_write(repo_root, ["roadmap", "repoint", "--issue-num", str(issue_num),
   704	                             "--doc-path", doc_path], dry_run, journal)
   705	            if (row["section"], row["status_marker"], raw_text) != (target_section_db, marker, new_raw_text):
   706	                ledger_write(repo_root, ["roadmap", "update", "--issue-num", str(issue_num),
   707	                             "--section", target_section_db, "--status-marker", marker,
   708	                             "--raw-text", new_raw_text], dry_run, journal)
   709	            updated = True
   710	
   711	    # 2. Update ROADMAP.md if present (legacy mode)
   712	    if os.path.isfile(roadmap_path):
   713	        with open(roadmap_path, "r", encoding="utf-8", errors="replace") as f:
   714	            lines = f.readlines()
   715	
   716	        entry_pattern = re.compile(rf"^-\s+\*\*GH-{issue_num}\b")
   717	        starts = [i for i, line in enumerate(lines) if entry_pattern.search(line)]
   718	        if not starts:
   719	            log(f"No entry found in ROADMAP.md for GH-{issue_num} (skipping roadmap move)")
   720	            return updated
   721	
   722	        blocks = []
   723	        for start_idx in starts:
   724	            end_idx = len(lines)
   725	            for j in range(start_idx + 1, len(lines)):
   726	                if lines[j].startswith("- **") or lines[j].startswith("### ") or lines[j].startswith("## "):
   727	                    end_idx = j
   728	                    break
   729	            blocks.append((start_idx, end_idx, lines[start_idx:end_idx]))
   730	
   731	        expected_marker = "SHIPPED" if is_merged else "DECLINED"
   732	        canonical = next(
   733	            (block for _, _, block in blocks if expected_marker in block[0]),
   734	            blocks[0][2],
   735	        )
   736	        block_lines = list(canonical)
   737	        first_line = block_lines[0]
   738	
   739	        if len(blocks) == 1 and expected_marker in first_line:
   740	            log(f"GH-{issue_num} is already marked {expected_marker} in ROADMAP.md")
   741	            return True
   742	
   743	        title_match = re.search(r"^-\s+\*\*([^*]+)\*\*", first_line)
   744	        title_part = title_match.group(1).strip() if title_match else f"GH-{issue_num}"
   745	
   746	        if "—" in first_line:
   747	            rest = first_line.split("—", 1)[1]
   748	        else:
   749	            after_title = first_line[title_match.end():] if title_match else first_line
   750	            rest = re.sub(r"^(?:\s*✅\s*(?:\*\*.*?\*\*)?|\s*🚧\s*(?:\*\*.*?\*\*)?|\s*🛑\s*(?:\*\*.*?\*\*)?|\s*)", "", after_title)
   751	            if not rest.startswith(" ") and rest != "\n" and rest != "":
   752	                rest = " " + rest
   753	            if not rest.endswith("\n"):
   754	                rest += "\n"
   755	
   756	        new_first_line = f"- **{title_part}** {badge_sub} —{rest}"
   757	        block_lines[0] = new_first_line
   758	
   759	        removed = set()
   760	        for start_idx, end_idx, _ in blocks:
   761	            removed.update(range(start_idx, end_idx))
   762	        new_lines = [line for idx, line in enumerate(lines) if idx not in removed]
   763	
   764	        target_idx = None
   765	        for k, line in enumerate(new_lines):
   766	            if line.strip() == target_section_md:
   767	                target_idx = k
   768	                break
   769	
   770	        if target_idx is None and not is_merged:
   771	            target_section_md = "### Completed"
   772	            for k, line in enumerate(new_lines):
   773	                if line.strip() == target_section_md:
   774	                    target_idx = k
   775	                    break
   776	
   777	        if target_idx is None:
   778	            die(f"Could not find '{target_section_md}' section in ROADMAP.md", code=5)
   779	
   780	        insert_pos = target_idx + 1
   780	        insert_pos = target_idx + 1
   781	        new_lines = new_lines[:insert_pos] + block_lines + new_lines[insert_pos:]
   782	
   783	        if not dry_run:
   784	            if journal:
   785	                journal.snapshot(roadmap_path)
   786	            with open(roadmap_path, "w", encoding="utf-8") as f:
   787	                f.writelines(new_lines)
   788	
   789	        updated = True
   790	
   791	    return updated
   792	
   793	
   794	def fix_mangled_roadmap_entries(repo_root, dry_run=False, journal=None):
   795	    roadmap_path = os.path.join(repo_root, "ROADMAP.md")
   796	    if not os.path.isfile(roadmap_path):
   797	        return
   798	    with open(roadmap_path, "r", encoding="utf-8") as f:
   799	        lines = f.readlines()
   800	    changed = False
   801	    for i, line in enumerate(lines):
   802	        if line.startswith("- **") and " ** " in line:
   803	            new_line = re.sub(r"^-\s+\*\*(GH-\d+)\s+\*\*", r"- **\1**", line)
   804	            if new_line != line:
   805	                lines[i] = new_line
   806	                changed = True
   807	    if changed and not dry_run:
   808	        if journal:
   809	            journal.snapshot(roadmap_path)
   810	        with open(roadmap_path, "w", encoding="utf-8") as f:
   811	            f.writelines(lines)
   812	
   813	
   814	def marathon_plan_findings(output, returncode):
   815	    """Return exit-driving structured findings emitted by marathon-plan."""
   816	    drift_types = {"already-landed", "already-closed"}
   817	    held_types = {
   818	        "unrated", "needs-doc", "needs-contract", "note-only",
   819	        "not-ready", "blocked", "blocked-dep",
   820	    }
   821	    relevant_types = drift_types if returncode == 4 else held_types
   822	    findings = []
   823	    for line in output.splitlines():
   824	        try:
   825	            finding = json.loads(line)
   826	        except (json.JSONDecodeError, TypeError):
   827	            continue
   828	        check = str(finding.get("check", ""))
   829	        finding_type = check.split("/", 1)[1] if "/" in check else check
   830	        if finding_type in relevant_types:
   831	            findings.append(finding)
   832	    return findings
   833	
   834	
   835	def finding_issue_numbers(finding):
   836	    """Extract issue identities from a planner finding without guessing by title."""
   837	    file_name = str(finding.get("file", ""))
   838	    evidence = " ".join(str(finding.get(key, "")) for key in ("file", "message", "action"))
   839	    numbers = {
   840	        int(number)
   841	        for number in re.findall(r"(?:GH-|issue\s+#|#)([0-9]{1,6})\b", evidence, re.IGNORECASE)
   842	    }
   843	    # Active-doc lookup also supports the legacy `123-title.md` filename shape.
   844	    legacy_doc = re.match(r"^(?:GH-)?([0-9]{1,6})(?:[^0-9]|$)", os.path.basename(file_name), re.IGNORECASE)
   845	    if legacy_doc:
   846	        numbers.add(int(legacy_doc.group(1)))
   847	    return numbers
   848	
   849	
   850	def describe_finding(finding):
   851	    """Produce a stable, operator-readable held-item label."""
   852	    issue_nums = sorted(finding_issue_numbers(finding))
   853	    file_name = str(finding.get("file", "")).strip()
   854	    identity = ", ".join(f"GH-{number}" for number in issue_nums)
   855	    if identity and file_name:
   856	        return f"{identity} ({file_name})"
   857	    if identity:
   858	        return identity
   859	    if file_name:
   860	        return file_name
   861	    return str(finding.get("message", "")).strip() or "unidentified planner item"
   862	
   863	
   864	def handle_marathon_plan_result(result, reconciled_issues):
   865	    """Scope planner drift/held failures to the issues reconciled in this run."""
   866	    if result.returncode == 0:
   867	        return
   868	    if result.returncode not in (4, 5):
   869	        die(
   870	            f"Subprocess 'marathon-plan.sh' failed with exit {result.returncode}:\n"
   871	            f"{result.stderr}\n{result.stdout}",
   872	            code=6,
   873	        )
   874	
   875	    findings = marathon_plan_findings(result.stdout, result.returncode)
   876	    if not findings:
   877	        # Preserve GH-202 compatibility with older/stub planners that expose only
   878	        # the exit-5 contract. Exit 4 must remain attributable and therefore
   879	        # fails closed when structured evidence is absent.
   880	        if result.returncode == 5:
   881	            log("  marathon-plan reports items held (exit 5) without structured findings — continuing (GH-202 compatibility)")
   882	            return
   883	        die("marathon-plan reported drift (exit 4) without attributable structured findings", code=6)
   884	
   885	    reconciled = {int(issue) for issue in reconciled_issues}
   886	    owned = [
   887	        finding for finding in findings
   888	        if finding_issue_numbers(finding) & reconciled
   889	    ]
   890	    unrelated = [finding for finding in findings if finding not in owned]
   891	
   892	    if owned:
   893	        labels = ", ".join(describe_finding(finding) for finding in owned)
   894	        die(
   895	            "marathon-plan found drift/held state attributable to the reconciled "
   896	            f"PR item(s): {labels}",
   897	            code=6,
   898	        )
   899	
   900	    log("  WARNING — marathon-plan found pre-existing unrelated drift/held items; keeping reconciliation:")
   901	    for finding in unrelated:
   902	        log(f"    - {describe_finding(finding)}")
   903	
   904	
   905	def snapshot_ledger_artifacts(repo_root, dry_run=False, journal=None):
   906	    """GH-424: capture the ledger and generated views BEFORE the first write.
   907	
   908	    Repeated calls retain the original state, including originally absent artifacts.
   909	    Both per-issue writes and downstream regeneration use this same snapshot set.
   910	    """
   911	    if dry_run or journal is None:
   912	        return
   913	    for name in (
   914	        "releases.db", "releases.sql", "RELEASES.generated.md",
   915	        "ROADMAP-DASHBOARD.md", "RELEASES-PREVIEW.html",
   916	        "LEADERBOARD.html", "LEADERBOARD.md",
   917	    ):
   918	        path = os.path.abspath(os.path.join(repo_root, name))
   919	        if path in journal.backups or path in journal.created_files:
   920	            continue
   921	        if os.path.exists(path):
   922	            journal.snapshot(path)
   923	        else:
   924	            journal.track_created(path)
   925	
   926	
   927	def run_subprocesses(repo_root, dry_run=False, journal=None, reconciled_issues=None):
   928	    """Orchestrate releases sync, view exports, and marathon replanning with DB rollback protection."""
   929	    log("Running downstream database sync and dashboard regeneration...")
   930	
   931	    snapshot_ledger_artifacts(repo_root, dry_run=dry_run, journal=journal)
   932	
   933	    def _plan_docs():
   934	        found = set()
   935	        for pattern in ("MARATHON-PLAN-*.md", os.path.join("PROJECT", "2-WORKING", "MARATHON-PLAN-*.md")):
   936	            found.update(glob.glob(os.path.join(repo_root, pattern)))
   937	        return found
   938	
   939	    pre_plan_docs = _plan_docs() if not dry_run else set()
   940	    if journal and not dry_run:
   941	        # Codex consult: a same-dated plan doc that already exists gets OVERWRITTEN by the
   942	        # replan, and tracking-only-created would leave rollback no bytes to restore.
   943	        for existing_doc in pre_plan_docs:
   944	            journal.snapshot(existing_doc)
   945	
   946	    # GH-358: resolve each harness tool against the repo first, then the harness home. On a
   947	    # vendored install these five live only under <repo>/.xyz/ and every one was unreachable,
   948	    # so the reconciler died on its first downstream step.
   949	    releases_app = harness_tool(repo_root, "utils/py/releases_app.py")
   950	    sync_cmd = ["python3", releases_app, "--root", repo_root, "roadmap", "sync"]
   951	    check_cmd = ["python3", releases_app, "--root", repo_root, "check"]
   952	    timeline_cmd = ["python3", harness_tool(repo_root, "utils/timeline/export_timeline.py"), "--preview"]
   953	    dash_cmd = ["bash", harness_tool(repo_root, "utils/roadmap-dashboard.sh")]
   954	    plan_cmd = ["bash", harness_tool(repo_root, "utils/marathon-plan.sh"), "--format", "json"]
   955	
   956	    if dry_run:
   957	        sync_cmd.append("--dry-run")
   958	        plan_cmd.append("--dry-run")
   959	
   960	    steps = [
   961	        ("releases roadmap sync", sync_cmd),
   962	        ("releases check", check_cmd),
   963	    ]
   964	    if not dry_run:
   965	        # GH-474: RELEASES-PREVIEW.html is an ADOPTED view — opt-in by presence. Every other
   966	        # consumer already treats it that way: releases_app.refresh_preview() skips it when
   967	        # absent (utils/py/releases_app.py:1170-1201), the merge resolver regenerates only what
   968	        # is already there (utils/releases-merge-resolve.sh:160-172), express.py snapshots it
   969	        # under os.path.lexists (utils/py/express.py:202-207) and jog_run.py stages it the same
   970	        # way. This step was the ONE consumer that regenerated it unconditionally, so a repo
   971	        # that had deliberately un-adopted the view got it silently recreated on the next
   972	        # reconcile — the deletion would not stick.
   973	        #
   974	        # ROADMAP-DASHBOARD.md stays unconditional on purpose, and the asymmetry is the point:
   975	        # it is NOT adopted-by-presence. It is required — githooks/dashboard-staleness-guard.sh
   976	        # refuses a push without it and utils/py/router_audit.py gates ROUTER.md's declaration
   977	        # of it. Regenerating a required view is correct; resurrecting an un-adopted one is not.
   978	        if os.path.exists(os.path.join(repo_root, "RELEASES-PREVIEW.html")):
   979	            steps.append(("export_timeline.py --preview", timeline_cmd))
   980	        else:
   981	            log("  (skipping export_timeline.py --preview — RELEASES-PREVIEW.html is not adopted here)")
   982	        steps.extend(
   983	            [
   984	                ("roadmap-dashboard.sh", dash_cmd),
   985	                ("marathon-plan.sh", plan_cmd),
   986	            ]
   987	        )
   988	    else:
   989	        steps.append(("marathon-plan.sh --dry-run", plan_cmd))
   990	
   991	    # GH-271: registration of created views/plan docs must happen even when a step DIES —
   992	    # the marathon-plan failure path raises from inside the loop, and a post-loop pass
   993	    # would never run, which is exactly how the stray MARATHON-PLAN escaped rollback.
   994	    try:
   995	        for name, cmd in steps:
   996	            log(f"  -> {name}")
   997	            # GH-429: roadmap-dashboard.sh derives ROOT from its own location and lands on <repo>/.xyz
   998	            # when vendored (#215 item 2); it honours this override, and the reconciler already knows
   999	            # the repo root. Harmless for the other steps, which ignore the variable.
  1000	            step_env = dict(os.environ, ROADMAP_DASHBOARD_ROOT=str(repo_root))
  1001	            r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False, env=step_env)
  1002	            if name.startswith("marathon-plan"):
  1003	                handle_marathon_plan_result(r, reconciled_issues or set())
  1004	            elif r.returncode != 0:
  1005	                die(f"Subprocess '{name}' failed with exit {r.returncode}:\n{r.stderr}\n{r.stdout}", code=6)
  1006	    finally:
  1007	        if journal and not dry_run:
  1008	            for plan_doc in _plan_docs() - pre_plan_docs:
  1009	                journal.track_created(plan_doc)
  1010	
  1011	
  1012	def run_validation_gate(repo_root):
  1013	    """Run pdda doc-health verification gate."""
  1014	    log("Running PDDA doc-hygiene gate...")
  1015	    gate_cmd = ["bash", "utils/pdda-local-checks.sh"] if os.path.exists(os.path.join(repo_root, "utils", "pdda-local-checks.sh")) else ["bash", "utils/pdda/pdda.sh"]
  1016	    r = subprocess.run(
  1017	        gate_cmd,
  1018	        cwd=repo_root,
  1019	        capture_output=True,
  1020	        text=True,
  1021	        check=False,
  1022	    )
  1023	    # GH-429: the exit status IS the consuming repo's enforcement decision — pdda-lib.sh makes
  1024	    # `observe`/`light` exit 0 and `full` exit non-zero on errors. Grepping stdout for ERROR
  1025	    # overrode that mode and made a live reconciliation impossible on any repo with a standing
  1026	    # observe-mode backlog. Block on the status; surface the findings when it reports but passes.
  1027	    if r.returncode != 0:
  1028	        die(f"PDDA validation gate failed:\n{r.stdout}", code=7)
  1029	    if "ERROR" in r.stdout:
  1030	        found = re.search(r"(\d+) error\(s\) found", r.stdout)
  1031	        count = found.group(1) if found else "some"
  1032	        log(f"  WARNING — pdda reported {count} finding(s) but exited 0 (repo enforcement mode is not blocking); continuing")
  1033	
  1034	
  1035	def main():
  1036	    parser = argparse.ArgumentParser(
  1037	        description="wave_reconcile.py — Canonical Post-Merge Wave & Marathon Lifecycle Reconciler"
  1038	    )
  1039	    parser.add_argument(
  1040	        "--root",
  1041	        help="Target repository root path (default: current working directory)",
  1042	    )
  1043	    parser.add_argument(
  1044	        "--pr",
  1045	        nargs="+",
  1046	        help="One or more merged PR numbers/IDs to reconcile",
  1047	    )
  1048	    parser.add_argument(
  1049	        "--commit",
  1050	        nargs="+",
  1051	        help="One or more commits landed directly on development to reconcile",
  1052	    )
  1053	    parser.add_argument(
  1054	        "--marathon",
  1055	        help="Marathon identifier / milestone name",
  1056	    )
  1057	    parser.add_argument(
  1058	        "--manifest",
  1059	        help="Path to structured JSON reconciliation manifest",
  1060	    )
  1061	    parser.add_argument(
  1062	        "--dry-run",
  1063	        action="store_true",
  1064	        help="Hermetic preview: assert zero file/DB/ref mutations",
  1065	    )
  1066	    parser.add_argument(
  1067	        "--offline",
  1068	        help="Run without network using offline JSON manifest cache",
  1069	    )
  1070	    parser.add_argument(
  1071	        "--skip-pull",
  1072	        action="store_true",
  1073	        help="Skip git pull --ff-only origin development (for testing/isolated clones)",
  1074	    )
  1075	    parser.add_argument(
  1076	        "--skip-branch-check",
  1077	        action="store_true",
  1078	        help="Skip active branch check (for tests on feature branches)",
  1079	    )
  1080	    parser.add_argument(
  1081	        "--allow-dirty",
  1082	        action="store_true",
  1083	        help="Allow dirty working tree (for test fixtures only)",
  1084	    )
  1085	    parser.add_argument(
  1086	        "--force-promote",
  1087	        action="store_true",
  1088	        help="Force promotion of active docs and roadmap entries to Completed regardless of linked issue OPEN state",
  1089	    )
  1090	    parser.add_argument(
  1091	        "--gate",
  1092	        "--require-receipts",
  1093	        action="store_true",
  1094	        dest="require_receipts",
  1095	        help="Require a receipt matching each PR number or exact merge commit before closeout (GH-425)",
  1096	    )
  1097	
  1098	    parser.add_argument("--catch-up", action="store_true", help="Recover closed-issue drift from committed docs and manifest")
  1099	
  1100	    args = parser.parse_args()
  1101	
  1102	    repo_root = os.path.abspath(args.root) if args.root else resolve_repo_root()
  1103	    lock_file = os.path.join(repo_root, ".git", "wave-reconcile.lock")
  1104	    journal = RollbackJournal()
  1105	    baseline = None
  1106	
  1107	    try:
  1108	        # Preflight phase
  1109	        log(f"Starting wave reconciliation (dry_run={args.dry_run}, root={repo_root})")
  1110	        baseline = check_porcelain_cleanliness(repo_root, allow_dirty=(args.allow_dirty or args.dry_run))
  1111	        check_current_branch(repo_root, skip_branch_check=args.skip_branch_check)
  1112	
  1113	        if not args.skip_pull and not args.dry_run and not args.offline:
  1114	            pull_upstream(repo_root)
  1115	
  1116	        offline_manifest = None
  1117	        if args.offline:
  1118	            try:
  1119	                with open(args.offline, "r", encoding="utf-8") as f:
  1120	                    offline_manifest = json.load(f)
  1121	            except Exception as e:
  1122	                die(f"Failed loading offline manifest from {args.offline}: {e}", code=4)
  1123	
  1124	        landing_items = [("pr", value) for value in (args.pr or [])]
  1125	        landing_items.extend(("commit", value) for value in (args.commit or []))
  1126	        if args.manifest:
  1127	            try:
  1128	                with open(args.manifest, "r", encoding="utf-8") as f:
  1129	                    mdata = json.load(f)
  1130	                    landing_items.extend(("pr", str(p)) for p in mdata.get("prs", []))
  1131	            except Exception as e:
  1132	                die(f"Failed loading manifest from {args.manifest}: {e}", code=4)
  1133	
  1134	        if not landing_items and not args.marathon and not args.catch_up:
  1135	            die("No PRs, commits, or marathon specified. Pass --pr <N>..., --commit <SHA>..., --marathon <name>, or --catch-up", code=2)
  1136	
  1137	        with ReconcilerLock(lock_file):
  1138	            reconciled_issues = set()
  1139	            repo_slug = github_slug_from_origin(repo_root)  # GH-429: URL-form closers, this repo only
  1140	            if args.catch_up:
  1141	                landing_items.extend(("pr", str(n)) for n in catch_up_prs(repo_root, repo_slug, offline_manifest))
  1142	            landing_items = list(dict.fromkeys((kind, str(value)) for kind, value in landing_items))
  1143	            for landing_kind, landing_id in landing_items:
  1144	                if landing_kind == "commit":
  1145	                    pr_meta = fetch_commit_metadata(repo_root, landing_id, offline_manifest)
  1146	                else:
  1147	                    pr_meta = fetch_pr_metadata(repo_root, landing_id, offline_manifest, dry_run=args.dry_run)
  1148	                landing = landing_label(pr_meta)
  1149	                log(f"Processing {landing}...")
  1150	                state = pr_meta.get("state", "").upper()
  1151	                is_merged = (state == "MERGED")
  1152	
  1153	                if not is_merged:
  1154	                    log(f"  {landing} state is '{state}' (unmerged/declined) -> routing to 4-MISC/")
  1155	
  1156	                base_ref = pr_meta.get("baseRefName", "")
  1157	                if base_ref and base_ref != "development":
  1158	                    die(
  1159	                        f"{landing} target base is '{base_ref}', not 'development'.",
  1160	                        code=4,
  1161	                    )
  1162	
  1163	                linked_issues, mentioned_issues = extract_linked_issues(pr_meta, repo_slug=repo_slug)
  1164	                # GH-425: unconditional whenever --gate/--require-receipts is requested — this
  1165	                # attributes evidence to the PR itself, not to whichever issue it happens to
  1166	                # close. Narrowing this to "only if the PR closes/references a tracked issue"
  1167	                # (introduced in GH-421's build) silently drops the guarantee for exactly the
  1168	                # PRs least likely to be scrutinized: ones with no linked issue at all.
  1169	                if args.require_receipts:
  1170	                    check_provenance_receipts(repo_root, pr_meta)
  1171	                reconciled_issues.update(linked_issues)
  1172	                log(f"  {landing} closes {linked_issues}; references {mentioned_issues}")
  1173	                # GH-271: mentions never act on their own. --force-promote is the one
  1174	                # explicit operator override that widens the action set past closers.
  1175	                action_issues = (
  1176	                    sorted(set(linked_issues) | set(mentioned_issues))
  1177	                    if args.force_promote
  1178	                    else linked_issues
  1179	                )
  1180	
  1181	                for issue_num in action_issues:
  1182	                    doc_path = find_active_doc_for_issue(repo_root, issue_num)
  1183	                    issue_state = fetch_issue_state(repo_root, issue_num, offline_manifest)
  1184	                    fm = parse_doc_frontmatter(doc_path) if doc_path else {}
  1185	                    is_multiphase = (
  1186	                        fm.get("umbrella") in ("true", "1", "yes")
  1187	                        or fm.get("multiphase") in ("true", "1", "yes")
  1188	                        or fm.get("multi_phase") in ("true", "1", "yes")
  1189	                    )
  1190	
  1191	                    is_open = (issue_state == "OPEN") or (issue_state is None and is_multiphase)
  1192	
  1193	                    if doc_path and is_open and is_merged and not args.force_promote:
  1194	                        # GH-202/GH-232: a merged PR does not complete an open issue or multi-phase umbrella.
  1195	                        # Phased umbrellas and open issues keep their active doc; evidence recorded in place.
  1196	                        log(f"  Issue #{issue_num} is OPEN — keeping {os.path.basename(doc_path)} active; recording merge evidence")
  1197	                        record_merge_evidence(doc_path, pr_meta, dry_run=args.dry_run, journal=journal)
  1198	                        log(f"  Issue #{issue_num} is OPEN — preserving active ROADMAP.md entry (skipping move to Completed)")
  1199	                    elif doc_path:
  1200	                        if is_merged:
  1201	                            ship_manifest_items(repo_root, issue_num, pr_meta, repo_slug, args.dry_run, journal)
  1202	                        log(f"  Found active doc: {os.path.basename(doc_path)}")
  1203	                        dest_path, ship_date = validate_and_update_doc(
  1204	                            doc_path, pr_meta, is_merged=is_merged, dry_run=args.dry_run, journal=journal
  1205	                        )
  1206	                        log(f"  Moved -> {os.path.basename(dest_path)} (destination: {os.path.basename(os.path.dirname(dest_path))})")
  1207	                        updated = update_roadmap_entry(
  1208	                            repo_root,
  1209	                            issue_num,
  1210	                            landing,
  1211	                            ship_date,
  1212	                            is_merged=is_merged,
  1213	                            dry_run=args.dry_run,
  1214	                            journal=journal,
  1215	                            doc_path=os.path.relpath(dest_path, repo_root),
  1216	                        )
  1217	                        if updated:
  1218	                            log(f"  ROADMAP.md entry updated for GH-{issue_num}")
  1219	                    else:
  1220	                        log(f"  No active doc in 2-WORKING for GH-{issue_num}")
     1	#!/usr/bin/env bash
     2	# utils/roadmap-dashboard.sh — render a read-only dashboard from ROADMAP.md (GH-27).
     3	
     4	set -euo pipefail
     5	
     6	HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
     7	# GH-272: releases-merge-resolve.sh drives this renderer against a --root TARGET repo —
     8	# the ledger it renders and the dashboard it writes must follow the target, not this
     9	# script's own checkout. Self-location stays the default for every other caller.
    10	ROOT="${ROADMAP_DASHBOARD_ROOT:-$(cd "$HERE/.." && pwd)}"
    11	SOURCE_FILE="${ROADMAP_DASHBOARD_SOURCE:-"$ROOT/ROADMAP.md"}"
    12	OUTPUT_FILE="${ROADMAP_DASHBOARD_OUTPUT:-"$ROOT/ROADMAP-DASHBOARD.md"}"
    13	
    14	usage() {
    15	  cat <<'EOF'
    16	Usage: bash utils/roadmap-dashboard.sh [--check]
    17	
    18	  Default: render ROADMAP-DASHBOARD.md from the canonical root ROADMAP.md.
    19	  --check: exit 0 when ROADMAP-DASHBOARD.md is in sync; non-zero on drift.
    20	EOF
    21	}
    22	
    23	MODE="write"
    24	if (($# > 1)); then
    25	  usage
    26	  exit 2
    27	fi
    28	if (($# == 1)); then
    29	  case "$1" in
    30	    --check) MODE="check" ;;
    31	    --help|-h) usage; exit 0 ;;
    32	    *) usage; exit 2 ;;
    33	  esac
    34	fi
    35	
    36	command -v node >/dev/null 2>&1 || {
    37	  echo "roadmap-dashboard: node is required" >&2
    38	  exit 2
    39	}
    40	
    41	TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/roadmap-dashboard.XXXXXX")"
    42	trap 'rm -rf "$TMP_DIR"' EXIT
    43	RENDERED="$TMP_DIR/ROADMAP-DASHBOARD.md"
    44	
    45	# GH-243: in a releases-mode repo the DB is the roadmap's source of truth and ROADMAP.md is
    46	# frozen — render from `roadmap list --json` (each row's lossless raw_text under its section)
    47	# instead of the legacy file. An explicit ROADMAP_DASHBOARD_SOURCE still wins (test seam), and
    48	# any failure here falls back to the legacy file rather than emitting an empty dashboard.
    49	if [ -z "${ROADMAP_DASHBOARD_SOURCE:-}" ] \
    50	   && (grep -q "ROADMAP_SOURCE=releases" "$ROOT/.pdda-mode" 2>/dev/null || [ ! -f "$ROOT/ROADMAP.md" ]) \
    51	   && [ -f "$ROOT/releases.db" ] && command -v python3 >/dev/null 2>&1; then
    52	  DB_SRC="$TMP_DIR/roadmap-from-db.md"
    53	  DB_JSON="$TMP_DIR/roadmap-rows.json"
    54	  # JSON goes through a temp file passed as argv — `python3 -` takes its PROGRAM from the
    55	  # heredoc on stdin, so piping data in as well would feed the parser nothing (the PR #240
    56	  # rollup.sh bug, same shape). The APP resolves from HERE (this script's own checkout) while
    57	  # --root follows $ROOT: under ROADMAP_DASHBOARD_ROOT (GH-272) the target repo may ship the
    58	  # ledger without a utils/ tree at all.
    59	  if python3 "$HERE/py/releases_app.py" --root "$ROOT" roadmap list --json > "$DB_JSON" 2>/dev/null \
    60	     && python3 - "$DB_JSON" > "$DB_SRC" <<'PY'
    61	import json, sys
    62	with open(sys.argv[1]) as f:
    63	    rows = json.load(f)
    64	print("# ROADMAP (rendered from the RELEASES DB — GH-243; ROADMAP.md is frozen legacy)\n")
    65	print("## Ledger\n")   # the renderer only counts sections below this heading
    66	sections = {}
    67	for r in rows:
    68	    sections.setdefault(r.get("section") or "(unsectioned)", []).append(r)
    69	for section, items in sections.items():
    70	    print(f"### {section}\n")
    71	    for r in sorted(items, key=lambda x: x.get("position") or 0):
    72	        line = (r.get("raw_text") or "").strip()
    73	        if not line:
    74	            gh = f"GH-{r['gh_number']} · " if r.get("gh_number") is not None else ""
    75	            line = f"- **{gh}{r.get('title', '')}**"
    76	        print(line)
    77	    print()
    78	PY
    79	  then
    80	    [ -s "$DB_SRC" ] && SOURCE_FILE="$DB_SRC"
    81	  fi
    82	fi
    83	
    84	if [ ! -f "$SOURCE_FILE" ]; then
    85	  echo "roadmap-dashboard: source not found: $SOURCE_FILE" >&2
    86	  exit 3
    87	fi
    88	
    89	# Resolve from HERE, not ROOT: a target ledger need not ship its own utils/ tree.
    90	# Failure must stop rendering rather than fall back to a second, drifting vocabulary.
    91	LEDGER_SECTIONS_JSON="$(python3 "$HERE/py/releases_app.py" roadmap sections --json)"
    92	node - "$SOURCE_FILE" "$LEDGER_SECTIONS_JSON" >"$RENDERED" <<'NODE'
    93	const fs = require("fs");
    94	
    95	const sourcePath = process.argv[2];
    96	const raw = fs.readFileSync(sourcePath, "utf8");
    97	const lines = raw.split(/\r?\n/);
    98	
    99	const banner = "<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit ROADMAP.md -->";
   100	const ledgerSections = JSON.parse(process.argv[3]);
   101	const knownStatuses = ["🟢", "🟡", "⏸️", "⛔", "✅", "🔮", "🔲"];
   102	const extraStatuses = ["⚠️"];
   103	
   104	function escapeCell(value) {
   105	  return String(value)
   106	    .replace(/\|/g, "\\|")
   107	    .replace(/</g, "&lt;")
   108	    .replace(/>/g, "&gt;");
   109	}
   110	
   111	function stripMarkdown(value) {
   112	  return value
   113	    .replace(/`([^`]+)`/g, "$1")
   114	    .replace(/\*\*([^*]+)\*\*/g, "$1")
   115	    .replace(/\*([^*]+)\*/g, "$1")
   116	    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
   117	    .trim();
   118	}
   119	
   120	function parseBullet(block) {
   121	  const text = block.map((line) => line.trim()).join(" ").replace(/\s+/g, " ").trim();
   122	  const titleMatch = text.match(/^- \*\*(.+?)\*\*/);
   123	  const title = titleMatch ? stripMarkdown(titleMatch[1]) : stripMarkdown(text.replace(/^- /, ""));
   124	
   125	  let status = "—";
   126	  for (const emoji of knownStatuses.concat(extraStatuses)) {
   127	    if (text.includes(emoji)) {
   128	      status = emoji;
   129	      break;
   130	    }
   131	  }
   132	
   133	  const links = [];
   134	  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
   135	  let match;
   136	  while ((match = linkPattern.exec(text)) !== null) {
   137	    links.push(`[${match[1]}](${match[2]})`);
   138	  }
   139	
   140	  return { title, status, links };
   141	}
   142	
   143	function formatTally(items) {
   144	  const counts = new Map();
   145	  for (const emoji of knownStatuses) counts.set(emoji, 0);
   146	  const extras = [];
   147	
   148	  for (const item of items) {
   149	    if (counts.has(item.status)) {
   150	      counts.set(item.status, counts.get(item.status) + 1);
   151	      continue;
   152	    }
   153	    if (item.status !== "—") {
   154	      if (!counts.has(item.status)) extras.push(item.status);
   155	      counts.set(item.status, (counts.get(item.status) || 0) + 1);
   156	    }
   157	  }
   158	
   159	  const ordered = knownStatuses.slice();
   160	  for (const emoji of extras) {
   161	    if (!ordered.includes(emoji)) ordered.push(emoji);
   162	  }
   163	
   164	  return ordered.map((emoji) => `${emoji} ${counts.get(emoji) || 0}`).join(" · ");
   165	}
   166	
   167	const sections = new Map();
   168	for (const heading of ledgerSections) sections.set(heading, []);
   169	
   170	let inLedger = false;
   171	let currentSection = null;
   172	let unknownSection = null;
   173	const droppedRows = [];
   174	// GH-474: rows under a heading this renderer does not recognise. They parse fine — they are
   175	// simply never rendered, because `sections` has no bucket for their heading. That makes them
   176	// INVISIBLE in the view while the ledger still carries them, and invisible without a byte
   177	// difference: the row was never in the output, so a fresh render still matches the committed
   178	// file. `releases roadmap update/move --section` writes the section verbatim with no
   179	// validation (utils/py/releases_app.py), so one typo is all it takes.
   180	const unknownSectionRows = [];
   181	
   182	for (let i = 0; i < lines.length; i++) {
   183	  const line = lines[i];
   184	
   185	  if (!inLedger) {
   186	    if (/^##\s+Ledger\s*$/.test(line.trim())) inLedger = true;
   187	    continue;
   188	  }
   189	
   190	  if (/^##\s+/.test(line) && !/^##\s+Ledger\s*$/.test(line.trim())) break;
   191	
   192	  const sectionMatch = line.match(/^###\s+(.+?)\s*$/);
   193	  if (sectionMatch) {
   194	    const heading = sectionMatch[1].trim();
   195	    if (sections.has(heading)) {
   196	      currentSection = heading;
   197	      unknownSection = null;
   198	    } else {
   199	      currentSection = null;
   200	      unknownSection = heading;
   201	    }
   202	    continue;
   203	  }
   204	
   205	  if (!currentSection) {
   206	    // GH-474: silence here used to be indistinguishable from "there was nothing to render".
   207	    // Report the rows an unrecognised heading swallowed, so a consumer reading stderr (the
   208	    // push guard) can tell "rendered everything" apart from "rendered everything I recognised".
   209	    // Only list items are counted: a bullet's continuation lines ride with their bullet.
   210	    if (unknownSection && /^\s*[-*+]\s+/.test(line)) {
   211	      const t = line.trim();
   212	      const m = t.match(/(?:GH-?|#)(\d+)/i);
   213	      unknownSectionRows.push({
   214	        section: unknownSection,
   215	        id: m ? `#${m[1]}` : JSON.stringify(t.length > 30 ? t.slice(0, 30) + "..." : t),
   216	        line: t,
   217	      });
   218	    }
   219	    continue;
   220	  }
utils/py/releases_app.py:36:                                 the DB/dump/digest/generation contract, so a refused writer
utils/py/releases_app.py:144:GENERATION_KEY = "generation"
utils/py/releases_app.py:158:# The settings keys an operator may write with `releases settings set`. Deliberately a
utils/py/releases_app.py:159:# deny-by-default allowlist: `generation` belongs to the writer protocol and `repo_slug` is the
utils/py/releases_app.py:452:    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
utils/py/releases_app.py:471:def get_generation(conn):
utils/py/releases_app.py:496:CREATE TABLE settings (            -- per-repo DB, so per-repo enforcement mode lives here
utils/py/releases_app.py:612:  state_digest_after TEXT NOT NULL     --   op_receipts, lock_audit, generation, and all digest
utils/py/releases_app.py:934:    releases, manifest_items, marathons, repos, settings, issue_refs, doc_lines, legacy_lines,
utils/py/releases_app.py:938:    tables = ("releases", "manifest_items", "marathons", "repos", "settings", "issue_refs",
utils/py/releases_app.py:1034:def dump_text(conn, generation, include_receipts=True, include_generation=True):
utils/py/releases_app.py:1035:    """Canonical logical dump. include_receipts=False, include_generation=False yields exactly
utils/py/releases_app.py:1036:    the BUSINESS-STATE text the receipt digests hash (r3: excluding op_receipts, generation and
utils/py/releases_app.py:1045:    if include_generation:
utils/py/releases_app.py:1046:        w("-- generation: %d" % generation)
utils/py/releases_app.py:1052:    settings_select = "SELECT key, value{extra} FROM settings"
utils/py/releases_app.py:1053:    if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1058:    if not include_generation:
utils/py/releases_app.py:1060:    _emit(w, "settings", settings_cols, _rows(conn, settings_select.format(extra=settings_extra) + " ORDER BY key"))
utils/py/releases_app.py:1225:    text = dump_text(conn, generation=0, include_receipts=False, include_generation=False)
utils/py/releases_app.py:1229:def dump_generation_from_text(text):
utils/py/releases_app.py:1231:        m = re.match(r"^-- generation: (\d+)$", line.strip())
utils/py/releases_app.py:1237:# ── generation marker in the generated file ─────────────────────────────────────────────────────
utils/py/releases_app.py:1242:GEN_MARKER_RE = re.compile(r"^<!-- releases-app generation: (\d+) -->$")
utils/py/releases_app.py:1245:def gen_marker(generation):
utils/py/releases_app.py:1246:    return "<!-- releases-app generation: %d -->" % generation
utils/py/releases_app.py:1302:    # LEADERBOARD.md rides the same adoption signal — generated, never hand-edited.
utils/py/releases_app.py:1303:    board = os.path.join(root, "LEADERBOARD.md")
utils/py/releases_app.py:1310:                print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
utils/py/releases_app.py:1313:            print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
utils/py/releases_app.py:1320:      write intent journal (txn_id, NEXT generation, planned outputs)   [BEFORE the DB commit]
utils/py/releases_app.py:1321:      -> BEGIN IMMEDIATE -> mutate -> stamp generation into settings -> COMMIT
utils/py/releases_app.py:1322:      -> stage dump (+ generated view when one exists), each carrying that generation
utils/py/releases_app.py:1338:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1346:            "generation": generation, "planned_outputs": planned,
utils/py/releases_app.py:1369:        if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1370:            cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
utils/py/releases_app.py:1371:                               (str(generation), now, GENERATION_KEY))
utils/py/releases_app.py:1373:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
utils/py/releases_app.py:1374:                             (GENERATION_KEY, str(generation), now))
utils/py/releases_app.py:1376:            cur = conn.execute("UPDATE settings SET value = ? WHERE key = ?",
utils/py/releases_app.py:1377:                               (str(generation), GENERATION_KEY))
utils/py/releases_app.py:1379:                conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
utils/py/releases_app.py:1380:                             (GENERATION_KEY, str(generation)))
utils/py/releases_app.py:1391:        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
utils/py/releases_app.py:1394:                                        gen_marker(generation) + "\n" + render_ledger(conn)),
utils/py/releases_app.py:1426:        -> stamp generation + op_receipt -> COMMIT
utils/py/releases_app.py:1459:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1466:            "generation": generation, "planned_outputs": planned, "db": paths["db"],
utils/py/releases_app.py:1483:            if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1484:                cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
utils/py/releases_app.py:1485:                                   (str(generation), now, GENERATION_KEY))
utils/py/releases_app.py:1487:                    conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
utils/py/releases_app.py:1488:                                 (GENERATION_KEY, str(generation), now))
utils/py/releases_app.py:1490:                cur = conn.execute("UPDATE settings SET value = ? WHERE key = ?",
utils/py/releases_app.py:1491:                                   (str(generation), GENERATION_KEY))
utils/py/releases_app.py:1493:                    conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
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
utils/py/releases_app.py:1956:            if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1957:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES ('enforcement', 'lenient', ?)", (now,))
utils/py/releases_app.py:1958:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES ('repo_slug', ?, ?)", (slug, now))
utils/py/releases_app.py:1959:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, '1', ?)", (GENERATION_KEY, now))
utils/py/releases_app.py:1961:                conn.execute("INSERT INTO settings(key, value) VALUES ('enforcement', 'lenient')")
utils/py/releases_app.py:1962:                conn.execute("INSERT INTO settings(key, value) VALUES ('repo_slug', ?)", (slug,))
utils/py/releases_app.py:1963:                conn.execute("INSERT INTO settings(key, value) VALUES (?, '1')", (GENERATION_KEY,))
utils/py/releases_app.py:1964:            generation = get_generation(conn)
utils/py/releases_app.py:1965:            _atomic_write(paths["dump"], dump_text(conn, generation))
utils/py/releases_app.py:1970:    print("initialized %s (slug %r, enforcement=lenient, generation 1); canonical dump at %s"
utils/py/releases_app.py:3515:    dashboard guard sees a clean regeneration range on the next push.
utils/py/releases_app.py:3547:    """`releases settings set <key> <value>` — write a settings row THROUGH the writer protocol.
utils/py/releases_app.py:3549:    GH-525: without this there is no supported way to configure the ledger at all. A settings row
utils/py/releases_app.py:3556:    writable: `generation` is owned by the writer protocol and `repo_slug` is identity, and letting
utils/py/releases_app.py:3571:            if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:3572:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?) "
utils/py/releases_app.py:3577:                conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) "
utils/py/releases_app.py:3581:        perform_write(root, conn, "settings-set", None, mutate)
utils/py/releases_app.py:3588:    """Print every settings row, so "what is this ledger configured to do" is one command."""
utils/py/releases_app.py:3592:        for row in conn.execute("SELECT key, value FROM settings ORDER BY key"):
utils/py/releases_app.py:3936:            print(summary + " — already in sync; no write, generation unchanged")
utils/py/releases_app.py:3971:        print(summary + " (txn %s, generation %d)" % (txn[:12], get_generation(conn)))
utils/py/releases_app.py:4538:        generation = get_generation(conn)
utils/py/releases_app.py:4539:        _atomic_write(paths["gen"], gen_marker(generation) + "\n" + render_ledger(conn))
utils/py/releases_app.py:4541:        print("generated %s (side-by-side, generation %d) + drift report %s"
utils/py/releases_app.py:4542:              % (paths["gen"], generation, paths["drift"]))
utils/py/releases_app.py:4616:            db_gen = get_generation(conn)
utils/py/releases_app.py:4622:                dump_gen = dump_generation_from_text(dump_content)
utils/py/releases_app.py:4624:                    fail("generation-mismatch",
utils/py/releases_app.py:4625:                         "settings.generation=%d but %s says %s — write in progress, crashed, or "
utils/py/releases_app.py:4638:                print("OK: generation trio consistent at %d (DB <-> dump)" % db_gen)
utils/py/releases_app.py:4646:                    fail("generation-mismatch",
utils/py/releases_app.py:4647:                         "%s carries generation %s but the DB is at %d — regenerate with "
utils/py/releases_app.py:4650:                    print("OK: %s generation marker matches (%d)" % (GEN_NAME, db_gen))
utils/py/releases_app.py:4793:                resolved = {"dump-divergence", "dump-missing", "generation-mismatch",
utils/py/releases_app.py:4892:    branches made unequal numbers of writes, keep BOTH `-- generation:` headers with no conflict
utils/py/releases_app.py:4900:               if re.match(r"^-- generation: \d+$", ln.strip())]
utils/py/releases_app.py:4902:        refuse("dump-multi-generation",
utils/py/releases_app.py:4903:               "the dump carries %d '-- generation:' headers (%s); a canonical dump has exactly one. "
utils/py/releases_app.py:4906:               "silently understate the generation. Keep the HIGHEST header, delete the rest, then "
utils/py/releases_app.py:4926:    for row in tables.get("settings", []):
utils/py/releases_app.py:4930:                   "settings key %r appears more than once. `settings` holds one row per key, so a "
utils/py/releases_app.py:4932:                   "(for 'generation', the higher value), delete the other, then rebuild." % key)
utils/py/releases_app.py:4966:    for row in tables.get("settings", []):
utils/py/releases_app.py:4967:        if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:4968:            conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
utils/py/releases_app.py:4971:            conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)", (row["key"], row["value"]))
utils/py/releases_app.py:5156:    dump_gen = dump_generation_from_text(dump_content)
utils/py/releases_app.py:5158:        refuse("dump-generation", "%s carries no generation header — not a canonical dump"
utils/py/releases_app.py:5162:    old_gen = get_generation(conn)
utils/py/releases_app.py:5204:            if _has_column(tconn, "settings", "updated_at"):
utils/py/releases_app.py:5205:                tconn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
utils/py/releases_app.py:5207:                if tconn.execute("SELECT 1 FROM settings WHERE key = ?",
utils/py/releases_app.py:5209:                    tconn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
utils/py/releases_app.py:5212:                tconn.execute("UPDATE settings SET value = ? WHERE key = ?",
utils/py/releases_app.py:5214:                if tconn.execute("SELECT 1 FROM settings WHERE key = ?",
utils/py/releases_app.py:5216:                    tconn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
utils/py/releases_app.py:5257:    print("rebuilt %s from %s (generation %d -> %d); displaced DB backed up at %s"
utils/py/releases_app.py:5274:        db_gen = get_generation(conn)
utils/py/releases_app.py:5282:                dump_gen = dump_generation_from_text(f.read())
utils/py/releases_app.py:5286:            staleness_banner = "<div style='background: red; color: white; padding: 10px; font-weight: bold;'>STALE SYNC: DB generation (%d) != Dump generation (%d)</div>" % (db_gen, dump_gen)
utils/py/releases_app.py:5415:                                             "(Phase 0+1: side-by-side generation only)")
utils/py/releases_app.py:5419:    sp = sub.add_parser("init", help="create the DB + dump; settings default lenient")
utils/py/releases_app.py:5520:    sp = sub.add_parser("gen", help="side-by-side generation (Phase 0: NEVER writes RELEASES.md)")
utils/py/releases_app.py:5537:    # GH-525: a ledger with configurable behaviour needs a configuring verb. A settings row is part
utils/py/releases_app.py:5540:    sp_set = sub.add_parser("settings", help="read/write operator-configurable ledger settings")
utils/py/releases_app.py:5542:    sp_sl = ssub.add_parser("list", help="print every settings row")
utils/py/releases_app.py:5736:        "settings": lambda a: {"set": cmd_settings_set,
utils/timeline/export_timeline.py:5:marathons, roadmap_items, settings, op_receipts) and emits
utils/timeline/export_timeline.py:448:    settings = dict(cx.execute("SELECT key, value FROM settings"))
utils/timeline/export_timeline.py:481:        {"slug": slug, "active": slug == settings.get("repo_slug")}
utils/timeline/export_timeline.py:483:    ] or [{"slug": settings.get("repo_slug", "repo"), "active": True}]
utils/timeline/export_timeline.py:522:            "subtitle": f"{settings.get('repo_slug', 'repo')} · releases.db · read-only",
utils/timeline/export_timeline.py:530:            "dbGeneration": int(settings.get("generation", 0)),
utils/leaderboard.sh:2:# utils/leaderboard.sh — render LEADERBOARD.md, the ranked read of every rated task (GH-108).
utils/leaderboard.sh:10:# LEADERBOARD.md is GENERATED and never hand-edited, following the established
utils/leaderboard.sh:13:# GitHub. Regeneration is idempotent — a stale checked-in copy is a review signal, not a hazard.
utils/leaderboard.sh:20:OUT="${LEADERBOARD_OUTPUT:-$ROOT/LEADERBOARD.md}"
utils/leaderboard.sh:27:  Default: render LEADERBOARD.md from releases.db via export_timeline.py --json.
utils/leaderboard.sh:28:  --check: write nothing; exit 0 when LEADERBOARD.md is already in sync, 1 on drift.
utils/marathon-plan.sh:1125:  // (surface) only: no per-lane run/verdict tracking (Level 2), no auto-generation from `gh pr list`
utils/pdda/pdda-edit-doc-hook.sh:13:# for visibility only. Wire it in .claude/settings.json (PostToolUse, matcher "Edit|Write|MultiEdit").
utils/pdda/pdda-stop-doc-health.sh:8:# visibility only. Wire it in .claude/settings.json as a `Stop` hook. Pairs with tier 1,
utils/releases-merge-resolve.sh:17:#                                  LEADERBOARD.html / LEADERBOARD.md are all rendered from
utils/releases-merge-resolve.sh:43:# rewrote this repo's own releases.db/releases.sql (recovered from HEAD; generation had advanced
utils/releases-merge-resolve.sh:75:  derived artifacts do not. Resolve it first (union both sides' rows, keeping ONE '-- generation:'
utils/releases-merge-resolve.sh:86:# A merged dump can be syntactically fine and still carry two '-- generation:' headers, which is
utils/releases-merge-resolve.sh:89:GEN_HEADERS="$(grep -c '^-- generation: ' "$DUMP" || true)"
utils/releases-merge-resolve.sh:91:  die "releases.sql carries $GEN_HEADERS '-- generation:' headers; a canonical dump has exactly one.
utils/releases-merge-resolve.sh:94:  the first and silently understate the generation.)"
utils/releases-merge-resolve.sh:96:[ "${GEN_HEADERS:-0}" -eq 1 ] || die "releases.sql carries no '-- generation:' header — not a canonical dump"
utils/releases-merge-resolve.sh:100:# with the ledger's generation counter silently REWOUND below a parent's. The advice to "keep the
utils/releases-merge-resolve.sh:104:_gen_of() {  # <git-ref-or-empty> -> the dump's generation number at that ref, or nothing
utils/releases-merge-resolve.sh:107:    | sed -n 's/^-- generation: \([0-9][0-9]*\)$/\1/p' | head -1
utils/releases-merge-resolve.sh:110:  KEPT="$(sed -n 's/^-- generation: \([0-9][0-9]*\)$/\1/p' "$DUMP" | head -1)"
utils/releases-merge-resolve.sh:116:    die "releases.sql kept '-- generation: $KEPT', but this merge's parents are at
utils/releases-merge-resolve.sh:118:  rewinds the ledger's generation counter, and every later check would still report clean — the
utils/releases-merge-resolve.sh:160:VIEWS="ROADMAP-DASHBOARD.md RELEASES-PREVIEW.html LEADERBOARD.html LEADERBOARD.md"
utils/releases-merge-resolve.sh:225:    *" LEADERBOARD.md "*)
utils/releases-merge-resolve.sh:227:      if ! LEADERBOARD_DB="$ROOT/releases.db" LEADERBOARD_OUTPUT="$ROOT/LEADERBOARD.md" bash "$HERE/leaderboard.sh"; then
utils/releases-merge-resolve.sh:228:        die "leaderboard.sh failed. The merge is left open on purpose; the stale LEADERBOARD.md
utils/py/fuzz_inputs.py:3:Fuzz generation and oracles for the four GH-141 Phase 3 target families.
utils/py/board_sync.py:9:    board_sync.py config                   print resolved settings (no secrets)
utils/py/board_sync.py:89:def resolve_settings():
utils/py/board_sync.py:300:        _warn("cached board IDs were resolved from different settings — re-resolving")
utils/py/board_sync.py:516:    sub.add_parser("config", help="print resolved settings (no secrets)")
utils/py/board_sync.py:526:    cfg = resolve_settings()
utils/py/express.py:72:    "LEADERBOARD.md",
utils/py/express.py:703:    "LEADERBOARD.md",
utils/py/consult.py:326:            # generation this harness has driven. Verdict routing below kept as the safety net.
utils/py/device_config.py:70:    """Return dictionary of all active resolved runtime settings."""
utils/py/releases_cycle.py:56:    settings = dict(cx.execute("SELECT key, value FROM settings"))
utils/py/releases_cycle.py:121:        "repo": repo_label or settings.get("repo_slug"),
utils/py/releases_cycle.py:123:        "db": {"generation": int(settings.get("generation", 0) or 0), "receipts": receipts,
utils/py/releases_cycle.py:153:        f"_generated {s['generatedAt']} · db generation {db['generation']} · "
utils/py/releases_cycle.py:198:                    help="override the repo label (default: the DB's own settings.repo_slug)")
utils/py/wave_reconcile.py:909:    Both per-issue writes and downstream regeneration use this same snapshot set.
utils/py/wave_reconcile.py:916:        "LEADERBOARD.html", "LEADERBOARD.md",
utils/py/wave_reconcile.py:929:    log("Running downstream database sync and dashboard regeneration...")
utils/py/wave_reconcile.py:1265:            # GH-421: skip downstream regeneration only when there was genuinely nothing to
utils/py/agy-turn.py:138:            # agy generation this harness has driven, runs headless without a TTY, and requires
utils/py/agy-turn.py:537:        # and isolation settings: the phase with TEN repo-root mentions was Approved, the one with
utils/py/releases_app.py:36:                                 the DB/dump/digest/generation contract, so a refused writer
utils/py/releases_app.py:144:GENERATION_KEY = "generation"
utils/py/releases_app.py:158:# The settings keys an operator may write with `releases settings set`. Deliberately a
utils/py/releases_app.py:159:# deny-by-default allowlist: `generation` belongs to the writer protocol and `repo_slug` is the
utils/py/releases_app.py:452:    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
utils/py/releases_app.py:471:def get_generation(conn):
utils/py/releases_app.py:496:CREATE TABLE settings (            -- per-repo DB, so per-repo enforcement mode lives here
utils/py/releases_app.py:612:  state_digest_after TEXT NOT NULL     --   op_receipts, lock_audit, generation, and all digest
utils/py/releases_app.py:934:    releases, manifest_items, marathons, repos, settings, issue_refs, doc_lines, legacy_lines,
utils/py/releases_app.py:938:    tables = ("releases", "manifest_items", "marathons", "repos", "settings", "issue_refs",
utils/py/releases_app.py:1034:def dump_text(conn, generation, include_receipts=True, include_generation=True):
utils/py/releases_app.py:1035:    """Canonical logical dump. include_receipts=False, include_generation=False yields exactly
utils/py/releases_app.py:1036:    the BUSINESS-STATE text the receipt digests hash (r3: excluding op_receipts, generation and
utils/py/releases_app.py:1045:    if include_generation:
utils/py/releases_app.py:1046:        w("-- generation: %d" % generation)
utils/py/releases_app.py:1052:    settings_select = "SELECT key, value{extra} FROM settings"
utils/py/releases_app.py:1053:    if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1058:    if not include_generation:
utils/py/releases_app.py:1060:    _emit(w, "settings", settings_cols, _rows(conn, settings_select.format(extra=settings_extra) + " ORDER BY key"))
utils/py/releases_app.py:1225:    text = dump_text(conn, generation=0, include_receipts=False, include_generation=False)
utils/py/releases_app.py:1229:def dump_generation_from_text(text):
utils/py/releases_app.py:1231:        m = re.match(r"^-- generation: (\d+)$", line.strip())
utils/py/releases_app.py:1237:# ── generation marker in the generated file ─────────────────────────────────────────────────────
utils/py/releases_app.py:1242:GEN_MARKER_RE = re.compile(r"^<!-- releases-app generation: (\d+) -->$")
utils/py/releases_app.py:1245:def gen_marker(generation):
utils/py/releases_app.py:1246:    return "<!-- releases-app generation: %d -->" % generation
utils/py/releases_app.py:1302:    # LEADERBOARD.md rides the same adoption signal — generated, never hand-edited.
utils/py/releases_app.py:1303:    board = os.path.join(root, "LEADERBOARD.md")
utils/py/releases_app.py:1310:                print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
utils/py/releases_app.py:1313:            print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
utils/py/releases_app.py:1320:      write intent journal (txn_id, NEXT generation, planned outputs)   [BEFORE the DB commit]
utils/py/releases_app.py:1321:      -> BEGIN IMMEDIATE -> mutate -> stamp generation into settings -> COMMIT
utils/py/releases_app.py:1322:      -> stage dump (+ generated view when one exists), each carrying that generation
utils/py/releases_app.py:1338:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1346:            "generation": generation, "planned_outputs": planned,
utils/py/releases_app.py:1369:        if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1370:            cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
utils/py/releases_app.py:1371:                               (str(generation), now, GENERATION_KEY))
utils/py/releases_app.py:1373:                conn.execute("INSERT INTO settings(key, value, updated_at) VALUES (?, ?, ?)",
utils/py/releases_app.py:1374:                             (GENERATION_KEY, str(generation), now))
utils/py/releases_app.py:1376:            cur = conn.execute("UPDATE settings SET value = ? WHERE key = ?",
utils/py/releases_app.py:1377:                               (str(generation), GENERATION_KEY))
utils/py/releases_app.py:1379:                conn.execute("INSERT INTO settings(key, value) VALUES (?, ?)",
utils/py/releases_app.py:1380:                             (GENERATION_KEY, str(generation)))
utils/py/releases_app.py:1391:        staged = [(_stage_write(paths["dump"], dump_text(conn, generation)), paths["dump"])]
utils/py/releases_app.py:1394:                                        gen_marker(generation) + "\n" + render_ledger(conn)),
utils/py/releases_app.py:1426:        -> stamp generation + op_receipt -> COMMIT
utils/py/releases_app.py:1459:        generation = get_generation(conn) + 1
utils/py/releases_app.py:1466:            "generation": generation, "planned_outputs": planned, "db": paths["db"],
utils/py/releases_app.py:1483:            if _has_column(conn, "settings", "updated_at"):
utils/py/releases_app.py:1484:                cur = conn.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '880,1100p'
nl -ba utils/py/wave_reconcile.py | sed -n '1100,1325p'
nl -ba utils/roadmap-dashboard.sh | sed -n '1,180p'
nl -ba utils/leaderboard.sh | sed -n '1,180p'
nl -ba utils/py/releases_app.py | sed -n '1230,1320p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
   880	        if result.returncode == 5:
   881	            log("  marathon-plan reports items held (exit 5) without structured findings — continuing (GH-202 compatibility)")
   882	            return
   883	        die("marathon-plan reported drift (exit 4) without attributable structured findings", code=6)
   884	
   885	    reconciled = {int(issue) for issue in reconciled_issues}
   886	    owned = [
   887	        finding for finding in findings
   888	        if finding_issue_numbers(finding) & reconciled
   889	    ]
   890	    unrelated = [finding for finding in findings if finding not in owned]
   891	
   892	    if owned:
   893	        labels = ", ".join(describe_finding(finding) for finding in owned)
   894	        die(
   895	            "marathon-plan found drift/held state attributable to the reconciled "
   896	            f"PR item(s): {labels}",
   897	            code=6,
   898	        )
   899	
   900	    log("  WARNING — marathon-plan found pre-existing unrelated drift/held items; keeping reconciliation:")
   901	    for finding in unrelated:
   902	        log(f"    - {describe_finding(finding)}")
   903	
   904	
   905	def snapshot_ledger_artifacts(repo_root, dry_run=False, journal=None):
   906	    """GH-424: capture the ledger and generated views BEFORE the first write.
   907	
   908	    Repeated calls retain the original state, including originally absent artifacts.
   909	    Both per-issue writes and downstream regeneration use this same snapshot set.
   910	    """
   911	    if dry_run or journal is None:
   912	        return
   913	    for name in (
   914	        "releases.db", "releases.sql", "RELEASES.generated.md",
   915	        "ROADMAP-DASHBOARD.md", "RELEASES-PREVIEW.html",
   916	        "LEADERBOARD.html", "LEADERBOARD.md",
   917	    ):
   918	        path = os.path.abspath(os.path.join(repo_root, name))
   919	        if path in journal.backups or path in journal.created_files:
   920	            continue
   921	        if os.path.exists(path):
   922	            journal.snapshot(path)
   923	        else:
   924	            journal.track_created(path)
   925	
   926	
   927	def run_subprocesses(repo_root, dry_run=False, journal=None, reconciled_issues=None):
   928	    """Orchestrate releases sync, view exports, and marathon replanning with DB rollback protection."""
   929	    log("Running downstream database sync and dashboard regeneration...")
   930	
   931	    snapshot_ledger_artifacts(repo_root, dry_run=dry_run, journal=journal)
   932	
   933	    def _plan_docs():
   934	        found = set()
   935	        for pattern in ("MARATHON-PLAN-*.md", os.path.join("PROJECT", "2-WORKING", "MARATHON-PLAN-*.md")):
   936	            found.update(glob.glob(os.path.join(repo_root, pattern)))
   937	        return found
   938	
   939	    pre_plan_docs = _plan_docs() if not dry_run else set()
   940	    if journal and not dry_run:
   941	        # Codex consult: a same-dated plan doc that already exists gets OVERWRITTEN by the
   942	        # replan, and tracking-only-created would leave rollback no bytes to restore.
   943	        for existing_doc in pre_plan_docs:
   944	            journal.snapshot(existing_doc)
   945	
   946	    # GH-358: resolve each harness tool against the repo first, then the harness home. On a
   947	    # vendored install these five live only under <repo>/.xyz/ and every one was unreachable,
   948	    # so the reconciler died on its first downstream step.
   949	    releases_app = harness_tool(repo_root, "utils/py/releases_app.py")
   950	    sync_cmd = ["python3", releases_app, "--root", repo_root, "roadmap", "sync"]
   951	    check_cmd = ["python3", releases_app, "--root", repo_root, "check"]
   952	    timeline_cmd = ["python3", harness_tool(repo_root, "utils/timeline/export_timeline.py"), "--preview"]
   953	    dash_cmd = ["bash", harness_tool(repo_root, "utils/roadmap-dashboard.sh")]
   954	    plan_cmd = ["bash", harness_tool(repo_root, "utils/marathon-plan.sh"), "--format", "json"]
   955	
   956	    if dry_run:
   957	        sync_cmd.append("--dry-run")
   958	        plan_cmd.append("--dry-run")
   959	
   960	    steps = [
   961	        ("releases roadmap sync", sync_cmd),
   962	        ("releases check", check_cmd),
   963	    ]
   964	    if not dry_run:
   965	        # GH-474: RELEASES-PREVIEW.html is an ADOPTED view — opt-in by presence. Every other
   966	        # consumer already treats it that way: releases_app.refresh_preview() skips it when
   967	        # absent (utils/py/releases_app.py:1170-1201), the merge resolver regenerates only what
   968	        # is already there (utils/releases-merge-resolve.sh:160-172), express.py snapshots it
   969	        # under os.path.lexists (utils/py/express.py:202-207) and jog_run.py stages it the same
   970	        # way. This step was the ONE consumer that regenerated it unconditionally, so a repo
   971	        # that had deliberately un-adopted the view got it silently recreated on the next
   972	        # reconcile — the deletion would not stick.
   973	        #
   974	        # ROADMAP-DASHBOARD.md stays unconditional on purpose, and the asymmetry is the point:
   975	        # it is NOT adopted-by-presence. It is required — githooks/dashboard-staleness-guard.sh
   976	        # refuses a push without it and utils/py/router_audit.py gates ROUTER.md's declaration
   977	        # of it. Regenerating a required view is correct; resurrecting an un-adopted one is not.
   978	        if os.path.exists(os.path.join(repo_root, "RELEASES-PREVIEW.html")):
   979	            steps.append(("export_timeline.py --preview", timeline_cmd))
   980	        else:
   981	            log("  (skipping export_timeline.py --preview — RELEASES-PREVIEW.html is not adopted here)")
   982	        steps.extend(
   983	            [
   984	                ("roadmap-dashboard.sh", dash_cmd),
   985	                ("marathon-plan.sh", plan_cmd),
   986	            ]
   987	        )
   988	    else:
   989	        steps.append(("marathon-plan.sh --dry-run", plan_cmd))
   990	
   991	    # GH-271: registration of created views/plan docs must happen even when a step DIES —
   992	    # the marathon-plan failure path raises from inside the loop, and a post-loop pass
   993	    # would never run, which is exactly how the stray MARATHON-PLAN escaped rollback.
   994	    try:
   995	        for name, cmd in steps:
   996	            log(f"  -> {name}")
   997	            # GH-429: roadmap-dashboard.sh derives ROOT from its own location and lands on <repo>/.xyz
   998	            # when vendored (#215 item 2); it honours this override, and the reconciler already knows
   999	            # the repo root. Harmless for the other steps, which ignore the variable.
  1000	            step_env = dict(os.environ, ROADMAP_DASHBOARD_ROOT=str(repo_root))
  1001	            r = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False, env=step_env)
  1002	            if name.startswith("marathon-plan"):
  1003	                handle_marathon_plan_result(r, reconciled_issues or set())
  1004	            elif r.returncode != 0:
  1005	                die(f"Subprocess '{name}' failed with exit {r.returncode}:\n{r.stderr}\n{r.stdout}", code=6)
  1006	    finally:
  1007	        if journal and not dry_run:
  1008	            for plan_doc in _plan_docs() - pre_plan_docs:
  1009	                journal.track_created(plan_doc)
  1010	
  1011	
  1012	def run_validation_gate(repo_root):
  1013	    """Run pdda doc-health verification gate."""
  1014	    log("Running PDDA doc-hygiene gate...")
  1015	    gate_cmd = ["bash", "utils/pdda-local-checks.sh"] if os.path.exists(os.path.join(repo_root, "utils", "pdda-local-checks.sh")) else ["bash", "utils/pdda/pdda.sh"]
  1016	    r = subprocess.run(
  1017	        gate_cmd,
  1018	        cwd=repo_root,
  1019	        capture_output=True,
  1020	        text=True,
  1021	        check=False,
  1022	    )
  1023	    # GH-429: the exit status IS the consuming repo's enforcement decision — pdda-lib.sh makes
  1024	    # `observe`/`light` exit 0 and `full` exit non-zero on errors. Grepping stdout for ERROR
  1025	    # overrode that mode and made a live reconciliation impossible on any repo with a standing
  1026	    # observe-mode backlog. Block on the status; surface the findings when it reports but passes.
  1027	    if r.returncode != 0:
  1028	        die(f"PDDA validation gate failed:\n{r.stdout}", code=7)
  1029	    if "ERROR" in r.stdout:
  1030	        found = re.search(r"(\d+) error\(s\) found", r.stdout)
  1031	        count = found.group(1) if found else "some"
  1032	        log(f"  WARNING — pdda reported {count} finding(s) but exited 0 (repo enforcement mode is not blocking); continuing")
  1033	
  1034	
  1035	def main():
  1036	    parser = argparse.ArgumentParser(
  1037	        description="wave_reconcile.py — Canonical Post-Merge Wave & Marathon Lifecycle Reconciler"
  1038	    )
  1039	    parser.add_argument(
  1040	        "--root",
  1041	        help="Target repository root path (default: current working directory)",
  1042	    )
  1043	    parser.add_argument(
  1044	        "--pr",
  1045	        nargs="+",
  1046	        help="One or more merged PR numbers/IDs to reconcile",
  1047	    )
  1048	    parser.add_argument(
  1049	        "--commit",
  1050	        nargs="+",
  1051	        help="One or more commits landed directly on development to reconcile",
  1052	    )
  1053	    parser.add_argument(
  1054	        "--marathon",
  1055	        help="Marathon identifier / milestone name",
  1056	    )
  1057	    parser.add_argument(
  1058	        "--manifest",
  1059	        help="Path to structured JSON reconciliation manifest",
  1060	    )
  1061	    parser.add_argument(
  1062	        "--dry-run",
  1063	        action="store_true",
  1064	        help="Hermetic preview: assert zero file/DB/ref mutations",
  1065	    )
  1066	    parser.add_argument(
  1067	        "--offline",
  1068	        help="Run without network using offline JSON manifest cache",
  1069	    )
  1070	    parser.add_argument(
  1071	        "--skip-pull",
  1072	        action="store_true",
  1073	        help="Skip git pull --ff-only origin development (for testing/isolated clones)",
  1074	    )
  1075	    parser.add_argument(
  1076	        "--skip-branch-check",
  1077	        action="store_true",
  1078	        help="Skip active branch check (for tests on feature branches)",
  1079	    )
  1080	    parser.add_argument(
  1081	        "--allow-dirty",
  1082	        action="store_true",
  1083	        help="Allow dirty working tree (for test fixtures only)",
  1084	    )
  1085	    parser.add_argument(
  1086	        "--force-promote",
  1087	        action="store_true",
  1088	        help="Force promotion of active docs and roadmap entries to Completed regardless of linked issue OPEN state",
  1089	    )
  1090	    parser.add_argument(
  1091	        "--gate",
  1092	        "--require-receipts",
  1093	        action="store_true",
  1094	        dest="require_receipts",
  1095	        help="Require a receipt matching each PR number or exact merge commit before closeout (GH-425)",
  1096	    )
  1097	
  1098	    parser.add_argument("--catch-up", action="store_true", help="Recover closed-issue drift from committed docs and manifest")
  1099	
  1100	    args = parser.parse_args()
  1100	    args = parser.parse_args()
  1101	
  1102	    repo_root = os.path.abspath(args.root) if args.root else resolve_repo_root()
  1103	    lock_file = os.path.join(repo_root, ".git", "wave-reconcile.lock")
  1104	    journal = RollbackJournal()
  1105	    baseline = None
  1106	
  1107	    try:
  1108	        # Preflight phase
  1109	        log(f"Starting wave reconciliation (dry_run={args.dry_run}, root={repo_root})")
  1110	        baseline = check_porcelain_cleanliness(repo_root, allow_dirty=(args.allow_dirty or args.dry_run))
  1111	        check_current_branch(repo_root, skip_branch_check=args.skip_branch_check)
  1112	
  1113	        if not args.skip_pull and not args.dry_run and not args.offline:
  1114	            pull_upstream(repo_root)
  1115	
  1116	        offline_manifest = None
  1117	        if args.offline:
  1118	            try:
  1119	                with open(args.offline, "r", encoding="utf-8") as f:
  1120	                    offline_manifest = json.load(f)
  1121	            except Exception as e:
  1122	                die(f"Failed loading offline manifest from {args.offline}: {e}", code=4)
  1123	
  1124	        landing_items = [("pr", value) for value in (args.pr or [])]
  1125	        landing_items.extend(("commit", value) for value in (args.commit or []))
  1126	        if args.manifest:
  1127	            try:
  1128	                with open(args.manifest, "r", encoding="utf-8") as f:
  1129	                    mdata = json.load(f)
  1130	                    landing_items.extend(("pr", str(p)) for p in mdata.get("prs", []))
  1131	            except Exception as e:
  1132	                die(f"Failed loading manifest from {args.manifest}: {e}", code=4)
  1133	
  1134	        if not landing_items and not args.marathon and not args.catch_up:
  1135	            die("No PRs, commits, or marathon specified. Pass --pr <N>..., --commit <SHA>..., --marathon <name>, or --catch-up", code=2)
  1136	
  1137	        with ReconcilerLock(lock_file):
  1138	            reconciled_issues = set()
  1139	            repo_slug = github_slug_from_origin(repo_root)  # GH-429: URL-form closers, this repo only
  1140	            if args.catch_up:
  1141	                landing_items.extend(("pr", str(n)) for n in catch_up_prs(repo_root, repo_slug, offline_manifest))
  1142	            landing_items = list(dict.fromkeys((kind, str(value)) for kind, value in landing_items))
  1143	            for landing_kind, landing_id in landing_items:
  1144	                if landing_kind == "commit":
  1145	                    pr_meta = fetch_commit_metadata(repo_root, landing_id, offline_manifest)
  1146	                else:
  1147	                    pr_meta = fetch_pr_metadata(repo_root, landing_id, offline_manifest, dry_run=args.dry_run)
  1148	                landing = landing_label(pr_meta)
  1149	                log(f"Processing {landing}...")
  1150	                state = pr_meta.get("state", "").upper()
  1151	                is_merged = (state == "MERGED")
  1152	
  1153	                if not is_merged:
  1154	                    log(f"  {landing} state is '{state}' (unmerged/declined) -> routing to 4-MISC/")
  1155	
  1156	                base_ref = pr_meta.get("baseRefName", "")
  1157	                if base_ref and base_ref != "development":
  1158	                    die(
  1159	                        f"{landing} target base is '{base_ref}', not 'development'.",
  1160	                        code=4,
  1161	                    )
  1162	
  1163	                linked_issues, mentioned_issues = extract_linked_issues(pr_meta, repo_slug=repo_slug)
  1164	                # GH-425: unconditional whenever --gate/--require-receipts is requested — this
  1165	                # attributes evidence to the PR itself, not to whichever issue it happens to
  1166	                # close. Narrowing this to "only if the PR closes/references a tracked issue"
  1167	                # (introduced in GH-421's build) silently drops the guarantee for exactly the
  1168	                # PRs least likely to be scrutinized: ones with no linked issue at all.
  1169	                if args.require_receipts:
  1170	                    check_provenance_receipts(repo_root, pr_meta)
  1171	                reconciled_issues.update(linked_issues)
  1172	                log(f"  {landing} closes {linked_issues}; references {mentioned_issues}")
  1173	                # GH-271: mentions never act on their own. --force-promote is the one
  1174	                # explicit operator override that widens the action set past closers.
  1175	                action_issues = (
  1176	                    sorted(set(linked_issues) | set(mentioned_issues))
  1177	                    if args.force_promote
  1178	                    else linked_issues
  1179	                )
  1180	
  1181	                for issue_num in action_issues:
  1182	                    doc_path = find_active_doc_for_issue(repo_root, issue_num)
  1183	                    issue_state = fetch_issue_state(repo_root, issue_num, offline_manifest)
  1184	                    fm = parse_doc_frontmatter(doc_path) if doc_path else {}
  1185	                    is_multiphase = (
  1186	                        fm.get("umbrella") in ("true", "1", "yes")
  1187	                        or fm.get("multiphase") in ("true", "1", "yes")
  1188	                        or fm.get("multi_phase") in ("true", "1", "yes")
  1189	                    )
  1190	
  1191	                    is_open = (issue_state == "OPEN") or (issue_state is None and is_multiphase)
  1192	
  1193	                    if doc_path and is_open and is_merged and not args.force_promote:
  1194	                        # GH-202/GH-232: a merged PR does not complete an open issue or multi-phase umbrella.
  1195	                        # Phased umbrellas and open issues keep their active doc; evidence recorded in place.
  1196	                        log(f"  Issue #{issue_num} is OPEN — keeping {os.path.basename(doc_path)} active; recording merge evidence")
  1197	                        record_merge_evidence(doc_path, pr_meta, dry_run=args.dry_run, journal=journal)
  1198	                        log(f"  Issue #{issue_num} is OPEN — preserving active ROADMAP.md entry (skipping move to Completed)")
  1199	                    elif doc_path:
  1200	                        if is_merged:
  1201	                            ship_manifest_items(repo_root, issue_num, pr_meta, repo_slug, args.dry_run, journal)
  1202	                        log(f"  Found active doc: {os.path.basename(doc_path)}")
  1203	                        dest_path, ship_date = validate_and_update_doc(
  1204	                            doc_path, pr_meta, is_merged=is_merged, dry_run=args.dry_run, journal=journal
  1205	                        )
  1206	                        log(f"  Moved -> {os.path.basename(dest_path)} (destination: {os.path.basename(os.path.dirname(dest_path))})")
  1207	                        updated = update_roadmap_entry(
  1208	                            repo_root,
  1209	                            issue_num,
  1210	                            landing,
  1211	                            ship_date,
  1212	                            is_merged=is_merged,
  1213	                            dry_run=args.dry_run,
  1214	                            journal=journal,
  1215	                            doc_path=os.path.relpath(dest_path, repo_root),
  1216	                        )
  1217	                        if updated:
  1218	                            log(f"  ROADMAP.md entry updated for GH-{issue_num}")
  1219	                    else:
  1220	                        log(f"  No active doc in 2-WORKING for GH-{issue_num}")
  1221	                        ship_date = (pr_meta.get("mergedAt") or datetime.now().isoformat())[:10]
  1222	                        if not is_open or args.force_promote:
  1223	                            if is_merged:
  1224	                                ship_manifest_items(repo_root, issue_num, pr_meta, repo_slug, args.dry_run, journal)
  1225	                            updated = update_roadmap_entry(
  1226	                                repo_root,
  1227	                                issue_num,
  1228	                                landing,
  1229	                                ship_date,
  1230	                                is_merged=is_merged,
  1231	                                dry_run=args.dry_run,
  1232	                                journal=journal,
  1233	                            )
  1234	                            if updated:
  1235	                                log(f"  ROADMAP.md entry updated for GH-{issue_num}")
  1236	                        else:
  1237	                            log(f"  Issue #{issue_num} is OPEN — preserving active ROADMAP.md entry (skipping move to Completed)")
  1238	
  1239	                # GH-271: reference-only mentions never promote or move anything. When the
  1240	                # mentioned issue is OPEN (or an unknowable-state umbrella), record merge
  1241	                # evidence on its active doc — the "Advances GH-N (phase k of n)" convention
  1242	                # GH-202/GH-232 pin — and nothing else. Issues already handled above (the
  1243	                # force-promote widening) are skipped.
  1244	                for issue_num in mentioned_issues:
  1245	                    if issue_num in action_issues:
  1246	                        continue
  1247	                    doc_path = find_active_doc_for_issue(repo_root, issue_num)
  1248	                    if not doc_path:
  1249	                        continue
  1250	                    issue_state = fetch_issue_state(repo_root, issue_num, offline_manifest)
  1251	                    fm = parse_doc_frontmatter(doc_path)
  1252	                    is_multiphase = (
  1253	                        fm.get("umbrella") in ("true", "1", "yes")
  1254	                        or fm.get("multiphase") in ("true", "1", "yes")
  1255	                        or fm.get("multi_phase") in ("true", "1", "yes")
  1256	                    )
  1257	                    is_open = (issue_state == "OPEN") or (issue_state is None and is_multiphase)
  1258	                    if is_open and is_merged:
  1259	                        log(f"  Issue #{issue_num} referenced without a closing keyword and OPEN — recording merge evidence only")
  1260	                        record_merge_evidence(doc_path, pr_meta, dry_run=args.dry_run, journal=journal)
  1261	
  1262	            # Global roadmap cleanups
  1263	            fix_mangled_roadmap_entries(repo_root, dry_run=args.dry_run, journal=journal)
  1264	
  1265	            # GH-421: skip downstream regeneration only when there was genuinely nothing to
  1266	            # act on this run (catch-up mode found no new PRs, and no --pr/--marathon target
  1267	            # was given) — the scheduled cron trigger's common case. NOT when a real PR or
  1268	            # marathon lane was processed but happened not to move a doc: run_subprocesses does
  1269	            # independent, valuable work every time (release-timeline export incl. the GH-474
  1270	            # preview refresh, releases check, the PDDA gate) that existing suites (gh202,
  1271	            # gh425, gh454) already pin as running on every real post-merge invocation,
  1272	            # regardless of doc lifecycle outcome. Byte-identical output on a genuine repeat
  1273	            # (issue #421's actual idempotency requirement) is satisfied by these regenerators
  1274	            # already being deterministic, not by skipping them.
  1275	            if not args.dry_run and not landing_items and not args.marathon:
  1276	                log("Nothing to reconcile; no artifacts written")
  1277	                journal.cleanup()
  1278	                return
  1279	
  1280	            # Subprocess orchestration
  1281	            run_subprocesses(
  1282	                repo_root,
  1283	                dry_run=args.dry_run,
  1284	                journal=journal,
  1285	                reconciled_issues=reconciled_issues,
  1286	            )
  1287	
  1288	            # Final validation gate
  1289	            if not args.dry_run:
  1290	                run_validation_gate(repo_root)
  1291	
  1292	            log("Wave reconciliation completed successfully! ✅")
  1293	            journal.cleanup()
  1294	
  1295	    except ReconcileError as re_err:
  1296	        journal.rollback()
  1297	        verify_rollback_completeness(repo_root, baseline)
  1298	        sys.exit(re_err.code)
  1299	    except (Exception, SystemExit) as exc:
  1300	        journal.rollback()
  1301	        verify_rollback_completeness(repo_root, baseline)
  1302	        raise exc
  1303	
  1304	
  1305	if __name__ == "__main__":
  1306	    main()
     1	#!/usr/bin/env bash
     2	# utils/roadmap-dashboard.sh — render a read-only dashboard from ROADMAP.md (GH-27).
     3	
     4	set -euo pipefail
     5	
     6	HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
     7	# GH-272: releases-merge-resolve.sh drives this renderer against a --root TARGET repo —
     8	# the ledger it renders and the dashboard it writes must follow the target, not this
     9	# script's own checkout. Self-location stays the default for every other caller.
    10	ROOT="${ROADMAP_DASHBOARD_ROOT:-$(cd "$HERE/.." && pwd)}"
    11	SOURCE_FILE="${ROADMAP_DASHBOARD_SOURCE:-"$ROOT/ROADMAP.md"}"
    12	OUTPUT_FILE="${ROADMAP_DASHBOARD_OUTPUT:-"$ROOT/ROADMAP-DASHBOARD.md"}"
    13	
    14	usage() {
    15	  cat <<'EOF'
    16	Usage: bash utils/roadmap-dashboard.sh [--check]
    17	
    18	  Default: render ROADMAP-DASHBOARD.md from the canonical root ROADMAP.md.
    19	  --check: exit 0 when ROADMAP-DASHBOARD.md is in sync; non-zero on drift.
    20	EOF
    21	}
    22	
    23	MODE="write"
    24	if (($# > 1)); then
    25	  usage
    26	  exit 2
    27	fi
    28	if (($# == 1)); then
    29	  case "$1" in
    30	    --check) MODE="check" ;;
    31	    --help|-h) usage; exit 0 ;;
    32	    *) usage; exit 2 ;;
    33	  esac
    34	fi
    35	
    36	command -v node >/dev/null 2>&1 || {
    37	  echo "roadmap-dashboard: node is required" >&2
    38	  exit 2
    39	}
    40	
    41	TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/roadmap-dashboard.XXXXXX")"
    42	trap 'rm -rf "$TMP_DIR"' EXIT
    43	RENDERED="$TMP_DIR/ROADMAP-DASHBOARD.md"
    44	
    45	# GH-243: in a releases-mode repo the DB is the roadmap's source of truth and ROADMAP.md is
    46	# frozen — render from `roadmap list --json` (each row's lossless raw_text under its section)
    47	# instead of the legacy file. An explicit ROADMAP_DASHBOARD_SOURCE still wins (test seam), and
    48	# any failure here falls back to the legacy file rather than emitting an empty dashboard.
    49	if [ -z "${ROADMAP_DASHBOARD_SOURCE:-}" ] \
    50	   && (grep -q "ROADMAP_SOURCE=releases" "$ROOT/.pdda-mode" 2>/dev/null || [ ! -f "$ROOT/ROADMAP.md" ]) \
    51	   && [ -f "$ROOT/releases.db" ] && command -v python3 >/dev/null 2>&1; then
    52	  DB_SRC="$TMP_DIR/roadmap-from-db.md"
    53	  DB_JSON="$TMP_DIR/roadmap-rows.json"
    54	  # JSON goes through a temp file passed as argv — `python3 -` takes its PROGRAM from the
    55	  # heredoc on stdin, so piping data in as well would feed the parser nothing (the PR #240
    56	  # rollup.sh bug, same shape). The APP resolves from HERE (this script's own checkout) while
    57	  # --root follows $ROOT: under ROADMAP_DASHBOARD_ROOT (GH-272) the target repo may ship the
    58	  # ledger without a utils/ tree at all.
    59	  if python3 "$HERE/py/releases_app.py" --root "$ROOT" roadmap list --json > "$DB_JSON" 2>/dev/null \
    60	     && python3 - "$DB_JSON" > "$DB_SRC" <<'PY'
    61	import json, sys
    62	with open(sys.argv[1]) as f:
    63	    rows = json.load(f)
    64	print("# ROADMAP (rendered from the RELEASES DB — GH-243; ROADMAP.md is frozen legacy)\n")
    65	print("## Ledger\n")   # the renderer only counts sections below this heading
    66	sections = {}
    67	for r in rows:
    68	    sections.setdefault(r.get("section") or "(unsectioned)", []).append(r)
    69	for section, items in sections.items():
    70	    print(f"### {section}\n")
    71	    for r in sorted(items, key=lambda x: x.get("position") or 0):
    72	        line = (r.get("raw_text") or "").strip()
    73	        if not line:
    74	            gh = f"GH-{r['gh_number']} · " if r.get("gh_number") is not None else ""
    75	            line = f"- **{gh}{r.get('title', '')}**"
    76	        print(line)
    77	    print()
    78	PY
    79	  then
    80	    [ -s "$DB_SRC" ] && SOURCE_FILE="$DB_SRC"
    81	  fi
    82	fi
    83	
    84	if [ ! -f "$SOURCE_FILE" ]; then
    85	  echo "roadmap-dashboard: source not found: $SOURCE_FILE" >&2
    86	  exit 3
    87	fi
    88	
    89	# Resolve from HERE, not ROOT: a target ledger need not ship its own utils/ tree.
    90	# Failure must stop rendering rather than fall back to a second, drifting vocabulary.
    91	LEDGER_SECTIONS_JSON="$(python3 "$HERE/py/releases_app.py" roadmap sections --json)"
    92	node - "$SOURCE_FILE" "$LEDGER_SECTIONS_JSON" >"$RENDERED" <<'NODE'
    93	const fs = require("fs");
    94	
    95	const sourcePath = process.argv[2];
    96	const raw = fs.readFileSync(sourcePath, "utf8");
    97	const lines = raw.split(/\r?\n/);
    98	
    99	const banner = "<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit ROADMAP.md -->";
   100	const ledgerSections = JSON.parse(process.argv[3]);
   101	const knownStatuses = ["🟢", "🟡", "⏸️", "⛔", "✅", "🔮", "🔲"];
   102	const extraStatuses = ["⚠️"];
   103	
   104	function escapeCell(value) {
   105	  return String(value)
   106	    .replace(/\|/g, "\\|")
   107	    .replace(/</g, "&lt;")
   108	    .replace(/>/g, "&gt;");
   109	}
   110	
   111	function stripMarkdown(value) {
   112	  return value
   113	    .replace(/`([^`]+)`/g, "$1")
   114	    .replace(/\*\*([^*]+)\*\*/g, "$1")
   115	    .replace(/\*([^*]+)\*/g, "$1")
   116	    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
   117	    .trim();
   118	}
   119	
   120	function parseBullet(block) {
   121	  const text = block.map((line) => line.trim()).join(" ").replace(/\s+/g, " ").trim();
   122	  const titleMatch = text.match(/^- \*\*(.+?)\*\*/);
   123	  const title = titleMatch ? stripMarkdown(titleMatch[1]) : stripMarkdown(text.replace(/^- /, ""));
   124	
   125	  let status = "—";
   126	  for (const emoji of knownStatuses.concat(extraStatuses)) {
   127	    if (text.includes(emoji)) {
   128	      status = emoji;
   129	      break;
   130	    }
   131	  }
   132	
   133	  const links = [];
   134	  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
   135	  let match;
   136	  while ((match = linkPattern.exec(text)) !== null) {
   137	    links.push(`[${match[1]}](${match[2]})`);
   138	  }
   139	
   140	  return { title, status, links };
   141	}
   142	
   143	function formatTally(items) {
   144	  const counts = new Map();
   145	  for (const emoji of knownStatuses) counts.set(emoji, 0);
   146	  const extras = [];
   147	
   148	  for (const item of items) {
   149	    if (counts.has(item.status)) {
   150	      counts.set(item.status, counts.get(item.status) + 1);
   151	      continue;
   152	    }
   153	    if (item.status !== "—") {
   154	      if (!counts.has(item.status)) extras.push(item.status);
   155	      counts.set(item.status, (counts.get(item.status) || 0) + 1);
   156	    }
   157	  }
   158	
   159	  const ordered = knownStatuses.slice();
   160	  for (const emoji of extras) {
   161	    if (!ordered.includes(emoji)) ordered.push(emoji);
   162	  }
   163	
   164	  return ordered.map((emoji) => `${emoji} ${counts.get(emoji) || 0}`).join(" · ");
   165	}
   166	
   167	const sections = new Map();
   168	for (const heading of ledgerSections) sections.set(heading, []);
   169	
   170	let inLedger = false;
   171	let currentSection = null;
   172	let unknownSection = null;
   173	const droppedRows = [];
   174	// GH-474: rows under a heading this renderer does not recognise. They parse fine — they are
   175	// simply never rendered, because `sections` has no bucket for their heading. That makes them
   176	// INVISIBLE in the view while the ledger still carries them, and invisible without a byte
   177	// difference: the row was never in the output, so a fresh render still matches the committed
   178	// file. `releases roadmap update/move --section` writes the section verbatim with no
   179	// validation (utils/py/releases_app.py), so one typo is all it takes.
   180	const unknownSectionRows = [];
     1	#!/usr/bin/env bash
     2	# utils/leaderboard.sh — render LEADERBOARD.md, the ranked read of every rated task (GH-108).
     3	#
     4	# ONE SCORER, NEVER TWO. This script does NOT compute calc and does NOT apply the
     5	# override-wins-over-calc rule. It consumes `export_timeline.py --json` and sorts on the
     6	# `effectiveScore` the exporter already derived. A shell script re-deriving scores would be the
     7	# exact drift class the "calc is never stored" rule exists to prevent, one layer up — the whole
     8	# job here is sort, rank, format.
     9	#
    10	# LEADERBOARD.md is GENERATED and never hand-edited, following the established
    11	# ROADMAP.md -> utils/roadmap-dashboard.sh -> ROADMAP-DASHBOARD.md pattern: committed so ranking
    12	# changes show up in diffs and review, greppable by agents that never open a browser, readable on
    13	# GitHub. Regeneration is idempotent — a stale checked-in copy is a review signal, not a hazard.
    14	
    15	set -euo pipefail
    16	
    17	HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    18	ROOT="$(cd "$HERE/.." && pwd)"
    19	DB="${LEADERBOARD_DB:-$ROOT/releases.db}"
    20	OUT="${LEADERBOARD_OUTPUT:-$ROOT/LEADERBOARD.md}"
    21	EXPORTER="$ROOT/utils/timeline/export_timeline.py"
    22	
    23	usage() {
    24	  cat <<'EOF'
    25	Usage: bash utils/leaderboard.sh [--check] [--top N]
    26	
    27	  Default: render LEADERBOARD.md from releases.db via export_timeline.py --json.
    28	  --check: write nothing; exit 0 when LEADERBOARD.md is already in sync, 1 on drift.
    29	  --top N: also print the top N to stdout (default: print nothing extra).
    30	
    31	Env: LEADERBOARD_DB, LEADERBOARD_OUTPUT.
    32	EOF
    33	}
    34	
    35	MODE="write"
    36	TOP=0
    37	while [ $# -gt 0 ]; do
    38	  case "$1" in
    39	    --check) MODE="check" ;;
    40	    --top) TOP="${2:-5}"; shift ;;
    41	    -h|--help) usage; exit 0 ;;
    42	    *) echo "leaderboard: unknown argument $1" >&2; usage >&2; exit 2 ;;
    43	  esac
    44	  shift
    45	done
    46	
    47	[ -f "$DB" ] || { echo "leaderboard: no releases DB at $DB" >&2; exit 2; }
    48	[ -f "$EXPORTER" ] || { echo "leaderboard: no exporter at $EXPORTER" >&2; exit 2; }
    49	
    50	# The payload goes through a FILE, not a pipe: `python3 - <<HEREDOC` already takes the script
    51	# from stdin, so a piped payload would arrive on an exhausted stream.
    52	PAYLOAD="$(mktemp "${TMPDIR:-/tmp}/leaderboard.XXXXXX.json")"
    53	trap 'rm -f "$PAYLOAD"' EXIT
    54	python3 "$EXPORTER" --db "$DB" --json > "$PAYLOAD"
    55	
    56	RENDERED="$(python3 - "$PAYLOAD" "$TOP" <<'PY'
    57	import json, sys
    58	
    59	payload = json.load(open(sys.argv[1]))
    60	top_n = int(sys.argv[2])
    61	
    62	# ratedTasks is the complete, already-ranked set the exporter emits: every rated roadmap row
    63	# once,
    64	# annotated with where it currently sits. Ranking off the release cards alone would silently omit
    65	# every rated task still in the queue — most of the candidates for "what goes to the front".
    66	rows = [{
    67	    "id": t["id"],
    68	    "title": t["title"],
    69	    "release": t["release"] or "—",
    70	    "lane": t["lane"],
    71	    "score": t["metrics"]["effectiveScore"],
    72	    "calc": t["metrics"]["calc"],
    73	    "override": (t.get("override") or {}).get("value"),
    74	    "axes": (t["metrics"]["pri"], t["metrics"]["sev"],
    75	             t["metrics"]["appeal"], t["metrics"]["effort"]),
    76	    "issue": (t.get("links") or {}).get("issue"),
    77	} for t in payload["ratedTasks"]]
    78	
    79	out = []
    80	w = out.append
    81	w("<!-- GENERATED by utils/leaderboard.sh from releases.db — do not hand-edit. -->")
    82	w("")
    83	w("# Leaderboard")
    84	w("")
    85	w("Every rated task in the ledger, highest first. **Higher is better on every axis**, effort")
    86	w("included — it scores cheapness, not cost, so a 90/90/90/90 item reads as what it is: a")
    87	w("screaming quick win. `calc` is the equal-weighted sum of the four axes (4–400) and is derived,")
    88	w("never stored. `ovr` is the operator override; where it exists it replaces `calc` for ranking,")
    89	w("while the four axes keep their honest values underneath.")
    90	w("")
    91	if not rows:
    92	    w("_No rated tasks yet. Add `rated N/N/N/N` to a ROADMAP.md entry and run "
    93	      "`releases roadmap sync`._")
    94	else:
    95	    w("| # | score | task | release | lane | pri | sev | appeal | effort | calc | ovr |")
    96	    w("|--:|------:|------|---------|------|----:|----:|-------:|-------:|-----:|----:|")
    97	    for i, r in enumerate(rows, 1):
    98	        title = r["title"].replace("|", "\\|")
    99	        label = "[%s](%s)" % (r["id"], r["issue"]) if r["issue"] else r["id"]
   100	        w("| %d | **%d** | %s — %s | %s | %s | %d | %d | %d | %d | %d | %s |"
   101	          % (i, r["score"], label, title, r["release"], r["lane"],
   102	             r["axes"][0], r["axes"][1], r["axes"][2], r["axes"][3], r["calc"],
   103	             str(r["override"]) if r["override"] is not None else "—"))
   104	    w("")
   105	    w("**Top of the line:** %s — %s (score %d%s)."
   106	      % (rows[0]["id"], rows[0]["title"], rows[0]["score"],
   107	         ", operator override" if rows[0]["override"] is not None else ""))
   108	w("")
   109	w("Source: `releases.db` via `export_timeline.py --json`. Regenerate with "
   110	  "`bash utils/leaderboard.sh`.")
   111	
   112	if top_n:
   113	    for r in rows[:top_n]:
   114	        print("%d\t%s\t%s" % (r["score"], r["id"], r["title"]), file=sys.stderr)
   115	print("\n".join(out))
   116	PY
   117	)"
   118	
   119	if [ "$MODE" = "check" ]; then
   120	  if [ -f "$OUT" ] && [ "$RENDERED" = "$(cat "$OUT")" ]; then
   121	    echo "leaderboard: $OUT is in sync"
   122	    exit 0
   123	  fi
   124	  echo "leaderboard: $OUT is stale — run 'bash utils/leaderboard.sh'" >&2
   125	  exit 1
   126	fi
   127	
   128	printf '%s\n' "$RENDERED" > "$OUT"
   129	echo "leaderboard: wrote $OUT"
  1230	    for line in text.splitlines():
  1231	        m = re.match(r"^-- generation: (\d+)$", line.strip())
  1232	        if m:
  1233	            return int(m.group(1))
  1234	    return None
  1235	
  1236	
  1237	# ── generation marker in the generated file ─────────────────────────────────────────────────────
  1238	# The side-by-side generated file carries the marker as an HTML comment on line 1 (the trio
  1239	# contract needs it there). The real RELEASES.md never carries one — this tool never writes that
  1240	# file, and no header is added during Phase 0 (the header arrives with the Phase 2 flip).
  1241	
  1242	GEN_MARKER_RE = re.compile(r"^<!-- releases-app generation: (\d+) -->$")
  1243	
  1244	
  1245	def gen_marker(generation):
  1246	    return "<!-- releases-app generation: %d -->" % generation
  1247	
  1248	
  1249	# ── staged writes + crash injection ─────────────────────────────────────────────────────────────
  1250	
  1251	def _crash(boundary):
  1252	    if os.environ.get("RELEASES_APP_CRASH_AT", "") == boundary:
  1253	        sys.stdout.flush()
  1254	        sys.stderr.flush()
  1255	        os._exit(EXIT_CRASH_INJECTED)
  1256	
  1257	
  1258	def _stage_write(final_path, content):
  1259	    """Staged temp-name write; the caller renames (atomic) only once the DB commit is durable."""
  1260	    tmp = "%s.tmp-%s" % (final_path, new_txn_id()[:12])
  1261	    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
  1262	        fh.write(content)
  1263	        fh.flush()
  1264	        os.fsync(fh.fileno())
  1265	    return tmp
  1266	
  1267	
  1268	def _atomic_write(final_path, content):
  1269	    tmp = _stage_write(final_path, content)
  1270	    os.replace(tmp, final_path)
  1271	
  1272	
  1273	# ── the writer protocol (PRD Git story 2-3): journal -> txn -> stage -> rename -> clear ─────────
  1274	
  1275	def refresh_preview(root):
  1276	    """GH-106: after a successful write, refresh the baked viewer artifacts — but only the ones
  1277	    the repo has ADOPTED (the file already exists at root; presence is the opt-in signal, so
  1278	    fixtures and non-adopting repos are silent no-ops). Best-effort by design: the write is
  1279	    already durable with its receipt when this runs, so a refresh failure WARNS on stderr and
  1280	    never fails the operation. Success is silent (the exporter's stdout is captured).
  1281	
  1282	    GH-108 adds LEADERBOARD.html on the same terms — one template, two baked artifacts, both
  1283	    regenerated by the same hook so a ranking can never lag the ledger it ranks."""
  1284	    exporter = os.path.join(root, "utils", "timeline", "export_timeline.py")
  1285	    if not os.path.exists(exporter):
  1286	        return
  1287	    for name, flag in (("RELEASES-PREVIEW.html", "--preview"),
  1288	                       ("LEADERBOARD.html", "--leaderboard")):
  1289	        target = os.path.join(root, name)
  1290	        if not os.path.exists(target):
  1291	            continue
  1292	        try:
  1293	            r = subprocess.run([sys.executable, exporter, flag, target],
  1294	                               cwd=root, capture_output=True, text=True, timeout=60)
  1295	            if r.returncode != 0:
  1296	                print("warning: %s refresh failed (the write itself is committed): %s"
  1297	                      % (name, r.stderr.strip() or r.stdout.strip() or
  1298	                         "exit %d" % r.returncode), file=sys.stderr)
  1299	        except Exception as exc:  # never let a rendered artifact break a committed write
  1300	            print("warning: %s refresh failed (the write itself is committed): %s"
  1301	                  % (name, exc), file=sys.stderr)
  1302	    # LEADERBOARD.md rides the same adoption signal — generated, never hand-edited.
  1303	    board = os.path.join(root, "LEADERBOARD.md")
  1304	    script = os.path.join(root, "utils", "leaderboard.sh")
  1305	    if os.path.exists(board) and os.path.exists(script):
  1306	        try:
  1307	            r = subprocess.run(["bash", script], cwd=root, capture_output=True, text=True,
  1308	                               timeout=60)
  1309	            if r.returncode != 0:
  1310	                print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
  1311	                      % (r.stderr.strip() or "exit %d" % r.returncode), file=sys.stderr)
  1312	        except Exception as exc:
  1313	            print("warning: LEADERBOARD.md refresh failed (the write itself is committed): %s"
  1314	                  % exc, file=sys.stderr)
  1315	
  1316	
  1317	def perform_write(root, conn, op, target_gid, mutate):
  1318	    """Run one CLI transaction under the full multi-artifact protocol:
  1319	
  1320	      write intent journal (txn_id, NEXT generation, planned outputs)   [BEFORE the DB commit]

exec
/bin/zsh -lc "rg -n \"After merging any PR|wave_reconcile|Lessons Learned|provenance.jsonl|test receipts|3-COMPLETED\" AGENTS.md SOP.md PROJECT/PDDA.md skills/merge-cleanup/SKILL.md ROUTER.md | head -n 180
nl -ba PROJECT/PDDA.md | sed -n '45,105p'
nl -ba SOP.md | sed -n '155,205p'
nl -ba skills/merge-cleanup/SKILL.md | sed -n '120,220p'
nl -ba ROADMAP-DASHBOARD.md | sed -n '1,12p'
nl -ba LEADERBOARD.md | sed -n '1,12p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
skills/merge-cleanup/SKILL.md:47:PR lands in, the tree `git merge --ff-only` runs in, and the tree `wave_reconcile.py`,
skills/merge-cleanup/SKILL.md:122:  - `python3 utils/py/wave_reconcile.py --pr <PR_NUM>`
SOP.md:241:3. **Batch reconciles.** The post-merge rule is "run `wave_reconcile.py --pr <N>` before
PROJECT/PDDA.md:34:- `PROJECT/3-COMPLETED`: completed docs with an outcome
PROJECT/PDDA.md:66:8. before moving to `PROJECT/3-COMPLETED`, a `## Lessons Learned (For Future Agents)` section appended to capture quirks and gotchas
PROJECT/PDDA.md:97:- **Scope:** `PROJECT/2-WORKING`, `PROJECT/1-INBOX/GH-*.md`, and `PROJECT/3-COMPLETED` (the last keeps a
PROJECT/PDDA.md:349:- scope: `PROJECT/2-WORKING` + `PROJECT/1-INBOX/GH-*.md` + `PROJECT/3-COMPLETED`; skip `quad_exempt: true`
PROJECT/PDDA.md:445:Scope: **both** `PROJECT/2-WORKING/` (active plans) and `PROJECT/3-COMPLETED/` (finished plans). The
PROJECT/PDDA.md:455:    `git mv` to `PROJECT/3-COMPLETED` (flag-only; a human runs the one reversible move)
PROJECT/PDDA.md:461:    by a self-contradictory status such as `Active — Phases 1-4 complete … Ready to close to 3-COMPLETED`:
PROJECT/PDDA.md:465:  - **(c)** doc is in `3-COMPLETED` but the issue is **OPEN** -> `warn`, recommending `gh issue close <n>`.
PROJECT/PDDA.md:466:    The lifecycle bucket is a deterministic signal; the status prose is not. `3-COMPLETED/` *is* the
PROJECT/PDDA.md:468:    A doc in `3-COMPLETED` with a **CLOSED** issue is the fully reconciled end state: no finding.
PROJECT/PDDA.md:525:    `PROJECT/3-COMPLETED/PDDA-SYNC-TO-OTHER-REPOS.md`), and the pre-`utils/pdda/` legacy layout path
AGENTS.md:54:After merging any PR into `development`, run `python3 utils/py/wave_reconcile.py --pr <N>` before
AGENTS.md:98:An uncommitted `provenance.jsonl` is not proof (GH-430). Any run cited as evidence in an issue, PR,
AGENTS.md:99:ROADMAP entry, or decision record must have its `provenance.jsonl` committed in the same PR — a path
AGENTS.md:304:  `PROJECT/3-COMPLETED/GH-177-MKTEMP-TRAP-REPO-WIPE.md`). Know what it does NOT protect: worktrees
AGENTS.md:378:    [GH-195-MARATHON-ROOT-AUDIT-BLIND-SPOT.md](PROJECT/3-COMPLETED/GH-195-MARATHON-ROOT-AUDIT-BLIND-SPOT.md).
ROUTER.md:171:- If the task is about the **Aider ↔ OpenRouter** turn-taker lane (`relay-automation/aider-turn.sh` — an OpenAI-standard build lane discrete from Codex; `AIDER_MODEL`/`OPENROUTER_API_KEY`, `--builder aider`), start in `PROJECT/3-COMPLETED/GH-77-AIDER-OPENROUTER-LANE.md`. The shim owns the tick token ops (Aider can't run shell mid-turn), asserts token ownership before launching Aider, and runs Aider `--no-auto-commits` (the harness commits).
ROUTER.md:176:- If the task is about cross-repo HQ tooling (`utils/hq/` — `hq.sh` single-repo actions, `rollup.sh` the Obsidian daily ROADMAP rollup, `marathon-scan.sh` the cross-repo marathon-preflight aggregator, `hq-lib.sh` the shared repo registry), start in `PROJECT/3-COMPLETED/GH-27-ROADMAP-DASHBOARD.md` and `PROJECT/3-COMPLETED/GH-158-HQ-MARATHON-SCAN.md`. The two rollups are deliberately separate today (`rollup.sh` → Obsidian, generic; `marathon-scan.sh` → hub repo, preflight-aware) and are not yet bridged — tracked in `PROJECT/1-INBOX/GH-192-HQ-MARATHON-OBSIDIAN-ROLLUP.md`.
    45	
    46	Every doc in `PROJECT/2-WORKING` should have:
    47	
    48	1. YAML frontmatter with at least `title`, `status`, `created`, `updated`, `owner`, and `goal`
    49	2. a near-top status table with the exact columns:
    50	
    51	```md
    52	## Status
    53	
    54	| What was just completed | What's next |
    55	|---|---|
    56	| ... | ... |
    57	```
    58	
    59	3. clear phase or work sections if the doc is a plan
    60	4. a table of contents (`## Table of contents`) listing each phase, if the plan is multi-phase — so a
    61	   cold agent can see the full phase span and jump to the live one without scrolling the whole body
    62	5. QA gates or acceptance criteria after each phase if the plan is multi-phase
    63	6. for any discovery or spike phase, its findings written **back into this doc** before its QA gate can
    64	   pass (see [Discovery & spike phases (Memory Injection)](#discovery--spike-phases-memory-injection))
    65	7. repo-relative paths only; no hardcoded absolute local paths
    66	8. before moving to `PROJECT/3-COMPLETED`, a `## Lessons Learned (For Future Agents)` section appended to capture quirks and gotchas
    67	
    68	Recommended fields when relevant:
    69	
    70	- `related`
    71	- `context_tags` (e.g. `[auth, flaky-tests, build]`)
    72	- `reviewed`
    73	- `branch`
    74	- `non_goals`
    75	- `gh_issue`
    76	- `effort`, `complexity`, `risk`, `phases` — triage ratings; **required for medium-large work** (see
    77	  [Triage ratings for medium-large work](#triage-ratings-for-medium-large-work))
    78	
    79	## Quad Concepts (opt-in)
    80	
    81	An **opt-in** glance layer, **off by default**. The `## Status` table says *where* the work is; Quad
    82	Concepts says *what* it is — a 5-second read of the core problems a plan tackles and how, so an operator
    83	can see whether the real pain points are covered. (Distinct from `context_tags`: those are for search;
    84	this is for glance.)
    85	
    86	When enabled system-wide via the `.pdda-quad` lever (or the `PDDA_QUAD` env var — **orthogonal** to the
    87	enforcement mode), tracked plan docs must carry a `## Quad Concepts` section of **1–4 bullets**,
    88	conventionally right after `## Status`:
    89	
    90	```md
    91	## Quad Concepts
    92	- <pain the doc addresses> → <how it addresses it>
    93	```
    94	
    95	- **Shape (deterministic):** 1–4 **top-level, non-empty** `-`/`*` bullets in the first `## Quad Concepts`
    96	  section. `pain → fix` phrasing is the convention (nudged by the LLM readiness rubric), not a hard regex.
    97	- **Scope:** `PROJECT/2-WORKING`, `PROJECT/1-INBOX/GH-*.md`, and `PROJECT/3-COMPLETED` (the last keeps a
    98	  glanceable summary for cold-start recall). `PROJECT/4-MISC` is out.
    99	- **Enable:** set `.pdda-quad` to `on` (or `PDDA_QUAD=1`). The enforcement mode still governs whether a
   100	  missing/malformed section merely reports or blocks. **Opt a doc out** with `quad_exempt: true`.
   101	- Enforced by `pdda.sh quad-concepts` (deterministic, structure-only) plus a warn-only readiness rubric.
   102	- `pdda.sh glance` (read-only, always available) rolls up `title + Quad Concepts` across `2-WORKING` for
   103	  a one-screen view of what the active portfolio is addressing.
   104	
   105	## Triage ratings for medium-large work
   155	### Never open a network path into the operator's machine without asking first
   156	
   157	A tunnel, a port forward, a remote bridge, an ngrok/cloudflared URL — anything that makes a local
   158	process reachable from outside the machine — **requires the operator's explicit permission each
   159	time.** It is not covered by "you may run the tests" or by a task that happens to involve the
   160	feature. Bridging in is a perfectly reasonable thing to want; the rule is that the operator decides,
   161	not the agent, because the agent cannot see who else is on the network or what else is on the disk.
   162	
   163	This was written after a mutation test removed a tunnel guard and stood up a real public URL to a
   164	local transcript store for about two minutes, unasked. The exposure was small and closed quickly.
   165	The reason it is a rule anyway is that nothing in the process would have stopped a larger one.
   166	
   167	### The guards read comments — an example in prose fails the scan just like real code
   168	
   169	`security-scan.sh` and `gh139-pipe-grep-guard.sh` are static text scans over the whole file. Writing
   170	the banned shape into a comment to *explain* it fails the guard exactly as writing it in code does.
   171	This happened four separate times in one session — a piped quiet grep, a credential-looking
   172	assignment, a shell-eval example, and a comment explaining one of the other three.
   173	
   174	Describe the shape in words rather than reproducing it, and run `security-scan.sh` plus
   175	`gh139-pipe-grep-guard.sh` locally **before** pushing new guard-adjacent shell. The full gate takes
   176	about nine minutes to tell you the same thing.
   177	
   178	### A test that starts a server must kill the server, not the shell that launched it
   179	
   180	Backgrounding `( ... ) &` and killing `$!` reaps the **subshell**. A `python3`/`node` child it
   181	spawned keeps running, keeps its port bound, and outlives the test — silently, because the suite
   182	already printed PASS and moved on. In the incident above this is exactly what left the bridge alive
   183	after its test finished; it was found in `ps`, not by the teardown.
   184	
   185	Kill the child by its own PID, or start it with `exec` so the subshell *becomes* the process. Then
   186	**verify** with `ps`/`lsof` rather than trusting the kill. A teardown that cannot fail is not a
   187	teardown — the same rule as `AGENTS.md` §6.
   188	
   189	## 4. Opinionated SOPs (XYZ-maintainer defaults — optional downstream)
   190	
   191	> **Who these are for:** These conventions exist to help the **XYZ maintainers** with our own
   192	> development flow on this repository. They are **not** part of the harness contract.
   193	> **Public users and downstream forks are free to disable them**, instruct their own LLM
   194	> maintainers to ignore them, or write a script that strips this section on pull from upstream.
   195	> Nothing in the codebase enforces them.
   196	
   197	- **The primary clone stays on `development`.** Each device has exactly one
   198	  **operator-designated primary clone** — the long-lived checkout the operator opens by default
   199	  and keeps mapped to GitHub. That clone is always kept on the `development` branch. This rule
   200	  applies **only** to the primary clone by role; task clones provisioned under the next rule are
   201	  exempt (they live on their own task branch and are disposable).
   202	- **Express-to-development is explicit; everything else gets a fresh full clone.** Direct
   203	  commit + push into `development` happens only when the user **explicitly asks** for an express
   204	  commit of critical work. In every other case, the LLM begins new work by provisioning a
   205	  **new local full-clone folder** — a full clone, *not* a git worktree (GH-564) — cloned from
   120	  fails after the PRs have already merged remotely.
   121	- Executes post-merge reconciliation:
   122	  - `python3 utils/py/wave_reconcile.py --pr <PR_NUM>`
   123	  - `python3 utils/py/releases_app.py gen && python3 utils/py/releases_app.py check`
   124	  - `bash utils/pdda/pdda.sh issue-doc-sync`
   125	
   126	### Phase 6: Safe Teardown
   127	- **Linked Worktrees:** Always removed via `git worktree remove <path>` from parent clone, followed by `git worktree prune` and `git worktree repair`. **Zero `rm -rf` on linked worktrees!**
   128	- **Standalone Clones:** Only deleted if verified 100% clean across Phase 2 & 3. Moved to Trash (`~/.Trash`) when available.
   129	- **Symlink Cleanup:** Prunes dangling skill symlinks in `~/.claude/skills/` and `~/.gemini/**/skills/`.
   130	
   131	---
   132	
   133	## CLI Usage
   134	
   135	Run scripts directly from the skill directory or via python:
   136	
   137	```bash
   138	# 1. Full Dry-Run Inspection (Default)
   139	python3 skills/merge-cleanup/scripts/merge_cleanup.py --prefix XYZ-forge
   140	
   141	# 2. Audit Only (Scan Clones and Worktrees)
   142	python3 skills/merge-cleanup/scripts/scan_clones.py --prefix XYZ-forge
   143	
   144	# 3. PR Topological Sequencing
   145	python3 skills/merge-cleanup/scripts/toposort_prs.py
   146	
   147	# 4. Execute Full Sequence (Merges, Reconciliation, and Teardown)
   148	python3 skills/merge-cleanup/scripts/merge_cleanup.py --prefix XYZ-forge --execute
   149	
   150	# 5. Teardown Only (Clean Clones/Worktrees without merging PRs)
   151	python3 skills/merge-cleanup/scripts/merge_cleanup.py --prefix XYZ-forge --teardown-only --execute
   152	
   153	# 6. Exclude Active In-Flight Work (e.g. PR 427)
   154	python3 skills/merge-cleanup/scripts/merge_cleanup.py --prefix XYZ-forge --exclude 427 --execute
   155	```
   156	
   157	---
   158	
   159	## Safety Guarantees
   160	
   161	1. **Zero Data Loss:** Any dirty working tree, unpopped stash, or unpushed commit automatically stops deletion and marks the checkout `PRESERVE_*`. The primary checkout is inspected first and by identity, so it can never be skipped by a scan filter.
   162	2. **No Blind Landing:** PR merges refuse to run while the primary checkout cannot fast-forward the integration branch.
   163	3. **Zero Process Interference:** Clones with active driver locks or running subagents are detected and preserved.
   164	4. **Canonical Worktree Protocol:** Linked worktrees are always cleanly deregistered from git metadata.
   165	5. **Governed Landing:** Every PR merge triggers deterministic wave reconciliation and doc sync.
     1	<!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit ROADMAP.md -->
     2	
     3	# ROADMAP Dashboard
     4	
     5	Read-only derived view of the root [ROADMAP.md](ROADMAP.md) ledger.
     6	
     7	## Queue / parked intake
     8	
     9	Summary: 50 items | Tally: 🟢 0 · 🟡 0 · ⏸️ 0 · ⛔ 0 · ✅ 0 · 🔮 0 · 🔲 0
    10	
    11	| Item | Status | Links |
    12	| --- | --- | --- |
     1	<!-- GENERATED by utils/leaderboard.sh from releases.db — do not hand-edit. -->
     2	
     3	# Leaderboard
     4	
     5	Every rated task in the ledger, highest first. **Higher is better on every axis**, effort
     6	included — it scores cheapness, not cost, so a 90/90/90/90 item reads as what it is: a
     7	screaming quick win. `calc` is the equal-weighted sum of the four axes (4–400) and is derived,
     8	never stored. `ovr` is the operator override; where it exists it replaces `calc` for ranking,
     9	while the four axes keep their honest values underneath.
    10	
    11	| # | score | task | release | lane | pri | sev | appeal | effort | calc | ovr |
    12	|--:|------:|------|---------|------|----:|----:|-------:|-------:|-----:|----:|

exec
/bin/zsh -lc "nl -ba utils/py/wave_reconcile.py | sed -n '1240,1295p'
nl -ba SOP.md | sed -n '232,252p'
nl -ba AGENTS.md | sed -n '48,58p;92,104p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-83325-4nan237k
 succeeded in 0ms:
  1240	                # mentioned issue is OPEN (or an unknowable-state umbrella), record merge
  1241	                # evidence on its active doc — the "Advances GH-N (phase k of n)" convention
  1242	                # GH-202/GH-232 pin — and nothing else. Issues already handled above (the
  1243	                # force-promote widening) are skipped.
  1244	                for issue_num in mentioned_issues:
  1245	                    if issue_num in action_issues:
  1246	                        continue
  1247	                    doc_path = find_active_doc_for_issue(repo_root, issue_num)
  1248	                    if not doc_path:
  1249	                        continue
  1250	                    issue_state = fetch_issue_state(repo_root, issue_num, offline_manifest)
  1251	                    fm = parse_doc_frontmatter(doc_path)
  1252	                    is_multiphase = (
  1253	                        fm.get("umbrella") in ("true", "1", "yes")
  1254	                        or fm.get("multiphase") in ("true", "1", "yes")
  1255	                        or fm.get("multi_phase") in ("true", "1", "yes")
  1256	                    )
  1257	                    is_open = (issue_state == "OPEN") or (issue_state is None and is_multiphase)
  1258	                    if is_open and is_merged:
  1259	                        log(f"  Issue #{issue_num} referenced without a closing keyword and OPEN — recording merge evidence only")
  1260	                        record_merge_evidence(doc_path, pr_meta, dry_run=args.dry_run, journal=journal)
  1261	
  1262	            # Global roadmap cleanups
  1263	            fix_mangled_roadmap_entries(repo_root, dry_run=args.dry_run, journal=journal)
  1264	
  1265	            # GH-421: skip downstream regeneration only when there was genuinely nothing to
  1266	            # act on this run (catch-up mode found no new PRs, and no --pr/--marathon target
  1267	            # was given) — the scheduled cron trigger's common case. NOT when a real PR or
  1268	            # marathon lane was processed but happened not to move a doc: run_subprocesses does
  1269	            # independent, valuable work every time (release-timeline export incl. the GH-474
  1270	            # preview refresh, releases check, the PDDA gate) that existing suites (gh202,
  1271	            # gh425, gh454) already pin as running on every real post-merge invocation,
  1272	            # regardless of doc lifecycle outcome. Byte-identical output on a genuine repeat
  1273	            # (issue #421's actual idempotency requirement) is satisfied by these regenerators
  1274	            # already being deterministic, not by skipping them.
  1275	            if not args.dry_run and not landing_items and not args.marathon:
  1276	                log("Nothing to reconcile; no artifacts written")
  1277	                journal.cleanup()
  1278	                return
  1279	
  1280	            # Subprocess orchestration
  1281	            run_subprocesses(
  1282	                repo_root,
  1283	                dry_run=args.dry_run,
  1284	                journal=journal,
  1285	                reconciled_issues=reconciled_issues,
  1286	            )
  1287	
  1288	            # Final validation gate
  1289	            if not args.dry_run:
  1290	                run_validation_gate(repo_root)
  1291	
  1292	            log("Wave reconciliation completed successfully! ✅")
  1293	            journal.cleanup()
  1294	
  1295	    except ReconcileError as re_err:
   232	   open the three issues you already know you will need: a *review-findings* lane (the
   233	   builder/reviewer split guarantees one), a *dogfood-findings* lane (dogfooding exists to
   234	   manufacture findings), and a *conformance* lane (new contracts always owe fixtures).
   235	   Follow-ups then arrive as scheduled phases instead of surprises. Evidence this works:
   236	   the GH-280 plan's follow-up record listed six items before execution began; all six
   237	   landed in that order, with review findings landed on top.
   238	2. **Batch same-seam scopes into one PR.** Five small PRs touching one seam is five
   239	   gate + merge + reconcile cycles for what is really one unit of review. GH-291 shipped
   240	   Scopes 1+5, 3+4, and 2 as three PRs; two would have carried the same review weight.
   241	3. **Batch reconciles.** The post-merge rule is "run `wave_reconcile.py --pr <N>` before
   242	   ending the task" — not "instantly, once per merge." Land 2–3 merges, then run one
   243	   reconcile pass for the batch. Each per-merge reconcile otherwise costs an extra
   244	   commit + gated push on `development`.
   245	4. **Never write bare `#N` for another repo's issues in a PR body.** The reconciler
   246	   resolves every `#N` against *this* repo and exits 6 when it cannot (GH-301 needed an
   247	   offline-manifest escape mid-reconcile). Cross-repo references are written `GH-N`;
   248	   in-repo references may use `#N`.
   249	5. **Delegate in this shape when lanes are independent:** each lane gets its own fresh
   250	   full clone and exactly one branch + one PR; it commits and pushes at every milestone
   251	   (the push gate is the boundary); it never merges its own PR. A single
   252	   orchestrator-reviewer holds merge duty, checks the three predicates (base branch,
    48	This file is the behavioral playbook for work in this repo: decision quality, reversibility, blast
    49	radius, planning shape, and proof.
    50	
    51	Do not restate routing, roadmap, changelog, or active-doc contracts here. Those live in
    52	`ROUTER.md` and `PROJECT/PDDA.md`.
    53	
    54	After merging any PR into `development`, run `python3 utils/py/wave_reconcile.py --pr <N>` before
    55	ending the task — the reconciler is single-command but nothing triggers it for you; `pdda.sh
    56	issue-doc-sync` is the deterministic drift detector when in doubt.
    57	
    58	Maintainer-only workflow defaults (branch discipline, express-to-development, fresh-clone-per-task)
    92	
    93	### 6. Verified beats plausible
    94	
    95	Do not claim success without the relevant test, script, or observable proof. If verification was
    96	skipped or failed, say that plainly and include the result.
    97	
    98	An uncommitted `provenance.jsonl` is not proof (GH-430). Any run cited as evidence in an issue, PR,
    99	ROADMAP entry, or decision record must have its `provenance.jsonl` committed in the same PR — a path
   100	you merely ran and can no longer show counts as no claim at all.
   101	
   102	**A check that cannot fail is not a check.** A passing assertion is evidence only once you have seen
   103	it fail: mutate the thing it guards — break the code, transpose the fix, delete the value — and watch
   104	it go red. If you cannot make it fail, it is decorative, and it is worse than nothing because it

codex
## ANSWER

**Block as written.** The direction is sound, but the plan does not yet guarantee a single reconciliation owner: `gh run list` is a non-atomic observation, so a local fallback can pass the check immediately before a hosted run starts. The view and pre-merge proposals also need tighter, deterministic contracts before implementation.

## FINDINGS

- [Blocker] **The in-flight lookup is advisory, not mutual exclusion.** GitHub Actions serializes hosted jobs via `concurrency.group: wave-reconcile` (`.github/workflows/wave-reconcile.yml:12-17`), while the Python lock is only clone-local (`utils/py/wave_reconcile.py:48-69`). A local process can observe no run and race a newly queued hosted run. Keep the existing fast-forward push as the ultimate safety boundary—the hosted writer already expects concurrent merges to reject its push and be recovered by catch-up (`.github/workflows/wave-reconcile.yml:90-94`)—but do not describe this as strict single-writer protection.

  Cheapest safe contract:

  1. Query the exact repository and workflow, requesting at least `queued`, `in_progress`, `waiting`, and `requested`; do not check only `in_progress`.
  2. Fail closed on missing `gh`, authentication failure, timeout, malformed JSON, or rate limiting.
  3. Recheck immediately before mutation and immediately before push.
  4. Provide a loud `--force-local-reconcile` override, rejected in `GITHUB_ACTIONS`, with the conflicting run IDs printed. Do not overload `--force-promote`.
  5. Document that the override accepts wasted/rejected work, not unsafe force-pushing.

  A stronger fallback is to dispatch the hosted workflow and let its concurrency group own serialization. Direct local writing should be the offline/emergency path.

- [Blocker] **`--pre-merge` cannot reuse the current post-merge receipt identity unchanged.** The existing receipt check accepts a PR number or the final 40-character merge commit and explicitly does **not** establish test success or committedness (`utils/py/wave_reconcile.py:342-399`). Before merge, the merge commit generally does not exist. Define pre-merge proof as a committed receipt in the candidate PR tree whose `commit` equals the current PR head SHA, whose result/status proves success, and whose command/suite meets the required gate. Read it from the Git object (`git show HEAD:path`/tree enumeration), not an untracked working-tree file. This matches the governance rule that uncommitted provenance is no proof (`AGENTS.md:98-100`).

- [Blocker] **Pre-merge discovery must be driven by the PR’s closing intent, not all files under `PROJECT/2-WORKING/`.** Validate only uniquely resolved docs for closing-keyword issues extracted from that PR, plus any doc move explicitly present in its diff. Otherwise unrelated active plans—or open multiphase umbrellas—will block the merge. The current resolver returns the first filename matching a permissive regex and depends on unsorted `os.listdir()` (`utils/py/wave_reconcile.py:476-487`); pre-merge must reject zero or multiple matches rather than choose nondeterministically.

- [Should] **Lessons Learned validation needs content, not heading presence.** Current closeout only searches for a heading (`utils/py/wave_reconcile.py:527-533`), so an empty section, HTML comment, template placeholder, or heading followed immediately by another `##` passes. Require at least one non-whitespace, non-comment, non-placeholder line before the next level-2 heading. Use exit 5 for the entire closeout-contract class and report every failing document in one run.

- [Should] **“Valid frontmatter” needs an explicit schema and a real parser.** The existing parser accepts loose colon-separated lines, does not verify a closing delimiter, silently returns `{}` on errors, and lowercases all values (`utils/py/wave_reconcile.py:490-508`). For pre-merge, require the PDDA fields `title`, `status`, `created`, `updated`, `owner`, and `goal` (`PROJECT/PDDA.md:46-49`), valid dates, exactly one closed YAML block at byte zero, and a status compatible with closing. Prefer the parser already used by PDDA validation so two validators cannot drift.

- [Should] **Classify legitimate view commits by causal renderer scope, not “any renderer source changed.”** Use per-view dependency allowlists:

  - `ROADMAP-DASHBOARD.md`: `utils/roadmap-dashboard.sh` plus the precise `releases_app.py` section/list contract it consumes.
  - `LEADERBOARD.md`: `utils/leaderboard.sh` plus `utils/timeline/export_timeline.py` and the relevant scoring/export contract.

  A task branch should pass when ledger semantics are valid and a clean head render succeeds, even if the committed view remains at the base version. It should fail if it commits either view unless:

  1. a dependency for that specific view changed;
  2. the committed bytes exactly equal a clean render from the candidate commit; and
  3. the renderer change actually changes the output relative to the base renderer for the same fixture/input.

  Do not let tests, comments, unrelated files under `utils/`, or merely touching a renderer file unlock both views. The present guard considers only ledger/dashboard path presence (`githooks/dashboard-staleness-guard.sh:104-113`) and currently instructs task branches to commit the dashboard (`githooks/dashboard-staleness-guard.sh:137-147`), so its policy and diagnostics both need replacement.

- [Should] **Preserve semantic corruption detection independently from view staging.** The current guard correctly catches renderer-reported dropped rows even when rendering produces no byte difference (`githooks/dashboard-staleness-guard.sh:149-190`). Keep that behavior. A clean render means “the view can be generated,” not “all ledger rows were represented.”

- [Should] **Use an HTML comment for generation stamping and share one parser/helper.** The cleanest backward-compatible form is:

  ```markdown
  <!-- releases-app generation: 123 -->
  <!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit the ledger through releases CLI. -->
  ```

  Put the generation marker on line 1 in both Markdown views. HTML comments do not alter rendered Markdown, and the repository already defines this exact syntax and regex (`utils/py/releases_app.py:1237-1246`). Read the value from the same read-only DB connection/snapshot used to obtain render data; do not query it separately after rendering. Update `--check` to compare both content and generation.

- [Should] **The roadmap header currently misstates its source.** It says to edit `ROADMAP.md` (`ROADMAP-DASHBOARD.md:1-5`), although releases-mode rendering reads `releases.db` and treats `ROADMAP.md` as frozen (`utils/roadmap-dashboard.sh:45-51`). Fix that in the same renderer change.

- [Should] **Skipping marathon generation needs a semantic input fingerprint.** The reconciler deliberately runs it for every real landing today (`utils/py/wave_reconcile.py:1265-1274`) and invokes it unconditionally in downstream work (`utils/py/wave_reconcile.py:960-987`). “Inputs unchanged” should mean a stable digest of only the planner’s canonical inputs/configuration and planner version—not filesystem mtimes, dashboard bytes, or DB generation, because unrelated receipt/settings writes can advance generation. Store the fingerprint in the generated plan or a committed reconciliation-owned marker, and test unchanged, relevant-change, and unrelated-ledger-change cases.

- [Should] **Governance must remove conflicting manual ownership language everywhere.** Current policy says reconciliation is not triggered automatically (`AGENTS.md:54-56`), recommends batching local reconciles (`SOP.md:241-244`), and merge cleanup directly runs local reconciliation (`skills/merge-cleanup/SKILL.md:120-124`). Replace these with “wait for and verify the hosted run for the landed SHA; invoke local fallback only under the documented failure/override contract.” Also define what merge cleanup does when the hosted job is queued, fails, or times out before clone teardown.

- [Pass] **Hosted writer mechanics are otherwise appropriately conservative.** It checks out fresh `development`, stages only declared artifacts, makes one non-force fast-forward push, and relies on scheduled/manual catch-up after rejection (`.github/workflows/wave-reconcile.yml:37-40,72-94`).

- [Pass] **Generation metadata belongs in these generated views.** Both files already begin with generated-file HTML comments (`ROADMAP-DASHBOARD.md:1`, `LEADERBOARD.md:1`), making a machine-readable comment marker minimally disruptive and backward compatible.

## RECOMMENDATION

**Revise before build: treat `gh run list` as fail-closed collision detection backed by fast-forward push—not a distributed lock—and specify causal view gating plus head-SHA, committed-success receipt validation for `--pre-merge`.**
tokens used
85,176
## ANSWER

**Block as written.** The direction is sound, but the plan does not yet guarantee a single reconciliation owner: `gh run list` is a non-atomic observation, so a local fallback can pass the check immediately before a hosted run starts. The view and pre-merge proposals also need tighter, deterministic contracts before implementation.

## FINDINGS

- [Blocker] **The in-flight lookup is advisory, not mutual exclusion.** GitHub Actions serializes hosted jobs via `concurrency.group: wave-reconcile` (`.github/workflows/wave-reconcile.yml:12-17`), while the Python lock is only clone-local (`utils/py/wave_reconcile.py:48-69`). A local process can observe no run and race a newly queued hosted run. Keep the existing fast-forward push as the ultimate safety boundary—the hosted writer already expects concurrent merges to reject its push and be recovered by catch-up (`.github/workflows/wave-reconcile.yml:90-94`)—but do not describe this as strict single-writer protection.

  Cheapest safe contract:

  1. Query the exact repository and workflow, requesting at least `queued`, `in_progress`, `waiting`, and `requested`; do not check only `in_progress`.
  2. Fail closed on missing `gh`, authentication failure, timeout, malformed JSON, or rate limiting.
  3. Recheck immediately before mutation and immediately before push.
  4. Provide a loud `--force-local-reconcile` override, rejected in `GITHUB_ACTIONS`, with the conflicting run IDs printed. Do not overload `--force-promote`.
  5. Document that the override accepts wasted/rejected work, not unsafe force-pushing.

  A stronger fallback is to dispatch the hosted workflow and let its concurrency group own serialization. Direct local writing should be the offline/emergency path.

- [Blocker] **`--pre-merge` cannot reuse the current post-merge receipt identity unchanged.** The existing receipt check accepts a PR number or the final 40-character merge commit and explicitly does **not** establish test success or committedness (`utils/py/wave_reconcile.py:342-399`). Before merge, the merge commit generally does not exist. Define pre-merge proof as a committed receipt in the candidate PR tree whose `commit` equals the current PR head SHA, whose result/status proves success, and whose command/suite meets the required gate. Read it from the Git object (`git show HEAD:path`/tree enumeration), not an untracked working-tree file. This matches the governance rule that uncommitted provenance is no proof (`AGENTS.md:98-100`).

- [Blocker] **Pre-merge discovery must be driven by the PR’s closing intent, not all files under `PROJECT/2-WORKING/`.** Validate only uniquely resolved docs for closing-keyword issues extracted from that PR, plus any doc move explicitly present in its diff. Otherwise unrelated active plans—or open multiphase umbrellas—will block the merge. The current resolver returns the first filename matching a permissive regex and depends on unsorted `os.listdir()` (`utils/py/wave_reconcile.py:476-487`); pre-merge must reject zero or multiple matches rather than choose nondeterministically.

- [Should] **Lessons Learned validation needs content, not heading presence.** Current closeout only searches for a heading (`utils/py/wave_reconcile.py:527-533`), so an empty section, HTML comment, template placeholder, or heading followed immediately by another `##` passes. Require at least one non-whitespace, non-comment, non-placeholder line before the next level-2 heading. Use exit 5 for the entire closeout-contract class and report every failing document in one run.

- [Should] **“Valid frontmatter” needs an explicit schema and a real parser.** The existing parser accepts loose colon-separated lines, does not verify a closing delimiter, silently returns `{}` on errors, and lowercases all values (`utils/py/wave_reconcile.py:490-508`). For pre-merge, require the PDDA fields `title`, `status`, `created`, `updated`, `owner`, and `goal` (`PROJECT/PDDA.md:46-49`), valid dates, exactly one closed YAML block at byte zero, and a status compatible with closing. Prefer the parser already used by PDDA validation so two validators cannot drift.

- [Should] **Classify legitimate view commits by causal renderer scope, not “any renderer source changed.”** Use per-view dependency allowlists:

  - `ROADMAP-DASHBOARD.md`: `utils/roadmap-dashboard.sh` plus the precise `releases_app.py` section/list contract it consumes.
  - `LEADERBOARD.md`: `utils/leaderboard.sh` plus `utils/timeline/export_timeline.py` and the relevant scoring/export contract.

  A task branch should pass when ledger semantics are valid and a clean head render succeeds, even if the committed view remains at the base version. It should fail if it commits either view unless:

  1. a dependency for that specific view changed;
  2. the committed bytes exactly equal a clean render from the candidate commit; and
  3. the renderer change actually changes the output relative to the base renderer for the same fixture/input.

  Do not let tests, comments, unrelated files under `utils/`, or merely touching a renderer file unlock both views. The present guard considers only ledger/dashboard path presence (`githooks/dashboard-staleness-guard.sh:104-113`) and currently instructs task branches to commit the dashboard (`githooks/dashboard-staleness-guard.sh:137-147`), so its policy and diagnostics both need replacement.

- [Should] **Preserve semantic corruption detection independently from view staging.** The current guard correctly catches renderer-reported dropped rows even when rendering produces no byte difference (`githooks/dashboard-staleness-guard.sh:149-190`). Keep that behavior. A clean render means “the view can be generated,” not “all ledger rows were represented.”

- [Should] **Use an HTML comment for generation stamping and share one parser/helper.** The cleanest backward-compatible form is:

  ```markdown
  <!-- releases-app generation: 123 -->
  <!-- GENERATED by utils/roadmap-dashboard.sh — DO NOT EDIT; edit the ledger through releases CLI. -->
  ```

  Put the generation marker on line 1 in both Markdown views. HTML comments do not alter rendered Markdown, and the repository already defines this exact syntax and regex (`utils/py/releases_app.py:1237-1246`). Read the value from the same read-only DB connection/snapshot used to obtain render data; do not query it separately after rendering. Update `--check` to compare both content and generation.

- [Should] **The roadmap header currently misstates its source.** It says to edit `ROADMAP.md` (`ROADMAP-DASHBOARD.md:1-5`), although releases-mode rendering reads `releases.db` and treats `ROADMAP.md` as frozen (`utils/roadmap-dashboard.sh:45-51`). Fix that in the same renderer change.

- [Should] **Skipping marathon generation needs a semantic input fingerprint.** The reconciler deliberately runs it for every real landing today (`utils/py/wave_reconcile.py:1265-1274`) and invokes it unconditionally in downstream work (`utils/py/wave_reconcile.py:960-987`). “Inputs unchanged” should mean a stable digest of only the planner’s canonical inputs/configuration and planner version—not filesystem mtimes, dashboard bytes, or DB generation, because unrelated receipt/settings writes can advance generation. Store the fingerprint in the generated plan or a committed reconciliation-owned marker, and test unchanged, relevant-change, and unrelated-ledger-change cases.

- [Should] **Governance must remove conflicting manual ownership language everywhere.** Current policy says reconciliation is not triggered automatically (`AGENTS.md:54-56`), recommends batching local reconciles (`SOP.md:241-244`), and merge cleanup directly runs local reconciliation (`skills/merge-cleanup/SKILL.md:120-124`). Replace these with “wait for and verify the hosted run for the landed SHA; invoke local fallback only under the documented failure/override contract.” Also define what merge cleanup does when the hosted job is queued, fails, or times out before clone teardown.

- [Pass] **Hosted writer mechanics are otherwise appropriately conservative.** It checks out fresh `development`, stages only declared artifacts, makes one non-force fast-forward push, and relies on scheduled/manual catch-up after rejection (`.github/workflows/wave-reconcile.yml:37-40,72-94`).

- [Pass] **Generation metadata belongs in these generated views.** Both files already begin with generated-file HTML comments (`ROADMAP-DASHBOARD.md:1`, `LEADERBOARD.md:1`), making a machine-readable comment marker minimally disruptive and backward compatible.

## RECOMMENDATION

**Revise before build: treat `gh run list` as fail-closed collision detection backed by fast-forward push—not a distributed lock—and specify causal view gating plus head-SHA, committed-success receipt validation for `--pre-merge`.**
