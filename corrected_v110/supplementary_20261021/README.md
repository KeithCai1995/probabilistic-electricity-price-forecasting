# Supplementary rolling-window control — 21 October 2026

This is a new supplementary study, not a rewrite or replacement of the corrected
18 October reference runs. Existing forecasting CSVs, four reference tables per
run, original logs and the downstream P2 input are unchanged.

## Design

Static by-horizon CQR uses all 82 original calibration days and then keeps its
correction fixed. The original adaptive wrapper uses a rolling buffer of 30
scores per horizon **and** updates alpha. Comparing only those wrappers cannot
separate rolling-window effects from alpha-feedback effects.

The new control sets gamma to zero while keeping the same horizon groups,
initial trailing-30-score buffers, subsequent rolling raw scores, raw quantile
model and target alpha=.20. The score buffer is independent of alpha. Thus the
control and gamma=.015 wrapper differ only in alpha feedback.

For each of the three previously used seeds, the full original baseline model
was reconstructed once; raw test quantiles and adaptive bounds were checked
against the preserved forecast before comparison. All raw quantiles and adaptive
bounds matched exactly. Calibration and test raw frames are saved here so both
wrappers can now be replayed without fitting a model. No gamma or seed was selected
using this study and no new untouched evaluation period is claimed.

## Results

| Seed | Method | Coverage | Width (EUR/MWh) | Interval score |
| --- | --- | ---: | ---: | ---: |
| 20260817 | Rolling fixed alpha | .820281 | 21.768209 | 30.592811 |
| 20260817 | Adaptive alpha | .806225 | 21.274739 | 30.727504 |
| 20260818 | Rolling fixed alpha | .822289 | 22.472269 | 32.070489 |
| 20260818 | Adaptive alpha | .814257 | 22.176603 | 32.236669 |
| 20260819 | Rolling fixed alpha | .825803 | 22.681780 | 32.514927 |
| 20260819 | Adaptive alpha | .817269 | 22.474140 | 32.780810 |

Alpha feedback narrows intervals by .208–.493 EUR/MWh and moves these overall
coverages closer to .80, but **worsens interval score in all three seeds** by
.135–.266. There is no evidence here that alpha feedback improves interval score
over the rolling fixed-alpha control. The earlier overall adaptive-versus-static
comparison evaluates a combined wrapper, not a separately established feedback
benefit. This is a limited simulated comparison, not a significance test,
real-market external validation, joint path calibration or coverage theorem.

## Files and reproduction

- `comparison_metrics.csv`: all five methods for the same three seeds.
- `adaptive_minus_fixed.csv`: paired method differences, not confidence intervals.
- `subset_metrics.csv`: overall and retrospectively selected price-extreme diagnostics.
- `<run>/calibration_raw_forecasts.csv`, `test_raw_forecasts.csv`: shared raw inputs.
- `<run>/rolling_control_intervals.csv`: fixed/adaptive bounds, alpha and corrections.
- `study_manifest.json`: actual execution times, software, source hashes and preserved-input checks.

```powershell
python -B scripts/check_rolling_control.py
python -B scripts/run_rolling_control.py --output-root local_runs/rolling_control_new
```

The first command is read-only and does not retrain. The second reconstructs the
three baseline models and writes a **new** output directory. Reusing a recognized
P1 run directory requires explicit `--overwrite`; preserved reference directories
remain protected. The manifest's source hashes describe the supplementary
execution snapshot, not the earlier reference experiments.
