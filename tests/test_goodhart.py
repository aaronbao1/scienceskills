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
