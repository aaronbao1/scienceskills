---
name: faithful-implementation
description: Use when implementing a method, algorithm, or model from the literature — defines the literature-derived test oracles so TDD proves the code matches the source, and detects divergence from it.
---

# Faithful Implementation

Implementing a method from a paper is not "write code that runs" — it is "write code that
**provably matches the source**". This skill is the *oracle layer*: it decides what each
test must assert so that a passing test means *faithful to the literature*. It plugs into
the existing build loop; it does not replace it.

## The core move: derive oracles before coding

From the method dossier (the `literature-review` output), extract for the method:

- **Equations / update rules** → assertions on intermediate and final values.
- **Reference outputs / reported numbers** → expected values, each with a tolerance.
- **Invariants** → properties that must always hold (conservation, normalization,
  monotonicity, shape, units, symmetry).
- **Edge cases named in the source** → explicit tests.
- **Numerical tolerance** → the allowed error, justified by float precision or the
  reported spread — never chosen just to make a test pass.

Each oracle becomes a failing test *before* implementation.

## Composes with (the contract)

1. `literature-review` produces the **method dossier** carrying the oracles.
2. `superpowers:writing-plans` turns the spec + oracles into a TDD plan; **each oracle
   becomes a task's failing test**.
3. `superpowers:subagent-driven-development` (or `superpowers:executing-plans`) executes
   the plan.
4. `superpowers:test-driven-development` runs each red→green cycle — green now means
   "matches the source", because the test asserts an oracle.
5. `superpowers:systematic-debugging` when a fidelity test fails and the cause is unclear.

You supply the oracles and the fidelity report; the superpowers skills supply the
machinery. This is why "faithful-implementation + writing-plans" and "+
subagent-driven-development" compose without friction.

## Fidelity report

After implementation, record for each oracle: matched / diverged / unverifiable, with the
evidence. A divergence is a result to explain, not to hide. A "better" alternative
implementation discovered mid-build is a `literature-review` decision (re-rank the
methods), not a silent swap.

## Domain lenses

- **Computational science:** tolerance and error analysis; conservation and convergence;
  compare against analytical or known-good solutions.
- **ML/AI:** control seeds; match the reported metric within its confidence interval;
  diff against a reference implementation; watch for data leakage.
- **Data science / statistics:** verify estimator formulas and identification
  assumptions, not just that the code runs.

## Red flags (stop)

- No oracle for a core equation — you are testing that it runs, not that it is right.
- Tolerances chosen to make the test pass rather than derived from the source.
- Divergence from the paper quietly "fixed" by editing the expected value.

## Consult

Before starting, read your playbook of learned heuristics:
`skills/skill-forge/insights/faithful-implementation/playbook.md` (skip if absent).

## Capture (run at session end)

When you finish a task that used this skill, record what happened so skill-forge can learn:

1. Snapshot this session: `python3 -m eval.harness.capture snapshot faithful-implementation`
2. Reflect against the five signals — user correction/redo · abandonment · approval · hard failure
   (tool/hook errors) · self-assessed struggle — then append ONE **generalized** insight (no
   project-specifics): pipe a JSON record to `python3 -m eval.harness.capture insight faithful-implementation` with
   fields `{ts, session_id, context, signals, what_worked, what_failed, lesson, proposed_edit?, confidence}`.

Record the *lesson*, not the incident. If a specific line of this SKILL.md caused a failure, include a
`proposed_edit` of `{old, new, reason}`.
