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
