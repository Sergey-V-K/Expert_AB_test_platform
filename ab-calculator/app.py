"""Streamlit UI. Run: streamlit run app.py

Rules:
- No statistics here. Only the form, calls to the engine, and drawing.
- Convert % and p.p. to fractions here, before calling the engine.

PM mode only (v1). Expert mode comes in v2 (SPEC Step 0).
"""

import streamlit as st

from sources import ALL_SOURCES
from ui import analysis_tab, design_tab

st.set_page_config(page_title="A/B Test Calculator", page_icon="🧪", layout="centered")

# ── Sidebar ──
with st.sidebar:
    # v1 is PM only; Expert comes in v2 (SPEC Step 0, BACKLOG B22).
    st.radio("User mode", ["PM", "Expert – v2"], index=0, disabled=True)
    st.caption("Data source")
    for source in ALL_SOURCES:
        label = source.name if source.available else f"{source.name} (soon)"
        st.button(label, disabled=not source.available, key=f"src_{source.name}",
                  width="stretch")
    st.divider()
    st.caption(
        "Assumptions: one metric, two groups, independent per-user observations, "
        "large-sample approximation, fixed-horizon test (no peeking). "
        "Run each guardrail metric separately with its own margin."
    )

# ── Header ──
st.title("A/B Test Calculator")
st.caption("Before the test: how many users and days? After the test: can we ship?")

c1, c2 = st.columns([1, 1])
metric = c1.radio("Metric", ["Binary (conversion)", "Continuous (mean)"], horizontal=True)
ni = c2.checkbox(
    "Include non-inferiority",
    help="Turn on when the question is \"does it hurt by more than X?\": UI simplification, "
         "migrations, removing features. If unsure, leave it off.",
)
metric_type = "binary" if metric.startswith("Binary") else "continuous"

tab_design, tab_analysis = st.tabs(["Design", "Analysis"])
with tab_design:
    design_tab.render(metric_type, ni)
with tab_analysis:
    analysis_tab.render(metric_type, ni)
