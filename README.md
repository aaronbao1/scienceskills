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
