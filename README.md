# P1 — Electricity-price forecasting under regime shift — corrected v1.1.0

**SIMULATED BENCHMARK — NOT FIELD DATA.**

This project compares quantile forecasts, static CQR and rolling adaptive CQR
for electricity prices under regime shifts. The corrected v1.1.0 runs, prepared
on 18 October 2026, include a baseline, two gamma sensitivities and three baseline
simulation seeds. See
[project history](PROJECT_HISTORY.md) for the version timeline and source note.

## Current result

At seed 20260817, gamma 0.015, adaptive marginal coverage is **0.806225**, mean
interval width **21.274739 EUR/MWh**, and interval score **30.727504**. The pooled
static comparator covers 0.924197 with width 27.580914; raw coverage is 0.556225.
The target is 80% hourly marginal coverage. Lower interval score is better.

The corrected rank is `k = ceil((n+1)*(1-alpha))`, selecting sorted score `k-1`.
When `k > n`, the correction is positive infinity. Nonfinite scores and invalid
alpha values are rejected, and decimal rank boundaries avoid floating-point
rounding errors. All five reference runs had zero unbounded final-test intervals.
The metric tables retain infinite full-sample means where needed and show
`finite_only_*` diagnostics separately.

Read [the corrected report](report/report_v110.md),
[release summary](NEW_RELEASE_SUMMARY.md), and
[reproduction record](REPRODUCIBILITY_RECORD.md) for the experiment details.

## Rolling-window control

The [fixed-alpha rolling control](corrected_v110/supplementary_20261021/README.md)
isolates alpha feedback from the shared 30-score rolling window. Across the three
existing seeds, gamma=0 gives coverage .820281–.825803 and slightly better interval
scores than gamma=.015. Feedback produces narrower intervals with coverage nearer
.80, but slightly worsens interval score in each seed. This separates the effect
of alpha feedback from that of the rolling window: the earlier adaptive-versus-static
comparison evaluates both together. The supplement was run on 21 October; the
original reference outputs and downstream P2 forecast are unchanged.

The active PDF is [Haorui_Cai_Forecasting_Report_v110.pdf](report/Haorui_Cai_Forecasting_Report_v110.pdf).
Optional PDF reproduction uses `python -m pip install -r requirements-report.txt`
then `python scripts/build_report.py`, which writes that same canonical filename.
The source uses corrected figures and explicit page breaks; check the rendered
PDF after rebuilding it. The historical PDF is kept separately.

## Reproduce a new run

Use Python >=3.11, create and activate a virtual environment, then:

```powershell
python -m pip install -r requirements-lock.txt
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Join-Path (Get-Location).Path 'src')
$env:MPLCONFIGDIR=(Join-Path (Get-Location).Path '.matplotlib')
$env:OMP_NUM_THREADS='2'
python -m unittest discover -s tests -v
python -B scripts/check_saved_outputs.py
python -B scripts/check_rolling_control.py
python scripts/run_experiment.py --config configs/base.yaml --output-root local_runs/v110_baseline
python scripts/run_experiment.py --config configs/gamma_030.yaml --output-root local_runs/v110_gamma_030
python scripts/run_experiment.py --config configs/gamma_sensitivity.yaml --output-root local_runs/v110_gamma_050
python scripts/run_seed_check.py --seed 20260818 --output-root local_runs/v110_seed_20260818
python scripts/run_seed_check.py --seed 20260819 --output-root local_runs/v110_seed_20260819
```

Scripts load this checkout's `src`, even if another editable installation exists.
Each run records its configuration, software versions and data fingerprint.

Use a dedicated `--output-root` for every experiment. Reusing a nonempty directory
requires `--overwrite` and a recognized P1 marker or run manifest. Arbitrary
existing directories, the repository root, source folders and preserved reference
directories remain protected. Overwrite replaces run-owned outputs without
deleting unrelated files. A new `local_runs/` directory is usually simplest;
`local_runs/` and `.matplotlib/` are ignored by Git.

The configured lower/upper quantiles and target miscoverage also govern the
rolling-origin comparator and all plot labels/coverage reference lines. Rolling
folds retain the original lower/median/upper three-model diagnostic; the default
q10/q90/80% design is unchanged.

## Verification

The 28 tests cover calibration edge cases, future-information perturbations,
output protection and a real-model q05/q95, 90%-target pipeline smoke. CI runs on
Ubuntu and Windows with Python 3.11 and 3.13. A separate full default rerun matched
all six baseline CSVs byte-for-byte, including the P2 input; CI uses the smaller
smoke dataset. See [VERIFICATION.md](VERIFICATION.md) for check results and commands.

The presentation update was merged in [PR #5](https://github.com/KeithCai1995/probabilistic-electricity-price-forecasting/pull/5),
and its [main-branch checks](https://github.com/KeithCai1995/probabilistic-electricity-price-forecasting/actions/runs/39736418760)
passed for commit `c1ad5d7`; results for other revisions are listed in Actions.

## Artifact map

| Location | Status |
| --- | --- |
| `corrected_v110/baseline/` | Corrected reference run, seed 20260817, gamma .015 |
| `corrected_v110/gamma_030/`, `gamma_050/` | Corrected same-seed sensitivities |
| `corrected_v110/seed_20260818/`, `seed_20260819/` | Additional full baseline seeds |
| `corrected_v110/logs/` | Reference execution and test logs, 2026-10-18 |
| `corrected_v110/supplementary_20261021/` | New fixed-alpha rolling control; shared raw frames and replay checks |
| `report/report_v110.md` | Active corrected report source |
| `historical/v102/` | Earlier numerical outputs, reports and documentation |
| `evidence/` | Earlier reproduction records |
| `PROJECT_HISTORY.md` | Version timeline and source note |

`corrected_v110/release_verification.json` describes its dated source snapshot;
the supplementary manifest records the later control experiment. Their recorded
hashes, dates and numerical values are retained when later code changes are made.

The v1.0.2 PDF is the historical report, not the corrected one. The old
`experiments/gamma_005` name meant gamma .050. The unchanged original
simulated CSV remains under `data/`; each corrected run also exports its own data.
The new forecast for downstream P2 is
`corrected_v110/baseline/outputs/forecast_quantiles_test.csv` (1,992 rows).

## Scope and limitations

These are research-training experiments on a 420-day simulator, not employer,
Tarim Oilfield, named-market or trading-system results. Forecast proxies are noisy
versions of simulated realised covariates rather than actual publication vintages.
Lagged prices use past history without future backfill. Daily issue time equals
the first target time, so horizon 1 is nowcast-like; the historical `day-ahead`
label needs a genuine prior issuance cutoff before operational use.

Hourly intervals are marginal, not jointly calibrated 24-hour paths. The online
wrapper uses 30 past scores per horizon and clips alpha to [.01,.99], which changes
the original ACI recursion. Coverage under dependent, shifting data is measured
empirically here, not guaranteed. Updates assume that earlier days' outcomes are
available immediately; real data delays and revisions would need explicit handling.

The same final block is reused for gamma diagnostics; no new untouched evaluation
set is created. All 1,992 final-test rows are in the renewable-shift regime, so
`Renewable shift` repeats `All`; there is no volatile final-test subset. Earlier
rolling folds show substantial coverage failures. Three seeds provide a small
robustness check rather than population inference or a universal method ranking.

The project uses established quantile-regression and conformal methods, with
sources in [RELATED_WORK.md](RELATED_WORK.md). See
[responsible use](RESPONSIBLE_USE.md) for scope and data-use limits.

## Presentation notes

Published logs and metadata replace the machine-specific prefix with `<WORKSPACE>`.
This placeholder is not a real directory. Path suffixes, experiment dates,
source/data hashes and numerical results are retained.
See [the presentation-update record](PRESENTATION_UPDATE_20261021.md).

Five rolling-coverage figures were redrawn from the same saved forecasts to show
the full 0-1 range, including raw coverage below .45. The live-plot regression
checks that all finite points remain visible. Earlier logs and the report retain
their dated 27-test snapshot; the latest suite has 28 tests (the original
18 October suite had 16).
