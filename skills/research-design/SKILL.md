---
name: research-design
description: Use when starting a research project or defining what to test — frames the question, states falsifiable hypotheses and success metrics, and plans experiments and ablations before any data is seen.
---

# Research Design

Decide what you are testing, why it matters, and how you will know you were right —
before you touch data or code. Good design is what makes later results trustworthy.

## Produce a research spec

Work through, in order:

1. **Question.** One sentence. What do you want to know? Narrow it until it is answerable.
2. **Novelty.** What is already known (from `literature-review`), and what specifically is
   new here? If nothing is new, say so.
3. **Hypotheses and predictions.** State each hypothesis and the concrete, **falsifiable**
   prediction it makes — the observation that would prove it wrong.
4. **Metrics.** Fix the primary metric and any secondary metrics now, and define how each
   is computed. The primary metric is chosen before seeing results — no moving the goalposts.
5. **Design.** Conditions, controls, baselines, and the **ablations** that isolate each
   claimed contribution. Decide sample size or compute budget and the stopping rule up front.
6. **Analysis plan.** State the analyses before running them (preregistration mindset) so
   results cannot be reverse-engineered into hypotheses.
7. **Threats.** List confounds, leakage risks, and validity threats, and how the design
   controls each.

Output: a **research spec** that downstream work consumes.

## Composes with

- `superpowers:brainstorming` upstream when the idea is still vague.
- The research spec feeds `superpowers:writing-plans`, which turns it into an
  implementation plan; `faithful-implementation` then supplies the literature-derived
  test oracles.
- For interpretive or non-empirical work, use `humanities-inquiry` instead.

## Domain lenses

- **ML/AI:** fix the eval set, metric, and seeds; pre-commit one ablation per component.
- **Computational science:** state the validation case (analytical or known-good) the
  method must reproduce.
- **Data science:** state the estimand and identification assumptions before modeling.

## Red flags (stop)

- A hypothesis with no observation that could falsify it.
- Choosing or changing the primary metric after seeing results.
- No baselines or ablations — you will not be able to attribute any effect.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/research-design/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot research-design`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight research-design` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
