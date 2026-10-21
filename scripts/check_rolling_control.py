"""Replay the saved supplementary rolling controls without fitting or writing files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_forecasting.conformal import adaptive_cqr
from energy_forecasting.metrics import interval_metrics
from energy_forecasting.models import quantile_column


def main() -> None:
    study = ROOT / "corrected_v110/supplementary_20261021"
    manifest = json.loads((study / "study_manifest.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(study / "comparison_metrics.csv", float_precision="round_trip")
    for name, audit in manifest["runs"].items():
        run_root = study / name
        for filename, expected in audit["output_sha256"].items():
            actual = hashlib.sha256((run_root / filename).read_bytes()).hexdigest()
            assert actual == expected, (name, filename, "hash")
        reference = ROOT / "corrected_v110" / name / "outputs/forecast_quantiles_test.csv"
        assert hashlib.sha256(reference.read_bytes()).hexdigest() == audit["reference_forecast_sha256"], name
        config = yaml.safe_load((run_root / "executed_config.yaml").read_text(encoding="utf-8"))
        calibration = pd.read_csv(run_root / "calibration_raw_forecasts.csv", float_precision="round_trip")
        test = pd.read_csv(run_root / "test_raw_forecasts.csv", float_precision="round_trip")
        saved = pd.read_csv(run_root / "rolling_control_intervals.csv", float_precision="round_trip")
        lower_col = quantile_column(config["calibration"]["lower_quantile"])
        upper_col = quantile_column(config["calibration"]["upper_quantile"])
        alpha = float(config["calibration"]["target_miscoverage"])
        window = int(config["calibration"]["adaptive_window_per_horizon"])
        for prefix, gamma, method in [("fixed", 0.0, "Rolling CQR (fixed alpha)"),
            ("adaptive", float(config["calibration"]["adaptive_gamma"]), "Adaptive CQR")]:
            values = adaptive_cqr(calibration, test, lower_col, upper_col, "price_eur_mwh", "horizon", alpha, gamma, window)
            for field, measured in zip(["lower", "upper", "alpha", "qhat"], values):
                np.testing.assert_allclose(measured, saved[f"{prefix}_{field}"], rtol=0, atol=1e-10, err_msg=f"{name}/{prefix}/{field}")
            metrics = interval_metrics(test["price_eur_mwh"].to_numpy(), values[0], values[1], alpha)
            reported = summary.loc[summary["run"].eq(name) & summary["method"].eq(method)].iloc[0]
            for field, measured in metrics.items():
                np.testing.assert_allclose(measured, float(reported[field]), rtol=0, atol=1e-10, equal_nan=True)
        print(f"PASS {name}: saved raw frames replay both rolling wrappers and their metrics")
    print("3/3 supplementary replays passed. No model fitted and no files written.")


if __name__ == "__main__":
    main()
