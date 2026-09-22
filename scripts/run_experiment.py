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
        help="Optional separate directory for data and outputs; prevents one run overwriting another.",
    )
    args = parser.parse_args()
    output_root = args.output_root.resolve() if args.output_root else ROOT
    result = run(args.config, output_root)
    print(result["summary"].to_string(index=False))
    print(f"\nArtifacts written under: {output_root / 'outputs'}")


if __name__ == "__main__":
    main()
