---
name: humanities-inquiry
description: Use for interpretive or qualitative research — close reading, hermeneutics, historiography, theoretical framing, and qualitative coding — where the goal is a defensible interpretation rather than an empirical measurement.
---

# Humanities Inquiry

Interpretive research asks what something means, not what value it takes. Rigor here is the
defensibility of the reading, the fit of the method, and honesty about your own position —
not statistical significance.

## Frame the inquiry

1. **Question.** What text, artifact, practice, or period are you interpreting, and what
   interpretive question are you asking of it?
2. **Method.** Choose the interpretive method that fits — close reading, hermeneutics,
   historiography, discourse analysis, qualitative coding — and say why it fits this material.
3. **Theoretical frame.** Name the lens (a critical, historical, or theoretical tradition)
   you read through, and what it foregrounds and hides.
4. **Evidence.** Ground every claim in specific passages, sources, or observations, with
   source criticism from `argumentation-and-sources`. An interpretation with no anchor is
   assertion.
5. **Reflexivity and positionality.** State your standpoint and how it shapes the reading;
   name rival interpretations and why yours is better supported.
6. **Ethics.** Address consent, representation, and harm when working with human subjects,
   communities, or sensitive material.

Output: a framed interpretation with its method, evidence, and acknowledged limits.

## Composes with

- `argumentation-and-sources` for source criticism and for stress-testing the argument.
- `research-synthesis` downstream to write up the interpretation with calibrated claims.
- This is the interpretive counterpart to `research-design`; use it instead for non-empirical
  work. `scientific-rigor` still governs honesty and reasoning.

## Red flags (stop)

- An interpretation with no textual or archival anchor.
- A reading that ignores the strongest rival interpretation.
- Positionality and ethics omitted when the material demands them.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/humanities-inquiry/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot humanities-inquiry`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight humanities-inquiry` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
