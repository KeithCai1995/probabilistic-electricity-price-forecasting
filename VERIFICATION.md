# Checks and reproducibility

The current test suite has 28 tests. It covers the conformal rank calculation,
infinite bounds, time ordering, configuration changes, plot axes and output paths.
The pipeline smoke test fits small models rather than replacing them with mocks.

Two scripts check the saved results without fitting models or changing files:

- `scripts/check_saved_outputs.py` recalculates the interval metrics for five
  reference runs and checks forecast ordering and timestamps.
- `scripts/check_rolling_control.py` replays the fixed-alpha and adaptive wrappers
  for the three saved seeds and compares their interval paths and metrics.

Commands are in the [README](README.md#reproduce-a-new-run).

## Published checks

The [22 October main run](https://github.com/KeithCai1995/probabilistic-electricity-price-forecasting/actions/runs/39736418760)
passed all four jobs for commit `c1ad5d7`: Ubuntu and Windows with Python 3.11 and
3.13. The workflow runs the tests and both saved-result checks. That result belongs
to the linked commit; later changes have their own workflow results.

## Earlier runs

[REPRODUCIBILITY_RECORD.md](REPRODUCIBILITY_RECORD.md) and
[the release summary](NEW_RELEASE_SUMMARY.md) retain the earlier run details.
The original reference suite had 16 tests, the 21 October update had 27, and the
rolling-coverage regression brought the count to 28. The report keeps its dated
27-test description.

The full baseline rerun matched all six saved CSVs byte-for-byte, including the
forecast export used by P2. Reference logs are in `corrected_v110/logs/`; the
fixed-alpha study is in `corrected_v110/supplementary_20261021/`.
