# Rubric — skill-forge

Score a forge run on each dimension, 0–4.

- **Evidence quality (weight 0.25):** Weaknesses and gains are concrete and backed by eval results, not impressions.
- **Evaluation rigor (weight 0.25):** Ground-truth anchored, multi-judge panel, A/B tournament — not a single score.
- **Gating soundness (weight 0.25):** Promotion respects the margin and blocks on any critical regression, with human approval.
- **Honesty (weight 0.15):** Regressions and judge disagreement are reported, not hidden.
- **Reversibility (weight 0.10):** The prior version stays recoverable (git tag) after promotion.

Blended score = Σ(weight × dimension / 4). A run that promotes without human approval scores
0 on gating soundness.
