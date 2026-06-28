# Rubric — deep-reasoning

Score an output produced under this skill on each dimension, 0–4.

- **Decomposition (weight 0.20):** The problem is restated precisely and broken into the right sub-problems.
- **Path diversity (weight 0.20):** When escalated, parallel paths use genuinely different framings, not paraphrases.
- **Verification rigor (weight 0.25):** The leading answer is checked by an independent flaw-finding pass, step by step.
- **Calibration (weight 0.20):** Confidence matches the evidence; uncertainties and what-would-change-it are stated.
- **Efficiency (weight 0.15):** Reasoning effort is matched to difficulty — neither under- nor over-thought.

Blended score = Σ(weight × dimension / 4). Trusting same-chain self-critique instead of an
independent verification pass scores 0 on verification rigor.
