# Known issues

Open blockers, defects found in the source, and defects introduced by the port.

## The port is frozen; the notebooks live in git

The notebooks under `analysis/` were never committed, which is why every fix had to
be written as a `POST_EDITS` regex against upstream source text: with no history
behind them, `port_notebook.py --all` was the only way to reconstruct them, so it had
to stay authoritative. They are now committed, and git is the change history.

**Do not run `port_notebook.py --all` again.** It regenerates from source and would
discard everything since. The tool is kept as the record of how the port was made,
and to bring genuinely *new* upstream files in (`port_notebook.py <key>` for one
notebook at a time). This supersedes the "hand-edits wiped by the next `--all`" row
in the port-defects table below.

## Open blockers

**Suppl 4h/4i — which acquisition is "air".** `wi_20250203` is the WI acquisition;
there are two non-WI ones and **no code combines them**: "air" appears nowhere in either
AZ folder, `3_PCA.ipynb` runs one plate at a time, `3_Fig_TechnicalReplicates` groups by
`Metadata_Barcode`, and `2_DetectandCombine` keeps all three distinct. The ported
notebooks emit one output per acquisition (`bomi`, `cleared3d`, `wi`); no combining step
was invented.

**The author states air is `CellPainting_20241220clearedspheroidsBOMI_20241220_151510`
— i.e. `bomi` alone**, not a combination. That settles which plate was used.

It does **not** yet reconcile with the numbers this triage recorded. Reproducing Suppl 4i's
null 95th percentile gave 0.486 for the two non-WI acquisitions combined against a published
line at ≈0.45, and **0.553 and 0.589 for each alone** — so `bomi` alone should sit at one of
the latter two, further from the published line than the combined figure. Either that earlier
inference was wrong, or the published dashed line was computed over a different subset than
assumed (the panel uses `pos_con` only). **Open:** recompute the null 95th percentile per
acquisition from the exp4 profiles and check which reproduces ≈0.45. Until then, take
air = `bomi` as the answer and treat the 0.486-vs-0.45 argument as superseded.

**Fig 3g / 3h cannot be reproduced — the code is lost.** Published Figure 3 runs a–h.
Panels 3e/3f were recovered (see below), but 3g/3h — the MIP-vs-Aggregates scatters,
coloured by dose and by pathway — survive only as
`3_Figure3/PercentReplicating/result-images/AggVsMIP_{dose,pathway}_aggregates.pdf`,
dated 2025-01-22. The string `AggVsMIP` appears in **no notebook, script or checkpoint**
in `colopaint3D`, `colopaint3D_fork` or `colopaint3D_AZ`, and all three
`3_PercentReplicating` variants in both trees were diffed — none contains the scatter.
The producing cell was written after the surviving notebook versions (2025-01-11/18)
and later overwritten. Not rebuilt: reconstructing it would mean guessing the dose and
pathway encodings. The `perc_replicating_conc_*.csv` that `3_PercentReplicating` writes
is the input it would need.

**`requirements.txt` did not resolve.** `statsmodels==0.14.6` requires numpy ≥1.22.3
against the pinned `numpy==1.22.0`, so `pip install -r requirements.txt` — and therefore
the documented `conda env create -f environment.yml` — exited `ResolutionImpossible`.
statsmodels is a transitive dependency of `copairs`, not a direct import; **unpinned it
resolves to 0.14.1**, which is numpy-1.22 compatible. Fixed. Same class as the missing
scikit-learn pin.

`cytominer-eval==0.1` and `pycytominer==0.2.0` import **fine** under the declared stack
(python 3.10, numpy 1.22.0, scipy 1.7.3, pandas 1.5.2). Earlier notes here claiming
otherwise were written from a python 3.11 / numpy 2 / pandas 3 interpreter and were wrong.
Build the environment before concluding a notebook is blocked.

**The expert-annotation `.npy` masks were written by numpy 2** (they reference
`numpy._core`) and cannot be unpickled by the pinned numpy 1.22. Suppl 2d does not need
them — it is drawn from the committed `segmentation_iou_cached.csv` — but the notebook's
`HAVE_MASKS` flag was computed and never consulted, so it died mid-load instead of falling
back. It now probes readability and uses the cache.

**Fig 5b / Suppl 5a — 2D UMAP unverified.** `PCAUMAP_pathway_v2` supports `data_type='2D'`
but no 2D output survives upstream. Marked `UNVERIFIED` in its `PANEL` map.

**Suppl 5e is a reconstruction.** `09_panel_c_recolor.py` was edited in place into a
cycling-dependence recolour and the MoA version was lost; `09b` rebuilds it (palette matches)
but may not be pixel-identical. `06_analyze_similarity.py` is gone — harmless, the MoA map is
hardcoded in `09b`.

**Fig 5f cannot run — one helper is still missing from the source.** The fingerprint cells
call `normalize_feat` (which "normalises the illum prefix so feature names match 3D") and
`parse_channel`. `normalize_feat` is **defined nowhere in `colopaint3D`, `colopaint3D_fork` or
`colopaint3D_AZ`**, and since it decides which features are compared between 2D and 3D it has
not been reinvented. `parse_channel` **has now been recovered** verbatim from line 200 (and
`_CHANNELS` from line 77) of `plot_cluster_signature.py`, which this triage had wrongly
excluded as exploratory. `cos_sim`, used by the same section, was simply never imported and is
plain `cosine_similarity`.

The Fig 5f cells are therefore guarded on `FIG5F_AVAILABLE = False` rather than deleted: the
code is kept verbatim and skipped with a message. Before this, those cells raised `NameError`
and aborted `3_PairwiseCorrelations` at cell 20 — which is why Fig 4e, Fig 5c, Suppl 4e/4f and
Suppl 5b/5c never appeared even for combinations that had been run. Setting `FIG5F_AVAILABLE`
to `True` once `normalize_feat` is recovered is all that is needed.

The same cells also used `data_2D`, which was defined nowhere; the port restores it as
`grit_data_2D_{cell_line}` (the only value consistent with `get_lowest_passing_profiles`),
**flagged for confirmation**.

**Deposition-dependent.** No BIA accession, so `download_images.py` is a scaffold; no dataset
URL, so use `download_data.py --from-local`. The CellProfiler `.cppipe` pipelines and Cellpose
models are **not in this repo** and none were found in the source — raw images alone do not
reproduce the features.

## Defects in the source

| Defect | Handling |
|---|---|
| `1_FeatureSorting` hardcoded `OutputDir = 'FeaturesImages_011225'` — any re-run **silently destroyed 7.7 GB** that is the provenance of the published profiles | `paths.feature_output()` requires an explicit stamp and refuses to overwrite |
| `requirements.txt` **omitted scikit-learn** (~50 imports) — the env could not reproduce | pinned `1.6.1`; `gseapy` still **needs a pin** |
| `np.fill_diagonal(df.values, …)` raises on pandas ≥2 (copy-on-write makes `.values` read-only). Correct under the pinned stack, breaks for anyone on a current one | rewritten as `to_numpy(copy=True)`, same result any version |
| **Fig 6d and Suppl 6b were one fused output** from a five-entry `SIGNATURE_PANELS` | split into two calls over disjoint subsets |
| **`3_CellCoverage`'s `savefig` was commented out** — the archived PDF was saved by hand | exactly what `save_panel` prevents |
| **`3_GritScores` writes back into `1_Data/results/`** — re-running it overwrites the published `grit_data_*.parquet` that every figure consumes | Fig 5a was rebuilt so it no longer requires that re-run; the hazard itself is unfixed |
| **The cell that wrote `grit_scores_descriptive_stats_*.csv` does not survive** — only its four outputs do | Fig 5a's compound sets re-derived as "treatments whose median grit per perturbation > 1.96", validated against all four originals: 46/46, 47/47, 38/38, 33/33 |
| A second `np.fill_diagonal(...values)` in `3_PairwiseCorrelations`' trailing `cluster_metrics`, missed when the first was fixed | same `to_numpy(copy=True)` rewrite |
| `3_PairwiseCorrelations` used `get_sim_matrix` one cell **before** defining it — only ever worked in a live kernel | the two cells swapped, with a note |
| `3_Plot_Spheroids` hardcoded one cell line with the other commented out, and `well`/`barcode` as separate variables to keep in sync | `EXAMPLE_WELL` lookup keyed on `cell_line`, so one parameter drives all three |
| **Fig 6e hides a substitution**: `fig_5fu_neighbours_frozen_doses.py` drops Vinorelbine for Crizotinib (#11) because its matched dose fails grit | **needs stating in the legend** |
| PairwiseCorrelations cells 24–27 re-save cells 19–21's filenames | both converted, last-write-wins preserved |
| `REPRODUCIBILITY_METHODS.md` documented three superseded notebooks | dropped by decision |
| exp1 referenced three feature stamps; `150125` is in the fork, `100125` is gone | stamps are re-extractions of the same images (max diff 2⁻¹⁴); exp1 repoints to `011225`. See `PORT_TRIAGE.md` |
| Suppl 5e's inputs were laptop-only; `similarities_2D.csv` existed nowhere | both regenerated in-repo; 3D validates at **703/703 pairs, max diff 1.55e-15** |

## Defects introduced by the port

Each was silent; the guard matters more than the fix.

| Defect | Consequence | Guard |
|---|---|---|
| Removing `os.chdir` from inside an `if` left an empty block | SyntaxError ×2 | indented `chdir` → `pass`; tool **AST-parses every cell** |
| Commenting a lone `savefig` inside a `for` left an empty block | SyntaxError | indent read from preceding text, `pass` appended |
| **Duplicate `POST_EDITS` keys** (Python keeps the last) | rules dropped, absolute paths reappeared — hit twice | tool scans its own source, raises on duplicates |
| Hand-edits wiped by the next `--all` | fixes silently reverted | all edits live in `POST_EDITS`; port reproducible from source |
| **`IMG2COND` copied truncated** at a line break | Suppl 3h cache missing 2 of 3 clearing conditions | builders print per-group counts — which exposed it |
| Port dropped `Metadata_Barcode`/`Well` | weaker source table | restored; values verified identical (1470/1470) |
| README cited a dropped `METHODS.md` | dangling reference | removed; claims re-checked |
| **`save_panel(plt.gcf(), …)` after `plt.show()`** in the Fig 5d cell | `Fig5d.pdf` was a blank page while its source table and manifest row looked healthy — `--verify` passed | pass the `fig` the cell already bound; a blank-page check now runs after `run_all.py` |
| **Three panels commented out as "not a paper panel"** — Suppl 2c attached to the raw rather than normalized variance, Fig 6b's `plot_metric` savefig, Fig 5a's `GritScores_hits` | Suppl 2c plotted the wrong quantity; Fig 6b and Fig 5a were absent | re-pointed / re-enabled; see the panel map in `PORT_TRIAGE.md` |
| **`PLATE_TAG` injected into `3_PCA_objective` but not `3_Fig_TechnicalReplicates`**, which uses it | Suppl 4i would raise `NameError` | same `EXP4_TAGS` block added |
| **Two source-relative paths left unrewritten** in `3_Fig_TechnicalReplicates` (`spher_colo52_v1/1_Data/…`) | resolve against cwd; Suppl 4i could not load its inputs | routed through `profiles()` / `metadata()` |
| A self-introspection cell survived with its `notebook_path` assignment already stripped | `3_PairwiseCorrelations` exited non-zero on every run | cell deleted — it only printed its own source |

## Current verification

```
35 notebooks · 0 absolute paths · 0 os.chdir · 0 syntax errors
28 save_panel calls · 46 panels rendered · 0 blank · 2 live savefig (both intentional)
18 non-panel savefig commented, not deleted
run_all.py --verify: green · scripts/check_panels_nonblank.py: green
```

Verified from a **clean state**: `figures/` and `MANIFEST.csv` emptied, then every figure
folder re-run — 32 runs, 28 pass, 4 fail on the environment blockers below.

**Executed.** Every figure folder runs end to end; `run_all.py` expands 31 notebooks
into ~42 runs via `SWEEPS`. A blank-page check (rasterise each PDF, assert a non-white
pixel) runs alongside `--verify` — it is what would have caught `Fig5d`, which had a
healthy manifest row and source table behind an empty page.

Still not produced, and why:

| Panel | Blocked on |
|---|---|
| Fig 3g/3h | code lost (above) |
| Fig 5f (2D/3D) | `normalize_feat` missing; cells guarded, not deleted |
| Suppl 4h ×6, 4i ×3 | exp4 profiles absent from `data/`; regenerating them needs `pycytominer`, which cannot import (above). The notebooks themselves are fixed and ready |
