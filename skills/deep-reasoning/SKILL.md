---
name: deep-reasoning
description: Use for any genuinely hard problem that deserves more than a single pass — runs a budget-aware tiered deliberation protocol (triage, decompose, parallel paths, independent verification, search) that matches reasoning effort to difficulty.
---

# Deep Reasoning

A harness for thinking hard, well. It scales deliberation to the difficulty of the problem:
most problems resolve in one careful pass; the hardest get parallel reasoning, independent
verification, and search. The discipline is to spend effort where it changes the answer and to
stop when the answer is settled.

## The protocol (escalate only as needed; stop when settled)

**0. Triage.** Restate the problem precisely. Classify it (type, difficulty, stakes) and name
what would make an answer wrong. Pick a starting tier — do not bring heavy machinery to an easy
problem, because over-thinking degrades easy answers and wastes effort.

**1. Single deliberate pass.** Decompose into sub-problems. Reason step by step. Make every
assumption explicit. Do one quick self-check for obvious errors. Most problems end here.

**2. Parallel paths.** If the pass is low-confidence or the stakes are high, generate several
**independent** reasoning paths that take genuinely different framings — not paraphrases of one
approach. Dispatch them with `dispatching-parallel-agents` or the Workflow tool. If they
**converge**, confidence rises; if they **diverge**, that is a signal to verify and escalate,
not to majority-vote a possibly-wrong consensus.

**3. Independent verification.** For the leading candidate, run a separate verification pass
whose only job is to **find the flaw** — check each step, not just the conclusion. Do not rely
on the same chain to critique itself; a chain is unreliable at catching its own errors. Kill
candidates that fail verification.

**4. Search, debate, or decompose (hardest only).** Choose the tool that fits: branch and
**backtrack** (tree-of-thought) when the problem needs exploration; **debate** distinct
positions and adjudicate when it is a contested judgment call; **decompose** to the smallest
hard sub-problem, solve it, and compose when it is deeply multi-step.

**5. Calibrated answer.** Give the answer with an honest confidence — state what you are unsure
about and do not be falsely certain — the reasoning that decided it, and **what would change
it**. Stop when the answer is settled or the budget is spent. Never present a first-pass guess
as a verified result.

## Composes with

- `dispatching-parallel-agents` and the Workflow tool for the parallel-paths and verification
  steps. General-purpose: invoke this for any hard reasoning task, in or out of research.
- For a runnable, tested aggregation of the parallel paths (self-consistency plus a calibrated
  confidence and an explicit escalate-or-stop signal), use `deep-reasoning-ultra`.

## Red flags (stop)

- Bringing parallel paths and search to a problem a single careful pass would settle.
- Majority-voting a consensus when the paths might be uniformly wrong.
- Trusting a chain's critique of its own reasoning instead of an independent check.
- Presenting an answer with false confidence and no statement of what would change it.
