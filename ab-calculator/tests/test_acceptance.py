"""Acceptance tests: PM mode vs the public calculators (SPEC Step 0, BACKLOG B18).

Superiority is checked against Evan Miller, NI against Sealed Envelope
(binary non-inferiority, same alpha). Tolerance: 1% of N per group.

Reference values must be entered by hand from the tools themselves.
`source` says where each number comes from. "formula" means the number
was computed from the tool's published formula and still has to be
confirmed in the tool. Change it to "tool" once checked.

Cases still to add (need tool values): low baseline, high baseline,
unequal split (Sealed Envelope only; Evan Miller supports 1:1 only).
"""

import pytest

from engine import design

TOLERANCE = 0.01  # 1% of N

# baseline, mde, alpha, power, ratio, expected n per group, source
# Checked 2026-11-14: evanmiller.org/ab-testing/sample-size.html, absolute MDE.
EVAN_MILLER = [
    pytest.param(0.113, 0.001, 0.05, 0.80, 1.0, 1_575_224, "tool", id="reference"),
]

# baseline, margin, alpha, power, ratio, expected n per group, source
# Checked 2026-11-14: sealedenvelope.com/power/binary-noninferior/,
# same % in both groups. Sealed Envelope rounds z to 1.645 and 0.842, so its N
# is 0.04% above the exact Blackwelder formula (137,708 and 647,806).
SEALED_ENVELOPE_NI = [
    pytest.param(0.113, 0.003, 0.05, 0.80, 1.0, 137_766, "tool", id="reference"),
    pytest.param(0.0021, 0.0002, 0.05, 0.80, 1.0, 648_079, "tool", id="low-baseline"),
]


@pytest.mark.parametrize("baseline,mde,alpha,power,ratio,expected,source", EVAN_MILLER)
def test_superiority_n_matches_evan_miller(baseline, mde, alpha, power, ratio, expected, source):
    r = design.binary_superiority_n(baseline, mde, alpha=alpha, power=power, ratio=ratio)
    assert r.n_control == pytest.approx(expected, rel=TOLERANCE)


@pytest.mark.parametrize("baseline,margin,alpha,power,ratio,expected,source", SEALED_ENVELOPE_NI)
def test_ni_n_matches_sealed_envelope(baseline, margin, alpha, power, ratio, expected, source):
    r = design.binary_non_inferiority_n(baseline, margin, alpha=alpha, power=power, ratio=ratio)
    assert r.n_control == pytest.approx(expected, rel=TOLERANCE)
