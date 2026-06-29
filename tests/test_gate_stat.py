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
