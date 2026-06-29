---
name: skill-forge
description: Use to improve the research skills themselves — runs a self-contained, log-driven loop that mines insights each skill captured from its own sessions, distills them into a playbook, and proposes human-approved, gated edits to a skill.
---

# Skill Forge

The self-improvement engine for this suite. It is **self-contained**: every target skill captures its own
session insights into a central store under `skills/skill-forge/insights/<skill>/`, and skill-forge turns
those logs into improvements. It evolves one skill at a time and never promotes a durable change without
measured evidence on a held-out benchmark and your approval.

Improvement lives in two layers:
- **Playbook (fast, reversible, no gate).** Distilled heuristics each skill consults at use-time.
- **SKILL.md (slow, gated, rare).** Durable edits, promoted only through the held-out gate + your approval.

## Store

```
skills/skill-forge/insights/<skill>/
  transcripts/<session-id>.jsonl   raw session snapshots (gitignored cache)
  raw.jsonl                        per-session insight records (committed)
  playbook.md                      curated heuristics, bounded, inline vote tags (committed)
  gate-history.jsonl               one line per gate round (committed)
```

## The loop

1. **Capture (in each skill).** At session end, the skill snapshots its transcript and appends a robust,
   generalized insight to `raw.jsonl` (`python3 -m eval.harness.capture`). Behavioral signals only —
   correction/redo, abandonment, approval, hard failure, self-assessed struggle — no judge.
2. **Distill.** Read recent `raw.jsonl` (and `transcripts/` for detail), contrast failures vs successes,
   and curate `playbook.md` with ADD / EDIT / UPVOTE / DOWNVOTE. Keep it **bounded** (default ≤25 entries;
   prune lowest net-vote). Heuristics must be generalized — no project-specifics.
3. **Crystallize.** When a heuristic has earned its keep (net votes ≥4, recurs across ≥3 sessions), express
   it as an attributed line edit `{old, new, reason}` against the target SKILL.md, in 1–2 candidates in
   isolated worktrees (`using-git-worktrees`).
4. **Gate.** Run incumbent vs candidate on the **held-out `gate` split only** (`split: gate` tasks the loop
   never mined against), K seeds, paired on the same tasks/seeds. Collect a results JSON and run
   `python3 -m eval.harness.forge <skill> results.json`. It runs the Goodhart monitor, then promotes only
   when there is **no critical-task regression**, the candidate **wins gold on every seed**, and the mean
   gain **exceeds the incumbent's seed-to-seed noise**. Exit 0 = promote-pending-approval, 1 = reject,
   2 = halt.
5. **Promote.** On pass **and your approval**: replace the SKILL.md, mark the heuristic `crystallized` and
   retire it from the playbook, and `git tag` the new version so the prior one is one `git checkout` away.

## Judging guidance (orchestration, not code)

When a benchmark task is judge-scored: use a panel of ≥3 judges from **disjoint model families, none from
the candidate-generator's family**; compare both A/B orders and count a win only if it wins both; sanitize
candidate-controlled text before it enters the judge template; and always keep deterministic ground-truth
tasks as the non-judge tripwire. A disjoint panel **reduces, not eliminates**, shared bias.

## Results JSON shape

`{"skill", "incumbent": {"hash", "runs": [{"task_id","seed","score","critical","split"}]},
"candidate": {...}, "use_sign_test"?}`

## Composes with

`deep-research` and the captured `raw.jsonl` (mining), `writing-skills` (candidate edits),
`using-git-worktrees` (isolation), `dispatching-parallel-agents` / the Workflow tool (parallel running and
judging), and `eval.harness.forge` (gate + monitor + round log).

## Red flags (stop)

- Promoting without human approval, or without a measured gain over the incumbent on the held-out split.
- Gating on the dev split, on a sub-noise margin, or on a benchmark too small to have power.
- A single judge, a single A/B order, or a judge panel from one family (or the candidate's own family).
- Editing the benchmark/rubric to make a candidate pass — improve the skill, not the test.
- Continuing to crystallize while the monitor reports proxy↑/gold↓ (reward hacking).
- Committing non-generalized, project-specific content into the insight store.
- No rollback path — every promotion must leave the prior version recoverable in git.
