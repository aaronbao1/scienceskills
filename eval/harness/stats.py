from __future__ import annotations

import math
import random
from dataclasses import dataclass


def bonferroni_alpha(alpha: float, n_comparisons: int) -> float:
    """Bonferroni-correct a significance level for n simultaneous comparisons."""
    if n_comparisons < 1:
        raise ValueError("n_comparisons must be >= 1")
    return alpha / n_comparisons


def paired_permutation_pvalue(
    deltas: list[float],
    max_exact: int = 18,
    n_mc: int = 20000,
    seed: int = 0,
) -> float:
    """Two-sided paired sign-flip permutation test on per-item deltas.

    Statistic is the sum of deltas; under H0 each delta's sign is equally likely.
    Exact enumeration of all 2**n sign assignments when n <= max_exact, else a
    seeded Monte-Carlo estimate with add-one smoothing.
    """
    n = len(deltas)
    if n == 0:
        raise ValueError("no deltas")
    obs = abs(sum(deltas))
    eps = 1e-12
    if n <= max_exact:
        total = 1 << n
        count = 0
        for mask in range(total):
            s = 0.0
            for i in range(n):
                s += deltas[i] if (mask >> i) & 1 else -deltas[i]
            if abs(s) >= obs - eps:
                count += 1
        return count / total
    rng = random.Random(seed)
    count = 0
    for _ in range(n_mc):
        s = 0.0
        for d in deltas:
            s += d if rng.random() < 0.5 else -d
        if abs(s) >= obs - eps:
            count += 1
    return (1 + count) / (1 + n_mc)


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Standard normal inverse CDF (Acklam's rational approximation)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Linear-interpolated percentile of an already-sorted list (pct in [0, 100])."""
    if not sorted_vals:
        raise ValueError("empty")
    if pct <= 0:
        return sorted_vals[0]
    if pct >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def paired_bootstrap_ci(
    deltas: list[float],
    confidence: float = 0.95,
    n_boot: int = 10000,
    seed: int = 0,
    method: str = "bca",
) -> tuple[float, float]:
    """Bootstrap CI for the mean of paired deltas (BCa by default, else percentile)."""
    n = len(deltas)
    if n == 0:
        raise ValueError("no deltas")
    mean = sum(deltas) / n
    if max(deltas) - min(deltas) == 0.0:  # constant: CI is degenerate
        return (mean, mean)
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += deltas[rng.randrange(n)]
        boots.append(s / n)
    boots.sort()
    alpha = 1.0 - confidence
    if method == "percentile":
        return (_percentile(boots, 100 * alpha / 2), _percentile(boots, 100 * (1 - alpha / 2)))
    # BCa
    below = sum(1 for b in boots if b < mean) / n_boot
    below = min(max(below, 1e-9), 1.0 - 1e-9)
    z0 = _norm_ppf(below)
    total = sum(deltas)
    jack = [(total - deltas[i]) / (n - 1) for i in range(n)]
    jbar = sum(jack) / n
    num = sum((jbar - j) ** 3 for j in jack)
    den = 6.0 * (sum((jbar - j) ** 2 for j in jack) ** 1.5)
    a = num / den if den != 0 else 0.0

    def adj(z_alpha: float) -> float:
        z = z0 + (z0 + z_alpha) / (1.0 - a * (z0 + z_alpha))
        return _norm_cdf(z)

    lo_p = adj(_norm_ppf(alpha / 2))
    hi_p = adj(_norm_ppf(1.0 - alpha / 2))
    return (_percentile(boots, 100 * lo_p), _percentile(boots, 100 * hi_p))


@dataclass(frozen=True)
class StatVerdict:
    mean_delta: float
    ci_low: float
    ci_high: float
    p_value: float
    alpha: float
    significant: bool


def significant_improvement(
    deltas: list[float],
    alpha: float = 0.05,
    n_candidates: int = 1,
    n_boot: int = 10000,
    seed: int = 0,
    method: str = "bca",
) -> StatVerdict:
    """Promote-worthy iff BCa lower bound > 0 AND permutation p < Bonferroni alpha."""
    if not deltas:
        raise ValueError("no deltas")
    ac = bonferroni_alpha(alpha, n_candidates)
    p = paired_permutation_pvalue(deltas, seed=seed)
    lo, hi = paired_bootstrap_ci(deltas, confidence=1.0 - ac, n_boot=n_boot, seed=seed, method=method)
    mean = sum(deltas) / len(deltas)
    return StatVerdict(mean, lo, hi, p, ac, (lo > 0.0) and (p < ac))
