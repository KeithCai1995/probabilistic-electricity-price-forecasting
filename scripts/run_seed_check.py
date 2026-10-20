"""Seed diagnostic; writes an explicit config then runs it.

Invoke once per seed with a dedicated output root. The same full baseline model,
420-day simulator and rolling folds are retained, so only the seed changes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_forecasting.experiment import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / "configs/base.yaml").read_text(encoding="utf-8"))
    config["seed"] = args.seed
    args.output_root.mkdir(parents=True, exist_ok=True)
    config_path = args.output_root / "executed_config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    result = run(config_path, args.output_root)
    print(result["summary"].to_string(index=False))
    print(f"Artifacts written under: {args.output_root / 'outputs'}")


if __name__ == "__main__":
    main()
