"""Decision: from test results to a verdict.

Superiority and non-inferiority are judged separately, then combined.
Verdicts are based on where the CI lies relative to 0, the threshold
from the brief, and -margin. Not on the p-value alone (SPEC 1.3).

A failed SRM check blocks every verdict.

Rules below are a proposal for review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from engine.stats import NonInferiorityResult, SRMResult, SuperiorityResult


class Verdict(str, Enum):
    """Superiority verdict. `threshold` = minimum worthwhile effect (>= 0)."""

    SRM_FAILURE = "srm_failure"          # split is broken, do not interpret
    SHIP = "ship"                        # CI fully above threshold
    TOO_SMALL = "too_small"              # CI above 0, but fully below threshold
    HARM = "harm"                        # CI fully below 0
    NO_WORTHWHILE_EFFECT = "no_worthwhile_effect"  # CI has 0, fully below threshold
    INCONCLUSIVE = "inconclusive"        # CI too wide to tell


class NIVerdict(str, Enum):
    NON_INFERIOR = "non_inferior"   # CI low > -margin
    INFERIOR = "inferior"           # CI high < -margin
    INCONCLUSIVE = "inconclusive"   # CI crosses -margin


@dataclass(frozen=True)
class Decision:
    """Everything the UI needs to show the result."""

    verdict: Verdict
    ni_verdict: Optional[NIVerdict]
    srm: SRMResult
    flags: list[str] = field(default_factory=list)  # borderline, low_counts


def superiority_verdict(
    result: SuperiorityResult, threshold: float = 0.0, higher_is_better: bool = True
) -> Verdict:
    """Verdict from the two-sided CI, in this order:

    1. ci.low  > threshold                 -> SHIP
    2. ci.high < 0                         -> HARM
    3. ci.high < threshold and ci.low > 0  -> TOO_SMALL
    4. ci.high < threshold                 -> NO_WORTHWHILE_EFFECT
    5. otherwise                           -> INCONCLUSIVE

    threshold = 0 (no threshold in the brief) gives the classic
    win / loss / not significant.

    higher_is_better=False (e.g. time to event, error rate):
    flip the sign of diff and CI before the rules.
    """
    raise NotImplementedError


def ni_verdict(
    result: NonInferiorityResult, higher_is_better: bool = True
) -> NIVerdict:
    """Verdict from the (1 - 2*alpha) CI:

    ci.low  > -margin -> NON_INFERIOR
    ci.high < -margin -> INFERIOR
    otherwise         -> INCONCLUSIVE

    higher_is_better=False: flip signs first.
    """
    raise NotImplementedError


def decide(
    srm: SRMResult,
    sup: SuperiorityResult,
    ni: Optional[NonInferiorityResult] = None,
    threshold: float = 0.0,
    higher_is_better: bool = True,
    flags: Optional[list[str]] = None,
) -> Decision:
    """Combine all checks into one Decision.

    If srm.failed: verdict = SRM_FAILURE and ni_verdict = None.
    The numbers are still in `sup` and `ni` for diagnosis,
    but the UI must not show them as a decision.
    """
    raise NotImplementedError
