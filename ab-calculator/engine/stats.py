"""Statistical tests for one metric and two groups (control vs treatment).

All rates, means and effects are in metric units as fractions:
a conversion rate of 11.3% is 0.113. Convert % and p.p. in the UI.

Methods (see SPEC.md, step 1):
- Binary metrics: pooled z-test for the p-value (equals Evan Miller's
  chi-squared test), Wald CI (unpooled SE) for the difference.
- Low counts: also return the Newcombe CI as a safer reference.
- Continuous metrics: Welch t-test on per-user summary stats.
- Relative lift: CI by the delta method, not by dividing the absolute CI.

Data-quality checks (SRM, low counts, borderline) are in engine/checks.py
and re-exported here.
"""

from __future__ import annotations

import math

from scipy import stats as _sps

from engine.options import (
    DEFAULT_ALTERNATIVE,
    DEFAULT_CI_METHOD,
    Alternative,
    CIMethod,
    require_v1,
)
from engine.results import Interval, NonInferiorityResult, SRMResult, SuperiorityResult
from engine.checks import (  # noqa: F401  (re-exported)
    LOW_COUNTS_THRESHOLD,
    SRM_THRESHOLD,
    borderline_flags,
    is_low_counts,
    srm_check,
)

_NAN_INTERVAL_FIELDS = (math.nan, math.nan)


# ---------------------------------------------------------------------------
# Input checks
# ---------------------------------------------------------------------------

def _check_alpha(alpha: float, one_sided_ni: bool = False) -> None:
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if one_sided_ni and alpha >= 0.5:
        raise ValueError(f"NI uses the (1 - 2*alpha) CI, so alpha must be < 0.5, got {alpha}")


def _check_binary(conv_c: int, n_c: int, conv_t: int, n_t: int) -> None:
    for name, conv, n in (("control", conv_c, n_c), ("treatment", conv_t, n_t)):
        if n <= 0:
            raise ValueError(f"n {name} must be > 0, got {n}")
        if conv < 0:
            raise ValueError(f"conversions {name} must be >= 0, got {conv}")
        if conv > n:
            raise ValueError(f"conversions {name} ({conv}) > n {name} ({n})")


def _check_continuous(sd_c: float, n_c: int, sd_t: float, n_t: int) -> None:
    for name, sd, n in (("control", sd_c, n_c), ("treatment", sd_t, n_t)):
        if n < 2:
            raise ValueError(f"n {name} must be >= 2, got {n}")
        if sd < 0:
            raise ValueError(f"sd {name} must be >= 0, got {sd}")


def _check_margin(margin: float) -> None:
    if not margin > 0:
        raise ValueError(f"margin must be > 0 (absolute units), got {margin}")


def _rel(mean_c: float, var_c: float, mean_t: float, var_t: float, level: float):
    """Relative lift and its CI; NaN when the control mean is 0."""
    if mean_c == 0:
        return math.nan, Interval(*_NAN_INTERVAL_FIELDS, level)
    return (mean_t - mean_c) / mean_c, relative_lift_ci(mean_c, var_c, mean_t, var_t, level)


# ---------------------------------------------------------------------------
# Binary metrics
# ---------------------------------------------------------------------------

def binary_superiority(
    conv_c: int, n_c: int, conv_t: int, n_t: int, alpha: float,
    ci_method: CIMethod = DEFAULT_CI_METHOD,
    alternative: Alternative = DEFAULT_ALTERNATIVE,
) -> SuperiorityResult:
    """Two-sided superiority test for a conversion rate.

    p-value: pooled z-test (one rate for both groups under H0).
    Equals Evan Miller's chi-squared test (SPEC 1.2).
    CI: Wald, unpooled SE, two-sided (1 - alpha).

    If any group has fewer than LOW_COUNTS_THRESHOLD conversions,
    set low_counts=True and also return newcombe_ci.

    ci_method, alternative: Expert options (v2). v1 supports only the defaults.

    Raises ValueError on bad input: n <= 0, conv < 0, conv > n,
    alpha not in (0, 1).
    """
    require_v1("ci_method", ci_method)
    require_v1("alternative", alternative)
    _check_binary(conv_c, n_c, conv_t, n_t)
    _check_alpha(alpha)

    p_c, p_t = conv_c / n_c, conv_t / n_t
    diff = p_t - p_c

    p_pool = (conv_c + conv_t) / (n_c + n_t)
    se0 = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    if se0 == 0:
        p_value = 1.0
    else:
        p_value = float(2 * _sps.norm.sf(abs(diff) / se0))

    var_c, var_t = p_c * (1 - p_c) / n_c, p_t * (1 - p_t) / n_t
    z = float(_sps.norm.ppf(1 - alpha / 2))
    half = z * math.sqrt(var_c + var_t)
    level = 1 - alpha
    rel_lift, rel_ci = _rel(p_c, var_c, p_t, var_t, level)

    low = is_low_counts(conv_c, conv_t)
    return SuperiorityResult(
        metric_type="binary",
        control=p_c,
        treatment=p_t,
        diff=diff,
        ci=Interval(diff - half, diff + half, level),
        p_value=p_value,
        rel_lift=rel_lift,
        rel_ci=rel_ci,
        method="Pooled z-test, Wald CI",
        low_counts=low,
        newcombe_ci=newcombe_ci(conv_c, n_c, conv_t, n_t, level) if low else None,
    )


def binary_non_inferiority(
    conv_c: int, n_c: int, conv_t: int, n_t: int, margin: float, alpha: float,
    ci_method: CIMethod = DEFAULT_CI_METHOD,
) -> NonInferiorityResult:
    """One-sided non-inferiority test for a conversion rate.

    z = (diff + margin) / SE, SE unpooled (Wald).
    CI: Wald, two-sided (1 - 2*alpha). Requires alpha < 0.5.

    `margin` is positive and in absolute units (0.003 = 0.3 p.p.).
    Convert a relative margin with to_absolute() first.

    ci_method: Expert option (v2). v1 supports only "wald".
    """
    require_v1("ci_method", ci_method)
    _check_binary(conv_c, n_c, conv_t, n_t)
    _check_alpha(alpha, one_sided_ni=True)
    _check_margin(margin)

    p_c, p_t = conv_c / n_c, conv_t / n_t
    diff = p_t - p_c
    se = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    return _ni_result(diff, se, margin, alpha, _sps.norm)


def newcombe_ci(
    conv_c: int, n_c: int, conv_t: int, n_t: int, level: float
) -> Interval:
    """Newcombe (1998) hybrid score CI (method 10) for treatment - control.

    Built from two Wilson intervals. Better than Wald when counts are low
    or rates are close to 0 or 1. Used only as a reference for low counts.
    """
    _check_binary(conv_c, n_c, conv_t, n_t)
    z = float(_sps.norm.ppf(1 - (1 - level) / 2))
    l_c, u_c = _wilson(conv_c, n_c, z)
    l_t, u_t = _wilson(conv_t, n_t, z)
    p_c, p_t = conv_c / n_c, conv_t / n_t
    diff = p_t - p_c
    low = diff - math.sqrt((p_t - l_t) ** 2 + (u_c - p_c) ** 2)
    high = diff + math.sqrt((u_t - p_t) ** 2 + (p_c - l_c) ** 2)
    return Interval(low, high, level)


def _wilson(conv: int, n: int, z: float) -> tuple[float, float]:
    """Wilson score interval for one proportion."""
    p = conv / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))
    return center - half, center + half


# ---------------------------------------------------------------------------
# Continuous metrics
# ---------------------------------------------------------------------------

def _welch(sd_c: float, n_c: int, sd_t: float, n_t: int):
    """Variances of the group means, SE of the difference, Welch df."""
    var_c, var_t = sd_c ** 2 / n_c, sd_t ** 2 / n_t
    se = math.sqrt(var_c + var_t)
    if se == 0:
        return var_c, var_t, 0.0, math.inf
    df = (var_c + var_t) ** 2 / (var_c ** 2 / (n_c - 1) + var_t ** 2 / (n_t - 1))
    return var_c, var_t, se, df


def continuous_superiority(
    mean_c: float, sd_c: float, n_c: int,
    mean_t: float, sd_t: float, n_t: int,
    alpha: float,
) -> SuperiorityResult:
    """Two-sided Welch t-test for a mean, from summary stats.

    Inputs must be per-user values: one row = one randomized user.
    Per-event data gives a too small SE and too many false wins.

    Welch does not assume equal variances. Always Welch, never Student.

    Raises ValueError on bad input: n < 2, sd < 0, alpha not in (0, 1).
    """
    _check_continuous(sd_c, n_c, sd_t, n_t)
    _check_alpha(alpha)

    diff = mean_t - mean_c
    var_c, var_t, se, df = _welch(sd_c, n_c, sd_t, n_t)
    level = 1 - alpha
    if se == 0:
        p_value = 1.0 if diff == 0 else 0.0
        ci = Interval(diff, diff, level)
    else:
        dist = _sps.t(df)
        p_value = float(2 * dist.sf(abs(diff) / se))
        half = float(dist.ppf(1 - alpha / 2)) * se
        ci = Interval(diff - half, diff + half, level)
    rel_lift, rel_ci = _rel(mean_c, var_c, mean_t, var_t, level)

    return SuperiorityResult(
        metric_type="continuous",
        control=mean_c,
        treatment=mean_t,
        diff=diff,
        ci=ci,
        p_value=p_value,
        rel_lift=rel_lift,
        rel_ci=rel_ci,
        method="Welch t-test",
    )


def continuous_non_inferiority(
    mean_c: float, sd_c: float, n_c: int,
    mean_t: float, sd_t: float, n_t: int,
    margin: float, alpha: float,
) -> NonInferiorityResult:
    """One-sided Welch non-inferiority test for a mean.

    t = (diff + margin) / SE, Welch-Satterthwaite degrees of freedom.
    CI: two-sided (1 - 2*alpha).
    """
    _check_continuous(sd_c, n_c, sd_t, n_t)
    _check_alpha(alpha, one_sided_ni=True)
    _check_margin(margin)

    diff = mean_t - mean_c
    _, _, se, df = _welch(sd_c, n_c, sd_t, n_t)
    return _ni_result(diff, se, margin, alpha, _sps.t(df))


def _ni_result(diff: float, se: float, margin: float, alpha: float, dist) -> NonInferiorityResult:
    """Shared NI logic: one-sided p-value and the (1 - 2*alpha) CI."""
    level = 1 - 2 * alpha
    if se == 0:
        p_value = 0.0 if diff + margin > 0 else 1.0
        ci = Interval(diff, diff, level)
    else:
        p_value = float(dist.sf((diff + margin) / se))
        half = float(dist.ppf(1 - alpha)) * se
        ci = Interval(diff - half, diff + half, level)
    return NonInferiorityResult(
        diff=diff,
        margin=margin,
        ci=ci,
        p_value=p_value,
        non_inferior=bool(ci.low > -margin),
        inferior=bool(ci.high < -margin),
    )


# ---------------------------------------------------------------------------
# Relative lift
# ---------------------------------------------------------------------------

def relative_lift_ci(
    mean_c: float, var_mean_c: float,
    mean_t: float, var_mean_t: float,
    level: float,
) -> Interval:
    """CI for (mean_t - mean_c) / mean_c by the delta method.

    var_mean_* is the variance of the group mean (SE squared).
    Do not divide the absolute CI by mean_c: mean_c is also random,
    and that interval covers less than promised.

        Var(R) ~ var_t / mc^2 + mt^2 * var_c / mc^4,   R = mt / mc - 1

    Raises ValueError if mean_c == 0.
    """
    if mean_c == 0:
        raise ValueError("relative lift is undefined when the control mean is 0")
    lift = mean_t / mean_c - 1
    se = math.sqrt(var_mean_t / mean_c ** 2 + mean_t ** 2 * var_mean_c / mean_c ** 4)
    half = float(_sps.norm.ppf(1 - (1 - level) / 2)) * se
    return Interval(lift - half, lift + half, level)


def to_absolute(value: float, unit: str, baseline: float) -> float:
    """Convert a threshold or margin to absolute metric units.

    unit = "abs": value is already absolute (0.003 = 0.3 p.p.).
    unit = "rel": value is relative to baseline (0.02 = 2%),
                  result = value * |baseline|.

    Baseline: the planned control value in Design,
    the observed control value in Analysis.
    """
    if unit == "abs":
        return value
    if unit == "rel":
        return value * abs(baseline)
    raise ValueError(f"unit must be 'abs' or 'rel', got {unit!r}")


__all__ = [
    "Interval", "SuperiorityResult", "NonInferiorityResult", "SRMResult",
    "LOW_COUNTS_THRESHOLD", "SRM_THRESHOLD",
    "binary_superiority", "binary_non_inferiority", "newcombe_ci",
    "continuous_superiority", "continuous_non_inferiority",
    "relative_lift_ci", "to_absolute",
    "srm_check", "is_low_counts", "borderline_flags",
]
