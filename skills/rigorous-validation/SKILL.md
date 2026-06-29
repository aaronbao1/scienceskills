---
name: rigorous-validation
description: Use when results exist and must be validated before they are believed — checks reproducibility, statistical validity, robustness, baselines, and leakage and bias, and red-teams your own findings.
---

# Rigorous Validation

A result is not a result until you have tried to break it. Validate the end product, not
just unit correctness, before any claim is made.

## The validation pass

1. **Reproduce.** Re-run from a clean state with fixed seeds and a captured environment. A
   result you cannot reproduce is not yet a result.
2. **Baselines.** Compare against trivial and strong baselines. An effect with no baseline
   is uninterpretable.
3. **Ablate.** Remove each claimed component and confirm the effect tracks it.
4. **Statistics.** Test significance with appropriate methods; report effect sizes and
   intervals; control multiple comparisons; check power. Delegate to `data:statistical-analysis`.
5. **Robustness.** Sweep seeds, splits, and reasonable settings. Report where the result
   holds and where it breaks.
6. **Leakage and bias.** Check train/test (or source/derived) separation, label leakage,
   and selection bias. This is where most false results come from.
7. **Red-team.** Ask "how could this number be wrong, inflated, or fabricated?" and test
   the most likely failure before publishing it.

Output: a **validation report** — claims, the evidence for each, the threats addressed,
and residual risks.

## Composes with

- `data:statistical-analysis` and `data:validate-data` for the statistics and QA.
- `/code-review` and `superpowers:requesting-code-review` for code correctness.
- `superpowers:verification-before-completion` as the evidence-before-claims gate.
- For argument-driven work, validity is argument soundness — use `argumentation-and-sources`.

## Domain lenses

- **ML/AI:** seed variance, data leakage, train/test contamination, metric gaming.
- **Computational science:** convergence, conservation, sensitivity to discretization.
- **Data science:** identification assumptions, confounding, robustness of the estimate.

## Red flags (stop)

- A single-run number reported as the result.
- "Significant" without a stated test, correction, or effect size.
- No leakage check on a surprisingly good result.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/rigorous-validation/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot rigorous-validation`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight rigorous-validation` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
