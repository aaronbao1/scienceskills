# Rubric — rigorous-validation

Score an output produced under this skill on each dimension, 0–4.

- **Reproducibility (weight 0.25):** Clean re-run, fixed seeds, captured environment.
- **Statistical validity (weight 0.25):** Right test, effect sizes and intervals, multiple-comparison control.
- **Robustness (weight 0.20):** Seeds, splits, and settings swept; where it holds and breaks is reported.
- **Leakage and bias (weight 0.20):** Separation and selection checked; surprising results red-teamed.
- **Honesty (weight 0.10):** Residual risks and negative findings reported.

Blended score = Σ(weight × dimension / 4). A surprising result with no leakage check scores
0 on leakage and bias.
