# tests/test_gate.py
from eval.harness.gate import decide

def _runs(scores_by_seed, critical=False):
    # scores_by_seed: {seed: [(task_id, score), ...]}
    out = []
    for seed, pairs in scores_by_seed.items():
        for task_id, score in pairs:
            out.append({"task_id": task_id, "seed": seed, "score": score, "critical": critical})
    return out

def test_promote_when_wins_every_seed_above_noise():
    inc = _runs({1: [("t", 0.50)], 2: [("t", 0.50)], 3: [("t", 0.50)]})
    cand = _runs({1: [("t", 0.70)], 2: [("t", 0.72)], 3: [("t", 0.71)]})
    d = decide(inc, cand)
    assert d.promote and d.mean_delta > d.noise_floor

def test_reject_sub_noise_gain():
    inc = _runs({1: [("t", 0.40)], 2: [("t", 0.60)], 3: [("t", 0.50)]})  # noisy incumbent
    cand = _runs({1: [("t", 0.41)], 2: [("t", 0.61)], 3: [("t", 0.51)]})  # tiny gain
    d = decide(inc, cand)
    assert not d.promote and "noise floor" in d.reason

def test_critical_regression_vetoes():
    inc = _runs({1: [("t", 0.50)]}, critical=True)
    cand = _runs({1: [("t", 0.40)]}, critical=True)
    d = decide(inc, cand)
    assert not d.promote and d.critical_regression

def test_reject_when_loses_one_seed():
    inc = _runs({1: [("t", 0.50)], 2: [("t", 0.50)]})
    cand = _runs({1: [("t", 0.70)], 2: [("t", 0.45)]})  # regresses on seed 2
    d = decide(inc, cand)
    assert not d.promote and "seed" in d.reason
