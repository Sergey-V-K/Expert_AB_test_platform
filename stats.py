"""Statistical tests for one metric and two groups (control vs treatment).

All rates, means and effects are in metric units as fractions:
a conversion rate of 11.3% is 0.113. Convert % and p.p. in the UI.

Methods (see SPEC.md, step 1):
- Binary metrics: pooled z-test for the p-value, Wald CI (unpooled SE)
  for the difference. This is the standard pair used by online calculators.
- Low counts: also return the Newcombe CI as a safer reference.
- Continuous metrics: Welch t-test on per-user summary stats.
- Relative lift: CI by the delta method, not by dividing the absolute CI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Conversions per group below this value -> low-counts warning.
# Starting value. Calibrate with an A/A simulation (BACKLOG B2).
LOW_COUNTS_THRESHOLD = 25

# SRM p-value threshold. Fixed. Does not depend on the test alpha (SPEC 1.4).
SRM_THRESHOLD = 0.001


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Interval:
    """A confidence interval for the treatment - control difference."""

    low: float
    high: float
    level: float  # coverage of a two-sided interval, e.g. 0.95


@dataclass(frozen=True)
class SuperiorityResult:
    """Result of a two-sided superiority test.

    `ci` and `p_value` come from the same test family, so they agree
    except in rare cases right at the significance edge (BACKLOG B3).
    """

    metric_type: str          # "binary" or "continuous"
    control: float            # rate or mean in control
    treatment: float          # rate or mean in treatment
    diff: float               # treatment - control
    ci: Interval              # two-sided (1 - alpha) CI for diff
    p_value: float            # two-sided, H0: diff = 0
    rel_lift: float           # diff / control
    rel_ci: Interval          # CI for rel_lift, delta method
    method: str               # short name, shown in the UI
    low_counts: bool = False  # True if any group has too few conversions
    newcombe_ci: Optional[Interval] = None  # binary + low counts only


@dataclass(frozen=True)
class NonInferiorityResult:
    """Result of a one-sided non-inferiority test.

    H0: diff <= -margin. H1: diff > -margin.
    One-sided alpha, as in product platforms and Sealed Envelope (SPEC 1.1).
    The test passes if the lower bound of the two-sided (1 - 2*alpha) CI
    is above -margin. For alpha = 0.05 this is a 90% CI.
    """

    diff: float           # treatment - control
    margin: float         # positive number, metric units
    ci: Interval          # two-sided (1 - 2*alpha) CI
    p_value: float        # one-sided, H0: diff <= -margin
    non_inferior: bool    # ci.low > -margin
    inferior: bool        # ci.high < -margin


@dataclass(frozen=True)
class SRMResult:
    """Sample ratio mismatch check (chi-squared goodness of fit)."""

    n_control: int
    n_treatment: int
    expected_ratio: float   # treatment / control, as planned
    observed_ratio: float   # treatment / control, as observed
    p_value: float
    failed: bool            # p_value < threshold


# ---------------------------------------------------------------------------
# Binary metrics
# ---------------------------------------------------------------------------

def binary_superiority(
    conv_c: int, n_c: int, conv_t: int, n_t: int, alpha: float
) -> SuperiorityResult:
    """Two-sided superiority test for a conversion rate.

    p-value: pooled z-test (one rate for both groups under H0).
    CI: Wald, unpooled SE, two-sided (1 - alpha).
    Same as standard online calculators.

    If any group has fewer than LOW_COUNTS_THRESHOLD conversions,
    set low_counts=True and also return newcombe_ci.

    Raises ValueError on bad input: n <= 0, conv < 0, conv > n,
    alpha not in (0, 1).
    """
    raise NotImplementedError


def binary_non_inferiority(
    conv_c: int, n_c: int, conv_t: int, n_t: int, margin: float, alpha: float
) -> NonInferiorityResult:
    """One-sided non-inferiority test for a conversion rate.

    z = (diff + margin) / SE, SE unpooled (Wald).
    CI: Wald, two-sided (1 - 2*alpha).

    `margin` is positive and in absolute units (0.003 = 0.3 p.p.).
    Convert a relative margin with to_absolute() first.
    """
    raise NotImplementedError


def newcombe_ci(
    conv_c: int, n_c: int, conv_t: int, n_t: int, level: float
) -> Interval:
    """Newcombe (1998) hybrid score CI (method 10) for treatment - control.

    Built from two Wilson intervals. Better than Wald when counts are low
    or rates are close to 0 or 1. Used only as a reference for low counts.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Continuous metrics
# ---------------------------------------------------------------------------

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
    raise NotImplementedError


def continuous_non_inferiority(
    mean_c: float, sd_c: float, n_c: int,
    mean_t: float, sd_t: float, n_t: int,
    margin: float, alpha: float,
) -> NonInferiorityResult:
    """One-sided Welch non-inferiority test for a mean.

    t = (diff + margin) / SE, Welch-Satterthwaite degrees of freedom.
    CI: two-sided (1 - 2*alpha).
    """
    raise NotImplementedError


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

    Raises ValueError if mean_c == 0.
    """
    raise NotImplementedError


def to_absolute(value: float, unit: str, baseline: float) -> float:
    """Convert a threshold or margin to absolute metric units.

    unit = "abs": value is already absolute (0.003 = 0.3 p.p.).
    unit = "rel": value is relative to baseline (0.02 = 2%),
                  result = value * baseline.

    Baseline: the planned control value in Design,
    the observed control value in Analysis.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Data quality checks
# ---------------------------------------------------------------------------

def srm_check(
    n_c: int, n_t: int, expected_ratio: float = 1.0,
    threshold: float = SRM_THRESHOLD,
) -> SRMResult:
    """Chi-squared test: does the observed split match the planned one?

    Always runs. SRM is about significance, not about the size
    of the imbalance: at large N even 0.5% can be a real bug.

    expected_ratio = treatment / control as planned. 1.0 = 50/50,
    0.25 = 80/20 (control/treatment).

    Use counts of all assigned users, not only triggered or filtered ones.
    """
    raise NotImplementedError


def is_low_counts(
    conv_c: int, conv_t: int, threshold: int = LOW_COUNTS_THRESHOLD
) -> bool:
    """True if any group has fewer conversions than `threshold`.

    With so few conversions the normal approximation is rough
    and the CI is very wide.
    """
    raise NotImplementedError


def borderline_flags(
    p_value: float, alpha: float, ci: Interval,
    margin: Optional[float] = None, threshold: Optional[float] = None,
) -> list[str]:
    """Flags for results where a small change in data could flip the decision.

    Returns short codes, the UI turns them into text:
    - "p_near_alpha":   0.7 * alpha <= p_value <= 1.3 * alpha
    - "ci_near_zero":   a CI edge is within 10% of CI width from 0
    - "ci_near_margin": ci.low is within 10% of CI width from -margin
    - "ci_near_threshold": a CI edge is within 10% of CI width from threshold
    - "p_ci_disagree":  p-value and CI give different answers about 0
                        (pooled p vs unpooled CI, BACKLOG B3)
    """
    raise NotImplementedError
