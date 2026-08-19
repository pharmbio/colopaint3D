"""Save a figure panel together with the table it was drawn from.

The rule this enforces: **a panel cannot be published without its source data.**
``save_panel`` writes the rendered panel, the table behind it, and a manifest row
in one call, so there is no way to produce one without the others.

    from utils.panels import save_panel

    save_panel(fig, "Fig5c", data=plotted_df,
               caption="Hierarchical clustering of 2D compound profiles")

That writes:

    figures/Fig5/Fig5c.pdf
    source_data/Fig5c_hierarchical_clustering.csv
    source_data/MANIFEST.csv                     (one row appended)

Panel naming drives everything: ``Fig5c`` -> figure ``Fig5``, panel ``c``.
Supplementary panels use ``SupplFig3a``.

The target figure comes from the panel name, so one parameterised notebook can
write into Fig4, Fig5 and SupplFig5 without per-figure bookkeeping.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from utils.paths import SOURCE_DATA_ROOT, figdir

__all__ = ["save_panel", "panel_figure", "MANIFEST", "verify_manifest"]

MANIFEST = SOURCE_DATA_ROOT / "MANIFEST.csv"
MANIFEST_FIELDS = [
    "panel", "figure", "source_data", "figure_files", "notebook", "n_rows", "caption", "written_utc",
]

# "Fig5c" -> ("Fig5", "c");  "SupplFig3a" -> ("SupplFig3", "a")
# A trailing "_part" covers a panel assembled from more than one file, e.g. Fig 5f
# is the 2D and 3D fingerprint clustermaps side by side: "Fig5f_2D", "Fig5f_3D".
_PANEL_RE = re.compile(
    r"^(?P<figure>(?:Suppl)?Fig\d+)(?P<panel>[A-Za-z]\d?)?(?P<part>_[A-Za-z0-9_]+)?$"
)

# PDF only: vector, editable text, and what the figure assembly actually consumes.
# Pass formats=("pdf", "png") on a call that also needs a raster preview.
DEFAULT_FORMATS = ("pdf",)


def apply_figure_defaults() -> None:
    """Keep vector text editable so panels can be assembled downstream.

    Type-42 embedding keeps PDF text selectable in Illustrator/Inkscape instead of
    outlined. Set before every save, since ``plt.style.use`` or ``seaborn.set_theme``
    would otherwise reset it.
    """
    import matplotlib as mpl

    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["svg.fonttype"] = "none"


def panel_figure(panel: str) -> str:
    """Return the figure a panel belongs to. ``"Fig5c"`` -> ``"Fig5"``."""
    m = _PANEL_RE.match(panel)
    if not m:
        raise ValueError(
            f"panel name {panel!r} not understood; expected e.g. 'Fig5c', 'SupplFig3a', 'Fig6e'"
        )
    return m.group("figure")


def _slug(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z]+", "_", text.strip().lower())
    return re.sub(r"_+", "_", text).strip("_")


def _write_table(data: Any, dest: Path) -> tuple[int, bool]:
    """Write ``data`` to ``dest`` as CSV; return (row count, content changed).

    Accepts a DataFrame/Series, a column mapping, or an iterable of dicts. Duck-typed,
    so pandas is not imported at module load.

    Writes via a temporary file and replaces ``dest`` only when the bytes differ, so a
    re-run that reproduces a table leaves its mtime alone.
    """
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        n_rows = _render_table(data, tmp)
        changed = not (dest.exists() and dest.read_bytes() == tmp.read_bytes())
        if changed:
            tmp.replace(dest)
        return n_rows, changed
    finally:
        tmp.unlink(missing_ok=True)


def _render_table(data: Any, dest: Path) -> int:
    """Write ``data`` to ``dest`` as CSV; return the number of data rows."""
    if hasattr(data, "to_csv"):
        frame = data
        if getattr(frame, "ndim", 2) == 1 and hasattr(frame, "to_frame"):
            frame = frame.to_frame()
        # Keep the index only when it carries information: named, or non-RangeIndex.
        index = frame.index
        keep_index = bool(
            getattr(index, "name", None)
            or getattr(index, "names", [None]) != [None]
            or type(index).__name__ != "RangeIndex"
        )
        frame.to_csv(dest, index=keep_index)
        return int(frame.shape[0])

    if isinstance(data, dict):
        keys = list(data)
        length = len(next(iter(data.values()))) if data else 0
        rows = [{k: data[k][i] for k in keys} for i in range(length)]
    elif isinstance(data, Iterable):
        rows = [dict(r) for r in data]
    else:
        raise TypeError(f"cannot write source data of type {type(data).__name__}")

    if not rows:
        raise ValueError("refusing to write an empty source-data table")
    with dest.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _append_manifest(row: dict, *, table_changed: bool = True) -> None:
    """Replace this panel's manifest row, keeping the file sorted by panel.

    ``written_utc`` is preserved when nothing else changed, so a clean ``git status``
    after a run means it reproduced exactly and any diff is real drift.
    """
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    previous: dict | None = None
    if MANIFEST.exists():
        with MANIFEST.open(newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("panel") == row["panel"]:
                    previous = r
                else:
                    existing.append(r)

    if previous is not None and not table_changed:
        same = all(previous.get(f) == row[f] for f in MANIFEST_FIELDS if f != "written_utc")
        if same:
            row = {**row, "written_utc": previous["written_utc"]}

    with MANIFEST.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for prev in sorted(existing + [row], key=lambda r: r["panel"]):
            writer.writerow(prev)


def save_panel(
    fig,
    panel: str,
    data: Any,
    caption: str | None = None,
    notebook: str | None = None,
    formats: Iterable[str] = DEFAULT_FORMATS,
    slug: str | None = None,
    dpi: int = 300,
) -> dict:
    """Write a panel, its source table, and a manifest row.

    Parameters
    ----------
    fig
        A matplotlib ``Figure``.
    panel
        Paper panel name, e.g. ``"Fig5c"``. Determines the output figure folder.
    data
        The table actually plotted — a DataFrame, Series, column mapping, or list
        of dicts. Required: this is the point of the function.
    caption
        Short description, recorded in the manifest and used for the table's
        filename slug.
    notebook
        Where this panel came from; recorded for traceability.

    Returns the manifest row that was written.
    """
    if data is None:
        raise ValueError(
            f"{panel}: source data is required. Pass the dataframe you plotted so the "
            "panel ships with its table."
        )

    figure = panel_figure(panel)
    # Named for the panel alone: source_data/Fig5c.csv. The description lives in the
    # manifest's caption column.
    table_path = SOURCE_DATA_ROOT / f"{panel}.csv"
    SOURCE_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    n_rows, table_changed = _write_table(data, table_path)

    apply_figure_defaults()
    out_dir = figdir(figure)
    written: list[str] = []
    for ext in formats:
        dest = out_dir / f"{panel}.{ext}"
        fig.savefig(dest, dpi=dpi, bbox_inches="tight")
        written.append(dest.name)

    row = {
        "panel": panel,
        "figure": figure,
        "source_data": table_path.name,
        "figure_files": ";".join(written),
        "notebook": notebook or "",
        "n_rows": str(n_rows),
        "caption": caption or "",
        "written_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _append_manifest(row, table_changed=table_changed)
    print(f"[save_panel] {panel} -> {table_path.name} ({n_rows} rows), {', '.join(written)}")
    return row


def verify_manifest() -> list[str]:
    """Return a list of problems: panels missing tables, figures missing rows.

    Runs at the end of ``run_all.py``, so the claim "every panel has source data" is
    testable rather than asserted.
    """
    problems: list[str] = []
    if not MANIFEST.exists():
        return ["source_data/MANIFEST.csv does not exist — no panels recorded"]

    with MANIFEST.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    recorded_figure_files: set[str] = set()
    for row in rows:
        table = SOURCE_DATA_ROOT / row["source_data"]
        if not table.exists():
            problems.append(f"{row['panel']}: manifest lists {row['source_data']} but it is missing")
        for fname in filter(None, row["figure_files"].split(";")):
            path = figdir(row["figure"]) / fname
            recorded_figure_files.add(str(path))
            if not path.exists():
                problems.append(f"{row['panel']}: figure file {fname} is missing")

    # The reverse direction: a rendered panel with no manifest row would ship
    # without source data.
    from utils.paths import FIGURES_ROOT

    if FIGURES_ROOT.is_dir():
        for path in FIGURES_ROOT.rglob("*.pdf"):
            if ".ipynb_checkpoints" in path.parts:
                continue          # Jupyter's own copies, not outputs
            try:
                panel_figure(path.stem)
            except ValueError:
                continue          # not a panel name: a notebook's own extra output
            if str(path) not in recorded_figure_files:
                problems.append(f"{path.relative_to(FIGURES_ROOT)}: rendered but has no MANIFEST row")
    return problems
