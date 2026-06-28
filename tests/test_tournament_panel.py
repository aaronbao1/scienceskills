import pytest
from eval.harness.tournament import (
    resolve_swapped,
    aggregate_panel,
    panel_disagreement,
    TournamentError,
)


def test_resolve_swapped_consistent_wins():
    assert resolve_swapped("candidate", "candidate") == "candidate"
    assert resolve_swapped("incumbent", "incumbent") == "incumbent"


def test_resolve_swapped_disagreement_is_tie():
    assert resolve_swapped("candidate", "incumbent") == "tie"
    assert resolve_swapped("incumbent", "candidate") == "tie"
    assert resolve_swapped("tie", "tie") == "tie"


def test_resolve_swapped_invalid_raises():
    with pytest.raises(TournamentError):
        resolve_swapped("candidate", "nobody")


def test_aggregate_panel_majority():
    assert aggregate_panel(["candidate", "candidate", "incumbent"]) == "candidate"
    assert aggregate_panel(["candidate", "candidate", "tie"]) == "candidate"


def test_aggregate_panel_no_majority_is_tie():
    assert aggregate_panel(["candidate", "incumbent", "tie"]) == "tie"
    assert aggregate_panel(["candidate", "candidate", "incumbent", "incumbent"]) == "tie"


def test_aggregate_panel_empty_raises():
    with pytest.raises(TournamentError):
        aggregate_panel([])


def test_panel_disagreement():
    assert panel_disagreement(["candidate", "candidate", "candidate"]) == pytest.approx(0.0)
    assert panel_disagreement(["candidate", "candidate", "incumbent"]) == pytest.approx(1 / 3)
