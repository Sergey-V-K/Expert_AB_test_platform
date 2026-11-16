"""Tests for engine/stats.py.

Reference values come from independent sources:
- statsmodels (z-test, Wald and Newcombe CIs),
- scipy (Welch),
- numbers checked by hand in the design thread (SRM cases).
These tests fail until the engine is written. That is expected.
"""

import pytest
from scipy import stats as sps
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportions_ztest,
)

from engine import stats

# (conv_c, n_c, conv_t, n_t)
BINARY_CASES = [
    (56500, 500000, 56250, 500000),  # default form values
    (4, 50, 11, 50),                 # p near alpha
    (500, 2500, 425, 2500),          # significant harm
]


@pytest.mark.parametrize("conv_c,n_c,conv_t,n_t", BINARY_CASES)
def test_binary_superiority_matches_statsmodels(conv_c, n_c, conv_t, n_t):
    r = stats.binary_superiority(conv_c, n_c, conv_t, n_t, alpha=0.05)

    _, p_ref = proportions_ztest([conv_t, conv_c], [n_t, n_c])  # pooled
    low_ref, high_ref = confint_proportions_2indep(
        conv_t, n_t, conv_c, n_c, method="wald", compare="diff", alpha=0.05
    )
    assert r.p_value == pytest.approx(p_ref, rel=1e-6)
    assert r.ci.low == pytest.approx(low_ref, abs=1e-9)
    assert r.ci.high == pytest.approx(high_ref, abs=1e-9)
    assert r.ci.level == pytest.approx(0.95)


def test_newcombe_matches_statsmodels():
    ci = stats.newcombe_ci(1, 330, 1, 370, level=0.95)
    low_ref, high_ref = confint_proportions_2indep(
        1, 370, 1, 330, method="newcomb", compare="diff", alpha=0.05
    )
    assert ci.low == pytest.approx(low_ref, abs=1e-9)
    assert ci.high == pytest.approx(high_ref, abs=1e-9)


def test_low_counts_returns_newcombe():
    r = stats.binary_superiority(1, 330, 1, 370, alpha=0.05)
    assert r.low_counts is True
    assert r.newcombe_ci is not None


def test_binary_ni_uses_one_sided_alpha():
    # alpha = 0.05 one-sided -> 90% two-sided CI
    r = stats.binary_non_inferiority(500, 2500, 425, 2500, margin=0.04, alpha=0.05)
    low_ref, _ = confint_proportions_2indep(
        425, 2500, 500, 2500, method="wald", compare="diff", alpha=0.10
    )
    assert r.ci.level == pytest.approx(0.90)
    assert r.ci.low == pytest.approx(low_ref, abs=1e-9)  # about -0.048
    assert r.non_inferior is False and r.inferior is False


def test_continuous_superiority_matches_scipy_welch():
    r = stats.continuous_superiority(100.0, 40.0, 1000, 104.0, 55.0, 1200, alpha=0.05)
    ref = sps.ttest_ind_from_stats(104.0, 55.0, 1200, 100.0, 40.0, 1000, equal_var=False)
    assert r.p_value == pytest.approx(ref.pvalue, rel=1e-6)


@pytest.mark.parametrize(
    "n_c,n_t,ratio,should_fail",
    [
        (821588, 815482, 1.0, True),    # Kohavi / Fabijan example, p ~ 1.8e-6
        (500000, 504000, 1.0, True),    # 0.8% imbalance, p ~ 6.6e-5
        (500000, 500000, 1.0, False),
        (100000, 900000, 9.0, False),   # planned 10/90 split
        (100000, 900000, 1.0, True),    # same split, ratio not set
        (330, 370, 1.0, False),         # small sample, p ~ 0.13
    ],
)
def test_srm(n_c, n_t, ratio, should_fail):
    assert stats.srm_check(n_c, n_t, expected_ratio=ratio).failed is should_fail


def test_srm_kohavi_p_value():
    assert stats.srm_check(821588, 815482).p_value == pytest.approx(1.8e-6, rel=0.05)


def test_to_absolute():
    assert stats.to_absolute(0.003, "abs", baseline=0.113) == pytest.approx(0.003)
    assert stats.to_absolute(0.02, "rel", baseline=0.113) == pytest.approx(0.00226)


def test_borderline_flags_lower_is_better_flips():
    ci = stats.Interval(-0.0103, -0.0005, 0.95)     # better when lower
    ni_ci = stats.Interval(-0.0095, -0.0018, 0.90)
    flags = stats.borderline_flags(0.02, 0.05, ci, margin=0.0, threshold=0.0099,
                                   ni_ci=ni_ci, higher_is_better=False)
    assert "ci_near_threshold" in flags
    assert "ci_near_zero" in flags
