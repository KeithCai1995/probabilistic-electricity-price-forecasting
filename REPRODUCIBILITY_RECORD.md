# P1 reference reproducibility record

## Purpose and provenance

This file records the commands, environment and output snapshots supplied with the
portfolio and checked again on 22 September 2026. The results were regenerated from the included code
and checked against the saved tables. This is a technical reproducibility record. It
does not claim that the applicant personally performed each earlier development step.
The applicant should add a dated personal verification entry only after independently
running, inspecting and explaining the project.

All inputs are simulated. No Tarim Oilfield, employer or live-market data were used.

## Verified environment

- Python 3.12.14
- NumPy 2.3.5
- pandas 2.2.3
- SciPy 1.17.0
- scikit-learn 1.8.0
- Matplotlib 3.10.8
- PyYAML 6.0.3

The same package versions are recorded in `requirements-lock.txt`.

## Baseline reproduction

```bash
python scripts/run_experiment.py --config configs/base.yaml \
  --output-root evidence/runs/baseline
```

| Interval | Coverage | Mean width (EUR/MWh) | Interval score |
| --- | ---: | ---: | ---: |
| Raw quantiles | 0.547691 | 11.755545 | 34.348397 |
| Static CQR (pooled) | 0.924197 | 27.640967 | 32.181476 |
| Static CQR (by horizon) | 0.932731 | 29.289561 | 33.555028 |
| Adaptive CQR, gamma 0.015 | 0.825803 | 22.495669 | 30.953800 |

Median-model MAE was 6.302875 EUR/MWh, compared with 11.268044 for the
seasonal-naive baseline. The horizon-specific static comparator is deliberately
included because the adaptive method also calibrates by horizon. Adaptive CQR is
narrower and has a lower interval score in this simulation, but this comparison does
not establish that adaptation will be superior in a real market.

Adaptive-CQR coverage was 0.6275 on the extreme-price subset and 0.709924 on the
OOD-flag subset. These are failure results, not headline successes.

## Rolling-origin check

Each of the three earlier origins now evaluates raw, pooled-static,
horizon-specific-static and adaptive intervals. Adaptive-CQR coverage was 0.831845,
0.747024 and 0.839286 across the three folds. Its interval scores were 30.962542,
48.778363 and 44.645724. The middle fold remains difficult. The saved table reports
all four methods so the adaptive result is not confused with the pooled-static result.

## Parameter sensitivity

Only `calibration.adaptive_gamma` changes from `0.015` to `0.050` in
`configs/gamma_sensitivity.yaml`.

```bash
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml \
  --output-root evidence/runs/gamma_005
```

The faster update moved adaptive coverage from 0.825803 to 0.807229 and reduced
mean width from 22.495669 to 21.300759 EUR/MWh. The interval score became slightly
worse, from 30.953800 to 31.072058. Extreme-price coverage fell from 0.6275 to
0.6025, and OOD coverage fell from 0.709924 to 0.702290. A narrower interval was
therefore not a clear improvement. This is a post-hoc sensitivity diagnostic on the
same evaluation period, not a valid basis for tuning gamma or selecting a winner.
Gamma 0.015 remains the pre-specified reference configuration.

Saved reference tables are under `experiments/baseline` and
`experiments/gamma_005`.

## Automated checks

```bash
python -m unittest discover -s tests -v
```

Six tests passed again on 22 September 2026. They check chronological and complete
features, the finite-sample quantile, exclusion of target and realised-future
variables from model features, rejection of leading missing history, separation of
horizon-specific corrections, and non-use of a sample's own outcome in its adaptive
interval.
