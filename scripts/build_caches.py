#!/usr/bin/env python3
"""Precompute the small tables that let feature-dump-dependent panels still run.

Suppl 3g/3h and Suppl 2e read the 19.5 GB of ``FeaturesImages_*`` dumps and the
519 MB expert-annotation CellProfiler output. Those are outside every download
tier, so the aggregation each panel actually plots is computed once here and
committed as a small CSV. The panels then plot from the cache, and the whole
figure set regenerates from the 147 MB profile download.

The aggregation logic is lifted verbatim from the notebooks — this script is a
runner, not a reimplementation.

    python scripts/build_caches.py --list
    python scripts/build_caches.py suppl3g suppl3h
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.paths import external, features  # noqa: E402

OUT_S3 = Path(__file__).resolve().parents[1] / "analysis" / "3_SupplFigure3" / "data"
OUT_S2 = Path(__file__).resolve().parents[1] / "analysis" / "3_SupplFigure2" / "data"

# From 3_Robustness_Combined_Final cell 1, complete. (An earlier truncated copy of
# this dict silently produced a cache missing the 20_40 and noclear conditions.)
IMG2COND = {8787: "nyquist", 8804: "nyquist", 8780: "double_dens", 8799: "double_dens",
            8783: "37C", 8802: "37C", 8793: "noclear", 8795: "noclear",
            8789: "20_40", 8791: "20_40", 8797: "20_40",
            8827: "10x", 8831: "10x", 8825: "40x", 8829: "40x"}

# From cell 16.
COMP = {"HOECHST": "nuclei", "MITO": "cells", "CONC": "cells",
        "PHAandWGA": "cells", "SYTO": "cells"}


def slice_perwell(folder, comp_map, img2cond=None, cond=None):
    """Verbatim from 3_Robustness_Combined_Final cell 16."""
    fs = sorted(glob.glob(f"{folder}/HCT116_Slice*MedianAgg.parquet"),
                key=lambda p: int(re.search(r"Slice(\d+)", p).group(1)))
    chcols = {ch: f"Intensity_MeanIntensity_{ch}_{comp}" for ch, comp in comp_map.items()}
    perch = {ch: {} for ch in comp_map}
    for f in fs:
        sidx = int(re.search(r"Slice(\d+)", f).group(1))
        d = pd.read_parquet(f)
        avail = d.columns
        d = d[d["Metadata_cmpdname"] == "dmso"]
        if img2cond is not None:
            d = d[d["Metadata_image_id"].map(img2cond) == cond]
        if len(d) == 0:
            continue
        d = d.copy()
        d["wid"] = d["Metadata_Barcode"].astype(str) + "_" + d["Metadata_Well"].astype(str)
        for ch, cc in chcols.items():
            if cc in avail:
                perch[ch][sidx] = d.groupby("wid")[cc].median()
    return {ch: pd.DataFrame(perch[ch]).T.sort_index() for ch in comp_map if perch[ch]}


def build_suppl3g() -> Path:
    """Per-slice, per-well median channel intensity — the input to panel g."""
    v3_slice = features("exp3_clearing_mag_z", "150526", "SingleSlice")
    v1_slice = features("exp1_main", "011225", "SingleSlice")
    frames = []
    for label, folder, kw in (("nyquist", v3_slice, dict(img2cond=IMG2COND, cond="nyquist")),
                              ("v1", v1_slice, {})):
        per = slice_perwell(str(folder), COMP, **kw)
        for ch, df in per.items():
            long = (df.rename_axis("slice").reset_index()
                      .melt(id_vars="slice", var_name="wid", value_name="median_intensity"))
            long.insert(0, "source", label)
            long.insert(1, "channel", ch)
            frames.append(long)
        print(f"  {label}: {len(per)} channels, slices {sorted(next(iter(per.values())).index)[:3]}...")
    out = pd.concat(frames, ignore_index=True).dropna(subset=["median_intensity"])
    dest = OUT_S3 / "suppl3g_bleaching_perwell.csv"
    OUT_S3.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"  wrote {dest.name}: {len(out):,} rows")
    return dest


def build_suppl3h() -> Path:
    """Objects detected per z-plane per well — the input to panel h."""
    v3_sc = features("exp3_clearing_mag_z", "150526", "SingleCell", "HCT116.parquet")
    v1_sc = features("exp1_main", "011225", "SingleCell", "HCT116.parquet")

    sc = pd.read_parquet(v3_sc, columns=["Metadata_image_id", "Metadata_cmpdname",
                                         "Metadata_z", "Metadata_Well_nuclei", "Metadata_Barcode"])
    sc["cond"] = sc["Metadata_image_id"].map(IMG2COND)
    sc["wid"] = sc["Metadata_Barcode"].astype(str) + "_" + sc["Metadata_Well_nuclei"].astype(str)
    dm = sc[sc["Metadata_cmpdname"] == "dmso"]
    Z14 = list(np.linspace(0, 43, 14).round().astype(int))

    rows = []
    for cond in ["20_40", "noclear", "nyquist"]:
        s = dm[dm["cond"] == cond]
        if cond == "nyquist":
            s = s[s["Metadata_z"].isin(Z14)]
        if not len(s):
            print(f"  {cond}: no rows (condition absent from this dump)")
            continue
        g = s.groupby(["Metadata_z", "wid"]).size().rename("n_objects").reset_index()
        g.insert(0, "cond", cond)
        g = g.rename(columns={"Metadata_z": "z"})
        rows.append(g)
        print(f"  {cond}: {g['wid'].nunique()} wells, {g['z'].nunique()} z-planes")

    v1sc = pd.read_parquet(v1_sc, columns=["Metadata_Site", "Metadata_cmpdname",
                                           "Metadata_Barcode", "Metadata_Well", "Metadata_cell_line"])
    v1dm = v1sc[(v1sc["Metadata_cell_line"] == "HCT116") & (v1sc["Metadata_cmpdname"] == "dmso")].copy()
    v1dm["wid"] = v1dm["Metadata_Barcode"].astype(str) + "_" + v1dm["Metadata_Well"].astype(str)
    g = v1dm.groupby(["Metadata_Site", "wid"]).size().rename("n_objects").reset_index()
    g.insert(0, "cond", "v1")
    g = g.rename(columns={"Metadata_Site": "z"})
    rows.append(g)
    print(f"  v1: {g['wid'].nunique()} wells, {g['z'].nunique()} z-planes")

    out = pd.concat(rows, ignore_index=True)
    dest = OUT_S3 / "suppl3h_detection_perwell.csv"
    OUT_S3.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"  wrote {dest.name}: {len(out):,} rows")
    return dest


def _exec_notebook_until(nb_path: Path, ready, label: str) -> dict:
    """Run a notebook's code cells in order until ``ready(ns)`` is true.

    Used instead of reimplementing the aggregation: these panels depend on
    helper functions and intermediate frames defined across many earlier cells,
    so executing the notebook is the only way to be sure the cached table is
    what the notebook actually produces.
    """
    import json as _json
    import os as _os

    ns: dict = {"__name__": "__cache_build__"}
    nb = _json.loads(nb_path.read_text())
    cwd = _os.getcwd()
    _os.chdir(nb_path.parent)          # the notebooks resolve ROOT from cwd
    try:
        for i, c in enumerate(nb.get("cells", [])):
            if c.get("cell_type") != "code":
                continue
            src = "".join(c.get("source", []))
            src = "\n".join("" if l.strip().startswith(("%", "!", "?")) else l
                             for l in src.split("\n"))
            if not src.strip():
                continue
            try:
                exec(compile(src, f"<{label} cell {i}>", "exec"), ns)
            except Exception as exc:                      # noqa: BLE001
                print(f"  cell {i} raised {type(exc).__name__}: {exc}")
                raise
            if ready(ns):
                print(f"  reached the target frame after cell {i}")
                return ns
    finally:
        _os.chdir(cwd)
    raise RuntimeError(f"{label}: target frame never appeared")


def build_similarities() -> Path:
    """Pairwise 2D and 3D compound similarity — the input Suppl 5e needs.

    ``similarities_2D.csv`` exists only on a laptop; the 3D matrix survives as
    3_Figure4/PairwiseCorrelations/similarities.csv. Both are regenerated here
    from the committed profiles, and the 3D one is checked against the survivor.
    """
    repo = Path(__file__).resolve().parents[1]
    nb = repo / "analysis" / "3_Figure4" / "3_PairwiseCorrelations.ipynb"
    ns = _exec_notebook_until(
        nb,
        lambda n: isinstance(n.get("sim"), dict) and {"2D", "aggregates"} <= set(n["sim"]),
        "PairwiseCorrelations")

    sim = ns["sim"]
    out_dir = repo / "analysis" / "3_SupplFigure5" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, name in (("2D", "similarities_2D.csv"), ("aggregates", "similarities_3D.csv")):
        d = sim[key][["Drug1", "Drug2", "Similarity"]].copy()
        d.to_csv(out_dir / name, index=False)
        written.append((name, len(d), d["Drug1"].append(d["Drug2"]).nunique()
                        if hasattr(d["Drug1"], "append") else
                        pd.concat([d["Drug1"], d["Drug2"]]).nunique()))
        print(f"  wrote {name}: {len(d)} pairs")

    # validate the regenerated 3D matrix against the surviving original
    orig = external("spher_colo52_v1/3_Figure4/PairwiseCorrelations/similarities.csv")
    if orig.exists():
        a = pd.read_csv(orig)[["Drug1", "Drug2", "Similarity"]]
        b = pd.read_csv(out_dir / "similarities_3D.csv")
        key = lambda d: d.apply(lambda r: tuple(sorted([r.Drug1, r.Drug2])), axis=1)
        a["k"], b["k"] = key(a), key(b)
        m = a.merge(b, on="k", suffixes=("_orig", "_new"))
        if len(m):
            diff = (m["Similarity_orig"] - m["Similarity_new"]).abs()
            print(f"  validation vs surviving similarities.csv: {len(m)}/{len(a)} pairs matched, "
                  f"max |diff| = {diff.max():.3g}")
        else:
            print("  validation: no pairs matched the surviving file (naming differs)")
    else:
        print(f"  validation skipped: {orig} not found")
    return out_dir / "similarities_2D.csv"


def build_suppl2e() -> Path:
    """Per-plane feature correlation vs depth — the input to Suppl 2e."""
    repo = Path(__file__).resolve().parents[1]
    nb = repo / "analysis" / "3_SupplFigure2" / "error_propegation.ipynb"
    ns = _exec_notebook_until(nb, lambda n: "df_corr_plane" in n, "error_propegation")
    d = ns["df_corr_plane"]
    dest = OUT_S2 / "error_propagation_cached.csv"
    OUT_S2.mkdir(parents=True, exist_ok=True)
    d.to_csv(dest, index=False)
    print(f"  wrote {dest.name}: {len(d):,} rows, columns {list(d.columns)}")
    return dest


BUILDERS = {"suppl3g": build_suppl3g, "suppl3h": build_suppl3h,
            "similarities": build_similarities, "suppl2e": build_suppl2e}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", choices=sorted(BUILDERS) + [[]], default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for k in BUILDERS:
            print(f"  {k}")
        return 0
    names = sorted(BUILDERS) if args.all else args.names
    if not names:
        ap.error("give names, or --all, or --list")
    for n in names:
        print(f"[{n}]")
        BUILDERS[n]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
