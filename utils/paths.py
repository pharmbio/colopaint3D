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
    "REPO_ROOT", "DATA_ROOT", "FEATURES_ROOT", "FIGURES_ROOT", "SOURCE_DATA_ROOT", "ANALYSIS_ROOT",
    "EXTERNAL_ROOT", "DERIVED_ROOT",
    "EXPERIMENTS", "UPSTREAM_NAMES",
    "profiles", "profile_input", "derived",
    "features", "feature_output", "figdir", "source_data", "analysis", "data_dir",
    "metadata", "external", "require", "cellprofiler_results",
]

# paths.py lives at <repo>/utils/paths.py, so the root is two levels up. This is
# resolved from __file__ rather than the working directory on purpose: it stays
# correct no matter where a notebook is executed from.
REPO_ROOT = Path(os.environ.get("COLOPAINT3D_ROOT", Path(__file__).resolve().parents[1]))

DATA_ROOT = Path(os.environ.get("COLOPAINT3D_DATA", REPO_ROOT / "data"))
# Per-slice / single-cell CellProfiler dumps (~19.5 GB). Outside every download
# tier, so this points wherever they actually live.
FEATURES_ROOT = Path(os.environ.get("COLOPAINT3D_FEATURES", DATA_ROOT / "features"))
FIGURES_ROOT = Path(os.environ.get("COLOPAINT3D_FIGURES", REPO_ROOT / "figures"))
# Bulk inputs kept outside the repo and outside every download tier.
EXTERNAL_ROOT = Path(os.environ.get("COLOPAINT3D_EXTERNAL",
                                    "/share/data/analyses/christa/colopaint3D"))
SOURCE_DATA_ROOT = Path(os.environ.get("COLOPAINT3D_SOURCE_DATA", REPO_ROOT / "source_data"))
# Anything a run *generates* that is not a panel. Separate from DATA_ROOT on purpose:
# DATA_ROOT holds the deposited tables listed in scripts/data_manifest.tsv and is never
# written to, so regenerating can never overwrite a deposited artifact. See derived().
DERIVED_ROOT = Path(os.environ.get("COLOPAINT3D_DERIVED", REPO_ROOT / "derived"))
ANALYSIS_ROOT = REPO_ROOT / "analysis"

# Raw CellProfiler output, the input to 1_FeatureSorting. On the pharmbio cluster this
# is a mount; everyone else downloads it from the BioImage Archive into DATA_ROOT.
CLUSTER_CP_RESULTS = Path("/share/data/cellprofiler/automation/results")

# The three experiments in the paper. Keys are used everywhere; the values record
# which upstream folder each came from, so the port stays traceable.
EXPERIMENTS = {
    "exp1_main": "z-slice sampling, 52 compounds — feeds every figure",
    "exp2_spheroid_size": "seeding density / spheroid size — Suppl Fig 3c",
    "exp3_clearing_mag_z": "clearing, magnification, z-sampling — Suppl Fig 3b/d/e",
    "exp4_objective": "air vs water-immersion objective — Suppl Fig 4h/i",
}

# Upstream provenance. exp4 came from a *separate repository*
# (`colopaint3D_AZ`), not from the colopaint3D tree.
UPSTREAM_NAMES = {
    "exp1_main": "colopaint3D/spher_colo52_v1",
    "exp2_spheroid_size": "colopaint3D/spher_colo52_v2",
    "exp3_clearing_mag_z": "colopaint3D/spher_colo52_v3",
    "exp4_objective": "colopaint3D_AZ/spher_colo52_v1",
}

# exp4's acquisitions are named by run rather than by condition.
EXP4_DATASETS = {
    "bomi_20241220": "CellPainting_20241220clearedspheroidsBOMI_20241220_151510",
    "cleared3d_20250127": "CellPainting_20250127Cellpaintcleared3D_20250127_171120",
    "wi_20250203": "CellPainting_CellPaint3DBomi_WI_for_Jordi_20250203_155142",
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


def derived(exp: str, name: str = "") -> Path:
    """Destination for a table a notebook *generates*, mirroring :func:`profiles`.

    >>> derived("exp1_main", "normalized_data_merged_HCT116.csv")

    ``data/`` holds what was downloaded — every file in ``scripts/data_manifest.tsv``,
    SHA256-verified — and notebooks never write there. Anything regenerated lands here
    instead, so a re-run cannot overwrite a deposited artifact. It did once:
    ``Prepare_Slice_Features`` rebuilt ``normalized_data_merged_HCT116.csv`` straight
    into ``data/``, leaving the local copy 305,902,842 B against the deposit's
    305,863,934 B, with nothing to report the drift.

    ``derived/`` is gitignored and always safe to delete. To adopt a regenerated table,
    copy it into ``data/`` deliberately and re-hash the manifest.
    """
    _check_experiment(exp)
    base = DERIVED_ROOT / exp
    base.mkdir(parents=True, exist_ok=True)
    return base / name if name else base


def profile_input(exp: str, name: str) -> Path:
    """Read a profile table: the deposit first, a local regeneration second.

    The deposit wins, so a stale ``derived/`` can never shadow it. The fallback is for
    someone who skipped the ``normalized`` download tier and rebuilt the table from the
    feature dumps instead. Returns the canonical ``data/`` path when neither exists, so
    :func:`require` names the file a reader is expected to fetch.
    """
    deposited = profiles(exp, name)
    if deposited.exists():
        return deposited
    regenerated = DERIVED_ROOT / exp / name
    return regenerated if regenerated.exists() else deposited


def features(exp: str, version: str, level: str, name: str | None = None) -> Path:
    """Path to a CellProfiler feature dump.

    >>> features("exp1_main", "011225", "SingleCell", "HCT116.parquet")

    ``version`` is the DDMMYY extraction stamp. These dumps total ~19.5 GB and are
    outside every download tier, so point ``COLOPAINT3D_FEATURES`` at wherever they
    live. Extraction stamps are re-runs of the same images, not different data.
    """
    _check_experiment(exp)
    base = FEATURES_ROOT / exp / f"FeaturesImages_{version}_none" / level
    return base / name if name else base


def feature_output(exp: str, version: str, *, allow_existing: bool = False) -> Path:
    """Destination for a FeatureSorting run. **Refuses to overwrite by default.**

    The upstream notebook hardcoded ``OutputDir = 'FeaturesImages_011225'``, so any
    re-run silently overwrote a 7.7 GB feature set that took hours to build — and
    that set is the provenance of the published profiles. Overwriting is therefore
    opt-in, and ``version`` has no default so the stamp is always a deliberate choice.

    >>> feature_output("exp1_main", "130826")          # new stamp, fine
    >>> feature_output("exp1_main", "011225")          # raises: would clobber
    >>> feature_output("exp1_main", "011225", allow_existing=True)   # explicit
    """
    _check_experiment(exp)
    if not version or not version.strip():
        raise ValueError("version is required, e.g. '130826' (DDMMYY of the extraction)")
    dest = FEATURES_ROOT / exp / f"FeaturesImages_{version}_none"
    if dest.exists() and not allow_existing:
        raise FileExistsError(
            f"{dest} already exists.\n"
            "Refusing to overwrite an existing feature set — it is the provenance of\n"
            "the published profiles. Either choose a new version stamp, or pass\n"
            "allow_existing=True if you really mean to replace it."
        )
    return dest


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


def external(name: str) -> Path:
    """A bulk input held outside the repo (expert annotations, mask stacks, ...).

    These are too large to ship or to put in a download tier — the expert-annotation
    set alone is 7.7 GB. Notebooks that need them read from here when present and
    otherwise fall back to a small cached table committed under the figure folder,
    so the published figure still regenerates. Point ``COLOPAINT3D_EXTERNAL`` at
    wherever the bulk inputs live.
    """
    return EXTERNAL_ROOT / name


def data_dir(exp: str) -> Path:
    """The shipped ``1_Data`` folder for an experiment (metadata, file maps).

    Upstream this was one ``rootDir`` holding metadata, feature dumps and results
    together; here those are split across ``analysis/1_Data``, ``data/features``
    and ``data/``, so this covers only the small shipped metadata.
    """
    _check_experiment(exp)
    return ANALYSIS_ROOT / "1_Data" / exp


def metadata(name: str, exp: str = "exp1_main") -> Path:
    """Path to a plate/compound metadata table shipped with the analysis."""
    _check_experiment(exp)
    return ANALYSIS_ROOT / "1_Data" / exp / name


def cellprofiler_results(exp: str = "exp1_main") -> Path:
    """Where the raw CellProfiler output tables live, for ``1_FeatureSorting``.

    Three sources, tried in order:

    1. ``COLOPAINT3D_CP_RESULTS`` — an explicit override, always wins;
    2. ``<DATA_ROOT>/cellprofiler_results/<exp>`` — the copy fetched from the
       BioImage Archive by ``analysis/0_Download``;
    3. the pharmbio cluster mount.

    The returned path is not guaranteed to exist: only the cluster fallback is
    returned unconditionally, so that the error a user without any of the three
    sees names the cluster rather than a directory they have never heard of.
    Pass it through :func:`require` if you need it to be present.
    """
    _check_experiment(exp)
    override = os.environ.get("COLOPAINT3D_CP_RESULTS")
    if override:
        return Path(override)
    downloaded = DATA_ROOT / "cellprofiler_results" / exp
    if downloaded.is_dir() and any(downloaded.iterdir()):
        return downloaded
    return CLUSTER_CP_RESULTS


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
