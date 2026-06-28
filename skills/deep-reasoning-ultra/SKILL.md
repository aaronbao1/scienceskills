---
name: deep-reasoning-ultra
description: Use for the hardest, highest-stakes reasoning problems — the deep-reasoning protocol plus a deterministic aggregation core (self-consistency, calibrated confidence, escalate/stop) that turns parallel reasoning paths into an auditable decision.
---

# Deep Reasoning Ultra

The maximal-rigor version of `deep-reasoning`. It runs the same tiered protocol, but the
aggregation of parallel reasoning is a **deterministic, tested mechanism** rather than a
judgment call: `python3 -m eval.harness.consensus` tallies the paths, blends in verifier
verdicts, computes a calibrated confidence, and returns an explicit escalate-or-stop signal.

## The protocol

Follow the `deep-reasoning` tiers (triage → single pass → parallel paths → independent
verification → search/debate/decompose → calibrated answer). The difference is in how Tiers 2
and 3 aggregate:

1. **Generate paths.** Dispatch N independent reasoning paths (genuinely different framings)
   with `dispatching-parallel-agents` or the Workflow tool. Collect each path's final answer.
2. **Verify.** Dispatch independent verifier agents whose job is to find the flaw in the leading
   answer; collect a pass or fail verdict from each.
3. **Aggregate (deterministic).** Write the answers and verdicts to a results JSON and run
   `python3 -m eval.harness.consensus results.json`. It returns the top answer, the agreement
   rate, the verifier pass rate, a calibrated confidence, and `converged` / `escalate`.
   - Results JSON: `{"answers": ["...", ...], "verifier_verdicts": [true, false, ...],
     "agreement_threshold": 0.6, "confidence_threshold": 0.7}` (thresholds optional).
4. **Act on the signal.** If `converged` and not `escalate`, stop and report the answer with its
   confidence. If `escalate`, go to the next tier (more, again-diverse paths, then
   search/debate/decompose) and re-aggregate. Never override a `not converged` signal with a
   confident answer — low agreement or failed verification means the problem is not settled.
5. **Calibrated answer.** Report the answer, the consensus numbers (agreement, verifier pass
   rate, confidence), and what would change it.

## Composes with

- `dispatching-parallel-agents` and the Workflow tool (paths and verifiers).
- `eval.harness.consensus` — the deterministic aggregation, self-consistency, calibrated
  confidence, and escalate-or-stop signal.

## Red flags (stop)

- Reporting an answer the consensus marks `not converged` as if it were settled.
- Running one reasoning path and calling it consensus — aggregation needs several independent paths.
- Letting the same chain both answer and verify.
- Skipping the escalation the `escalate` signal calls for because the first answer "looks right".
