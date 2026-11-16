# SPEC

Agreed decisions. Change them here first, then in the code.
Evidence for the method choices: `research/industry-practices.md`.

## Step 0. Modes and references

- Two modes: **PM** and **Expert**. PM mode is Expert mode with locked
  defaults: one engine, same numbers when Expert uses the defaults.
- v1 ships **PM mode only**. Expert mode (the DA version) is v2. In v1 the
  PM / Expert toggle is shown in the sidebar, disabled ("Expert – v2").
- Design / Analysis are the main tabs. PM / Expert is a separate toggle that
  changes which inputs and outputs are shown, not the workflow.
- The engine already takes the method choices as arguments (CI method,
  NI sample-size method, test side) with PM defaults. v1 implements only
  the defaults; other values raise `NotImplementedError`.
- Numbers follow industry practice and the public calculators, not the old
  Colab. References: **Evan Miller** for superiority, **Sealed Envelope**
  (binary non-inferiority) for NI, with the same alpha value.
- "Same numbers" = within **1%** of the reference N (and ±0.001 p.p. on CI
  bounds). Checked by acceptance tests on fixed cases with hand-entered
  reference values.

## Step 1. Methods

| # | Decision | Based on |
|---|---|---|
| 1.1 | Superiority: two-sided alpha. Sample size: pooled variance under H0, unpooled under H1 (0.27% from Evan Miller on the reference case; equal to statsmodels and Sealed Envelope). Non-inferiority: one-sided alpha, NI passes if the low bound of the (1 - 2*alpha) CI is above -margin (90% CI for alpha = 0.05). NI sample size: Blackwelder with z(1 - alpha), same numbers as Sealed Envelope with the same alpha. Colab is corrected to the same rule. | GrowthBook, Statsig, Spotify, Sealed Envelope |
| 1.2 | Binary analysis: pooled z-test for p-value (equals Evan Miller's chi-squared test), Wald CI (unpooled SE). Newcombe CI shown as a reference when counts are low. | Evan Miller; industry platforms; Fagerland et al. 2011 |
| 1.3 | Verdict by the position of the CI relative to 0, the threshold and -margin. The p-value is shown for reference. If the pooled p-value and the Wald CI disagree about significance, the verdict follows the CI and a "Borderline" warning is shown. | Kohavi; Avito; Spotify |
| 1.4 | SRM: chi-squared on every analysis, p < 0.001, blocks the verdict. Not tied to alpha. Use counts of assigned users. | Kohavi; Microsoft ExP; LinkedIn |
| 1.5 | Continuous metrics: always Welch, on per-user summary stats (mean, SD, N). | Delacre et al. 2017; Yandex Go |
| 1.6 | Low-counts warning: fewer than ~25 conversions in a group. Calibrate later with A/A simulation (B2). | Online calculators; own simulation |
| 1.7 | Borderline warning as in Colab: p-value within [0.7*alpha, 1.3*alpha], or a CI edge within 10% of the CI width from 0 or -margin. | Colab |

No choice of test side or test method in the PM version.

## Step 2. Scope of v1 (PM version)

In:
- Design: binary and continuous metrics; superiority and NI; sample size;
  duration shown as raw days and rounded up to full weeks
  (e.g. "23 days -> run 4 full weeks (28 days)"); detectable effect
  for a given sample and a "fits / does not fit" check against the threshold.
- Analysis: CI, p-value, verdict in plain words; optional threshold from the
  brief; SRM block; borderline and low-counts warnings; hints about per-user
  data and assigned users.
- Threshold and margin can be entered in p.p. or %. Tests run in absolute
  units. Relative lift is shown with a delta-method CI.
- Data sources: manual input works. CSV, Excel, BigQuery, Looker are stubs,
  shown in the UI as disabled.

Out (later): Expert mode (v2), several metrics per run, A/B/n, ratio metrics,
CUPED, bootstrap, A/A simulation, sequential testing, source logic, the
"Advanced" NI sample-size method (separate H0/H1 variances, v2 Expert).

## Step 4. Verdict

Colab outcomes, with two labels renamed to industry wording
(GrowthBook, Statsig, Eppo, Amplitude) and row 6 added.

Superiority only:

| # | Superiority | Decision |
|---|---|---|
| 1 | Better | Ship |
| 2 | Not significant | Inconclusive: keep control (was "No action") |
| 3 | Worse | Don't ship |

Superiority + NI: the row is chosen from the pair of results:

| # | Superiority | NI | Decision |
|---|---|---|---|
| 1 | Better | Yes | Ship |
| 2 | Not significant | Yes | Safe to ship |
| 3 | Not significant | No | Don't ship |
| 4 | Worse | Yes | Discuss: worse, but within margin (was "Safe to ship*") |
| 5 | Worse | No, beyond margin | Don't ship |
| 6 | Worse | No, crosses margin | Don't ship (new, Colab showed row 3 here) |

SRM failure blocks every row.
Threshold from the brief (optional) does not change the row. It adds one
line under the verdict: effect above / below / unclear vs threshold.
`higher_is_better=False` flips signs for metrics where lower is better.

## Step 3. Repository

GitHub. Python 3.11 (fixed by the Docker image on the server).
Flat structure, see README. Split files when they grow past ~300 lines.
Tests compare the engine with independent references
(Evan Miller, Sealed Envelope, statsmodels, scipy), not with its own old output.

## Step 5. Colab

The Colab notebook is corrected now to match this SPEC on NI (one-sided
alpha, 90% CI, z(1 - alpha) in both NI sample-size methods) and on the
labels. When v1 ships, Colab is frozen with a banner pointing to the new
calculator.
