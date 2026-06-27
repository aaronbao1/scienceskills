import pytest
from eval.harness.tournament import tally_tournament, TournamentError


def test_tally_counts_and_rate():
    verdicts = [
        {"task_id": "t1", "winner": "candidate"},
        {"task_id": "t2", "winner": "candidate"},
        {"task_id": "t3", "winner": "incumbent"},
        {"task_id": "t4", "winner": "tie"},
    ]
    out = tally_tournament(verdicts)
    assert out["candidate_wins"] == 2
    assert out["incumbent_wins"] == 1
    assert out["ties"] == 1
    assert out["candidate_win_rate"] == pytest.approx(0.5)


def test_invalid_winner_raises():
    with pytest.raises(TournamentError):
        tally_tournament([{"task_id": "t1", "winner": "nobody"}])


def test_empty_is_zero_rate():
    out = tally_tournament([])
    assert out["candidate_win_rate"] == 0.0
