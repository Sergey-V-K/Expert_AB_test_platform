# A/B Test Calculator

Design and analysis of A/B tests for one metric and two groups.
PM version first. The engine is built so a DA version can be added later.

Status: **v1 runs locally**. The statistics engine passes all tests,
including checks against Evan Miller and Sealed Envelope. The Streamlit UI
(PM mode, Design and Analysis tabs) works locally. Deployment (Coolify) is next.

## Structure

```
engine/stats.py     tests: z-test, Wald, Newcombe, Welch, relative lift
engine/checks.py    SRM, low counts, borderline flags
engine/results.py   result dataclasses
engine/options.py   method choices, PM defaults
engine/design.py    sample size, duration, detectable effect
engine/decision.py  verdict: superiority + NI + threshold + SRM block
sources.py          data sources: manual input works, others are stubs
app.py              Streamlit UI: sidebar, tabs
ui/                 UI pieces: design_tab, analysis_tab, charts, text (labels)
.streamlit/         Streamlit config (theme, no usage stats)
tests/              tests against independent references
SPEC.md             agreed decisions
BACKLOG.md          open items
```

Rules:
- `engine` does not import Streamlit and does not print.
- `app.py` does no statistics.
- Inside the engine all values are fractions (0.113, not 11.3).
- Stubs raise `NotImplementedError`. The UI shows them as disabled.

## First setup

1. Create an empty repo on GitHub (no README, no .gitignore).
2. Keep the project **outside Google Drive**, e.g. `~/code/ab-calculator`.
3. Push the skeleton:

```bash
cd ~/code/ab-calculator
git init
git add .
git commit -m "Skeleton: structure, docstrings, tests"
git branch -M main
git remote add origin git@github.com:<org>/ab-calculator.git
git push -u origin main
```

4. Create an environment with Python 3.11, outside the project folder:

```bash
conda create -n ab-calculator python=3.11 -y
conda activate ab-calculator
python -m pip install -r requirements-dev.txt
```

## Run

```bash
python -m streamlit run app.py --server.address localhost   # UI at http://localhost:8501
python -m pytest                  # tests
```
