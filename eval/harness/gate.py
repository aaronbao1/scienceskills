from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    reason: str


def decide_promotion(
    incumbent_overall: float,
    candidate_overall: float,
    per_task: list[dict],
    margin: float = 0.02,
) -> PromotionDecision:
    """Promote only on a clear overall gain with no critical-task regression."""
    regressions = [
        t["task_id"]
        for t in per_task
        if t.get("critical") and t["candidate"] < t["incumbent"]
    ]
    if regressions:
        return PromotionDecision(False, f"critical regression on: {', '.join(regressions)}")
    delta = candidate_overall - incumbent_overall
    if delta < margin:
        return PromotionDecision(False, f"insufficient gain: +{delta:.3f} < margin {margin}")
    return PromotionDecision(True, f"promote: +{delta:.3f} over incumbent, no critical regression")
