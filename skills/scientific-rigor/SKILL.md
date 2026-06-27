---
name: scientific-rigor
description: Use for any scientific research, analysis, or research-codebase task — sets the rigor, honesty, and creativity standards and routes to the right research-phase skill.
---

# Scientific Rigor

The always-on backbone for research work. It holds the **standards** (how rigorous,
honest, and creative the work must be) and **routes** to the phase skill for the task.

## Standards (apply to everything)

1. **Falsifiability first.** State what would prove a claim wrong before gathering
   evidence for it. A claim nothing could disconfirm is not a result.
2. **Intellectual honesty.** Report what happened — failures, negative results, skipped
   steps. Never present a hoped-for outcome as an observed one.
3. **Calibrated uncertainty.** Attach confidence; distinguish shown, suggested, and
   speculated. Prefer intervals to point claims.
4. **Anti-bias discipline.** Decide analyses before seeing results (no HARKing); fix the
   metric before optimizing it (no p-hacking); seek disconfirming evidence; never
   cherry-pick.
5. **Robustness.** A result that holds only at one seed, split, or setting is fragile —
   say so, and stress every important claim.
6. **Structured creativity.** Generate widely, then prune hard with explicit criteria.
   Innovation and rigor are partners — see
   [reasoning-and-creativity.md](reasoning-and-creativity.md).

Detailed checklists: [rigor-checklists.md](rigor-checklists.md).

## Router — which skill for this moment

| You are about to… | Use |
| --- | --- |
| Frame a question, hypotheses, metrics, experiment plan | `research-design` (empirical) or `humanities-inquiry` (interpretive) |
| Survey the field or choose among competing methods | `literature-review` or `argumentation-and-sources` |
| Implement a method faithfully to its source | `faithful-implementation` (with `writing-plans`, `subagent-driven-development`, `test-driven-development`) |
| Validate results before believing them | `rigorous-validation` (with `data:statistical-analysis`, `/code-review`) |
| Turn validated results into a write-up | `research-synthesis` (with `data:create-viz`, `docx`/`pptx`) |
| Improve these skills themselves | `skill-forge` |

## Composition rule

Delegate. This suite never reinvents planning, TDD, code review, statistics, or document
generation — it adds the scientific layer and hands the rest to the existing skill.

## Red flags (stop)

- Optimizing a metric you defined after seeing the data.
- "It worked when I ran it" standing in for a reproducible result.
- An implementation "based on" a paper with no check that it matches the paper.
- Claims broader than the evidence; limitations omitted.
