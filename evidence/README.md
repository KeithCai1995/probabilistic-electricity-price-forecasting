# Evidence index

## Purpose

This directory records the applicant's independent verification and learning work
after the initial portfolio snapshot was placed under version control. It is intended
to make the process inspectable without implying that pre-import development steps
were completed by the applicant.

All datasets and results in this directory come from the included simulator. No
Tarim Oilfield, employer, client or live-market data are used.

## Suggested reading order

1. `../PROJECT_HISTORY.md` — provenance and Git-history boundary;
2. `learning_log/baseline_reproduction.md` — independent baseline reproduction;
3. `learning_log/gamma_050_sensitivity.md` — rerun of the supplied sensitivity;
4. `learning_log/gamma_030_plan.md` — intermediate-gamma plan written before running;
5. `learning_log/gamma_030_results.md` — observed results and limitations;
6. the relevant `runs/*/outputs/run_manifest.json` and result tables.

## Environment and tests

| File | Purpose |
| --- | --- |
| `python_version.txt` | Local Python version recorded on Windows |
| `unit_tests.txt` | Clean output from six passing unit tests |

The supplied reference environment used Python 3.12.14. The applicant's local
verification used Python 3.13.15 with the locked package versions.

## Terminal logs

| File | Command represented |
| --- | --- |
| `baseline_terminal_log.txt` | Baseline run using `configs/base.yaml` |
| `gamma_050_terminal_log.txt` | Supplied sensitivity using gamma 0.050 |
| `gamma_030_terminal_log.txt` | Applicant-planned run using gamma 0.030 |

The logs are stored as UTF-8 text so they can be reviewed directly. Exit code 0 was
recorded for all three runs.

## Learning records

| File | Status |
| --- | --- |
| `learning_log/baseline_reproduction.md` | Completed 25 September 2026 |
| `learning_log/gamma_050_sensitivity.md` | Completed 25 September 2026 |
| `learning_log/gamma_030_plan.md` | Committed before the gamma 0.030 run |
| `learning_log/gamma_030_results.md` | Completed 26 September 2026 |

The gamma 0.030 plan states the hypothesis and evaluation criteria before the result
was known. The result record reports both improvements and non-improvements.

## Generated run snapshots

| Directory | Configuration | Status |
| --- | --- | --- |
| `runs/baseline/` | `configs/base.yaml`, gamma 0.015 | Independent baseline reproduction |
| `runs/gamma_050/` | `configs/gamma_sensitivity.yaml`, gamma 0.050 | Rerun of supplied sensitivity |
| `runs/gamma_030/` | `configs/gamma_030.yaml`, gamma 0.030 | Applicant-planned exploratory run |

Each run directory contains:

- `data/simulated_hourly_market.csv` — generated simulated benchmark;
- `outputs/run_manifest.json` — seed, configuration, software and data fingerprint;
- `outputs/forecast_quantiles_test.csv` — evaluation-period forecasts;
- `outputs/tables/` — overall, rolling-origin, subset and reliability tables;
- `outputs/figures/` — six generated diagnostic figures.

## Key local Adaptive CQR comparison

| Adaptive gamma | Coverage | Mean width | Interval score |
| ---: | ---: | ---: | ---: |
| 0.015 | 0.826305 | 22.362592 | 30.906253 |
| 0.030 | 0.811245 | 21.671771 | 30.906484 |
| 0.050 | 0.804217 | 21.348917 | 31.116844 |

The target coverage is 0.80. Gamma 0.050 is closest to that target and has the
narrowest interval, but it has a worse interval score. Gamma 0.015 has the lowest
interval score by a very small margin. Gamma 0.030 gives an intermediate result.
No setting is presented as universally optimal.

## Reference snapshots versus applicant evidence

The imported reference snapshots are stored separately under `../experiments/`.
The legacy directory `../experiments/gamma_005/` represents gamma 0.050. Files under
this `evidence/` directory record later applicant-run verification. Reference and
applicant metrics should not be silently combined because tiny cross-platform
floating-point differences changed the exact simulated values and fingerprints.

## Scope limits

These records show execution, checking, a controlled parameter change and result
interpretation on one simulated benchmark. They do not establish:

- performance on real electricity-market or employer data;
- general validity under every form of temporal dependence or regime shift;
- jointly reliable 24-hour scenario paths from marginal hourly intervals;
- an independently validated optimal gamma;
- personal authorship of development work completed before the Git import.
