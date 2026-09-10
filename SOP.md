# Standard Operating Procedure (SOP): Testing Campaigns, Benchmarks, and Artifact Provenance

> **Scope & Relationship to `AGENTS.md`**:
> - **`GUIDING-PRINCIPLES.md` → "The North Star"** is the canonical source of truth for the durable / reversible / DRY bar and the "extend what exists, don't fork a parallel system" rule. Nothing here restates it.
> - **`AGENTS.md`** owns repo-wide behavioral governance, core principles (*Verified Beats Plausible*, blast radius sizing, reversibility scale), marathon load rails, role splits, and push boundary gates.
> - **`SOP.md` (this file)** is a specialized, tactical execution procedure specifically for **testing campaigns, ATE variation matrices, and benchmark telemetry provenance** (`TESTS-RESULTS/`).
> - **Overlap (~25%)**: This SOP references and enforces `AGENTS.md` invariants (standalone clone isolation GH-564, githooks/pre-push gates, and committed `.jsonl` telemetry GH-430) within its step-by-step campaign workflow rather than redefining general repository policy.
> - **Exception to this file's scope**: §4 "Opinionated SOPs" is a general **maintainer-workflow
>   appendix** (branch discipline, express-to-development, fresh-clone-per-task) — it governs all
>   maintainer development work, not just testing campaigns, and is optional for downstream users.

This document outlines the standard operating procedure for designing, executing, verifying, and committing evidence from automated testing campaigns, harness evaluations, and ATE variation matrices.

> Picking a skill to run a step of this SOP (e.g. a diagnostic pass before a campaign, or a relay
> to synthesize a fix)? See `ARCHITECTURE.md` → "Skills Index" for the full one-line inventory.

---

## 1. Governance & Principles

- **Verified Beats Plausible (Rule 6 / GH-430):** Any model grading, performance claim, or architecture recommendation must be backed by retained, committed telemetry (`error_log.jsonl` / `*.jsonl`) in `TESTS-RESULTS/`.
- **Full Clone Isolation (GH-564):** Never run destructive suites, resets, or multi-hour variation runs in the primary working tree or a linked worktree. Always provision a standalone clone (e.g. `../XYZ-forge-<topic>`).
- **Process Group Containment:** All spawned runners must use process-group session isolation (`setsid`) and PGID-targeted cleanup (`SIGTERM` -> `SIGKILL`) to prevent zombie child processes.
- **Auto-File Confirmed Defects:** When a campaign, probe, or soak produces a finding with a deterministic reproduction, the agent **files the GitHub bug issue immediately — without waiting to be prompted**. Filing an issue is easily reversible and non-destructive (close it if wrong), so asking permission first adds latency without adding safety. Only ambiguous or attribution-unclear findings get *offered* ("want this filed?") rather than silently held. Every filed issue carries the reproduction command, evidence links, and a fix sketch so it is marathon-ready. First applied 2026-08-23: the Gen 3.5 soak findings (#174/#177) became #180–#184 without prompting.

---

## 2. Standard Workflow Lifecycle

```
[1. Intake / PDDA Doc]
        │
        ▼
[2. Standalone Clone Setup] ──> (bash githooks/install.sh)
        │
        ▼
[3. Local Gate Preflight (non-qualifying)] ──> (./validate.sh)
        │
        ▼
[4. Grid Configuration]     ──> (utils/ate/variations.<name>.yaml)
        │
        ▼
[5. Campaign Execution]     ──> (python3 utils/ate/scripts/run_variations.py)
        │
        ▼
[6. Supervision & Triage]   ──> (checkin.py / local LM Studio classifier)
        │
        ▼
[7. Results Ingestion]      ──> (TESTS-RESULTS/YYYY-MM-DD+GH-<n>/)
        │
        ▼
[8. Registry & Closeout]    ──> (HARNESS-MODELS-REGISTRY.md & PR)
```

---

## 3. Step-by-Step Instructions

### Step 1: Intake & Working Doc
1. File the tracking GitHub issue.
2. Scaffold the active doc in `PROJECT/2-WORKING/GH-<n>-<SLUG>.md`.
3. Park the ledger row **in the RELEASES DB** (`ROADMAP.md` is retired per GH-269):
   `python3 utils/py/releases_app.py roadmap add --issue-num N --issue-url U --title T --created YYYY-MM-DD --doc-path P`
   (`hq park` routes there automatically). Note `roadmap sync` is a **legacy-mode-only** verb — in
   this repo it refuses with "releases-mode repo" and is never part of the flow.
4. Verify document hygiene with `utils/pdda/pdda.sh run`.

### Step 1b: Promoting a capture from 1-INBOX to 2-WORKING (releases-mode)

The promotion procedure is four DB/file steps on the RELEASES DB:

1. `git mv PROJECT/1-INBOX/GH-<n>-<SLUG>.md PROJECT/2-WORKING/GH-<n>-<SLUG>.md`, then bring the
   doc up to the 2-WORKING contract: full frontmatter **including the `updated:` key**
   (`pdda-check-frontmatter` hard-fails without it — this is what actually turned the push gate
   red, not any missing ROADMAP pointer), the exact two-column `## Status` table, and QA gates
   when phased.
2. Repoint the parked row: `python3 utils/py/releases_app.py roadmap repoint --issue-num <n> --doc-path PROJECT/2-WORKING/GH-<n>-<SLUG>.md`.
3. Refresh the row text: `python3 utils/py/releases_app.py roadmap update --issue-num <n> --raw-text '- **GH-<n> · <title>** ...'`
   — the value **must be a markdown bullet starting `- **<title>**`** or the verb refuses.
4. Regenerate the views (`bash utils/roadmap-dashboard.sh`; ledger writes auto-refresh the baked
   HTML) and verify: `releases check` clean + `utils/pdda/pdda.sh run` zero errors. pdda's
   coverage check reads the DB in releases-mode — a promoted doc needs **no** `ROADMAP.md` line.

### Step 2: Isolated Full Clone Provisioning
```bash
git clone . ../XYZ-forge-<topic>
cd ../XYZ-forge-<topic>
bash githooks/install.sh
```

> **This is a disposable CAMPAIGN clone** (destructive-suite isolation, GH-564) — cloning from
> the local checkout is fine because nothing here ever pushes. It is **not** the fix/feat PR
> lane: new development work clones from the **GitHub remote** and branches off
> `origin/development` per §4 "Opinionated SOPs", so its `origin` points at GitHub.

### Step 3: Local Gate Preflight (non-qualifying)
Before launching a campaign or spending API tokens:
```bash
./validate.sh
bash utils/fuzzing/fuzz-loop.sh
```
Ensure 100% of test suites pass before proceeding. This is a **self-check preflight** — the
qualifying run that writes the evidence record is `bash ci-local.sh` (see `AGENTS.md`), which
remains outstanding until run.

### Step 4: Configure Matrix & Telemetry
Define the variation matrix in `utils/ate/variations.<name>.yaml`:
- Always use `{harness_root}` in `command_template` for script paths.
- Ensure the runner emits structured telemetry fields (`duration_ms`, `turn_count`, `prompt_tokens`, `completion_tokens`, `tokens_source`).
- **Diagnostic Probes:** Set `expects_edits: false` on diagnostic grids that read/report without modifying the working tree (prevents false `no_edit` classifications).

### Step 5: Execute Campaign with Supervision
Provision a disposable scratch repository outside the codebase:
```bash
SCRATCH="${TMPDIR:-/tmp}/ate-scratch-<name>"
mkdir -p "$SCRATCH" && git -C "$SCRATCH" init -q

python3 utils/ate/scripts/run_variations.py \
  --repo "$SCRATCH" \
  --variations utils/ate/variations.<name>.yaml \
  --lmstudio-model "google/gemma-4-31b-qat" \
  --minutes 60 \
  --log-file "$SCRATCH/error_log.jsonl" \
  --test-name "<topic>-grid" \
  --allow-destructive-reset
```

### Step 6: Monitor & Inspect Drift
Supervise the running loop at 5-minute intervals using `checkin.py`:
```bash
python3 utils/ate/scripts/checkin.py --log "$SCRATCH/error_log.jsonl"
```
Monitor failure clusters, category distributions (`auth_failure`, `config_error`, `env_failure`), and throughput. If a valid defect is identified:
1. **File a GitHub tracking issue immediately (auto-file — §1; do not wait to be prompted).** Ambiguous findings: offer to file rather than holding them silently.
2. If straightforward, dispatch to DeepSeek Harness (`dsh` -> OpenRouter -> `deepseek-v4-pro`) in a clean standalone full clone (GH-564) to synthesize a fix and regression test.
3. If complex, record findings on the issue for architectural planning.

### Step 7: Commit Artifact Receipts
Store the campaign output in `TESTS-RESULTS/`:
1. Create `TESTS-RESULTS/YYYY-MM-DD+GH-<issue-number>/`.
2. Copy `error_log.jsonl` and raw baseline measurements into the folder.
3. Author a `SUMMARY.md` documenting duration, total runs, variation distribution, and key findings.

### Step 8: Update Registries and Open PR
1. Record findings and policy updates in `HARNESS-MODELS-REGISTRY.md`.
2. Update the status table in `PROJECT/2-WORKING/GH-<n>-<SLUG>.md`.
3. Update GitHub issue with summary notes.
4. Verify pre-push gates (`test/gh308-frozen-twin-guard.sh --check --staged`).
5. Commit, push branch, and open PR against `development`.

---

## 3b. Anti-patterns (learned the hard way, 2026-09-02)

### Never open a network path into the operator's machine without asking first

A tunnel, a port forward, a remote bridge, an ngrok/cloudflared URL — anything that makes a local
process reachable from outside the machine — **requires the operator's explicit permission each
time.** It is not covered by "you may run the tests" or by a task that happens to involve the
feature. Bridging in is a perfectly reasonable thing to want; the rule is that the operator decides,
not the agent, because the agent cannot see who else is on the network or what else is on the disk.

This was written after a mutation test removed a tunnel guard and stood up a real public URL to a
local transcript store for about two minutes, unasked. The exposure was small and closed quickly.
The reason it is a rule anyway is that nothing in the process would have stopped a larger one.

### The guards read comments — an example in prose fails the scan just like real code

`security-scan.sh` and `gh139-pipe-grep-guard.sh` are static text scans over the whole file. Writing
the banned shape into a comment to *explain* it fails the guard exactly as writing it in code does.
This happened four separate times in one session — a piped quiet grep, a credential-looking
assignment, a shell-eval example, and a comment explaining one of the other three.

Describe the shape in words rather than reproducing it, and run `security-scan.sh` plus
`gh139-pipe-grep-guard.sh` locally **before** pushing new guard-adjacent shell. The full gate takes
about nine minutes to tell you the same thing.

### A test that starts a server must kill the server, not the shell that launched it

Backgrounding `( ... ) &` and killing `$!` reaps the **subshell**. A `python3`/`node` child it
spawned keeps running, keeps its port bound, and outlives the test — silently, because the suite
already printed PASS and moved on. In the incident above this is exactly what left the bridge alive
after its test finished; it was found in `ps`, not by the teardown.

Kill the child by its own PID, or start it with `exec` so the subshell *becomes* the process. Then
**verify** with `ps`/`lsof` rather than trusting the kill. A teardown that cannot fail is not a
teardown — the same rule as `AGENTS.md` §6.

## 4. Opinionated SOPs (XYZ-maintainer defaults — optional downstream)

> **Who these are for:** These conventions exist to help the **XYZ maintainers** with our own
> development flow on this repository. They are **not** part of the harness contract.
> **Public users and downstream forks are free to disable them**, instruct their own LLM
> maintainers to ignore them, or write a script that strips this section on pull from upstream.
> Nothing in the codebase enforces them.

- **The primary clone stays on `development`.** Each device has exactly one
  **operator-designated primary clone** — the long-lived checkout the operator opens by default
  and keeps mapped to GitHub. That clone is always kept on the `development` branch. This rule
  applies **only** to the primary clone by role; task clones provisioned under the next rule are
  exempt (they live on their own task branch and are disposable).
- **Express-to-development is explicit; everything else gets a fresh full clone.** Direct
  commit + push into `development` happens only when the user **explicitly asks** for an express
  commit of critical work. In every other case, the LLM begins new work by provisioning a
  **new local full-clone folder** — a full clone, *not* a git worktree (GH-564) — cloned from
  the GitHub remote so `origin` points at GitHub, wired with the gate, and branched off
  `origin/development`:

  ```bash
  git clone git@github.com:HiQS-Labs/XYZ-forge.git ../XYZ-forge-<topic>
  cd ../XYZ-forge-<topic>
  bash githooks/install.sh                       # per-clone; the gate does not travel (GH-549)
  git checkout -b feat/<topic> origin/development   # or fix/<topic>
  ```

  Work lands by pushing that task branch and opening a PR into `development`. **This policy is
  the standing explicit authorization** for that fresh-clone task branch under `AGENTS.md`'s
  "do not create new git branches automatically" rail — the same carve-out shape as the
  marathon per-lane branch. It authorizes exactly one `feat/`/`fix/` branch per fresh task
  clone, and it is *not* a licence to commit directly onto `development` (the express path
  above remains user-request-only).

### Arc planning — schedule the follow-up lanes, don't discover them

> Lesson from the GH-280/#291 stretch (2026-08-29): six PRs in ~48h, each small and safe,
> yet the shape of progress was a thicket instead of a line. Post-mortem: the *arc* was
> predictable (implement → review findings → dogfood findings → conformance → default
> flip); only the specific defects weren't. The fix is not fewer rails — it is making the
> predictable parts of the arc explicit at plan time.

1. **Pre-create the budgeted follow-up lanes at plan time.** Before implementation starts,
   open the three issues you already know you will need: a *review-findings* lane (the
   builder/reviewer split guarantees one), a *dogfood-findings* lane (dogfooding exists to
   manufacture findings), and a *conformance* lane (new contracts always owe fixtures).
   Follow-ups then arrive as scheduled phases instead of surprises. Evidence this works:
   the GH-280 plan's follow-up record listed six items before execution began; all six
   landed in that order, with review findings landed on top.
2. **Batch same-seam scopes into one PR.** Five small PRs touching one seam is five
   gate + merge + reconcile cycles for what is really one unit of review. GH-291 shipped
   Scopes 1+5, 3+4, and 2 as three PRs; two would have carried the same review weight.
3. **Reconciliation ownership and batching.** Hosted `wave-reconcile.yml` is the primary landing
   writer on `development`, automatically reconciling docs, ledger, and views. If running local
   reconciliation as fallback, the rule is to let hosted runs finish (or pass `--force-local-reconcile`
   in emergencies) and batch multiple PRs (`wave_reconcile.py --pr <N> <M>`) rather than running
   instantly per merge. Task branches must not commit routine view updates (`ROADMAP-DASHBOARD.md`,
   `LEADERBOARD.md`).
4. **Never write bare `#N` for another repo's issues in a PR body.** The reconciler
   resolves every `#N` against *this* repo and exits 6 when it cannot (GH-301 needed an
   offline-manifest escape mid-reconcile). Cross-repo references are written `GH-N`;
   in-repo references may use `#N`.
5. **Delegate in this shape when lanes are independent:** each lane gets its own fresh
   full clone and exactly one branch + one PR; it commits and pushes at every milestone
   (the push gate is the boundary); it never merges its own PR. A single
   orchestrator-reviewer holds merge duty, checks the three predicates (base branch,
   diff size vs logical scope, gate evidence on the final SHA), merges pinned to the
   reviewed head — and **independently verifies any claim the gate cannot prove** (the
   gate-invisible example: a suite exempted from the registry as "pre-existing red").

### The project website (GitHub Pages) — edit, update, deploy

`PAGES/` is the root of the live site at <https://hiqs-labs.github.io/XYZ-forge/>.
There is no upload step and no build step for the static pages: what is committed to
`PAGES/` is what gets served. Deploy happens in `.github/workflows/pages.yml`
(Pages is enabled with **Source: GitHub Actions**, i.e. `build_type=workflow` — a custom
folder like `PAGES/` is not servable from the "deploy from a branch" mode, which only
supports `/` and `/docs`).

**Two kinds of pages, two rules:**

- **Static pages** (`index.html`, `use-cases.html`, `how-it-works.html`, `faq.html`,
  `contact.html`, `issues.html`, `assets/style.css`, `robots.txt`, `sitemap.xml`) —
  hand-edit the HTML directly. `issues.html` is an instant-redirect stub to the GitHub
  issue tracker (noindex, no nav — deliberate).
- **Generated pages** (`roadmap.html`, `models-harnesses.html`) — **never hand-edit.**
  They are baked from the committed ledgers by `utils/py/site_build.py`
  (roadmap ← `releases_app.py roadmap list --json`; models ← `harnesses.db`) and are
  regenerated at deploy time, so a hand edit is silently overwritten on the next deploy.
  Change their *data* through the normal ledger verbs (`releases_app`, `harness_app`);
  change their *look* in the generator's render functions, then re-run it.

**Edit + refresh the generated copies locally:**

```bash
python3 utils/py/site_build.py           # rewrite the two generated pages from the ledgers
python3 utils/py/site_build.py --check   # informational: are committed copies stale?
```

**Preview locally** (loopback only — never bind a preview server to anything but
127.0.0.1; see §3b on network paths):

```bash
cd PAGES && python3 -m http.server 8765 --bind 127.0.0.1
# then open http://127.0.0.1:8765/ — links are relative, so they work under any prefix
```

**Deploy ("upload"):** commit and push to `development` (or `main`). The workflow
triggers on changes to `PAGES/**`, `utils/py/site_build.py`, `utils/py/releases_app.py`,
`releases.db`/`releases.sql`, `harnesses.db`/`harnesses.sql`, and the workflow file —
so a ledger push republishes the roadmap even when nobody re-ran the builder. To
redeploy without a push: `gh workflow run pages.yml --ref development`. Verify with
`gh run watch <id>` and a `curl -sI` of the live URL; the concurrency group (`pages`)
cancels superseded runs, so only one deploy lands at a time. The normal pre-push gate
applies (~8 min if code paths are touched).

**Site-specific rails:**

- **Everything in `PAGES/` is publicly served.** No scratch files, notes, or drafts in
  there (the near-miss: `PAGES/TEMP.md` research notes would have shipped as a public
  page; they now live in `temp/`). Scratch goes to `temp/`, never the site root.
- **Relative links only.** The site serves under `/XYZ-forge/`; an absolute path like
  `/assets/style.css` 404s in production while working in some local previews.
- **Adding a page means three edits:** the new file, the nav link in every static page
  *and* the `NAV` list in `utils/py/site_build.py` (the generator does not read the
  static pages), and a `<url>` entry in `sitemap.xml` (the sitemap is static).
- **`google<token>.html` stays.** It is the Search Console verification file; deleting
  it un-verifies the property. It is meant to be public.
- **Do not copy the timeline template's styling into the site.**
  `utils/timeline/RELEASES.html` is AGPL-derived (Neochrome); the site's own stylesheet
  exists partly to keep that license out of the public site.
- **Empty ledgers fail the deploy on purpose.** `site_build.py` exits 2 if a query
  returns zero rows (an empty page would otherwise look like success — AGENTS.md §6).
  Fix the data, don't bypass the guard.
