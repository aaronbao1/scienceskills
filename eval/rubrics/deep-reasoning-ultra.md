# Rubric — deep-reasoning-ultra

Score an output produced under this skill on each dimension, 0–4.

- **Decomposition (weight 0.15):** Problem restated precisely and split into the right sub-problems.
- **Path diversity (weight 0.20):** Parallel paths use genuinely different framings, not paraphrases.
- **Verification rigor (weight 0.25):** Independent flaw-finding verification, step by step.
- **Aggregation soundness (weight 0.25):** The consensus signal (agreement, verifier pass rate, escalate) is used correctly to decide stop-or-escalate.
- **Calibration (weight 0.15):** Reported confidence matches the consensus numbers; uncertainties stated.

Blended score = Σ(weight × dimension / 4). Reporting a "not converged" result as settled scores
0 on aggregation soundness.
