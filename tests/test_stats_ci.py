import pytest
from eval.harness.stats import (
    paired_bootstrap_ci,
    significant_improvement,
    StatVerdict,
    _norm_ppf,
    _norm_cdf,
)


def test_norm_helpers():
    assert _norm_ppf(0.975) == pytest.approx(1.959964, abs=1e-3)
    assert _norm_cdf(1.959964) == pytest.approx(0.975, abs=1e-3)


def test_norm_ppf_rejects_bounds():
    with pytest.raises(ValueError):
        _norm_ppf(0.0)


def test_ci_empty_raises():
    with pytest.raises(ValueError):
        paired_bootstrap_ci([])


def test_ci_constant_is_degenerate():
    lo, hi = paired_bootstrap_ci([0.1] * 6)
    assert lo == pytest.approx(0.1)
    assert hi == pytest.approx(0.1)


def test_ci_strong_positive_excludes_zero():
    deltas = [0.2, 0.25, 0.15, 0.30, 0.22, 0.18, 0.27, 0.21]
    lo, hi = paired_bootstrap_ci(deltas, seed=0)
    assert lo > 0.0
    assert lo <= sum(deltas) / len(deltas) <= hi


def test_ci_symmetric_includes_zero():
    deltas = [0.3, -0.3, 0.25, -0.25, 0.1, -0.1, 0.2, -0.2]
    lo, hi = paired_bootstrap_ci(deltas, seed=0)
    assert lo < 0.0 < hi


def test_ci_is_deterministic():
    deltas = [0.2, -0.05, 0.1, 0.15, -0.1, 0.3, 0.05, 0.12]
    assert paired_bootstrap_ci(deltas, seed=3) == paired_bootstrap_ci(deltas, seed=3)


def test_significant_when_powered():
    v = significant_improvement([0.1] * 6, alpha=0.05, n_candidates=1)
    assert isinstance(v, StatVerdict)
    assert v.p_value == pytest.approx(2 / 64)
    assert v.ci_low > 0
    assert v.significant


def test_underpowered_five_not_significant():
    v = significant_improvement([0.1] * 5, alpha=0.05, n_candidates=1)
    assert not v.significant  # p = 0.0625 >= 0.05


def test_bonferroni_flips_decision():
    # p = 0.03125: significant at alpha=0.05, not at 0.05/3 = 0.0167.
    assert significant_improvement([0.1] * 6, alpha=0.05, n_candidates=1).significant
    assert not significant_improvement([0.1] * 6, alpha=0.05, n_candidates=3).significant


def test_zero_effect_not_significant():
    v = significant_improvement([0.0] * 8)
    assert v.mean_delta == pytest.approx(0.0)
    assert not v.significant
