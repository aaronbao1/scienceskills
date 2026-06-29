---
name: argumentation-and-sources
description: Use for evidence and source criticism in argument-driven work — appraising primary and secondary sources, constructing and stress-testing arguments, mapping scholarly debate, and catching fallacies and unsupported leaps.
---

# Argumentation and Sources

In argument-driven scholarship, validity is the soundness of the argument and the quality
of its sources — the counterpart to statistical validation. Build the case, then try to
break it.

## Appraise sources

- **Provenance.** Who produced the source, when, why, and for whom? Distinguish primary
  from secondary; weigh bias, distance from events, and reliability.
- **Corroboration.** Triangulate claims across independent sources; flag a claim that rests
  on a single uncorroborated source.
- **Citation integrity.** Every claim is traceable to a source you have actually examined.

## Build and stress-test the argument

- **Structure.** State the thesis, the premises, and how each premise is supported.
- **Stress-test.** Steelman the strongest counterargument and answer it. Map the scholarly
  debate rather than citing only allies.
- **Fallacy check.** Scan for informal fallacies — appeal to popularity or authority, hasty
  generalization, false dilemma, circularity — and for leaps the evidence does not carry.

Output: a sourced, stress-tested argument with its debate map and residual weaknesses.

## Composes with

- Supplies source criticism to `humanities-inquiry` and `literature-review`.
- For argument-driven work this plays the validation role that `rigorous-validation` plays
  for empirical work; `research-synthesis` writes up the result.

## Red flags (stop)

- A thesis supported only by sources that already agree with it.
- A claim resting on one uncorroborated or unexamined source.
- The strongest counterargument left unaddressed.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/argumentation-and-sources/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot argumentation-and-sources`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight argumentation-and-sources` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
