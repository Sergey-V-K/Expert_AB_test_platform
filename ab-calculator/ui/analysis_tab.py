"""Analysis tab: test results, verdict, charts."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from engine import decision, stats
from engine.decision import NonInferiority, Row, Superiority
from ui import charts
from ui.text import FLAGS, HELP, MATRIX_NI, MATRIX_SUP, ROWS, THRESHOLD, fmt_effect, fmt_level, fmt_p

UNIT_REL = "% of baseline"


def _raw_effect(label: str, default: float, binary: bool, key: str, help: str) -> tuple[float, str]:
    """Number + unit, converted later (relative units need the observed baseline)."""
    c1, c2 = st.columns([3, 2])
    unit = c2.selectbox("Unit", ["p.p." if binary else "metric units", UNIT_REL],
                        key=f"{key}_unit", label_visibility="hidden")
    value = c1.number_input(label, value=default, min_value=0.0, step=0.01,
                            format="%.4f", key=key, help=help)
    return value, unit


def _to_abs(value: float, unit: str, binary: bool, baseline: float) -> float:
    if unit == UNIT_REL:
        return stats.to_absolute(value / 100, "rel", baseline)
    return value / 100 if binary else value


def render(metric_type: str, ni: bool) -> None:
    binary = metric_type == "binary"

    st.subheader("Results of the test")
    st.caption("Use per-user data (one user = one row) and counts of all assigned users, "
               "not only triggered or filtered ones.")
    c_ctl, c_trt = st.columns(2)
    with c_ctl.container(border=True):
        st.markdown("**Control**")
        if binary:
            conv_c = st.number_input("Conversions", value=56_500, min_value=0, step=100, key="a_conv_c")
        else:
            mean_c = st.number_input("Mean", value=100.0, key="a_mean_c")
            sd_c = st.number_input("SD (per user)", value=40.0, min_value=0.0, key="a_sd_c")
        n_c = st.number_input("Users (N)", value=500_000, min_value=1, step=1000, key="a_n_c")
    with c_trt.container(border=True):
        st.markdown("**Treatment**")
        if binary:
            conv_t = st.number_input("Conversions", value=56_250, min_value=0, step=100, key="a_conv_t")
        else:
            mean_t = st.number_input("Mean", value=101.0, key="a_mean_t")
            sd_t = st.number_input("SD (per user)", value=40.0, min_value=0.0, key="a_sd_t")
        n_t = st.number_input("Users (N)", value=500_000, min_value=1, step=1000, key="a_n_t")

    margin_raw = _raw_effect("Non-inferiority margin", 0.30 if binary else 5.0, binary,
                             f"a_margin_{metric_type}", HELP["margin"]) if ni else None

    c1, c2, c3 = st.columns(3)
    alpha = c1.number_input("Alpha", value=0.05, min_value=0.001, max_value=0.499, step=0.01,
                            format="%.3f", key="a_alpha", help=HELP["alpha"])
    ratio = c2.number_input("Planned ratio (T/C)", value=1.0, min_value=0.01, step=0.25,
                            key="a_ratio", help=HELP["ratio"] + " Used for the SRM check.")
    higher = c3.radio("Better is", ["Higher", "Lower"], horizontal=True, key="a_dir",
                      help="Lower is better for metrics like error rate or load time.") == "Higher"
    use_thr = st.checkbox("The brief has a threshold (smallest effect that pays off)", key="a_use_thr")
    thr_raw = _raw_effect("Threshold", 0.10 if binary else 2.0, binary, f"a_thr_{metric_type}",
                          HELP["threshold"]) if use_thr else None

    try:
        if binary:
            sup = stats.binary_superiority(conv_c, n_c, conv_t, n_t, alpha)
        else:
            sup = stats.continuous_superiority(mean_c, sd_c, n_c, mean_t, sd_t, n_t, alpha)
        margin = _to_abs(*margin_raw, binary, sup.control) if ni else None
        threshold = (_to_abs(*thr_raw, binary, sup.control) or None) if use_thr else None
        ni_r = None
        if ni:
            if binary:
                ni_r = stats.binary_non_inferiority(conv_c, n_c, conv_t, n_t, margin, alpha)
            else:
                ni_r = stats.continuous_non_inferiority(mean_c, sd_c, n_c, mean_t, sd_t, n_t,
                                                        margin, alpha)
        srm = stats.srm_check(n_c, n_t, ratio)
        flags = stats.borderline_flags(sup.p_value, alpha, sup.ci, margin=margin,
                                       threshold=threshold, ni_ci=ni_r.ci if ni_r else None,
                                       higher_is_better=higher)
        dec = decision.decide(srm, sup, ni_r, threshold if threshold else None, higher, flags)
    except ValueError as e:
        st.error(f"Check the inputs: {e}")
        return

    st.divider()
    _verdict(dec, srm)
    if dec.row is not Row.SRM_FAILURE:
        _warnings(dec, sup)
        _charts(sup, ni_r, dec, binary, higher)
    _numbers(sup, ni_r, binary, alpha, dec.row is Row.SRM_FAILURE)
    _matrix(dec.row, ni)


def _verdict(dec: decision.Decision, srm: stats.SRMResult) -> None:
    label, tone, text = ROWS[dec.row]
    box = {"success": st.success, "warning": st.warning, "info": st.info, "error": st.error}[tone]
    box(f"### {label}\n{text}")
    if dec.row is Row.SRM_FAILURE:
        st.error(f"Observed ratio T/C = {srm.observed_ratio:.4f}, planned {srm.expected_ratio:.4f}, "
                 f"SRM p-value = {srm.p_value:.2e} (< 0.001). Check that the planned ratio is "
                 "right, then look for allocation, logging or filtering bugs.")
    if dec.threshold is not None:
        st.markdown(f"**Threshold:** {THRESHOLD[dec.threshold]}")


def _warnings(dec: decision.Decision, sup: stats.SuperiorityResult) -> None:
    for f in dec.flags:
        st.warning(f"**Borderline result.** {FLAGS[f]}")
    if sup.low_counts:
        st.warning(f"**Low counts.** A group has fewer than {stats.LOW_COUNTS_THRESHOLD} "
                   "conversions, so the normal approximation is rough. "
                   "The Newcombe CI is shown below as a reference.")


def _charts(sup, ni_r, dec, binary: bool, higher: bool) -> None:
    k = 100 if binary else 1
    unit = "Treatment − Control, p.p." if binary else "Treatment − Control"
    values = [sup.ci.low * k, sup.ci.high * k]
    margin_at = None
    if ni_r:
        margin_at = (-ni_r.margin if higher else ni_r.margin) * k
        values += [ni_r.ci.low * k, ni_r.ci.high * k, margin_at]
    dom = charts.domain(values)

    color = {Superiority.BETTER: charts.GREEN, Superiority.WORSE: charts.RED}.get(
        dec.superiority, charts.GREY)
    st.altair_chart(charts.ci_chart(sup.ci.low * k, sup.ci.high * k, sup.diff * k, color,
                                    f"Superiority ({sup.ci.level:.0%} CI), p = {fmt_p(sup.p_value)}",
                                    dom, unit), width="stretch", height=190)
    if ni_r:
        ok = dec.non_inferiority is NonInferiority.YES
        st.altair_chart(charts.ci_chart(ni_r.ci.low * k, ni_r.ci.high * k, ni_r.diff * k,
                                        charts.GREEN if ok else charts.RED,
                                        f"Non-inferiority ({ni_r.ci.level:.0%} CI, one-sided alpha): "
                                        f"{'passed' if ok else 'not passed'}",
                                        dom, unit, margin_at=margin_at), width="stretch", height=190)


def _numbers(sup, ni_r, binary: bool, alpha: float, srm_failed: bool) -> None:
    def ci(i):
        return f"[{fmt_effect(i.low, binary)}, {fmt_effect(i.high, binary)}]"
    rows = [
        ("Control", fmt_level(sup.control, binary)),
        ("Treatment", fmt_level(sup.treatment, binary)),
        ("Difference (T − C)", fmt_effect(sup.diff, binary)),
        (f"{sup.ci.level:.0%} CI ({sup.method.split(', ')[-1]})", ci(sup.ci)),
        ("p-value (two-sided)", f"{fmt_p(sup.p_value)}  (alpha = {alpha})"),
    ]
    if not math.isnan(sup.rel_lift):
        rows.append(("Relative lift", f"{sup.rel_lift:+.2%}  "
                     f"[{sup.rel_ci.low:+.2%}, {sup.rel_ci.high:+.2%}]"))
    if sup.newcombe_ci is not None:
        rows.append(("Newcombe CI (reference)", ci(sup.newcombe_ci)))
    if ni_r:
        rows += [
            ("NI margin", fmt_effect(-ni_r.margin, binary)),
            (f"NI {ni_r.ci.level:.0%} CI", ci(ni_r.ci)),
            ("NI p-value (one-sided)", fmt_p(ni_r.p_value)),
        ]
    rows.append(("Method", sup.method))
    title = "Numbers (for diagnosis only: SRM failed)" if srm_failed else "Numbers"
    with st.expander(title, expanded=not srm_failed):
        st.table(pd.DataFrame(rows, columns=["", "Value"]).set_index(""))


def _matrix(row: Row, ni: bool) -> None:
    if ni:
        df = pd.DataFrame([(r.value, s, n, d) for r, s, n, d in MATRIX_NI],
                          columns=["#", "Superiority", "Non-inferior?", "Decision"])
        active = row.value
    else:
        df = pd.DataFrame([(i + 1, s, d) for i, (r, s, d) in enumerate(MATRIX_SUP)],
                          columns=["#", "Superiority", "Decision"])
        active = {Row.SHIP: 1, Row.INCONCLUSIVE: 2, Row.DONT_SHIP: 3}.get(row)
    with st.expander("Decision table"):
        st.dataframe(
            df.style.apply(lambda r: ["background-color: #fff3bf" if r["#"] == active else ""
                                      for _ in r], axis=1),
            hide_index=True, width="stretch",
        )
        if row is Row.SRM_FAILURE:
            st.caption("No row applies: SRM failure blocks the decision.")
