# eval/harness/gate.py
"""Single deterministic promotion decision for skill-forge."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass
class Decision:
    promote: bool
    reason: str
    mean_delta: float
    per_seed_delta: dict
    noise_floor: float
    critical_regression: bool


def decide(incumbent_runs, candidate_runs, *, eps=1e-9, use_sign_test=False, alpha=0.05) -> Decision:
    inc = {(r["task_id"], r["seed"]): r for r in incumbent_runs}
    cand = {(r["task_id"], r["seed"]): r for r in candidate_runs}
    keys = sorted(set(inc) & set(cand))
    if not keys:
        return Decision(False, "no paired runs", 0.0, {}, 0.0, False)

    critical = False
    for k in keys:
        if (inc[k].get("critical") or cand[k].get("critical")) and cand[k]["score"] < inc[k]["score"]:
            critical = True
            break

    deltas = {k: cand[k]["score"] - inc[k]["score"] for k in keys}
    mean_delta = fmean(deltas.values())
    seeds = sorted({s for (_, s) in keys})
    per_seed = {s: fmean([deltas[k] for k in keys if k[1] == s]) for s in seeds}
    inc_seed_means = [fmean([inc[k]["score"] for k in keys if k[1] == s]) for s in seeds]
    noise_floor = max(pstdev(inc_seed_means) if len(inc_seed_means) > 1 else 0.0, eps)

    if critical:
        return Decision(False, "critical-task regression", mean_delta, per_seed, noise_floor, True)

    reasons = []
    if not mean_delta > 0:
        reasons.append("mean delta not positive")
    wins_every_seed = all(d > 0 for d in per_seed.values())
    if not wins_every_seed:
        reasons.append("loses on >=1 seed")
    beats_noise = mean_delta > noise_floor
    if not beats_noise:
        reasons.append(f"gain {mean_delta:.4f} <= noise floor {noise_floor:.4f}")

    promote = (mean_delta > 0) and wins_every_seed and beats_noise
    if promote and use_sign_test:
        from scipy.stats import wilcoxon
        try:
            _, p = wilcoxon(list(deltas.values()))
            if p >= alpha:
                promote = False
                reasons.append(f"sign test p={p:.3f} >= alpha")
        except ValueError:
            pass

    return Decision(promote, "promote" if promote else "; ".join(reasons), mean_delta, per_seed,
                    noise_floor, False)
