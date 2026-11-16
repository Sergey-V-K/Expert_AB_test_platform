"""Experiment design: sample size, duration, detectable effect.

All rates and effects are fractions. `ratio` = n_treatment / n_control.
Superiority uses a two-sided alpha. Non-inferiority uses a one-sided alpha
(SPEC 1.1, to confirm: BACKLOG B1).
"""

from __future__ import annotations

from dataclasses import dataclass


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
# Sample size
# ---------------------------------------------------------------------------

def binary_superiority_n(
    baseline: float, mde: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a two-sided test of a conversion rate.

    Standard normal-approximation formula, no continuity correction:

        n_c = ( z(1-a/2) * sqrt(p_bar*(1-p_bar)*(1 + 1/r))
              + z(power) * sqrt(p1*(1-p1) + p2*(1-p2)/r) )^2 / mde^2

    p1 = baseline, p2 = baseline + mde,
    p_bar = (p1 + r*p2) / (1 + r)  (weighted by group size).
    n_t = ceil(n_c * r).

    With r = 1 this matches common online calculators.
    """
    raise NotImplementedError


def binary_non_inferiority_n(
    baseline: float, margin: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a one-sided non-inferiority test of a conversion rate.

    Blackwelder (1982), as in Sealed Envelope. Assumes no true difference:

        n_c = (z(1-a) + z(power))^2 * p*(1-p)*(1 + 1/r) / margin^2

    Gives the same numbers as Sealed Envelope with the same alpha.
    """
    raise NotImplementedError


def continuous_superiority_n(
    sd: float, mde: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a two-sided test of a mean.

        n_c = (z(1-a/2) + z(power))^2 * sd^2 * (1 + 1/r) / mde^2

    sd is the per-user standard deviation, from historical data.
    Assumes equal SD in both groups.
    """
    raise NotImplementedError


def continuous_non_inferiority_n(
    sd: float, margin: float, alpha: float, power: float, ratio: float = 1.0
) -> SampleSize:
    """Sample size for a one-sided non-inferiority test of a mean.

        n_c = (z(1-a) + z(power))^2 * sd^2 * (1 + 1/r) / margin^2
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------

def duration(n_total: int, daily_traffic: int) -> Duration:
    """Days needed to collect n_total users.

    days_recommended is rounded up to full weeks (minimum 7),
    so the test covers weekly patterns.
    daily_traffic = users entering the experiment per day, both groups.
    """
    raise NotImplementedError


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

    Use: compare the result with the threshold from the brief.
    If detectable > threshold, the test cannot see worthwhile effects:
    the answer is "does not fit", not "raise the threshold".
    """
    raise NotImplementedError


def fits(detectable: float, threshold: float) -> bool:
    """True if the test can see effects of the size that matters.

    detectable <= threshold, both positive and in the same units.
    """
    raise NotImplementedError
