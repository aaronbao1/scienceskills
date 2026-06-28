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
2. **Generate candidates.** Use `writing-skills` (or `skill-creator`) to draft two or three
   variant versions of the SKILL.md, each addressing the weaknesses differently. Create each
   in an isolated worktree via `using-git-worktrees` so runs never collide.
3. **Run on the benchmark slice.** For the skill's `eval/benchmarks/<skill>/tasks.yaml`,
   dispatch one agent per (version, task) that adopts that version's SKILL.md and performs
   the task. Score each task in the range 0 to 1:
   - `ground_truth` tasks: score with the harness scorer (`eval.harness.score`) and mark
     them critical — a regression on a verifiable task blocks promotion.
   - `judge` tasks: dispatch a panel of at least three judge agents that score the output
     against `eval/rubrics/<skill>.md`; blend the dimension scores with `eval.harness.blend`
     and average the panel.
4. **A/B tournament.** For each task, dispatch judge agents to compare the incumbent's and
   the candidate's outputs head-to-head and record the winner.
5. **Gate and propose.** Score on the **held-out gate split only** — the `split: gate`
   tasks the loop never mined or generated against — pairing incumbent and candidate on the
   same tasks and seeds. Collect per-(task, seed) scores into a results JSON and run
   `python3 -m eval.harness.forge results.json`. It builds the paired held-out deltas and
   promotes only on **statistical significance** (bootstrap CI lower bound above zero and a
   paired permutation p below the Bonferroni-corrected alpha for the number of candidates),
   with no critical-task regression. Present the proposal and the evidence to your human
   partner. Promote only on approval — then replace the SKILL.md and `git tag` the new
   version so the prior one is always one `git checkout` away.

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
