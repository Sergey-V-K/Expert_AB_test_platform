"""Tests for engine/design.py.

NI reference: Sealed Envelope formula (Blackwelder), one-sided alpha.
Superiority reference: standard normal-approximation formula (statsmodels).
Cross-checks with the public calculators (Evan Miller, Sealed Envelope):
tests/test_acceptance.py.
"""

import pytest

from engine import design


@pytest.mark.parametrize(
    "alpha,expected",
    [
        # Exact Blackwelder formula. The Sealed Envelope tool shows 648,079 at
        # alpha 5%: it rounds z, +0.04%. Tool check: tests/test_acceptance.py.
        (0.05, 647806),
        (0.025, 822402),
    ],
)
def test_binary_ni_n_matches_sealed_envelope(alpha, expected):
    r = design.binary_non_inferiority_n(0.0021, 0.0002, alpha=alpha, power=0.8)
    assert r.n_control == pytest.approx(expected, abs=2)


@pytest.mark.parametrize(
    "baseline,mde,ratio,expected_n_c",
    [
        (0.113, 0.001, 1.0, 1579473),
        (0.20, 0.02, 1.0, 6510),
        (0.20, 0.02, 4.0, 4102),  # unequal split, weighted p_bar
    ],
)
def test_binary_superiority_n(baseline, mde, ratio, expected_n_c):
    r = design.binary_superiority_n(baseline, mde, alpha=0.05, power=0.8, ratio=ratio)
    assert r.n_control == pytest.approx(expected_n_c, abs=2)


def test_duration_rounds_to_full_weeks():
    d = design.duration(n_total=100_000, daily_traffic=10_000)
    assert d.days_by_traffic == 10
    assert d.days_recommended == 14


def test_detectable_effect_is_inverse_of_sample_size():
    n = design.binary_superiority_n(0.20, 0.02, alpha=0.05, power=0.8).n_control
    mde = design.detectable_effect(
        n, ratio=1.0, alpha=0.05, power=0.8,
        test="superiority", metric_type="binary", baseline=0.20,
    )
    assert mde == pytest.approx(0.02, rel=1e-3)
