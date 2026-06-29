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


def render_stat_proposal(
    skill: str,
    verdict,
    decision,
    tournament: dict,
    per_task: list[dict],
    n_obs: int,
) -> str:
    """Render a human-facing statistical promotion proposal as markdown."""
    result = "PROMOTE" if decision.promote else "REJECT"
    lines = [
        f"# Promotion proposal — {skill}",
        "",
        f"- Decision: {result} — {decision.reason}",
        f"- Held-out observations: {n_obs}",
    ]
    if verdict is not None:
        lines += [
            f"- Mean held-out delta: {verdict.mean_delta:+.3f}",
            f"- Bootstrap CI: [{verdict.ci_low:+.3f}, {verdict.ci_high:+.3f}]",
            f"- Permutation p = {verdict.p_value:.3f} (alpha = {verdict.alpha:.3f}, Bonferroni-corrected)",
        ]
    else:
        lines.append("- Statistical test: not run (no held-out gate observations)")
    lines += [
        "",
        "## A/B tournament",
        (
            f"- candidate wins {tournament['candidate_wins']}, "
            f"incumbent wins {tournament['incumbent_wins']}, "
            f"ties {tournament['ties']} "
            f"(candidate win rate {tournament['candidate_win_rate']:.2f})"
        ),
        "",
        "## Per held-out task (seed-averaged)",
        "| task | incumbent | candidate | critical |",
        "| --- | --- | --- | --- |",
    ]
    for t in per_task:
        crit = "yes" if t.get("critical") else "no"
        lines.append(f"| {t['task_id']} | {t['incumbent']:.2f} | {t['candidate']:.2f} | {crit} |")
    return "\n".join(lines) + "\n"
