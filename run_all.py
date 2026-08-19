#!/usr/bin/env python3
"""Regenerate every figure and source-data table in the paper.

One entry point for the whole analysis. Order matters only between stages:
``1_Data`` and ``2_Processing`` produce the reusable profile tables, and every
figure folder is a pure consumer of them, so figures can run in any order or
individually.

    python run_all.py                    # everything, in order
    python run_all.py --figure Fig5      # one figure
    python run_all.py --stage 2_Processing
    python run_all.py --skip 1_Data      # everything except feature sorting

Data is expected under ``downloaded_data/`` — fetch it first with::

    python utils/download_data.py

Point at data held elsewhere with ``COLOPAINT3D_DATA=/path/to/profiles``.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.paths import (ANALYSIS_ROOT, DATA_ROOT, FEATURES_ROOT,  # noqa: E402
                         REPO_ROOT, STAGING_ROOT, bulk_input, cellprofiler_results)

# Stages run in this order. Anything in analysis/ not named here is treated as a
# figure folder and run afterwards, alphabetically.
ORDERED_STAGES = ["0_Download", "1_Data", "2_Processing"]

# Folders that hold code but produce no figures on their own.
NON_FIGURE = set(ORDERED_STAGES) | {"4_BioImageArchive"}

# Only run when named explicitly: 0_Download pulls 16.6 GB.
OPT_IN_STAGES = {"0_Download"}

SKIP_PARTS = {".ipynb_checkpoints", "__pycache__", ".venv"}

# Notebooks needing inputs bigger than the downloaded profile tier. Each maps to a path
# that must exist; if it does not, the notebook is skipped with a reason instead of
# failing mid-run. The panels downstream are still rebuilt from the profile tables.
# The gate only asks whether an experiment has feature dumps at all — notebooks pin
# their own extraction stamp via require(features(...)).


def _feature_root(exp: str) -> Path:
    """The experiment's feature dumps, deposit first then the staged copy."""
    for root in (FEATURES_ROOT, STAGING_ROOT / "features"):
        if (root / exp).is_dir():
            return root / exp
    return FEATURES_ROOT / exp


REQUIRES: dict[str, Callable[[], Path]] = {
    # raw CellProfiler output, the input to feature sorting
    **{f"analysis/1_Data/{exp}/1_FeatureSorting.ipynb": (lambda e=exp: cellprofiler_results(e))
       for exp in ("exp1_main", "exp2_spheroid_size", "exp3_clearing_mag_z", "exp4_objective")},
    "analysis/2_Processing/exp1_main/Pycytominer_MIP.ipynb":
        lambda: cellprofiler_results("exp1_main"),
    "analysis/4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb":
        lambda: cellprofiler_results("exp1_main"),

    # per-slice / single-cell feature dumps, 19.5 GB, staged under input/features/
    **{nb: (lambda e=exp: _feature_root(e)) for nb, exp in {
        "analysis/2_Processing/exp1_main/2_Pycytominer.ipynb": "exp1_main",
        "analysis/2_Processing/exp1_main/2_Pycytominer_certain_slices.ipynb": "exp1_main",
        "analysis/2_Processing/exp2_spheroid_size/2_Pycytominer.ipynb": "exp2_spheroid_size",
        "analysis/2_Processing/exp3_clearing_mag_z/2_Pycytominer.ipynb": "exp3_clearing_mag_z",
        "analysis/2_Processing/exp4_objective/2_DetectandCombine.ipynb": "exp4_objective",
        "analysis/3_Figure2/CellCoverage/3_CellCoverage.ipynb": "exp1_main",
        "analysis/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb": "exp1_main",
        "analysis/3_Figure2/RemoveNoise/Prepare_Slice_Features.ipynb": "exp1_main",
    }.items()},

    # bulk tiers of the deposit, staged under input/
    "analysis/3_Figure6/EdU/EdU_analysis.ipynb":
        lambda: bulk_input("exp5_edu", "EdU_nuclei.csv"),
    # Needs both tiers: the expert masks and the single-cell dumps.
    "analysis/3_SupplFigure2/error_propegation.ipynb":
        lambda: next((q for q in (bulk_input("expert_annotation", "featICF_cells.csv"),
                                  _feature_root("exp1_main")) if not q.exists()),
                     _feature_root("exp1_main")),
}

# 3_Robustness_Combined_Final is deliberately absent: five of its seven panels need only
# the profile tables and are written first, so it fails at the panel that cannot run
# rather than being skipped whole.


def unavailable(rel: str) -> str | None:
    """Why ``rel`` cannot run here, or None if it can."""
    need = REQUIRES.get(rel)
    if need is None:
        return None
    path = need()
    if not path.exists():
        return f"needs {path}, which is not present"
    if path.is_dir() and not any(path.iterdir()):
        return f"needs {path}, which is empty"
    return None


# Notebooks parameterised by cell line and/or data type, read from the environment so
# one notebook emits every combination its PANEL map promises.
_LINES = ("HCT116", "HT29")
_TYPES = ("MIP", "aggregates", "2D")


def _sweep(lines=(), types=()):
    if lines and types:
        return [{"COLOPAINT3D_CELL_LINE": c, "COLOPAINT3D_DATA_TYPE": d}
                for c in lines for d in types]
    if lines:
        return [{"COLOPAINT3D_CELL_LINE": c} for c in lines]
    return [{"COLOPAINT3D_DATA_TYPE": d} for d in types]


SWEEPS = {
    # Fig 4a-d, Fig 5b, Suppl 4a-d, Suppl 5a
    "analysis/3_Figure4/PCAUMAP_pathway_v2.ipynb": _sweep(_LINES, _TYPES),
    # Fig 4e-f, Fig 5c-d, Suppl 4e-f, Suppl 5b-c. Both dimensions: sweeping cell_line
    # alone leaves Fig4e and Fig5c unrendered.
    "analysis/3_Figure4/3_PairwiseCorrelations.ipynb": _sweep(_LINES, _TYPES),
    # Fig 3e/3f (loops cell_line internally)
    "analysis/3_Figure3/3_PercentReplicating.ipynb": _sweep(types=("MIP", "aggregates")),
    # Fig 2f + Suppl 1d
    "analysis/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb": _sweep(lines=_LINES),
    # writes grit_data_{data_type}_{cell_line}.parquet
    "analysis/2_Processing/exp1_main/3_GritScores.ipynb": _sweep(_LINES, _TYPES),
    # Suppl 4h: air (the BOMI acquisition) vs water-immersion.
    "analysis/3_SupplFigure4/3_PCA_objective.ipynb": [
        {"COLOPAINT3D_PLATE": t} for t in ("air", "wi")
    ],
}


def _tag(env: dict) -> str:
    """Short suffix identifying one sweep combination, for the executed-copy name."""
    return "_".join(env[k] for k in ("COLOPAINT3D_CELL_LINE", "COLOPAINT3D_DATA_TYPE",
                                 "COLOPAINT3D_PLATE") if k in env)


class Notebook:
    """A notebook to execute, with the group it belongs to.

    ``env`` holds the sweep parameters for this run; a notebook with a SWEEPS entry
    yields one Notebook per combination.
    """

    def __init__(self, path: Path, group: str, env: dict | None = None):
        self.path = path
        self.group = group
        self.env = env or {}

    @property
    def rel(self) -> str:
        return self.path.relative_to(REPO_ROOT).as_posix()

    @property
    def label(self) -> str:
        return f"{self.rel} [{_tag(self.env)}]" if self.env else self.rel

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notebook {self.label}>"


def _matches_figure(group: str, figure: str) -> bool:
    """Accept any spelling of a figure folder.

    ``3_Figure5`` is matched by ``Fig5``, ``Figure5`` or ``3_Figure5``; likewise
    ``3_SupplFigure3`` by ``SupplFig3``. Folder names use the real paper numbers,
    so this only has to absorb the Fig/Figure abbreviation and the stage prefix.
    """
    def norm(text: str) -> str:
        text = text.lower()
        if "_" in text:
            text = text.split("_", 1)[1]
        return text.replace("figure", "fig")

    return norm(group) == norm(figure)


def discover(figure: str | None = None, stage: str | None = None,
             skip: Iterable[str] = ()) -> list[Notebook]:
    """Return notebooks to run, in execution order."""
    if not ANALYSIS_ROOT.is_dir():
        return []

    groups: list[str] = []
    present = sorted(p.name for p in ANALYSIS_ROOT.iterdir() if p.is_dir())
    for name in ORDERED_STAGES:
        if name in present:
            groups.append(name)
    groups += [n for n in present if n not in ORDERED_STAGES and n not in NON_FIGURE]

    # Opt-in stages appear only when named. Kept in ORDERED_STAGES so --stage still
    # finds them and they sort correctly when they do run.
    if stage is None:
        groups = [g for g in groups if g not in OPT_IN_STAGES]

    # --skip accepts a stage name or any spelling of a figure folder, like --figure.
    for name in skip:
        matched = [g for g in groups if g == name or _matches_figure(g, name)]
        if not matched:
            raise SystemExit(f"nothing to skip matches {name!r} (have {present})")
        groups = [g for g in groups if g not in matched]

    if stage:
        groups = [g for g in groups if g == stage]
        if not groups:
            raise SystemExit(f"no such stage: {stage!r} (have {present})")
    if figure:
        groups = [g for g in groups if _matches_figure(g, figure)]
        if not groups:
            raise SystemExit(
                f"no folder matches figure {figure!r}; try one of "
                f"{[p for p in present if p not in NON_FIGURE]}"
            )

    found: list[Notebook] = []
    for group in groups:
        root = ANALYSIS_ROOT / group
        for path in sorted(root.rglob("*.ipynb")):
            if SKIP_PARTS & set(path.parts):
                continue
            if path.name.endswith(".executed.ipynb"):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if (why := unavailable(rel)) is not None:
                print(f"  (skipping {rel}: {why})")
                continue
            for env in SWEEPS.get(rel, [{}]):
                found.append(Notebook(path, group, env))
    return found


def _runner() -> str:
    """Pick an execution backend, preferring papermill."""
    try:
        import papermill  # noqa: F401

        return "papermill"
    except ImportError:
        pass
    # sys.executable, not a bare "jupyter", so the runner stays in the calling venv.
    if subprocess.run(
        [sys.executable, "-m", "nbconvert", "--version"], capture_output=True
    ).returncode == 0:
        return "nbconvert"
    raise SystemExit(
        "no notebook runner available. Install one of:\n"
        "    pip install papermill        (preferred)\n"
        "    pip install nbconvert"
    )


def execute(nb: Notebook, backend: str) -> tuple[bool, float, str]:
    """Run one notebook. Returns (ok, seconds, message)."""
    started = time.time()
    # Distinct executed copy per sweep combination, so a failure is traceable.
    stem = f"{nb.path.stem}.{_tag(nb.env)}" if nb.env else nb.path.stem
    out = nb.path.with_name(f"{stem}.executed.ipynb")
    if backend == "papermill":
        cmd = [sys.executable, "-m", "papermill", str(nb.path), str(out),
               "--cwd", str(nb.path.parent), "--log-output"]
    else:
        cmd = [
            sys.executable, "-m", "nbconvert", "--to", "notebook", "--execute",
            f"--output={out.name}", str(nb.path),
        ]
    # Parameters travel by environment: nbconvert cannot inject cells.
    env = {**os.environ, **nb.env}
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = time.time() - started
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        return False, elapsed, "\n".join(tail)
    return True, elapsed, ""


def _verify(ok_message: str, lead: str = "source-data problems") -> int:
    """Check the run is sound: panels ↔ manifest ↔ source tables, and no blank panel.

    Both halves are needed: a panel can have a healthy manifest row and a correct source
    table and still be an empty page.
    """
    from utils.check_panels_nonblank import main as panels_have_ink
    from utils.panels import verify_manifest

    problems = verify_manifest()
    if problems:
        print(f"{lead} ({len(problems)}):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if panels_have_ink() != 0:
        return 1
    print(ok_message)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--figure", help="run one figure, e.g. Fig5 or SupplFig3")
    ap.add_argument("--stage", help="run one stage, e.g. 1_Data or 2_Processing")
    ap.add_argument(
        "--skip", action="append", default=[], metavar="NAME",
        help="skip a stage or figure folder; repeatable. --skip 1_Data leaves out "
             "feature sorting, which needs the 19.5 GB dumps and rewrites them",
    )
    ap.add_argument(
        "--keep-going", action="store_true",
        help="continue after a notebook fails instead of stopping",
    )
    args = ap.parse_args()

    notebooks = discover(figure=args.figure, stage=args.stage, skip=args.skip)
    if not notebooks:
        print("No notebooks found under analysis/.")
        return 0

    print(f"Running {len(notebooks)} notebook(s):\n")
    current = None
    for nb in notebooks:
        if nb.group != current:
            current = nb.group
            print(f"  [{current}]")
        print(f"      {nb.label}")
    print()

    if not DATA_ROOT.is_dir() or not any(DATA_ROOT.iterdir()):
        print(
            f"warning: {DATA_ROOT} is empty. Notebooks will fail on missing inputs.\n"
            "         Run: python utils/download_data.py\n",
            file=sys.stderr,
        )

    backend = _runner()
    print(f"backend: {backend}\n")

    failures: list[tuple[Notebook, str]] = []
    for i, nb in enumerate(notebooks, 1):
        print(f"[{i}/{len(notebooks)}] {nb.label} ... ", end="", flush=True)
        ok, elapsed, msg = execute(nb, backend)
        if ok:
            print(f"ok ({elapsed:.0f}s)")
        else:
            print(f"FAILED ({elapsed:.0f}s)")
            print("    " + msg.replace("\n", "\n    "), file=sys.stderr)
            failures.append((nb, msg))
            if not args.keep_going:
                print("\nstopping. Use --keep-going to run the rest anyway.", file=sys.stderr)
                break

    print()
    if failures:
        print(f"{len(failures)} notebook(s) failed:", file=sys.stderr)
        for nb, _ in failures:
            print(f"  - {nb.label}", file=sys.stderr)
        return 1

    return _verify("done: all notebooks ran and every panel has source data.",
                   lead="all notebooks ran, but source-data problems")


if __name__ == "__main__":
    raise SystemExit(main())
