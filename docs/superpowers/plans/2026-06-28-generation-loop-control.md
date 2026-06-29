# Generation & Loop Control (Tier 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace skill-forge's freeform "draft 2-3 variants" GENERATE step with evidence-grounded reflective mutation (structured, line-targeted edits applied deterministically), and turn the loop-control guards against Goodharting — Pareto-diverse candidate selection, eval-anchor accumulation, proxy/gold over-optimization halt, and statistically-triggered benchmark refresh — from prose norms into enforced deterministic mechanisms.

**Architecture:** Four small pure-stdlib modules under `eval/harness/` — `mutation.py` (apply validated line edits), `pareto.py` (instance-wise non-dominated set), `goodhart.py` (over-optimization halt + judge-only-streak cap), `anchor.py` (seed retention + refresh trigger, reusing Tier-1 `stats.significant_improvement`) — plus a `loop_control.py` integrator with a CLI that composes the guards into one across-rounds decision (analogous to `forge.py`). The skill orchestrates the LLM steps (which traces to mine, what edits to propose); the harness deterministically applies, selects, and gates. Builds on merged Tier 1 (`stats.py`, held-out split) and Tier 2 (judge bias controls). Everything is deterministic (no RNG except the seeded bootstrap reused from Tier 1; no network).

**Tech Stack:** Python 3.9.6 (stdlib only; reuses `eval.harness.stats`; **no numpy/scipy**), pytest, PyYAML; markdown skill.

**Evidence base (with the research caveats baked in):**
- **Reflective, trace-grounded mutation beats freeform/RL** — feed the proposer the failed transcripts + rubric/judge feedback and require each edit to attribute a failure to a specific SKILL.md line. — [GEPA](https://arxiv.org/html/2507.19457v1) (>10pp over MIPROv2, up to 35x fewer rollouts). We enforce the *attribution* discipline (each edit must name the failure it fixes) and apply edits deterministically so a candidate cannot silently rewrite the whole document.
- **Carry candidates on an instance-wise Pareto frontier, not best-on-aggregate** — best-on-aggregate local-optimas after one iteration. — [GEPA](https://arxiv.org/html/2507.19457v1).
- **Ground each candidate in a structured trace summary, never a blank prompt; minibatch for exploration, full held-out for the gate.** — [MIPROv2](https://dspy.ai/api/optimizers/MIPROv2/).
- **Accumulate the eval anchor; never replace it with self-generated data** — replacement diverges (collapse); accumulation bounds test loss. — [Is Model Collapse Inevitable?](https://rylanschaeffer.github.io/content/research/2024_arxiv_is_model_collapse_inevitable/main.html). We enforce seed-retention.
- **Treat the judge/dev score as a Goodhart-able proxy: halt when proxy rises while gold (ground-truth) stalls/drops; cap consecutive judge-only promotions.** — [Scaling Laws for RM Overoptimization](https://arxiv.org/pdf/2210.10760). **Caveat (from our research):** the exact functional form is RL-specific and a multi-round `+β·log k` extension was REFUTED — so we detect divergence empirically (proxy↑ ∧ gold↓ over a window) and bound rounds as a precaution, NOT via any closed-form Goodhart curve, and we do not rely on edit-distance/KL penalties (which the source shows do not fix over-optimization).
- **Refresh the benchmark on a statistical trigger** — compare dev vs held-out gate; when the gap is significant, regenerate ground-truth. — [Benchmark Inflation / Retro-Holdouts](https://arxiv.org/pdf/2410.09247). We reuse Tier-1's paired significance test for the trigger; the specific public-benchmark inflation magnitudes (rated UNCERTAIN / likely non-transferable to a small private eval) are NOT encoded.

## Scope

In scope (the GENERATE step + across-rounds loop control): reflective line-edit application, Pareto-frontier selection, over-optimization halt + judge-only cap, anchor accumulation + refresh trigger, the `loop_control` integrator/CLI, and the skill/rubric/benchmark docs.

**Out of scope:** the single-candidate gate (Tier 1, done); the tournament/judge bias controls (Tier 2, done); actually *running* the proposer LLM or generating real transcripts (the skill's runtime job — this layer validates/applies/selects/gates the artifacts they produce).

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest installed for system `python3` (3.9.6); no venv.
- Standard library only in new harness code; may import `eval.harness.stats`. **No numpy/scipy/third-party deps.**
- Every new harness module starts with `from __future__ import annotations`.
- New harness modules importable as `eval.harness.<module>`; `loop_control` runnable as `python3 -m eval.harness.loop_control <history.json>`.
- **Determinism:** all new functions deterministic; the only randomness is the seeded bootstrap inside `stats.significant_improvement` (seed passed through). Identical input + seed → identical output.
- **Backward compatibility:** do not modify `forge.py`, `gate.py`, `tournament.py`, `stats.py`, `forge_report.py`, `judge_safety.py`, or any existing test. All currently-passing tests (189) must stay green.
- **No overclaim:** skill/rubric prose and code comments must NOT encode a closed-form Goodhart curve, a `+β·log k` multi-round term, or specific public-benchmark inflation magnitudes (all REFUTED/UNCERTAIN in the research). The halt is empirical divergence detection; the refresh trigger reuses the paired significance test.
- The `skill-forge` SKILL.md keeps `name: skill-forge`, one H1, `description` ≤ 1024 chars, no `TODO`/`TBD`/`FIXME`, sentence case, and the substrings `writing-skills`, `deep-research`, `eval.harness.forge`, `human`. The rubric keeps dimensions `evidence quality`, `evaluation rigor`, `gating soundness`, `honesty`, `reversibility` with weights summing to 1.0 (do not change the weights). The benchmark keeps ≥1 `ground_truth` task and ≥1 each of `dev`/`gate` split, loading via `eval.harness.tasks.load_tasks`.
- DRY, YAGNI, TDD, frequent commits. Work on the `generation-loop-control` branch — never `main`.

---

### Task 1: `mutation.py` — reflective, attributed line edits

**Files:**
- Create: `eval/harness/mutation.py`
- Test: `tests/test_mutation.py`

**Interfaces:**
- Consumes: nothing (stdlib).
- Produces: `class MutationError(ValueError)`; `apply_line_edits(text: str, edits: list[dict]) -> str`. Each edit is `{"old": <exact existing line>, "new": <replacement line>, "reason": <non-empty attribution>}`. Each `old` must match exactly one line in `text` (else `MutationError`); a missing/empty `reason` raises `MutationError` (enforces the attribute-each-failure discipline). Empty `edits` returns `text` unchanged.

- [ ] **Step 1: Write the failing test**

`tests/test_mutation.py`:
```python
import pytest
from eval.harness.mutation import apply_line_edits, MutationError

DOC = "# Skill\n\n- Always cite sources.\n- Be concise.\n"


def test_applies_single_attributed_edit():
    edits = [{"old": "- Be concise.", "new": "- Be concise and specific.", "reason": "task t3 was vague"}]
    out = apply_line_edits(DOC, edits)
    assert "- Be concise and specific." in out
    assert "- Always cite sources." in out  # untouched lines preserved


def test_empty_edits_is_noop():
    assert apply_line_edits(DOC, []) == DOC


def test_missing_line_raises():
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Nonexistent line.", "new": "x", "reason": "r"}])


def test_ambiguous_edit_raises():
    doc = "- dup\n- dup\n"
    with pytest.raises(MutationError):
        apply_line_edits(doc, [{"old": "- dup", "new": "- once", "reason": "r"}])


def test_missing_reason_raises():
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Be concise.", "new": "x", "reason": ""}])
    with pytest.raises(MutationError):
        apply_line_edits(DOC, [{"old": "- Be concise.", "new": "x"}])


def test_multiple_edits_apply():
    edits = [
        {"old": "- Always cite sources.", "new": "- Always cite primary sources.", "reason": "t1"},
        {"old": "- Be concise.", "new": "- Be concise and specific.", "reason": "t3"},
    ]
    out = apply_line_edits(DOC, edits)
    assert "- Always cite primary sources." in out
    assert "- Be concise and specific." in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_mutation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.mutation'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/mutation.py`:
```python
from __future__ import annotations


class MutationError(ValueError):
    """Raised when a reflective line edit is malformed or does not match the document."""


def apply_line_edits(text: str, edits: list[dict]) -> str:
    """Apply attributed, line-targeted edits to a skill document.

    Each edit is {"old", "new", "reason"}: `old` must match exactly one line, `reason` must be
    a non-empty attribution of the failure it fixes. Anything else raises MutationError — a
    candidate cannot blindly rewrite or target an ambiguous line.
    """
    lines = text.split("\n")
    for edit in edits:
        if not edit.get("reason"):
            raise MutationError(f"edit missing reason/attribution: {edit!r}")
        old = edit["old"]
        matches = [i for i, line in enumerate(lines) if line == old]
        if not matches:
            raise MutationError(f"no line matches: {old!r}")
        if len(matches) > 1:
            raise MutationError(f"ambiguous edit, {len(matches)} lines match: {old!r}")
        lines[matches[0]] = edit["new"]
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_mutation.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/mutation.py tests/test_mutation.py
git commit -m "feat: reflective attributed line-edit application"
```

---

### Task 2: `pareto.py` — instance-wise Pareto frontier

**Files:**
- Create: `eval/harness/pareto.py`
- Test: `tests/test_pareto.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `dominates(a: list[float], b: list[float]) -> bool` (True iff `a` ≥ `b` on every task and > on at least one; raises `ValueError` on length mismatch); `pareto_front(candidates: dict) -> list` (IDs of candidates not dominated by any other, preserving input order).

- [ ] **Step 1: Write the failing test**

`tests/test_pareto.py`:
```python
import pytest
from eval.harness.pareto import dominates, pareto_front


def test_dominates_basic():
    assert dominates([0.9, 0.9], [0.5, 0.5]) is True
    assert dominates([0.5, 0.5], [0.9, 0.9]) is False
    assert dominates([1.0, 0.0], [0.0, 1.0]) is False  # trade-off: neither dominates
    assert dominates([0.5, 0.5], [0.5, 0.5]) is False  # equal is not strict domination


def test_dominates_length_mismatch_raises():
    with pytest.raises(ValueError):
        dominates([0.5], [0.5, 0.5])


def test_front_keeps_tradeoffs():
    cands = {"A": [1.0, 0.0], "B": [0.0, 1.0], "C": [0.5, 0.5]}
    assert sorted(pareto_front(cands)) == ["A", "B", "C"]  # aggregate-tie, all non-dominated


def test_front_drops_dominated():
    cands = {"A": [0.9, 0.9], "B": [0.5, 0.5], "C": [0.8, 0.95]}
    front = pareto_front(cands)
    assert "B" not in front          # dominated by A
    assert "A" in front and "C" in front  # A vs C is a trade-off


def test_front_single_candidate():
    assert pareto_front({"only": [0.3, 0.7]}) == ["only"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_pareto.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.pareto'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/pareto.py`:
```python
from __future__ import annotations


def dominates(a: list[float], b: list[float]) -> bool:
    """True iff `a` is >= `b` on every task and strictly greater on at least one."""
    if len(a) != len(b):
        raise ValueError("score vectors differ in length")
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def pareto_front(candidates: dict) -> list:
    """IDs of candidates not dominated by any other (instance-wise non-dominated set)."""
    ids = list(candidates)
    return [
        cid
        for cid in ids
        if not any(dominates(candidates[other], candidates[cid]) for other in ids if other != cid)
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_pareto.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/pareto.py tests/test_pareto.py
git commit -m "feat: instance-wise pareto frontier selection"
```

---

### Task 3: `goodhart.py` — over-optimization halt + judge-only cap

**Files:**
- Create: `eval/harness/goodhart.py`
- Test: `tests/test_goodhart.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `overoptimization_halt(rounds: list[dict], lookback: int = 2, eps: float = 1e-9) -> dict` with keys `halt` (bool) and `reason` (str); each round dict has `proxy` (judge/dev score) and `gold` (ground-truth score); halts when proxy is strictly increasing while gold is non-increasing across the last `lookback`+1 rounds. `judge_only_streak_exceeded(promotions: list[str], cap: int = 3) -> bool` (True when the trailing run of `"judge_only"` promotions exceeds `cap`).

- [ ] **Step 1: Write the failing test**

`tests/test_goodhart.py`:
```python
from eval.harness.goodhart import overoptimization_halt, judge_only_streak_exceeded


def _r(p, g):
    return {"proxy": p, "gold": g}


def test_halt_on_proxy_up_gold_down():
    rounds = [_r(0.70, 0.80), _r(0.78, 0.78), _r(0.85, 0.75)]
    out = overoptimization_halt(rounds)
    assert out["halt"] is True
    assert "gold" in out["reason"]


def test_no_halt_when_both_rise():
    rounds = [_r(0.70, 0.70), _r(0.78, 0.75), _r(0.85, 0.80)]
    assert overoptimization_halt(rounds)["halt"] is False


def test_no_halt_insufficient_history():
    assert overoptimization_halt([_r(0.7, 0.8)])["halt"] is False


def test_no_halt_when_proxy_flat():
    rounds = [_r(0.80, 0.80), _r(0.80, 0.78), _r(0.80, 0.75)]
    assert overoptimization_halt(rounds)["halt"] is False  # proxy not strictly rising


def test_judge_only_streak():
    assert judge_only_streak_exceeded(["judge_only"] * 4, cap=3) is True
    assert judge_only_streak_exceeded(["judge_only"] * 3, cap=3) is False
    assert judge_only_streak_exceeded(["judge_only", "ground_truth", "judge_only", "judge_only"], cap=1) is True
    assert judge_only_streak_exceeded(["ground_truth"], cap=0) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_goodhart.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.goodhart'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/goodhart.py`:
```python
from __future__ import annotations


def overoptimization_halt(rounds: list[dict], lookback: int = 2, eps: float = 1e-9) -> dict:
    """Halt when the proxy (judge/dev) score rises while the gold (ground-truth) score stalls/drops.

    Detects divergence empirically over the last `lookback`+1 rounds — no closed-form Goodhart
    curve is assumed. Each round has `proxy` and `gold`.
    """
    if len(rounds) < lookback + 1:
        return {"halt": False, "reason": "insufficient history"}
    window = rounds[-(lookback + 1):]
    proxies = [r["proxy"] for r in window]
    golds = [r["gold"] for r in window]
    proxy_up = all(proxies[i + 1] > proxies[i] + eps for i in range(len(proxies) - 1))
    gold_down = all(golds[i + 1] <= golds[i] + eps for i in range(len(golds) - 1))
    if proxy_up and gold_down:
        return {
            "halt": True,
            "reason": (
                f"proxy rising ({proxies[0]:.3f}->{proxies[-1]:.3f}) while gold "
                f"stalls/drops ({golds[0]:.3f}->{golds[-1]:.3f})"
            ),
        }
    return {"halt": False, "reason": "no proxy/gold divergence"}


def judge_only_streak_exceeded(promotions: list[str], cap: int = 3) -> bool:
    """True when the trailing run of consecutive 'judge_only' promotions exceeds `cap`."""
    streak = 0
    for promotion in reversed(promotions):
        if promotion == "judge_only":
            streak += 1
        else:
            break
    return streak > cap
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_goodhart.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/goodhart.py tests/test_goodhart.py
git commit -m "feat: goodhart over-optimization halt + judge-only-streak cap"
```

---

### Task 4: `anchor.py` — eval-anchor accumulation + refresh trigger

**Files:**
- Create: `eval/harness/anchor.py`
- Test: `tests/test_anchor.py`

**Interfaces:**
- Consumes: `eval.harness.stats.significant_improvement`.
- Produces: `accumulate_anchor(seed_ids: list[str], current_ids: list[str]) -> dict` with keys `intact` (bool) and `missing` (list[str] — seed tasks no longer present); `should_refresh_benchmark(dev_gate_deltas: list[float], alpha: float = 0.05, seed: int = 0) -> dict` with keys `refresh` (bool) and `reason` (str) — refreshes when the dev-minus-gate per-task gap is a significant positive divergence (benchmark inflation), via the Tier-1 paired significance test.

- [ ] **Step 1: Write the failing test**

`tests/test_anchor.py`:
```python
from eval.harness.anchor import accumulate_anchor, should_refresh_benchmark


def test_anchor_intact():
    out = accumulate_anchor(["s1", "s2"], ["s1", "s2", "new1"])
    assert out["intact"] is True
    assert out["missing"] == []


def test_anchor_dropped_seed_detected():
    out = accumulate_anchor(["s1", "s2"], ["s2", "new1"])
    assert out["intact"] is False
    assert out["missing"] == ["s1"]


def test_refresh_when_dev_gate_gap_significant():
    # dev consistently +0.10 over gate on 6 tasks -> significant inflation -> refresh.
    out = should_refresh_benchmark([0.10] * 6)
    assert out["refresh"] is True


def test_no_refresh_when_no_gap():
    out = should_refresh_benchmark([0.0] * 8)
    assert out["refresh"] is False


def test_no_refresh_on_empty():
    assert should_refresh_benchmark([])["refresh"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_anchor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.anchor'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/anchor.py`:
```python
from __future__ import annotations

from eval.harness.stats import significant_improvement


def accumulate_anchor(seed_ids: list[str], current_ids: list[str]) -> dict:
    """Verify the permanent ground-truth seed is still present; report any dropped anchors."""
    present = set(current_ids)
    missing = [s for s in seed_ids if s not in present]
    return {"intact": not missing, "missing": missing}


def should_refresh_benchmark(dev_gate_deltas: list[float], alpha: float = 0.05, seed: int = 0) -> dict:
    """Refresh when dev performance has significantly outrun the held-out gate (benchmark inflation).

    `dev_gate_deltas` is the per-task (dev_score - gate_score). A significant positive gap means
    the dev set no longer reflects held-out reality — regenerate fresh ground-truth tasks.
    """
    if not dev_gate_deltas:
        return {"refresh": False, "reason": "no data"}
    verdict = significant_improvement(dev_gate_deltas, alpha=alpha, seed=seed)
    if verdict.significant:
        return {
            "refresh": True,
            "reason": f"dev-gate gap significant (mean {verdict.mean_delta:+.3f}, p={verdict.p_value:.3f})",
        }
    return {"refresh": False, "reason": f"dev-gate gap not significant (p={verdict.p_value:.3f})"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_anchor.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/anchor.py tests/test_anchor.py
git commit -m "feat: eval-anchor accumulation + statistical benchmark-refresh trigger"
```

---

### Task 5: `loop_control.py` — integrator + CLI

**Files:**
- Create: `eval/harness/loop_control.py`
- Test: `tests/test_loop_control.py`

**Interfaces:**
- Consumes: `eval.harness.goodhart` (`overoptimization_halt`, `judge_only_streak_exceeded`), `eval.harness.anchor` (`accumulate_anchor`, `should_refresh_benchmark`).
- Produces: `loop_decision(history: dict) -> dict` (keys `halt` bool, `goodhart` dict, `judge_only_streak_exceeded` bool, `anchor` dict, `refresh` dict — `halt` is True if the Goodhart divergence fires, OR the judge-only streak is exceeded, OR the anchor is broken); `render_loop_report(decision: dict) -> str`; `main(argv: list[str] | None = None) -> int` (0 = continue, 1 = halt, 2 = bad input), runnable as `python3 -m eval.harness.loop_control <history.json>`.
- History JSON shape: `{"rounds": [{"proxy", "gold"}], "promotions": ["judge_only"|"ground_truth"], "seed_ids": [...], "current_ids": [...], "dev_gate_deltas": [...], "lookback": 2, "judge_only_cap": 3, "alpha": 0.05, "seed": 0}`.

- [ ] **Step 1: Write the failing test**

`tests/test_loop_control.py`:
```python
import json
from eval.harness.loop_control import loop_decision, render_loop_report, main


def _continue_history():
    return {
        "rounds": [{"proxy": 0.70, "gold": 0.70}, {"proxy": 0.78, "gold": 0.76}, {"proxy": 0.85, "gold": 0.82}],
        "promotions": ["ground_truth", "judge_only"],
        "seed_ids": ["s1", "s2"], "current_ids": ["s1", "s2", "n1"],
        "dev_gate_deltas": [0.0] * 8,
    }


def _halt_history():
    h = _continue_history()
    h["rounds"] = [{"proxy": 0.70, "gold": 0.80}, {"proxy": 0.78, "gold": 0.78}, {"proxy": 0.85, "gold": 0.75}]
    return h


def test_continue_decision():
    d = loop_decision(_continue_history())
    assert d["halt"] is False
    assert d["goodhart"]["halt"] is False


def test_halt_on_overoptimization():
    d = loop_decision(_halt_history())
    assert d["halt"] is True
    assert d["goodhart"]["halt"] is True


def test_halt_on_broken_anchor():
    h = _continue_history()
    h["current_ids"] = ["s2", "n1"]  # dropped s1
    d = loop_decision(h)
    assert d["halt"] is True
    assert d["anchor"]["intact"] is False


def test_render_mentions_decision():
    md = render_loop_report(loop_decision(_halt_history()))
    assert "# Loop control" in md
    assert "HALT" in md


def test_main_exit_codes(tmp_path):
    cont = tmp_path / "cont.json"
    cont.write_text(json.dumps(_continue_history()), encoding="utf-8")
    assert main([str(cont)]) == 0

    halt = tmp_path / "halt.json"
    halt.write_text(json.dumps(_halt_history()), encoding="utf-8")
    assert main([str(halt)]) == 1


def test_main_bad_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert main([str(bad)]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_loop_control.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.loop_control'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/loop_control.py`:
```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.harness.anchor import accumulate_anchor, should_refresh_benchmark
from eval.harness.goodhart import judge_only_streak_exceeded, overoptimization_halt


def loop_decision(history: dict) -> dict:
    """Compose the Goodhart halt, judge-only cap, anchor check, and refresh trigger."""
    goodhart = overoptimization_halt(history.get("rounds", []), history.get("lookback", 2))
    streak = judge_only_streak_exceeded(history.get("promotions", []), history.get("judge_only_cap", 3))
    anchor = accumulate_anchor(history.get("seed_ids", []), history.get("current_ids", []))
    refresh = should_refresh_benchmark(
        history.get("dev_gate_deltas", []),
        history.get("alpha", 0.05),
        history.get("seed", 0),
    )
    halt = goodhart["halt"] or streak or not anchor["intact"]
    return {
        "halt": halt,
        "goodhart": goodhart,
        "judge_only_streak_exceeded": streak,
        "anchor": anchor,
        "refresh": refresh,
    }


def render_loop_report(decision: dict) -> str:
    """Render the loop-control decision as markdown."""
    verdict = "HALT" if decision["halt"] else "CONTINUE"
    anchor = decision["anchor"]
    lines = [
        "# Loop control",
        "",
        f"- Decision: {verdict}",
        f"- Goodhart over-optimization: {'HALT' if decision['goodhart']['halt'] else 'ok'} — {decision['goodhart']['reason']}",
        f"- Judge-only streak exceeded: {'yes' if decision['judge_only_streak_exceeded'] else 'no'}",
        f"- Anchor intact: {'yes' if anchor['intact'] else 'no'}"
        + ("" if anchor["intact"] else f" (missing: {', '.join(anchor['missing'])})"),
        f"- Benchmark refresh: {'yes' if decision['refresh']['refresh'] else 'no'} — {decision['refresh']['reason']}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval.harness.loop_control")
    parser.add_argument("history", help="path to a loop-history JSON file")
    args = parser.parse_args(argv)
    try:
        history = json.loads(Path(args.history).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read history file: {exc}", file=sys.stderr)
        return 2
    try:
        decision = loop_decision(history)
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        print(f"error: malformed history: {exc}", file=sys.stderr)
        return 2
    print(render_loop_report(decision))
    return 1 if decision["halt"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_loop_control.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/loop_control.py tests/test_loop_control.py
git commit -m "feat: loop-control integrator + CLI (goodhart halt + anchor + refresh)"
```

---

### Task 6: `skill-forge` skill + rubric + benchmark reflect Tier-3 controls

**Files:**
- Modify: `skills/skill-forge/SKILL.md`
- Modify: `eval/rubrics/skill-forge.md`
- Modify: `eval/benchmarks/skill-forge/tasks.yaml`
- Test: `tests/test_skill_forge_loop.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`.
- Produces: documentation of reflective mutation + loop control + an over-optimization benchmark task.
- Constraint: keep `tests/test_skill_forge.py`, `tests/test_skill_forge_gate.py`, and `tests/test_skill_forge_judge.py` assertions valid (protected substrings; rubric dimensions + weights; ≥1 ground_truth; ≥1 dev and ≥1 gate split; the order-swap and significance tasks).

- [ ] **Step 1: Write the failing test**

`tests/test_skill_forge_loop.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks, split_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_documents_reflective_generation_and_loop_control():
    body = SKILL.read_text(encoding="utf-8").lower()
    assert "reflective" in body
    assert "pareto" in body
    assert "accumulate" in body or "anchor" in body
    assert "halt" in body            # goodhart over-optimization halt
    assert "loop_control" in body    # eval.harness.loop_control
    for needle in ("writing-skills", "deep-research", "eval.harness.forge", "human"):
        assert needle in body


def test_rubric_mentions_generation_grounding_or_overopt():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    assert "reflective" in text or "trace" in text or "over-optim" in text or "goodhart" in text
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "honesty", "reversibility"):
        assert dim in text


def test_benchmark_has_overoptimization_task():
    tasks = load_tasks(TASKS)
    dev, gate = split_tasks(tasks)
    assert dev and gate
    assert any(t.kind == "ground_truth" for t in tasks)
    assert any(t.id == "overoptimization_halt" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skill_forge_loop.py -v`
Expected: FAIL — reflective/pareto/loop_control strings absent; no `overoptimization_halt` task.

- [ ] **Step 3: Edit the skill, rubric, and benchmark**

In `skills/skill-forge/SKILL.md`, replace step 2 ("Generate candidates") with:
```markdown
2. **Generate candidates (reflective mutation).** Do not draft from scratch. Feed the proposer
   the FAILED transcripts/traces from the mine step plus the rubric and judge feedback, and use
   `writing-skills` to express each fix as a structured line edit that attributes a specific
   failure to a specific line of the SKILL.md — `{old, new, reason}`. Apply the edits
   deterministically with `eval.harness.mutation` (a candidate cannot blindly rewrite the whole
   document or target an ambiguous line). Produce two or three such candidates in isolated
   worktrees via `using-git-worktrees`, and carry them on an instance-wise Pareto frontier
   (`eval.harness.pareto`) rather than always keeping the best-on-aggregate — aggregate-best
   selection local-optimas after one round.
```

In `skills/skill-forge/SKILL.md`, add a new section after the "The cycle" section (before "Results JSON shape"):
```markdown
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
```

In `eval/rubrics/skill-forge.md`, replace the "Evidence quality" bullet with:
```markdown
- **Evidence quality (weight 0.25):** Weaknesses and gains are concrete and backed by eval results; candidates are grounded in failed traces via reflective, attributed line edits — not impressions or freeform rewrites.
```

In `eval/rubrics/skill-forge.md`, replace the "Honesty" bullet with:
```markdown
- **Honesty (weight 0.15):** Regressions and judge disagreement are reported, not hidden; the loop halts on proxy/gold over-optimization rather than chasing a Goodharted judge score.
```

In `eval/benchmarks/skill-forge/tasks.yaml`, add this task (keep all existing tasks):
```yaml
- id: overoptimization_halt
  kind: ground_truth
  split: gate
  prompt: >
    Over three rounds the judge (proxy) score rose 0.70, 0.78, 0.85 while the deterministic
    ground-truth score fell 0.80, 0.78, 0.75. Should the self-improvement loop keep promoting on
    the judge score, or halt? Answer with one lowercase word: halt or continue.
  scorer: exact
  expected: "halt"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skill_forge_loop.py tests/test_skill_forge.py tests/test_skill_forge_gate.py tests/test_skill_forge_judge.py tests/test_skills_valid.py -v`
Expected: PASS — new loop-control tests pass; the Tier-1/Tier-2 contract tests and the skill lint stay green.

- [ ] **Step 5: Commit**

```bash
git add skills/skill-forge/SKILL.md eval/rubrics/skill-forge.md eval/benchmarks/skill-forge/tasks.yaml tests/test_skill_forge_loop.py
git commit -m "feat: skill-forge docs + benchmark reflect reflective generation + loop control"
```

---

### Task 7: Full-suite green + loop-control dry-run

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified generation + loop-control subsystem, end-to-end.

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q -W error`
Expected: PASS — all prior tests plus `test_mutation`, `test_pareto`, `test_goodhart`, `test_anchor`, `test_loop_control`, and `test_skill_forge_loop`, green, no warnings.

- [ ] **Step 2: Harness lint + validate**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0.

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (skill-forge slice loads with the new task).

- [ ] **Step 3: Loop-control dry-run — HALT (over-optimization)**

```bash
cat > /tmp/loop-halt.json <<'JSON'
{
  "rounds": [{"proxy": 0.70, "gold": 0.80}, {"proxy": 0.78, "gold": 0.78}, {"proxy": 0.85, "gold": 0.75}],
  "promotions": ["ground_truth", "judge_only"],
  "seed_ids": ["s1", "s2"], "current_ids": ["s1", "s2", "n1"],
  "dev_gate_deltas": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
}
JSON
python3 -m eval.harness.loop_control /tmp/loop-halt.json; echo "exit=$?"
```
Expected: a "# Loop control" block with Decision: HALT and a Goodhart line citing the proxy↑/gold↓ divergence; `exit=1`.

- [ ] **Step 4: Loop-control dry-run — CONTINUE + refresh trigger**

```bash
cat > /tmp/loop-continue.json <<'JSON'
{
  "rounds": [{"proxy": 0.70, "gold": 0.70}, {"proxy": 0.78, "gold": 0.76}, {"proxy": 0.85, "gold": 0.82}],
  "promotions": ["ground_truth", "judge_only"],
  "seed_ids": ["s1", "s2"], "current_ids": ["s1", "s2", "n1"],
  "dev_gate_deltas": [0.10, 0.10, 0.10, 0.10, 0.10, 0.10]
}
JSON
python3 -m eval.harness.loop_control /tmp/loop-continue.json; echo "exit=$?"
```
Expected: Decision: CONTINUE (gold rises with proxy, anchor intact), but "Benchmark refresh: yes" because the dev-gate gap is significant; `exit=0`.

- [ ] **Step 5: Confirm clean tree**

Run: `git status` (expect clean; `/tmp/loop-*.json` are outside the repo).

- [ ] **Step 6: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify generation + loop-control suite green + loop-control dry-run"
```

## Self-Review

**Spec coverage (Tier-3 checklist → tasks):**
- Reflective, attributed mutation replacing freeform generation → Task 1 (`mutation.apply_line_edits`, enforces per-edit attribution + exact-line match) + Task 6 (skill step 2).
- Instance-wise Pareto frontier (avoid best-on-aggregate local optima) → Task 2 (`pareto_front`) + Task 6 (skill step 2).
- Structured/grounded candidates + minibatch-explore / full-gate (MIPROv2) → documented in Task 6 (skill step 2 references mined traces; the minibatch-vs-full split is the Tier-1 dev/gate split, already merged) — no new code beyond the structured-edit application.
- Accumulate the eval anchor; never replace → Task 4 (`accumulate_anchor`) + Task 5 (loop halt on broken anchor) + Task 6 (loop-control section).
- Goodhart halt (proxy↑/gold↓) + judge-only cap; no edit-distance/KL reliance → Task 3 (`overoptimization_halt`, `judge_only_streak_exceeded`) + Task 5 (integrator) + Task 6 + Task 7 (HALT dry-run).
- Statistically-triggered benchmark refresh → Task 4 (`should_refresh_benchmark`, reuses Tier-1 `significant_improvement`) + Task 5 + Task 7 (refresh dry-run).
- **No overclaim:** the halt is empirical divergence detection (no closed-form curve, no `+β·log k`); the refresh reuses the paired significance test; no public-benchmark inflation magnitudes are encoded — stated in Global Constraints and reflected in code comments/prose.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new module, test, skill, rubric, or benchmark. Every code step shows complete content.

**Type consistency:** `loop_decision` (Task 5) consumes `overoptimization_halt`/`judge_only_streak_exceeded` (Task 3) and `accumulate_anchor`/`should_refresh_benchmark` (Task 4) with the exact signatures defined; `render_loop_report`/`main` read the dict keys `loop_decision` produces (`halt`, `goodhart`, `judge_only_streak_exceeded`, `anchor`, `refresh`). `anchor.should_refresh_benchmark` calls `stats.significant_improvement` (merged Tier 1) with `(deltas, alpha, seed)`. The history JSON shape is identical across Task 5's interface block, Task 5's code, and Task 7's dry-run files. No existing module or test is modified, so all 189 prior tests are untouched.
