"""Experiment design: sample size, duration, detectable effect.

All rates and effects are fractions. `ratio` = n_treatment / n_control.
Superiority uses a two-sided alpha. Non-inferiority uses a one-sided alpha
(SPEC 1.1). References: Evan Miller (superiority), Sealed Envelope (NI),
within 1% of N (SPEC Step 0, BACKLOG B18).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import optimize as _opt
from scipy import stats as _sps

from engine.options import (
    DEFAULT_ALTERNATIVE,
    DEFAULT_NI_METHOD,
    Alternative,
    NIMethod,
    require_v1,
)


@dataclass(frozen=True)
class SampleSize:
    n_control: int
    n_treatment: int
    n_total: int


@dataclass(frozen=True)
class Duration:
    days_by_traffic: int    # n_total / daily_traffic, rounded up
    days_recommended: int   # rounded up to full weeks, at least 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _z(q: float) -> float:
    return float(_sps.norm.ppf(q))


def _check_common(alpha: float, power: float, ratio: float, one_sided_ni: bool = False) -> None:
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if one_sided_ni and alpha >= 0.5:
        raise ValueError(f"NI alpha must be < 0.5, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power must be in (0, 1), got {power}")
    if not ratio > 0:
        raise ValueError(f"ratio must be > 0, got {ratio}")


def _check_rate(name: str, p: float) -> None:
    if not 0 < p < 1:
        raise ValueError(f"{name} must be in (0, 1), got {p}")


def _sizes(n_c_exact: float, ratio: float) -> SampleSize:
    n_c = math.ceil(n_c_exact)
    n_t = math.ceil(n_c * ratio)
    return SampleSize(n_c, n_t, n_c + n_t)


def _binary_sup_exact(baseline: float, mde: float, alpha: float, power: float, ratio: float) -> float:
    """Unrounded n_control for binary superiority (see binary_superiority_n)."""
    p1, p2 = baseline, baseline + mde
    p_bar = (p1 + ratio * p2) / (1 + ratio)
    se_h0 = math.sqrt(p_bar * (1 - p_bar) * (1 + 1 / ratio))
    se_h1 = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)
    return ((_z(1 - alpha / 2) * se_h0 + _z(power) * se_h1) / mde) ** 2


# ---------------------------------------------------------------------------
# Sample size
# ---------------------------------------------------------------------------

def binary_superiority_n(
    baseline: float, mde: float, alpha: float, power: float, ratio: float = 1.0,
    alternative: Alternative = DEFAULT_ALTERNATIVE,
) -> SampleSize:
    """Sample size for a two-sided test of a conversion rate.

    Standard normal-approximation formula, no continuity correction:

        n_c = ( z(1-a/2) * sqrt(p_bar*(1-p_bar)*(1 + 1/r))
              + z(power) * sqrt(p1*(1-p1) + p2*(1-p2)/r) )^2 / mde^2

    p1 = baseline, p2 = baseline + mde,
    p_bar = (p1 + r*p2) / (1 + r)  (weighted by group size).
    n_t = ceil(n_c * r).

    With r = 1 this is the Colab formula. It is within 0.3% of Evan Miller
    (who uses p1 instead of p_bar under H0) and equal to statsmodels and
    Sealed Envelope. With r != 1, Colab uses the plain mean of p1 and p2
    for p_bar; the weighted mean here is the pooled rate under H0.

    alternative: Expert option (v2). v1 supports only "two-sided".
    """
    require_v1("alternative", alternative)
    _check_common(alpha, power, ratio)
    _check_rate("baseline", baseline)
    if mde == 0:
        raise ValueError("mde must not be 0")
    _check_rate("baseline + mde", baseline + mde)
    return _sizes(_binary_sup_exact(baseline, mde, alpha, power, ratio), ratio)


def binary_non_inferiority_n(
    baseline: float, margin: float, alpha: float, power: float, ratio: float = 1.0,
    method: NIMethod = DEFAULT_NI_METHOD,
) -> SampleSize:
    """Sample size for a one-sided non-inferiority test of a conversion rate.

    Blackwelder (1982), as in Sealed Envelope. Assumes no true difference:

        n_c = (z(1-a) + z(power))^2 * p*(1-p)*(1 + 1/r) / margin^2

    Gives the same numbers as Sealed Envelope with the same alpha
    (Sealed Envelope's NI alpha is one-sided; it rounds z, so it shows
    about 0.04% more).

    method: "standard" (above). "advanced" = separate H0/H1 variances, as in
    Colab; Expert option (v2, BACKLOG B17), not in v1.
    """
    require_v1("ni_method", method)
    _check_common(alpha, power, ratio, one_sided_ni=True)
    _check_rate("baseline", baseline)
    if not margin > 0:
        raise ValueError(f"margin must be > 0, got {margin}")
    var = baseline * (1 - baseline) * (1 + 1 / ratio)
    n_c = (_z(1 - alpha) + _z(power)) ** 2 * var / margin ** 2
    return _sizes(n_c, ratio)


def continuous_superiority_n(
    sd: float, mde: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a two-sided test of a mean.

        n_c = (z(1-a/2) + z(power))^2 * sd^2 * (1 + 1/r) / mde^2

    sd is the per-user standard deviation, from historical data.
    Assumes equal SD in both groups.
    """
    _check_common(alpha, power, ratio)
    if not sd > 0:
        raise ValueError(f"sd must be > 0, got {sd}")
    if mde == 0:
        raise ValueError("mde must not be 0")
    n_c = (_z(1 - alpha / 2) + _z(power)) ** 2 * sd ** 2 * (1 + 1 / ratio) / mde ** 2
    return _sizes(n_c, ratio)


def continuous_non_inferiority_n(
    sd: float, margin: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a one-sided non-inferiority test of a mean.

        n_c = (z(1-a) + z(power))^2 * sd^2 * (1 + 1/r) / margin^2
    """
    _check_common(alpha, power, ratio, one_sided_ni=True)
    if not sd > 0:
        raise ValueError(f"sd must be > 0, got {sd}")
    if not margin > 0:
        raise ValueError(f"margin must be > 0, got {margin}")
    n_c = (_z(1 - alpha) + _z(power)) ** 2 * sd ** 2 * (1 + 1 / ratio) / margin ** 2
    return _sizes(n_c, ratio)


# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------

def duration(n_total: int, daily_traffic: int) -> Duration:
    """Days needed to collect n_total users.

    days_recommended is rounded up to full weeks (minimum 7),
    so the test covers weekly patterns. The UI shows both
    ("23 days -> run 4 full weeks (28 days)", BACKLOG B23).
    daily_traffic = users entering the experiment per day, both groups.
    """
    if not daily_traffic > 0:
        raise ValueError(f"daily_traffic must be > 0, got {daily_traffic}")
    if n_total < 0:
        raise ValueError(f"n_total must be >= 0, got {n_total}")
    days = math.ceil(n_total / daily_traffic)
    weeks = max(1, math.ceil(days / 7))
    return Duration(days_by_traffic=days, days_recommended=weeks * 7)


# ---------------------------------------------------------------------------
# Inverse task: what can we detect?
# ---------------------------------------------------------------------------

def detectable_effect(
    n_control: int, ratio: float, alpha: float, power: float,
    test: str, metric_type: str,
    baseline: float | None = None, sd: float | None = None,
) -> float:
    """Smallest effect (MDE) or margin we can detect with this sample.

    test: "superiority" or "non_inferiority".
    metric_type: "binary" (needs baseline) or "continuous" (needs sd).

    Inverse of the *_n functions above. Binary superiority has no closed
    form (variance depends on the effect), so it is solved numerically.
    Returns a positive number in absolute units (an increase over baseline
    for binary superiority).

    Use: compare the result with the threshold from the brief.
    If detectable > threshold, the test cannot see worthwhile effects:
    the answer is "does not fit", not "raise the threshold".
    """
    if not n_control > 0:
        raise ValueError(f"n_control must be > 0, got {n_control}")
    if test not in ("superiority", "non_inferiority"):
        raise ValueError(f"test must be 'superiority' or 'non_inferiority', got {test!r}")
    ni = test == "non_inferiority"
    _check_common(alpha, power, ratio, one_sided_ni=ni)
    z_a = _z(1 - alpha) if ni else _z(1 - alpha / 2)
    z_b = _z(power)

    if metric_type == "continuous":
        if sd is None or not sd > 0:
            raise ValueError("continuous metrics need sd > 0")
        return (z_a + z_b) * sd * math.sqrt((1 + 1 / ratio) / n_control)

    if metric_type != "binary":
        raise ValueError(f"metric_type must be 'binary' or 'continuous', got {metric_type!r}")
    if baseline is None:
        raise ValueError("binary metrics need a baseline")
    _check_rate("baseline", baseline)

    if ni:
        return (z_a + z_b) * math.sqrt(baseline * (1 - baseline) * (1 + 1 / ratio) / n_control)

    hi = 1 - baseline - 1e-12
    def gap(mde: float) -> float:
        return _binary_sup_exact(baseline, mde, alpha, power, ratio) - n_control
    if gap(hi) > 0:
        raise ValueError("sample too small: even the largest possible effect is not detectable")
    return float(_opt.brentq(gap, 1e-12, hi, xtol=1e-12))


def fits(detectable: float, threshold: float) -> bool:
    """True if the test can see effects of the size that matters.

    detectable <= threshold, both positive and in the same units.
    """
    if not detectable > 0 or not threshold > 0:
        raise ValueError(f"both values must be > 0, got {detectable}, {threshold}")
    return detectable <= threshold
