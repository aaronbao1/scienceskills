from __future__ import annotations

import math
import random


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
