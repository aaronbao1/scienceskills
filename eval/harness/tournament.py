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


def resolve_swapped(first: str, second: str) -> str:
    """Collapse a position-swapped pair of verdicts into one bias-robust winner.

    `first` = winner when the incumbent is shown first; `second` = winner when the candidate
    is shown first. A side wins only if it wins in BOTH orders; any disagreement is a tie.
    """
    if first not in VALID_WINNERS or second not in VALID_WINNERS:
        raise TournamentError(f"invalid swapped verdict: {first!r}, {second!r}")
    return first if first == second else "tie"


def aggregate_panel(verdicts: list[str]) -> str:
    """Strict-plurality panel winner over order-resolved verdicts; ties on no strict plurality."""
    if not verdicts:
        raise TournamentError("empty panel")
    for verdict in verdicts:
        if verdict not in VALID_WINNERS:
            raise TournamentError(f"invalid verdict: {verdict!r}")
    cand = verdicts.count("candidate")
    inc = verdicts.count("incumbent")
    tie = verdicts.count("tie")
    if cand > inc and cand > tie:
        return "candidate"
    if inc > cand and inc > tie:
        return "incumbent"
    return "tie"


def panel_disagreement(verdicts: list[str]) -> float:
    """Fraction of judges whose verdict differs from the aggregated panel verdict (0 = unanimous)."""
    if not verdicts:
        raise TournamentError("empty panel")
    decision = aggregate_panel(verdicts)
    return 1.0 - verdicts.count(decision) / len(verdicts)


def check_panel_independence(
    judge_families: list[str],
    agent_family,
    min_judges: int = 3,
    min_families: int = 3,
) -> dict:
    """Validate a judge panel: enough judges, enough distinct families, none sharing the agent's."""
    families = list(judge_families)
    reasons: list[str] = []
    if len(families) < min_judges:
        reasons.append(f"only {len(families)} judges (need >= {min_judges})")
    if len(set(families)) < min_families:
        reasons.append(f"only {len(set(families))} distinct families (need >= {min_families})")
    if agent_family in families:
        reasons.append(f"a judge shares the agent family: {agent_family}")
    return {"independent": not reasons, "reasons": reasons}


def verbosity_flag(
    winner: str,
    incumbent_chars: int,
    candidate_chars: int,
    ratio: float = 1.25,
) -> bool:
    """True when the winning side's output is >= ratio times the loser's length (possible length bias)."""
    if winner == "candidate":
        return candidate_chars >= ratio * max(incumbent_chars, 1)
    if winner == "incumbent":
        return incumbent_chars >= ratio * max(candidate_chars, 1)
    return False
