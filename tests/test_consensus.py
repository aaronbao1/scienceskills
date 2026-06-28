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
