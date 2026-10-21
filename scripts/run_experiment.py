from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from energy_forecasting.experiment import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the P1 probabilistic forecasting experiment")
    parser.add_argument("--config", default=str(ROOT / "configs" / "base.yaml"))
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Dedicated directory for this run; repository roots and preserved references are protected.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Explicitly allow replacing run-owned outputs in a nonempty run directory")
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    result = run(args.config, output_root, overwrite=args.overwrite)
    print(result["summary"].to_string(index=False))
    print(f"\nArtifacts written under: {output_root / 'outputs'}")


if __name__ == "__main__":
    main()
