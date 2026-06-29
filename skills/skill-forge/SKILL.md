---
name: skill-forge
description: Use to improve the research skills themselves — runs the self-improvement loop that mines weaknesses, generates candidate skill versions, evaluates them with judges and A/B tournaments, and proposes a human-approved promotion.
---

# Skill Forge

The engine that makes this suite self-improving. It evolves one skill at a time and never
promotes a change without measured evidence and your approval. The deterministic scoring,
gating, and reporting live in Python (`python3 -m eval.harness.forge`); the
non-deterministic steps — running a skill on a task, judging quality — are run by dispatched
agents.

## The cycle (one target skill)

1. **Mine.** Gather concrete weaknesses and new best-practices for the target skill from
   its eval history, recent session transcripts, and `deep-research`. Turn them into a short
   list of specific, testable improvements.
2. **Generate candidates (reflective mutation).** Do not draft from scratch. Feed the proposer
   the FAILED transcripts/traces from the mine step plus the rubric and judge feedback, and use
   `writing-skills` to express each fix as a structured line edit that attributes a specific
   failure to a specific line of the SKILL.md — `{old, new, reason}`. Apply the edits
   deterministically with `eval.harness.mutation` (a candidate cannot blindly rewrite the whole
   document or target an ambiguous line). Produce two or three such candidates in isolated
   worktrees via `using-git-worktrees`, and carry them on an instance-wise Pareto frontier
   (`eval.harness.pareto`) rather than always keeping the best-on-aggregate — aggregate-best
   selection collapses to a local optimum after one round.
3. **Run on the benchmark slice.** For the skill's `eval/benchmarks/<skill>/tasks.yaml`,
   dispatch one agent per (version, task) that adopts that version's SKILL.md and performs
   the task. Score each task in the range 0 to 1:
   - `ground_truth` tasks: score with the harness scorer (`eval.harness.score`) and mark
     them critical — a regression on a verifiable task blocks promotion.
   - `judge` tasks: dispatch a panel of at least three judge agents **from disjoint model
     families, none from the candidate-generator's family** (a same-family judge can reward its
     own house style — a reward-hacking channel). Run them at/near temperature 0, **sanitize any
     candidate-controlled text before it enters the judge template** (a content-free or
     delimiter-injecting output can otherwise hijack the score), score against
     `eval/rubrics/<skill>.md`, blend the dimension scores with `eval.harness.blend`, and take
     the panel majority. A disjoint-family panel reduces — but does not eliminate — shared judge
     bias, so keep the deterministic ground-truth tasks as the non-judge tripwire.
4. **A/B tournament.** For each task, dispatch judge agents to compare the incumbent's and
   the candidate's outputs head-to-head **in both orders**. A side wins only if it wins in both
   orders; otherwise score a tie — order-swapped scoring stops position bias from manufacturing a
   win. Flag any comparison the winning side won while being materially longer (possible verbosity
   bias) for the human reviewer.
5. **Gate and propose.** Score on the **held-out gate split only** — the `split: gate`
   tasks the loop never mined or generated against — pairing incumbent and candidate on the
   same tasks and seeds. Collect per-(task, seed) scores into a results JSON and run
   `python3 -m eval.harness.forge results.json`. It builds the paired held-out deltas and
   promotes only on **statistical significance** (bootstrap CI lower bound above zero and a
   paired permutation p below the Bonferroni-corrected alpha for the number of candidates),
   with no critical-task regression. Present the proposal and the evidence to your human
   partner. Promote only on approval — then replace the SKILL.md and `git tag` the new
   version so the prior one is always one `git checkout` away.

## Loop control (across rounds)

The single-skill cycle runs many times; these guards keep it honest over rounds and are gated by
`python3 -m eval.harness.loop_control <history.json>`:

- **Accumulate the eval anchor.** Keep a permanent seed of human/ground-truth tasks in the
  benchmark every round; never replace it with self-generated transcripts. `eval.harness.anchor`
  flags a dropped seed.
- **Halt on over-optimization.** Track the judge/dev (proxy) score and the deterministic
  ground-truth (gold) score each round. When the proxy rises while gold stalls or drops, HALT —
  the loop is Goodharting the judge. Cap consecutive judge-only promotions. Edit-distance or KL
  penalties alone do not fix this, so the halt watches the proxy/gold divergence directly.
- **Refresh on a statistical trigger.** When the dev-set and held-out gate performance diverge
  significantly (`eval.harness.anchor` reuses the gate's paired significance test), regenerate
  fresh ground-truth tasks and bound the rounds run against any fixed set.

## Results JSON shape

`{"skill", "alpha", "n_candidates", "seed", "incumbent": {"hash", "runs": [{"task_id",
"split", "seed", "score", "critical"}]}, "candidate": {...}, "tournament": [{"task_id",
"winner": "candidate|incumbent|tie"}]}`

## Composes with

- `deep-research` (mining), `writing-skills` and `anthropic-skills:skill-creator` (candidates),
  `using-git-worktrees` (isolation), `dispatching-parallel-agents` and the Workflow tool
  (parallel running and judging), and `eval.harness.forge` (deterministic gating and report).

## Red flags (stop)

- Promoting without human approval, or without a measured gain over the incumbent.
- A single judge instead of a panel — one judge is easy to game.
- Editing the benchmark or rubric to make a candidate pass (reward hacking). Improve the
  skill, not the test.
- No rollback path — every promotion must leave the prior version recoverable in git.
- Gating on the dev split, or on a benchmark too small to have power — a sub-noise margin is
  not a real gain. Grow or refresh the held-out set instead.
- Promoting on a raw point-margin without a significance test, or testing several candidates
  without Bonferroni-correcting the threshold.
- A single-order A/B comparison, or a judge panel drawn from one model family (or the candidate's
  own family) — position and self-preference bias can fabricate the margin.
- Feeding raw candidate-controlled text into the judge template without sanitizing it, or trusting
  a judge-only verdict with no deterministic ground-truth tripwire.
