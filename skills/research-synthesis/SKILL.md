---
name: research-synthesis
description: Use when turning validated results into a report, paper, figures, or deck — interprets findings honestly, visualizes them, and writes claims calibrated to the evidence with explicit limitations.
---

# Research Synthesis

Communicate what the evidence supports — no more, no less. The synthesis is where honest
work is most easily undone by overclaiming.

## From results to write-up

1. **Interpret.** State what each validated result means and, equally, what it does not.
   Tie every interpretation to the evidence in the validation report.
2. **Calibrate claims.** Match each claim's strength to its evidence: shown, suggested, or
   speculated. Quantify uncertainty. Cut any claim the evidence does not carry.
3. **Visualize.** Choose figures that show the data honestly — appropriate scales, error
   bars, and baselines; no chart that flatters the result. Delegate to `data:create-viz`.
4. **Limitations.** State the conditions under which the result holds, the threats that
   remain, and what would change the conclusion.
5. **Write.** Produce the artifact (report, paper section, or deck) with claims, evidence,
   and limitations clearly separated.

Output: the write-up plus its figures.

## Composes with

- `data:create-viz` and `data:data-visualization` for figures.
- `anthropic-skills:docx`, `pptx`, `pdf`, and `xlsx` for documents and decks.
- `anthropic-skills:web-artifacts-builder` for interactive results.
- Reads the **validation report** from `rigorous-validation`; never claim beyond it.

## Domain lenses

- **ML/AI:** report variance and the exact eval setup; show baselines beside results.
- **Computational science:** report error bars and the validation case reproduced.
- **Data science:** state the estimand, the assumptions, and what would break the estimate.

## Red flags (stop)

- A claim stronger than the validation report supports.
- A figure with a truncated axis or missing baseline that inflates the effect.
- Limitations omitted because they weaken the story.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/research-synthesis/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot research-synthesis`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight research-synthesis` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
