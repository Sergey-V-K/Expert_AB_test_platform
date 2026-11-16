"""Data-quality checks: SRM, low counts, borderline results.

Re-exported from engine.stats, so callers can use stats.srm_check() etc.
"""

from __future__ import annotations

from typing import Optional

from scipy import stats as _sps

from engine.results import Interval, SRMResult

# Conversions per group below this value -> low-counts warning.
# Starting value. Calibrate with an A/A simulation (BACKLOG B2).
LOW_COUNTS_THRESHOLD = 25

# SRM p-value threshold. Fixed. Does not depend on the test alpha (SPEC 1.4).
SRM_THRESHOLD = 0.001

# Borderline zones (SPEC 1.7, same as Colab).
P_NEAR_ALPHA = (0.7, 1.3)   # p in [0.7 * alpha, 1.3 * alpha]
EDGE_SHARE = 0.10           # CI edge within 10% of the CI width


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
    if n_c <= 0 or n_t <= 0:
        raise ValueError(f"group sizes must be > 0, got {n_c}, {n_t}")
    if not expected_ratio > 0:
        raise ValueError(f"expected_ratio must be > 0, got {expected_ratio}")
    total = n_c + n_t
    exp_c = total / (1 + expected_ratio)
    _, p_value = _sps.chisquare([n_c, n_t], f_exp=[exp_c, total - exp_c])
    p_value = float(p_value)
    return SRMResult(
        n_control=n_c,
        n_treatment=n_t,
        expected_ratio=expected_ratio,
        observed_ratio=n_t / n_c,
        p_value=p_value,
        failed=bool(p_value < threshold),
    )


def is_low_counts(
    conv_c: int, conv_t: int, threshold: int = LOW_COUNTS_THRESHOLD
) -> bool:
    """True if any group has fewer conversions than `threshold`.

    With so few conversions the normal approximation is rough
    and the CI is very wide.
    """
    return min(conv_c, conv_t) < threshold


def borderline_flags(
    p_value: float, alpha: float, ci: Interval,
    margin: Optional[float] = None, threshold: Optional[float] = None,
    ni_ci: Optional[Interval] = None,
    higher_is_better: bool = True,
) -> list[str]:
    """Flags for results where a small change in data could flip the decision.

    Returns short codes, the UI turns them into text (SPEC 1.3, 1.7):
    - "p_near_alpha":   0.7 * alpha <= p_value <= 1.3 * alpha
    - "ci_near_zero":   a CI edge is within 10% of CI width from 0
    - "ci_near_margin": ni_ci.low is within 10% of the superiority CI width
                        from -margin. Uses the NI (1 - 2*alpha) CI, since the
                        NI verdict does. Falls back to ci.low without ni_ci.
    - "ci_near_threshold": a CI edge is within 10% of CI width from threshold
    - "p_ci_disagree":  pooled p-value and Wald CI give different answers
                        about 0. The verdict follows the CI (BACKLOG B3, done).

    margin and threshold are positive. higher_is_better=False flips the CIs
    first, as decision.py does.
    """
    if not higher_is_better:
        ci = Interval(-ci.high, -ci.low, ci.level)
        if ni_ci is not None:
            ni_ci = Interval(-ni_ci.high, -ni_ci.low, ni_ci.level)
    flags: list[str] = []
    edge = (ci.high - ci.low) * EDGE_SHARE

    lo, hi = P_NEAR_ALPHA
    if lo * alpha <= p_value <= hi * alpha:
        flags.append("p_near_alpha")

    if min(abs(ci.low), abs(ci.high)) < edge:
        flags.append("ci_near_zero")

    if margin is not None and margin > 0:
        ni_low = ni_ci.low if ni_ci is not None else ci.low
        if abs(ni_low + margin) < edge:
            flags.append("ci_near_margin")

    if threshold is not None:
        if min(abs(ci.low - threshold), abs(ci.high - threshold)) < edge:
            flags.append("ci_near_threshold")

    ci_significant = ci.low > 0 or ci.high < 0
    if (p_value < alpha) != ci_significant:
        flags.append("p_ci_disagree")

    return flags
