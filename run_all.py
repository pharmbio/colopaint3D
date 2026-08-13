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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.paths import ANALYSIS_ROOT, DATA_ROOT, REPO_ROOT  # noqa: E402

# Stages run in this order. Anything in analysis/ not named here is treated as a
# figure folder and run afterwards, alphabetically.
ORDERED_STAGES = ["1_Data", "2_Processing"]

# Folders that hold code but produce no figures on their own.
NON_FIGURE = {"1_Data", "2_Processing", "4_BioImageArchive"}

SKIP_PARTS = {".ipynb_checkpoints", "__pycache__", ".venv"}


class Notebook:
    """A notebook to execute, with the group it belongs to."""

    def __init__(self, path: Path, group: str):
        self.path = path
        self.group = group

    @property
    def rel(self) -> str:
        return self.path.relative_to(REPO_ROOT).as_posix()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notebook {self.rel}>"


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


def discover(figure: str | None = None, stage: str | None = None) -> list[Notebook]:
    """Return notebooks to run, in execution order."""
    if not ANALYSIS_ROOT.is_dir():
        return []

    groups: list[str] = []
    present = sorted(p.name for p in ANALYSIS_ROOT.iterdir() if p.is_dir())
    for name in ORDERED_STAGES:
        if name in present:
            groups.append(name)
    groups += [n for n in present if n not in ORDERED_STAGES and n not in NON_FIGURE]

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
            found.append(Notebook(path, group))
    return found


def _runner() -> tuple[str, list[str]]:
    """Pick an execution backend, preferring papermill."""
    try:
        import papermill  # noqa: F401

        return "papermill", []
    except ImportError:
        pass
    if subprocess.run(
        ["jupyter", "nbconvert", "--version"], capture_output=True
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
    out = nb.path.with_suffix(".executed.ipynb")
    if backend == "papermill":
        cmd = ["papermill", str(nb.path), str(out), "--cwd", str(nb.path.parent), "--log-output"]
    else:
        cmd = [
            "jupyter", "nbconvert", "--to", "notebook", "--execute",
            f"--output={out.name}", str(nb.path),
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
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

    notebooks = discover(figure=args.figure, stage=args.stage)
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
        print(f"      {nb.rel}")
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
        print(f"[{i}/{len(notebooks)}] {nb.rel} ... ", end="", flush=True)
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
            print(f"  - {nb.rel}", file=sys.stderr)
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
