"""Audit and summarize the assistant-executed corrected release without rerunning models."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import energy_forecasting


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-root", type=Path, help="Optional read-only v1.0.2 source for preservation checks")
    args = parser.parse_args()
    release = ROOT / "corrected_v110"
    tables = release / "comparison_tables"
    tables.mkdir(parents=True, exist_ok=True)
    run_names = ["baseline", "gamma_030", "gamma_050", "seed_20260818", "seed_20260819"]
    metrics = []
    run_audits = {}
    quantiles = ["q05", "q10", "q25", "q50", "q75", "q90", "q95"]
    intervals = {
        "Raw quantiles": ("q10", "q90"),
        "Static CQR (pooled)": ("static_lower", "static_upper"),
        "Static CQR (by horizon)": ("horizon_static_lower", "horizon_static_upper"),
        "Adaptive CQR": ("adaptive_lower", "adaptive_upper"),
    }
    for name in run_names:
        output = release / name / "outputs"
        forecast_path = output / "forecast_quantiles_test.csv"
        forecasts = pd.read_csv(forecast_path)
        summary = pd.read_csv(output / "tables/overall_metrics.csv")
        manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        assert len(forecasts) == 1992
        assert np.isfinite(forecasts[quantiles]).all().all()
        assert (np.diff(forecasts[quantiles].to_numpy(), axis=1) >= 0).all()
        assert forecasts.groupby("issue_time")["horizon"].nunique().eq(24).all()
        assert manifest["release_version"] == "1.1.0"
        assert "Assistant" in manifest["execution_provenance"]
        for method, (lower_col, upper_col) in intervals.items():
            lower = forecasts[lower_col].to_numpy()
            upper = forecasts[upper_col].to_numpy()
            y = forecasts["price_eur_mwh"].to_numpy()
            reported = summary.loc[summary["method"].eq(method)].iloc[0]
            coverage = np.mean((lower <= y) & (y <= upper))
            width = np.mean(upper - lower)
            score = np.mean((upper - lower) + 10.0 * np.maximum(lower-y, 0) + 10.0 * np.maximum(y-upper, 0))
            np.testing.assert_allclose([coverage, width, score], reported[["coverage", "mean_width", "interval_score"]].to_numpy(dtype=float), rtol=1e-12)
        summary.insert(0, "run", name)
        summary.insert(1, "seed", manifest["seed"])
        summary.insert(2, "gamma", manifest["config"]["calibration"]["adaptive_gamma"])
        metrics.append(summary)
        run_audits[name] = {
            "forecast_rows": len(forecasts),
            "forecast_sha256": sha256(forecast_path),
            "data_fingerprint": manifest["data_fingerprint"],
            "n_figures": len(list((output / "figures").glob("*.png"))),
            "max_unbounded_fraction": float(summary["unbounded_fraction"].max()),
        }
    combined = pd.concat(metrics, ignore_index=True)
    combined.to_csv(tables / "all_corrected_metrics.csv", index=False)
    combined.loc[combined["run"].isin(run_names[:3])].to_csv(tables / "gamma_sensitivity.csv", index=False)
    combined.loc[combined["run"].isin(["baseline", "seed_20260818", "seed_20260819"])].to_csv(tables / "three_baseline_seeds.csv", index=False)
    old_output = ROOT / "evidence/runs/baseline/outputs"
    old_metrics = pd.read_csv(old_output / "tables/overall_metrics.csv")
    new_metrics = combined.loc[combined["run"].eq("baseline")]
    old_metrics.merge(new_metrics, on="method", suffixes=("_old_v102_windows", "_new_v110")).to_csv(tables / "baseline_old_new.csv", index=False)
    old_forecast = pd.read_csv(old_output / "forecast_quantiles_test.csv")
    new_forecast = pd.read_csv(release / "baseline/outputs/forecast_quantiles_test.csv")
    assert np.array_equal(old_forecast[quantiles].to_numpy(), new_forecast[quantiles].to_numpy())
    old_manifest = json.loads((old_output / "run_manifest.json").read_text(encoding="utf-8"))
    assert old_manifest["data_fingerprint"] == run_audits["baseline"]["data_fingerprint"]
    source_files = sorted(list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tests").glob("*.py")))
    for path in source_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    source_hashes = {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_files}
    preservation = {"status": "not_requested", "checked_files": 0, "mismatches": []}
    if args.original_root:
        pairs = [("historical/v102/outputs", "outputs"), ("historical/v102/experiments", "experiments"), ("historical/v102/report", "report"), ("historical/v102/README.md", "README.md"), ("historical/v102/REPRODUCIBILITY_RECORD.md", "REPRODUCIBILITY_RECORD.md"), ("evidence", "evidence")]
        preservation["status"] = "checked_against_read_only_original"
        preservation["source_root"] = str(args.original_root.resolve())
        for local_relative, original_relative in pairs:
            local_path = ROOT / local_relative
            paths = [local_path] if local_path.is_file() else list(local_path.rglob("*"))
            for path in paths:
                if not path.is_file():
                    continue
                suffix = Path() if local_path.is_file() else path.relative_to(local_path)
                original_path = args.original_root / original_relative / suffix
                preservation["checked_files"] += 1
                if not original_path.is_file() or sha256(path) != sha256(original_path):
                    preservation["mismatches"].append(path.relative_to(ROOT).as_posix())
        assert not preservation["mismatches"], preservation["mismatches"]
    audit = {
        "execution_provenance": "Assistant-executed local release verification, 2026-10-18; not applicant personal execution.",
        "version": energy_forecasting.__version__,
        "python": platform.python_version(),
        "interpreter": sys.executable,
        "import_location": str(Path(energy_forecasting.__file__).resolve()),
        "source_import_is_this_copy": Path(energy_forecasting.__file__).resolve().is_relative_to(ROOT / "src"),
        "bytecode_disabled": bool(sys.dont_write_bytecode),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "plot_cache": os.environ.get("MPLCONFIGDIR"),
        "raw_quantiles_exact_match_old_windows_baseline": True,
        "baseline_data_fingerprint_matches_old_windows": True,
        "source_syntax_validated_count": len(source_files),
        "source_sha256": source_hashes,
        "runs": run_audits,
        "historical_preservation": preservation,
    }
    assert audit["source_import_is_this_copy"]
    (release / "release_verification.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"version": audit["version"], "source_import_is_this_copy": True, "raw_quantiles_exact_match": True, "runs": run_audits, "preservation": preservation}, indent=2))


if __name__ == "__main__":
    main()
