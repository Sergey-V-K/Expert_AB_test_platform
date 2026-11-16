"""Smoke tests for the Streamlit UI (headless, streamlit.testing.AppTest).

They check that the app runs without errors in the main scenarios and that
the numbers on screen are the engine's numbers. Statistics are tested in the
other test files.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _app(*steps):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    for step in steps:
        step(at)
        at.run()
    assert not at.exception, at.exception
    return at


def _ni(at):
    next(c for c in at.checkbox if c.label.startswith("Include")).check()


def _continuous(at):
    next(r for r in at.radio if r.label == "Metric").set_value("Continuous (mean)")


def _set(key, value):
    def step(at):
        next(n for n in at.number_input if n.key == key).set_value(value)
    return step


def test_default_design_and_verdict():
    at = _app()
    assert at.metric[0].value == "1,579,473"          # superiority N, as Colab
    assert any("Inconclusive: keep control" in i.value for i in at.info)


def test_ni_design_and_verdict():
    at = _app(_ni)
    assert [m.value for m in at.metric[:2]] == ["1,579,473", "137,708"]
    assert any("Safe to ship" in s.value for s in at.success)


def test_switching_metric_type_resets_effect_inputs():
    at = _app(_continuous, _ni)
    assert [m.value for m in at.metric[:2]] == ["6,280", "792"]


def test_srm_failure_blocks_verdict():
    at = _app(_ni, _set("a_n_t", 510_000))
    assert any("SRM failure" in e.value for e in at.error)
    assert not any("Safe to ship" in s.value for s in at.success)


@pytest.mark.parametrize("conv_t,label", [(57_500, "Ship"), (54_000, "Don't ship")])
def test_superiority_rows(conv_t, label):
    at = _app(_set("a_conv_t", conv_t))
    boxes = [b.value for b in list(at.success) + list(at.error)]
    assert any(b.startswith(f"### {label}\n") for b in boxes)


def test_low_counts_warning():
    at = _app(_set("a_conv_c", 4), _set("a_n_c", 50), _set("a_conv_t", 11), _set("a_n_t", 50))
    assert any("Low counts" in w.value for w in at.warning)
