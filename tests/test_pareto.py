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
