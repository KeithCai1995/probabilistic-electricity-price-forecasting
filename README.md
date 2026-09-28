# Project 1 — Probabilistic electricity-price forecasting under regime shift

> **Data status:** SIMULATED BENCHMARK — NOT FIELD DATA. All coverage, error and
> interval-width values in this repository come from the included simulator. They
> are not results from Tarim Oilfield, an employer, a named electricity market or
> a live trading system.

This application portfolio demonstrates a leakage-controlled and reproducible
pipeline for short-horizon probabilistic electricity-price forecasting under
regime shift. Seven pooled direct models, one for each quantile level, use forecast
horizon as an input and estimate marginal uncertainty for 24 hourly targets. The
comparison includes a seasonal-naive point baseline, raw quantile intervals,
pooled static conformalized quantile regression (CQR), horizon-specific static CQR
and an online adaptive CQR wrapper.

## What the project demonstrates

- chronological train/calibration/evaluation separation;
- rolling-origin diagnostics rather than a random train/test split;
- multi-quantile forecasts rather than point forecasts alone;
- coverage, interval width, interval score, pinball loss and approximate CRPS;
- explicit checks on extreme-price and out-of-distribution subsets;
- reproducible configurations, tests, manifests, tables and figures;
- honest reporting of calibration failures and trade-offs.

## Provenance and my verification work

The initial portfolio snapshot and supplied reference outputs predate this Git
repository. `PROJECT_HISTORY.md` records that boundary. I do not use the later Git
history as evidence that I personally completed every earlier development step.

After the initial import, I independently:

1. created a Windows virtual environment using Python 3.13.15;
2. ran all six unit tests successfully;
3. reproduced the baseline and compared it with the supplied Python 3.12.14
   reference run;
4. reran the supplied `adaptive_gamma = 0.050` sensitivity configuration;
5. wrote and committed a pre-run plan for an intermediate
   `adaptive_gamma = 0.030` experiment;
6. ran that experiment, compared all three gamma values and recorded its limits.

The dated records, terminal logs and generated outputs are indexed in
`evidence/README.md`. These records show my verification and learning work after
the import; they do not convert the pre-import history into personal Git evidence.

## Quick start

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the locked dependencies and run the tests:

```bash
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
```

Run the reference configuration without overwriting committed evidence:

```bash
python scripts/run_experiment.py --config configs/base.yaml --output-root local_runs/baseline
```

Optional sensitivity runs:

```bash
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml --output-root local_runs/gamma_050
python scripts/run_experiment.py --config configs/gamma_030.yaml --output-root local_runs/gamma_030
```

`local_runs/` is excluded by `.gitignore`. The fixed seed is stored in each YAML
configuration. Every generated `run_manifest.json` records the configuration,
software versions and data fingerprint.

## Configuration status

| Configuration | Adaptive gamma | Status and purpose |
| --- | ---: | --- |
| `configs/base.yaml` | 0.015 | Pre-specified reference configuration |
| `configs/gamma_sensitivity.yaml` | 0.050 | Supplied post-hoc sensitivity configuration |
| `configs/gamma_030.yaml` | 0.030 | Applicant-planned exploratory sensitivity run |

The supplied snapshot directory `experiments/gamma_005/` is a legacy name for the
`0.050` configuration. The directory is retained to preserve the imported reference
snapshot. New evidence uses the clearer name `evidence/runs/gamma_050/`.

The gamma comparisons reuse the same chronologically held-out evaluation block.
They are sensitivity diagnostics, not independent test-set tuning and not proof
that one gamma value is universally optimal. Gamma 0.015 remains the pre-specified
reference configuration.

## Reproducibility status

The supplied reference run used Python 3.12.14. I reproduced the pipeline on
Windows with Python 3.13.15 and the locked package versions. All six tests passed.
The local simulated data had the same shape and non-numeric values as the reference
data, and the numeric values matched after rounding to 10 decimal places. The
maximum absolute numeric difference was approximately `2.84e-14`.

Those negligible cross-platform floating-point differences changed the exact data
fingerprint and caused small metric differences. The Windows run is therefore
reported as a successful numerical cross-platform reproduction, not a byte-identical
reproduction. `REPRODUCIBILITY_RECORD.md` keeps the supplied reference results and
the later applicant verification results separate.

## Data boundary

The benchmark is simulated. It represents hourly load, renewable output,
day-ahead forecasts, data-quality incidents and three market regimes. It is not
Tarim Oilfield data and it is not evidence about any real company or electricity
market. `data/README.md` defines a schema for a possible future extension using
appropriately licensed public data.

Any real-data extension would need to preserve time order and issuance-time feature
availability. Employer or client data would additionally require permission,
de-identification and a separate data-governance review.

## Model choices

The default backend is scikit-learn histogram gradient boosting with quantile loss,
so the project can run without proprietary software. An optional LightGBM backend
can be selected after installing `requirements-optional.txt`. Quantile crossings
are repaired by row-wise rearrangement; this practical choice is reported as a
limitation.

The adaptive calibration parameter controls how quickly the interval correction
responds to recent errors. A larger gamma can react faster but may also produce
greater instability or larger penalties on missed observations. The personal
gamma 0.030 run therefore evaluates coverage, width and interval score together
rather than selecting a setting from coverage alone.

## Relationship to existing work

The project implements established ideas rather than claiming a new foundational
algorithm. Quantile regression and CQR motivate the raw and static intervals;
adaptive and sequential conformal work motivates online updates under change; and
recent electricity-price studies show that probabilistic and conformal forecasting
is already an active field. `RELATED_WORK.md` records the closest strands and the
project's contribution boundary.

The contribution is an inspectable training benchmark with explicit temporal
separation, reproducible stress tests and failure analysis. It is not the first use
of conformal prediction for electricity prices, and it does not establish general
coverage under arbitrary temporal dependence.

## Evaluation limits

The final 83-day block is chronologically separated from model fitting and initial
conformal calibration. However, it is also reused for the reported post-hoc gamma
sensitivity diagnostics. It should therefore not be described as an untouched test
set after those analyses were performed.

The reported hourly intervals are marginal intervals. They do not automatically
form a jointly reliable 24-hour scenario path. Results from one simulated dataset
and one random seed cannot establish real-market performance or universal model
superiority.

## Repository guide

- `REPRODUCIBILITY_RECORD.md` — supplied reference record plus dated applicant verification;
- `evidence/README.md` — index of personal logs, plans, runs and result tables;
- `PROJECT_HISTORY.md` — boundary between the imported snapshot and later Git work;
- `RELATED_WORK.md` — literature relationship and contribution limits;
- `RESPONSIBLE_USE.md` — data, claims and disclosure boundaries;
- `configs/` — reference and sensitivity configurations;
- `tests/` — six automated checks;
- `experiments/` — supplied reference snapshots;
- `evidence/runs/` — applicant-run output snapshots.

## Responsible use

Read `RESPONSIBLE_USE.md` before sharing or describing the project. Never present
the simulated results as employer, field or trading outcomes. If an application or
university asks about generative AI, coding assistance or external editing, disclose
that assistance accurately under the applicable rule.
