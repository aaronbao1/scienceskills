from __future__ import annotations


def overoptimization_halt(rounds: list[dict], lookback: int = 2, eps: float = 1e-9) -> dict:
    """Halt when the proxy (judge/dev) score rises while the gold (ground-truth) score stalls/drops.

    Detects divergence empirically over the last `lookback`+1 rounds — no closed-form Goodhart
    curve is assumed. Each round has `proxy` and `gold`.
    """
    if len(rounds) < lookback + 1:
        return {"halt": False, "reason": "insufficient history"}
    window = rounds[-(lookback + 1):]
    proxies = [r["proxy"] for r in window]
    golds = [r["gold"] for r in window]
    proxy_up = all(proxies[i + 1] > proxies[i] + eps for i in range(len(proxies) - 1))
    gold_down = all(golds[i + 1] <= golds[i] + eps for i in range(len(golds) - 1))
    if proxy_up and gold_down:
        return {
            "halt": True,
            "reason": (
                f"proxy rising ({proxies[0]:.3f}->{proxies[-1]:.3f}) while gold "
                f"stalls/drops ({golds[0]:.3f}->{golds[-1]:.3f})"
            ),
        }
    return {"halt": False, "reason": "no proxy/gold divergence"}


def judge_only_streak_exceeded(promotions: list[str], cap: int = 3) -> bool:
    """True when the trailing run of consecutive 'judge_only' promotions exceeds `cap`."""
    streak = 0
    for promotion in reversed(promotions):
        if promotion == "judge_only":
            streak += 1
        else:
            break
    return streak > cap
