# Project 1 - Probabilistic electricity price forecasting under regime shift

> **Data status:** SIMULATED BENCHMARK - NOT FIELD DATA. All reported coverage,
> error and interval-width values are produced by the included simulator. They are
> not results from Tarim Oilfield, an employer or a named electricity market.

This portfolio demonstrates a leakage-controlled, reproducible pipeline for short-horizon
probabilistic electricity-price forecasting under regime shift. Seven pooled direct models,
one per quantile level, use forecast horizon as an input and estimate marginal uncertainty
for 24 hourly targets. The comparison includes a seasonal-naive baseline, pooled static
conformalized quantile regression (CQR), horizon-specific static CQR and an online
adaptive CQR wrapper.

## What the project demonstrates

- chronological train/calibration/evaluation separation and rolling-origin diagnostics;
- multi-quantile forecasts rather than point forecasts alone;
- calibration, sharpness, approximate CRPS, pinball loss and tail-subset evaluation;
- explicit stress tests for regime shift and out-of-distribution observations;
- one-command reproduction of every table and figure used in the technical report.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-lock.txt
python scripts/run_experiment.py --config configs/base.yaml --output-root evidence/runs/baseline
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml --output-root evidence/runs/gamma_005
python -m unittest discover -s tests -v
```

The separate output roots stop one run from overwriting another. Omit `--output-root`
only when intentionally refreshing the repository's main `outputs` folder. The fixed
random seed is stored in `configs/base.yaml`; each `run_manifest.json` records the
configuration, software versions and data fingerprint. `requirements-lock.txt` records
the exact package versions used for the supplied results, while `requirements.txt`
retains broader compatibility constraints.

`REPRODUCIBILITY_RECORD.md` records the supplied baseline, the gamma sensitivity
run and the results that became worse. It is a technical record, not evidence of the
applicant's personal development history. The two output snapshots are kept under
`experiments/`.

## Data boundary

The included benchmark is simulated and is deliberately labelled as such. It represents
hourly load, renewable output, day-ahead forecasts, data-quality incidents and three
market regimes. It is not Tarim Oilfield data and it is not evidence about any real
company or electricity market. The `data/README.md` file defines a schema for replacing
the benchmark with data exported from ENTSO-E, Elexon or Open Power System Data.

## Model choices

The default backend is scikit-learn's histogram gradient boosting with quantile loss so
that the project runs without proprietary software. An optional LightGBM backend can be
selected after installing `requirements-optional.txt`. Quantile crossings are repaired
by row-wise rearrangement; this practical choice is reported as a limitation.

## Relationship to existing work

The project implements established ideas rather than claiming a new foundational
algorithm. Quantile regression and CQR motivate the raw and static intervals;
adaptive and sequential conformal work motivates online updates under change; and
recent electricity-price studies show that probabilistic and conformal forecasting
is already an active field. `RELATED_WORK.md` records the closest strands and the
portfolio's narrow contribution boundary.

The contribution is an inspectable, leakage-controlled training benchmark with
reproducible stress tests and explicit failure analysis. It is not the first use of
conformal prediction for electricity prices and it does not establish general
coverage under arbitrary temporal dependence.

## Reproducibility notes

The two configurations and six unit tests provide a short verification path.
The main points to check are the chronological split, the coverage-width trade-off,
the difference between pooled and horizon-specific static calibration, the adaptive
update, extreme/OOD failures and the difference between marginal hourly intervals
and a jointly reliable 24-hour path.

The final 83-day block is a chronologically separated evaluation period. It is excluded
from fitting and conformal calibration, but it is also used for the reported post-hoc
parameter-sensitivity diagnostic. It should therefore not be described as an untouched
test set after the analysis was completed.

## Responsible use

Read `RESPONSIBLE_USE.md` before sharing. Do not describe the simulated results as field
evidence. A real-data extension should preserve the time ordering, issuance-time feature
availability and calibration/evaluation separation used here.
