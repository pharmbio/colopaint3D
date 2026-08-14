"""
Panel C/E: 2D-vs-3D Cell Painting similarity scatter, coloured by MoA PAIR CLASS.

Reconstruction of the earlier MoA-pair-class-coloured version of panel C
(the "Drug pair similarity: 2D vs 3D" figure). The on-disk 09_panel_c_recolor.py
was edited in place into a cycling-dependence recolour and the MoA-class source
was lost; this rebuilds it from the drug->MoA map in 06_analyze_similarity.py and
the scatter/boxplot layout in 09.

Each point = one drug pair.
  x = cosine similarity in 2D Cell Painting
  y = cosine similarity in 3D Cell Painting (spheroid, scAgg)
Diagonal y=x; above = more similar in 3D, below = more similar in 2D.

Pair-class legend (matches the uploaded panel E):
  MAPK x MAPK
  Antimetabolite x Antimetabolite
  Antimetabolite x PARPi
  Antimetabolite x MDM2i / Topo I
  Other

USAGE
-----
    python 09b_panel_c_moa_class.py \
        --sim2d   /path/to/similarities_2D.csv \
        --sim3d   /path/to/similarities.csv \
        --outdir  /Users/chrri621/Desktop/Spheroid-Drug-Screen

Both CSVs need columns: Drug1, Drug2, Similarity (pair order irrelevant; canonicalised).
NOTE: similarities.csv in this repo is the 3D spheroid matrix. The 2D matrix is not
in the connected folder -- supply it via --sim2d. Without it the script exits with a
clear message rather than guessing.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- repo path bootstrap (added when porting into colopaint3D_paper) ---
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'utils' / 'paths.py').is_file())
sys.path.insert(0, str(ROOT))
from utils.panels import save_panel
DATA = ROOT / 'analysis' / '3_SupplFigure5' / 'data'
from matplotlib.lines import Line2D
from scipy.stats import spearmanr


# ---------------------------------------------------------------------------
# Drug code -> MoA class  (verbatim from 06_analyze_similarity.py)
# ---------------------------------------------------------------------------
MOA = {
    "5Z-7-": "TAK1 inh", "AMG23": "MDM2 inh (p53 reactivator)",
    "AZD45": "FGFR inh", "AZD77": "CHK1/2 inh", "AZD80": "mTOR inh (kinase)",
    "Adavo": "WEE1 inh", "Afati": "EGFR/HER2 TKI", "Alpel": "PI3Ka inh",
    "BMS-7": "IGF1R/IR inh", "Binim": "MEK1/2 inh", "Borte": "Proteasome inh",
    "Cobim": "MEK1/2 inh", "Crizo": "ALK/MET/ROS1 TKI", "Dabra": "BRAF V600E inh",
    "Encor": "BRAF V600E inh", "Fluor": "Antimetabolite (TS inh)", "Gefit": "EGFR TKI",
    "Gemci": "Antimetabolite (RNR/dCK)", "MK-22": "AKT inh (allosteric)",
    "Nutli": "MDM2 inh (p53 reactivator)", "Olapa": "PARP inh",
    "Oxali": "Pt DNA crosslinker", "PD032": "MEK1/2 inh", "PI-10": "PI3K/mTOR inh (dual)",
    "Pacli": "Microtubule stabilizer", "Palbo": "CDK4/6 inh", "Regor": "Multi-kinase TKI",
    "SB505": "TGFbR / ALK4-5-7 inh", "SN-38": "Topoisomerase I inh",
    "Soraf": "Multi-kinase TKI (RAF)", "Tanes": "HSP90 inh", "Tasel": "PI3K inh",
    "Trame": "MEK1/2 inh", "Trifl": "Antimetabolite (TS/incorp.)", "Velip": "PARP inh",
    "Vinor": "Microtubule destabilizer", "Vorin": "HDAC inh", "abema": "CDK4/6 inh",
}

# Collapse MoA -> the coarse buckets the legend uses
MAPK_MOAS = {"MEK1/2 inh", "BRAF V600E inh", "Multi-kinase TKI (RAF)",
             "Multi-kinase TKI", "TAK1 inh"}

def bucket(moa):
    if moa in MAPK_MOAS:                              return "MAPK"
    if moa.startswith("Antimetabolite"):             return "Antimetabolite"
    if moa == "PARP inh":                            return "PARPi"
    if moa.startswith("MDM2 inh"):                   return "MDM2i/TopoI"
    if moa == "Topoisomerase I inh":                 return "MDM2i/TopoI"
    return "Other"

def pair_class(c1, c2):
    b = {bucket(MOA.get(c1, "Other")), bucket(MOA.get(c2, "Other"))}
    if b == {"MAPK"}:                            return "MAPK x MAPK"
    if b == {"Antimetabolite"}:                  return "Antimetabolite x Antimetabolite"
    if b == {"Antimetabolite", "PARPi"}:         return "Antimetabolite x PARPi"
    if b == {"Antimetabolite", "MDM2i/TopoI"}:   return "Antimetabolite x MDM2i / Topo I"
    return "Other"

PAIR_COLOURS = {
    "MAPK x MAPK":                       "#7f7f7f",  # gray
    "Antimetabolite x Antimetabolite":   "#2c7bb6",  # blue
    "Antimetabolite x PARPi":            "#fdae61",  # orange
    "Antimetabolite x MDM2i / Topo I":   "#d7301f",  # red
    "Other":                             "#cfcfcf",  # light gray, background
}
PLOT_ORDER = ["Other", "MAPK x MAPK", "Antimetabolite x Antimetabolite",
              "Antimetabolite x PARPi", "Antimetabolite x MDM2i / Topo I"]

# Pairs labelled on the uploaded panel E
HIGHLIGHT_PAIRS = [
    ("Nutli", "Trifl"), ("Gemci", "SN-38"), ("AMG23", "Fluor"),
    ("SN-38", "Trifl"), ("Fluor", "SN-38"), ("Olapa", "Trifl"),
    ("Fluor", "Olapa"),
]


def canon(d1, d2):
    return (d1, d2) if d1 <= d2 else (d2, d1)

def load_sim(path, label):
    p = Path(path)
    if not p.exists():
        sys.exit(f"ERROR: {label} similarity file not found: {path}\n"
                 f"       The 2D matrix is not in the connected folder. Supply it with --sim2d.")
    df = pd.read_csv(p)
    if not {"Drug1", "Drug2", "Similarity"}.issubset(df.columns):
        sys.exit(f"ERROR: {label} file must have columns Drug1, Drug2, Similarity. Got {list(df.columns)}")
    df = df[["Drug1", "Drug2", "Similarity"]].copy()
    cc = df.apply(lambda r: canon(r.Drug1, r.Drug2), axis=1)
    df["Drug1"] = [c[0] for c in cc]
    df["Drug2"] = [c[1] for c in cc]
    return (df.drop_duplicates(["Drug1", "Drug2"])
              .rename(columns={"Similarity": f"sim_{label}"}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim2d", default=str(DATA / "similarities_2D.csv"))
    ap.add_argument("--sim3d", default=str(DATA / "similarities_3D.csv"))
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--label-all", action="store_true", help="label every pair (crowded)")
    args = ap.parse_args(argv)

    d2 = load_sim(args.sim2d, "2D")
    d3 = load_sim(args.sim3d, "3D")
    pairs = pd.merge(d2, d3, on=["Drug1", "Drug2"], how="inner")
    if pairs.empty:
        sys.exit("ERROR: no pairs in common between the 2D and 3D files after canonicalising codes.")
    pairs["pair_class"] = pairs.apply(lambda r: pair_class(r.Drug1, r.Drug2), axis=1)

    rho, p = spearmanr(pairs.sim_2D, pairs.sim_3D)

    fig, ax = plt.subplots(figsize=(7.2, 7))
    # Both axes start at 0.2 (author's call). Pairs below that are outside the
    # plotted range and are not drawn; n dropped is reported below.
    lo = 0.2
    hi = max(pairs.sim_2D.max(), pairs.sim_3D.max()) + 0.05

    # diagonal + decoupling guide lines
    ax.plot([lo, hi], [lo, hi], ls="--", lw=0.8, color="0.4", zorder=1)
    ax.plot([lo, hi - 0.15], [lo + 0.15, hi], ls=":", lw=0.6, color="0.7", zorder=1)
    ax.plot([lo + 0.15, hi], [lo, hi - 0.15], ls=":", lw=0.6, color="0.7", zorder=1)
    ax.annotate("more similar in 3D", xy=(0.18, 0.42), xycoords="axes fraction",
                rotation=45, color="0.55", fontsize=9, ha="center")
    ax.annotate("more similar in 2D", xy=(0.30, 0.30), xycoords="axes fraction",
                rotation=45, color="0.55", fontsize=9, ha="center")

    for cls in PLOT_ORDER:
        sub = pairs[pairs.pair_class == cls]
        if sub.empty:
            continue
        is_other = cls == "Other"
        ax.scatter(sub.sim_2D, sub.sim_3D, c=PAIR_COLOURS[cls],
                   s=18 if is_other else 40,
                   alpha=0.30 if is_other else 0.9,
                   edgecolors="none" if is_other else "black",
                   linewidths=0 if is_other else 0.4,
                   zorder=2 if is_other else 3)

    # highlight-pair labels
    for a, b in HIGHLIGHT_PAIRS:
        a, b = canon(a, b)
        row = pairs[(pairs.Drug1 == a) & (pairs.Drug2 == b)]
        if len(row):
            x, y = float(row.iloc[0].sim_2D), float(row.iloc[0].sim_3D)
            ax.annotate(f"{a} / {b}", xy=(x, y), xytext=(6, 6),
                        textcoords="offset points", fontsize=8, color="#b3471a",
                        arrowprops=dict(arrowstyle="-", lw=0.4, color="#b3471a"), zorder=10)

    if args.label_all:
        for _, r in pairs.iterrows():
            ax.annotate(f"{r.Drug1}/{r.Drug2}", xy=(r.sim_2D, r.sim_3D), fontsize=4, alpha=0.5)

    ax.set_xlabel("Cosine similarity (2D)", fontsize=11)
    ax.set_ylabel("Cosine similarity (3D) scAgg", fontsize=11)
    ax.set_title("Drug pair similarity: 2D vs 3D", fontsize=13)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    _clipped = pairs[(pairs.sim_2D < lo) | (pairs.sim_3D < lo)]
    if len(_clipped):
        print(f"axis limits clip {len(_clipped)} of {len(pairs)} pairs below {lo}")
    ax.axhline(0, color="0.85", lw=0.6); ax.axvline(0, color="0.85", lw=0.6)
    ax.axhline(0.5, color="0.85", lw=0.6, ls="--"); ax.axvline(0.5, color="0.85", lw=0.6, ls="--")

    handles = [Line2D([0], [0], marker="o", ls="", markerfacecolor=PAIR_COLOURS[c],
                      markeredgecolor="black" if c != "Other" else "none",
                      markersize=7, label=c) for c in
               ["MAPK x MAPK", "Antimetabolite x Antimetabolite",
                "Antimetabolite x PARPi", "Antimetabolite x MDM2i / Topo I", "Other"]]
    ax.legend(handles=handles, title="Drug pair class", loc="lower right",
              fontsize=8, title_fontsize=9, frameon=True, framealpha=0.95)

    fig.tight_layout()
    save_panel(fig, "SupplFig5e", data=pairs.sort_values("pair_class"),
               caption="Drug-pair similarity 2D vs 3D, coloured by MoA pair class",
               notebook="analysis/3_SupplFigure5/3_SupplFig5e_moa_class.ipynb")
    out = Path(args.outdir) if args.outdir else None
    print(f"n pairs: {len(pairs)}  Spearman rho(2D,3D) = {rho:.3f} (p={p:.2e})")
    print("Class counts:\n", pairs.pair_class.value_counts().to_string())


if __name__ == "__main__":
    main()
