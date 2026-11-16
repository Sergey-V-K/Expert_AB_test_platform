# Industry practices: binary A/B tests (two groups, fixed horizon)

Researched 2026-11-14. Primary sources only: official docs, source code, and the companies' own engineering blogs. "not public" means no primary source was found. "could not verify" means a source exists but its method could not be read.
Code was read at these commits: GrowthBook `ca928b5` (2026-11-13) and spotify/confidence `0f12dd3` (2026-02-26).

## Summary

- **NI alpha.** Wherever the method is visible, an NI or guardrail check is a **one-sided test at the full α**:
  - Spotify `confidence` code: z(1−α) for the test and for sample size.
  - Sealed Envelope NI calculator: Φ⁻¹(α).
  - GrowthBook and Statsig: their one-sided tests do not halve α.

  Eppo is the exception. Its default 95% two-sided interval acts as a one-sided α=0.025 check, and Eppo tells users to set α=0.1 for a one-sided 0.05 test.
- **CI for the difference.** Every platform uses a **Wald-type normal (or Welch t) interval with unpooled per-arm variances**. No platform found uses Newcombe/Wilson for the difference. Newcombe appears only as the statsmodels default (`confint_proportions_2indep`). Evan Miller shows Wilson intervals per arm, not for the difference.
- **P-value.** Platforms use **unpooled** z or Welch t: Statsig, GrowthBook, Eppo, Optimizely, Spotify, Amplitude. Pooled tests appear only in the public calculators: Evan Miller's chi-squared (equal to a pooled z) and statsmodels `proportions_ztest`. AB Testguide and VWO use unpooled z.
- **Superiority N.** All the variants agree within about 0.8% for the reference case:
  - pooled H0 + unpooled H1 (Colab, statsmodels);
  - unpooled H0/H1 (Sealed Envelope, VWO);
  - baseline variance in both arms (Statsig calculator, GrowthBook).

  The choice does not matter in practice. The one-sided vs two-sided z matters a lot (about −21%).
- **SRM.** Chi-squared is near-universal. **p < 0.001 is the most common threshold** (GrowthBook, Eppo, Statsig red alert, AB Testguide). Microsoft uses 0.0005 and Amplitude uses a sequential test at α=0.01. Most tools **warn**. Microsoft ExP holds results back until SRM passes, LinkedIn hides the report by default, and Spotify Confidence makes SRM block "Ship".
- **Verdict labels.** Platforms use three or four levels: ship / discuss-review / don't ship (rollback), sometimes with "keep running". Borderline results go to a **"discuss / review" bucket**. No platform found uses a "p near α" flag.

## Comparison table

Columns: Q1 NI · Q2 CI / p-value · Q3 superiority N · Q4 SRM · Q5 labels and guardrails · Q6 simple/advanced. Markers [x] refer to the per-company notes.

| Company | Q1 NI | Q2 CI / p-value | Q3 Superiority N | Q4 SRM | Q5 Labels / guardrails | Q6 Modes |
|---|---|---|---|---|---|---|
| **Spotify (Confidence)** | One-sided at α: NIM sets a one-sided alternative, z(1−α), CI one-sided [S1][S2]. NI N: single (control) variance in both arms, z(1−α) [S3] | Unpooled z for both p-value and CI (SE = √(v₁/n₁+v₂/n₂)) [S1] | Unpooled: p(1−p) + (p+δ)(1−p−δ), no pooled H0 [S3] | Pearson χ² [S4]. Threshold not public in docs. Blocks "Ship"; Abort when SRM [S6] | Ship / Continue / End / Abort, shown as "Don't ship" after end [S6]. Guardrails = NI tests, not α-corrected, power-corrected [S5] | not public |
| **GrowthBook** | No NI margin in the stats engine (`test_value` = 0). One-sided tests use full α, t(1−α) [G1] | Welch t, unpooled variances, relative lift by default (delta method), absolute optional [G1][G2] | Power calc: control variance p(1−p) in both arms, relative effect, z(1−α/2) or z(1−α) [G3][G4] | χ² GOF [G5], p < 0.001 default [G6]. Warns [G7] | Ship now / Roll back now / Ready for review. "Clear Signals" or "Do No Harm" criteria with guardrails [G8] | not public |
| **Statsig** | One-sided test option ("non-inferiority tests"), all α in one direction. No margin setting documented [T1] | Z-test with unpooled var(Δ). Welch t if df < 100 [T2][T3] | Docs: MDE formula with z(1−α/2) [T4]. Public calculator: control variance in both arms, one-sided default [T5] | χ² [T6]. Yellow at 0.001–0.01, red at p < 0.001 and ≥ 0.1% deviation [T7]. Blocking not documented | Rollout Winning Group / Discuss / Do Not Roll Out [T8] | not public |
| **Eppo** | Default 95% CI = one-sided NI at α=0.025. Set α=0.1 for one-sided 0.05 [E1] | Normal CI, separate per-arm variances, relative lift via delta method [E2] | Relative MDE = (z(1−α/2)+z(1−β))·√(2σ²/N)/μ (single variance) [E3] | Pearson χ², α = 0.001. Warns [E4] | Roll out winning variant / Extend run time / Discuss with stakeholders / Do not roll out. Guardrail cutoff breach triggers a recommendation [E5] | not public |
| **Optimizely** | not public | Fixed-horizon doc: Wald CI, delta method, relative, two-sided [O1]. Default engine is sequential [O2] | Fixed-horizon doc: unpooled σ²_h, σ²_t, z(α/2) [O1]. Public calculator: sequential, formula not published [O2] | Sequential Bayesian multinomial test (SSRM), threshold not public. Warns [O3][O4] | "Statistically significant and positive/negative", "Not yet conclusive" [O4] | not public |
| **Amplitude Experiment** | not public | Welch t (unpooled). Default is sequential (mSPRT) [A1][A2] | not public | Sequential χ², α = 0.01. Notifies [A3][A4] | Significant / Not Significant / Inconclusive. P-values hidden until 100 users and 25 conversions per arm [A4] | Stats settings in an "Advanced" section (CUPED, Bonferroni, sequential, 95% by default) [A5] |
| **VWO** | Calculator has a "Non-inferiority" objective with ROPE [V1] | Calculator: unpooled z, plus Bayesian-style "chance to beat" [V2] | Unpooled H0/H1, z(1−FPR/2), relative MDE, ROPE default 1% [V1] | not public | not public | not public |
| **Microsoft ExP** | not public | not public | not public | χ², p < 0.0005. Results revealed only after the SRM test passes [M1] | not public | not public |
| **LinkedIn** | not public | not public | not public | χ² GOF, threshold not public. Report hidden by default plus a warning [L1] | not public | not public |
| **Uber** | not public | χ² for proportion metrics, α = 0.05 [U1] | not public | "Sample size imbalance" check, method not public [U1] | Monitoring: alert or pause on significant degradation (mSPRT) [U1] | not public |
| **Airbnb** | not public | not public | not public | Sequential SRM (SSRM) model mentioned [B1] | Impact guardrail: escalation if impact is below −T (e.g. −0.5%); about 80% of flagged launches go ahead after discussion [B2]* | not public |
| **Booking.com** | not public | not public | not public | not public | not public | not public |
| **Netflix** | not public | Sequential (anytime-valid) methods [N1] | not public | not public | not public | not public |

\* B2 is taken from a search-engine extract of Airbnb's own post. The full page returned HTTP 403, so treat it as partly verified.

## Online calculators

Reference case: baseline 11.30%, absolute MDE +0.10 p.p. (relative 0.885%), α = 0.05, power 0.80, 1:1 split. NI case: margin 0.30 p.p., true difference 0.

All N are **per group**. They were computed locally from each tool's published formula or JS source. None was taken from a screenshot of the tool.

| Calculator | Sample-size formula | Sides / MDE input | Analysis CI / test | Reference N per group |
|---|---|---|---|---|
| **Colab (ours)** | pooled p̄ under H0 + unpooled under H1 | two-sided z(1−α/2); absolute MDE | Newcombe CI; pooled z | **1,579,473** |
| statsmodels `samplesize_proportions_2indep_onetail` [R1] | pooled under H0 (`std_null`) + unpooled under H1 (`std_alt`) | two-sided by default | `confint_proportions_2indep` default **Newcombe**; `test_proportions_2indep` default Agresti-Caffo; `proportions_ztest` pooled [R1] | 1,579,473 (ceil of 1,579,472.06) |
| Sealed Envelope, binary superiority [C1] | unpooled: p₁q₁ + p₂q₂ | f(α/2, β), two-sided; inputs in % | none (design only) | 1,579,470 |
| VWO duration calculator [V1] | unpooled H0/H1 | z(1−FPR/2); relative MDE; defaults FPR 10%, ROPE 1% | unpooled z [V2] | 1,579,470 with FPR = 5% and ROPE = 0 (could not verify that the UI accepts ROPE = 0) |
| Evan Miller [C2] | √(2·p₁q₁) under H0 (baseline, not pooled) + unpooled under H1 | two-sided z(1−α/2); absolute or relative MDE | Pearson χ² without continuity correction (= pooled z); Wilson CI per arm [C3] | 1,575,224 (rounded) |
| Statsig public calculator [T5] | p₁q₁ for both arms | **one-sided by default ("Recommended")**; relative MDE; z from a lookup table | n/a | 1,239,368 one-sided (default); 1,573,403 two-sided |
| GrowthBook (in-app power, no standalone public calculator) [G3][G4] | p₁q₁ for both arms, delta method on relative lift | two-sided by default | Welch t | about 1,587,384 (solved numerically) |
| AB Testguide, analysis [C4] | sample-size tool is a Shiny app: **could not verify** | analysis default is **one-sided**, 95% | unpooled z; Wald CI per arm; SRM warning at p < 0.001 (z-test on share) | could not verify |
| Optimizely [O2] | sequential Stats Engine, formula not published | two-tailed; relative MDE | sequential | could not verify |
| CXL | page behind a Cloudflare challenge | | | could not verify |
| G*Power | not checked (desktop binary) | | | could not verify |

NI reference case (margin 0.30 p.p., p = 11.3% in both arms):

| Method | z for α | N per group |
|---|---|---|
| Colab "standard" (Blackwelder, 2pq) | z(1−α/2) = 1.960 | **174,823** |
| SPEC / Sealed Envelope NI at α = 5% [C1] / Spotify code [S3] | z(1−α) = 1.645 | **137,708** |
| Sealed Envelope NI at α = 2.5% | 1.960 | 174,823 |
| Colab "separate variances" (H0 at p−margin) | z(1−α/2) / z(1−α) | 173,400 / 136,648 |

**Important:** Sealed Envelope's NI formula is f(α, β) = [Φ⁻¹(α) + Φ⁻¹(β)]², which is one-sided [C1]. Its superiority calculator uses f(α/2, β). The Colab label "Standard (Blackwelder, matches Sealed Envelope)" is true **only if Sealed Envelope's α is set to 2.5%**. With the same α = 5% in both tools, Colab is 27% larger.

## Per-company notes

**Spotify (Confidence).** The open-source `spotify/confidence` library is not necessarily the same code as the commercial Confidence platform. The docs do not state the sidedness of NI.
- [S1] z-test computer: SE = √(var₁/n₁ + var₂/n₂). The p-value and CI use `_zstat_generic` / `_zconfint_generic` with `alternative` = preference ("larger"/"smaller" when a NIM is set). https://github.com/spotify/confidence/blob/0f12dd39afd15c48baf24e9d28fcbe72a905bb53/spotify_confidence/analysis/frequentist/confidence_computers/z_test_computer.py#L86-L120
- [S2] NIM handling: a direction makes the test one-sided, and the NIM is relative (× control mean). https://github.com/spotify/confidence/blob/0f12dd39afd15c48baf24e9d28fcbe72a905bb53/spotify_confidence/analysis/frequentist/nims_and_mdes.py#L46-L76 . z_alpha = Φ⁻¹(1 − α/(2 if two-sided else 1)): https://github.com/spotify/confidence/blob/0f12dd39afd15c48baf24e9d28fcbe72a905bb53/spotify_confidence/analysis/frequentist/confidence_computers/confidence_computer.py#L645-L649
- [S3] Sample size: n = (z_α+z_β)²/δ² · (σ²_c/κ + σ²_t). For binary superiority σ²_t = (p+δ)(1−p−δ). For NI σ²_t = σ²_c ("mean of control and treatment … identical"). https://github.com/spotify/confidence/blob/0f12dd39afd15c48baf24e9d28fcbe72a905bb53/spotify_confidence/analysis/frequentist/confidence_computers/z_test_computer.py#L456-L516
- [S4] SRM uses Pearson χ²: https://github.com/spotify/confidence/blob/0f12dd39afd15c48baf24e9d28fcbe72a905bb53/spotify_confidence/analysis/frequentist/sample_ratio_test.py
- [S5] Decision rule: ship if ≥1 success metric is superior and all guardrails are non-inferior. Guardrails are not α-corrected; power is corrected β/(G+1). Quality failures (SRM) block shipping. https://engineering.atspotify.com/2024/03/risk-aware-product-decisions-in-a-b-tests-with-multiple-metrics
- [S6] Labels Ship / Continue / End / Abort ("Don't ship" once ended). Ship requires no SRM. https://confidence.spotify.com/docs/experiments/analyze-results . NIM can be relative; tests run on absolute values: https://confidence.spotify.com/docs/capabilities/experiments/statistics/stat-tests

**GrowthBook.** Docs and code agree.
- [G1] `TwoSidedTTest` uses t(1−α/2); one-sided tests use t(1−α); Welch df. https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/stats/gbstats/frequentist/tests.py#L198-L241 . One-sided intervals are used only when `one_sided_intervals` is set (default False): https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/stats/gbstats/models/settings.py
- [G2] Relative vs absolute effects, delta method, Welch-Satterthwaite: https://docs.growthbook.io/statistics/details . Proportion variance = p(1−p): https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/stats/gbstats/models/statistics.py
- [G3] Power code: `getMetricVariance` = p(1−p) is used for both arms; `powerFrequentist` uses z(1−α/2) for two-tailed, otherwise z(1−α). https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/shared/src/power/power.ts#L337-L545
- [G4] Power docs state the assumptions "equal variance across control and treatment" and a two-sample t-test. https://docs.growthbook.io/statistics/power-technical
- [G5] `check_srm`: χ² GOF. https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/stats/gbstats/utils.py#L70-L84
- [G6] `DEFAULT_SRM_THRESHOLD = 0.001` (configurable `srmThreshold`). https://github.com/growthbook/growthbook/blob/ca928b54ef315ad7f34e30900e1a9b1ef386f018/packages/shared/src/constants.ts
- [G7] "will warn you … only … if the p-value is less than 0.001". https://docs.growthbook.io/using/experimenting#sample-ratio-mismatch-srm
- [G8] Decision framework: Ship now / Roll back now / Ready for review; "Unhealthy" status on SRM. https://docs.growthbook.io/app/experiment-decisions

**Statsig.**
- [T1] One-sided tests are also called non-inferiority tests; they put all alpha in one direction. https://docs.statsig.com/stats-engine/methodologies/one-sided-test-whn/
- [T2] Z-test, Welch when df < 100; CI = Δ ± z·√var(Δ). https://docs.statsig.com/stats-engine/confidence-intervals
- [T3] Z = (X̄t − X̄c)/√(var(X̄t)+var(X̄c)). https://docs.statsig.com/stats-engine/p-value
- [T4] Power analysis uses Z₁₋α/₂ and historical variance. https://docs.statsig.com/experiments-plus/power-analysis
- [T5] Public calculator JS: n′ = ((z_{1−α/s}+z_{1−β})·√(pA(1−pA))/(pB−pA))²; total = n′/(r(1−r)); relative MDE; "One-sided Test (Recommended)". https://www.statsig.com/calculator , https://www.statsig.com/js/calculator.js
- [T6] SRM χ²: https://docs.statsig.com/stats-engine/methodologies/srm-checks
- [T7] SRM thresholds table: https://docs.statsig.com/experiments/monitor
- [T8] Decision framework (advisory): https://docs.statsig.com/experiments/templates/decision-framework

**Eppo.**
- [E1] https://docs.geteppo.com/guides/advanced-experimentation/non-inferiority-tests
- [E2] https://docs.geteppo.com/statistics/confidence-intervals/statistical-nitty-gritty/
- [E3] https://docs.geteppo.com/statistics/sample-size-calculator/usage/
- [E4] https://docs.geteppo.com/statistics/sample-ratio-mismatch/
- [E5] https://docs.geteppo.com/experiment-analysis/configuration/protocols/

**Optimizely.**
- [O1] Fixed-horizon statistics page: https://docs.optimizely.com/experimentation-strategy/docs/frequentist-fixed-horizon-statistics
- [O2] Sample size calculator: "two-tailed sequential likelihood ratio test", relative MDE, default 95%. https://www.optimizely.com/sample-size-calculator/
- [O3] SRM detection: https://support.optimizely.com/hc/en-us/articles/13409080412173-Optimizely-s-automatic-sample-ratio-mismatch-detection
- [O4] Results page labels and SRM health status: https://docs.optimizely.com/performance-edge/docs/RuEB-optimizely-experiment-results-page

**Amplitude.**
- [A1] Welch t-test: https://amplitude.com/docs/feature-experiment/experiment-theory/analyze-with-t-test
- [A2] Sequential testing: https://amplitude.com/docs/faq/sequential-testing
- [A3] SRM: https://amplitude.com/docs/feature-experiment/troubleshooting/sample-ratio-mismatch
- [A4] Learnings page (labels, 100 users / 25 conversions rule): https://amplitude.com/docs/feature-experiment/workflow/experiment-learnings
- [A5] Statistical preferences: https://amplitude.com/docs/experiment/workflow/finalize-statistical-preferences

**VWO.**
- [V1] Duration calculator JS (`getRequiredVisitors`). https://vwo.com/tools/ab-test-duration-calculator/ . Script: https://wingify.com/wp-content/cache/autoptimize/1/js/autoptimize_single_87cc2458bba36b4d168a263d18973935.js
- [V2] Significance calculator JS (`calculatePValue`: unpooled SE). https://vwo.com/tools/ab-test-significance-calculator/ . Script: https://wingify.com/wp-content/cache/autoptimize/1/js/autoptimize_single_391238241e0e364af99b0559f2c4d8e9.js

**Microsoft ExP.** [M1] https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/

**LinkedIn.** [L1] https://www.linkedin.com/blog/engineering/ab-testing-experimentation/a-b-testing-variant-assignment

**Uber.** [U1] https://www.uber.com/blog/xp/

**Airbnb.**
- [B1] https://medium.com/airbnb-engineering/https-medium-com-jonathan-parks-scaling-erf-23fd17c91166
- [B2] https://medium.com/airbnb-engineering/designing-experimentation-guardrails-ed6a976ec669 (HTTP 403; details come from the search extract)

**Netflix.** [N1] https://netflixtechblog.com/sequential-a-b-testing-keeps-the-world-streaming-netflix-part-1-continuous-data-cba6c7ed49df

**Booking.com.** No primary source found on these questions. The Booking.com paper (https://arxiv.org/abs/1710.08217) abstract does not cover them, and the full text was not read.

**Calculators.**
- [C1] Sealed Envelope:
  - NI: https://www.sealedenvelope.com/power/binary-noninferior/
  - Superiority: https://www.sealedenvelope.com/power/binary-superiority/
- [C2] Evan Miller sample size: https://www.evanmiller.org/ab-testing/sample-size.html (`sample-size-fixed.js`)
- [C3] Evan Miller chi-squared: https://www.evanmiller.org/ab-testing/chi-squared.html (`chi-squared.js`)
- [C4] AB Testguide: https://abtestguide.com/calc/ (`js/script_srm_lowdata.js`)
- [R1] statsmodels 0.14.0, `statsmodels.stats.proportion`, read locally from the installed source: https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.confint_proportions_2indep.html

## Implications for matching Colab vs SPEC

| Point | Colab | SPEC | Industry majority | Supports | Flag |
|---|---|---|---|---|---|
| **NI CI level** | 95% two-sided (= one-sided 2.5%) | 90% two-sided (one-sided 5%) | One-sided at full α: Spotify code, Statsig, GrowthBook one-sided, Sealed Envelope NI. Eppo by default effectively uses 2.5%, but says one-sided 5% needs α = 0.1 | **SPEC** | Colab is stricter. It is defensible (pharma-like, same as Eppo's default) but not the product norm. |
| **NI N z-value** | z(1−α/2) | z(1−α) | z(1−α): Spotify code [S3], Sealed Envelope NI [C1] | **SPEC** | **Yes.** Colab says it "matches Sealed Envelope", but that holds only at SE α = 2.5%. At α = 5%: 174,823 vs 137,708 per group. To reproduce Colab exactly, the PM would have to enter α = 0.05 and silently get a 2.5% test. Each side is internally consistent (95% CI with z(1−α/2), 90% CI with z(1−α)). Do not mix them. |
| **CI method** | Newcombe | Wald (unpooled) | All platforms use Wald/Welch with unpooled variance; none uses Newcombe. statsmodels' default is Newcombe | **SPEC** for platforms. Colab has statsmodels on its side | Not a norm violation: at experiment-scale N the two agree to about 4 decimals. Newcombe is better with low counts. |
| **P-value test** | pooled z | pooled z | Platforms: unpooled (Statsig, GrowthBook, Eppo, Spotify, Optimizely, Amplitude). Calculators split: Evan Miller χ² is pooled; AB Testguide and VWO are unpooled | Platforms side with neither | SPEC 1.3 asks for "CI and p-value from the same test family". A pooled p-value with a Wald CI is not strictly one family, and they can disagree right at α. If that matters, use unpooled z + Wald (platform norm) or pooled z + score-type CI. |
| **Superiority N** | pooled H0 + unpooled H1 | same | Mixed; all within about 0.8% at the reference case | either | None. Colab = statsmodels exactly (1,579,473); Sealed Envelope/VWO 1,579,470; Evan Miller 1,575,224. Statsig's public calculator is one-sided by default (1,239,368). |
| **Superiority N vs online calculators** | above | above | Most two-sided calculators (Sealed Envelope, VWO, statsmodels, Evan Miller) land within 0.3% of Colab | Keep Colab's formula | Match is "approximate" against everything except statsmodels (exact). Matching Statsig/AB Testguide needs one-sided z. |
| **SRM** | χ², p < 0.001, blocks | same | χ² everywhere; 0.001 most common (GrowthBook, Eppo, Statsig red, AB Testguide); Microsoft 0.0005; Amplitude 0.01 sequential. Most tools **warn**; Microsoft (withhold), LinkedIn (hide) and Spotify (no Ship) block | Both (they agree) | Blocking is the stricter minority, backed by Microsoft, LinkedIn and Spotify. Not against the norm for a decision tool. |
| **Labels** | Ship / Safe to ship / Safe to ship* / Don't ship / No action | same, plus row 6 | 3–4 levels: ship / discuss-review / don't ship (+ keep running). Borderline goes to "discuss" | Both, roughly | "Safe to ship*" (significantly worse but within margin) matches the platforms' "Discuss / Ready for review". The p-near-α borderline flag has no platform precedent (neither good nor bad). Spotify's rule (ship only if ≥1 success metric wins) is stricter than "Safe to ship" on NI alone. |
| **Simple vs advanced mode** | n/a | PM version hides test side and method | Little public evidence. Amplitude keeps stats settings in an "Advanced" section; Statsig's calculator defaults to one-sided | n/a | n/a |

**Bottom line.** Reproducing Colab exactly goes against the clear norm on one point: **NI at z(1−α/2) / 95% CI for a stated α = 0.05**. That is defensible only if it is labelled as one-sided α = 0.025. Newcombe vs Wald is a non-issue at real sample sizes.
