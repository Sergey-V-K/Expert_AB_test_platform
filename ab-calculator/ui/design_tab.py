"""Design tab: sample size, duration, detectable effect."""

from __future__ import annotations

import streamlit as st

from engine import design, stats
from ui.text import HELP, fmt_days, fmt_effect

UNITS_BINARY = ["p.p.", "% of baseline"]
UNITS_CONT = ["metric units", "% of baseline"]


def effect_input(label: str, default: float, binary: bool, baseline: float,
                 key: str, help: str | None = None) -> float:
    """Number + unit. Returns an absolute effect in engine units (fractions)."""
    c1, c2 = st.columns([3, 2])
    units = UNITS_BINARY if binary else UNITS_CONT
    unit = c2.selectbox("Unit", units, key=f"{key}_unit", label_visibility="hidden")
    value = c1.number_input(label, value=default, min_value=0.0, step=0.01,
                            format="%.4f", key=key, help=help)
    if unit == "% of baseline":
        return stats.to_absolute(value / 100, "rel", baseline)
    return value / 100 if binary else value


def render(metric_type: str, ni: bool) -> None:
    binary = metric_type == "binary"

    st.subheader("Inputs")
    if binary:
        baseline = st.number_input("Baseline conversion rate (%)", value=11.30, min_value=0.0,
                                   max_value=100.0, step=0.1, format="%.2f", key="d_base") / 100
        sd = None
    else:
        c1, c2 = st.columns(2)
        baseline = c1.number_input("Baseline mean", value=100.0, key="d_mean")
        sd = c2.number_input("Standard deviation (per user)", value=40.0, min_value=0.0,
                             key="d_sd", help=HELP["sd"])

    mde = effect_input("Minimum detectable effect (MDE)", 0.10 if binary else 2.0,
                       binary, baseline, f"d_mde_{metric_type}",
                       help="The smallest improvement the test should be able to detect.")
    margin = None
    if ni:
        margin = effect_input("Non-inferiority margin", 0.30 if binary else 5.0,
                              binary, baseline, f"d_margin_{metric_type}", help=HELP["margin"])

    c1, c2, c3, c4 = st.columns(4)
    alpha = c1.number_input("Alpha", value=0.05, min_value=0.001, max_value=0.499,
                            step=0.01, format="%.3f", key="d_alpha", help=HELP["alpha"])
    power = c2.number_input("Power", value=0.80, min_value=0.5, max_value=0.999,
                            step=0.05, format="%.2f", key="d_power", help=HELP["power"])
    ratio = c3.number_input("Ratio (T/C)", value=1.0, min_value=0.01, step=0.25,
                            key="d_ratio", help=HELP["ratio"])
    traffic = c4.number_input("Daily traffic", value=10_000, min_value=1, step=1000,
                              key="d_traffic", help=HELP["traffic"])

    try:
        if binary:
            sup = design.binary_superiority_n(baseline, mde, alpha, power, ratio)
            ni_n = design.binary_non_inferiority_n(baseline, margin, alpha, power, ratio) if ni else None
        else:
            sup = design.continuous_superiority_n(sd, mde, alpha, power, ratio)
            ni_n = design.continuous_non_inferiority_n(sd, margin, alpha, power, ratio) if ni else None
    except ValueError as e:
        st.error(f"Check the inputs: {e}")
        return

    st.subheader("Result")
    plans = [("Superiority", sup)] + ([("Non-inferiority", ni_n)] if ni else [])
    cols = st.columns(len(plans))
    for col, (name, n) in zip(cols, plans):
        d = design.duration(n.n_total, traffic)
        with col.container(border=True):
            st.markdown(f"**{name}**")
            st.metric("Users per group (control)", f"{n.n_control:,}")
            st.caption(f"Treatment: {n.n_treatment:,} · Total: {n.n_total:,}")
            st.caption(f"Duration: {fmt_days(d.days_by_traffic, d.days_recommended)}")

    biggest = max((n for _, n in plans), key=lambda n: n.n_total)
    d = design.duration(biggest.n_total, traffic)
    msg = (f"Collect **{biggest.n_total:,} users** in total: "
           f"{fmt_days(d.days_by_traffic, d.days_recommended)}.")
    if ni:
        msg += " This is the larger of the two, so one test answers both questions."
    st.success(msg)
    if biggest.n_total > traffic * 7 * 8:
        st.warning("This needs more than 8 weeks of traffic. Consider a larger MDE "
                   "or margin, or more traffic.")

    _detectable(binary, baseline, sd, alpha, power, ratio, ni, sup.n_control)


def _detectable(binary, baseline, sd, alpha, power, ratio, ni, default_n) -> None:
    with st.expander("What can a given sample detect?"):
        st.caption("Use this when the sample is fixed. Compare the detectable effect "
                   "with the threshold from the brief.")
        c1, c2 = st.columns(2)
        n_c = c1.number_input("Users per group (control)", value=int(default_n), min_value=2,
                              step=1000, key=f"d_fixed_n_{default_n}")
        test = c2.selectbox("Test", ["superiority"] + (["non_inferiority"] if ni else []),
                            format_func=lambda t: t.replace("_", "-").capitalize(), key="d_fixed_test")
        thr = effect_input("Threshold from the brief", 0.10 if binary else 2.0,
                           binary, baseline, f"d_thr_{'binary' if binary else 'continuous'}", help=HELP["threshold"])
        try:
            det = design.detectable_effect(int(n_c), ratio, alpha, power, test,
                                           "binary" if binary else "continuous",
                                           baseline=baseline if binary else None, sd=sd)
        except ValueError as e:
            st.error(str(e))
            return
        st.metric("Detectable effect", fmt_effect(det, binary).lstrip("+"))
        if thr > 0:
            if design.fits(det, thr):
                st.success("Fits: the test can detect effects of the size that matters.")
            else:
                st.error("Does not fit: the test cannot see effects of the size that matters. "
                         "Get more users, not a bigger threshold.")
