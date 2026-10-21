# Reproduction record — corrected v1.1.0

Reference experiment date: 2026-10-18. The earlier reproduction record is at
`historical/v102/REPRODUCIBILITY_RECORD.md`; earlier run logs remain
under `evidence/` and describe v1.0.2 only.

The preservation baseline is the uploaded v1.0.2 archive's extracted snapshot at
`work/pv18/p1`, not the separately maintained Desktop working repository. The
2026-10-18 validation matched 73 historical/evidence files before later wording
cleanup. Current checks cover retained numerical artifacts and machine records;
edited documentation and report presentation are excluded from byte-identity claims.
Pre-cleanup copies are stored separately outside this repository. Some Desktop evidence
uses CRLF rather than the uploaded snapshot's LF line endings; no Desktop-byte
identity is asserted. Desktop was used only as the read-only interpreter location.

The original Windows Python environment was used read-only, with bytecode disabled,
`PYTHONPATH` set to this revision's `src`, a workspace-local matplotlib cache and
`OMP_NUM_THREADS=2`. Scripts also prepend their own checkout's `src`. Actual import
location, interpreter and package versions are recorded in release verification.
No dependency was installed into the original environment.

The 18 October reference suite passed 16 tests. Evidence: `corrected_v110/logs/unit_tests.txt`.
It includes exact rank/index cases, ties, invalid alpha/scores, empty/non-vector
scores, unattainable ranks, decimal boundaries and adjacent alphas, adaptive
infinite-bound propagation, infinite metrics, conditional diagnostics, the
historical chart clipping case, temporal separation and feature/outcome checks.

| Run | Config | Seed |
| --- | --- | ---: |
| `corrected_v110/baseline` | `configs/base.yaml` | 20260817 |
| `corrected_v110/gamma_030` | `configs/gamma_030.yaml` | 20260817 |
| `corrected_v110/gamma_050` | `configs/gamma_sensitivity.yaml` | 20260817 |
| `corrected_v110/seed_20260818` | saved `executed_config.yaml` | 20260818 |
| `corrected_v110/seed_20260819` | saved `executed_config.yaml` | 20260819 |

Every run uses 420 days, seven quantile models with 140 boosting iterations,
247/82/83 issue-day splits, 30 scores per adaptive horizon and three rolling folds.
Only the indicated gamma or seed differs. Each exports data, forecasts, four tables,
six figures and a manifest. Logs use the run's name under `corrected_v110/logs/`.
README gives reproduction commands writing separate `local_runs/` paths.

The baseline data fingerprint equals preserved Windows v1.0.2:
`6d446b5560d6427574969caeb1b861aaebca30923fefa6093931b7700907e495`.
The raw seven forecast quantiles match exactly. Thus the within-Windows change in
calibration metrics is attributable to the correction rather than a new simulation
or retrained raw forecast difference. The supplied older Python 3.12 reference
had different raw forecasts and remains a separate historical comparator.

The baseline downstream forecast has 1,992 rows. Its SHA256 and all release
summary tables are recorded by `scripts/summarize_release.py`. The current metadata
verification is dated separately from the reference experiments and does not
represent a new model run. A SHA match audits
these local bytes; it does not establish scientific validity.

## Technical update — 21 October 2026

The expanded local suite passes 27 tests, adding nondefault configuration/plot
checks, a real-model complete small pipeline smoke, future-price and future-y
perturbations, a gamma=0 rolling-buffer check, and output-directory safeguards.
The new lightweight CI workflow is configured, not represented as an already
completed GitHub run. Read-only `scripts/check_saved_outputs.py` checks all five
preserved reference runs; `scripts/check_rolling_control.py` replays the new
controls from shared saved raw calibration and test frames without model fitting.

A complete fresh default run, including all rolling folds and six figures,
reproduced the reference simulated data, forecast CSV and four metric tables
byte-for-byte. The forecast SHA256 remains
`6901c84f413ba1375fd8096c3c4910c2346d479a7ff18274832c2d27aba8472b`.
Local verification logs and fresh outputs are kept in ignored
`local_runs/verification_20261021/`; the original reference files were not replaced.

The independently dated supplementary fixed-alpha study is at
`corrected_v110/supplementary_20261021/`. All three reconstructed raw forecast sets
and original adaptive bounds matched their preserved references exactly before
comparison. Its results, inputs and source hashes belong to that supplementary
execution, not the historical reference logs. Existing dated source-hash records
are retained as execution snapshots rather than silently refreshed to later code.
