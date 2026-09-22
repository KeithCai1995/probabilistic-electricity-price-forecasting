from __future__ import annotations

import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
import yaml

from .conformal import adaptive_cqr, groupwise_static_cqr, static_cqr
from .data import build_day_ahead_examples, chronological_split, dataframe_fingerprint, simulate_hourly_market
from .metrics import approximate_crps, interval_metrics, pinball_loss, rolling_coverage
from .models import QuantileEnsemble, ood_score, quantile_column


COLORS = {
    "navy": "#17324D",
    "blue": "#2F6B9A",
    "teal": "#2A9D8F",
    "gold": "#E9A23B",
    "red": "#C54B4B",
    "gray": "#6B7280",
}


def _configure_plotting() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 220,
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def run(config_path: str | Path, root: str | Path) -> dict:
    root = Path(root)
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    for folder in [root / "outputs" / "figures", root / "outputs" / "tables", root / "data"]:
        folder.mkdir(parents=True, exist_ok=True)
    _configure_plotting()

    hourly = simulate_hourly_market(
        n_days=int(config["data"]["n_days"]),
        start=config["data"]["start"],
        timezone=config["data"]["timezone"],
        seed=int(config["seed"]),
    )
    examples = build_day_ahead_examples(hourly)
    splits = chronological_split(
        examples,
        float(config["split"]["train_fraction"]),
        float(config["split"]["calibration_fraction"]),
    )

    model_config = config["model"]
    quantiles = [float(q) for q in model_config["quantiles"]]
    model = QuantileEnsemble(
        quantiles=quantiles,
        backend=model_config["backend"],
        params={k: v for k, v in model_config.items() if k not in {"backend", "quantiles"}},
        seed=int(config["seed"]),
    ).fit(splits.train)
    pred_cal = model.predict(splits.calibration)
    pred_test = model.predict(splits.test)

    calibration = pd.concat([splits.calibration.reset_index(drop=True), pred_cal.reset_index(drop=True)], axis=1)
    test = pd.concat([splits.test.reset_index(drop=True), pred_test.reset_index(drop=True)], axis=1)
    lower_col = quantile_column(float(config["calibration"]["lower_quantile"]))
    upper_col = quantile_column(float(config["calibration"]["upper_quantile"]))
    alpha = float(config["calibration"]["target_miscoverage"])

    static_low, static_high, static_qhat = static_cqr(
        calibration["price_eur_mwh"].to_numpy(),
        calibration[lower_col].to_numpy(),
        calibration[upper_col].to_numpy(),
        test[lower_col].to_numpy(),
        test[upper_col].to_numpy(),
        alpha,
    )
    test["static_lower"] = static_low
    test["static_upper"] = static_high

    horizon_static_low, horizon_static_high, horizon_static_qhats = groupwise_static_cqr(
        calibration,
        test,
        lower_col,
        upper_col,
        "price_eur_mwh",
        "horizon",
        alpha,
    )
    test["horizon_static_lower"] = horizon_static_low
    test["horizon_static_upper"] = horizon_static_high

    adaptive_input_cal = calibration.copy()
    adaptive_input_test = test.copy()
    adaptive_low, adaptive_high, alpha_path, qhat_path = adaptive_cqr(
        adaptive_input_cal,
        adaptive_input_test,
        lower_col,
        upper_col,
        "price_eur_mwh",
        "horizon",
        alpha,
        float(config["calibration"]["adaptive_gamma"]),
        int(config["calibration"]["adaptive_window_per_horizon"]),
    )
    test["adaptive_lower"] = adaptive_low
    test["adaptive_upper"] = adaptive_high
    test["adaptive_alpha"] = alpha_path
    test["adaptive_qhat"] = qhat_path
    scores, ood_threshold = ood_score(splits.train, test)
    test["ood_score"] = scores
    test["ood_flag"] = scores > ood_threshold

    test["seasonal_naive"] = test["price_lag24"]
    target = test["price_eur_mwh"].to_numpy()
    median = test[quantile_column(0.5)].to_numpy()
    base_metrics = {
        "seasonal_naive_mae": float(np.mean(np.abs(target - test["seasonal_naive"].to_numpy()))),
        "quantile_model_mae": float(np.mean(np.abs(target - median))),
        "mean_pinball": float(np.mean([pinball_loss(target, test[quantile_column(q)].to_numpy(), q) for q in quantiles])),
        "approx_crps": approximate_crps(target, test, quantiles),
    }

    interval_methods = {
        "Raw quantiles": (test[lower_col].to_numpy(), test[upper_col].to_numpy()),
        "Static CQR (pooled)": (test["static_lower"].to_numpy(), test["static_upper"].to_numpy()),
        "Static CQR (by horizon)": (
            test["horizon_static_lower"].to_numpy(),
            test["horizon_static_upper"].to_numpy(),
        ),
        "Adaptive CQR": (test["adaptive_lower"].to_numpy(), test["adaptive_upper"].to_numpy()),
    }
    summary_rows = []
    for method, (low, high) in interval_methods.items():
        row = {"method": method, **interval_metrics(target, low, high, alpha), **base_metrics}
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(root / "outputs" / "tables" / "overall_metrics.csv", index=False)

    extreme_fraction = float(config["evaluation"]["extreme_fraction"])
    low_cut, high_cut = np.quantile(target, [extreme_fraction, 1.0 - extreme_fraction])
    subsets = {
        "All": np.ones(len(test), dtype=bool),
        "Price extremes": (target <= low_cut) | (target >= high_cut),
        "Volatile regime": test["regime"].eq("volatile").to_numpy(),
        "Renewable shift": test["regime"].eq("renewable_shift").to_numpy(),
        "OOD flag": test["ood_flag"].to_numpy(),
    }
    subset_rows = []
    for subset_name, mask in subsets.items():
        if not np.any(mask):
            continue
        for method, (low, high) in interval_methods.items():
            metrics = interval_metrics(target[mask], low[mask], high[mask], alpha)
            subset_rows.append({"subset": subset_name, "method": method, "n": int(mask.sum()), **metrics})
    subset = pd.DataFrame(subset_rows)
    subset.to_csv(root / "outputs" / "tables" / "subset_metrics.csv", index=False)

    reliability_rows = []
    for q in quantiles:
        reliability_rows.append(
            {
                "nominal_quantile": q,
                "empirical_frequency": float(np.mean(target <= test[quantile_column(q)].to_numpy())),
            }
        )
    reliability = pd.DataFrame(reliability_rows)
    reliability.to_csv(root / "outputs" / "tables" / "quantile_reliability.csv", index=False)

    rolling_origin = _rolling_origin_backtest(examples, config)
    rolling_origin.to_csv(root / "outputs" / "tables" / "rolling_origin_metrics.csv", index=False)

    export_columns = [
        "issue_time", "target_time", "issue_day", "horizon", "regime", "price_eur_mwh",
        "seasonal_naive", *[quantile_column(q) for q in quantiles],
        "static_lower", "static_upper", "horizon_static_lower", "horizon_static_upper",
        "adaptive_lower", "adaptive_upper",
        "adaptive_alpha", "adaptive_qhat", "ood_score", "ood_flag",
    ]
    test[export_columns].to_csv(root / "outputs" / "forecast_quantiles_test.csv", index=False)
    hourly.to_csv(root / "data" / "simulated_hourly_market.csv", index=False)

    _plot_forecast_window(test, root / "outputs" / "figures" / "figure_1_forecast_window.png")
    _plot_coverage_width(summary, root / "outputs" / "figures" / "figure_2_coverage_width.png")
    _plot_rolling_coverage(test, int(config["evaluation"]["rolling_coverage_window_hours"]), root / "outputs" / "figures" / "figure_3_rolling_coverage.png")
    _plot_reliability(reliability, root / "outputs" / "figures" / "figure_4_quantile_reliability.png")
    _plot_subset_coverage(subset, root / "outputs" / "figures" / "figure_5_subset_coverage.png")
    _plot_ood(test, root / "outputs" / "figures" / "figure_6_ood_diagnostic.png")

    manifest = {
        "project": "P1_forecasting_under_regime_shift",
        "data_status": "simulated_benchmark_not_field_data",
        "claim_boundary": "Research-training portfolio; not a live-market or employer result.",
        "seed": int(config["seed"]),
        "data_fingerprint": dataframe_fingerprint(hourly),
        "n_hourly_rows": int(len(hourly)),
        "n_examples": int(len(examples)),
        "split_issue_days": {
            "train": int(splits.train["issue_day"].nunique()),
            "calibration": int(splits.calibration["issue_day"].nunique()),
            "test": int(splits.test["issue_day"].nunique()),
        },
        "static_qhat": static_qhat,
        "horizon_static_qhats": horizon_static_qhats,
        "ood_threshold": ood_threshold,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "config": config,
    }
    (root / "outputs" / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "summary": summary,
        "subset": subset,
        "reliability": reliability,
        "rolling_origin": rolling_origin,
        "manifest": manifest,
    }


def _rolling_origin_backtest(examples: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Expanding-window diagnostic with a nested, past-only calibration block."""

    days = np.sort(examples["issue_day"].unique())
    n_folds = int(config["evaluation"]["rolling_origin_folds"])
    test_days = int(config["evaluation"]["rolling_origin_test_days"])
    last_origin = int(len(days) * 0.76) - test_days
    first_origin = int(len(days) * 0.46)
    origins = np.linspace(first_origin, last_origin, n_folds, dtype=int)
    rows: list[dict[str, float | int | str]] = []
    model_config = config["model"]
    alpha = float(config["calibration"]["target_miscoverage"])

    for fold, origin in enumerate(origins, start=1):
        train_days = days[:origin]
        test_fold_days = days[origin : origin + test_days]
        calibration_days = train_days[-42:]
        fit_days = train_days[:-42]
        fit_frame = examples[examples["issue_day"].isin(fit_days)].reset_index(drop=True)
        calibration_frame = examples[examples["issue_day"].isin(calibration_days)].reset_index(drop=True)
        test_frame = examples[examples["issue_day"].isin(test_fold_days)].reset_index(drop=True)
        fold_model = QuantileEnsemble(
            quantiles=[0.10, 0.50, 0.90],
            backend=model_config["backend"],
            params={k: v for k, v in model_config.items() if k not in {"backend", "quantiles"}},
            seed=int(config["seed"]) + fold,
        ).fit(fit_frame)
        calibration_pred = fold_model.predict(calibration_frame)
        test_pred = fold_model.predict(test_frame)
        pooled_low, pooled_high, _ = static_cqr(
            calibration_frame["price_eur_mwh"].to_numpy(),
            calibration_pred["q10"].to_numpy(),
            calibration_pred["q90"].to_numpy(),
            test_pred["q10"].to_numpy(),
            test_pred["q90"].to_numpy(),
            alpha,
        )

        calibration_eval = pd.concat(
            [calibration_frame.reset_index(drop=True), calibration_pred.reset_index(drop=True)],
            axis=1,
        )
        test_eval = pd.concat(
            [test_frame.reset_index(drop=True), test_pred.reset_index(drop=True)],
            axis=1,
        )
        horizon_low, horizon_high, _ = groupwise_static_cqr(
            calibration_eval,
            test_eval,
            "q10",
            "q90",
            "price_eur_mwh",
            "horizon",
            alpha,
        )
        adaptive_low, adaptive_high, _, _ = adaptive_cqr(
            calibration_eval,
            test_eval,
            "q10",
            "q90",
            "price_eur_mwh",
            "horizon",
            alpha,
            float(config["calibration"]["adaptive_gamma"]),
            int(config["calibration"]["adaptive_window_per_horizon"]),
        )

        y = test_frame["price_eur_mwh"].to_numpy()
        fold_intervals = {
            "Raw quantiles": (test_pred["q10"].to_numpy(), test_pred["q90"].to_numpy()),
            "Static CQR (pooled)": (pooled_low, pooled_high),
            "Static CQR (by horizon)": (horizon_low, horizon_high),
            "Adaptive CQR": (adaptive_low, adaptive_high),
        }
        for method, (low, high) in fold_intervals.items():
            rows.append(
                {
                    "fold": fold,
                    "method": method,
                    "train_end": str(pd.to_datetime(fit_frame["target_time"]).max()),
                    "test_start": str(pd.to_datetime(test_frame["target_time"]).min()),
                    "test_end": str(pd.to_datetime(test_frame["target_time"]).max()),
                    "n_test": int(len(test_frame)),
                    "median_mae": float(np.mean(np.abs(y - test_pred["q50"].to_numpy()))),
                    **interval_metrics(y, low, high, alpha),
                }
            )
    return pd.DataFrame(rows)


def _plot_forecast_window(test: pd.DataFrame, path: Path) -> None:
    frame = test.sort_values("target_time").iloc[: 14 * 24]
    x = pd.to_datetime(frame["target_time"]).dt.tz_localize(None)
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    ax.fill_between(x, frame["adaptive_lower"], frame["adaptive_upper"], color=COLORS["teal"], alpha=0.20, label="Adaptive 80% interval")
    ax.plot(x, frame["price_eur_mwh"], color=COLORS["navy"], lw=1.0, label="Realised price")
    ax.plot(x, frame["q50"], color=COLORS["gold"], lw=1.0, label="Median forecast")
    ax.set(title="Two-week out-of-sample forecast window", ylabel="EUR/MWh", xlabel="Target time")
    ax.legend(ncol=3, loc="upper left")
    _save_figure(fig, path)


def _plot_coverage_width(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    method_colors = {
        "Raw quantiles": COLORS["gray"],
        "Static CQR (pooled)": COLORS["blue"],
        "Static CQR (by horizon)": COLORS["gold"],
        "Adaptive CQR": COLORS["teal"],
    }
    for _, row in summary.iterrows():
        color = method_colors[row["method"]]
        ax.scatter(row["mean_width"], row["coverage"], s=90, color=color, label=row["method"])
    ax.axhline(0.80, color=COLORS["red"], ls="--", lw=1, label="80% target")
    ax.set(xlabel="Mean interval width (EUR/MWh)", ylabel="Empirical coverage", title="Reliability-sharpness trade-off")
    ax.set_ylim(0.55, 1.0)
    ax.legend()
    _save_figure(fig, path)


def _plot_rolling_coverage(test: pd.DataFrame, window: int, path: Path) -> None:
    frame = test.sort_values("target_time").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    for label, low, high, color in [
        ("Raw", "q10", "q90", COLORS["gray"]),
        ("Static pooled", "static_lower", "static_upper", COLORS["blue"]),
        ("Static by horizon", "horizon_static_lower", "horizon_static_upper", COLORS["gold"]),
        ("Adaptive CQR", "adaptive_lower", "adaptive_upper", COLORS["teal"]),
    ]:
        curve = rolling_coverage(frame["price_eur_mwh"], frame[low], frame[high], window)
        ax.plot(pd.to_datetime(frame["target_time"]).dt.tz_localize(None), curve, lw=1.1, label=label, color=color)
    ax.axhline(0.80, color=COLORS["red"], ls="--", lw=1)
    ax.set(title=f"Rolling empirical coverage ({window}-hour window)", ylabel="Coverage", xlabel="Target time", ylim=(0.45, 1.02))
    ax.legend(ncol=2)
    _save_figure(fig, path)


def _plot_reliability(reliability: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.plot([0, 1], [0, 1], color=COLORS["gray"], ls="--", lw=1)
    ax.plot(reliability["nominal_quantile"], reliability["empirical_frequency"], marker="o", color=COLORS["blue"])
    ax.set(xlabel="Nominal quantile", ylabel="Empirical frequency", title="Quantile reliability", xlim=(0, 1), ylim=(0, 1))
    _save_figure(fig, path)


def _plot_subset_coverage(subset: pd.DataFrame, path: Path) -> None:
    pivot = subset.pivot(index="subset", columns="method", values="coverage")
    method_order = [
        "Raw quantiles",
        "Static CQR (pooled)",
        "Static CQR (by horizon)",
        "Adaptive CQR",
    ]
    pivot = pivot[[method for method in method_order if method in pivot.columns]]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    pivot.plot(
        kind="bar",
        ax=ax,
        color=[COLORS["gray"], COLORS["blue"], COLORS["gold"], COLORS["teal"]],
    )
    ax.axhline(0.80, color=COLORS["red"], ls="--", lw=1)
    ax.set(title="Coverage by stress-test subset", ylabel="Coverage", xlabel="", ylim=(0, 1.02))
    ax.tick_params(axis="x", rotation=20)
    ax.legend(title="", loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8)
    _save_figure(fig, path)


def _plot_ood(test: pd.DataFrame, path: Path) -> None:
    absolute_error = np.abs(test["price_eur_mwh"] - test["q50"])
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.scatter(test["ood_score"], absolute_error, s=8, alpha=0.28, color=COLORS["blue"])
    ax.set(xlabel="Standardised feature-distance score", ylabel="Absolute median error (EUR/MWh)", title="Simple OOD diagnostic")
    _save_figure(fig, path)
