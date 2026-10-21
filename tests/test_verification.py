from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from energy_forecasting.conformal import adaptive_cqr, finite_sample_quantile
from energy_forecasting.data import build_day_ahead_examples, simulate_hourly_market
from energy_forecasting.experiment import (
    _plot_coverage_width, _plot_forecast_window, _plot_rolling_coverage,
    _plot_subset_coverage, _rolling_origin_backtest, run, validate_config,
)
from energy_forecasting.models import FEATURE_COLUMNS, QuantileEnsemble
from energy_forecasting.output import REPOSITORY_ROOT, prepare_output_root


LOCAL_RUNS = ROOT / "local_runs"


def smoke_config() -> dict:
    config = yaml.safe_load((ROOT / "configs/base.yaml").read_text(encoding="utf-8"))
    config["data"]["n_days"] = 80
    config["model"].update(quantiles=[0.05, 0.50, 0.95], max_iter=3, max_leaf_nodes=5)
    config["calibration"].update(lower_quantile=0.05, upper_quantile=0.95,
                                  target_miscoverage=0.10, adaptive_window_per_horizon=12)
    config["evaluation"].update(rolling_origin_folds=1, rolling_origin_test_days=3,
                                rolling_origin_calibration_days=12,
                                rolling_coverage_window_hours=12)
    return config


class TestTemporalRegression(unittest.TestCase):
    def test_future_price_perturbation_cannot_change_issuance_inputs(self) -> None:
        hourly = simulate_hourly_market(n_days=20, seed=7)
        examples = build_day_ahead_examples(hourly)
        changed = hourly.copy()
        changed.loc[10 * 24:, "price_observed_eur_mwh"] += 100000.0
        changed.loc[10 * 24:, "price_eur_mwh"] += 100000.0
        altered = build_day_ahead_examples(changed)
        before = examples.loc[examples["issue_day"].eq(10), FEATURE_COLUMNS]
        after = altered.loc[altered["issue_day"].eq(10), FEATURE_COLUMNS]
        np.testing.assert_array_equal(before.to_numpy(), after.to_numpy())

    def test_future_outcomes_leave_all_earlier_horizon_intervals_unchanged(self) -> None:
        calibration = pd.DataFrame({"horizon": np.tile([1, 2], 15), "y": np.arange(30) / 10,
                                    "lo": 0.0, "hi": 2.0})
        test = pd.DataFrame({"horizon": np.tile([1, 2], 4), "y": np.linspace(1, 3, 8),
                             "lo": 0.0, "hi": 2.0,
                             "target_time": pd.date_range("2025-03-01", periods=8, freq="12h")})
        first = adaptive_cqr(calibration, test, "lo", "hi", "y", "horizon", .2, .015, 12)
        changed = test.copy()
        changed.loc[4:, "y"] += 1000.0
        second = adaptive_cqr(calibration, changed, "lo", "hi", "y", "horizon", .2, .015, 12)
        for original, altered in zip(first, second):
            np.testing.assert_array_equal(original[:4], altered[:4])

    def test_gamma_zero_is_fixed_alpha_with_a_rolling_score_buffer(self) -> None:
        calibration = pd.DataFrame({"horizon": 1, "y": np.arange(6, dtype=float), "lo": 0.0, "hi": 1.0})
        test = pd.DataFrame({"horizon": 1, "y": [9.0, 1.0, 2.0], "lo": 0.0, "hi": 1.0,
                             "target_time": pd.date_range("2025-03-01", periods=3, freq="D")})
        lower, upper, alphas, qhats = adaptive_cqr(calibration, test, "lo", "hi", "y", "horizon", .25, 0.0, 4)
        scores = list(np.maximum(-calibration["y"], calibration["y"] - 1).to_numpy()[-4:])
        expected = []
        for y in test["y"]:
            expected.append(finite_sample_quantile(np.asarray(scores), .25))
            scores = (scores + [max(-y, y - 1)])[-4:]
        np.testing.assert_array_equal(alphas, .25)
        np.testing.assert_array_equal(qhats, expected)
        np.testing.assert_array_equal(lower, -np.asarray(expected))
        np.testing.assert_array_equal(upper, 1 + np.asarray(expected))


class TestConfigAndSmoke(unittest.TestCase):
    def test_nondefault_pipeline_really_fits_models_and_matches_plot_targets(self) -> None:
        LOCAL_RUNS.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p1_smoke_", dir=LOCAL_RUNS) as directory:
            base = Path(directory)
            config_path = base / "config.yaml"
            config_path.write_text(yaml.safe_dump(smoke_config()), encoding="utf-8")
            # Real simulation, feature pipeline, model fits, calibrators and all plots.
            result = run(config_path, base / "run")
            forecasts = pd.read_csv(base / "run/outputs/forecast_quantiles_test.csv")
            self.assertIn("q05", forecasts)
            self.assertIn("q95", forecasts)
            self.assertNotIn("q10", forecasts)
            self.assertEqual(len(result["rolling_origin"]), 4)
            self.assertEqual(len(list((base / "run/outputs/figures").glob("*.png"))), 6)
            manifest = json.loads((base / "run/outputs/run_manifest.json").read_text())
            self.assertEqual(manifest["config"]["calibration"]["target_miscoverage"], .1)
            self.assertTrue(np.isfinite(forecasts[["q05", "q50", "q95"]]).all().all())

    def test_rolling_fold_receives_configured_quantiles_and_alpha(self) -> None:
        config = smoke_config()
        examples = build_day_ahead_examples(simulate_hourly_market(n_days=80, seed=7))
        observed_grids = []
        original_init = QuantileEnsemble.__post_init__
        def observe_init(model):
            observed_grids.append(model.quantiles)
            original_init(model)
        with patch.object(QuantileEnsemble, "__post_init__", observe_init), patch(
            "energy_forecasting.experiment.static_cqr",
            wraps=__import__("energy_forecasting.conformal", fromlist=["static_cqr"]).static_cqr,
        ) as calibrator:
            result = _rolling_origin_backtest(examples, config)
        self.assertEqual(observed_grids, [[.05, .50, .95]])
        self.assertEqual(calibrator.call_args.args[-1], .10)
        self.assertEqual(len(result), 4)

    def test_all_interval_plot_labels_use_nondefault_coverage(self) -> None:
        frame = pd.DataFrame({"target_time": pd.date_range("2025-01-01", periods=30, freq="h"),
                              "price_eur_mwh": 1.0, "q50": 1.0, "q05": 0.0, "q95": 2.0,
                              "static_lower": 0.0, "static_upper": 2.0,
                              "horizon_static_lower": 0.0, "horizon_static_upper": 2.0,
                              "adaptive_lower": 0.0, "adaptive_upper": 2.0})
        summary = pd.DataFrame({"method": ["Raw quantiles"], "coverage": [.9], "mean_width": [2.]})
        subset = pd.DataFrame({"subset": ["All"], "method": ["Raw quantiles"], "coverage": [.9]})
        with patch("energy_forecasting.experiment._save_figure") as save:
            _plot_forecast_window(frame, Path("unused.png"), target_coverage=.9)
            figure = save.call_args.args[0]
            self.assertIn("Adaptive 90% interval", figure.axes[0].get_legend_handles_labels()[1])
            plt.close(figure)
            _plot_coverage_width(summary, Path("unused.png"), target_coverage=.9)
            figure = save.call_args.args[0]
            self.assertIn("90% target", figure.axes[0].get_legend_handles_labels()[1])
            self.assertEqual(float(figure.axes[0].lines[0].get_ydata()[0]), .9)
            plt.close(figure)
            _plot_rolling_coverage(frame, 12, Path("unused.png"), lower_col="q05", upper_col="q95", target_coverage=.9)
            figure = save.call_args.args[0]
            self.assertEqual(float(figure.axes[0].lines[-1].get_ydata()[0]), .9)
            plt.close(figure)
            _plot_subset_coverage(subset, Path("unused.png"), target_coverage=.9)
            figure = save.call_args.args[0]
            self.assertEqual(float(figure.axes[0].lines[-1].get_ydata()[0]), .9)
            plt.close(figure)

    def test_invalid_quantile_and_split_settings_fail_before_fitting(self) -> None:
        base = smoke_config()
        variants = []
        for grid in ([.5, .05, .95], [.05, .5, .5, .95], [.1, .5, .9], [.05, .101, .104, .5, .95]):
            config = copy.deepcopy(base)
            config["model"]["quantiles"] = grid
            variants.append(config)
        config = copy.deepcopy(base)
        config["split"] = {"train_fraction": .8, "calibration_fraction": .3}
        variants.append(config)
        for config in variants:
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_config(config)


class TestOutputSafety(unittest.TestCase):
    def test_nonempty_output_requires_explicit_overwrite_without_deleting_other_files(self) -> None:
        LOCAL_RUNS.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p1_safety_", dir=LOCAL_RUNS) as directory:
            target = Path(directory) / "run"
            prepare_output_root(target)
            sentinel = target / "keep.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prepare_output_root(target)
            self.assertEqual(prepare_output_root(target, overwrite=True), target.resolve())
            self.assertEqual(sentinel.read_text(), "preserve")

    def test_repository_sources_and_reference_outputs_are_always_protected(self) -> None:
        for path in (REPOSITORY_ROOT, REPOSITORY_ROOT.parent, REPOSITORY_ROOT / "src",
                     REPOSITORY_ROOT / "SRC",
                     REPOSITORY_ROOT / "corrected_v110/baseline", REPOSITORY_ROOT / "historical/v102",
                     REPOSITORY_ROOT / ".git/tmp"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare_output_root(path, overwrite=True)

    def test_overwrite_refuses_unrecognized_existing_directory(self) -> None:
        LOCAL_RUNS.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p1_safety_", dir=LOCAL_RUNS) as directory:
            target = Path(directory)
            sentinel = target / "unrelated.txt"
            sentinel.write_text("not a P1 run", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_output_root(target, overwrite=True)
            self.assertEqual(sentinel.read_text(), "not a P1 run")

    def test_run_and_seed_override_refuse_existing_output_before_model_execution(self) -> None:
        LOCAL_RUNS.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p1_safety_", dir=LOCAL_RUNS) as directory:
            target = Path(directory)
            (target / "sentinel.txt").write_text("untouched", encoding="utf-8")
            for seed in (None, 20260818):
                with self.subTest(seed=seed), patch("energy_forecasting.experiment.fit_forecast_frames") as fit:
                    with self.assertRaises(FileExistsError):
                        run(ROOT / "configs/base.yaml", target, seed_override=seed)
                    fit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
