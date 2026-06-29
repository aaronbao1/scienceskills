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
    if delta < margin - 1e-9:
        return PromotionDecision(False, f"insufficient gain: +{delta:.3f} < margin {margin}")
    return PromotionDecision(True, f"promote: +{delta:.3f} over incumbent, no critical regression")


def decide_promotion_stat(verdict, per_task: list[dict]) -> PromotionDecision:
    """Promote only on a statistically significant gain with no critical-task regression.

    `verdict` is a stats.StatVerdict or None (no held-out observations). The critical
    veto is checked first so a ground-truth regression always blocks promotion.
    """
    regressions = [
        t["task_id"]
        for t in per_task
        if t.get("critical") and t["candidate"] < t["incumbent"] - 1e-9
    ]
    if regressions:
        return PromotionDecision(False, f"critical regression on: {', '.join(regressions)}")
    if verdict is None:
        return PromotionDecision(False, "no held-out (gate) observations to test")
    detail = (
        f"mean {verdict.mean_delta:+.3f}, CI low {verdict.ci_low:+.3f}, "
        f"p={verdict.p_value:.3f}, alpha={verdict.alpha:.3f}"
    )
    if not verdict.significant:
        return PromotionDecision(False, f"not significant: {detail}")
    return PromotionDecision(True, f"promote: {detail} (CI low > 0 and p < alpha)")
