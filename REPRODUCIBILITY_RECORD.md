# Reproduction record — corrected v1.1.0

Execution date: 2026-10-18. Operator: AI coding assistant in a local workspace.
The original record is preserved byte-for-byte at
`historical/v102/REPRODUCIBILITY_RECORD.md`; all original personal logs remain
under `evidence/` and describe v1.0.2 only.

The preservation baseline is the uploaded v1.0.2 archive's extracted snapshot at
`work/pv18/p1`, not the separately maintained Desktop working repository. Seventy-three
historical/evidence files match that snapshot byte-for-byte. Some Desktop evidence
uses CRLF rather than the uploaded snapshot's LF line endings; no Desktop-byte
identity is asserted. Desktop was used only as the read-only interpreter location.

The original Windows Python environment was used read-only, with bytecode disabled,
`PYTHONPATH` set to this revision's `src`, a workspace-local matplotlib cache and
`OMP_NUM_THREADS=2`. Scripts also prepend their own checkout's `src`. Actual import
location, interpreter and package versions are recorded in release verification.
No dependency was installed into the original environment.

The current suite passes 16 tests. Evidence: `corrected_v110/logs/unit_tests.txt`.
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
summary tables are recorded by `scripts/summarize_release.py`. A SHA match audits
these local bytes; it does not establish scientific validity.
