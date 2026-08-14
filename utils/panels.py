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
Supplementary panels use ``SupplFig3a``. This generalises a convention already
present upstream (``panel_source_data.csv``, ``Figure3A2B2_n_per_condition.csv``).

Note on multi-figure notebooks: several notebooks are parameterised by
``data_type`` and emit panels into more than one figure. Because the target
figure is derived from the panel name, one notebook can write into Fig4, Fig5
and SupplFig5 without any per-figure bookkeeping.
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
    r"^(?P<figure>(?:Suppl)?Fig\d+)(?P<panel>[A-Za-z]\d?)?(?P<part>_[A-Za-z0-9]+)?$"
)

# PDF only: vector, editable text, and what the figure assembly actually consumes.
# Pass formats=("pdf", "png") on a call that also needs a raster preview.
DEFAULT_FORMATS = ("pdf",)


def apply_figure_defaults() -> None:
    """Keep vector text editable so panels can be assembled downstream.

    Type-42 (TrueType) embedding means the text in exported PDFs stays selectable
    and editable in Illustrator/Inkscape rather than being converted to outlines.
    Set immediately before every save, because a notebook that calls
    ``plt.style.use`` or ``seaborn.set_theme`` after import would otherwise reset it.
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


def _write_table(data: Any, dest: Path) -> int:
    """Write ``data`` to ``dest`` as CSV; return the number of data rows.

    Accepts a pandas DataFrame/Series, a mapping of columns, or an iterable of
    dicts, so notebooks do not have to normalise before saving. Duck-typed rather
    than importing pandas at module load, so a plain list of dicts also works.
    """
    if hasattr(data, "to_csv"):
        frame = data
        if getattr(frame, "ndim", 2) == 1 and hasattr(frame, "to_frame"):
            frame = frame.to_frame()
        # Keep the index only when it carries information a reader would need:
        # a named index, or any non-default (non-RangeIndex) index such as
        # compound names or a MultiIndex. A bare RangeIndex is just row numbers.
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


def _append_manifest(row: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if MANIFEST.exists():
        with MANIFEST.open(newline="") as fh:
            existing = [r for r in csv.DictReader(fh) if r.get("panel") != row["panel"]]
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
    name_slug = slug or (_slug(caption) if caption else "source_data")
    table_path = SOURCE_DATA_ROOT / f"{panel}_{name_slug}.csv"
    SOURCE_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    n_rows = _write_table(data, table_path)

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
    _append_manifest(row)
    print(f"[save_panel] {panel} -> {table_path.name} ({n_rows} rows), {', '.join(written)}")
    return row


def verify_manifest() -> list[str]:
    """Return a list of problems: panels missing tables, figures missing rows.

    Used by ``run_all.py --verify`` and by the submission check, so the claim
    "every panel has source data" is testable rather than asserted.
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
    # without source data, which is exactly what this repo exists to prevent.
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
