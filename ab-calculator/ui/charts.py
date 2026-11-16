"""CI charts (Altair, ships with Streamlit). Drawing only."""

from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd

GREEN, RED, GREY = "#2e8b57", "#d84a3a", "#9aa0a6"


def ci_chart(
    low: float, high: float, point: float, color: str, title: str,
    x_domain: tuple[float, float], x_title: str,
    margin_at: Optional[float] = None,
) -> alt.LayerChart:
    """One horizontal CI bar with the point estimate, a dotted line at 0 and,
    for NI, a dashed line at the margin. Values are already in display units."""
    bar = pd.DataFrame({"low": [low], "high": [high], "y": [0]})
    pt = pd.DataFrame({"x": [point], "y": [0]})
    scale = alt.Scale(domain=list(x_domain), nice=False, zero=False)
    y = alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1, 1]))

    layers = [
        alt.Chart(pd.DataFrame({"x": [0], "y": [-1], "y2": [1]}))
        .mark_rule(strokeDash=[2, 3], color="#888", strokeWidth=1.5)
        .encode(x=alt.X("x:Q", scale=scale, title=x_title), y=y, y2="y2:Q"),
        alt.Chart(bar).mark_rule(strokeWidth=3, color=color)
        .encode(x=alt.X("low:Q", scale=scale, title=x_title), x2="high:Q", y=y),
        alt.Chart(bar).mark_tick(thickness=2, size=18, color=color, orient="vertical")
        .encode(x="low:Q", y=y),
        alt.Chart(bar).mark_tick(thickness=2, size=18, color=color, orient="vertical")
        .encode(x="high:Q", y=y),
        alt.Chart(pt).mark_point(filled=True, size=90, color=color)
        .encode(x="x:Q", y=y, tooltip=[alt.Tooltip("x:Q", title="Estimate", format=".4f")]),
    ]
    if margin_at is not None:
        m = pd.DataFrame({"x": [margin_at], "label": ["margin"]})
        layers.append(
            alt.Chart(m.assign(y=-1, y2=0.55)).mark_rule(strokeDash=[6, 4], color="#666", strokeWidth=1.5)
            .encode(x="x:Q", y=y, y2="y2:Q")
        )
        layers.append(
            alt.Chart(m.assign(y=0.75)).mark_text(dy=-4, color="#666", fontSize=11)
            .encode(x="x:Q", y=y, text="label:N")
        )
    return alt.layer(*layers).properties(title=title, height=90)


def domain(values: list[float]) -> tuple[float, float]:
    """Shared x range for both charts, with padding."""
    lo, hi = min(values + [0.0]), max(values + [0.0])
    pad = max((hi - lo) * 0.15, 1e-9)
    return lo - pad, hi + pad
