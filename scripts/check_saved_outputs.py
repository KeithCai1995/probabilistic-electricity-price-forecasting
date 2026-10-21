"""Read-only consistency checks of preserved reference forecasts and metric tables."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_forecasting.metrics import interval_metrics


def main() -> None:
    runs = ["baseline", "gamma_030", "gamma_050", "seed_20260818", "seed_20260819"]
    quantiles = ["q05", "q10", "q25", "q50", "q75", "q90", "q95"]
    methods = {
        "Raw quantiles": ("q10", "q90"),
        "Static CQR (pooled)": ("static_lower", "static_upper"),
        "Static CQR (by horizon)": ("horizon_static_lower", "horizon_static_upper"),
        "Adaptive CQR": ("adaptive_lower", "adaptive_upper"),
    }
    for name in runs:
        output = ROOT / "corrected_v110" / name / "outputs"
        frame = pd.read_csv(output / "forecast_quantiles_test.csv", float_precision="round_trip")
        summary = pd.read_csv(output / "tables/overall_metrics.csv", float_precision="round_trip")
        assert len(frame) == 1992, name
        assert not frame.duplicated(["issue_time", "horizon"]).any(), name
        assert frame.groupby("issue_time")["horizon"].apply(lambda values: set(values) == set(range(1, 25))).all(), name
        assert np.isfinite(frame[quantiles]).all().all(), name
        assert (np.diff(frame[quantiles].to_numpy(), axis=1) >= 0.0).all(), name
        lead = (pd.to_datetime(frame["target_time"], utc=True) - pd.to_datetime(frame["issue_time"], utc=True)).dt.total_seconds() / 3600
        np.testing.assert_array_equal(lead, frame["horizon"] - 1)
        for method, (lower_col, upper_col) in methods.items():
            lower, upper = frame[lower_col].to_numpy(), frame[upper_col].to_numpy()
            assert (lower <= upper).all(), (name, method)
            measured = interval_metrics(frame["price_eur_mwh"].to_numpy(), lower, upper, .2)
            reported = summary.loc[summary["method"].eq(method)].iloc[0]
            for field, actual in measured.items():
                np.testing.assert_allclose(actual, float(reported[field]), rtol=1e-11, atol=1e-11, equal_nan=True,
                                           err_msg=f"{name}/{method}/{field}")
        print(f"PASS {name}: 1,992 forecasts; timing, ordering and all saved interval metrics")
    print("5/5 preserved reference checks passed. No files written; no model rerun.")


if __name__ == "__main__":
    main()
