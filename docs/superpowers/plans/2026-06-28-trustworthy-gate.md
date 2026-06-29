# Trustworthy Promotion Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace skill-forge's fixed `+0.02` promotion margin with a held-out split + a paired statistical-significance gate (bootstrap CI lower bound > 0 AND paired permutation p < Bonferroni-corrected α), so a candidate is promoted only on evidence that clears the noise floor of a small, judge-scored benchmark.

**Architecture:** Add one pure-stdlib stats module (`eval/harness/stats.py`: paired permutation test, BCa bootstrap CI, Bonferroni correction, significance verdict). Add a `split` (dev/gate) field to benchmark tasks so the loop mines/generates on dev tasks but gates only on an untouched held-out set. Add a `decide_promotion_stat` decision policy in `gate.py` that consumes a verdict plus per-task critical-regression info. Wire a new statistical path into `forge.py` (consuming per-(task, seed) `runs`) and a statistical proposal renderer into `forge_report.py`. The legacy `decide_promotion` + `task_scores` path stays intact so all existing tests pass. Every random step is seeded for determinism.

**Tech Stack:** Python 3.9.6 (stdlib only: `math`, `random`, `itertools`, `dataclasses`; **no numpy/scipy**), pytest, PyYAML; markdown skill.

**Evidence base:** Grounded in the deep-research report `scratchpad/research-report.md` (Tier-1 checklist). Load-bearing supported citations:
- Paired significance rule (BCa lower bound > 0 AND permutation p < 0.05) and "pairing is what gives power at small k" — [When +1% Is Not Enough](https://arxiv.org/html/2511.19794v1).
- Held-out reuse is safe for only ~O(log n) adaptive queries — [The reusable holdout, Dwork et al. 2015](https://www.nematilab.info/bmijc/assets/091218_paper.pdf).
- Power/MDE: a tiny benchmark cannot detect 1–2pt gains — [With Little Power, Card et al. 2020](https://aclanthology.org/2020.emnlp-main.745/).
- Multiple-comparison correction across the 2–3 generated candidates (Bonferroni/Holm at small N) — [Controlling type-I errors](https://www.statsig.com/blog/controlling-type-i-errors-bonferroni-benjamini-hochberg).
- Estimate variance across all randomness sources, not seed-only — ["We need to talk about random seeds", Bethard 2022](https://arxiv.org/abs/2210.13393).
- **Explicitly NOT adopted (refuted):** the Ladder `eta`-rate as the gate threshold (near-vacuous at small n; would reject genuine gains). We implement significance via the paired bootstrap + permutation protocol instead.

## Scope

In scope (the "trustworthy gate" subsystem): held-out/dev split discipline, paired significance gate, Bonferroni correction, seed-variance aggregation, and the report/skill/benchmark changes that expose it.

**Out of scope — separate future plans:** judge-bias controls (order-swapping, disjoint-family panel, verbosity control, judge-template sanitization) = Tier 2; reflective candidate generation (GEPA-style) and benchmark-refresh triggers = Tier 3. Do not implement these here.

## Global Constraints

- Run pytest as `python3 -m pytest` (no `pytest` on PATH); pyyaml + pytest already installed for system `python3` (3.9.6); no venv.
- Standard library only in new harness code — **no numpy, scipy, or any third-party numeric dependency**.
- Every new harness module starts with `from __future__ import annotations`.
- New harness modules are importable as `eval.harness.<module>`; `forge` stays runnable as `python3 -m eval.harness.forge <results.json>`.
- **Determinism:** every randomized routine (bootstrap, Monte-Carlo permutation) takes an explicit integer `seed`; identical inputs + seed must yield identical output. Exact (enumerated) permutation is used whenever n ≤ 18.
- **Backward compatibility:** do not change the signatures or behavior of existing `decide_promotion` (gate.py), `render_promotion_proposal` (forge_report.py), or the legacy `task_scores` path in `forge.evaluate`. All currently-passing tests must stay green.
- The `skill-forge` SKILL.md frontmatter `name == skill-forge`; body has one H1; `description` ≤ 1024 chars; no `TODO`/`TBD`/`FIXME`; sentence case. The strings `writing-skills`, `deep-research`, `eval.harness.forge`, and `human` must remain present (asserted by `tests/test_skill_forge.py`).
- The benchmark `tasks.yaml` must keep loading via `eval.harness.tasks.load_tasks` and keep ≥1 `ground_truth` task (asserted by `tests/test_skill_forge.py`).
- DRY, YAGNI, TDD, frequent commits. Never implement on `main`/`master` without consent — work on the `trustworthy-gate` branch/worktree.

---

### Task 1: `stats.py` — permutation test + Bonferroni correction

**Files:**
- Create: `eval/harness/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces: `bonferroni_alpha(alpha: float, n_comparisons: int) -> float`; `paired_permutation_pvalue(deltas: list[float], max_exact: int = 18, n_mc: int = 20000, seed: int = 0) -> float`. Two-sided paired sign-flip test; exact enumeration of all `2**n` sign assignments when `n <= max_exact`, else seeded Monte-Carlo with add-one smoothing.

- [ ] **Step 1: Write the failing test**

`tests/test_stats.py`:
```python
import pytest
from eval.harness.stats import bonferroni_alpha, paired_permutation_pvalue


def test_bonferroni_alpha():
    assert bonferroni_alpha(0.05, 1) == pytest.approx(0.05)
    assert bonferroni_alpha(0.05, 3) == pytest.approx(0.05 / 3)


def test_bonferroni_alpha_rejects_bad_n():
    with pytest.raises(ValueError):
        bonferroni_alpha(0.05, 0)


def test_permutation_empty_raises():
    with pytest.raises(ValueError):
        paired_permutation_pvalue([])


def test_permutation_all_zero_is_one():
    assert paired_permutation_pvalue([0.0, 0.0, 0.0]) == pytest.approx(1.0)


def test_permutation_exact_six_equal_positive():
    # n=6 equal +0.1: only all-+ and all-- reach |obs|; 2/64.
    assert paired_permutation_pvalue([0.1] * 6) == pytest.approx(2 / 64)


def test_permutation_exact_five_underpowered():
    # n=5 cannot clear 0.05 with a sign test: 2/32 = 0.0625.
    assert paired_permutation_pvalue([0.1] * 5) == pytest.approx(2 / 32)


def test_permutation_monte_carlo_is_seeded_and_deterministic():
    deltas = [0.05 * (i % 3 - 1) + 0.2 for i in range(25)]  # n=25 > max_exact -> MC
    p1 = paired_permutation_pvalue(deltas, max_exact=18, n_mc=2000, seed=7)
    p2 = paired_permutation_pvalue(deltas, max_exact=18, n_mc=2000, seed=7)
    assert p1 == p2
    assert 0.0 <= p1 <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_stats.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eval.harness.stats'`.

- [ ] **Step 3: Write minimal implementation**

`eval/harness/stats.py`:
```python
from __future__ import annotations

import math
import random


def bonferroni_alpha(alpha: float, n_comparisons: int) -> float:
    """Bonferroni-correct a significance level for n simultaneous comparisons."""
    if n_comparisons < 1:
        raise ValueError("n_comparisons must be >= 1")
    return alpha / n_comparisons


def paired_permutation_pvalue(
    deltas: list[float],
    max_exact: int = 18,
    n_mc: int = 20000,
    seed: int = 0,
) -> float:
    """Two-sided paired sign-flip permutation test on per-item deltas.

    Statistic is the sum of deltas; under H0 each delta's sign is equally likely.
    Exact enumeration of all 2**n sign assignments when n <= max_exact, else a
    seeded Monte-Carlo estimate with add-one smoothing.
    """
    n = len(deltas)
    if n == 0:
        raise ValueError("no deltas")
    obs = abs(sum(deltas))
    eps = 1e-12
    if n <= max_exact:
        total = 1 << n
        count = 0
        for mask in range(total):
            s = 0.0
            for i in range(n):
                s += deltas[i] if (mask >> i) & 1 else -deltas[i]
            if abs(s) >= obs - eps:
                count += 1
        return count / total
    rng = random.Random(seed)
    count = 0
    for _ in range(n_mc):
        s = 0.0
        for d in deltas:
            s += d if rng.random() < 0.5 else -d
        if abs(s) >= obs - eps:
            count += 1
    return (1 + count) / (1 + n_mc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_stats.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/stats.py tests/test_stats.py
git commit -m "feat: forge stats — paired permutation test + bonferroni"
```

---

### Task 2: `stats.py` — BCa bootstrap CI + significance verdict

**Files:**
- Modify: `eval/harness/stats.py`
- Test: `tests/test_stats_ci.py`

**Interfaces:**
- Consumes: `bonferroni_alpha`, `paired_permutation_pvalue` (Task 1).
- Produces: `paired_bootstrap_ci(deltas: list[float], confidence: float = 0.95, n_boot: int = 10000, seed: int = 0, method: str = "bca") -> tuple[float, float]`; `@dataclass(frozen=True) StatVerdict(mean_delta: float, ci_low: float, ci_high: float, p_value: float, alpha: float, significant: bool)`; `significant_improvement(deltas: list[float], alpha: float = 0.05, n_candidates: int = 1, n_boot: int = 10000, seed: int = 0, method: str = "bca") -> StatVerdict`. A constant `deltas` vector short-circuits the CI to `(mean, mean)` (avoids the degenerate BCa acceleration). `significant` is `ci_low > 0 AND p_value < bonferroni_alpha(alpha, n_candidates)`.

- [ ] **Step 1: Write the failing test**

`tests/test_stats_ci.py`:
```python
import pytest
from eval.harness.stats import (
    paired_bootstrap_ci,
    significant_improvement,
    StatVerdict,
    _norm_ppf,
    _norm_cdf,
)


def test_norm_helpers():
    assert _norm_ppf(0.975) == pytest.approx(1.959964, abs=1e-3)
    assert _norm_cdf(1.959964) == pytest.approx(0.975, abs=1e-3)


def test_norm_ppf_rejects_bounds():
    with pytest.raises(ValueError):
        _norm_ppf(0.0)


def test_ci_empty_raises():
    with pytest.raises(ValueError):
        paired_bootstrap_ci([])


def test_ci_constant_is_degenerate():
    lo, hi = paired_bootstrap_ci([0.1] * 6)
    assert lo == pytest.approx(0.1)
    assert hi == pytest.approx(0.1)


def test_ci_strong_positive_excludes_zero():
    deltas = [0.2, 0.25, 0.15, 0.30, 0.22, 0.18, 0.27, 0.21]
    lo, hi = paired_bootstrap_ci(deltas, seed=0)
    assert lo > 0.0
    assert lo <= sum(deltas) / len(deltas) <= hi


def test_ci_symmetric_includes_zero():
    deltas = [0.3, -0.3, 0.25, -0.25, 0.1, -0.1, 0.2, -0.2]
    lo, hi = paired_bootstrap_ci(deltas, seed=0)
    assert lo < 0.0 < hi


def test_ci_is_deterministic():
    deltas = [0.2, -0.05, 0.1, 0.15, -0.1, 0.3, 0.05, 0.12]
    assert paired_bootstrap_ci(deltas, seed=3) == paired_bootstrap_ci(deltas, seed=3)


def test_significant_when_powered():
    v = significant_improvement([0.1] * 6, alpha=0.05, n_candidates=1)
    assert isinstance(v, StatVerdict)
    assert v.p_value == pytest.approx(2 / 64)
    assert v.ci_low > 0
    assert v.significant


def test_underpowered_five_not_significant():
    v = significant_improvement([0.1] * 5, alpha=0.05, n_candidates=1)
    assert not v.significant  # p = 0.0625 >= 0.05


def test_bonferroni_flips_decision():
    # p = 0.03125: significant at alpha=0.05, not at 0.05/3 = 0.0167.
    assert significant_improvement([0.1] * 6, alpha=0.05, n_candidates=1).significant
    assert not significant_improvement([0.1] * 6, alpha=0.05, n_candidates=3).significant


def test_zero_effect_not_significant():
    v = significant_improvement([0.0] * 8)
    assert v.mean_delta == pytest.approx(0.0)
    assert not v.significant
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_stats_ci.py -v`
Expected: FAIL — `ImportError: cannot import name 'paired_bootstrap_ci'`.

- [ ] **Step 3: Write minimal implementation**

Append to `eval/harness/stats.py`:
```python
from dataclasses import dataclass


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Standard normal inverse CDF (Acklam's rational approximation)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Linear-interpolated percentile of an already-sorted list (pct in [0, 100])."""
    if not sorted_vals:
        raise ValueError("empty")
    if pct <= 0:
        return sorted_vals[0]
    if pct >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def paired_bootstrap_ci(
    deltas: list[float],
    confidence: float = 0.95,
    n_boot: int = 10000,
    seed: int = 0,
    method: str = "bca",
) -> tuple[float, float]:
    """Bootstrap CI for the mean of paired deltas (BCa by default, else percentile)."""
    n = len(deltas)
    if n == 0:
        raise ValueError("no deltas")
    mean = sum(deltas) / n
    if max(deltas) - min(deltas) == 0.0:  # constant: CI is degenerate
        return (mean, mean)
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += deltas[rng.randrange(n)]
        boots.append(s / n)
    boots.sort()
    alpha = 1.0 - confidence
    if method == "percentile":
        return (_percentile(boots, 100 * alpha / 2), _percentile(boots, 100 * (1 - alpha / 2)))
    # BCa
    below = sum(1 for b in boots if b < mean) / n_boot
    below = min(max(below, 1e-9), 1.0 - 1e-9)
    z0 = _norm_ppf(below)
    total = sum(deltas)
    jack = [(total - deltas[i]) / (n - 1) for i in range(n)]
    jbar = sum(jack) / n
    num = sum((jbar - j) ** 3 for j in jack)
    den = 6.0 * (sum((jbar - j) ** 2 for j in jack) ** 1.5)
    a = num / den if den != 0 else 0.0

    def adj(z_alpha: float) -> float:
        z = z0 + (z0 + z_alpha) / (1.0 - a * (z0 + z_alpha))
        return _norm_cdf(z)

    lo_p = adj(_norm_ppf(alpha / 2))
    hi_p = adj(_norm_ppf(1.0 - alpha / 2))
    return (_percentile(boots, 100 * lo_p), _percentile(boots, 100 * hi_p))


@dataclass(frozen=True)
class StatVerdict:
    mean_delta: float
    ci_low: float
    ci_high: float
    p_value: float
    alpha: float
    significant: bool


def significant_improvement(
    deltas: list[float],
    alpha: float = 0.05,
    n_candidates: int = 1,
    n_boot: int = 10000,
    seed: int = 0,
    method: str = "bca",
) -> StatVerdict:
    """Promote-worthy iff BCa lower bound > 0 AND permutation p < Bonferroni alpha."""
    if not deltas:
        raise ValueError("no deltas")
    ac = bonferroni_alpha(alpha, n_candidates)
    p = paired_permutation_pvalue(deltas, seed=seed)
    lo, hi = paired_bootstrap_ci(deltas, confidence=1.0 - ac, n_boot=n_boot, seed=seed, method=method)
    mean = sum(deltas) / len(deltas)
    return StatVerdict(mean, lo, hi, p, ac, (lo > 0.0) and (p < ac))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_stats_ci.py -v`
Expected: PASS (11 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/stats.py tests/test_stats_ci.py
git commit -m "feat: forge stats — BCa bootstrap CI + significance verdict"
```

---

### Task 3: `tasks.py` — dev/gate split discipline

**Files:**
- Modify: `eval/harness/tasks.py`
- Test: `tests/test_tasks_split.py`

**Interfaces:**
- Consumes: existing `load_tasks`, `Task`, `BenchmarkError`.
- Produces: `Task.split: str = "gate"` (new field, default `"gate"`); validation that any provided `split` is in `VALID_SPLITS = {"dev", "gate"}`; `split_tasks(tasks: list[Task]) -> tuple[list[Task], list[Task]]` returning `(dev_tasks, gate_tasks)`.
- Note: default `"gate"` keeps every existing benchmark slice valid and unchanged (all tasks become held-out gate tasks).

- [ ] **Step 1: Write the failing test**

`tests/test_tasks_split.py`:
```python
import pytest
from eval.harness.tasks import load_tasks, split_tasks, BenchmarkError


def _write(tmp_path, text):
    p = tmp_path / "tasks.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_split_defaults_to_gate(tmp_path):
    path = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: do a thing\n")
    tasks = load_tasks(path)
    assert tasks[0].split == "gate"


def test_split_parsed_and_partitioned(tmp_path):
    path = _write(
        tmp_path,
        "- id: d1\n  kind: judge\n  prompt: dev one\n  split: dev\n"
        "- id: g1\n  kind: judge\n  prompt: gate one\n  split: gate\n"
        "- id: g2\n  kind: ground_truth\n  prompt: gate two\n  scorer: exact\n"
        "  expected: x\n  split: gate\n",
    )
    tasks = load_tasks(path)
    dev, gate = split_tasks(tasks)
    assert [t.id for t in dev] == ["d1"]
    assert [t.id for t in gate] == ["g1", "g2"]


def test_invalid_split_raises(tmp_path):
    path = _write(tmp_path, "- id: t1\n  kind: judge\n  prompt: x\n  split: holdout\n")
    with pytest.raises(BenchmarkError):
        load_tasks(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tasks_split.py -v`
Expected: FAIL — `ImportError: cannot import name 'split_tasks'` (and `Task` has no `split`).

- [ ] **Step 3: Write minimal implementation**

In `eval/harness/tasks.py`, add the constant after `VALID_KINDS`:
```python
VALID_SPLITS: set[str] = {"dev", "gate"}
```

Add the `split` field to the `Task` dataclass (after `tolerance`):
```python
    tolerance: float | None = None
    split: str = "gate"
```

In `load_tasks`, after the `prompt` validation block and before the `scorer = item.get("scorer")` line, add split validation:
```python
        split = item.get("split", "gate")
        if split not in VALID_SPLITS:
            raise BenchmarkError(f"{path}[{tid}]: split must be one of {sorted(VALID_SPLITS)}")
```

Pass `split=split` into the `Task(...)` construction:
```python
        tasks.append(
            Task(
                id=tid,
                prompt=prompt,
                kind=kind,
                scorer=scorer,
                expected=item.get("expected"),
                tolerance=item.get("tolerance"),
                split=split,
            )
        )
```

Add the helper at the end of the module:
```python
def split_tasks(tasks: list[Task]) -> tuple[list[Task], list[Task]]:
    """Partition tasks into (dev, gate) by their split field."""
    dev = [t for t in tasks if t.split == "dev"]
    gate = [t for t in tasks if t.split == "gate"]
    return dev, gate
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tasks_split.py tests/test_tasks.py -v`
Expected: PASS — new split tests pass and the existing `tests/test_tasks.py` stays green (default `split="gate"`).

- [ ] **Step 5: Commit**

```bash
git add eval/harness/tasks.py tests/test_tasks_split.py
git commit -m "feat: dev/gate split discipline in benchmark tasks"
```

---

### Task 4: `gate.py` — `decide_promotion_stat` decision policy

**Files:**
- Modify: `eval/harness/gate.py`
- Test: `tests/test_gate_stat.py`

**Interfaces:**
- Consumes: `eval.harness.stats.StatVerdict` (Task 2); existing `PromotionDecision`.
- Produces: `decide_promotion_stat(verdict, per_task: list[dict]) -> PromotionDecision`. `verdict` is a `StatVerdict` or `None` (None = no held-out observations). `per_task` dicts carry `task_id`, `incumbent`, `candidate`, optional `critical`. Order of checks: critical-regression veto first, then `None` guard, then `verdict.significant`.
- Note: the existing `decide_promotion` (margin-based) is left untouched for backward compatibility.

- [ ] **Step 1: Write the failing test**

`tests/test_gate_stat.py`:
```python
from eval.harness.gate import decide_promotion_stat, PromotionDecision
from eval.harness.stats import StatVerdict


def _v(significant, mean=0.1, lo=0.02, hi=0.18, p=0.03, alpha=0.05):
    return StatVerdict(mean, lo, hi, p, alpha, significant)


def _task(tid, inc, cand, critical=False):
    return {"task_id": tid, "incumbent": inc, "candidate": cand, "critical": critical}


def test_promotes_on_significant_verdict():
    d = decide_promotion_stat(_v(True), [_task("t1", 0.7, 0.8)])
    assert isinstance(d, PromotionDecision)
    assert d.promote


def test_rejects_non_significant_verdict():
    d = decide_promotion_stat(_v(False), [_task("t1", 0.7, 0.72)])
    assert not d.promote
    assert "not significant" in d.reason


def test_critical_regression_vetoes_even_if_significant():
    per_task = [_task("t1", 0.5, 0.9), _task("crit", 1.0, 0.0, critical=True)]
    d = decide_promotion_stat(_v(True), per_task)
    assert not d.promote
    assert "crit" in d.reason


def test_none_verdict_rejects():
    d = decide_promotion_stat(None, [_task("t1", 0.7, 0.7)])
    assert not d.promote
    assert "no held-out" in d.reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_gate_stat.py -v`
Expected: FAIL — `ImportError: cannot import name 'decide_promotion_stat'`.

- [ ] **Step 3: Write minimal implementation**

Append to `eval/harness/gate.py`:
```python
def decide_promotion_stat(verdict, per_task: list[dict]) -> PromotionDecision:
    """Promote only on a statistically significant gain with no critical-task regression.

    `verdict` is a stats.StatVerdict or None (no held-out observations). The critical
    veto is checked first so a ground-truth regression always blocks promotion.
    """
    regressions = [
        t["task_id"]
        for t in per_task
        if t.get("critical") and t["candidate"] < t["incumbent"] - 1e-9
    ]
    if regressions:
        return PromotionDecision(False, f"critical regression on: {', '.join(regressions)}")
    if verdict is None:
        return PromotionDecision(False, "no held-out (gate) observations to test")
    detail = (
        f"mean {verdict.mean_delta:+.3f}, CI low {verdict.ci_low:+.3f}, "
        f"p={verdict.p_value:.3f}, alpha={verdict.alpha:.3f}"
    )
    if not verdict.significant:
        return PromotionDecision(False, f"not significant: {detail}")
    return PromotionDecision(True, f"promote: {detail} (CI low > 0 and p < alpha)")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_gate_stat.py tests/test_gate.py -v`
Expected: PASS — new statistical-gate tests pass and the existing `tests/test_gate.py` (legacy `decide_promotion`) stays green.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/gate.py tests/test_gate_stat.py
git commit -m "feat: forge statistical promotion gate (significance + critical veto)"
```

---

### Task 5: `forge_report.py` — statistical proposal renderer

**Files:**
- Modify: `eval/harness/forge_report.py`
- Test: `tests/test_forge_report_stat.py`

**Interfaces:**
- Consumes: a `PromotionDecision`-like object (`.promote`, `.reason`); a `StatVerdict`-like object or `None`; `tournament` dict; `per_task` list.
- Produces: `render_stat_proposal(skill: str, verdict, decision, tournament: dict, per_task: list[dict], n_obs: int) -> str`. `n_obs` is the number of paired (task, seed) held-out observations behind the test.
- Note: the existing `render_promotion_proposal` is left untouched.

- [ ] **Step 1: Write the failing test**

`tests/test_forge_report_stat.py`:
```python
from eval.harness.forge_report import render_stat_proposal
from eval.harness.gate import PromotionDecision
from eval.harness.stats import StatVerdict


def test_renders_significant_proposal():
    verdict = StatVerdict(0.10, 0.02, 0.18, 0.031, 0.05, True)
    decision = PromotionDecision(True, "promote: mean +0.100, CI low +0.020, p=0.031, alpha=0.050 (CI low > 0 and p < alpha)")
    tournament = {"candidate_wins": 3, "incumbent_wins": 1, "ties": 0, "candidate_win_rate": 0.75}
    per_task = [{"task_id": "g1", "incumbent": 0.70, "candidate": 0.80, "critical": False}]
    md = render_stat_proposal("literature-review", verdict, decision, tournament, per_task, n_obs=18)
    assert "# Promotion proposal — literature-review" in md
    assert "PROMOTE" in md
    assert "Held-out observations: 18" in md
    assert "p = 0.031" in md
    assert "g1" in md


def test_renders_no_holdout_reject():
    decision = PromotionDecision(False, "no held-out (gate) observations to test")
    tournament = {"candidate_wins": 0, "incumbent_wins": 0, "ties": 0, "candidate_win_rate": 0.0}
    md = render_stat_proposal("research-design", None, decision, tournament, [], n_obs=0)
    assert "REJECT" in md
    assert "no held-out" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_forge_report_stat.py -v`
Expected: FAIL — `ImportError: cannot import name 'render_stat_proposal'`.

- [ ] **Step 3: Write minimal implementation**

Append to `eval/harness/forge_report.py`:
```python
def render_stat_proposal(
    skill: str,
    verdict,
    decision,
    tournament: dict,
    per_task: list[dict],
    n_obs: int,
) -> str:
    """Render a human-facing statistical promotion proposal as markdown."""
    result = "PROMOTE" if decision.promote else "REJECT"
    lines = [
        f"# Promotion proposal — {skill}",
        "",
        f"- Decision: {result} — {decision.reason}",
        f"- Held-out observations: {n_obs}",
    ]
    if verdict is not None:
        lines += [
            f"- Mean held-out delta: {verdict.mean_delta:+.3f}",
            f"- Bootstrap CI: [{verdict.ci_low:+.3f}, {verdict.ci_high:+.3f}]",
            f"- Permutation p = {verdict.p_value:.3f} (alpha = {verdict.alpha:.3f}, Bonferroni-corrected)",
        ]
    else:
        lines.append("- Statistical test: not run (no held-out gate observations)")
    lines += [
        "",
        "## A/B tournament",
        (
            f"- candidate wins {tournament['candidate_wins']}, "
            f"incumbent wins {tournament['incumbent_wins']}, "
            f"ties {tournament['ties']} "
            f"(candidate win rate {tournament['candidate_win_rate']:.2f})"
        ),
        "",
        "## Per held-out task (seed-averaged)",
        "| task | incumbent | candidate | critical |",
        "| --- | --- | --- | --- |",
    ]
    for t in per_task:
        crit = "yes" if t.get("critical") else "no"
        lines.append(f"| {t['task_id']} | {t['incumbent']:.2f} | {t['candidate']:.2f} | {crit} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_forge_report_stat.py tests/test_forge_report.py -v`
Expected: PASS — new renderer tests pass and the existing `tests/test_forge_report.py` stays green.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/forge_report.py tests/test_forge_report_stat.py
git commit -m "feat: forge statistical promotion proposal renderer"
```

---

### Task 6: `forge.py` — held-out `runs` path wired to the statistical gate

**Files:**
- Modify: `eval/harness/forge.py`
- Test: `tests/test_forge_stat.py`

**Interfaces:**
- Consumes: `eval.harness.stats.significant_improvement`; `eval.harness.gate.decide_promotion_stat`; `eval.harness.forge_report.render_stat_proposal`; existing legacy imports.
- Produces: `build_paired_deltas(inc_runs: list[dict], cand_runs: list[dict], split: str = "gate") -> list[float]`; `aggregate_per_task(inc_runs: list[dict], cand_runs: list[dict], split: str = "gate") -> list[dict]`; an `evaluate(results)` that branches to the statistical path when both `incumbent` and `candidate` carry a `runs` list, else falls back to the legacy `task_scores` path. `main` exit codes unchanged (0 = promote, else 1; 2 on bad input).
- New results JSON shape (statistical path):
```json
{
  "skill": "literature-review",
  "alpha": 0.05,
  "n_candidates": 3,
  "seed": 0,
  "incumbent": {"hash": "i", "runs": [{"task_id": "g1", "split": "gate", "seed": 0, "score": 0.70, "critical": false}]},
  "candidate": {"hash": "c", "runs": [{"task_id": "g1", "split": "gate", "seed": 0, "score": 0.80, "critical": false}]},
  "tournament": [{"task_id": "g1", "winner": "candidate"}]
}
```
Pairing is by `(task_id, seed)` on `split == "gate"` runs only; `seed` defaults to `0` when absent.

- [ ] **Step 1: Write the failing test**

`tests/test_forge_stat.py`:
```python
import json
from eval.harness.forge import build_paired_deltas, aggregate_per_task, evaluate, main
from eval.harness.gate import PromotionDecision


def _run(tid, score, seed=0, split="gate", critical=False):
    return {"task_id": tid, "split": split, "seed": seed, "score": score, "critical": critical}


def test_build_paired_deltas_gate_only_matched_by_task_and_seed():
    inc = [_run("g1", 0.7, 0), _run("g1", 0.7, 1), _run("d1", 0.5, 0, split="dev")]
    cand = [_run("g1", 0.8, 0), _run("g1", 0.9, 1), _run("d1", 0.9, 0, split="dev")]
    deltas = build_paired_deltas(inc, cand)
    assert sorted(deltas) == [0.1, 0.2]  # dev pair excluded


def test_aggregate_per_task_seed_means():
    inc = [_run("g1", 0.6, 0), _run("g1", 0.8, 1)]
    cand = [_run("g1", 0.7, 0), _run("g1", 0.9, 1)]
    per_task = aggregate_per_task(inc, cand)
    assert per_task[0]["task_id"] == "g1"
    assert per_task[0]["incumbent"] == 0.7
    assert per_task[0]["candidate"] == 0.8


def _results(inc_scores, cand_scores, n_candidates=1, critical=False):
    inc = [_run(f"g{i}", s, 0, critical=critical) for i, s in enumerate(inc_scores)]
    cand = [_run(f"g{i}", s, 0, critical=critical) for i, s in enumerate(cand_scores)]
    return {
        "skill": "demo",
        "alpha": 0.05,
        "n_candidates": n_candidates,
        "seed": 0,
        "incumbent": {"hash": "i", "runs": inc},
        "candidate": {"hash": "c", "runs": cand},
        "tournament": [{"task_id": "g0", "winner": "candidate"}],
    }


def test_evaluate_promotes_on_significant_holdout():
    # 6 gate tasks, candidate +0.1 each -> p = 0.03125, CI low > 0.
    res = _results([0.7] * 6, [0.8] * 6)
    decision, report = evaluate(res)
    assert isinstance(decision, PromotionDecision)
    assert decision.promote
    assert "# Promotion proposal — demo" in report
    assert "Held-out observations: 6" in report


def test_evaluate_rejects_underpowered_holdout():
    # 5 gate tasks -> p = 0.0625, cannot clear alpha.
    res = _results([0.7] * 5, [0.8] * 5)
    decision, _ = evaluate(res)
    assert not decision.promote


def test_evaluate_bonferroni_blocks_three_candidates():
    res = _results([0.7] * 6, [0.8] * 6, n_candidates=3)
    decision, _ = evaluate(res)
    assert not decision.promote  # 0.03125 >= 0.05/3


def test_legacy_task_scores_path_still_works():
    legacy = {
        "skill": "demo",
        "margin": 0.02,
        "incumbent": {"hash": "i", "task_scores": [{"task_id": "t1", "score": 0.70, "critical": False}]},
        "candidate": {"hash": "c", "task_scores": [{"task_id": "t1", "score": 0.90, "critical": False}]},
        "tournament": [{"task_id": "t1", "winner": "candidate"}],
    }
    decision, report = evaluate(legacy)
    assert decision.promote
    assert "# Promotion proposal — demo" in report


def test_main_exit_codes(tmp_path):
    promote = tmp_path / "p.json"
    promote.write_text(json.dumps(_results([0.7] * 6, [0.8] * 6)), encoding="utf-8")
    assert main([str(promote)]) == 0

    reject = tmp_path / "r.json"
    reject.write_text(json.dumps(_results([0.7] * 5, [0.8] * 5)), encoding="utf-8")
    assert main([str(reject)]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_forge_stat.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_paired_deltas'`.

- [ ] **Step 3: Write minimal implementation**

In `eval/harness/forge.py`, extend the imports:
```python
from eval.harness.blend import overall_score
from eval.harness.forge_report import render_promotion_proposal, render_stat_proposal
from eval.harness.gate import decide_promotion, decide_promotion_stat
from eval.harness.stats import significant_improvement
from eval.harness.tournament import tally_tournament
```

Add the two builders above `evaluate`:
```python
def build_paired_deltas(inc_runs: list[dict], cand_runs: list[dict], split: str = "gate") -> list[float]:
    """Per-(task, seed) candidate-minus-incumbent deltas on held-out runs only."""
    def index(runs):
        return {
            (r["task_id"], r.get("seed", 0)): r["score"]
            for r in runs
            if r.get("split", "gate") == split
        }
    inc = index(inc_runs)
    cand = index(cand_runs)
    keys = sorted(set(inc) & set(cand))
    return [cand[k] - inc[k] for k in keys]


def aggregate_per_task(inc_runs: list[dict], cand_runs: list[dict], split: str = "gate") -> list[dict]:
    """Seed-averaged per-task incumbent/candidate scores (held-out split only)."""
    def fold(runs):
        sums: dict = {}
        counts: dict = {}
        crit: dict = {}
        for r in runs:
            if r.get("split", "gate") != split:
                continue
            tid = r["task_id"]
            sums[tid] = sums.get(tid, 0.0) + r["score"]
            counts[tid] = counts.get(tid, 0) + 1
            crit[tid] = crit.get(tid, False) or bool(r.get("critical"))
        means = {t: sums[t] / counts[t] for t in sums}
        return means, crit
    inc_m, inc_c = fold(inc_runs)
    cand_m, cand_c = fold(cand_runs)
    per_task = []
    for tid in sorted(set(inc_m) & set(cand_m)):
        per_task.append(
            {
                "task_id": tid,
                "incumbent": inc_m[tid],
                "candidate": cand_m[tid],
                "critical": inc_c.get(tid, False) or cand_c.get(tid, False),
            }
        )
    return per_task
```

Replace the body of `evaluate` with a branch that prefers the statistical path:
```python
def evaluate(results: dict) -> tuple:
    """Statistical held-out gate when 'runs' are present; else the legacy margin gate."""
    skill = results["skill"]
    inc = results["incumbent"]
    cand = results["candidate"]
    tournament = tally_tournament(results.get("tournament", []))

    if "runs" in inc and "runs" in cand:
        alpha = results.get("alpha", 0.05)
        n_candidates = results.get("n_candidates", 1)
        seed = results.get("seed", 0)
        deltas = build_paired_deltas(inc["runs"], cand["runs"])
        per_task = aggregate_per_task(inc["runs"], cand["runs"])
        verdict = (
            significant_improvement(deltas, alpha=alpha, n_candidates=n_candidates, seed=seed)
            if deltas
            else None
        )
        decision = decide_promotion_stat(verdict, per_task)
        report = render_stat_proposal(skill, verdict, decision, tournament, per_task, len(deltas))
        return decision, report

    # Legacy margin path (unchanged).
    margin = results.get("margin", 0.02)
    inc_tasks = inc["task_scores"]
    cand_tasks = cand["task_scores"]
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
                "critical": bool(it.get("critical")) or bool(ct.get("critical")),
            }
        )
    decision = decide_promotion(inc_overall, cand_overall, per_task, margin)
    report = render_promotion_proposal(skill, inc_overall, cand_overall, decision, tournament, per_task)
    return decision, report
```

Leave `content_hash`, `load_results`, and `main` unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_forge_stat.py tests/test_forge.py -v`
Expected: PASS — new statistical-path tests pass and the existing `tests/test_forge.py` (legacy path) stays green.

- [ ] **Step 5: Commit**

```bash
git add eval/harness/forge.py tests/test_forge_stat.py
git commit -m "feat: forge held-out runs path wired to the statistical gate"
```

---

### Task 7: `skill-forge` skill + rubric + benchmark reflect the trustworthy gate

**Files:**
- Modify: `skills/skill-forge/SKILL.md`
- Modify: `eval/rubrics/skill-forge.md`
- Modify: `eval/benchmarks/skill-forge/tasks.yaml`
- Test: `tests/test_skill_forge_gate.py`

**Interfaces:**
- Consumes: `eval.harness.tasks.load_tasks`, `eval.harness.tasks.split_tasks`.
- Produces: documentation + benchmark annotations matching the new gate; a new ground-truth gate task exercising the underpowered-significance rule.
- Constraint: keep `tests/test_skill_forge.py` assertions valid (`writing-skills`, `deep-research`, `eval.harness.forge`, `human`; rubric dimensions `evidence quality`, `evaluation rigor`, `gating soundness`, `reversibility`; ≥1 ground_truth task).

- [ ] **Step 1: Write the failing test**

`tests/test_skill_forge_gate.py`:
```python
from pathlib import Path
from eval.harness.tasks import load_tasks, split_tasks

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skill-forge" / "SKILL.md"
RUBRIC = ROOT / "eval" / "rubrics" / "skill-forge.md"
TASKS = ROOT / "eval" / "benchmarks" / "skill-forge" / "tasks.yaml"


def test_skill_documents_holdout_and_significance():
    body = SKILL.read_text(encoding="utf-8").lower()
    assert "held-out" in body
    assert "significance" in body or "significant" in body
    # Legacy contract assertions must still hold.
    for needle in ("writing-skills", "deep-research", "eval.harness.forge", "human"):
        assert needle in body


def test_rubric_mentions_significance_and_holdout():
    text = RUBRIC.read_text(encoding="utf-8").lower()
    assert "held-out" in text
    assert "significan" in text
    for dim in ("evidence quality", "evaluation rigor", "gating soundness", "reversibility"):
        assert dim in text


def test_benchmark_has_dev_and_gate_splits():
    tasks = load_tasks(TASKS)
    dev, gate = split_tasks(tasks)
    assert dev, "expected at least one dev task"
    assert gate, "expected at least one gate task"
    assert any(t.kind == "ground_truth" for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skill_forge_gate.py -v`
Expected: FAIL — `held-out`/`significance` strings absent; benchmark has no dev split.

- [ ] **Step 3: Edit the skill, rubric, and benchmark**

In `skills/skill-forge/SKILL.md`, replace step 5 of "The cycle" with the held-out + significance version:
```markdown
5. **Gate and propose.** Score on the **held-out gate split only** — the `split: gate`
   tasks the loop never mined or generated against — pairing incumbent and candidate on the
   same tasks and seeds. Collect per-(task, seed) scores into a results JSON and run
   `python3 -m eval.harness.forge results.json`. It builds the paired held-out deltas and
   promotes only on **statistical significance** (bootstrap CI lower bound above zero and a
   paired permutation p below the Bonferroni-corrected alpha for the number of candidates),
   with no critical-task regression. Present the proposal and the evidence to your human
   partner. Promote only on approval — then replace the SKILL.md and `git tag` the new
   version so the prior one is always one `git checkout` away.
```

In the same file, update the "Results JSON shape" line to the runs shape:
```markdown
`{"skill", "alpha", "n_candidates", "seed", "incumbent": {"hash", "runs": [{"task_id",
"split", "seed", "score", "critical"}]}, "candidate": {...}, "tournament": [{"task_id",
"winner": "candidate|incumbent|tie"}]}`
```

In the same file, add two red flags to the "Red flags (stop)" list:
```markdown
- Gating on the dev split, or on a benchmark too small to have power — a sub-noise margin is
  not a real gain. Grow or refresh the held-out set instead.
- Promoting on a raw point-margin without a significance test, or testing several candidates
  without Bonferroni-correcting the threshold.
```

In `eval/rubrics/skill-forge.md`, replace the "Evaluation rigor" and "Gating soundness" bullets:
```markdown
- **Evaluation rigor (weight 0.25):** Held-out gate split kept disjoint from mine/generate, multi-judge panel, A/B tournament, and variance estimated across seeds — not a single point score.
- **Gating soundness (weight 0.25):** Promotion requires statistical significance (paired bootstrap CI above zero and a Bonferroni-corrected permutation p) and blocks on any critical regression, with human approval.
```

Replace `eval/benchmarks/skill-forge/tasks.yaml` with the split-annotated version plus a significance task:
```yaml
- id: gate_arithmetic
  kind: ground_truth
  split: gate
  prompt: >
    Incumbent overall score is 0.80, candidate is 0.805, the promotion margin is 0.02, and
    no task regressed. Should the candidate be promoted? Answer with one lowercase word:
    yes or no.
  scorer: exact
  expected: "no"
- id: significance_underpowered
  kind: ground_truth
  split: gate
  prompt: >
    A candidate beats the incumbent by +0.1 on all 5 held-out tasks, each scored once. A
    paired sign-flip permutation test gives p = 0.0625. At alpha = 0.05, should it be
    promoted? Answer with one lowercase word: yes or no.
  scorer: exact
  expected: "no"
- id: design_fair_eval
  kind: judge
  split: dev
  prompt: >
    Describe how you would evaluate a candidate version of the literature-review skill so
    the comparison is fair and hard to game: what to anchor on, how to split dev versus
    held-out, how many judges, and what would block promotion. Judged on evaluation rigor
    and gating soundness per the rubric.
- id: reject_reward_hacking
  kind: judge
  split: dev
  prompt: >
    A candidate skill scores higher only because the benchmark task was edited to match its
    output. Explain why this must be rejected and how the loop should prevent it.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skill_forge_gate.py tests/test_skill_forge.py tests/test_skills_valid.py -v`
Expected: PASS — new gate-doc tests pass; the original `tests/test_skill_forge.py` contract tests and the parametrized skill lint stay green.

- [ ] **Step 5: Commit**

```bash
git add skills/skill-forge/SKILL.md eval/rubrics/skill-forge.md eval/benchmarks/skill-forge/tasks.yaml tests/test_skill_forge_gate.py
git commit -m "feat: skill-forge docs + benchmark reflect held-out significance gate"
```

---

### Task 8: Full-suite green + statistical forge dry-run

**Files:**
- Modify: none (verification task; fold any fix into the file that needs it).

**Interfaces:**
- Consumes: everything above.
- Produces: a verified trustworthy-gate subsystem, end-to-end.

- [ ] **Step 1: Run the whole test suite**

Run: `python3 -m pytest -q`
Expected: PASS — all prior tests plus the new `test_stats`, `test_stats_ci`, `test_tasks_split`, `test_gate_stat`, `test_forge_report_stat`, `test_forge_stat`, and `test_skill_forge_gate` files, green, no warnings.

- [ ] **Step 2: Run the harness against the real repo**

Run: `python3 -m eval.harness.cli lint`
Expected: `lint: OK`, exit 0.

Run: `python3 -m eval.harness.cli validate`
Expected: `validate: OK`, exit 0 (skill-forge slice still loads, now with splits).

- [ ] **Step 3: Statistical forge dry-run — promote case**

```bash
cat > /tmp/forge-stat-promote.json <<'JSON'
{
  "skill": "literature-review",
  "alpha": 0.05,
  "n_candidates": 1,
  "seed": 0,
  "incumbent": {"hash": "i", "runs": [
    {"task_id": "g1", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g2", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g3", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g4", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g5", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g6", "split": "gate", "seed": 0, "score": 0.70}
  ]},
  "candidate": {"hash": "c", "runs": [
    {"task_id": "g1", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g2", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g3", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g4", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g5", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g6", "split": "gate", "seed": 0, "score": 0.80}
  ]},
  "tournament": [{"task_id": "g1", "winner": "candidate"}]
}
JSON
python3 -m eval.harness.forge /tmp/forge-stat-promote.json; echo "exit=$?"
```
Expected: a "# Promotion proposal — literature-review" block with Decision: PROMOTE, `p = 0.031`, CI lower bound above 0, "Held-out observations: 6", and `exit=0`.

- [ ] **Step 4: Statistical forge dry-run — reject (underpowered) case**

```bash
cat > /tmp/forge-stat-reject.json <<'JSON'
{
  "skill": "literature-review",
  "alpha": 0.05,
  "n_candidates": 1,
  "seed": 0,
  "incumbent": {"hash": "i", "runs": [
    {"task_id": "g1", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g2", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g3", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g4", "split": "gate", "seed": 0, "score": 0.70},
    {"task_id": "g5", "split": "gate", "seed": 0, "score": 0.70}
  ]},
  "candidate": {"hash": "c", "runs": [
    {"task_id": "g1", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g2", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g3", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g4", "split": "gate", "seed": 0, "score": 0.80},
    {"task_id": "g5", "split": "gate", "seed": 0, "score": 0.80}
  ]},
  "tournament": [{"task_id": "g1", "winner": "candidate"}]
}
JSON
python3 -m eval.harness.forge /tmp/forge-stat-reject.json; echo "exit=$?"
```
Expected: a proposal with Decision: REJECT, "not significant" (p = 0.062 ≥ alpha 0.050), and `exit=1` — the same +0.10 mean as the promote case, rejected purely because 5 tasks are underpowered.

- [ ] **Step 5: Confirm clean tree**

Run: `git status` (expect clean; `/tmp/forge-stat-*.json` are outside the repo).

- [ ] **Step 6: Commit (only if any fix was needed)**

```bash
git add -A
git commit -m "test: verify trustworthy-gate suite green + statistical forge dry-run"
```

## Self-Review

**Spec coverage (Tier-1 checklist → tasks):**
- Held-out/dev split discipline (checklist 1) → Task 3 (`split` field + `split_tasks`) + Task 6 (`build_paired_deltas`/`aggregate_per_task` gate-only) + Task 7 (benchmark splits).
- Paired significance rule, BCa lower bound > 0 AND permutation p < α (checklist 2, 3) → Task 1 (permutation) + Task 2 (BCa CI + `significant_improvement`) + Task 4 (decision policy) + Task 6 (wiring).
- Power/MDE — reject sub-noise gains on tiny sets (checklist 4) → demonstrated by the underpowered 5-task path (Task 2 `test_underpowered_five_not_significant`, Task 6 `test_evaluate_rejects_underpowered_holdout`, Task 8 reject dry-run); benchmark grown with explicit gate tasks (Task 7).
- Bonferroni across candidates (checklist 5) → Task 1 (`bonferroni_alpha`) + Task 2 (`test_bonferroni_flips_decision`) + Task 6 (`n_candidates` consumed, `test_evaluate_bonferroni_blocks_three_candidates`).
- Variance across all randomness sources (checklist 6) → results JSON carries per-(task, seed) `runs`; deltas pair on `(task_id, seed)` so seeds enter the test (Task 6). Out of this plan's code scope: actually generating multi-seed runs (that is the runtime agent work the skill orchestrates) — documented in Task 7's SKILL.md, not implemented in Python.
- Critical no-regression veto preserved (checklist 8 in spirit) → Task 4 (`decide_promotion_stat` checks critical first).
- Explicitly NOT adopted: the Ladder η-rate (refuted) — not implemented; significance is the bootstrap+permutation protocol per the supported citation.
- Tier 2 / Tier 3 items (judge-bias controls, reflective generation, refresh triggers) are out of scope by design and deferred to separate plans.

**Placeholder scan:** No `TODO`/`TBD`/`FIXME` in any new module, test, skill, rubric, or benchmark. Every code step shows complete content.

**Type consistency:** `stats.significant_improvement(...) -> StatVerdict` (mean_delta, ci_low, ci_high, p_value, alpha, significant) is consumed identically by `gate.decide_promotion_stat(verdict, per_task)` (Task 4), `forge_report.render_stat_proposal(..., verdict, ...)` (Task 5), and `forge.evaluate` (Task 6). `build_paired_deltas`/`aggregate_per_task` signatures in Task 6's prose, code, and tests match. The statistical results JSON shape (`runs` with `task_id`/`split`/`seed`/`score`/`critical`; top-level `alpha`/`n_candidates`/`seed`) is identical across Task 6's interface block, Task 6's code, Task 7's SKILL.md "Results JSON shape", and Task 8's dry-run files. Legacy `decide_promotion`, `render_promotion_proposal`, and the `task_scores` path are unchanged and covered by the retained original tests.
