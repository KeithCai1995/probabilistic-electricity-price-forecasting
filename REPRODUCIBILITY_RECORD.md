# P1 reference and applicant reproducibility record

## Purpose and provenance

This file separates two kinds of evidence:

1. the supplied reference record, checked on 22 September 2026; and
2. the applicant's independent Windows verification, completed on 25–26 September
   2026 after the portfolio was placed under version control.

The imported portfolio files predate this Git repository. The later commits and
files under `evidence/` record only the work actually completed after import. They
do not claim that the applicant personally performed each earlier development step.

All inputs are simulated. No Tarim Oilfield, employer or live-market data were used.

## Supplied reference environment

- Python 3.12.14
- NumPy 2.3.5
- pandas 2.2.3
- SciPy 1.17.0
- scikit-learn 1.8.0
- Matplotlib 3.10.8
- PyYAML 6.0.3

The same package versions are recorded in `requirements-lock.txt`.

## Supplied baseline reference

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
narrower and has a lower interval score in this simulation, but this comparison
does not establish that adaptation will be superior in a real market.

Adaptive-CQR coverage was 0.6275 on the extreme-price subset and 0.709924 on the
OOD-flag subset. These are failure results, not headline successes.

## Supplied rolling-origin check

Each of the three earlier origins evaluates raw, pooled-static,
horizon-specific-static and adaptive intervals. Adaptive-CQR coverage was 0.831845,
0.747024 and 0.839286 across the three folds. Its interval scores were 30.962542,
48.778363 and 44.645724. The middle fold remains difficult. The saved table reports
all four methods so the adaptive result is not confused with the pooled-static result.

## Supplied gamma 0.050 sensitivity

Only `calibration.adaptive_gamma` changes from `0.015` to `0.050` in
`configs/gamma_sensitivity.yaml`.

```bash
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml \
  --output-root evidence/runs/gamma_050
```

The supplied reference sensitivity result moved adaptive coverage from 0.825803
to 0.807229 and reduced mean width from 22.495669 to 21.300759 EUR/MWh. The
interval score became slightly worse, from 30.953800 to 31.072058. Extreme-price
coverage fell from 0.6275 to 0.6025, and OOD coverage fell from 0.709924 to
0.702290. A narrower interval was therefore not a clear improvement.

This is a post-hoc sensitivity diagnostic on the same evaluation period, not a
valid basis for selecting a winner or claiming an independently tuned gamma.
Gamma 0.015 remains the pre-specified reference configuration.

The imported reference snapshots remain under `experiments/baseline/` and
`experiments/gamma_005/`. The latter is a legacy directory name for the gamma
0.050 run.

## Supplied automated checks

```bash
python -m unittest discover -s tests -v
```

Six tests passed in the supplied environment on 22 September 2026. They check
chronological and complete features, the finite-sample quantile, exclusion of target
and realised-future variables from model features, rejection of leading missing
history, separation of horizon-specific corrections, and non-use of a sample's own
outcome in its adaptive interval.

## Applicant verification: Windows and Python 3.13.15

### Environment and automated tests

The applicant created a local Windows virtual environment with Python 3.13.15 and
installed the locked dependencies. All six unit tests passed before the baseline
run on 25 September 2026. They were rerun on 26 September after documentation and
encoding checks and again passed six out of six with exit code 0.

Evidence:

- `evidence/python_version.txt`
- `evidence/unit_tests.txt`
- Git commit `8dc6c6a`

### Independent baseline reproduction

The applicant ran:

```bash
python scripts/run_experiment.py --config configs/base.yaml \
  --output-root evidence/runs/baseline
```

The run completed with exit code 0.

| Interval | Coverage | Mean width (EUR/MWh) | Interval score |
| --- | ---: | ---: | ---: |
| Raw quantiles | 0.556225 | 11.896091 | 34.007247 |
| Static CQR (pooled) | 0.924197 | 27.600691 | 32.188923 |
| Static CQR (by horizon) | 0.927711 | 29.282753 | 33.657756 |
| Adaptive CQR, gamma 0.015 | 0.826305 | 22.362592 | 30.906253 |

The seasonal-naive MAE was 11.268044 EUR/MWh and the quantile-model median MAE
was 6.299118 EUR/MWh.

The local simulated data had the same shape and non-numeric columns as the supplied
reference data. The numeric values matched after rounding to 10 decimal places, with
a maximum absolute difference of approximately `2.84e-14`. The local data
fingerprint differed because the fingerprint hashes the underlying floating-point
values. The result is therefore a successful numerical cross-platform reproduction,
not a byte-identical reproduction.

Evidence:

- `evidence/learning_log/baseline_reproduction.md`
- `evidence/baseline_terminal_log.txt`
- `evidence/runs/baseline/outputs/run_manifest.json`
- `evidence/runs/baseline/outputs/tables/overall_metrics.csv`
- Git commit `9a0bb1d`

### Rerun of the supplied gamma 0.050 sensitivity

The applicant reran the supplied sensitivity configuration on the local Windows
environment. The adaptive result was:

| Adaptive gamma | Coverage | Mean width | Interval score |
| ---: | ---: | ---: | ---: |
| 0.015 | 0.826305 | 22.362592 | 30.906253 |
| 0.050 | 0.804217 | 21.348917 | 31.116844 |

Gamma 0.050 moved coverage closer to the 0.80 target and narrowed the interval,
but its interval score was worse. The result was therefore mixed rather than a
general improvement. Raw and static results remained unchanged, as expected.

Evidence:

- `evidence/learning_log/gamma_050_sensitivity.md`
- `evidence/gamma_050_terminal_log.txt`
- `evidence/runs/gamma_050/outputs/tables/overall_metrics.csv`
- Git commit `9d1db12`

### Applicant-planned gamma 0.030 experiment

Before running the intermediate value, the applicant committed a dated plan explaining
the choice of gamma 0.030, the expected trade-off and the evaluation criteria. The
configuration changed only `adaptive_gamma` from 0.015 to 0.030.

| Adaptive gamma | Coverage | Mean width | Interval score |
| ---: | ---: | ---: | ---: |
| 0.015 | 0.826305 | 22.362592 | 30.906253 |
| 0.030 | 0.811245 | 21.671771 | 30.906484 |
| 0.050 | 0.804217 | 21.348917 | 31.116844 |

Gamma 0.030 produced coverage and width between the other two settings. Compared
with gamma 0.015, it moved coverage closer to the 0.80 target and reduced mean width
by about 3.1%, while the interval score increased by only about 0.00023. It was a
useful compromise in this simulated run, but it is not established as a universal
or independently validated optimum.

Evidence:

- `configs/gamma_030.yaml`
- `evidence/learning_log/gamma_030_plan.md`
- `evidence/learning_log/gamma_030_results.md`
- `evidence/gamma_030_terminal_log.txt`
- `evidence/runs/gamma_030/outputs/tables/overall_metrics.csv`
- pre-run plan commit `d926174`
- result commit `9adfbc4`

## Interpretation limits

The applicant's runs establish that the included pipeline executes successfully in
the recorded Windows environment and that the main qualitative findings are stable
to negligible cross-platform numerical differences. They do not establish real-market
performance, universal conformal coverage, joint 24-hour path validity or superiority
of one gamma value across datasets.

All gamma comparisons reuse the same final evaluation period. They must remain
labelled as post-hoc sensitivity analysis rather than independent hyperparameter
selection. The complete evidence map is in `evidence/README.md`.
