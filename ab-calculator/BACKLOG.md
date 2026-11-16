# BACKLOG

## Step 1: to confirm
- B2. Low-counts threshold: start at ~25, calibrate with A/A simulation.

## v1: architecture
- B4. `sources`: manual input works; CSV, Excel, BigQuery, Looker are stubs, shown disabled.
- B5. Stub: aggregate per-event rows to per-user rows.
- B6. Engine returns data, not text. Superiority, NI, SRM are separate results.
- B15. Continuous metrics (Welch, summary stats).
- B16. Threshold and margin in p.p. or %; tests in absolute units; relative lift with delta-method CI.
- B21. Engine signatures take the method choices (CI method, NI sample-size method, test side) with PM defaults. Only defaults implemented; others raise `NotImplementedError`.

## v1: acceptance tests
- B18. Acceptance tests against public calculators, tolerance 1% of N (±0.001 p.p. on CI bounds). Superiority vs Evan Miller, NI vs Sealed Envelope (same alpha). Enter reference values by hand from the tools themselves.
  Cases: reference (baseline 11.30%, MDE 0.10 p.p., margin 0.30 p.p., alpha 0.05, power 0.80, 1:1), plus low baseline, high baseline, unequal split.
  Reference case, checked in the tools on 2026-11-14: Evan Miller 1,575,224 per group (our formula 1,579,473, +0.27%); Sealed Envelope NI 137,766 per group (exact formula 137,708; the tool rounds z, +0.04%). Low-baseline NI case: Sealed Envelope 648,079.
  Still to add from the tools: high baseline, unequal split.

## Later (v2, Expert / DA version)
- B7. Logic for CSV, Excel, BigQuery, Looker.
- B8. Several metrics per run; AND/OR decision rule. Correct alpha for success metrics, power for NI guardrails (Spotify 2024).
- B9. A/B/n.
- B10. Ratio metrics (delta method), CUPED, bootstrap.
- B11. A/A simulation: check criterion calibration and power.
- B12. Sequential testing.
- B17. Advanced NI sample size method (separate H0/H1 variances). Expert mode only.
- B24. Expert mode: expose method choices (CI method, NI method, test side, strict 95% NI to reproduce old Colab), raw z and SE.

## Before release
- B13. Deploy to Lightspeed's Coolify as a Dockerfile app (port 8501, bind 0.0.0.0, healthcheck /_stcore/health). Needs: instance URL, access model (SSO or Coolify basic auth), GitHub repo. Test the WebSocket through the Coolify proxy on the first deploy.
- B25. Freeze Colab with a banner pointing to the new calculator.

## Done
- B1. NI: one-sided alpha (90% CI at alpha = 0.05), Blackwelder with z(1 - alpha). Confirmed by research (`research/industry-practices.md`).
- B3. Pooled p and Wald CI disagree: verdict follows the CI, "Borderline" warning shown (SPEC 1.3).
- B20. Colab: corrected now (one-sided NI in analysis and both sample-size methods, new labels); frozen at v1 release (B25).
- B22. Sidebar: PM / Expert toggle, Expert disabled.
- B23. Duration shown as raw days and full weeks.
- v1 UI: Design and Analysis tabs, CI charts, decision table, warnings; runs locally.
- Step 0. Modes: PM in v1, Expert in v2, one engine. References: Evan Miller, Sealed Envelope, 1% tolerance.
- Step 4. Verdict: Colab outcomes + row 6; "No action" -> "Inconclusive: keep control", "Safe to ship*" -> "Discuss: worse, but within margin".

## Communication
- B14. Tell the colleague: the "Fleiss" option does not always give a smaller N; NI guardrails do not need a stricter alpha; alpha in Sealed Envelope is one-sided.
- B19. Tell users: Colab's NI was stricter than labelled (it matched Sealed Envelope only at alpha = 2.5%). Colab and the new calculator now use one-sided alpha. Old NI results may change from "Don't ship" to "Safe to ship"; same alpha now gives a smaller N (e.g. 137,708 vs 174,823 per group for 11.3% baseline and 0.30 p.p. margin). In Sealed Envelope, use the same alpha value as in our calculator. Two labels renamed.
