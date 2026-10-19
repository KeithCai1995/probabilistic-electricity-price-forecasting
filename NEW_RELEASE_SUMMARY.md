# Corrected local release v1.1.0 — 2026-10-18

This note describes the reference package prepared on 2026-10-18. Earlier
v1.0.2 records are retained separately. See [project history](PROJECT_HISTORY.md)
for the version timeline, later local reproduction and sources.

The conformal correction now selects the exact discrete rank
`ceil((n+1)*(1-alpha))`, using positive infinity when the rank exceeds `n`.
Invalid/nonfinite inputs are rejected, decimal rank boundaries are protected,
infinite interval scores stay infinite, and conditional finite-only diagnostics
are labeled. The coverage-width chart now includes the historical raw .547691
point. Package metadata and runtime version both read 1.1.0.

Sixteen tests pass. Five full 420-day corrected runs are retained, each with three
rolling folds. Baseline adaptive coverage/width/score changes from the preserved
Windows v1.0.2 values `.826305 / 22.362592 / 30.906253` to
`.806225 / 21.274739 / 30.727504`. Raw quantile predictions match exactly, providing
a controlled calibration comparison. Baseline is not retuned.

| Gamma, seed 20260817 | Adaptive coverage | Width | Interval score |
| --- | ---: | ---: | ---: |
| .015 baseline | .806225 | 21.274739 | 30.727504 |
| .030 sensitivity | .798193 | 21.107557 | 30.833048 |
| .050 sensitivity | .795181 | 20.784492 | 30.999364 |

Across baseline seeds 20260817–20260819, adaptive coverage ranges .806225–.817269,
width 21.274739–22.474140, and score 30.727504–32.780810. Final-test unbounded
fractions are zero for all methods/runs. Infinity handling is still necessary for
small buffers and small alpha; it has not been replaced by a finite cap.

Old active outputs/experiments/report were moved inside `historical/v102/` and
their bytes preserved. Earlier `evidence/` personal logs remain unmodified.
Saved corrected reference results are under `corrected_v110/`; active report source is
`report/report_v110.md`. Read it for timing, dependence, clipping, subset and joint
calibration limitations. These simulated results are not evidence of live-market
performance or a new coverage theorem.
