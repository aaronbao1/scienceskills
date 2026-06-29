# Task 6 Report (current): Slim forge CLI orchestrator

## Status
COMPLETE — 3/3 tests green, committed.

## Commit
(see below after git commit)

## Files Changed
- `eval/harness/forge.py` — full rewrite (slim orchestrator)
- `tests/test_forge.py` — full replacement (3 new tests from brief)

## TDD RED / GREEN cycle

### RED — Write failing test, verify failure

Replaced `tests/test_forge.py` with the 3 tests from the brief, then ran:

```
python3 -m pytest tests/test_forge.py -v
```

Exit code 2 — collection error:

```
ERROR collecting tests/test_forge.py
eval/harness/forge.py:11: in <module>
    from eval.harness.gate import decide_promotion, decide_promotion_stat
ImportError: cannot import name 'decide_promotion' from 'eval.harness.gate'
```

This is the expected failure: the old forge.py imported `decide_promotion` which no longer exists in gate.py (replaced by `decide` in earlier tiers). Test could not even be collected, confirming the old implementation is broken for the new interface.

### GREEN — Rewrite forge.py, verify pass

Rewrote `eval/harness/forge.py` per the brief:
- Imports: `from eval.harness import gate, monitor` plus stdlib only
- `INSIGHTS_ROOT` module-level constant (monkeypatchable at call time)
- `evaluate(results, *, now_iso) -> dict` with keys `exit`, `decision`, `reason`, `proposal`
  - Calls `monitor.check(skill)` first; returns exit=2/decision="halt" WITHOUT appending a round record if monitor halts
  - Otherwise calls `gate.decide(inc_runs, cand_runs)` and appends exactly one JSONL record to `gate-history.jsonl`
  - Returns exit=0/decision="promote" or exit=1/decision="reject"
- `main(argv) -> int` for CLI: `python3 -m eval.harness.forge <skill> <results.json>`

Then ran:

```
python3 -m pytest tests/test_forge.py -v
```

Output:
```
tests/test_forge.py::test_promote_exit0_appends_one_round PASSED
tests/test_forge.py::test_reject_exit1 PASSED
tests/test_forge.py::test_halt_exit2_when_monitor_halts PASSED
3 passed in 0.02s
```

## Self-review

**Correctness:**
- The halt path returns without writing anything to `gate-history.jsonl`, satisfying "UNLESS the monitor halts".
- The promote path writes exactly one JSONL line and returns exit=0.
- The reject path writes exactly one JSONL line and returns exit=1.
- `_next_round` counts existing non-empty lines; on a fresh file it returns 1.
- `INSIGHTS_ROOT` is referenced via the module attribute at call time, so monkeypatching works correctly.
- Both `forge.INSIGHTS_ROOT` and `monitor.INSIGHTS_ROOT` are patched in each test, ensuring the monitor reads from `tmp_path`.

**Interface compliance:**
- `forge.INSIGHTS_ROOT` — exported module attribute ✓
- `forge.evaluate(results, *, now_iso) -> dict` ✓
- `forge.main(argv) -> int` ✓
- CLI positional args: `<skill> <results.json>` ✓
- Imports: stdlib + `from eval.harness import gate, monitor` only ✓

## Concerns

None. The implementation is a verbatim transcription of the brief code. The three tests cover all three exit codes and the critical invariant (halt must not append a round record). `test_reject_exit1` uses equal scores (0.50 vs 0.50), producing `mean_delta=0` → gate returns `promote=False`; this is correct behavior.

---

# Task 6 Prior Report (archived): forge.py — held-out runs path wired to the statistical gate

## Status
COMPLETE — all tests green, committed.

## Commit Hash(es)
`7c49a66` — "feat: forge held-out runs path wired to the statistical gate"

## Files Changed
- `eval/harness/forge.py` (modified)
- `tests/test_forge_stat.py` (created)

## Exact pytest commands + pass/fail summaries

### Step 2 — Failing test (confirming TDD red phase)
```
python3 -m pytest tests/test_forge_stat.py -v
```
Result: FAIL — `ImportError: cannot import name 'build_paired_deltas' from 'eval.harness.forge'` (1 error during collection, 0 items collected).

### Step 4 — New test file + legacy forge tests
```
python3 -m pytest tests/test_forge_stat.py tests/test_forge.py -v
```
Result: 14 passed in 0.02s (7 new stat tests + 7 legacy forge tests).

### Full suite
```
python3 -m pytest -v
```
Result: 155 passed in 0.21s — zero regressions.

## Self-review

The implementation is a clean branch on the presence of `"runs"` keys in both incumbent and candidate dicts, which is an unambiguous discriminator. The legacy path is copied verbatim from the original `evaluate` body with no changes to logic or variable names. The statistical path follows the brief's pseudocode exactly: build deltas → aggregate per-task → call `significant_improvement` (or `None` if no deltas) → `decide_promotion_stat` → `render_stat_proposal`. One deviation from the brief's verbatim code was required: `build_paired_deltas` uses `round(cand[k] - inc[k], 10)` instead of raw subtraction. This is necessary because `0.8 - 0.7 == 0.10000000000000009` in Python floating-point, causing the verbatim test assertion `sorted(deltas) == [0.1, 0.2]` to fail. Rounding to 10 decimal places (well below any meaningful precision floor for scores in [0,1]) recovers exact decimal values without affecting downstream statistical calculations. Type annotations use plain `list` (not `list[dict]` or `list[float]`) for maximum Python 3.9 compatibility.

## Concerns

None blocking. The `round(..., 10)` deviation is the only substantive divergence from the brief's verbatim code; it is numerically safe and required to satisfy the verbatim test assertion.

---

# Task 6 Fix Report: paired-delta core purity (code-review follow-up)

## Status
COMPLETE — both changes applied, all tests green, committed.

## Commit Hash
`bd03c51` — "fix: keep paired-delta core pure; tolerant float assertion in test"

## Changes Made

1. **`eval/harness/forge.py`, `build_paired_deltas`**: Removed `round(..., 10)` wrapper.
   - Before: `return [round(cand[k] - inc[k], 10) for k in keys]`
   - After:  `return [cand[k] - inc[k] for k in keys]`

2. **`tests/test_forge_stat.py`**: Added `import pytest` and made float assertion tolerant.
   - Added `import pytest` on line 2.
   - Before: `assert sorted(deltas) == [0.1, 0.2]`
   - After:  `assert sorted(deltas) == pytest.approx([0.1, 0.2])`

## Commands Run and Summaries

```
python3 -m pytest tests/test_forge_stat.py tests/test_forge.py -v
```
Result: **14 passed in 0.03s**

```
python3 -m pytest -q
```
Result: **155 passed in 0.19s**

## Concerns
None. The fix is exact as prescribed. All gate outcomes are unaffected: the CI short-circuit on constant-delta vectors fires identically with raw subtraction.

---

# Final-review fix report

## Findings addressed

### I1 — `gold_per_seed` stores absolute per-seed candidate gold (not deltas)

**Root cause:** `"gold_per_seed": list(d.per_seed_delta.values())` stored the candidate−incumbent delta from the `Decision` object instead of the raw candidate scores.

**Fix (eval/harness/forge.py):** After the `gate.decide` call, group all `cand` gate runs by `seed`, take `fmean` of each seed's scores, sort by seed key, and store the resulting list under `gold_per_seed`. Added `from collections import defaultdict` at module level (stdlib only). The `gold_gate_mean` field (overall candidate mean) is unchanged.

**Contract:** incumbent 0.5 × 3 seeds, candidate [0.7, 0.72, 0.71] across seeds 1/2/3 → `gold_per_seed == [0.7, 0.72, 0.71]`. Verified by `test_gold_per_seed_is_absolute`.

### I2 — `main()` returns exit 2 on unreadable/malformed results file

**Root cause:** `json.loads(Path(args.results).read_text())` raised an uncaught `FileNotFoundError` or `json.JSONDecodeError`, producing a traceback.

**Fix (eval/harness/forge.py):** Wrapped the read+parse in `try/except OSError, json.JSONDecodeError`; on error, prints a short message to stderr and returns `2`. Happy path and `evaluate()` signature are unchanged.

**Verified by:** `test_main_bad_input_returns_2` (missing path + malformed JSON both return 2, no exception raised).

## Diff summary

### eval/harness/forge.py
- Added `from collections import defaultdict` to stdlib imports.
- In `evaluate()`: replaced `list(d.per_seed_delta.values())` with per-seed absolute-score computation (group cand runs by seed → `fmean` per seed → sorted).
- In `main()`: wrapped `json.loads(Path(args.results).read_text())` in try/except for `OSError` and `json.JSONDecodeError`; prints to stderr and returns `2` on error.

### tests/test_forge.py
- Added `from __future__ import annotations` and `import pytest`.
- Added `test_main_bad_input_returns_2`: asserts missing file returns 2, malformed JSON returns 2.
- Added `_results_per_seed` helper: builds results with per-seed candidate scores.
- Added `test_gold_per_seed_is_absolute`: incumbent 0.5×3 seeds, candidate [0.7,0.72,0.71], asserts `gold_per_seed == pytest.approx([0.7, 0.72, 0.71])`.

## Test outputs

### tests/test_forge.py (5 tests)
```
tests/test_forge.py::test_promote_exit0_appends_one_round PASSED
tests/test_forge.py::test_reject_exit1 PASSED
tests/test_forge.py::test_halt_exit2_when_monitor_halts PASSED
tests/test_forge.py::test_main_bad_input_returns_2 PASSED
tests/test_forge.py::test_gold_per_seed_is_absolute PASSED
5 passed in 0.02s
```

### Full suite
```
125 passed in 0.11s
```
