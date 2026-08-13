"""Repo-relative path resolution.

Every path in this repository is derived from here. Notebooks must NOT call
``os.chdir()`` and must NOT contain absolute paths — that is what made the
upstream tree unrunnable anywhere but one machine (22 ``chdir`` calls, 7
references to a sibling checkout, and two spellings of the same mount:
``/share/...`` and ``/home/jovyan/share/...``).

Notebook preamble (works at any folder depth):

    import sys, pathlib
    ROOT = next(p for p in pathlib.Path.cwd().parents if (p / "utils" / "paths.py").is_file())
    sys.path.insert(0, str(ROOT))
    from utils.paths import profiles, figdir, EXPERIMENTS

Overrides, for running against data held outside the repo:

    COLOPAINT3D_DATA=/mnt/big/profiles  python run_all.py
"""
from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "REPO_ROOT", "DATA_ROOT", "FIGURES_ROOT", "SOURCE_DATA_ROOT", "ANALYSIS_ROOT",
    "EXPERIMENTS", "UPSTREAM_NAMES",
    "profiles", "figdir", "source_data", "analysis", "metadata", "require",
]

# paths.py lives at <repo>/utils/paths.py, so the root is two levels up. This is
# resolved from __file__ rather than the working directory on purpose: it stays
# correct no matter where a notebook is executed from.
REPO_ROOT = Path(os.environ.get("COLOPAINT3D_ROOT", Path(__file__).resolve().parents[1]))

DATA_ROOT = Path(os.environ.get("COLOPAINT3D_DATA", REPO_ROOT / "data"))
FIGURES_ROOT = Path(os.environ.get("COLOPAINT3D_FIGURES", REPO_ROOT / "figures"))
SOURCE_DATA_ROOT = REPO_ROOT / "source_data"
ANALYSIS_ROOT = REPO_ROOT / "analysis"

# The three experiments in the paper. Keys are used everywhere; the values record
# which upstream folder each came from, so the port stays traceable.
EXPERIMENTS = {
    "exp1_main": "z-slice sampling, 52 compounds — feeds every figure",
    "exp2_spheroid_size": "seeding density / spheroid size — Suppl Fig 3 only",
    "exp3_clearing_mag_z": "clearing, magnification, z-sampling — Suppl Fig 3 only",
}

UPSTREAM_NAMES = {
    "exp1_main": "spher_colo52_v1",
    "exp2_spheroid_size": "spher_colo52_v2",
    "exp3_clearing_mag_z": "spher_colo52_v3",
}


def _check_experiment(exp: str) -> str:
    if exp not in EXPERIMENTS:
        raise KeyError(
            f"unknown experiment {exp!r}; expected one of {sorted(EXPERIMENTS)}"
        )
    return exp


def profiles(exp: str, name: str) -> Path:
    """Path to a processed profile table, e.g.

    >>> profiles("exp1_main", "grit_data_aggregates_HCT116.parquet")

    Nothing is created; use :func:`require` to fail helpfully when absent.
    """
    _check_experiment(exp)
    return DATA_ROOT / exp / name


def figdir(figure: str) -> Path:
    """Directory for a figure's rendered panels, created on demand.

    ``figure`` is the paper figure name, e.g. ``"Fig5"``, ``"SupplFig3"``.
    """
    out = FIGURES_ROOT / figure
    out.mkdir(parents=True, exist_ok=True)
    return out


def source_data(filename: str) -> Path:
    """Path to a per-panel source-data table under ``source_data/``.

    Source tables are CSV and live apart from the parquet intermediates in
    ``data/`` so that submission material is never mixed with working data.
    """
    SOURCE_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    return SOURCE_DATA_ROOT / filename


def analysis(*parts: str) -> Path:
    """Path inside ``analysis/``, e.g. ``analysis("3_Figure5", "GritScores")``."""
    return ANALYSIS_ROOT.joinpath(*parts)


def metadata(name: str, exp: str = "exp1_main") -> Path:
    """Path to a plate/compound metadata table shipped with the analysis."""
    _check_experiment(exp)
    return ANALYSIS_ROOT / "1_Data" / exp / name


def require(path: Path, hint: str | None = None) -> Path:
    """Return ``path`` if it exists, else raise with actionable instructions.

    Missing input data is the single most likely failure for someone who has
    just cloned this repo, so the error names the fix instead of surfacing a
    bare FileNotFoundError from deep inside pandas.
    """
    path = Path(path)
    if path.exists():
        return path

    lines = [f"missing required input: {path}"]
    if path.is_relative_to(DATA_ROOT):
        lines.append(
            "This is a downloaded profile table. Fetch the processed data with:\n"
            "    python scripts/download_data.py"
        )
    if hint:
        lines.append(hint)
    raise FileNotFoundError("\n".join(lines))
