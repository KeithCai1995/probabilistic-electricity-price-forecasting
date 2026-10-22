# Project history

The project was placed under version control on 22 September 2026; imported
material predates that Git history. The original statement is preserved at
[historical/v102/PROJECT_HISTORY.md](historical/v102/PROJECT_HISTORY.md).

## Version timeline

- **v1.0.2:** earlier reference material and reproduction records, retained under
  `historical/v102/` and `evidence/`. Old paths in the frozen evidence index
  refer to that layout; old `experiments/` and `outputs/` are now under
  `historical/v102/`.
- **18 October 2026:** v1.1.0 corrects conformal calibration and adds regression
  tests, corrected reference runs and simulation-seed checks.
- **19 October 2026:** a personal rerun completed 16 tests and the default
  baseline, matching the reference metrics. Its local logs are kept separately
  under `Personal_Logs/20261019_080009/`, outside this repository.
- **21 October 2026:** configuration-aware rolling quantiles and plot targets,
  output-directory safeguards, future-information regressions, a real-model
  nondefault pipeline smoke and a lightweight CI workflow were added. A fresh
  complete default run reproduced all six baseline CSVs byte-for-byte. The
  supplementary gamma=0 control uses the same reconstructed raw forecasts and
  30-score buffers for all three existing baseline seeds. Feedback narrowed
  intervals but slightly worsened interval score in each seed; no standalone
  feedback advantage is claimed. New outputs are under
  `corrected_v110/supplementary_20261021/`; prior evidence and P2 input are unchanged.
  The active PDF filename is `report/Haorui_Cai_Forecasting_Report_v110.pdf`.

- **21 October 2026 - presentation follow-up:** redacted local workspace prefixes
  with an explicit `<WORKSPACE>` placeholder, without changing recorded dates,
  hashes or numerical results. Expanded the rolling-coverage axis, added a live
  plot regression (28 tests in total), and redrew five current charts from saved
  forecasts without refitting. See `PRESENTATION_UPDATE_20261021.md`.

## Sources

Initial code and reference analyses were supplied. Method sources are credited in
[RELATED_WORK.md](RELATED_WORK.md); execution details remain in the dated records.

Presentation and source-note wording was cleaned on 19 October 2026. Numerical
data, configurations and figures were retained; pre-cleanup copies are stored
separately outside this repository.
