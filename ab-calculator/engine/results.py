"""Result dataclasses shared by engine/stats.py, engine/checks.py and
engine/decision.py. Re-exported from engine.stats.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Interval:
    """A confidence interval for the treatment - control difference."""

    low: float
    high: float
    level: float  # coverage of a two-sided interval, e.g. 0.95


@dataclass(frozen=True)
class SuperiorityResult:
    """Result of a two-sided superiority test.

    `ci` (Wald) and `p_value` (pooled z) can disagree in rare cases right at
    the significance edge. The verdict follows the CI; the disagreement is
    shown as the "p_ci_disagree" borderline flag (SPEC 1.3).
    """

    metric_type: str          # "binary" or "continuous"
    control: float            # rate or mean in control
    treatment: float          # rate or mean in treatment
    diff: float               # treatment - control
    ci: Interval              # two-sided (1 - alpha) CI for diff
    p_value: float            # two-sided, H0: diff = 0
    rel_lift: float           # diff / control (NaN if control == 0)
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
