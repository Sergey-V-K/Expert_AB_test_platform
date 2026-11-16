# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A/B test calculator (design + analysis) for one metric and two groups. PM version first; the engine is built so a DA version can be added later. Python 3.11 (fixed by the server's Docker image).

**Status: v1 runs locally.** Engine and PM-mode UI work; all tests pass. Expert-mode options (non-default `ci_method`, `alternative`, `ni_method`) raise `NotImplementedError` until v2. Deployment target: Lightspeed's Coolify (Dockerfile app, port 8501), not set up yet. The docstrings are the spec for each function.

## Commands

```bash
python -m pip install -r requirements-dev.txt   # dev env (conda env "ab-calculator", py3.11)
python -m streamlit run app.py                   # UI
python -m pytest                                 # all tests
python -m pytest tests/test_stats.py::test_binary_superiority_matches_statsmodels   # one test
python -m pytest -k "ni_status"                  # by name
```

## Architecture

```
sources.py  ->  ExperimentData (per-group summary stats: n, conversions | mean, sd)
app.py      ->  sidebar, Metric + NI selectors, Design / Analysis tabs
ui/design_tab.py, ui/analysis_tab.py  forms, unit conversion (%/p.p. -> fractions), engine calls, drawing
ui/charts.py        Altair CI charts; pass height to st.altair_chart (Streamlit ignores the chart's own height)
ui/text.py          decision labels, warnings, help texts, formatting
engine/results.py   result dataclasses (Interval, SuperiorityResult, NonInferiorityResult, SRMResult)
engine/stats.py     tests: superiority / NI / Newcombe / relative-lift CI; re-exports checks and results
engine/checks.py    SRM, low counts, borderline flags
engine/design.py    sample size, duration (rounded up to full weeks), detectable effect, fits()
engine/decision.py  decide(srm, sup, ni, threshold, higher_is_better) -> Decision (matrix Row + statuses)
engine/options.py   method choices (CI method, test side, NI method), PM defaults, require_v1()
tests/test_acceptance.py  N vs Evan Miller / Sealed Envelope, 1% tolerance (BACKLOG B18)
tests/test_app.py   headless UI smoke tests (streamlit.testing.AppTest)
```

Layering rules (from README / `engine/__init__.py`):
- `engine` never imports Streamlit and never prints. Functions return frozen dataclasses / enums, not text (BACKLOG B6).
- `app.py` and `ui/` do no statistics — only the form, unit conversion, engine calls, drawing.
- Widget keys for effect inputs include the metric type, so switching Binary/Continuous does not carry values over.
- Inside the engine all values are fractions (0.113, not 11.3). Threshold/margin can be entered as absolute (p.p.) or relative (%); `stats.to_absolute` converts using the control baseline (planned in Design, observed in Analysis).
- Data sources implement the `DataSource` protocol. Only `ManualSource` works; CSV/Excel/BigQuery/Looker are `_Stub` subclasses with `available=False` that raise `NotImplementedError` and are shown disabled in the UI.
- Split a file when it grows past ~300 lines.

## Statistical decisions (SPEC.md is the source of truth)

**Change SPEC.md first, then the code.** Key points that are easy to get wrong:
- Superiority: two-sided alpha. Binary = pooled z-test p-value + Wald CI (unpooled SE); Newcombe CI added as a reference when counts are low.
- Non-inferiority: **one-sided alpha**; passes if the low bound of the **(1 − 2·alpha)** CI (90% at alpha=0.05) is above −margin. NI sample size = Blackwelder with z(1 − alpha), matching Sealed Envelope when the same alpha value is entered there (its NI alpha is one-sided). The Colab notebook has been corrected to the same rule.
- Reference calculators for PM mode: Evan Miller (superiority), Sealed Envelope (NI). Acceptance tolerance: 1% of N (BACKLOG B18).
- Labels: "No action" is now "Inconclusive: keep control"; "Safe to ship*" is now "Discuss: worse, but within margin" (SPEC Step 4).
- Modes: PM in v1; Expert (DA) in v2 on the same engine. Engine functions take method arguments with PM defaults; non-default values raise `NotImplementedError` (SPEC Step 0).
- Continuous metrics: always Welch on per-user summary stats.
- Relative lift CI: delta method, not the absolute CI divided by baseline.
- SRM: chi-squared on assigned-user counts, p < 0.001 (`SRM_THRESHOLD`, not tied to alpha); a failure blocks every verdict.
- Low counts: < 25 conversions in a group (`LOW_COUNTS_THRESHOLD`, to be calibrated — B2).
- Verdict is decided by where the CI sits relative to 0, −margin and the threshold. Decision matrix rows 1–6 follow the Colab labels, plus new row 6 (worse + NI CI crosses margin → Don't ship). The optional threshold never changes the row; it only adds an above/below/unclear line. `higher_is_better=False` flips signs.
- No user choice of test side or method in the PM version.

Out of scope for v1: multiple metrics, A/B/n, ratio metrics, CUPED, bootstrap, A/A simulation, sequential testing, real source logic. See BACKLOG.md.

## Tests

Tests compare the engine against **independent references** (statsmodels, scipy, hand-checked Sealed Envelope numbers), never against the engine's own earlier output. `statsmodels` is a dev-only dependency — the engine must not import it.

## Notes

- `.gitignore` excludes `data/`, `*.csv`, `*.xlsx`: never commit experiment data.
- The parent folder (`../`) contains older copies of `stats.py`, `design.py`, `decision.py` and `SPEC.md`; they are out of date (e.g. SPEC lacks Step 4). Work in this directory.
