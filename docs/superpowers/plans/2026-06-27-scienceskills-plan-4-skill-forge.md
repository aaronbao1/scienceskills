# scienceskills Plan 4 — skill-forge (self-improvement loop) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `skill-forge`, the self-improvement engine: a deterministic Python core that blends scores, applies a promotion gate, tallies A/B tournaments, and renders a human-facing promotion proposal — plus the `skill-forge` SKILL.md that orchestrates the full loop (mine → generate candidates → run + judge → gate → human-approved promotion) using Claude Code's agent tools.

**Architecture:** The loop's *deterministic* mechanics live in new Python modules under `eval/harness/` (`blend`, `gate`, `tournament`, `forge_report`, `forge`), each TDD'd with no LLM or network dependency. The loop's *non-deterministic* steps (running a candidate skill on a task, LLM-judging quality, A/B comparison) are performed at runtime by agents that the `skill-forge` SKILL.md dispatches; their scores are collected into a results JSON that `python3 -m eval.harness.forge` consumes to produce a gated promotion proposal. This is the same separation the rest of the suite uses: unit-test the math, orchestrate the judgment. Git provides version history and rollback (the skill `git tag`s on promotion).

**Tech Stack:** Python 3.9+, pytest, PyYAML; markdown skill.

## Staging roadmap (this is Plan 4 of 4 — the final plan)

- Plans 1–3 (merged): scaffold + harness + 8 skills (backbone, 5 lifecycle, 2 humanities) + benchmark slices + rubrics.
- **Plan 4 (this doc):** `skill-forge` deterministic core (`blend`, `gate`, `tournament`, `forge_report`, `forge`) + the `skill-forge` skill (+ rubric + slice). Completes the 9-skill suite and satisfies the last router/`CLAUDE.md` forward-reference.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- Every new harness module starts with `from __future__ import annotations`.
- New harness modules are importable as `eval.harness.<module>`; `forge` is runnable as `python3 -m eval.harness.forge <results.json>`.
- The `skill-forge` SKILL.md frontmatter `name == skill-forge`; body H1; `description` ≤ 1024 chars; no `TODO`/`TBD`/`FIXME`; sentence case.
- The benchmark `tasks.yaml` loads via `eval.harness.tasks.load_tasks`.
- DRY, YAGNI, TDD, frequent commits. Never implement on `main`/`master` without consent — work on a feature branch.

---

### Task 1: `blend.py` — rubric weights + score blending

**Files:**
- Create: `eval/harness/blend.py`
- Test: `tests/test_blend.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_rubric_weights(rubric_text: str) -> dict[str, float]`; `blend_dimension_scores(weights: dict[str, float], scores: dict[str, float]) -> float`; `overall_score(task_scores: list[float]) -> float`; `RubricError(ValueError)`.

- [ ] **Step 1: Write the failing test**

`tests/test_blend.py`:
```python
import pytest
from eval.harness.blend import (
    parse_rubric_weights,
    blend_dimension_scores,
    overall_score,
    RubricError,
)

RUBRIC = """# Rubric — demo
- **Alpha thing (weight 0.50):** ...
- **Beta thing (weight 0.50):** ...
"""


def test_parse_rubric_weights():
    w = parse_rubric_weights(RUBRIC)
    assert w == {"alpha thing": 0.5, "beta thing": 0.5}


def test_parse_rubric_weights_rejects_bad_sum():
    bad = "- **A (weight 0.50):** x\n- **B (weight 0.40):** y\n"
    with pytest.raises(RubricError):
        parse_rubric_weights(bad)


def test_parse_rubric_weights_rejects_empty():
    with pytest.raises(RubricError):
        parse_rubric_weights("# no dimensions here\n")


def test_blend_dimension_scores():
    weights = {"alpha thing": 0.5, "beta thing": 0.5}
    scores = {"alpha thing": 4.0, "beta thing": 2.0}
    # 0.5*(4/4) + 0.5*(2/4) = 0.5 + 0.25 = 0.75
    assert blend_dimension_scores(weights, scores) == pytest.approx(0.75)


def test_blend_missing_dimension_raises():
    with pytest.raises(RubricError):
        blend_dimension_scores({"a": 1.0}, {})


def test_blend_out_of_range_raises():
    with pytest.raises(RubricError):
        blend_dimension_scores({"a": 1.0}, {"a": 5.0})


def test_overall_score():
    assert overall_score([1.0, 0.0, 0.5]) == pytest.approx(0.5)


def test_overall_score_empty_raises():
    with pytest.raises(ValueError):
        overall_score([])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_blend.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.blend'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/blend.py`:
```python
from __future__ import annotations

import re

_DIM_RE = re.compile(r"\*\*(.+?)\s*\(weight\s+([0-9.]+)\)\s*:\*\*")


class RubricError(ValueError):
    """Raised when a rubric cannot be parsed or its weights are invalid."""


def parse_rubric_weights(rubric_text: str) -> dict[str, float]:
    """Extract {dimension (lowercased): weight} from a rubric's markdown."""
    weights: dict[str, float] = {}
    for match in _DIM_RE.finditer(rubric_text):
        weights[match.group(1).strip().lower()] = float(match.group(2))
    if not weights:
        raise RubricError("no weighted dimensions found")
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise RubricError(f"weights sum to {total}, expected 1.0")
    return weights


def blend_dimension_scores(weights: dict[str, float], scores: dict[str, float]) -> float:
    """Blend 0-4 dimension scores by weight into a [0, 1] value."""
    total = 0.0
    for dim, weight in weights.items():
        if dim not in scores:
            raise RubricError(f"missing score for dimension '{dim}'")
        value = scores[dim]
        if not 0 <= value <= 4:
            raise RubricError(f"score for '{dim}' out of range 0-4: {value}")
        total += weight * (value / 4.0)
    return total


def overall_score(task_scores: list[float]) -> float:
    """Mean of per-task [0, 1] scores."""
    if not task_scores:
        raise ValueError("no task scores")
    return sum(task_scores) / len(task_scores)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_blend.py -v`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/blend.py tests/test_blend.py
git commit -m "feat: forge score blending (rubric weights + overall)"
```

---

### Task 2: `gate.py` — promotion gate

**Files:**
- Create: `eval/harness/gate.py`
- Test: `tests/test_gate.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `@dataclass(frozen=True) PromotionDecision(promote: bool, reason: str)`; `decide_promotion(incumbent_overall: float, candidate_overall: float, per_task: list[dict], margin: float = 0.02) -> PromotionDecision`. Each `per_task` dict has keys `task_id`, `incumbent`, `candidate`, and optional `critical` (bool).

- [ ] **Step 1: Write the failing test**

`tests/test_gate.py`:
```python
from eval.harness.gate import decide_promotion, PromotionDecision


def _task(tid, inc, cand, critical=False):
    return {"task_id": tid, "incumbent": inc, "candidate": cand, "critical": critical}


def test_promotes_on_clear_gain():
    d = decide_promotion(0.70, 0.80, [_task("t1", 0.7, 0.8)], margin=0.02)
    assert isinstance(d, PromotionDecision)
    assert d.promote


def test_rejects_insufficient_gain():
    d = decide_promotion(0.80, 0.805, [_task("t1", 0.8, 0.805)], margin=0.02)
    assert not d.promote
    assert "insufficient" in d.reason


def test_rejects_critical_regression_even_with_gain():
    per_task = [_task("t1", 0.5, 0.9), _task("crit", 1.0, 0.0, critical=True)]
    d = decide_promotion(0.75, 0.90, per_task, margin=0.02)
    assert not d.promote
    assert "crit" in d.reason


def test_boundary_exactly_margin_promotes():
    d = decide_promotion(0.80, 0.82, [_task("t1", 0.8, 0.82)], margin=0.02)
    assert d.promote
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_gate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.gate'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/gate.py`:
```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    reason: str


def decide_promotion(
    incumbent_overall: float,
    candidate_overall: float,
    per_task: list[dict],
    margin: float = 0.02,
) -> PromotionDecision:
    """Promote only on a clear overall gain with no critical-task regression."""
    regressions = [
        t["task_id"]
        for t in per_task
        if t.get("critical") and t["candidate"] < t["incumbent"]
    ]
    if regressions:
        return PromotionDecision(False, f"critical regression on: {', '.join(regressions)}")
    delta = candidate_overall - incumbent_overall
    if delta < margin:
        return PromotionDecision(False, f"insufficient gain: +{delta:.3f} < margin {margin}")
    return PromotionDecision(True, f"promote: +{delta:.3f} over incumbent, no critical regression")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_gate.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/gate.py tests/test_gate.py
git commit -m "feat: forge promotion gate (margin + critical-regression block)"
```

---

### Task 3: `tournament.py` — A/B tally

**Files:**
- Create: `eval/harness/tournament.py`
- Test: `tests/test_tournament.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `tally_tournament(verdicts: list[dict]) -> dict` (keys: `candidate_wins`, `incumbent_wins`, `ties`, `candidate_win_rate`); `TournamentError(ValueError)`; constant `VALID_WINNERS`. Each verdict dict has a `winner` in `{"candidate", "incumbent", "tie"}`.

- [ ] **Step 1: Write the failing test**

`tests/test_tournament.py`:
```python
import pytest
from eval.harness.tournament import tally_tournament, TournamentError


def test_tally_counts_and_rate():
    verdicts = [
        {"task_id": "t1", "winner": "candidate"},
        {"task_id": "t2", "winner": "candidate"},
        {"task_id": "t3", "winner": "incumbent"},
        {"task_id": "t4", "winner": "tie"},
    ]
    out = tally_tournament(verdicts)
    assert out["candidate_wins"] == 2
    assert out["incumbent_wins"] == 1
    assert out["ties"] == 1
    assert out["candidate_win_rate"] == pytest.approx(0.5)


def test_invalid_winner_raises():
    with pytest.raises(TournamentError):
        tally_tournament([{"task_id": "t1", "winner": "nobody"}])


def test_empty_is_zero_rate():
    out = tally_tournament([])
    assert out["candidate_win_rate"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tournament.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.tournament'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/tournament.py`:
```python
from __future__ import annotations

VALID_WINNERS = {"candidate", "incumbent", "tie"}


class TournamentError(ValueError):
    """Raised when a tournament verdict is malformed."""


def tally_tournament(verdicts: list[dict]) -> dict:
    """Tally head-to-head verdicts into win/loss/tie counts and a candidate win rate."""
    for verdict in verdicts:
        if verdict.get("winner") not in VALID_WINNERS:
            raise TournamentError(f"invalid winner: {verdict.get('winner')!r}")
    candidate = sum(1 for v in verdicts if v["winner"] == "candidate")
    incumbent = sum(1 for v in verdicts if v["winner"] == "incumbent")
    ties = sum(1 for v in verdicts if v["winner"] == "tie")
    total = len(verdicts)
    return {
        "candidate_wins": candidate,
        "incumbent_wins": incumbent,
        "ties": ties,
        "candidate_win_rate": candidate / total if total else 0.0,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tournament.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/tournament.py tests/test_tournament.py
git commit -m "feat: forge A/B tournament tally"
```

---

### Task 4: `forge_report.py` — promotion proposal renderer

**Files:**
- Create: `eval/harness/forge_report.py`
- Test: `tests/test_forge_report.py`

**Interfaces:**
- Consumes: a `PromotionDecision`-like object with `.promote` and `.reason`.
- Produces: `render_promotion_proposal(skill: str, incumbent_overall: float, candidate_overall: float, decision, tournament: dict, per_task: list[dict]) -> str`.

- [ ] **Step 1: Write the failing test**

`tests/test_forge_report.py`:
```python
from eval.harness.forge_report import render_promotion_proposal
from eval.harness.gate import PromotionDecision


def test_renders_proposal():
    decision = PromotionDecision(True, "promote: +0.100 over incumbent, no critical regression")
    tournament = {"candidate_wins": 3, "incumbent_wins": 1, "ties": 0, "candidate_win_rate": 0.75}
    per_task = [{"task_id": "t1", "incumbent": 0.7, "candidate": 0.8, "critical": True}]
    md = render_promotion_proposal("literature-review", 0.70, 0.80, decision, tournament, per_task)
    assert "# Promotion proposal — literature-review" in md
    assert "PROMOTE" in md
    assert "candidate win rate 0.75" in md
    assert "t1" in md


def test_renders_reject():
    decision = PromotionDecision(False, "insufficient gain: +0.005 < margin 0.02")
    tournament = {"candidate_wins": 1, "incumbent_wins": 1, "ties": 2, "candidate_win_rate": 0.25}
    md = render_promotion_proposal("research-design", 0.80, 0.805, decision, tournament, [])
    assert "REJECT" in md
    assert "insufficient gain" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_forge_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.forge_report'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/forge_report.py`:
```python
from __future__ import annotations


def render_promotion_proposal(
    skill: str,
    incumbent_overall: float,
    candidate_overall: float,
    decision,
    tournament: dict,
    per_task: list[dict],
) -> str:
    """Render a human-facing promotion proposal as markdown."""
    verdict = "PROMOTE" if decision.promote else "REJECT"
    lines = [
        f"# Promotion proposal — {skill}",
        "",
        f"- Incumbent overall: {incumbent_overall:.3f}",
        f"- Candidate overall: {candidate_overall:.3f}",
        f"- Delta: {candidate_overall - incumbent_overall:+.3f}",
        f"- Decision: {verdict} — {decision.reason}",
        "",
        "## A/B tournament",
        (
            f"- candidate wins {tournament['candidate_wins']}, "
            f"incumbent wins {tournament['incumbent_wins']}, "
            f"ties {tournament['ties']} "
            f"(candidate win rate {tournament['candidate_win_rate']:.2f})"
        ),
        "",
        "## Per-task",
        "| task | incumbent | candidate | critical |",
        "| --- | --- | --- | --- |",
    ]
    for t in per_task:
        crit = "yes" if t.get("critical") else "no"
        lines.append(f"| {t['task_id']} | {t['incumbent']:.2f} | {t['candidate']:.2f} | {crit} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_forge_report.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/forge_report.py tests/test_forge_report.py
git commit -m "feat: forge promotion proposal renderer"
```

---

### Task 5: `forge.py` — integrator + CLI

**Files:**
- Create: `eval/harness/forge.py`
- Test: `tests/test_forge.py`

**Interfaces:**
- Consumes: `eval.harness.blend.overall_score`, `eval.harness.gate.decide_promotion`, `eval.harness.tournament.tally_tournament`, `eval.harness.forge_report.render_promotion_proposal`.
- Produces: `content_hash(text: str) -> str` (12-hex); `load_results(path) -> dict`; `evaluate(results: dict) -> tuple` returning `(PromotionDecision, report_markdown)`; `main(argv: list[str] | None = None) -> int` (exit 0 if promote else 1), runnable as `python3 -m eval.harness.forge <results.json>`.

Results JSON shape:
```json
{
  "skill": "literature-review",
  "margin": 0.02,
  "incumbent": {"hash": "abc", "task_scores": [{"task_id": "t1", "score": 0.7, "critical": false}]},
  "candidate": {"hash": "def", "task_scores": [{"task_id": "t1", "score": 0.9, "critical": false}]},
  "tournament": [{"task_id": "t1", "winner": "candidate"}]
}
```

- [ ] **Step 1: Write the failing test**

`tests/test_forge.py`:
```python
import json
from eval.harness.forge import content_hash, evaluate, main
from eval.harness.gate import PromotionDecision


def _results(cand_score, critical=False):
    return {
        "skill": "demo",
        "margin": 0.02,
        "incumbent": {"hash": "i", "task_scores": [{"task_id": "t1", "score": 0.70, "critical": critical}]},
        "candidate": {"hash": "c", "task_scores": [{"task_id": "t1", "score": cand_score, "critical": critical}]},
        "tournament": [{"task_id": "t1", "winner": "candidate"}],
    }


def test_content_hash_stable_and_short():
    h1 = content_hash("hello")
    h2 = content_hash("hello")
    assert h1 == h2
    assert len(h1) == 12
    assert content_hash("world") != h1


def test_evaluate_promotes_on_gain():
    decision, report = evaluate(_results(0.90))
    assert isinstance(decision, PromotionDecision)
    assert decision.promote
    assert "# Promotion proposal — demo" in report


def test_evaluate_rejects_small_gain():
    decision, _ = evaluate(_results(0.705))
    assert not decision.promote


def test_main_exit_codes(tmp_path):
    promote_file = tmp_path / "promote.json"
    promote_file.write_text(json.dumps(_results(0.90)), encoding="utf-8")
    assert main([str(promote_file)]) == 0

    reject_file = tmp_path / "reject.json"
    reject_file.write_text(json.dumps(_results(0.705)), encoding="utf-8")
    assert main([str(reject_file)]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_forge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.forge'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/forge.py`:
```python
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eval.harness.blend import overall_score
from eval.harness.forge_report import render_promotion_proposal
from eval.harness.gate import decide_promotion
from eval.harness.tournament import tally_tournament


def content_hash(text: str) -> str:
    """Stable 12-hex content hash for identifying a skill version."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def load_results(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(results: dict) -> tuple:
    """Blend scores, apply the gate, tally the tournament, render the proposal."""
    skill = results["skill"]
    margin = results.get("margin", 0.02)
    inc_tasks = results["incumbent"]["task_scores"]
    cand_tasks = results["candidate"]["task_scores"]
    inc_overall = overall_score([t["score"] for t in inc_tasks])
    cand_overall = overall_score([t["score"] for t in cand_tasks])

    inc_by_id = {t["task_id"]: t for t in inc_tasks}
    per_task = []
    for ct in cand_tasks:
        it = inc_by_id.get(ct["task_id"])
        if it is None:
            continue
        per_task.append(
            {
                "task_id": ct["task_id"],
                "incumbent": it["score"],
                "candidate": ct["score"],
                "critical": ct.get("critical", False),
            }
        )

    decision = decide_promotion(inc_overall, cand_overall, per_task, margin)
    tournament = tally_tournament(results.get("tournament", []))
    report = render_promotion_proposal(skill, inc_overall, cand_overall, decision, tournament, per_task)
    return decision, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.forge")
    parser.add_argument("results", help="path to a forge results JSON file")
    args = parser.parse_args(argv)
    decision, report = evaluate(load_results(args.results))
    print(report)
    return 0 if decision.promote else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_forge.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/forge.py tests/test_forge.py
git commit -m "feat: forge integrator + CLI (results JSON -> gated proposal)"
```

---

### Task 6: `skill-forge` skill + rubric + benchmark slice

**Files:**
- Create: `skills/skill-forge/SKILL.md`
- Create: `eval/rubrics/skill-forge.md`
- Create: `eval/benchmarks/skill-forge/tasks.yaml`
- Test: `tests/test_skill_forge.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`; auto-covered by `tests/test_skills_valid.py` lint.
- Produces: the `skill-forge` skill, completing the 9-skill suite.

- [ ] **Step 1: Write the failing test**

`tests/test_skill_forge.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_declares_composition_contract():
    body = SKILL.read_text(encoding="utf-8")
    assert "writing-skills" in body
    assert "deep-research" in body
    assert "eval.harness.forge" in body
    assert "human" in body.lower()


def test_rubric_has_core_dimensions():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "reversibility"):
        assert dim in text


def test_benchmark_slice_loads_with_ground_truth():
    tasks = load_tasks(TASKS)
    assert len(tasks) >= 2
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skill_forge.py -v`
Expected: FAIL — `FileNotFoundError` (files absent).

- [ ] **Step 3: Write the skill, rubric, and benchmark files**

`skills/skill-forge/SKILL.md`:
```markdown
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
5. **Gate and propose.** Collect the scores and verdicts into a results JSON and run
   `python3 -m eval.harness.forge results.json`. It blends scores, applies the promotion gate
   (a margin of improvement and no critical regression), and renders a promotion proposal.
   Present the proposal and the evidence to your human partner. Promote only on approval —
   then replace the SKILL.md and `git tag` the new version so the prior one is always one
   `git checkout` away.

## Results JSON shape

`{"skill", "margin", "incumbent": {"hash", "task_scores": [{"task_id", "score", "critical"}]},
"candidate": {...}, "tournament": [{"task_id", "winner": "candidate|incumbent|tie"}]}`

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
```

`eval/rubrics/skill-forge.md`:
```markdown
# Rubric — skill-forge

Score a forge run on each dimension, 0–4.

- **Evidence quality (weight 0.25):** Weaknesses and gains are concrete and backed by eval results, not impressions.
- **Evaluation rigor (weight 0.25):** Ground-truth anchored, multi-judge panel, A/B tournament — not a single score.
- **Gating soundness (weight 0.25):** Promotion respects the margin and blocks on any critical regression, with human approval.
- **Honesty (weight 0.15):** Regressions and judge disagreement are reported, not hidden.
- **Reversibility (weight 0.10):** The prior version stays recoverable (git tag) after promotion.

Blended score = Σ(weight × dimension / 4). A run that promotes without human approval scores
0 on gating soundness.
```

`eval/benchmarks/skill-forge/tasks.yaml`:
```yaml
- id: gate_arithmetic
  kind: ground_truth
  prompt: >
    Incumbent overall score is 0.80, candidate is 0.805, the promotion margin is 0.02, and
    no task regressed. Should the candidate be promoted? Answer with one lowercase word:
    yes or no.
  scorer: contains
  expected: "no"
- id: design_fair_eval
  kind: judge
  prompt: >
    Describe how you would evaluate a candidate version of the literature-review skill so
    the comparison is fair and hard to game: what to anchor on, how many judges, and what
    would block promotion. Judged on evaluation rigor and gating soundness per the rubric.
- id: reject_reward_hacking
  kind: judge
  prompt: >
    A candidate skill scores higher only because the benchmark task was edited to match its
    output. Explain why this must be rejected and how the loop should prevent it.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skill_forge.py tests/test_skills_valid.py -v`
Expected: PASS (contract, rubric, benchmark tests pass; `skill-forge` lints clean under the parametrized skill test).

- [ ] **Step 5: Commit**

```bash
git add skills/skill-forge eval/rubrics/skill-forge.md eval/benchmarks/skill-forge tests/test_skill_forge.py
git commit -m "feat: skill-forge skill + rubric + benchmark slice"
```

---

### Task 7: Full-suite green + validate + forge dry-run

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified, complete 9-skill suite.

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — all prior tests plus the five new harness test files and the `skill-forge` per-skill test and lint param, all green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0 (now covers nine skills).

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (now covers eight benchmark slices).

- [ ] **Step 3: Forge dry-run (deterministic end-to-end)**

Write a sample results file and run the forge entry point to confirm the gated proposal renders end-to-end:

```bash
cat > /tmp/forge-demo.json <<'JSON'
{
  "skill": "literature-review",
  "margin": 0.02,
  "incumbent": {"hash": "i", "task_scores": [{"task_id": "rank_methods", "score": 0.70, "critical": false}]},
  "candidate": {"hash": "c", "task_scores": [{"task_id": "rank_methods", "score": 0.85, "critical": false}]},
  "tournament": [{"task_id": "rank_methods", "winner": "candidate"}]
}
JSON
python3 -m eval.harness.forge /tmp/forge-demo.json; echo "exit=$?"
```
Expected: prints a "# Promotion proposal — literature-review" markdown block with Decision: PROMOTE, and `exit=0`.

- [ ] **Step 4: Confirm clean tree**

Run: `git status` (expect clean; `/tmp/forge-demo.json` is outside the repo).

- [ ] **Step 5: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify skill-forge suite green + forge dry-run"
```

## Self-Review

**Spec coverage (design spec §3.4 + §5):** the deterministic eval/loop core (§5: blend → gate → tournament → proposal) → Tasks 1–5; the orchestrating `skill-forge` skill that drives mine → generate → run/judge → gate → human-approved promotion using Claude Code's agent tools → Task 6; the live run/judge are orchestrated by the skill rather than hard-coded in Python, because LLM judging is non-deterministic — the Python layer unit-tests every piece of math and gating around it. Version history/rollback is delegated to git (`git tag` on promotion), per §5 step 5. This completes the 9-skill suite and satisfies the last router/`CLAUDE.md` forward-reference (`skill-forge`).

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new module, skill, rubric, or benchmark. All code and content steps show complete content.

**Type consistency:** `forge.py` imports `overall_score` (blend), `decide_promotion`/`PromotionDecision` (gate), `tally_tournament` (tournament), and `render_promotion_proposal` (forge_report) — each defined in Tasks 1–4 with the exact signatures used in Task 5. The results JSON shape in Task 5's `evaluate`, in the Task 6 SKILL.md, and in the Task 7 dry-run are identical. The `skill-forge` test assertions (`writing-skills`, `deep-research`, `eval.harness.forge`, `human`; rubric dimensions; ground_truth task) all match the SKILL.md, rubric, and `tasks.yaml` content verbatim.
