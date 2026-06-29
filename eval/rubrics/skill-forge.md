# Rubric — skill-forge

Score a forge run on each dimension, 0–4.

- **Evidence quality (weight 0.25):** Weaknesses and gains are concrete and backed by eval results, not impressions.
- **Evaluation rigor (weight 0.25):** Held-out gate split kept disjoint from mine/generate, multi-judge panel, A/B tournament, and variance estimated across seeds — not a single point score.
- **Gating soundness (weight 0.25):** Promotion requires statistical significance (paired bootstrap CI above zero and a Bonferroni-corrected permutation p) and blocks on any critical regression, with human approval.
- **Honesty (weight 0.15):** Regressions and judge disagreement are reported, not hidden.
- **Reversibility (weight 0.10):** The prior version stays recoverable (git tag) after promotion.

Blended score = Σ(weight × dimension / 4). A run that promotes without human approval scores
0 on gating soundness.
