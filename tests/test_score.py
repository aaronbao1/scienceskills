import pytest
from eval.harness.score import score_output, ScoreResult


def test_exact_match():
    r = score_output("exact", "hello", " hello ")
    assert isinstance(r, ScoreResult)
    assert r.passed and r.score == 1.0


def test_exact_mismatch():
    assert not score_output("exact", "a", "b").passed


def test_numeric_within_tolerance():
    assert score_output("numeric", 2.0, "2.0005", tolerance=0.001).passed


def test_numeric_outside_tolerance():
    assert not score_output("numeric", 2.0, "2.5", tolerance=0.001).passed


def test_numeric_non_numeric_actual():
    assert not score_output("numeric", 2.0, "not a number", tolerance=0.1).passed


def test_contains():
    assert score_output("contains", "needle", "a needle in hay").passed


def test_regex():
    assert score_output("regex", r"\d{3}", "abc123").passed


def test_unknown_scorer_raises():
    with pytest.raises(ValueError):
        score_output("bogus", 1, "1")
