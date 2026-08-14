# Cell Painting in 3D spheroids — paper analysis

Analysis code for **"High-content morphological profiling by Cell Painting in 3D
spheroids."**

A scalable adaptation of Cell Painting to 3D spheroids: adaptive spheroid detection and
z-placement at acquisition, per-slice feature extraction and normalisation, and a comparison
of what 3D recovers relative to 2D and to maximum-intensity projections.

Only the analysis published in the paper; see `provenance/` for what was included and why.

---

## Quick start

```bash
# 1. Environment
conda env create -f environment.yml
conda activate colopaint3d
# There is no package to install — helpers are imported from utils/ directly.

# 2. Processed profile tables (~147 MB)
python scripts/download_data.py

# 3. See what would run, then run it
python run_all.py --dry-run
python run_all.py
```

Individual figures:

```bash
python run_all.py --figure Fig5          # also accepts Figure5 or 3_Figure5
python run_all.py --figure SupplFig3
python run_all.py --stage 2_Processing
python run_all.py --verify               # check every panel has source data
```

Several notebooks are parameterised by cell line and data type and emit panels into
more than one figure. They read those parameters from the environment, defaulting to
the value each used to hardcode, and `run_all.py` runs them over every combination:

```bash
COLOPAINT3D_CELL_LINE=HT29 COLOPAINT3D_DATA_TYPE=MIP jupyter nbconvert --execute ...
```

Data held outside the repo:

```bash
COLOPAINT3D_DATA=/mnt/big/profiles python run_all.py
```

---

## Layout

```
run_all.py            Single entry point for the whole analysis
utils/                paths.py (path resolution) · panels.py (figure + source data)
scripts/              download_data.py · download_images.py
acquisition/          Nikon JOBS/GA3 acquisition protocols and optical configs
analysis/
  1_Data/             Feature sorting, per experiment
  2_Processing/       Normalisation, feature selection, grit-score computation
  3_Figure2/ …        One folder per paper figure
  3_SupplFigure3/     Reproducibility (Percent Replicating)
  4_BioImageArchive/  Image deposition metadata
source_data/          One table per figure panel, plus MANIFEST.csv
figures/              Rendered panels (generated, not tracked)
data/                 Downloaded profile tables (not tracked)
provenance/           Record of the port
  PORT_TRIAGE.md      Panel map, what was included/excluded and why
  KNOWN_ISSUES.md     Open blockers, source defects, port defects and guards
  SOURCE_SNAPSHOT.tsv Content hashes of the tree this was ported from
  port_notebook.py    Reproduces the port from source
  build_caches.py     Rebuilds the committed cache tables
```

`1_Data` and `2_Processing` produce every reusable table; figure folders only
consume them, so figures can run in any order or on their own.

### Experiments

Four acquisitions feed the paper. They are **not** versions of one dataset and their
numbers are not comparable across experiments; exp4 came from a separate repository:

| Key | What it varies | Used by |
|---|---|---|
| `exp1_main` | z-slice sampling, 52 compounds | Fig 2–6, Suppl 1–3, 5 |
| `exp2_spheroid_size` | seeding density / spheroid size | Suppl Fig 3c |
| `exp3_clearing_mag_z` | clearing, magnification, z-sampling density | Suppl Fig 3b/d/e |
| `exp4_objective` | air vs water-immersion objective | Suppl Fig 4h/i |

---

## Source data

Every panel ships with the table it was drawn from — `save_panel` writes the panel, its
table and a manifest row in one call, so a figure cannot be produced without its source data:

```python
from utils.panels import save_panel

save_panel(fig, "Fig5c", data=plotted_df,
           caption="Hierarchical clustering of 2D compound profiles")
```

That writes `figures/Fig5/Fig5c.pdf`, `source_data/Fig5c_hierarchical_clustering.csv`, and
a `source_data/MANIFEST.csv` row mapping panel → notebook → table → figure.
`run_all.py --verify` fails if any rendered panel lacks a table, or vice versa.

Panel names carry the figure (`Fig5c` → `figures/Fig5/`), which is what lets one notebook —
several are parameterised by `data_type` and `cell_line` — emit into several figures without
bookkeeping. A panel split across files uses a suffix: `Fig5f_2D`, `Fig5f_3D`. PDFs use
type-42 fonts so text stays editable.

---

## Data availability

`scripts/download_data.py` fetches the profile tables the figures are built from, SHA256-verified
against `scripts/data_manifest.tsv`:

| Tier | Contents | Size |
|---|---|---|
| `required` | 65 parquet profile tables (`grit_data_*`, `selected_data_*`) | 147 MB |
| `normalized` | 3 `normalized_data_*.csv`, Figure 2 PCA only — `--include-normalized` | 570 MB |

Re-running `1_Data`/`2_Processing` additionally needs the per-slice CellProfiler
feature dumps (`FeaturesImages_*`, **19.5 GB**), which are not in either tier.
Regenerating the *figures* does not require them — the tiers above begin
downstream of `2_Processing`, which is why they are the default entry point.

### Cached tables

Five panels aggregate inputs that are far too large to ship — the feature dumps, the
7.7 GB expert-annotation set, and 67 MB of EdU per-object CSVs. For those, the
aggregation each panel actually plots is precomputed and **committed** (4.3 MB total),
so the whole figure set regenerates from the 147 MB download:

| Panel | Cached table | Rows |
|---|---|---|
| Suppl 3g | `suppl3g_bleaching_perwell.csv` | 7,870 |
| Suppl 3h | `suppl3h_detection_perwell.csv` | 1,546 |
| Suppl 2d | `segmentation_iou_cached.csv` | 288 |
| Suppl 2e | `error_propagation_cached.csv` | 423 |
| Suppl 5e | `similarities_{2D,3D}.csv` | 1035 / 703 |
| Fig 6b | `panel_source_data.csv` | per spheroid |

`python provenance/build_caches.py --all` regenerates them where the bulk inputs are
available; point `COLOPAINT3D_EXTERNAL` at them. The regenerated 3D similarity matrix is
validated against the surviving original (703/703 pairs, max |diff| 1.6e-15).

Raw images are to be deposited in the BioImage Archive; `analysis/4_BioImageArchive/`
generates the deposition metadata and `scripts/download_images.py` will retrieve from it.

> **Not yet available.** No dataset URL is configured — the data has not been
> deposited. Until then, populate `data/` from a local working copy:
>
> ```bash
> python scripts/download_data.py --from-local /path/to/colopaint3D --link
> ```

---

## Reproducibility

Analyses that sample or embed use seed 42; deterministic steps do not seed. The Suppl Fig 3
statistics (Percent Replicating, its matched non-replicate null, the tests) are implemented in
`analysis/3_SupplFigure3/3_Robustness_Combined_Final.ipynb`; the paper's methods section is
the authority for how they are described.

`provenance/SOURCE_SNAPSHOT.tsv` records a content hash for every file in the working
tree this release was ported from; `provenance/PORT_TRIAGE.md` records what was included,
excluded and why; and `provenance/KNOWN_ISSUES.md` records the open blockers and the
defects found on both sides of the port.

`provenance/port_notebook.py` records how the port was made and can still bring a new
notebook across from the source tree one at a time. It is **no longer the maintenance
path** — the notebooks are committed and git is the change history. Do not run
`--all`; it regenerates from source and would discard everything since.

**Execution status.** Every figure folder now runs end to end. Three notebooks do not,
for reasons outside this repo:

| Notebook | Why |
|---|---|
| `2_Processing/exp1_main/3_GritScores` | `cytominer-eval==0.1` imports `np.float`, removed in numpy 1.24 |
| `3_Figure2/RemoveNoise/Prepare_Slice_Features` | `pycytominer==0.2.0` imports `scipy.stats.median_absolute_deviation`, removed in scipy 1.7 |
| `1_Data/*`, other `2_Processing/*` | need the 19.5 GB per-slice feature dumps, which are not in either download tier |

The pinned versions predate the current scientific stack; `requirements-frozen.txt` is
the environment they were written against. Neither blocks the figures — the download
tier begins downstream of `2_Processing`.

---

## References

- [CellProfiler](https://github.com/CellProfiler)
- [Pycytominer](https://github.com/cytomining/pycytominer)
- [Spheroid detection](https://github.com/Ionshiv/SphereDetect)

## Citation

See `CITATION.cff`.

## License

See `LICENSE`.
