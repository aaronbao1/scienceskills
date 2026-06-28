# deep-reasoning + deep-reasoning-ultra — Design Spec

> **Status:** Design (brainstorming → writing-plans). Decisions locked in conversation 2026-06-27.
> **Date:** 2026-06-27

## 1. Overview

Two standalone, **general-purpose** reasoning skills added to the `scienceskills` plugin —
usable on any hard problem (concepts, ideas, approaches, math, code, strategy), **not**
science-specific and **not** coupled to or routed from `scientific-rigor`:

- **`deep-reasoning`** — a protocol-only skill: a rigorous, budget-aware tiered deliberation
  procedure. It orchestrates existing tools (`dispatching-parallel-agents`, the Workflow
  tool) for the parallel/verify/search steps; aggregation is judgment-based. No new code.
- **`deep-reasoning-ultra`** — the same protocol **plus** a deterministic Python aggregation
  core (`eval/harness/consensus.py`): self-consistency tally, inter-path agreement,
  calibrated confidence, and an escalate/stop signal — TDD'd and CLI-runnable — so the
  aggregation is a real, auditable mechanism rather than a judgment call.

Both follow the suite's skill pattern: `SKILL.md` + `eval/rubrics/<n>.md` +
`eval/benchmarks/<n>/tasks.yaml` + `tests/test_<n>.py`. Both can be improved by `skill-forge`.

### 1.1 Goals
- A reusable harness for **deep, rigorous reasoning** on hard problems, inspired by how
  test-time-compute systems (o1 / o1-pro long reasoning, Gemini Deep Think parallel
  thinking) scale deliberation.
- **Budget-aware tiered escalation**: match reasoning compute to detected difficulty and
  confidence — don't over-think easy problems, do bring the full machinery to hard ones.
- A heavyweight `-ultra` variant whose aggregation/confidence is a tested, deterministic
  mechanism.

### 1.2 Non-goals (YAGNI)
- No coupling to `scientific-rigor` or science framing (explicitly general-purpose).
- No model training / no reward-model training — this orchestrates an existing LLM agent.
- `deep-reasoning` ships no new code (protocol-only by design).
- No fully-autonomous unbounded search — every tier is budget-bounded.

## 2. Locked Decisions

| Decision | Choice |
|---|---|
| Count | Two skills: `deep-reasoning`, `deep-reasoning-ultra` |
| Scope | Standalone, general-purpose; decoupled from `scientific-rigor`; no science framing |
| Placement | In the `scienceskills` plugin (reuses lint/eval/test infra; improvable by skill-forge) |
| Compute model | Budget-aware tiered escalation |
| `-ultra` extra | A deterministic `eval/harness/consensus.py` aggregation core + CLI |

## 3. The reasoning protocol (shared spine)

A tiered escalation. Each tier is bounded; you escalate only when the cheaper tier is
low-confidence or the stakes are high, and you **stop** when converged or the budget is spent.

**Tier 0 — Triage (always, cheap).** Classify the problem (type, difficulty, what would make
an answer wrong, stakes). Pick a starting tier. Restate the problem precisely.

**Tier 1 — Single deliberate pass (default).** Decompose into sub-problems; reason step by
step; make assumptions explicit; do one quick self-check for obvious errors. *Evidence:
deliberate chain-of-thought helps, but over-escalating hurts easy problems ("overthinking")
and wastes budget — so most problems should resolve here.*

**Tier 2 — Parallel paths + self-consistency (escalate if Tier 1 is low-confidence or
stakes are high).** Generate N **independent** reasoning paths that use genuinely different
framings/decompositions (not paraphrases). Aggregate: convergence → confidence; divergence →
escalate. *Evidence: self-consistency/majority vote improves over a single path but
**saturates and can degrade on very hard problems** where the majority is systematically
wrong — so divergence is a signal to escalate, not to blindly majority-vote, and path
**diversity** is what makes it work.*

**Tier 3 — Adversarial verification (escalate on divergence or high stakes).** For the
leading candidate(s), run **independent** verifier passes whose job is to **find the flaw**,
not confirm. Check each reasoning step, not just the final answer. Kill candidates that fail.
*Evidence: a model **self-critiquing its own chain is unreliable at catching its own
errors**; independent verification and step-level (process) checking are markedly more
reliable — "let's verify step by step".*

**Tier 4 — Search / debate / decompose-and-conquer (max, hardest only).** Pick the tool that
fits: tree-of-thought branching with **backtracking** for problems needing exploration;
multi-agent **debate** (assign distinct positions, adjudicate) for contested judgment calls;
recursive **decomposition** (reduce to the smallest hard sub-case, solve, compose) for deep
multi-step problems. *Evidence: ToT/search helps where backtracking matters (puzzles,
planning) at higher cost; debate is **mixed** — helpful via diverse error-catching but
prone to sycophantic agreement, so adjudication quality matters; decomposition is robustly
helpful.*

**Converge — calibrated answer (always).** Output the answer with a **calibrated confidence**
(models are typically overconfident — say what you're unsure about), the decisive reasoning,
and **what would change the answer**. Stop when converged or the budget is exhausted; never
present a Tier-1 guess as a verified result.

**Anti-patterns guarded against:** over-thinking simple problems; majority-voting a wrong
consensus; trusting same-chain self-critique; sycophantic debate; unbounded search cost;
overconfidence.

## 4. `deep-reasoning` (protocol-only)

`skills/deep-reasoning/SKILL.md` operationalizes §3 as guidance. The parallel/verify/search
steps say to dispatch agents via `dispatching-parallel-agents` / the Workflow tool;
aggregation is the reasoning agent's judgment (read the N paths, judge convergence). No code.

- **Composes with:** `dispatching-parallel-agents`, the Workflow tool (parallel paths,
  verifiers). General-purpose — invoked for any hard reasoning task.
- **Rubric dimensions:** decomposition, path diversity, verification rigor, calibration,
  efficiency (right-sized compute). Weights sum to 1.0.
- **Benchmark slice:** judge tasks exercising tier selection, independent verification, and
  calibration; plus one `ground_truth` task with a verifiable answer.

## 5. `deep-reasoning-ultra` (protocol + consensus core)

`skills/deep-reasoning-ultra/SKILL.md` runs the same protocol but makes aggregation a
**deterministic, tested mechanism**: after dispatching N path agents and verifier agents, it
collects their final answers + verdicts into a JSON and runs
`python3 -m eval.harness.consensus results.json`, which returns the aggregated answer, the
agreement rate, the verifier pass rate, a calibrated confidence, and an **escalate/stop**
decision. The skill escalates tiers based on that signal.

### 5.1 The consensus core — `eval/harness/consensus.py` (deterministic, TDD'd)
- `normalize_answer(s: str) -> str` — lowercase, strip, collapse whitespace (for grouping
  equivalent final answers).
- `tally_answers(answers: list[str]) -> dict` → `{top, counts, agreement_rate, n}` where
  `agreement_rate = count(top)/n`.
- `@dataclass(frozen=True) Aggregate(answer, agreement_rate, verifier_pass_rate, confidence,
  converged, escalate)`.
- `aggregate(answers, verifier_verdicts=None, agreement_threshold=0.6,
  confidence_threshold=0.7) -> Aggregate`:
  - tally → `top`, `agreement_rate`.
  - `verifier_pass_rate = mean(verdicts)` if verdicts given, else `None`.
  - `confidence = agreement_rate` if no verdicts, else `0.5*agreement_rate +
    0.5*verifier_pass_rate`.
  - `converged = agreement_rate >= agreement_threshold and (verifier_pass_rate is None or
    verifier_pass_rate >= 0.5)`.
  - `escalate = confidence < confidence_threshold`.
- CLI `main(argv) -> int`: reads a results JSON (`{answers: [...], verifier_verdicts: [...]
  | null, agreement_threshold?, confidence_threshold?}`), prints a markdown summary, exit 0
  if `converged` else 1. Runnable as `python3 -m eval.harness.consensus <file>`.

- **Composes with:** `dispatching-parallel-agents` / Workflow (paths + verifiers) and
  `eval.harness.consensus` (deterministic aggregation). The skill body references
  `eval.harness.consensus`.
- **Rubric dimensions:** decomposition, path diversity, verification rigor, aggregation
  soundness (uses the consensus signal correctly), calibration. Weights sum to 1.0.
- **Benchmark slice:** judge tasks + one `ground_truth` (e.g., a gate-style arithmetic check
  of the escalate rule), with a `contains`/`exact` scorer.

## 6. Repo layout additions
```
skills/deep-reasoning/SKILL.md
skills/deep-reasoning-ultra/SKILL.md
eval/harness/consensus.py                 # ultra only
eval/rubrics/deep-reasoning.md
eval/rubrics/deep-reasoning-ultra.md
eval/benchmarks/deep-reasoning/tasks.yaml
eval/benchmarks/deep-reasoning-ultra/tasks.yaml
tests/test_consensus.py
tests/test_deep_reasoning.py
tests/test_deep_reasoning_ultra.py
```

## 7. Testing strategy
- `consensus.py` → TDD (deterministic units: tally, aggregate, escalate, CLI exit codes).
- Skill prose → validated by `tests/test_skills_valid.py` lint (auto-covers both new skills)
  + each skill's contract/rubric/benchmark test.
- End-to-end: a `consensus` dry-run on a sample results JSON (converged + escalate cases).

## 8. Integration with the suite
- Both skills are **standalone**: no reference to `scientific-rigor`, no science framing.
  They do not edit the router or `CLAUDE.md` (the suite's master prompt stays as-is; these
  are general-purpose additions a user invokes directly or another skill calls when a problem
  is genuinely hard).
- Both lint clean, get benchmark slices, and are improvable by `skill-forge` like any skill.
- Harness now covers 11 skills / 10 benchmark slices after this lands.

## 9. Success criteria
1. `deep-reasoning` and `deep-reasoning-ultra` present, lint clean, each with rubric +
   benchmark slice + contract test; neither references `scientific-rigor` or science.
2. `consensus.py` TDD'd; `python3 -m eval.harness.consensus <file>` returns a correct
   aggregate + escalate/stop decision (converged → exit 0, escalate → exit 1).
3. Full suite green; `cli lint` (11 skills) + `validate` (10 slices) exit 0.

## 10. Implementation order (for the plan)
1. `consensus.py` core (TDD).
2. `deep-reasoning` skill + rubric + slice + test.
3. `deep-reasoning-ultra` skill + rubric + slice + test (references `eval.harness.consensus`).
4. Full-suite green + validate + consensus dry-run.

## 11. Evidence basis (from the deep-research pass)

A deep-research pass (27 primary sources, 129 claims extracted, 25 adversarially verified,
24 confirmed / 1 refuted) confirmed the technique landscape and the tiered design:
- **Compute-optimal scaling** — matching test-time compute to difficulty beats uniform max
  ("Scaling LLM Test-Time Compute Optimally", arXiv:2408.03314; OpenAI o1). → Tier-0 triage
  + escalation, not always-max.
- **Step-level (process) verification** beats outcome-only checking ("Let's Verify Step by
  Step", arXiv:2305.20050). → Tier 3 checks each step.
- **Self-correction is unreliable** without an external signal ("LLMs Cannot Self-Correct
  Reasoning Yet", arXiv:2310.01798; "When Can LLMs Actually Correct Their Own Mistakes",
  TACL 2024). → Tier 3 uses **independent** verifiers, not same-chain self-critique.
- **Best-of-N with verifiers / aggregation** ("Free Process Rewards…", arXiv:2408.15240;
  OVM/PRM-guided search, arXiv:2502.00271). → Tier 2 + the `-ultra` consensus core.
- **Search over reasoning** and **debate / self-refine** (composable-models LLM debate;
  Self-Refine, arXiv:2303.17651) — useful but cost- and adjudication-sensitive. → Tier 4,
  chosen by fit.
- **Refuted by the verification pass:** the claim that verifier-guided beam search reliably
  underperforms repeated sampling at large sample sizes (arXiv:2502.00271) was killed
  (2/3 refute) — contested, so the design treats verification as a tier, not a universal win.
