#!/usr/bin/env python3
"""Regenerate every figure and source-data table in the paper.

One entry point for the whole analysis. Order matters only between stages:
``1_Data`` and ``2_Processing`` produce the reusable profile tables, and every
figure folder is a pure consumer of them, so figures can run in any order or
individually.

    python run_all.py --dry-run          # print what would run, touch nothing
    python run_all.py                    # everything, in order
    python run_all.py --figure Fig5      # one figure
    python run_all.py --stage 2_Processing
    python run_all.py --skip 1_Data      # everything except feature sorting
    python run_all.py --verify           # check every panel has source data

Data is expected under ``data/`` — fetch it first with::

    python scripts/download_data.py

Point at data held elsewhere with ``COLOPAINT3D_DATA=/path/to/profiles``.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.paths import (ANALYSIS_ROOT, CLUSTER_CP_RESULTS, DATA_ROOT,  # noqa: E402
                         REPO_ROOT, cellprofiler_results)

# Stages run in this order. Anything in analysis/ not named here is treated as a
# figure folder and run afterwards, alphabetically.
ORDERED_STAGES = ["0_Download", "1_Data", "2_Processing"]

# Folders that hold code but produce no figures on their own.
NON_FIGURE = {"0_Download", "1_Data", "2_Processing", "4_BioImageArchive"}

# Stages that only run when named explicitly (--stage / --figure). 0_Download pulls
# 16.6 GB from the BioImage Archive; that should be a deliberate act, not something a
# bare `python run_all.py` starts.
OPT_IN_STAGES = {"0_Download"}

SKIP_PARTS = {".ipynb_checkpoints", "__pycache__", ".venv"}

# Notebooks that overwrite shipped data tables in place and whose output is not
# bit-reproducible. Skipped by default; --include-destructive runs them anyway.
#
# Prepare_Slice_Features used to be listed here: it rebuilds
# normalized_data_merged_HCT116.csv, and its rebuild keeps 779 selected features where
# the file shipped with the port had 781, which moves Fig 2g's variance-explained
# figures. It now runs by default, because a figure the repo cannot rebuild from its own
# data is the worse problem: the panel is regenerated from data/exp1_main rather than
# inherited. The slice effect is unchanged either way (eta2 0.64 -> 0.05); only the
# percentages move. The superseded 781-feature table is not kept here -- it survives
# upstream at colopaint3D/spher_colo52_v1/1_Data/results/.
DESTRUCTIVE: set[str] = set()

# Notebooks that need input tiers not everyone has, and what to check for. The figure
# tier runs off the profile tables in data/<experiment>/, which are a few hundred MB and
# travel with the release; these need something bigger or something private, so a clone
# that lacks them should skip the notebook with an explanation rather than die inside
# pandas 40 minutes into a run.
#
#   CP_INPUT raw CellProfiler output — either the pharmbio mount or the copy fetched
#            from the BioImage Archive by 0_Download, whichever cellprofiler_results()
#            resolves to.
#   CLUSTER  the same mount, but for the QC / featICF_spheroid tier that the deposit
#            does *not* carry, so a download cannot substitute.
#   FEATURES the ~35 GB per-slice feature dumps under data/features/.
#
# Skipping is not "these panels are unreproducible": the panels downstream of them are
# rebuilt from committed tables. It means the *upstream* step cannot be re-run here.

# notebook -> the experiment whose CellProfiler output it sorts
NEEDS_CP_INPUT = {
    "analysis/1_Data/exp1_main/1_FeatureSorting.ipynb": "exp1_main",
    "analysis/1_Data/exp2_spheroid_size/1_FeatureSorting.ipynb": "exp2_spheroid_size",
    "analysis/1_Data/exp3_clearing_mag_z/1_FeatureSorting.ipynb": "exp3_clearing_mag_z",
    "analysis/1_Data/exp4_objective/1_FeatureSorting.ipynb": "exp4_objective",
}

# These read tiers absent from S-BIAD2254 (per-plate QC tables, featICF_spheroid, and
# the raw image tree), so only the cluster will do.
NEEDS_CLUSTER = {
    "analysis/2_Processing/exp1_main/Pycytominer_MIP.ipynb",
    "analysis/4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb",
}

# notebook -> the experiment whose feature dump it reads
NEEDS_FEATURES = {
    "analysis/2_Processing/exp1_main/2_Pycytominer.ipynb": "exp1_main",
    "analysis/2_Processing/exp1_main/2_Pycytominer_certain_slices.ipynb": "exp1_main",
    "analysis/2_Processing/exp2_spheroid_size/2_Pycytominer.ipynb": "exp2_spheroid_size",
    "analysis/2_Processing/exp3_clearing_mag_z/2_Pycytominer.ipynb": "exp3_clearing_mag_z",
    "analysis/2_Processing/exp4_objective/2_DetectandCombine.ipynb": "exp4_objective",
    "analysis/3_Figure2/CellCoverage/3_CellCoverage.ipynb": "exp1_main",
    "analysis/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb": "exp1_main",
    "analysis/3_Figure2/RemoveNoise/Prepare_Slice_Features.ipynb": "exp1_main",
    "analysis/3_SupplFigure2/error_propegation.ipynb": "exp1_main",
    "analysis/3_SupplFigure3/3_Robustness_Combined_Final.ipynb": "exp1_main",
}


def unavailable(rel: str) -> str | None:
    """Why ``rel`` cannot run here, or None if it can."""
    if rel in NEEDS_CLUSTER and not CLUSTER_CP_RESULTS.is_dir():
        return (f"needs the QC / featICF_spheroid tier under {CLUSTER_CP_RESULTS}, which "
                "S-BIAD2254 does not carry (pharmbio cluster only)")
    exp_cp = NEEDS_CP_INPUT.get(rel)
    if exp_cp is not None:
        src = cellprofiler_results(exp_cp)
        if not src.is_dir():
            return (f"needs raw CellProfiler output; none found at {src}. Fetch it with "
                    "`python run_all.py --stage 0_Download` (16.6 GB), or set "
                    "COLOPAINT3D_CP_RESULTS. The tables it would produce ship in data/")
    exp = NEEDS_FEATURES.get(rel)
    if exp is not None:
        d = DATA_ROOT / "features" / exp
        if not d.is_dir() or not any(d.iterdir()):
            return (f"needs the per-slice feature dump at {d} (~35 GB, not in the "
                    "release; see provenance/DATA_INVENTORY.md)")
    return None

# Notebooks parameterised by cell line and/or data type. Each reads its parameters
# from the environment, defaulting to the value it used to hardcode, so one notebook
# emits every combination its PANEL map promises. Without this the maps offer ten
# panels and a run produces two.
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
    # Fig 4e-f, Fig 5c-d, Suppl 4e-f, Suppl 5b-c. Both dimensions: the clustermap uses
    # the notebook's top-level data_type, and only the 2D-vs-3D difference map further
    # down loops data_type on its own. Sweeping cell_line alone leaves Fig4e and Fig5c
    # unrendered.
    "analysis/3_Figure4/3_PairwiseCorrelations.ipynb": _sweep(_LINES, _TYPES),
    # Fig 3e/3f (loops cell_line internally)
    "analysis/3_Figure3/3_PercentReplicating.ipynb": _sweep(types=("MIP", "aggregates")),
    # Fig 2f + Suppl 1d
    "analysis/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb": _sweep(lines=_LINES),
    # writes grit_data_{data_type}_{cell_line}.parquet, which everything downstream reads
    "analysis/2_Processing/exp1_main/3_GritScores.ipynb": _sweep(_LINES, _TYPES),
    # Suppl 4h, one output per exp4 acquisition (air = bomi, WI = wi)
    # Suppl 4h is air vs WI only: air = bomi, WI = wi. cleared3d is a third exp4
    # acquisition that the published panel does not use.
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
             skip: Iterable[str] = (), include_destructive: bool = False) -> list[Notebook]:
    """Return notebooks to run, in execution order."""
    if not ANALYSIS_ROOT.is_dir():
        return []

    groups: list[str] = []
    present = sorted(p.name for p in ANALYSIS_ROOT.iterdir() if p.is_dir())
    for name in ORDERED_STAGES:
        if name in present:
            groups.append(name)
    groups += [n for n in present if n not in ORDERED_STAGES and n not in NON_FIGURE]

    # Opt-in stages appear only when asked for by name. Kept out of the default run
    # rather than out of ORDERED_STAGES, so --stage 0_Download still finds it and it
    # still sorts ahead of 1_Data when it does run.
    if stage is None:
        groups = [g for g in groups if g not in OPT_IN_STAGES]

    # --skip accepts a stage name (1_Data) or any spelling of a figure folder
    # (SupplFig3 / Figure3 / 3_SupplFigure3), so it reads the same as --figure.
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
            if rel in DESTRUCTIVE and not include_destructive:
                print(f"  (skipping {rel}: overwrites shipped data, see KNOWN_ISSUES)")
                continue
            if (why := unavailable(rel)) is not None:
                print(f"  (skipping {rel}: {why})")
                continue
            for env in SWEEPS.get(rel, [{}]):
                found.append(Notebook(path, group, env))
    return found


def _runner() -> tuple[str, list[str]]:
    """Pick an execution backend, preferring papermill."""
    try:
        import papermill  # noqa: F401

        return "papermill", []
    except ImportError:
        pass
    # sys.executable, not a bare "jupyter": the runner must stay in whatever
    # interpreter invoked it, so `<venv>/bin/python run_all.py` uses that venv.
    if subprocess.run(
        [sys.executable, "-m", "nbconvert", "--version"], capture_output=True
    ).returncode == 0:
        return "nbconvert", []
    raise SystemExit(
        "no notebook runner available. Install one of:\n"
        "    pip install papermill        (preferred)\n"
        "    pip install nbconvert"
    )


def execute(nb: Notebook, backend: str) -> tuple[bool, float, str]:
    """Run one notebook. Returns (ok, seconds, message)."""
    started = time.time()
    # Sweep combinations get distinct executed copies, so one does not overwrite
    # the next and a failure can be traced to the combination that caused it.
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
    # Parameters travel by environment: nbconvert cannot inject cells, and this
    # works identically under papermill.
    env = {**os.environ, **nb.env}
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = time.time() - started
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        return False, elapsed, "\n".join(tail)
    return True, elapsed, ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--figure", help="run one figure, e.g. Fig5 or SupplFig3")
    ap.add_argument("--stage", help="run one stage, e.g. 1_Data or 2_Processing")
    ap.add_argument(
        "--include-destructive", action="store_true",
        help="also run notebooks that overwrite shipped data tables in place "
             "(currently Prepare_Slice_Features; see provenance/KNOWN_ISSUES.md)",
    )
    ap.add_argument(
        "--skip", action="append", default=[], metavar="NAME",
        help="skip a stage or figure folder; repeatable. --skip 1_Data leaves out "
             "feature sorting, which needs the 19.5 GB dumps and rewrites them",
    )
    ap.add_argument("--dry-run", action="store_true", help="print the plan, execute nothing")
    ap.add_argument("--list", action="store_true", help="alias for --dry-run")
    ap.add_argument(
        "--verify", action="store_true",
        help="check every rendered panel has source data, then exit",
    )
    ap.add_argument(
        "--keep-going", action="store_true",
        help="continue after a notebook fails instead of stopping",
    )
    args = ap.parse_args()

    if args.verify:
        from utils.panels import verify_manifest

        problems = verify_manifest()
        if not problems:
            print("source data OK: every rendered panel has a table and a manifest row")
            return 0
        print(f"source-data problems ({len(problems)}):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    notebooks = discover(figure=args.figure, stage=args.stage, skip=args.skip,
                         include_destructive=args.include_destructive)
    if not notebooks:
        print("No notebooks found under analysis/.")
        print("(The analysis code has not been ported into this repo yet — see WP6.)")
        return 0

    dry = args.dry_run or args.list
    print(f"{'Would run' if dry else 'Running'} {len(notebooks)} notebook(s):\n")
    current = None
    for nb in notebooks:
        if nb.group != current:
            current = nb.group
            print(f"  [{current}]")
        print(f"      {nb.label}")
    print()

    if dry:
        print(f"data root: {DATA_ROOT}" + ("" if DATA_ROOT.is_dir() else "  (missing)"))
        return 0

    if not DATA_ROOT.is_dir() or not any(DATA_ROOT.iterdir()):
        print(
            f"warning: {DATA_ROOT} is empty. Notebooks will fail on missing inputs.\n"
            "         Run: python scripts/download_data.py\n",
            file=sys.stderr,
        )

    backend, _ = _runner()
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

    from utils.panels import verify_manifest

    problems = verify_manifest()
    if problems:
        print(f"all notebooks ran, but {len(problems)} source-data problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("done: all notebooks ran and every panel has source data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
