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
    d = decide_promotion(0.50, 0.52, [_task("t1", 0.5, 0.52)], margin=0.02)
    assert d.promote


def test_nominal_margin_gain_promotes_despite_float_error():
    # 0.82 - 0.80 == 0.019999999999999907 in IEEE-754; a nominal 0.02 gain must promote
    d = decide_promotion(0.80, 0.82, [_task("t1", 0.80, 0.82)], margin=0.02)
    assert d.promote
