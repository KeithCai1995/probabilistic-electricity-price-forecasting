"""Supplementary fixed-alpha rolling control using shared raw forecasts.

Reconstruct the original model's calibration/test frames once per preserved seed,
check the raw test forecasts and adaptive intervals against their saved reference,
then compare gamma=0 with the original gamma using identical horizon score buffers.
No preserved reference file is modified and no new model tuning is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_forecasting.conformal import adaptive_cqr, groupwise_static_cqr, static_cqr
from energy_forecasting.data import dataframe_fingerprint
from energy_forecasting.experiment import fit_forecast_frames
from energy_forecasting.metrics import interval_metrics
from energy_forecasting.models import quantile_column
from energy_forecasting.output import prepare_output_root


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = sorted(list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tests").glob("*.py")))
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths}


def run_control(reference_root: Path, output_root: Path, seeds: list[int], *, overwrite: bool = False) -> pd.DataFrame:
    if len(set(seeds)) != len(seeds) or not seeds:
        raise ValueError("Provide a nonempty list of distinct preserved baseline seeds")
    references = {}
    for seed in seeds:
        name = "baseline" if seed == 20260817 else f"seed_{seed}"
        directory = reference_root / name / "outputs"
        manifest_path = directory / "run_manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"No preserved baseline reference for seed {seed}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if int(manifest["seed"]) != seed or float(manifest["config"]["calibration"]["adaptive_gamma"]) != .015:
            raise ValueError("The supplementary study only accepts original, untuned gamma=.015 baseline references")
        references[seed] = (name, directory, manifest)
    output_root = prepare_output_root(output_root, overwrite=overwrite)
    started = datetime.now(timezone.utc).isoformat()
    rows, subset_rows, audits = [], [], {}
    for seed, (name, directory, manifest) in references.items():
        print(f"START seed {seed}: reconstruct original full baseline model once", flush=True)
        config = manifest["config"]
        hourly, splits, calibration, test = fit_forecast_frames(config)
        saved = pd.read_csv(directory / "forecast_quantiles_test.csv", float_precision="round_trip")
        quantiles = [quantile_column(float(q)) for q in config["model"]["quantiles"]]
        if dataframe_fingerprint(hourly) != manifest["data_fingerprint"]:
            raise AssertionError("Reconstructed simulator does not match preserved fingerprint")
        for column in ("issue_time", "target_time"):
            np.testing.assert_array_equal(pd.to_datetime(test[column], utc=True), pd.to_datetime(saved[column], utc=True))
        np.testing.assert_array_equal(test["horizon"], saved["horizon"])
        np.testing.assert_allclose(test[quantiles + ["price_eur_mwh"]].to_numpy(), saved[quantiles + ["price_eur_mwh"]].to_numpy(),
                                   rtol=0, atol=1e-10, err_msg="Raw model forecasts changed; do not compare calibration wrappers")
        raw_difference = float(np.max(np.abs(test[quantiles].to_numpy() - saved[quantiles].to_numpy())))
        lower_col = quantile_column(float(config["calibration"]["lower_quantile"]))
        upper_col = quantile_column(float(config["calibration"]["upper_quantile"]))
        alpha = float(config["calibration"]["target_miscoverage"])
        window = int(config["calibration"]["adaptive_window_per_horizon"])
        gamma = float(config["calibration"]["adaptive_gamma"])
        pooled_lo, pooled_hi, _ = static_cqr(calibration["price_eur_mwh"].to_numpy(),
            calibration[lower_col].to_numpy(), calibration[upper_col].to_numpy(),
            test[lower_col].to_numpy(), test[upper_col].to_numpy(), alpha)
        horizon_lo, horizon_hi, _ = groupwise_static_cqr(calibration, test, lower_col, upper_col, "price_eur_mwh", "horizon", alpha)
        fixed_lo, fixed_hi, fixed_alpha, fixed_qhat = adaptive_cqr(calibration, test, lower_col, upper_col,
            "price_eur_mwh", "horizon", alpha, 0.0, window)
        adaptive_lo, adaptive_hi, adaptive_alpha, adaptive_qhat = adaptive_cqr(calibration, test, lower_col, upper_col,
            "price_eur_mwh", "horizon", alpha, gamma, window)
        np.testing.assert_array_equal(fixed_alpha, alpha)
        np.testing.assert_allclose(adaptive_lo, saved["adaptive_lower"], rtol=0, atol=1e-10)
        np.testing.assert_allclose(adaptive_hi, saved["adaptive_upper"], rtol=0, atol=1e-10)
        intervals = {
            "Raw quantiles": (test[lower_col].to_numpy(), test[upper_col].to_numpy()),
            "Static CQR (pooled)": (pooled_lo, pooled_hi),
            "Static CQR (by horizon)": (horizon_lo, horizon_hi),
            "Rolling CQR (fixed alpha)": (fixed_lo, fixed_hi),
            "Adaptive CQR": (adaptive_lo, adaptive_hi),
        }
        y = test["price_eur_mwh"].to_numpy()
        low_cut, high_cut = np.quantile(y, [float(config["evaluation"]["extreme_fraction"]), 1.0 - float(config["evaluation"]["extreme_fraction"])])
        subsets = {"All": np.ones(len(y), dtype=bool), "Price extremes (retrospective)": (y <= low_cut) | (y >= high_cut)}
        for method, (lower, upper) in intervals.items():
            rows.append({"run": name, "seed": seed, "method": method, "target_coverage": 1-alpha,
                         "n": len(y), **interval_metrics(y, lower, upper, alpha)})
            for subset, mask in subsets.items():
                subset_rows.append({"run": name, "seed": seed, "subset": subset, "method": method,
                                    "n": int(mask.sum()), **interval_metrics(y[mask], lower[mask], upper[mask], alpha)})
        run_root = output_root / name
        run_root.mkdir(parents=True, exist_ok=True)
        (run_root / "executed_config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        raw_columns = ["issue_time", "target_time", "horizon", "regime", "price_eur_mwh", *quantiles]
        calibration[raw_columns].to_csv(run_root / "calibration_raw_forecasts.csv", index=False)
        test[raw_columns].to_csv(run_root / "test_raw_forecasts.csv", index=False)
        output = test[["issue_time", "target_time", "horizon", "price_eur_mwh"]].copy()
        output["fixed_lower"], output["fixed_upper"] = fixed_lo, fixed_hi
        output["fixed_alpha"], output["fixed_qhat"] = fixed_alpha, fixed_qhat
        output["adaptive_lower"], output["adaptive_upper"] = adaptive_lo, adaptive_hi
        output["adaptive_alpha"], output["adaptive_qhat"] = adaptive_alpha, adaptive_qhat
        output.to_csv(run_root / "rolling_control_intervals.csv", index=False)
        audits[name] = {
            "seed": seed, "n_calibration": len(calibration), "n_test": len(test), "window_per_horizon": window,
            "fixed_gamma": 0.0, "adaptive_gamma": gamma,
            "same_raw_predictions_and_initial_score_buffer": True,
            "max_raw_quantile_difference_against_saved": raw_difference,
            "raw_quantiles_bitwise_match_saved": bool(np.array_equal(test[quantiles].to_numpy(), saved[quantiles].to_numpy())),
            "max_adaptive_bound_difference_against_saved": float(max(np.max(np.abs(adaptive_lo-saved["adaptive_lower"])), np.max(np.abs(adaptive_hi-saved["adaptive_upper"])))),
            "data_fingerprint": dataframe_fingerprint(hourly),
            "reference_forecast_sha256": sha256(directory / "forecast_quantiles_test.csv"),
            "reference_manifest_sha256": sha256(directory / "run_manifest.json"),
            "split_issue_days": {key: int(getattr(splits, key)["issue_day"].nunique()) for key in ["train", "calibration", "test"]},
            "output_sha256": {path.name: sha256(path) for path in sorted(run_root.iterdir()) if path.is_file()},
        }
        print(f"PASS seed {seed}: saved raw/adaptive match; fixed and adaptive share window={window}", flush=True)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(output_root / "comparison_metrics.csv", index=False)
    pd.DataFrame(subset_rows).to_csv(output_root / "subset_metrics.csv", index=False)
    paired = []
    for seed in seeds:
        frame = comparison.loc[comparison["seed"].eq(seed)].set_index("method")
        fields = ["coverage", "mean_width", "interval_score", "unbounded_fraction"]
        paired.append({"seed": seed, **{f"adaptive_minus_fixed_{field}": float(frame.loc["Adaptive CQR", field] - frame.loc["Rolling CQR (fixed alpha)", field]) for field in fields}})
    pd.DataFrame(paired).to_csv(output_root / "adaptive_minus_fixed.csv", index=False)
    audit = {
        "study": "Fixed-alpha rolling-window control", "study_date": "2026-10-21", "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed supplementary experiment, not a replacement of 2026-10-18 reference evidence",
        "design": "Same reconstructed baseline models, raw calibration/test quantiles, horizon groups and score buffers; only gamma=0 versus .015 changes.",
        "scope": "Simulated final blocks from three existing seeds; no retuning, no independent test-set claim, no coverage theorem or joint calibration claim.",
        "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"), "source_sha256": source_hashes(), "runs": audits,
    }
    (output_root / "study_manifest.json").write_text(json.dumps(audit, indent=2, allow_nan=False), encoding="utf-8")
    print(comparison.to_string(index=False), flush=True)
    print(f"Supplementary outputs: {output_root.resolve()}", flush=True)
    return comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, default=ROOT / "corrected_v110")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20260817, 20260818, 20260819])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    run_control(args.reference_root, args.output_root, args.seeds, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
