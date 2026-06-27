from __future__ import annotations

VALID_WINNERS = {"candidate", "incumbent", "tie"}


class TournamentError(ValueError):
    """Raised when a tournament verdict is malformed."""


def tally_tournament(verdicts: list[dict]) -> dict:
    """Tally head-to-head verdicts into win/loss/tie counts and a candidate win rate."""
    for verdict in verdicts:
        if verdict.get("winner") not in VALID_WINNERS:
            raise TournamentError(f"invalid winner: {verdict.get('winner')!r}")
    candidate = sum(1 for v in verdicts if v["winner"] == "candidate")
    incumbent = sum(1 for v in verdicts if v["winner"] == "incumbent")
    ties = sum(1 for v in verdicts if v["winner"] == "tie")
    total = len(verdicts)
    return {
        "candidate_wins": candidate,
        "incumbent_wins": incumbent,
        "ties": ties,
        "candidate_win_rate": candidate / total if total else 0.0,
    }
