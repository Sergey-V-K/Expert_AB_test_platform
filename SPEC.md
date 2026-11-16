# SPEC

Agreed decisions. Change them here first, then in the code.

## Step 1. Methods

| # | Decision | Based on |
|---|---|---|
| 1.1 | Superiority: two-sided alpha. Non-inferiority: one-sided alpha, NI passes if the low bound of the (1 - 2*alpha) CI is above -margin. NI sample size: Blackwelder with z(1 - alpha), same numbers as Sealed Envelope with the same alpha. **To confirm (B1).** | GrowthBook, Statsig, Spotify, Sealed Envelope |
| 1.2 | Binary analysis: pooled z-test for p-value, Wald CI (unpooled SE). Newcombe CI shown as a reference when counts are low. | Standard online calculators; Fagerland et al. 2011 |
| 1.3 | Verdict by the position of the CI relative to 0, the threshold and -margin. CI and p-value from the same test family. | Kohavi; Avito; Spotify |
| 1.4 | SRM: chi-squared on every analysis, p < 0.001, blocks the verdict. Not tied to alpha. Use counts of assigned users. | Kohavi |
| 1.5 | Continuous metrics: always Welch, on per-user summary stats (mean, SD, N). | Delacre et al. 2017; Yandex Go |
| 1.6 | Low-counts warning: fewer than ~25 conversions in a group. Calibrate later with A/A simulation (B2). | Online calculators; own simulation |

No choice of test side or test method in the PM version.

## Step 2. Scope of v1 (PM version)

In:
- Design: binary and continuous metrics; superiority and NI; sample size;
  duration (traffic-based and rounded up to full weeks); detectable effect
  for a given sample and a "fits / does not fit" check against the threshold.
- Analysis: CI, p-value, verdict in plain words; optional threshold from the
  brief; SRM block; borderline and low-counts warnings; hints about per-user
  data and assigned users.
- Threshold and margin can be entered in p.p. or %. Tests run in absolute
  units. Relative lift is shown with a delta-method CI.
- Data sources: manual input works. CSV, Excel, BigQuery, Looker are stubs,
  shown in the UI as disabled.

Out (later): several metrics per run, A/B/n, ratio metrics, CUPED,
bootstrap, A/A simulation, sequential testing, source logic.

## Step 3. Repository

GitHub. Python 3.11 (fixed by the Docker image on the server).
Flat structure, see README. Split files when they grow past ~300 lines.
Tests compare the engine with independent references
(statsmodels, scipy, Sealed Envelope), not with its own old output.
