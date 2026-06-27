# Rubric — faithful-implementation

Score an output produced under this skill on each dimension, 0–4.

- **Faithfulness (weight 0.35):** Does the implementation provably match the source?
  Are equations, reference numbers, and invariants asserted as oracles?
- **Correctness (weight 0.25):** Is the code actually correct and tested (real tests,
  watched to fail first)?
- **Rigor (weight 0.20):** Tolerances justified; edge cases from the source covered;
  divergences investigated rather than hidden.
- **Honesty (weight 0.10):** Fidelity report records matched / diverged / unverifiable
  truthfully, including failures.
- **Creativity (weight 0.10):** Where the source is ambiguous, are reasonable,
  well-justified choices made and documented?

Blended score = Σ(weight × dimension / 4). A submission that edits expected values to
force a pass scores 0 on faithfulness regardless of other dimensions.
