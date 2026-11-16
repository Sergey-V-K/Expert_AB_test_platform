"""Tests for engine/decision.py. Rows follow SPEC Step 4 (Colab outcomes, renamed labels, row 6)."""

import pytest

from engine import decision
from engine.decision import NonInferiority, Row, Superiority, Threshold
from engine.stats import Interval, NonInferiorityResult, SRMResult, SuperiorityResult


def sup(low, high):
    diff = (low + high) / 2
    return SuperiorityResult(
        metric_type="binary", control=0.1, treatment=0.1 + diff, diff=diff,
        ci=Interval(low, high, 0.95), p_value=0.5, rel_lift=diff / 0.1,
        rel_ci=Interval(low / 0.1, high / 0.1, 0.95), method="test",
    )


def ni(low, high, margin=0.04):
    return NonInferiorityResult(
        diff=(low + high) / 2, margin=margin, ci=Interval(low, high, 0.90),
        p_value=0.5, non_inferior=low > -margin, inferior=high < -margin,
    )


SRM_OK = SRMResult(500000, 500000, 1.0, 1.0, 0.9, failed=False)
SRM_BAD = SRMResult(821588, 815482, 1.0, 0.9926, 1.8e-6, failed=True)


@pytest.mark.parametrize(
    "low,high,expected",
    [
        (0.001, 0.004, Superiority.BETTER),
        (-0.002, 0.004, Superiority.NOT_SIGNIFICANT),
        (-0.010, -0.002, Superiority.WORSE),
    ],
)
def test_superiority_status(low, high, expected):
    assert decision.superiority_status(sup(low, high)) is expected


def test_lower_is_better_flips_sign():
    assert decision.superiority_status(sup(-0.010, -0.006), higher_is_better=False) is Superiority.BETTER


@pytest.mark.parametrize(
    "low,high,expected",
    [
        (-0.02, 0.01, NonInferiority.YES),
        (-0.06, -0.05, NonInferiority.NO_BEYOND),
        (-0.048, -0.012, NonInferiority.NO_CROSSES),
    ],
)
def test_ni_status(low, high, expected):
    assert decision.ni_status(ni(low, high)) is expected


@pytest.mark.parametrize(
    "low,high,expected",
    [
        (0.006, 0.010, Threshold.ABOVE),
        (-0.002, 0.004, Threshold.BELOW),
        (0.001, 0.008, Threshold.UNCLEAR),
    ],
)
def test_threshold_status(low, high, expected):
    assert decision.threshold_status(sup(low, high), threshold=0.005) is expected


@pytest.mark.parametrize(
    "s,n,row",
    [
        (sup(0.001, 0.004), None, Row.SHIP),
        (sup(-0.002, 0.004), None, Row.INCONCLUSIVE),
        (sup(-0.010, -0.002), None, Row.DONT_SHIP),
        (sup(0.001, 0.004), ni(0.002, 0.003), Row.NI_1_SHIP),
        (sup(-0.002, 0.004), ni(-0.001, 0.003), Row.NI_2_SAFE),
        (sup(-0.050, 0.004), ni(-0.045, 0.002), Row.NI_3_DONT),
        (sup(-0.020, -0.002), ni(-0.018, -0.004), Row.NI_4_DISCUSS),
        (sup(-0.070, -0.050), ni(-0.068, -0.052), Row.NI_5_DONT_BEYOND),
        # 500/2500 vs 425/2500, margin 4 p.p.: Colab showed row 3 here.
        (sup(-0.0515, -0.0085), ni(-0.048, -0.012), Row.NI_6_DONT_CROSSES),
    ],
)
def test_rows(s, n, row):
    assert decision.decide(SRM_OK, s, n).row is row


def test_srm_blocks_everything():
    d = decision.decide(SRM_BAD, sup(0.006, 0.010), ni(-0.01, 0.02), threshold=0.005)
    assert d.row is Row.SRM_FAILURE
    assert d.superiority is None and d.non_inferiority is None and d.threshold is None
