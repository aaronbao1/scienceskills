import pytest
from eval.harness.stats import bonferroni_alpha, paired_permutation_pvalue


def test_bonferroni_alpha():
    assert bonferroni_alpha(0.05, 1) == pytest.approx(0.05)
    assert bonferroni_alpha(0.05, 3) == pytest.approx(0.05 / 3)


def test_bonferroni_alpha_rejects_bad_n():
    with pytest.raises(ValueError):
        bonferroni_alpha(0.05, 0)


def test_permutation_empty_raises():
    with pytest.raises(ValueError):
        paired_permutation_pvalue([])


def test_permutation_all_zero_is_one():
    assert paired_permutation_pvalue([0.0, 0.0, 0.0]) == pytest.approx(1.0)


def test_permutation_exact_six_equal_positive():
    # n=6 equal +0.1: only all-+ and all-- reach |obs|; 2/64.
    assert paired_permutation_pvalue([0.1] * 6) == pytest.approx(2 / 64)


def test_permutation_exact_five_underpowered():
    # n=5 cannot clear 0.05 with a sign test: 2/32 = 0.0625.
    assert paired_permutation_pvalue([0.1] * 5) == pytest.approx(2 / 32)


def test_permutation_monte_carlo_is_seeded_and_deterministic():
    deltas = [0.05 * (i % 3 - 1) + 0.2 for i in range(25)]  # n=25 > max_exact -> MC
    p1 = paired_permutation_pvalue(deltas, max_exact=18, n_mc=2000, seed=7)
    p2 = paired_permutation_pvalue(deltas, max_exact=18, n_mc=2000, seed=7)
    assert p1 == p2
    assert 0.0 <= p1 <= 1.0
