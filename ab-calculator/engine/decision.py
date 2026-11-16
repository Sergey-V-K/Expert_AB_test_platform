"""Decision: from test results to a verdict.

Outcomes follow the Colab calculator, with two labels renamed to industry
wording and row 6 added (SPEC Step 4). Superiority and NI are judged
separately, and the matrix row is chosen from the pair.

The verdict follows the CI, not the p-value (SPEC 1.3). If they disagree,
the "p_ci_disagree" borderline flag is shown.

A failed SRM check blocks every verdict.

The engine returns rows, not text. Display labels (set in the UI):
    SHIP / NI_1_SHIP            "Ship"
    INCONCLUSIVE                "Inconclusive: keep control"
    DONT_SHIP / NI_3, NI_5, NI_6 "Don't ship"
    NI_2_SAFE                   "Safe to ship"
    NI_4_DISCUSS                "Discuss: worse, but within margin"
    SRM_FAILURE                 "SRM failure"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from engine.results import Interval, NonInferiorityResult, SRMResult, SuperiorityResult


class Superiority(str, Enum):
    BETTER = "better"                    # ci.low > 0
    NOT_SIGNIFICANT = "not_significant"  # CI contains 0
    WORSE = "worse"                      # ci.high < 0


class NonInferiority(str, Enum):
    YES = "yes"                          # ci.low > -margin
    NO_CROSSES = "no_crosses"            # CI crosses -margin
    NO_BEYOND = "no_beyond"              # ci.high < -margin


class Threshold(str, Enum):
    """Extra line under the verdict. Only when the brief has a threshold."""

    ABOVE = "above"      # ci.low > threshold: effect pays off
    BELOW = "below"      # ci.high < threshold: effect too small to pay off
    UNCLEAR = "unclear"  # CI contains the threshold


class Row(str, Enum):
    """Decision matrix row (SPEC Step 4)."""

    SRM_FAILURE = "srm_failure"
    # Superiority only
    SHIP = "ship"                    # better
    INCONCLUSIVE = "inconclusive"    # not significant -> keep control (was "No action")
    DONT_SHIP = "dont_ship"          # worse
    # Superiority + NI
    NI_1_SHIP = "1"                  # better,          NI yes
    NI_2_SAFE = "2"                  # not significant, NI yes
    NI_3_DONT = "3"                  # not significant, NI no
    NI_4_DISCUSS = "4"               # worse,           NI yes  -> discuss (was "Safe to ship*")
    NI_5_DONT_BEYOND = "5"           # worse,           NI no, beyond margin
    NI_6_DONT_CROSSES = "6"          # worse,           NI no, crosses margin (new)


@dataclass(frozen=True)
class Decision:
    """Everything the UI needs to show the result."""

    row: Row
    superiority: Optional[Superiority]     # None if SRM failed
    non_inferiority: Optional[NonInferiority]
    threshold: Optional[Threshold]
    srm: SRMResult
    flags: list[str] = field(default_factory=list)  # borderline, low_counts


def superiority_status(
    result: SuperiorityResult, higher_is_better: bool = True
) -> Superiority:
    """From the two-sided (1 - alpha) CI:

    ci.low  > 0 -> BETTER
    ci.high < 0 -> WORSE
    otherwise   -> NOT_SIGNIFICANT

    higher_is_better=False (time to event, error rate): flip signs first.
    """
    low, high = _oriented(result.ci, higher_is_better)
    if low > 0:
        return Superiority.BETTER
    if high < 0:
        return Superiority.WORSE
    return Superiority.NOT_SIGNIFICANT


def ni_status(
    result: NonInferiorityResult, higher_is_better: bool = True
) -> NonInferiority:
    """From the (1 - 2*alpha) CI (90% for alpha = 0.05, SPEC 1.1):

    ci.low  > -margin -> YES
    ci.high < -margin -> NO_BEYOND
    otherwise         -> NO_CROSSES

    higher_is_better=False: flip signs first.
    """
    low, high = _oriented(result.ci, higher_is_better)
    if low > -result.margin:
        return NonInferiority.YES
    if high < -result.margin:
        return NonInferiority.NO_BEYOND
    return NonInferiority.NO_CROSSES


def threshold_status(
    result: SuperiorityResult, threshold: float, higher_is_better: bool = True
) -> Threshold:
    """Where the CI lies vs the threshold from the brief (absolute units, > 0).

    ci.low  > threshold -> ABOVE
    ci.high < threshold -> BELOW
    otherwise           -> UNCLEAR

    Does not change the matrix row. Shown as one line under the verdict.
    """
    if not threshold > 0:
        raise ValueError(f"threshold must be > 0, got {threshold}")
    low, high = _oriented(result.ci, higher_is_better)
    if low > threshold:
        return Threshold.ABOVE
    if high < threshold:
        return Threshold.BELOW
    return Threshold.UNCLEAR


def decide(
    srm: SRMResult,
    sup: SuperiorityResult,
    ni: Optional[NonInferiorityResult] = None,
    threshold: Optional[float] = None,
    higher_is_better: bool = True,
    flags: Optional[list[str]] = None,
) -> Decision:
    """Combine all checks into one Decision.

    SRM failed -> row SRM_FAILURE, no statuses. Numbers stay in `sup` and
    `ni` for diagnosis, but the UI must not show them as a decision.

    No NI: row from superiority (SHIP / INCONCLUSIVE / DONT_SHIP).
    With NI: row from the pair (superiority, NI):

        better,          any            -> 1
        not significant, YES            -> 2
        not significant, NO_*           -> 3
        worse,           YES            -> 4
        worse,           NO_BEYOND      -> 5
        worse,           NO_CROSSES     -> 6

    "better" always gives NI YES with the same data, so row 1 needs no NI check.
    """
    flags = list(flags or [])
    if srm.failed:
        return Decision(Row.SRM_FAILURE, None, None, None, srm, flags)

    s = superiority_status(sup, higher_is_better)
    t = threshold_status(sup, threshold, higher_is_better) if threshold is not None else None

    if ni is None:
        row = {
            Superiority.BETTER: Row.SHIP,
            Superiority.NOT_SIGNIFICANT: Row.INCONCLUSIVE,
            Superiority.WORSE: Row.DONT_SHIP,
        }[s]
        return Decision(row, s, None, t, srm, flags)

    n = ni_status(ni, higher_is_better)
    if s is Superiority.BETTER:
        row = Row.NI_1_SHIP
    elif s is Superiority.NOT_SIGNIFICANT:
        row = Row.NI_2_SAFE if n is NonInferiority.YES else Row.NI_3_DONT
    else:
        row = {
            NonInferiority.YES: Row.NI_4_DISCUSS,
            NonInferiority.NO_BEYOND: Row.NI_5_DONT_BEYOND,
            NonInferiority.NO_CROSSES: Row.NI_6_DONT_CROSSES,
        }[n]
    return Decision(row, s, n, t, srm, flags)


def _oriented(ci: Interval, higher_is_better: bool) -> tuple[float, float]:
    """CI bounds with "better" pointing up. Flips signs for lower-is-better."""
    return (ci.low, ci.high) if higher_is_better else (-ci.high, -ci.low)
