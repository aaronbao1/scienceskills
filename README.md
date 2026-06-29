# scienceskills

A self-improving Claude Code skill suite for **rigorous scientific research** — framing
questions, surveying the literature, implementing methods faithfully, validating results,
and writing them up, with a built-in engine that improves the skills from their own usage.

This README is the front door. It covers what each skill does, how to chain them across a
research project, how the self-improvement engine (`skill-forge`) works, and the commands
for the eval harness. Operating standards live in [`CLAUDE.md`](CLAUDE.md); the original
design is in [`docs/superpowers/specs/2026-06-27-scienceskills-design.md`](docs/superpowers/specs/2026-06-27-scienceskills-design.md).

## Install into Claude Code

The suite ships as a Claude Code plugin through the dev marketplace in
[`.claude-plugin/`](.claude-plugin/) (marketplace `scienceskills-dev`, plugin
`scienceskills`). These are slash commands — **enter them one at a time**, letting the first
finish before the second. (Pasting both together makes `marketplace add` treat the second
line as part of the repo URL and the clone fails.)

**Step 1** — register this repo as a plugin marketplace (Claude Code reads
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)):

```
/plugin marketplace add aaronbao1/scienceskills
```

**Step 2** — once that succeeds, install the plugin from it:

```
/plugin install scienceskills@scienceskills-dev
```

Run `/plugin` anytime to browse, verify, or manage installed plugins.

**Local development** — to test edits to the skills without going through GitHub, add your
clone as a marketplace by path, then install — again, one command at a time:

```
/plugin marketplace add /absolute/path/to/scienceskills
```

```
/plugin install scienceskills@scienceskills-dev
```

**Committed config** — to enable the plugin from `settings.json` instead of the commands
above (e.g. a shared `.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "scienceskills-dev": {
      "source": { "source": "github", "repo": "aaronbao1/scienceskills" }
    }
  },
  "enabledPlugins": { "scienceskills@scienceskills-dev": true }
}
```

Once installed, the skills activate automatically on matching work, or you can invoke one by
name (e.g. `scientific-rigor`, `research-design`) — see below. To build or test the suite
itself, see [Dev setup](#dev-setup).

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
