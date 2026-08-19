"""Repo-relative path resolution.

Every path in this repository is derived from here. Notebooks must NOT call
``os.chdir()`` and must NOT contain absolute paths: resolution that depends on one
machine's filesystem does not survive a clone.

Every default resolves under :data:`REPO_ROOT`. The ``COLOPAINT3D_*`` environment
variables are the only way to point outside it, and each is opt-in.

Notebook preamble (works at any folder depth):

    import sys, pathlib
    ROOT = next(p for p in pathlib.Path.cwd().parents if (p / "utils" / "paths.py").is_file())
    sys.path.insert(0, str(ROOT))
    from utils.paths import profiles, figdir, EXPERIMENTS

Overrides, for running against data held elsewhere:

    COLOPAINT3D_DATA=<some-other-location>  python utils/download_data.py --check
"""
from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "REPO_ROOT", "DATA_ROOT", "FEATURES_ROOT", "FIGURES_ROOT", "SOURCE_DATA_ROOT", "ANALYSIS_ROOT",
    "STAGING_ROOT", "DERIVED_ROOT", "GENESETS_ROOT", "geneset",
    "BULK_TIERS", "bulk_input",
    "EXPERIMENTS",
    "profiles", "profile_input", "derived",
    "analysis_input", "analysis_input_output",
    "features", "feature_output", "figdir", "source_data", "analysis", "data_dir",
    "metadata", "require", "cellprofiler_results",
]

# Two levels up from utils/paths.py. From __file__, not the working directory, so it
# holds wherever a notebook runs.
REPO_ROOT = Path(os.environ.get("COLOPAINT3D_ROOT", Path(__file__).resolve().parents[1]))

DATA_ROOT = Path(os.environ.get("COLOPAINT3D_DATA", REPO_ROOT / "downloaded_data"))
# Per-slice / single-cell CellProfiler dumps (~19.5 GB), outside every download tier.
FEATURES_ROOT = Path(os.environ.get("COLOPAINT3D_FEATURES", DATA_ROOT / "features"))
FIGURES_ROOT = Path(os.environ.get("COLOPAINT3D_FIGURES", REPO_ROOT / "figures"))
# Deposit staging: the bulk tiers as assembled for upload to S-BIAD2254, and what
# bulk_input() falls back to until they are fetched. Not env-overridable.
STAGING_ROOT = REPO_ROOT / "input"
# MSigDB gene-set files (.gmt), separately licensed so neither committed nor deposited.
GENESETS_ROOT = Path(os.environ.get("COLOPAINT3D_GENESETS", REPO_ROOT / "genesets"))
# Staged copy: genesets/ first, then input/genesets/.
GENESETS_STAGED = STAGING_ROOT / "genesets"
SOURCE_DATA_ROOT = Path(os.environ.get("COLOPAINT3D_SOURCE_DATA", REPO_ROOT / "source_data"))
# Anything a run generates that is not a panel. Kept apart from DATA_ROOT, which holds
# the deposit and is never written to. See derived().
DERIVED_ROOT = Path(os.environ.get("COLOPAINT3D_DERIVED", REPO_ROOT / "derived"))
ANALYSIS_ROOT = REPO_ROOT / "analysis"

# The five acquisitions in the paper, and the panels each one feeds.
EXPERIMENTS = {
    "exp1_main": "z-slice sampling, 52 compounds — feeds every figure",
    "exp2_spheroid_size": "seeding density / spheroid size — Suppl Fig 3c",
    "exp3_clearing_mag_z": "clearing, magnification, z-sampling — Suppl Fig 3b/d/e",
    "exp4_objective": "air vs water-immersion objective — Suppl Fig 4h/i",
    "exp5_edu": "EdU proliferation and 5-FU/olaparib RNA-seq — Fig 6b/6c/6d, Suppl Fig 6b",
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

    Notebooks never write to ``downloaded_data/``, so a re-run cannot overwrite a
    deposited artifact. ``derived/`` is gitignored and safe to delete; to adopt a
    regenerated table, copy it across deliberately and re-hash the manifest.
    """
    _check_experiment(exp)
    base = DERIVED_ROOT / exp
    base.mkdir(parents=True, exist_ok=True)
    return base / name if name else base


def profile_input(exp: str, name: str) -> Path:
    """Read a profile table: the deposit first, a local regeneration second.

    The deposit wins, so a stale ``derived/`` cannot shadow it. Returns the
    ``downloaded_data/`` path when neither exists, so :func:`require` names the file a
    reader is expected to fetch.
    """
    deposited = profiles(exp, name)
    if deposited.exists():
        return deposited
    regenerated = DERIVED_ROOT / exp / name
    return regenerated if regenerated.exists() else deposited


# The one extraction stamp each experiment is read at. Stamps are re-runs of the same
# images, not different data. Keeping the choice here rather than in thirteen notebook
# literals is what stops a second stamp reappearing unnoticed.
EXTRACTION_STAMP = {
    "exp1_main": "011225",
    "exp2_spheroid_size": "070426",
    "exp3_clearing_mag_z": "150526",
}


def features(exp: str, level: str, name: str | None = None, *,
             version: str | None = None) -> Path:
    """Path to a CellProfiler feature dump, archive first.

    >>> features("exp1_main", "SingleCell", "HCT116.parquet")

    The stamp comes from :data:`EXTRACTION_STAMP`; ``version`` overrides it for exp4,
    whose three acquisitions each carry their own composite name.

    Resolution order, mirroring :func:`bulk_input`:

    1. ``downloaded_data/features/<exp>/FeaturesImages_<stamp>_none/<level>``;
    2. ``input/features/<exp>/FeaturesImages_<stamp>_none/<level>`` — the staged copy.

    Returns the first when neither exists, so :func:`require` names the directory a
    reader is expected to populate.
    """
    _check_experiment(exp)
    if version is None:
        try:
            version = EXTRACTION_STAMP[exp]
        except KeyError:
            raise KeyError(
                f"{exp} has no single extraction stamp; pass version= explicitly"
            ) from None
    rel = Path(exp) / f"FeaturesImages_{version}_none" / level
    for root in (FEATURES_ROOT, STAGING_ROOT / "features"):
        cand = root / rel
        cand = cand / name if name else cand
        if cand.exists():
            return cand
    base = FEATURES_ROOT / rel
    return base / name if name else base


def feature_output(exp: str, version: str, *, allow_existing: bool = False) -> Path:
    """Destination for a FeatureSorting run. **Refuses to overwrite by default.**

    A feature set takes hours to build and backs the published profiles, so overwriting
    is opt-in and ``version`` has no default.

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
            "Refusing to overwrite an existing feature set. Choose a new version\n"
            "stamp, or pass allow_existing=True to replace it."
        )
    return dest


ANALYSIS_INPUT_SUBDIR = "analysis_inputs"


def analysis_input(relpath: str) -> Path:
    """Resolve a small analysis input, archive first.

    >>> analysis_input("3_Figure6/DEG/data/QMMFHL-colo52_Control_vs_colo52_5-FU-dge.csv")

    The aggregations a panel plots when its real inputs are too large to ship.

    Resolution order, highest priority first:

    1. ``downloaded_data/analysis_inputs/<relpath>`` — the archive, checksummed against
       ``utils/data_manifest.tsv``, and authoritative.
    2. ``derived/analysis_inputs/<relpath>`` — rebuilt locally.
    3. ``input/analysis_inputs/<relpath>`` — the staged copy.
    4. ``analysis/<relpath>`` — a copy dropped back beside its notebook.

    ``relpath`` is relative to ``analysis/``. Returns the archive path when nothing
    exists, so :func:`require` names the file a reader is expected to fetch.

    **Always pass a file, never a directory.** Resolution stops at the first level
    that exists, so a folder holding one regenerated table shadows the rest.
    """
    fetched = DATA_ROOT / ANALYSIS_INPUT_SUBDIR / relpath
    if fetched.exists():
        return fetched
    rebuilt = DERIVED_ROOT / ANALYSIS_INPUT_SUBDIR / relpath
    if rebuilt.exists():
        return rebuilt
    staged = STAGING_ROOT / ANALYSIS_INPUT_SUBDIR / relpath
    if staged.exists():
        return staged
    committed = ANALYSIS_ROOT / relpath
    return committed if committed.exists() else fetched


def analysis_input_output(relpath: str) -> Path:
    """Destination for a rebuilt analysis input.

    Always under ``derived/``, never ``downloaded_data/``, which holds the deposit.
    """
    dest = DERIVED_ROOT / ANALYSIS_INPUT_SUBDIR / relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
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

    CSV, kept apart from the parquet intermediates in ``downloaded_data/``.
    """
    SOURCE_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    return SOURCE_DATA_ROOT / filename


def analysis(*parts: str) -> Path:
    """Path inside ``analysis/``, e.g. ``analysis("3_Figure5", "GritScores")``."""
    return ANALYSIS_ROOT.joinpath(*parts)


# Deposit tiers too large to commit: the EdU per-object tables behind Fig 6b and the
# expert-annotation measurements behind Suppl 2d/2e. One flat folder each, with a
# staged copy under input/<tier>/ of the same name.
BULK_TIERS = ("exp5_edu", "expert_annotation")


def bulk_input(tier: str, name: str = "") -> Path:
    """A bulk input tier from the deposit, archive first.

    >>> bulk_input("exp5_edu", "EdU_nuclei.csv")
    >>> bulk_input("expert_annotation")      # the directory

    Resolution order:

    1. ``downloaded_data/<tier>/`` — downloaded from S-BIAD2254;
    2. ``input/<tier>/`` — the staged copy, which ships in the tree.

    Returns the archive path when neither exists, so :func:`require` names the file to
    fetch. Every panel downstream also has a small fallback table, so a clone without
    these still draws the figure.
    """
    if tier not in BULK_TIERS:
        raise KeyError(f"unknown bulk tier {tier!r}; expected one of {BULK_TIERS}")
    rel = Path(tier)
    fetched = DATA_ROOT / rel
    staged = STAGING_ROOT / rel
    for base in (fetched, staged):
        cand = base / name if name else base
        if cand.exists():
            return cand
    return fetched / name if name else fetched


def geneset(name: str) -> Path:
    """An MSigDB ``.gmt`` gene-set file, supplied by the reader.

    >>> geneset("h.all.v2026.1.Hs.symbols.gmt")

    Figure 6 needs two, both MSigDB **v2026.1 (Hs)**:

    * ``h.all.v2026.1.Hs.symbols.gmt``  — Hallmark, 50 sets
    * ``c2.all.v2026.1.Hs.symbols.gmt`` — C2 curated, 7,670 sets

    Separately licensed, so cited rather than copied. Download both from
    https://www.gsea-msigdb.org/ into ``genesets/``, or set ``COLOPAINT3D_GENESETS``.
    Without them the gene-set panels fall back to the prerank results in S-BIAD2254.
    """
    fetched = GENESETS_ROOT / name
    return fetched if fetched.exists() else GENESETS_STAGED / name


def data_dir(exp: str) -> Path:
    """The shipped ``1_Data`` folder for an experiment (metadata, file maps).

    Metadata only; feature dumps and profile tables live under ``downloaded_data/``.
    """
    _check_experiment(exp)
    return ANALYSIS_ROOT / "1_Data" / exp


def metadata(name: str, exp: str = "exp1_main") -> Path:
    """Path to a plate/compound metadata table shipped with the analysis."""
    _check_experiment(exp)
    return ANALYSIS_ROOT / "1_Data" / exp / name


def cellprofiler_results(exp: str = "exp1_main") -> Path:
    """Where the raw CellProfiler output tables live, for ``1_FeatureSorting``.

    Two sources, tried in order:

    1. ``COLOPAINT3D_CP_RESULTS`` — an opt-in override, always wins;
    2. ``<DATA_ROOT>/cellprofiler_results/<exp>`` — fetched by ``analysis/0_Download``.

    Not guaranteed to exist; pass it through :func:`require` if you need it present.
    """
    _check_experiment(exp)
    override = os.environ.get("COLOPAINT3D_CP_RESULTS")
    if override:
        return Path(override)
    return DATA_ROOT / "cellprofiler_results" / exp


def require(path: Path, hint: str | None = None) -> Path:
    """Return ``path`` if it exists, else raise naming the fix.

    Missing input data is the likeliest failure on a fresh clone, so the error says
    what to do rather than surfacing a bare FileNotFoundError from inside pandas.
    """
    path = Path(path)
    if path.exists():
        return path

    lines = [f"missing required input: {path}"]
    if path.is_relative_to(DATA_ROOT):
        lines.append(
            "This is a downloaded profile table. Fetch the processed data with:\n"
            "    python utils/download_data.py"
        )
    if hint:
        lines.append(hint)
    raise FileNotFoundError("\n".join(lines))
