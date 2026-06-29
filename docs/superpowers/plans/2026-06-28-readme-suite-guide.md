# README Suite Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the minimal `README.md` into the single front-door guide for the scienceskills suite — covering how skills activate, a capability reference for all 11 skills, end-to-end composition workflows, a skill-forge deep dive, the eval-harness commands, and a reference-file map — written for both the operator (the repo owner) and researchers adopting the plugin.

**Architecture:** A single file, `README.md`, is fully rewritten. It is assembled section by section (one task per coherent section group), each section committed independently. There is no application code; "tests" are (1) factual-accuracy audits that every skill name and file path the README mentions actually exists, and (2) the repo's existing gates — `python3 -m eval.harness.cli lint`, `python3 -m eval.harness.cli validate`, and `pytest` — staying green so the doc change breaks nothing.

**Tech Stack:** Markdown. Verification via the project's Python eval harness (`eval/harness/cli.py`, `capture.py`, `forge.py`) and `pytest`.

## Global Constraints

- The deliverable is exactly one file: `README.md` at the repo root. Do not create new doc files; do not move the existing specs/plans.
- Every skill name written in the README MUST be one of the 11 real skill directories: `argumentation-and-sources`, `deep-reasoning`, `deep-reasoning-ultra`, `faithful-implementation`, `humanities-inquiry`, `literature-review`, `research-design`, `research-synthesis`, `rigorous-validation`, `scientific-rigor`, `skill-forge`.
- Every command written in the README MUST match the real harness surface, verbatim:
  - `python3 -m eval.harness.cli lint`
  - `python3 -m eval.harness.cli validate`
  - `python3 -m eval.harness.capture snapshot <skill>`
  - `python3 -m eval.harness.capture insight <skill>`
  - `python3 -m eval.harness.forge <skill> results.json`
- Capability blurbs MUST stay faithful to each skill's own `description:` frontmatter (paraphrase in spirit; do not invent capabilities a skill does not claim).
- Preserve the existing dev-setup content (venv / `pip install -e ".[dev]"` / `pytest`) and the lint/validate commands already in `README.md`.
- Keep the existing pointer to the design spec `docs/superpowers/specs/2026-06-27-scienceskills-design.md` and to `CLAUDE.md`.
- Cross-references inside the README use relative links that resolve from the repo root (e.g. `skills/scientific-rigor/SKILL.md`, `CLAUDE.md`).

---

## File Structure

- **Modify (full rewrite):** `README.md` — the only file changed. Responsibility: be the complete operator + adopter guide to the suite.

All tasks modify this one file by appending the next section. Order matters: the file reads top-to-bottom in the order tasks are executed.

---

### Task 1: Top of doc — intro, "how skills activate", and the lifecycle map

**Files:**
- Modify: `README.md` (replace entire file with the content below; later tasks append after the `<!-- §map end -->` marker)

**Interfaces:**
- Consumes: nothing.
- Produces: the document header through the lifecycle-map section. Later tasks append below the marker comment `<!-- §map end -->` and rely on the section headings established here (`## Skills` will be added in Task 2, etc.).

- [ ] **Step 1: Write the section content**

Replace the full contents of `README.md` with:

````markdown
# scienceskills

A self-improving Claude Code skill suite for **rigorous scientific research** — framing
questions, surveying the literature, implementing methods faithfully, validating results,
and writing them up, with a built-in engine that improves the skills from their own usage.

This README is the front door. It covers what each skill does, how to chain them across a
research project, how the self-improvement engine (`skill-forge`) works, and the commands
for the eval harness. Operating standards live in [`CLAUDE.md`](CLAUDE.md); the original
design is in [`docs/superpowers/specs/2026-06-27-scienceskills-design.md`](docs/superpowers/specs/2026-06-27-scienceskills-design.md).

## How the skills activate

The suite is a Claude Code plugin. Skills live in [`skills/`](skills/), one folder per
skill, each a `SKILL.md` with a `name` and a `description`. You don't memorize them:

- **`scientific-rigor` is the always-on backbone.** It holds the standards (falsifiability,
  honesty, calibrated uncertainty, anti-bias discipline, robustness, structured creativity)
  and **routes** you to the right phase skill for the moment. Reach for it — or just start a
  research task — and it points you onward.
- **Skills auto-trigger on their description**, or you can name one directly
  ("use `rigorous-validation`").
- **The composition rule:** this suite never reinvents planning, TDD, code review,
  statistics, or document generation. It adds the *scientific* layer and delegates the rest
  to existing skills (`writing-plans`, `test-driven-development`, `/code-review`,
  `data:statistical-analysis`, `docx`/`pptx`, …).

## The map — which skill for which phase

| You are about to… | Use |
| --- | --- |
| Frame a question, hypotheses, metrics, experiment plan | `research-design` (empirical) or `humanities-inquiry` (interpretive) |
| Survey a field or choose among competing methods | `literature-review` or `argumentation-and-sources` |
| Implement a method faithfully to its source | `faithful-implementation` (with `writing-plans`, `subagent-driven-development`, `test-driven-development`) |
| Validate results before believing them | `rigorous-validation` (with `data:statistical-analysis`, `/code-review`) |
| Turn validated results into a write-up | `research-synthesis` (with `data:create-viz`, `docx`/`pptx`) |
| Think hard about a single tough problem | `deep-reasoning`, or `deep-reasoning-ultra` for the highest stakes |
| Improve the skills themselves | `skill-forge` |

Always-on underneath all of it: `scientific-rigor` (standards + routing).

<!-- §map end -->
````

- [ ] **Step 2: Verify named skills exist**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && for s in research-design humanities-inquiry literature-review argumentation-and-sources faithful-implementation rigorous-validation research-synthesis deep-reasoning deep-reasoning-ultra skill-forge scientific-rigor; do test -d "skills/$s" || echo "MISSING: $s"; done; echo "skill-name audit done"
```
Expected: prints only `skill-name audit done` (no `MISSING:` lines).

- [ ] **Step 3: Verify the doc-link targets exist**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && for f in CLAUDE.md skills docs/superpowers/specs/2026-06-27-scienceskills-design.md; do test -e "$f" || echo "MISSING LINK: $f"; done; echo "link audit done"
```
Expected: prints only `link audit done`.

- [ ] **Step 4: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): intro, activation model, lifecycle map"
```

---

### Task 2: Skill reference — all 11 skills, grouped by role

**Files:**
- Modify: `README.md` (append after `<!-- §map end -->`)

**Interfaces:**
- Consumes: the headings/structure from Task 1.
- Produces: the `## Skills` section. Each entry follows the fixed shape **what · when · composes with**, faithful to the skill's `description:`.

- [ ] **Step 1: Append the section content**

Append to `README.md`:

````markdown
## Skills

Each entry is **what it does · when to reach for it · what it composes with**. The blurbs
track each skill's own `description` in its `SKILL.md`.

### Backbone & reasoning

**[`scientific-rigor`](skills/scientific-rigor/SKILL.md)** — the always-on backbone for any
research, analysis, or research-codebase task. Holds the rigor/honesty/creativity standards
and routes to the right phase skill. *Reach for it:* by default, on every research task.
*Composes with:* every other skill (it routes to them); carries the deep-dive references
`reasoning-and-creativity.md` and `rigor-checklists.md`.

**[`deep-reasoning`](skills/deep-reasoning/SKILL.md)** — a budget-aware, tiered deliberation
protocol (triage → decompose → parallel paths → independent verification → search) that
matches reasoning effort to difficulty. *Reach for it:* any genuinely hard problem that
deserves more than a single pass. *Composes with:* the Workflow tool /
`dispatching-parallel-agents` for the parallel paths.

**[`deep-reasoning-ultra`](skills/deep-reasoning-ultra/SKILL.md)** — the `deep-reasoning`
protocol plus a deterministic aggregation core (self-consistency, calibrated confidence,
escalate/stop) that turns parallel reasoning paths into an auditable decision. *Reach for
it:* the hardest, highest-stakes calls where you need a defensible confidence number.
*Composes with:* `deep-reasoning` (it is the heavyweight tier).

### Frame the question

**[`research-design`](skills/research-design/SKILL.md)** — frames the question, states
falsifiable hypotheses and success metrics, and plans experiments and ablations **before any
data is seen**. *Reach for it:* starting an empirical project or defining what to test.
*Composes with:* `literature-review` next; the pre-registered metrics feed
`rigorous-validation`.

**[`humanities-inquiry`](skills/humanities-inquiry/SKILL.md)** — close reading, hermeneutics,
historiography, theoretical framing, and qualitative coding, where the goal is a defensible
*interpretation* rather than an empirical measurement. *Reach for it:* interpretive or
qualitative research. *Composes with:* `argumentation-and-sources` for source criticism.

### Survey the field

**[`literature-review`](skills/literature-review/SKILL.md)** — searches and critically
appraises sources, maps the state of the art and the gaps, and produces a justified, ranked
comparison of methods plus the **oracles an implementation must match**. *Reach for it:*
surveying a field or choosing among competing methods. *Composes with:* `deep-research` for
the search; hands its oracles to `faithful-implementation`.

**[`argumentation-and-sources`](skills/argumentation-and-sources/SKILL.md)** — appraises
primary and secondary sources, constructs and stress-tests arguments, maps scholarly debate,
and catches fallacies and unsupported leaps. *Reach for it:* evidence and source criticism in
argument-driven work. *Composes with:* `humanities-inquiry`.

### Build it

**[`faithful-implementation`](skills/faithful-implementation/SKILL.md)** — defines the
literature-derived **test oracles** so that TDD proves the code matches its source, and
detects divergence from it. *Reach for it:* implementing a method, algorithm, or model from
the literature. *Composes with:* `writing-plans` → `subagent-driven-development` →
`test-driven-development` (the build trio).

### Validate it

**[`rigorous-validation`](skills/rigorous-validation/SKILL.md)** — checks reproducibility,
statistical validity, robustness, baselines, and leakage/bias, and red-teams your own
findings before you believe them. *Reach for it:* once results exist. *Composes with:*
`data:statistical-analysis` and `/code-review`.

### Write it up

**[`research-synthesis`](skills/research-synthesis/SKILL.md)** — interprets findings honestly,
visualizes them, and writes claims **calibrated to the evidence** with explicit limitations.
*Reach for it:* turning validated results into a report, paper, figures, or deck. *Composes
with:* `data:create-viz`, `docx`/`pptx`.

### Improve the skills

**[`skill-forge`](skills/skill-forge/SKILL.md)** — the self-improvement engine: mines the
insights each skill captured from its own sessions, distills them into a playbook, and
proposes human-approved, gated edits to a skill. *Reach for it:* improving the suite itself.
*Composes with:* the eval harness (`capture` / `forge`), `writing-skills`,
`using-git-worktrees`, and the Workflow tool. Full how-to below.
````

- [ ] **Step 2: Verify every `SKILL.md` link target exists**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && grep -oE 'skills/[a-z-]+/SKILL\.md' README.md | sort -u | while read -r f; do test -e "$f" || echo "MISSING: $f"; done; echo "skill-link audit done"
```
Expected: prints only `skill-link audit done`.

- [ ] **Step 3: Confirm all 11 skills are documented**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && echo "documented: $(grep -oE 'skills/[a-z-]+/SKILL\.md' README.md | sort -u | wc -l | tr -d ' ') of 11"
```
Expected: `documented: 11 of 11`.

- [ ] **Step 4: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): per-skill capability reference"
```

---

### Task 3: Composition workflows — end-to-end walkthroughs

**Files:**
- Modify: `README.md` (append)

**Interfaces:**
- Consumes: the skill names established in Task 2.
- Produces: the `## Workflows` section; downstream tasks do not depend on it.

- [ ] **Step 1: Append the section content**

Append to `README.md`:

````markdown
## Workflows — operating the full suite

Skills chain. `scientific-rigor` sits underneath every workflow, enforcing the standards and
routing between phases. Three common arcs:

### A. An empirical study (design → ship → believe → tell)

1. **`research-design`** — sharpen the question; state a hypothesis with a prediction that
   could fail; pre-register the primary metric and the ablations *before looking at data*.
2. **`literature-review`** — survey methods, pick one with justification, and extract the
   oracles the implementation must satisfy.
3. **`faithful-implementation`** — build it via `writing-plans` →
   `subagent-driven-development` → `test-driven-development`; the oracles from step 2 become
   the tests that prove fidelity to the source.
4. **`rigorous-validation`** — reproducibility, baselines, robustness across seeds and splits,
   a leakage/bias check, and a red-team of your own result (with `data:statistical-analysis`
   and `/code-review`).
5. **`research-synthesis`** — write it up with claims calibrated to the evidence and explicit
   limitations; figures via `data:create-viz`; deliverable via `docx`/`pptx`.
6. **At session end** — capture insights so `skill-forge` can learn (see the eval-harness
   section).

### B. An interpretive / humanities project

1. **`humanities-inquiry`** — frame the inquiry; fix the reading lens and any coding scheme in
   advance; close-read.
2. **`argumentation-and-sources`** — appraise primary and secondary sources, construct and
   stress-test the argument, map the scholarly debate, and catch fallacies and unsupported
   leaps.
3. **`research-synthesis`** — write the defensible interpretation with calibrated confidence
   and acknowledged counter-readings.

### C. One genuinely hard problem

- **`deep-reasoning`** for a hard one-off — it triages difficulty and spends effort
  accordingly (decompose, run parallel paths, verify independently, search).
- Escalate to **`deep-reasoning-ultra`** when the stakes demand an *auditable* decision: it
  aggregates the parallel paths into a calibrated confidence with an explicit escalate/stop.
````

- [ ] **Step 2: Verify no stray skill names slipped in**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && grep -oE '`[a-z][a-z-]+`' README.md | tr -d '`' | sort -u | grep -E '^(research-design|humanities-inquiry|literature-review|argumentation-and-sources|faithful-implementation|rigorous-validation|research-synthesis|deep-reasoning|deep-reasoning-ultra|skill-forge|scientific-rigor)$' | wc -l | xargs echo "in-suite skill mentions:"; echo "(sanity check — non-zero, no error)"
```
Expected: a non-zero count and no error. (This is a sanity check that the suite skills are referenced; external skills like `writing-plans` are expected too and are fine.)

- [ ] **Step 3: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): end-to-end composition workflows"
```

---

### Task 4: skill-forge deep dive

**Files:**
- Modify: `README.md` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: the `## skill-forge` section. Commands here MUST match the Global Constraints command list. Source of truth: [`skills/skill-forge/SKILL.md`](skills/skill-forge/SKILL.md).

- [ ] **Step 1: Append the section content**

Append to `README.md`:

````markdown
## skill-forge — the self-improvement engine

`skill-forge` evolves the suite **one skill at a time** and never promotes a durable change
without measured evidence on a held-out benchmark *and* your approval. It is self-contained:
every target skill captures its own session insights into a central store, and `skill-forge`
turns those logs into improvements.

**Two layers of improvement:**

- **Playbook** — fast, reversible, no gate. Distilled heuristics a skill consults at use-time.
- **`SKILL.md`** — slow, gated, rare. Durable edits, promoted only through the held-out gate
  plus your approval.

**The insight store** (`skills/skill-forge/insights/<skill>/`):

```
transcripts/<session-id>.jsonl   raw session snapshots (gitignored cache)
raw.jsonl                        per-session insight records (committed)
playbook.md                      curated heuristics, bounded, vote tags (committed)
gate-history.jsonl               one line per gate round (committed)
```

**The loop:**

1. **Capture** (run inside each skill, at session end). Snapshot the transcript and append
   one *generalized* insight — behavioral signals only (correction/redo, abandonment,
   approval, hard failure, self-assessed struggle), no judge:
   ```bash
   python3 -m eval.harness.capture snapshot <skill>
   # then pipe a JSON insight record to:
   python3 -m eval.harness.capture insight <skill>
   ```
2. **Distill.** Read recent `raw.jsonl`, contrast failures vs successes, and curate
   `playbook.md` with ADD / EDIT / UPVOTE / DOWNVOTE. Keep it bounded (default ≤25 entries;
   prune lowest net-vote). Heuristics must generalize — no project-specifics.
3. **Crystallize.** When a heuristic has earned its keep (net votes ≥4, recurs across ≥3
   sessions), express it as an attributed line edit `{old, new, reason}` against the target
   `SKILL.md`, in 1–2 candidates in isolated worktrees (`using-git-worktrees`).
4. **Gate.** Run incumbent vs candidate on the **held-out `gate` split only**, paired on the
   same tasks with **K ≥ 3 independent seeds per task**, then:
   ```bash
   python3 -m eval.harness.forge <skill> results.json
   ```
   It runs the Goodhart monitor and promotes only when there is no critical-task regression,
   the candidate wins gold on every seed, and the mean gain exceeds the incumbent's
   seed-to-seed noise. **Exit 0** = promote-pending-approval · **1** = reject · **2** = halt.
5. **Promote.** On pass **and your approval**: replace the `SKILL.md`, retire the heuristic
   from the playbook (mark it `crystallized`), and `git tag` the new version so the prior one
   is one `git checkout` away.

**Judging (when a task is judge-scored):** use a panel of ≥3 judges from disjoint model
families, none from the candidate-generator's family; compare both A/B orders and count a win
only if it wins both; sanitize candidate-controlled text before it enters the judge template;
always keep deterministic ground-truth tasks as the non-judge tripwire.

**Red flags — stop:** promoting without approval or without a measured held-out gain; gating
on the dev split, a sub-noise margin, or a single seed; a single judge or a single A/B order;
editing the benchmark to make a candidate pass; crystallizing while the monitor shows
proxy↑/gold↓; committing project-specific content into the store; leaving no git rollback path.
````

- [ ] **Step 2: Verify the forge commands and store paths are real**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && python3 -c "import eval.harness.capture, eval.harness.forge" && echo "modules import OK" && grep -q "snapshot" eval/harness/capture.py && grep -q "insight" eval/harness/capture.py && echo "capture subcommands OK"
```
Expected: `modules import OK` then `capture subcommands OK`.

- [ ] **Step 3: Verify the documented commands match the harness exactly**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && grep -nE 'python3 -m eval\.harness\.(capture (snapshot|insight)|forge) ' README.md && echo "command-string audit done"
```
Expected: lines for `capture snapshot`, `capture insight`, and `forge`, then `command-string audit done`.

- [ ] **Step 4: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): skill-forge deep dive (loop, store, gate)"
```

---

### Task 5: Eval harness — commands and benchmark schema

**Files:**
- Modify: `README.md` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: the `## Eval harness` section. Source of truth: `eval/harness/cli.py` (lint/validate), `eval/benchmarks/*/tasks.yaml` (schema), `eval/harness/forge.py` (gate).

- [ ] **Step 1: Append the section content**

Append to `README.md`:

````markdown
## Eval harness

The harness in [`eval/`](eval/) lints skills, validates benchmarks, captures session
insights, and runs the promotion gate.

| Command | Does |
| --- | --- |
| `python3 -m eval.harness.cli lint` | Lint every `skills/*/SKILL.md` (frontmatter, structure). Exit 1 if any issue. |
| `python3 -m eval.harness.cli validate` | Validate every `eval/benchmarks/*/tasks.yaml`. Exit 1 on any error. |
| `python3 -m eval.harness.capture snapshot <skill>` | Snapshot the current session's transcript into the skill's insight store. |
| `python3 -m eval.harness.capture insight <skill>` | Append one generalized insight record (piped JSON) to `raw.jsonl`. |
| `python3 -m eval.harness.forge <skill> results.json` | Run the promotion gate + Goodhart monitor. Exit 0 promote-pending-approval / 1 reject / 2 halt. |

**Benchmark task schema** (`eval/benchmarks/<skill>/tasks.yaml`): each task has an `id`, a
`kind` (`judge` for rubric-scored, `ground_truth` for deterministic), a `prompt`, and a
`split`. Ground-truth tasks add a `scorer` (e.g. `numeric`), an `expected` value, and a
`tolerance`. Rubrics live in [`eval/rubrics/`](eval/rubrics/), one per skill.

**Splits matter for the gate.** `split: dev` tasks are for iteration; `split: gate` tasks are
**held out** — the improvement loop never mines against them, so a candidate that wins on the
`gate` split has earned a real, un-overfit gain. The `forge` gate scores the held-out `gate`
split only.
````

- [ ] **Step 2: Verify the lint/validate commands run and the schema fields are real**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && python3 -m eval.harness.cli lint && python3 -m eval.harness.cli validate && grep -rqE 'split:\s*gate' eval/benchmarks/*/tasks.yaml && grep -rqE 'kind:\s*(judge|ground_truth)' eval/benchmarks/*/tasks.yaml && test -d eval/rubrics && echo "harness + schema audit done"
```
Expected: lint prints `lint: OK`, validate prints `validate: OK`, then `harness + schema audit done`.

- [ ] **Step 3: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): eval-harness commands and benchmark schema"
```

---

### Task 6: Reference-file map, dev setup, and repo layout (closing sections)

**Files:**
- Modify: `README.md` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: the closing `## Reference files`, `## Dev setup`, and `## Repo layout` sections. This is the end of the document.

- [ ] **Step 1: Append the section content**

Append to `README.md`:

````markdown
## Reference files

Some skills carry deep-dive companions and per-skill learned heuristics, loaded only when
relevant:

- **`scientific-rigor`** →
  [`reasoning-and-creativity.md`](skills/scientific-rigor/reasoning-and-creativity.md)
  (structured creativity: diverge widely, then prune with explicit criteria) and
  [`rigor-checklists.md`](skills/scientific-rigor/rigor-checklists.md) (detailed per-phase
  checklists).
- **Every skill** consults its learned playbook at
  `skills/skill-forge/insights/<skill>/playbook.md` before starting (skipped if absent) and
  captures insights back to the same store at session end.
- **Design & planning history** lives in
  [`docs/superpowers/specs/`](docs/superpowers/specs/) (design docs) and
  [`docs/superpowers/plans/`](docs/superpowers/plans/) (implementation plans).

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Lint skills and validate benchmarks:

```bash
python3 -m eval.harness.cli lint
python3 -m eval.harness.cli validate
```

## Repo layout

```
skills/         one folder per skill (SKILL.md + any reference files)
  skill-forge/insights/<skill>/   the self-improvement store (playbook, raw.jsonl, …)
eval/
  harness/      lint, validate, capture, forge (the gate + Goodhart monitor)
  benchmarks/   tasks.yaml per skill (dev + held-out gate splits)
  rubrics/      judge rubrics per skill
docs/superpowers/   specs (designs) and plans (implementation plans)
CLAUDE.md       operating standards + the skill router
```
````

- [ ] **Step 2: Verify the closing reference paths exist**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && for f in skills/scientific-rigor/reasoning-and-creativity.md skills/scientific-rigor/rigor-checklists.md docs/superpowers/specs docs/superpowers/plans eval/rubrics eval/benchmarks; do test -e "$f" || echo "MISSING: $f"; done; echo "reference-path audit done"
```
Expected: prints only `reference-path audit done`.

- [ ] **Step 3: Commit**

```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): reference-file map, dev setup, repo layout"
```

---

### Task 7: Whole-document verification, link audit, and self-review

**Files:**
- Modify: `README.md` (fixes only, if the audit finds problems)

**Interfaces:**
- Consumes: the complete `README.md` from Tasks 1–6.
- Produces: the final, verified README. No new sections.

- [ ] **Step 1: Audit every relative link in the README resolves**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && grep -oE '\]\(([A-Za-z0-9._/-]+)\)' README.md | sed -E 's/^\]\(//; s/\)$//' | grep -vE '^https?:' | sort -u | while read -r f; do path="${f%%#*}"; test -e "$path" || echo "BROKEN LINK: $f"; done; echo "full link audit done"
```
Expected: prints only `full link audit done` (no `BROKEN LINK:` lines). If any appear, fix the link in `README.md` and re-run.

- [ ] **Step 2: Confirm the repo gates are still green**

Run:
```bash
cd /Users/aaronbao/Developer/scienceskills && python3 -m eval.harness.cli lint && python3 -m eval.harness.cli validate && pytest -q
```
Expected: `lint: OK`, `validate: OK`, and pytest passes (no failures). A README-only change must not break these.

- [ ] **Step 3: Self-review the rendered doc**

Read `README.md` top to bottom and check:
- All 11 skills appear with a what/when/composes blurb.
- The four scope items are present: composition workflows, skill-forge deep dive, eval-harness usage, reference-file map.
- No placeholder text (`TBD`, `TODO`, `XXX`), no contradictory claims, no skill name outside the 11.
- Commands match the Global Constraints list verbatim.

Run a placeholder scan:
```bash
cd /Users/aaronbao/Developer/scienceskills && grep -nE 'TBD|TODO|FIXME|XXX|<placeholder>' README.md && echo "FOUND PLACEHOLDERS — fix them" || echo "no placeholders"
```
Expected: `no placeholders`.

- [ ] **Step 4: Commit any fixes**

If Steps 1–3 required edits:
```bash
cd /Users/aaronbao/Developer/scienceskills && git add README.md && git commit -m "docs(readme): fix links/accuracy from final audit"
```
If no fixes were needed, skip the commit.

---

## Self-Review (plan author)

**Spec coverage** — the four user-approved scope items map to tasks:
- Per-skill capability reference → Task 2 (all 11) ✓
- Composition workflows → Task 3 ✓
- skill-forge deep dive → Task 4 ✓
- Eval-harness usage → Task 5 ✓
- Reference-file map → Task 6 ✓
- Operator activation model + lifecycle map (the "how to operate the full suite" framing) → Task 1 ✓
- Audience = operator + adopter → handled by the what/when/composes shape and plain-English blurbs throughout ✓
- Location = expand `README.md` itself → every task modifies only `README.md` ✓

**Placeholder scan** — no `TBD`/`TODO`/"add error handling" steps; all content is literal markdown; Task 7 enforces a placeholder grep.

**Consistency** — the five harness commands are identical in Global Constraints, Task 4, and Task 5; the 11 skill names are identical in Global Constraints, Task 1, and Task 2. Verification steps grep the real files (`eval/harness/*.py`, `eval/benchmarks/*/tasks.yaml`) rather than asserting from memory.
