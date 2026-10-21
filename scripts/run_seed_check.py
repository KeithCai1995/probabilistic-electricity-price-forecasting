"""Seed diagnostic; writes an explicit config then runs it.

Invoke once per seed with a dedicated output root. The same full baseline model,
420-day simulator and rolling folds are retained, so only the seed changes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_forecasting.experiment import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true", help="Explicitly allow replacing outputs in a nonempty run directory")
    args = parser.parse_args()
    result = run(ROOT / "configs/base.yaml", args.output_root, seed_override=args.seed, overwrite=args.overwrite)
    print(result["summary"].to_string(index=False))
    print(f"Artifacts written under: {args.output_root / 'outputs'}")


if __name__ == "__main__":
    main()
