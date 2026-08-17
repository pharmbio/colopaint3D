# Where everything lives

A map of every location this analysis touches, what is in it, and who owns it.
Sizes measured 2026-08-17.

---

## 1. Inside the repo, tracked by git (~84 MB)

This is what someone else downloads. **Code, and the numbers behind each panel — nothing else.**

| path | what | size |
|---|---|---|
| `analysis/` | the notebooks — one folder per figure | — |
| `utils/` | `paths.py` (works out every file location), `panels.py` (saves each figure panel together with the numbers behind it) | 546 lines |
| `scripts/` | `download_data.py`, `make_source_data.py`, `build_caches.py`, `verify_deposit.py`, `check_panels_nonblank.py` | — |
| `run_all.py` | the single entry point | 401 lines |
| `source_data/` | one CSV per panel (55) + `MANIFEST.csv` | 50 MB |
| `analysis/**/data/` | 38 small tables, standing in for inputs too big to publish — **being moved to the archive** | 17 MB |

## 2. Inside the repo, NOT tracked (git ignores these)

These exist on this machine but not in a fresh copy, until they are downloaded or rebuilt.

| path | what | size | where it comes from |
|---|---|---|---|
| `data/` | the published tables the figures are drawn from | 405 MB | `scripts/download_data.py`, from the archive |
| `data/features/` | **shortcuts (symlinks)**, not real files — see §4 | 97 KB of links | created by `download_data.py --from-local --link` |
| `derived/` | anything a run regenerates | small | written by the notebooks; safe to delete |
| `figures/` | the rendered panels | 3.6 MB | written by `run_all.py` |

`data/` is never written to — that rule is what `derived/` exists to enforce.

## 3. The BioImage Archive — accession S-BIAD2254

The public home of the data. Everything a reader needs should come from here.

| folder | what | size | status |
|---|---|---|---|
| `results/` | raw measurement tables straight out of the image analysis, 18 files over 6 plates | 16.6 GB | deposited, verified |
| `processed_profiles/` | the 31 summary tables the figures are drawn from | 488 MB | deposited, verified |
| `segmentation/`, `feature_extraction/`, `image_acquisition/` | the cell-detection models, the image-analysis recipe, and the microscope settings | — | deposited |
| `analysis_inputs/` | the 38 small tables from §1 | 17 MB | **planned** |

## 4. Outside the repo — the old working folders

These are yours, they are large, and **nobody else has them.** Anything the analysis still
reads from here is something a reader will not be able to reproduce.

| path | what | size |
|---|---|---|
| `/share/data/analyses/christa/colopaint3D` | the original working folder this repo was copied out of | **125 GB** |
| `/share/data/analyses/christa/colopaint3D_fork` | a second copy of it; where one set of measurements and the 2D tables come from | 8.1 GB |
| `/share/data/analyses/christa/colopaint3D_AZ` | where the air-vs-water objective measurements come from | — |
| `/share/data/analyses/christa/colopaint3D_AZ_first` | an earlier copy; nothing in the repo refers to it | — |

The raw per-cell measurements — about 19.5 GB, one row for every cell found in every
image slice — physically live in these two folders. `data/features/` holds only shortcuts
to them:

There are **seven** such shortcuts, pointing into **three** different old folders:

```
exp1_main/FeaturesImages_011225_none  -> colopaint3D/spher_colo52_v1/...
exp1_main/FeaturesImages_150125_none  -> colopaint3D_fork/spher_colo52_v1/...
exp2_spheroid_size/...                -> colopaint3D/spher_colo52_v2/...
exp3_clearing_mag_z/...               -> colopaint3D/spher_colo52_v3/...
exp4_objective/... (three of them)    -> colopaint3D_AZ/spher_colo52_v1/...
```

None of them are stored in git, so someone else gets no broken links — the folder is
simply absent, which the code already handles.

So on this machine those measurements look like they are here. Anywhere else they are
simply missing, which is why four panels (Fig2d, Fig2f, SupplFig1d, SupplFig2e) cannot be
rebuilt from the published data alone.

### What the notebooks still read from these folders

| what | file | size | used by |
|---|---|---|---|
| EdU measurements, one row per cell | `colopaint3D/.../3_Figure6/EdU/` — `EdU_nuclei.csv` alone is 86 MB | 67 MB | Fig 6b |
| public gene lists (MSigDB) | `.../DEG/genesets/h.all…gmt` (48 KB), `c2.all…gmt` (4.6 MB) | 4.6 MB | Fig 6d — now falls back to a shipped 200-gene list |
| hand-drawn cell outlines used to check the automatic detection | `colopaint3D/expert-annotation/` | 7.7 GB | Suppl 2d/2e — already falls back to a stored summary |
| the flat 2D measurements, for comparing against 3D | `colopaint3D_fork/2D_features/selected_data_*.csv` | — | the 2D comparisons |

## 5. Outside the repo — the archive folder

`/share/data/analyses/christa/colopaint3D_paper_archive` (15 MB). Deliberately outside
git so no release step can delete it, and deliberately **not** shipped.

| folder | what |
|---|---|
| `actual_panels/` | the 12 published figure PNGs |
| `archived_originals/` | the 8 original January-2026 PDFs behind Fig 4a–d |
| `provenance/` | the record of how this repo was built from the old folder, and every known issue |
| `panel_review.html` | all 55 panels on one page, marked with what rebuilds and what does not |

---

## How the code finds a file

Almost every file location is worked out in `utils/paths.py`, so nothing is tied to one
machine. Two exceptions remain: `4_ImageBioArchive_Metadata` has the cluster path
`/share/data/cellprofiler/automation/results` written into it, and `2D_profiles` and
`Pycytominer_MIP` write to a folder path left over from the old layout.

| function | where it looks, in order |
|---|---|
| `profile_input(exp, name)` | the downloaded copy first, then anything rebuilt locally |
| `analysis_input(relpath)` | the downloaded copy, then a locally rebuilt one, then the copy still stored in git (temporary) |
| `derived(exp, name)` | always `derived/` — the only place runs write, so nothing can overwrite downloaded data |
| `external(name)` | the old working folder — see §4, and the thing being eliminated |

If your data sits somewhere else, these environment variables override the defaults: `COLOPAINT3D_DATA`, `COLOPAINT3D_FEATURES`,
`COLOPAINT3D_EXTERNAL`, `COLOPAINT3D_DERIVED`, `COLOPAINT3D_FIGURES`,
`COLOPAINT3D_SOURCE_DATA`.

## The short version

Three kinds of thing, three homes:

- **Code** → git.
- **Data** → the BioImage Archive, downloaded into `data/`.
- **Regenerated output** → `derived/`, disposable.

Anything still read from section 4 is a gap between that intention and where things stand.
