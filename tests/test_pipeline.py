from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from energy_forecasting.conformal import adaptive_cqr, finite_sample_quantile, groupwise_static_cqr
from energy_forecasting.data import build_day_ahead_examples, chronological_split, simulate_hourly_market
from energy_forecasting.models import FEATURE_COLUMNS


class TestDataPipeline(unittest.TestCase):
    def test_features_are_complete_and_time_ordered(self) -> None:
        hourly = simulate_hourly_market(n_days=60, seed=7)
        examples = build_day_ahead_examples(hourly)
        self.assertFalse(examples.isna().any().any())
        splits = chronological_split(examples, 0.6, 0.2)
        self.assertLess(splits.train["target_time"].max(), splits.calibration["target_time"].min())
        self.assertLess(splits.calibration["target_time"].max(), splits.test["target_time"].min())

    def test_finite_sample_quantile_is_monotone(self) -> None:
        scores = np.arange(20, dtype=float)
        self.assertGreaterEqual(finite_sample_quantile(scores, 0.1), finite_sample_quantile(scores, 0.2))

    def test_model_features_exclude_targets_and_realised_future_values(self) -> None:
        forbidden = {
            "price_eur_mwh",
            "regime",
            "availability",
            "price_spike_flag",
            "load_actual_mw",
            "renewable_actual_mw",
            "temperature_actual_c",
            "target_time",
        }
        self.assertTrue(forbidden.isdisjoint(FEATURE_COLUMNS))

    def test_leading_missing_history_is_rejected(self) -> None:
        hourly = simulate_hourly_market(n_days=20, seed=7)
        hourly.loc[0, "price_observed_eur_mwh"] = np.nan
        hourly.loc[0, "data_missing_flag"] = 1
        with self.assertRaises(ValueError):
            build_day_ahead_examples(hourly)

    def test_adaptive_interval_does_not_use_its_own_outcome(self) -> None:
        calibration = pd.DataFrame(
            {
                "target_time": pd.date_range("2025-01-01", periods=30, freq="D"),
                "horizon": 1,
                "y": np.linspace(0, 1, 30),
                "lo": np.linspace(-0.2, 0.8, 30),
                "hi": np.linspace(0.2, 1.2, 30),
            }
        )
        test = pd.DataFrame(
            {
                "target_time": pd.date_range("2025-02-01", periods=5, freq="D"),
                "horizon": 1,
                "y": [0.2, 0.3, 0.4, 0.5, 0.6],
                "lo": [0.0] * 5,
                "hi": [0.4] * 5,
            }
        )
        first = adaptive_cqr(calibration, test, "lo", "hi", "y", "horizon", 0.2, 0.01, 20)
        changed = test.copy()
        changed.loc[0, "y"] = 1000.0
        second = adaptive_cqr(calibration, changed, "lo", "hi", "y", "horizon", 0.2, 0.01, 20)
        self.assertAlmostEqual(first[0][0], second[0][0])
        self.assertAlmostEqual(first[1][0], second[1][0])

    def test_groupwise_static_calibration_keeps_horizons_separate(self) -> None:
        calibration = pd.DataFrame(
            {
                "horizon": [1, 1, 1, 2, 2, 2],
                "y": [3.0, 3.0, 3.0, 10.0, 10.0, 10.0],
                "lo": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "hi": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )
        test = pd.DataFrame(
            {
                "horizon": [1, 2],
                "y": [0.0, 10.0],
                "lo": [0.0, 0.0],
                "hi": [1.0, 1.0],
            }
        )
        lower, upper, qhats = groupwise_static_cqr(
            calibration, test, "lo", "hi", "y", "horizon", 0.2
        )
        self.assertNotEqual(qhats[1], qhats[2])
        self.assertAlmostEqual(lower[0], -2.0)
        self.assertAlmostEqual(upper[1], 10.0)


if __name__ == "__main__":
    unittest.main()
