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
