from __future__ import annotations


def render_promotion_proposal(
    skill: str,
    incumbent_overall: float,
    candidate_overall: float,
    decision,
    tournament: dict,
    per_task: list[dict],
) -> str:
    """Render a human-facing promotion proposal as markdown."""
    verdict = "PROMOTE" if decision.promote else "REJECT"
    lines = [
        f"# Promotion proposal — {skill}",
        "",
        f"- Incumbent overall: {incumbent_overall:.3f}",
        f"- Candidate overall: {candidate_overall:.3f}",
        f"- Delta: {candidate_overall - incumbent_overall:+.3f}",
        f"- Decision: {verdict} — {decision.reason}",
        "",
        "## A/B tournament",
        (
            f"- candidate wins {tournament['candidate_wins']}, "
            f"incumbent wins {tournament['incumbent_wins']}, "
            f"ties {tournament['ties']} "
            f"(candidate win rate {tournament['candidate_win_rate']:.2f})"
        ),
        "",
        "## Per-task",
        "| task | incumbent | candidate | critical |",
        "| --- | --- | --- | --- |",
    ]
    for t in per_task:
        crit = "yes" if t.get("critical") else "no"
        lines.append(f"| {t['task_id']} | {t['incumbent']:.2f} | {t['candidate']:.2f} | {crit} |")
    return "\n".join(lines) + "\n"
