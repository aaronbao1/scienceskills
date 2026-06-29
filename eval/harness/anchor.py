from __future__ import annotations

from eval.harness.stats import significant_improvement


def accumulate_anchor(seed_ids: list[str], current_ids: list[str]) -> dict:
    """Verify the permanent ground-truth seed is still present; report any dropped anchors."""
    present = set(current_ids)
    missing = [s for s in seed_ids if s not in present]
    return {"intact": not missing, "missing": missing}


def should_refresh_benchmark(dev_gate_deltas: list[float], alpha: float = 0.05, seed: int = 0) -> dict:
    """Refresh when dev performance has significantly outrun the held-out gate (benchmark inflation).

    `dev_gate_deltas` is the per-task (dev_score - gate_score). A significant positive gap means
    the dev set no longer reflects held-out reality — regenerate fresh ground-truth tasks.
    """
    if not dev_gate_deltas:
        return {"refresh": False, "reason": "no data"}
    verdict = significant_improvement(dev_gate_deltas, alpha=alpha, seed=seed)
    if verdict.significant:
        return {
            "refresh": True,
            "reason": f"dev-gate gap significant (mean {verdict.mean_delta:+.3f}, p={verdict.p_value:.3f})",
        }
    return {"refresh": False, "reason": f"dev-gate gap not significant (p={verdict.p_value:.3f})"}
