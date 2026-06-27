---
name: literature-review
description: Use when surveying a field or choosing among competing methods — searches and critically appraises sources, maps the state of the art and gaps, and produces a justified ranked comparison of methods with the oracles an implementation must match.
---

# Literature Review

Find what is known, judge it critically, and decide which method to use — with the
evidence to defend the choice. The output drives implementation, so it must be precise.

## Produce a method dossier

1. **Search.** Use `deep-research` to fan out across sources; cover seminal work, recent
   state of the art, and dissenting results. Record queries so the search is reproducible.
2. **Appraise.** For each source, note its claim, evidence quality, sample or benchmark,
   and limitations. Distinguish strong results from weak or unreplicated ones.
3. **Map.** Synthesize the state of the art and the **gaps** — what is unsolved or contested.
4. **Compare and rank.** Lay competing methods side by side against explicit criteria
   (accuracy, assumptions, cost, robustness, fit to your problem). Rank them and **state
   the recommended method with the reason it wins** for this context.
5. **Extract oracles.** Pull the equations, algorithms, hyperparameters, and reported
   numbers the chosen method specifies — these become the test oracles for
   `faithful-implementation`.

Output: a **method dossier** — appraised sources, a state-of-the-art and gap map, a ranked
comparison with the decision, and the extracted oracles.

## Composes with

- `deep-research` for the search and adversarial verification of claims.
- The dossier's oracles feed `faithful-implementation`; its decision feeds `research-design`.
- For argument-driven or primary-source work, defer source criticism to
  `argumentation-and-sources`.

## Domain lenses

- **ML/AI:** prefer results with released code and reported variance; note benchmark leakage.
- **Computational science:** capture the governing equations and validation cases.
- **Data science:** capture identification assumptions and estimator definitions.

## Red flags (stop)

- A method chosen by popularity or recency rather than fit and evidence.
- Citing a claim without recording the evidence behind it.
- No gap analysis — a review that only summarizes cannot justify new work.
