"""Protect reference artifacts when creating a new experiment output directory."""
from __future__ import annotations

import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def prepare_output_root(root: str | Path, *, overwrite: bool = False) -> Path:
    """Create a run directory, refusing nonempty targets unless explicitly allowed.

    Overwrite means replacing run-owned outputs in that directory, not deleting
    arbitrary files. Repository roots, source folders and preserved reference
    evidence remain protected even when overwrite=True.
    """
    target = Path(root).resolve()
    repository = REPOSITORY_ROOT.resolve()
    if target == target.parent or target == repository or target in repository.parents:
        raise ValueError("Output must be a dedicated run directory, not the repository or its ancestor")
    if ".git" in [part.casefold() for part in target.parts]:
        raise ValueError("Git metadata cannot be an experiment output directory")
    if target.is_relative_to(repository):
        relative = target.relative_to(repository)
        protected = {"src", "scripts", "tests", "configs", "data", "report", "historical", "evidence", ".github"}
        if relative.parts[0].casefold() in protected:
            raise ValueError("Source, reports and preserved evidence cannot be overwritten by a run")
        if relative.parts[0].casefold() == "corrected_v110" and (
            len(relative.parts) < 2 or not relative.parts[1].casefold().startswith("supplementary_")
        ):
            raise ValueError("Existing corrected reference artifacts are protected; use local_runs/ or supplementary_*")
    if target.exists():
        if not target.is_dir():
            raise ValueError("Output root is not a directory")
        if any(target.iterdir()):
            if not overwrite:
                raise FileExistsError("Output directory is nonempty; choose a new directory or pass --overwrite explicitly")
            recognized = False
            for marker, field, expected in [
                (target / ".p1_output.json", "project", "P1_forecasting_under_regime_shift"),
                (target / "outputs/run_manifest.json", "project", "P1_forecasting_under_regime_shift"),
            ]:
                try:
                    recognized = recognized or json.loads(marker.read_text(encoding="utf-8")).get(field) == expected
                except (OSError, ValueError, AttributeError):
                    pass
            if not recognized:
                raise ValueError("--overwrite only accepts a recognized P1 run directory, not arbitrary existing folders")
    target.mkdir(parents=True, exist_ok=True)
    (target / ".p1_output.json").write_text(json.dumps({"project": "P1_forecasting_under_regime_shift", "purpose": "dedicated experiment output"}, indent=2), encoding="utf-8")
    return target
