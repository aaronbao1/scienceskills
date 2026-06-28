# deep-reasoning + deep-reasoning-ultra Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two standalone, general-purpose reasoning skills to the `scienceskills` plugin — `deep-reasoning` (a budget-aware tiered deliberation protocol) and `deep-reasoning-ultra` (the protocol plus a deterministic `eval/harness/consensus.py` aggregation core).

**Architecture:** Both skills are markdown `SKILL.md` files describing the same tiered protocol (triage → single pass → parallel paths → independent verification → search/debate/decompose → calibrated answer), decoupled from `scientific-rigor` and not science-framed. `deep-reasoning` orchestrates existing tools and aggregates by judgment. `deep-reasoning-ultra` adds a TDD'd Python module (`consensus.py`) that tallies parallel-path answers, blends verifier verdicts, computes a calibrated confidence, and emits an escalate/stop signal, runnable as `python3 -m eval.harness.consensus`. Each skill ships a rubric, a benchmark slice, and a test, following the existing suite pattern; the parametrized `tests/test_skills_valid.py` auto-covers their lint.

**Tech Stack:** Python 3.9+, pytest, PyYAML; markdown skills.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- New harness modules start with `from __future__ import annotations`; importable as `eval.harness.<module>`; `consensus` runnable as `python3 -m eval.harness.consensus <file>`.
- Every new `SKILL.md` frontmatter has `name` == its directory name and a non-empty `description` ≤ 1024 chars; body starts with an H1; no literal `TODO`/`TBD`/`FIXME` tokens.
- **Both skills MUST be standalone:** the SKILL.md body must NOT contain the string `scientific-rigor` and must not be science-framed (the tests assert the absence of `scientific-rigor`). Do not edit the router in `skills/scientific-rigor/SKILL.md` or `CLAUDE.md`.
- Every benchmark `tasks.yaml` loads via `eval.harness.tasks.load_tasks`.
- Skill prose is the product: use the EXACT content from each task verbatim. Sentence case.
- DRY, YAGNI, TDD, frequent commits. Never implement on `main`/`master` without consent — work on a feature branch.

---

### Task 1: `consensus.py` — deterministic aggregation core

**Files:**
- Create: `eval/harness/consensus.py`
- Test: `tests/test_consensus.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `normalize_answer(s: str) -> str`; `tally_answers(answers: list[str]) -> dict` (keys `top`, `counts`, `agreement_rate`, `n`; raises `ValueError` on empty); `@dataclass(frozen=True) Aggregate(answer, agreement_rate, verifier_pass_rate, confidence, converged, escalate)`; `aggregate(answers, verifier_verdicts=None, agreement_threshold=0.6, confidence_threshold=0.7) -> Aggregate`; `render(agg) -> str`; `main(argv=None) -> int` (exit 0 if converged else 1), runnable as `python3 -m eval.harness.consensus <results.json>`.

- [ ] **Step 1: Write the failing test**

`tests/test_consensus.py`:
```python
import json
import pytest
from eval.harness.consensus import (
    normalize_answer,
    tally_answers,
    aggregate,
    Aggregate,
    main,
)


def test_normalize_answer():
    assert normalize_answer("  The  Answer ") == "the answer"


def test_tally_answers_majority():
    t = tally_answers(["A", "a", "B"])
    assert t["top"] == "a"
    assert t["n"] == 3
    assert t["agreement_rate"] == pytest.approx(2 / 3)


def test_tally_answers_empty_raises():
    with pytest.raises(ValueError):
        tally_answers([])


def test_aggregate_converges_on_high_agreement():
    agg = aggregate(["x", "x", "x"], None)
    assert isinstance(agg, Aggregate)
    assert agg.agreement_rate == 1.0
    assert agg.confidence == 1.0
    assert agg.converged
    assert not agg.escalate


def test_aggregate_escalates_on_disagreement():
    agg = aggregate(["x", "y", "z"], None, agreement_threshold=0.6, confidence_threshold=0.7)
    assert not agg.converged
    assert agg.escalate


def test_aggregate_blends_verifier_pass_rate():
    agg = aggregate(["x", "x", "x", "x"], [False, False, False, True])
    assert agg.verifier_pass_rate == pytest.approx(0.25)
    assert agg.confidence == pytest.approx(0.625)
    assert not agg.converged
    assert agg.escalate


def test_main_exit_codes(tmp_path):
    converged = tmp_path / "c.json"
    converged.write_text(json.dumps({"answers": ["x", "x", "x"]}), encoding="utf-8")
    assert main([str(converged)]) == 0

    diverged = tmp_path / "d.json"
    diverged.write_text(json.dumps({"answers": ["x", "y", "z"]}), encoding="utf-8")
    assert main([str(diverged)]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_consensus.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.consensus'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/consensus.py`:
```python
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


def normalize_answer(s: str) -> str:
    """Lowercase, strip, and collapse whitespace so equivalent answers group together."""
    return " ".join(str(s).strip().lower().split())


def tally_answers(answers: list[str]) -> dict:
    """Tally normalized answers into the top answer, counts, agreement rate, and n."""
    if not answers:
        raise ValueError("no answers")
    counts: dict[str, int] = {}
    for a in answers:
        key = normalize_answer(a)
        counts[key] = counts.get(key, 0) + 1
    top = max(counts, key=lambda k: counts[k])
    n = len(answers)
    return {"top": top, "counts": counts, "agreement_rate": counts[top] / n, "n": n}


@dataclass(frozen=True)
class Aggregate:
    answer: str
    agreement_rate: float
    verifier_pass_rate: float | None
    confidence: float
    converged: bool
    escalate: bool


def aggregate(
    answers: list[str],
    verifier_verdicts: list[bool] | None = None,
    agreement_threshold: float = 0.6,
    confidence_threshold: float = 0.7,
) -> Aggregate:
    """Combine parallel-path answers (+ optional verifier verdicts) into a calibrated decision."""
    tally = tally_answers(answers)
    agreement = tally["agreement_rate"]
    if verifier_verdicts:
        vpr: float | None = sum(1 for v in verifier_verdicts if v) / len(verifier_verdicts)
        confidence = 0.5 * agreement + 0.5 * vpr
    else:
        vpr = None
        confidence = agreement
    converged = agreement >= agreement_threshold and (vpr is None or vpr >= 0.5)
    escalate = confidence < confidence_threshold
    return Aggregate(
        answer=tally["top"],
        agreement_rate=agreement,
        verifier_pass_rate=vpr,
        confidence=confidence,
        converged=converged,
        escalate=escalate,
    )


def render(agg: Aggregate) -> str:
    vpr = "n/a" if agg.verifier_pass_rate is None else f"{agg.verifier_pass_rate:.2f}"
    return (
        "# Consensus\n\n"
        f"- Answer: {agg.answer}\n"
        f"- Agreement rate: {agg.agreement_rate:.2f}\n"
        f"- Verifier pass rate: {vpr}\n"
        f"- Confidence: {agg.confidence:.2f}\n"
        f"- Converged: {'yes' if agg.converged else 'no'}\n"
        f"- Escalate: {'yes' if agg.escalate else 'no'}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.consensus")
    parser.add_argument("results", help="path to a reasoning results JSON file")
    args = parser.parse_args(argv)
    data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    agg = aggregate(
        data["answers"],
        data.get("verifier_verdicts"),
        data.get("agreement_threshold", 0.6),
        data.get("confidence_threshold", 0.7),
    )
    print(render(agg))
    return 0 if agg.converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_consensus.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/consensus.py tests/test_consensus.py
git commit -m "feat: consensus aggregation core for deep-reasoning-ultra"
```

---

### Task 2: `deep-reasoning` skill + rubric + benchmark slice

**Files:**
- Create: `skills/deep-reasoning/SKILL.md`
- Create: `eval/rubrics/deep-reasoning.md`
- Create: `eval/benchmarks/deep-reasoning/tasks.yaml`
- Test: `tests/test_deep_reasoning.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the standalone `deep-reasoning` skill.

- [ ] **Step 1: Write the failing test**

`tests/test_deep_reasoning.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "deep-reasoning" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "deep-reasoning.md"
TASKS = ROOT / "eval" / "benchmarks" / "deep-reasoning" / "tasks.yaml"


def test_skill_is_standalone_and_tiered():
    body = SKILL.read_text(encoding="utf-8")
    assert "dispatching-parallel-agents" in body
    assert "triage" in body.lower()
    assert "verification" in body.lower()
    assert "scientific-rigor" not in body


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("decomposition", "path diversity", "verification rigor", "calibration"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_deep_reasoning.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/deep-reasoning/SKILL.md`:
```markdown
---
name: deep-reasoning
description: Use for any genuinely hard problem that deserves more than a single pass — runs a budget-aware tiered deliberation protocol (triage, decompose, parallel paths, independent verification, search) that matches reasoning effort to difficulty.
---

# Deep Reasoning

A harness for thinking hard, well. It scales deliberation to the difficulty of the problem:
most problems resolve in one careful pass; the hardest get parallel reasoning, independent
verification, and search. The discipline is to spend effort where it changes the answer and to
stop when the answer is settled.

## The protocol (escalate only as needed; stop when settled)

**0. Triage.** Restate the problem precisely. Classify it (type, difficulty, stakes) and name
what would make an answer wrong. Pick a starting tier — do not bring heavy machinery to an easy
problem, because over-thinking degrades easy answers and wastes effort.

**1. Single deliberate pass.** Decompose into sub-problems. Reason step by step. Make every
assumption explicit. Do one quick self-check for obvious errors. Most problems end here.

**2. Parallel paths.** If the pass is low-confidence or the stakes are high, generate several
**independent** reasoning paths that take genuinely different framings — not paraphrases of one
approach. Dispatch them with `dispatching-parallel-agents` or the Workflow tool. If they
**converge**, confidence rises; if they **diverge**, that is a signal to verify and escalate,
not to majority-vote a possibly-wrong consensus.

**3. Independent verification.** For the leading candidate, run a separate verification pass
whose only job is to **find the flaw** — check each step, not just the conclusion. Do not rely
on the same chain to critique itself; a chain is unreliable at catching its own errors. Kill
candidates that fail verification.

**4. Search, debate, or decompose (hardest only).** Choose the tool that fits: branch and
**backtrack** (tree-of-thought) when the problem needs exploration; **debate** distinct
positions and adjudicate when it is a contested judgment call; **decompose** to the smallest
hard sub-problem, solve it, and compose when it is deeply multi-step.

**5. Calibrated answer.** Give the answer with an honest confidence — state what you are unsure
about and do not be falsely certain — the reasoning that decided it, and **what would change
it**. Stop when the answer is settled or the budget is spent. Never present a first-pass guess
as a verified result.

## Composes with

- `dispatching-parallel-agents` and the Workflow tool for the parallel-paths and verification
  steps. General-purpose: invoke this for any hard reasoning task, in or out of research.
- For a runnable, tested aggregation of the parallel paths (self-consistency plus a calibrated
  confidence and an explicit escalate-or-stop signal), use `deep-reasoning-ultra`.

## Red flags (stop)

- Bringing parallel paths and search to a problem a single careful pass would settle.
- Majority-voting a consensus when the paths might be uniformly wrong.
- Trusting a chain's critique of its own reasoning instead of an independent check.
- Presenting an answer with false confidence and no statement of what would change it.
```

`eval/rubrics/deep-reasoning.md`:
```markdown
# Rubric — deep-reasoning

Score an output produced under this skill on each dimension, 0–4.

- **Decomposition (weight 0.20):** The problem is restated precisely and broken into the right sub-problems.
- **Path diversity (weight 0.20):** When escalated, parallel paths use genuinely different framings, not paraphrases.
- **Verification rigor (weight 0.25):** The leading answer is checked by an independent flaw-finding pass, step by step.
- **Calibration (weight 0.20):** Confidence matches the evidence; uncertainties and what-would-change-it are stated.
- **Efficiency (weight 0.15):** Reasoning effort is matched to difficulty — neither under- nor over-thought.

Blended score = Σ(weight × dimension / 4). Trusting same-chain self-critique instead of an
independent verification pass scores 0 on verification rigor.
```

`eval/benchmarks/deep-reasoning/tasks.yaml`:
```yaml
- id: tier_selection
  kind: judge
  prompt: >
    For each of these, state which reasoning tier you would start at and why: (a) "what is 12
    percent of 250?"; (b) "design a cache-eviction policy for a read-heavy workload with
    occasional bursts"; (c) "is this informal proof of the irrationality of sqrt(2) correct?"
    Judged on efficiency and decomposition per the rubric.
- id: independent_verification
  kind: judge
  prompt: >
    You have a candidate answer to a hard combinatorics problem produced by one reasoning
    chain. Describe how you would verify it so the check does not inherit the chain's blind
    spots, and why self-critique by the same chain is insufficient.
- id: percent_check
  kind: ground_truth
  prompt: >
    Reason carefully and report 12 percent of 250 as a single number.
  scorer: contains
  expected: "30"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_deep_reasoning.py tests/test_skills_valid.py -v`
Expected: PASS (contract, rubric, benchmark tests pass; `deep-reasoning` lints clean under the parametrized skill test).

- [ ] **Step 5: Commit**

```bash
git add skills/deep-reasoning eval/rubrics/deep-reasoning.md eval/benchmarks/deep-reasoning tests/test_deep_reasoning.py
git commit -m "feat: deep-reasoning skill + rubric + benchmark slice"
```

---

### Task 3: `deep-reasoning-ultra` skill + rubric + benchmark slice

**Files:**
- Create: `skills/deep-reasoning-ultra/SKILL.md`
- Create: `eval/rubrics/deep-reasoning-ultra.md`
- Create: `eval/benchmarks/deep-reasoning-ultra/tasks.yaml`
- Test: `tests/test_deep_reasoning_ultra.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; the `consensus.py` from Task 1 is the runtime dependency referenced by the SKILL.md (`eval.harness.consensus`). Auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the standalone `deep-reasoning-ultra` skill.

- [ ] **Step 1: Write the failing test**

`tests/test_deep_reasoning_ultra.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "deep-reasoning-ultra" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "deep-reasoning-ultra.md"
TASKS = ROOT / "eval" / "benchmarks" / "deep-reasoning-ultra" / "tasks.yaml"


def test_skill_references_consensus_core_and_is_standalone():
    body = SKILL.read_text(encoding="utf-8")
    assert "eval.harness.consensus" in body
    assert "dispatching-parallel-agents" in body
    assert "scientific-rigor" not in body


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("path diversity", "verification rigor", "aggregation soundness", "calibration"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_deep_reasoning_ultra.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/deep-reasoning-ultra/SKILL.md`:
```markdown
---
name: deep-reasoning-ultra
description: Use for the hardest, highest-stakes reasoning problems — the deep-reasoning protocol plus a deterministic aggregation core (self-consistency, calibrated confidence, escalate/stop) that turns parallel reasoning paths into an auditable decision.
---

# Deep Reasoning Ultra

The maximal-rigor version of `deep-reasoning`. It runs the same tiered protocol, but the
aggregation of parallel reasoning is a **deterministic, tested mechanism** rather than a
judgment call: `python3 -m eval.harness.consensus` tallies the paths, blends in verifier
verdicts, computes a calibrated confidence, and returns an explicit escalate-or-stop signal.

## The protocol

Follow the `deep-reasoning` tiers (triage → single pass → parallel paths → independent
verification → search/debate/decompose → calibrated answer). The difference is in how Tiers 2
and 3 aggregate:

1. **Generate paths.** Dispatch N independent reasoning paths (genuinely different framings)
   with `dispatching-parallel-agents` or the Workflow tool. Collect each path's final answer.
2. **Verify.** Dispatch independent verifier agents whose job is to find the flaw in the leading
   answer; collect a pass or fail verdict from each.
3. **Aggregate (deterministic).** Write the answers and verdicts to a results JSON and run
   `python3 -m eval.harness.consensus results.json`. It returns the top answer, the agreement
   rate, the verifier pass rate, a calibrated confidence, and `converged` / `escalate`.
   - Results JSON: `{"answers": ["...", ...], "verifier_verdicts": [true, false, ...],
     "agreement_threshold": 0.6, "confidence_threshold": 0.7}` (thresholds optional).
4. **Act on the signal.** If `converged` and not `escalate`, stop and report the answer with its
   confidence. If `escalate`, go to the next tier (more, again-diverse paths, then
   search/debate/decompose) and re-aggregate. Never override a `not converged` signal with a
   confident answer — low agreement or failed verification means the problem is not settled.
5. **Calibrated answer.** Report the answer, the consensus numbers (agreement, verifier pass
   rate, confidence), and what would change it.

## Composes with

- `dispatching-parallel-agents` and the Workflow tool (paths and verifiers).
- `eval.harness.consensus` — the deterministic aggregation, self-consistency, calibrated
  confidence, and escalate-or-stop signal.

## Red flags (stop)

- Reporting an answer the consensus marks `not converged` as if it were settled.
- Running one reasoning path and calling it consensus — aggregation needs several independent paths.
- Letting the same chain both answer and verify.
- Skipping the escalation the `escalate` signal calls for because the first answer "looks right".
```

`eval/rubrics/deep-reasoning-ultra.md`:
```markdown
# Rubric — deep-reasoning-ultra

Score an output produced under this skill on each dimension, 0–4.

- **Decomposition (weight 0.15):** Problem restated precisely and split into the right sub-problems.
- **Path diversity (weight 0.20):** Parallel paths use genuinely different framings, not paraphrases.
- **Verification rigor (weight 0.25):** Independent flaw-finding verification, step by step.
- **Aggregation soundness (weight 0.25):** The consensus signal (agreement, verifier pass rate, escalate) is used correctly to decide stop-or-escalate.
- **Calibration (weight 0.15):** Reported confidence matches the consensus numbers; uncertainties stated.

Blended score = Σ(weight × dimension / 4). Reporting a "not converged" result as settled scores
0 on aggregation soundness.
```

`eval/benchmarks/deep-reasoning-ultra/tasks.yaml`:
```yaml
- id: use_consensus_signal
  kind: judge
  prompt: >
    Five independent paths produced answers [A, A, B, A, C] and three verifiers on the leading
    answer A returned [pass, fail, pass]. Walk through what eval.harness.consensus reports
    (agreement, verifier pass rate, confidence, converged, escalate) and what you do next.
    Judged on aggregation soundness per the rubric.
- id: escalate_decision
  kind: ground_truth
  prompt: >
    The agreement rate is 0.4 and there are no verifier verdicts, with a confidence threshold of
    0.7. Does the consensus core signal escalate? Answer with one lowercase word: yes or no.
  scorer: exact
  expected: "yes"
- id: not_one_path
  kind: judge
  prompt: >
    Explain why running a single long reasoning chain and reporting its answer is NOT the same
    as the consensus this skill requires, and what minimum you need for a meaningful aggregate.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_deep_reasoning_ultra.py tests/test_skills_valid.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/deep-reasoning-ultra eval/rubrics/deep-reasoning-ultra.md eval/benchmarks/deep-reasoning-ultra tests/test_deep_reasoning_ultra.py
git commit -m "feat: deep-reasoning-ultra skill + rubric + benchmark slice"
```

---

### Task 4: Full-suite green + validate + consensus dry-run

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified increment (11 skills, 10 slices).

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — all prior tests plus `tests/test_consensus.py` (7), the two new per-skill test files (3 each), and the two extra `test_skills_valid` lint params, all green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0 (now covers eleven skills, including `deep-reasoning` and `deep-reasoning-ultra`).

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (now covers ten benchmark slices).

- [ ] **Step 3: Consensus dry-run (deterministic end-to-end)**

```bash
cat > /tmp/consensus-demo.json <<'JSON'
{"answers": ["42", "42", "42", "41"], "verifier_verdicts": [true, true, false], "confidence_threshold": 0.7}
JSON
python3 -m eval.harness.consensus /tmp/consensus-demo.json; echo "exit=$?"
```
Expected: prints a "# Consensus" block — Answer 42, agreement 0.75, verifier pass rate 0.67, confidence 0.71, Converged yes, Escalate no — and `exit=0`.

```bash
cat > /tmp/consensus-split.json <<'JSON'
{"answers": ["a", "b", "c", "d"]}
JSON
python3 -m eval.harness.consensus /tmp/consensus-split.json; echo "exit=$?"
```
Expected: Converged no, Escalate yes, `exit=1`.

- [ ] **Step 4: Confirm clean tree**

Run: `git status` (expect clean; the `/tmp/*.json` files are outside the repo).

- [ ] **Step 5: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify deep-reasoning skills suite green + consensus dry-run"
```

## Self-Review

**Spec coverage:** §4 `deep-reasoning` → Task 2; §5 `deep-reasoning-ultra` → Task 3; §5.1 `consensus.py` → Task 1; §7 testing + §9 success criteria → Tasks 1–4. §3 protocol is embodied verbatim in both SKILL.md bodies. §8 standalone constraint → enforced by the `assert "scientific-rigor" not in body` checks in both per-skill tests and by NOT editing the router/CLAUDE.md.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new module, skill, rubric, or benchmark (enforced by lint + `test_skills_valid.py`). All code and content steps show complete content.

**Type consistency:** `consensus.py` exposes `normalize_answer`, `tally_answers`, `Aggregate`, `aggregate`, `render`, `main` (Task 1), and the Task 3 SKILL.md references the `python3 -m eval.harness.consensus` entry + the results-JSON shape consistent with `main`/`aggregate`. The dry-run JSON in Task 4 matches that shape. Verified arithmetic for the dry-run: answers ["42","42","42","41"] → agreement 3/4 = 0.75; verdicts [T,T,F] → vpr 2/3 ≈ 0.667; confidence 0.5·0.75 + 0.5·0.667 ≈ 0.708 ≥ 0.7; converged (0.75 ≥ 0.6 and 0.667 ≥ 0.5) = yes; escalate (0.708 < 0.7) = no. The `escalate_decision` ground-truth: agreement 0.4, no verdicts → confidence 0.4 < 0.7 → escalate = yes.
