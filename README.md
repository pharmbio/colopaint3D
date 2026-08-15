# Cell Painting in 3D spheroids — paper analysis

Analysis code for **"High-content morphological profiling by Cell Painting in 3D
spheroids."** Adaptive spheroid detection and z-placement at acquisition, per-slice
feature extraction and normalisation, and a comparison of what 3D recovers relative to 2D
and to maximum-intensity projections.

## Quick start

```bash
python3.10 -m venv .venv                # Python 3.10; numba/llvmlite need it
source .venv/bin/activate
pip install -r requirements.txt         # no package to install; utils/ is imported directly

python scripts/download_data.py         # profile tables, 206 MB, SHA256-verified
python run_all.py                       # every figure and source-data table
```

`requirements.txt` is the only install path, and holds only what a paper panel needs.

Useful variants:

```bash
python run_all.py --dry-run                    # what would run, touching nothing
python run_all.py --figure Fig5                # also Figure5 or 3_Figure5
python run_all.py --verify                     # panels ↔ manifest ↔ source tables
python scripts/check_panels_nonblank.py        # and that none is an empty page

python scripts/download_data.py --include-normalized   # +306 MB, Figure 2g only
COLOPAINT3D_DATA=/mnt/big/profiles python run_all.py   # data held elsewhere
```

Everything comes from BioImage Archive accession **S-BIAD2254**. The figures never read
images or raw CellProfiler output, only the processed tables, so the download above is
enough. Re-deriving those tables needs the 16.6 GB CellProfiler tier
(`python run_all.py --stage 0_Download`, deliberately excluded from a bare run) and the
19.5 GB per-slice feature dumps. Notebooks whose input tier is absent are skipped with an
explanation naming it.

## Layout

```
run_all.py       Single entry point
utils/           paths.py (path resolution) · panels.py (figure + source data)
scripts/         download_data.py · make_source_data.py · build_caches.py · checks
analysis/        1_Data → 2_Processing → one folder per paper figure
source_data/     One table per panel, plus MANIFEST.csv
figures/         Rendered panels (generated, not tracked)
data/            Downloaded profile tables (not tracked) — never written to
derived/         Anything a run regenerates (not tracked) — safe to delete
```

`data/` holds the deposit and is read-only in practice: every file in it is listed in
`scripts/data_manifest.tsv` with a SHA256. Notebooks that rebuild one of those tables
write to `derived/` instead, and readers prefer the deposit and fall back to `derived/`,
so regenerating can never overwrite a deposited artifact. To adopt a regenerated table,
copy it into `data/` deliberately and re-hash the manifest.

Re-running is idempotent: a panel whose table comes out byte-identical leaves both the
table and its manifest row untouched, so `git status` after a run reports real drift only.
To generate somewhere else entirely — a reproducibility check that touches nothing:

```bash
COLOPAINT3D_FIGURES=/tmp/fresh/figures \
COLOPAINT3D_SOURCE_DATA=/tmp/fresh/source_data python run_all.py
```

`1_Data` and `2_Processing` produce every reusable table; figure folders only consume
them, so figures run in any order or on their own. Four acquisitions feed the paper and
are not versions of one dataset: `exp1_main` (Fig 2–6, Suppl 1–3, 5),
`exp2_spheroid_size` (Suppl 3c), `exp3_clearing_mag_z` (Suppl 3b/d/e) and
`exp4_objective` (Suppl 4h/i).

Panels are written by `utils.panels.save_panel`, which emits the PDF, its source table and
a manifest row in one call — so a panel cannot be produced without its source data, and
`run_all.py --verify` fails if either side is missing. Five panels aggregate inputs too
large to ship; for those the plotted aggregation is committed under `analysis/**/data/`
and `scripts/build_caches.py` regenerates it where the bulk inputs are available.

Analyses that sample or embed use seed 42; deterministic steps do not seed.

## Citation

See `CITATION.cff`. Licence: `LICENSE`.
