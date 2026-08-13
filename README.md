# Cell Painting in 3D spheroids — paper analysis

Analysis code for **"High-content morphological profiling by Cell Painting in 3D
spheroids."**

Cell Painting is well established for 2D monolayers. This paper presents a
scalable adaptation to 3D spheroids, covering adaptive spheroid detection and
z-placement at acquisition, per-slice feature extraction and normalisation, and a
comparison of what 3D profiling recovers relative to 2D and to maximum-intensity
projections.

This repository holds only the analysis published in the paper. It is a curated
release of a larger working tree; see `provenance/` for what was included and why.

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
  3_SupplFigure3/     Reproducibility (Percent Replicating) + its methods
  4_BioImageArchive/  Image deposition metadata
source_data/          One table per figure panel, plus MANIFEST.csv
figures/              Rendered panels (generated, not tracked)
data/                 Downloaded profile tables (not tracked)
provenance/           Record of the port: source snapshot and triage decisions
```

`1_Data` and `2_Processing` produce every reusable table; figure folders only
consume them, so figures can run in any order or on their own.

### Experiments

Three acquisitions feed the paper. They are **not** versions of one dataset and
their numbers are not comparable across experiments:

| Key | What it varies | Used by |
|---|---|---|
| `exp1_main` | z-slice sampling, 52 compounds | every figure |
| `exp2_spheroid_size` | seeding density / spheroid size | Suppl Fig 3 |
| `exp3_clearing_mag_z` | clearing, magnification, z-sampling density | Suppl Fig 3 |

---

## Source data

Every panel ships with the table it was drawn from. `utils/panels.py` writes the
panel, its table and a manifest row in a single call, so a figure cannot be
produced without its source data:

```python
from utils.panels import save_panel

save_panel(fig, "Fig5c", data=plotted_df,
           caption="Hierarchical clustering of 2D compound profiles")
```

That writes `figures/Fig5/Fig5c.{pdf,png}`,
`source_data/Fig5c_hierarchical_clustering.csv`, and a row in
`source_data/MANIFEST.csv` mapping panel → notebook → table → figure file.
`python run_all.py --verify` fails if any rendered panel lacks a table, or any
table lacks its panel.

Panel names carry the figure: `Fig5c` → `figures/Fig5/`, `SupplFig3a` →
`figures/SupplFig3/`. Several notebooks are parameterised by data type (`2D`,
`MIP`, `aggregates`) and emit panels into more than one figure; deriving the
target from the panel name is what lets one notebook do that without bookkeeping.

PDFs are written with type-42 fonts, so panel text stays editable for figure
assembly.

---

## Data availability

`scripts/download_data.py` fetches the processed profile tables the figures are
built from, verifying SHA256 against `scripts/data_manifest.tsv`:

| Tier | Contents | Size |
|---|---|---|
| `required` | 65 parquet profile tables (`grit_data_*`, `selected_data_*`) | 147 MB |
| `normalized` | 3 `normalized_data_*.csv`, Figure 2 PCA only — `--include-normalized` | 570 MB |

Re-running `1_Data`/`2_Processing` additionally needs the per-slice CellProfiler
feature dumps (`FeaturesImages_*`, **19.5 GB**), which are not in either tier.
Regenerating the *figures* does not require them — the tiers above begin
downstream of `2_Processing`, which is why they are the default entry point.

Raw images are to be deposited in the BioImage Archive;
`analysis/4_BioImageArchive/` generates the deposition metadata and
`scripts/download_images.py` will retrieve selected images from it.

> **Not yet available.** No dataset URL is configured — the data has not been
> deposited. Until then, populate `data/` from a local working copy:
>
> ```bash
> python scripts/download_data.py --from-local /path/to/colopaint3D --link
> ```

---

## Reproducibility

Fixed seeds throughout (`random.seed(42)`, `np.random.default_rng(42)`).
`analysis/3_SupplFigure3/METHODS.md` documents the Percent Replicating metric,
its matched non-replicate null, and the statistical tests — that analysis is
specific to Suppl Fig 3 and the document should not be read as applying
repo-wide.

`provenance/SOURCE_SNAPSHOT.tsv` records a content hash for every file in the
working tree this release was ported from, and `provenance/PORT_TRIAGE.md`
records what was included, excluded, and why.

---

## References

- [CellProfiler](https://github.com/CellProfiler)
- [Pycytominer](https://github.com/cytomining/pycytominer)
- [Spheroid detection](https://github.com/Ionshiv/SphereDetect)

## Citation

See `CITATION.cff`.

## License

See `LICENSE`.
