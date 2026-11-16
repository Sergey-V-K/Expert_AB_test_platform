"""User-facing text: decision labels, warnings, formatting (SPEC Step 4)."""

from __future__ import annotations

from engine.decision import Row, Threshold

# label, tone (success / warning / info / error), explanation
ROWS: dict[Row, tuple[str, str, str]] = {
    Row.SHIP: ("Ship", "success", "Treatment is significantly better than control."),
    Row.INCONCLUSIVE: (
        "Inconclusive: keep control", "info",
        "No significant difference detected. The CI includes zero. Keep control.",
    ),
    Row.DONT_SHIP: ("Don't ship", "error", "Treatment is significantly worse than control."),
    Row.NI_1_SHIP: ("Ship", "success", "Treatment is significantly better than control."),
    Row.NI_2_SAFE: (
        "Safe to ship", "success",
        "No significant difference, and the CI rules out a drop beyond the margin.",
    ),
    Row.NI_3_DONT: (
        "Don't ship", "error",
        "No significant difference, but a drop beyond the margin cannot be ruled out.",
    ),
    Row.NI_4_DISCUSS: (
        "Discuss: worse, but within margin", "warning",
        "Treatment is significantly worse, but within the acceptable margin. "
        "Discuss with the product team before shipping.",
    ),
    Row.NI_5_DONT_BEYOND: (
        "Don't ship", "error", "Treatment is worse than control beyond the acceptable margin.",
    ),
    Row.NI_6_DONT_CROSSES: (
        "Don't ship", "error",
        "Treatment is significantly worse, and a drop beyond the margin cannot be ruled out.",
    ),
    Row.SRM_FAILURE: (
        "SRM failure", "error",
        "Sample ratio mismatch. The results cannot be trusted. "
        "Find the cause before any decision.",
    ),
}

# Decision matrices shown under the verdict, as in Colab.
MATRIX_SUP = [
    (Row.SHIP, "Better", "Ship"),
    (Row.INCONCLUSIVE, "Not significant", "Inconclusive: keep control"),
    (Row.DONT_SHIP, "Worse", "Don't ship"),
]
MATRIX_NI = [
    (Row.NI_1_SHIP, "Better", "Yes", "Ship"),
    (Row.NI_2_SAFE, "Not significant", "Yes", "Safe to ship"),
    (Row.NI_3_DONT, "Not significant", "No", "Don't ship"),
    (Row.NI_4_DISCUSS, "Worse", "Yes", "Discuss"),
    (Row.NI_5_DONT_BEYOND, "Worse", "No, beyond margin", "Don't ship"),
    (Row.NI_6_DONT_CROSSES, "Worse", "No, crosses margin", "Don't ship"),
]

THRESHOLD = {
    Threshold.ABOVE: "The effect is above the threshold from the brief: it pays off.",
    Threshold.BELOW: "The effect is below the threshold from the brief: too small to pay off.",
    Threshold.UNCLEAR: "Unclear vs the threshold from the brief: the CI contains it.",
}

FLAGS = {
    "p_near_alpha": "The p-value is close to alpha. A small change in data could flip significance.",
    "ci_near_zero": "A CI edge is close to zero. The direction could change with more data.",
    "ci_near_margin": "The NI CI is close to the margin. The NI result could change with more data.",
    "ci_near_threshold": "A CI edge is close to the threshold. The threshold line could change with more data.",
    "p_ci_disagree": "The p-value and the CI disagree about significance. The verdict follows the CI.",
}

HELP = {
    "alpha": "False positive rate. 0.05 is standard. Superiority is two-sided; "
             "non-inferiority is one-sided (90% CI at 0.05). Use the same alpha in Design and Analysis.",
    "power": "Probability of detecting a real effect of the MDE size. 0.80 is standard.",
    "ratio": "Treatment users per control user. 1.0 = 50/50, 0.25 = 80/20 (control/treatment).",
    "margin": "Maximum acceptable drop. A product decision: agree on it with the team "
              "before the test and never change it after seeing results.",
    "threshold": "The smallest effect that pays off, from the experiment brief. "
                 "It does not change the decision; it adds one line under it.",
    "traffic": "Users entering the experiment per day, both groups together.",
    "sd": "Per-user standard deviation, from historical data.",
}


def fmt_effect(x: float, binary: bool) -> str:
    """Absolute effect: p.p. for binary metrics, metric units otherwise."""
    return f"{x * 100:+.3f} p.p." if binary else f"{x:+,.4g}"


def fmt_level(x: float, binary: bool) -> str:
    """A rate or mean."""
    return f"{x:.3%}" if binary else f"{x:,.4g}"


def fmt_days(days: int, recommended: int) -> str:
    weeks = recommended // 7
    if days == recommended:
        return f"{days} days ({weeks} full week{'s' if weeks > 1 else ''})"
    return f"{days} days → run {weeks} full week{'s' if weeks > 1 else ''} ({recommended} days)"


def fmt_p(p: float) -> str:
    return "< 0.0001" if p < 0.0001 else f"{p:.4f}"
