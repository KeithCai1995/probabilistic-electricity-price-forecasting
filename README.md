# P1 — Electricity-price forecasting under regime shift — corrected v1.1.0

**SIMULATED BENCHMARK — NOT FIELD DATA.** These are research-training experiments,
not employer, Tarim Oilfield, named-market or trading-system results.

The 2026-10-18 corrected local edition fixes the conformal order statistic and
re-runs the baseline, two gamma sensitivities and three baseline simulation seeds.
Reference runs and earlier reproduction records are kept separately. See
[project history](PROJECT_HISTORY.md) for the version timeline and source note.

## Current result

At seed 20260817, gamma 0.015, adaptive marginal coverage is **0.806225**, mean
interval width **21.274739 EUR/MWh**, and interval score **30.727504**. The pooled
static comparator covers 0.924197 with width 27.580914; raw coverage is 0.556225.
The 80% target is descriptive here: this clipped, rolling adaptive implementation
does not establish a coverage theorem under arbitrary temporal dependence.

The corrected rank is `k = ceil((n+1)*(1-alpha))`, selecting sorted score `k-1`.
When `k > n`, the correction is positive infinity rather than the largest finite
score. Nonfinite scores and invalid alpha values are rejected. All five completed
runs had zero unbounded final-test intervals; the general boundary is nevertheless
tested and retained. Tables include unconditional means, unbounded fractions and
clearly named `finite_only_*` conditional diagnostics. Infinite means remain
infinite. Decimal alpha boundaries avoid accidental extra ranks from binary
floating-point arithmetic.

Read [the corrected report](report/report_v110.md),
[release summary](NEW_RELEASE_SUMMARY.md), and
[reproduction record](REPRODUCIBILITY_RECORD.md) for the evidence and limits.

Optional PDF reproduction uses `python -m pip install -r requirements-report.txt`
then `python scripts/build_report.py --output report/P1_Technical_Report_Haorui_Cai_v110.pdf`.
The report source includes page breaks and uses only corrected figures. The PDF
must be visually checked after rendering; the historical PDF is kept separately.

## Reproduce a new run

Use Python >=3.11, create and activate a virtual environment, then:

```powershell
python -m pip install -r requirements-lock.txt
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Join-Path (Get-Location).Path 'src')
$env:MPLCONFIGDIR=(Join-Path (Get-Location).Path '.matplotlib')
$env:OMP_NUM_THREADS='2'
python -m unittest discover -s tests -v
python scripts/run_experiment.py --config configs/base.yaml --output-root local_runs/v110_baseline
python scripts/run_experiment.py --config configs/gamma_030.yaml --output-root local_runs/v110_gamma_030
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml --output-root local_runs/v110_gamma_050
python scripts/run_seed_check.py --seed 20260818 --output-root local_runs/v110_seed_20260818
python scripts/run_seed_check.py --seed 20260819 --output-root local_runs/v110_seed_20260819
```

Scripts explicitly put this checkout's `src` first on the import path, including
when an existing editable installation points elsewhere. A run manifest records
software versions, config, data fingerprint, version and execution context.
The release includes 16 passing regression tests; use the current test output for
later runs. Do not overwrite preserved historical records.

## Artifact map

| Location | Status |
| --- | --- |
| `corrected_v110/baseline/` | Corrected reference run, seed 20260817, gamma .015 |
| `corrected_v110/gamma_030/`, `gamma_050/` | Corrected same-seed sensitivities |
| `corrected_v110/seed_20260818/`, `seed_20260819/` | Additional full baseline seeds |
| `corrected_v110/logs/` | Reference execution and test logs, 2026-10-18 |
| `report/report_v110.md` | Active corrected report source |
| `historical/v102/` | Earlier numerical outputs and historical reports/documentation; presentation wording cleaned |
| `evidence/` | Earlier reproduction records; numerical artifacts retained and index wording cleaned |
| `PROJECT_HISTORY.md` | Version timeline and source note |

The original v1.0.2 PDF is historical and must not be presented as the corrected
report. The old `experiments/gamma_005` name meant gamma .050. The unchanged original
simulated CSV remains under `data/`; each corrected run also exports its own data.
The new forecast for downstream P2 is
`corrected_v110/baseline/outputs/forecast_quantiles_test.csv` (1,992 rows).

## Interpretation boundaries

The 420-day simulator generates issuance-time forecast proxies by perturbing
realised simulated covariates; there are no actual publication vintages. Daily
issue time equals the first target time, so horizon 1 is a nowcast-like case,
and the historical `day-ahead` label is too strong without an operational timing
adapter. Lagged prices use only past history; no future backfill is used.

Hourly intervals are marginal, not jointly calibrated 24-hour paths. The online
wrapper uses separate horizon buffers of 30 past scores and clips alpha to
[.01,.99], changing the usual ACI recursion. Same-horizon updates use earlier
days' outcomes, under assumed immediate availability. Both the simulator and this
availability assumption need validation before any operational use.

The same final block is reused for gamma diagnostics; no new untouched evaluation
set is created. All 1,992 final-test rows are in the renewable-shift regime, so the
`Renewable shift` subset repeats `All` and there is no volatile final-test subset.
Rolling folds cover different periods and show substantial failures. Three seeds
are a small robustness check, not population inference or proof of superiority.

Established quantile-regression and conformal methods underpin the project;
`RELATED_WORK.md` preserves the literature and contribution boundary. See
[responsible use](RESPONSIBLE_USE.md) for scope and data-use limits.
