# Known issues

Open blockers, defects found in the source, and defects introduced by the port.

## Open blockers

**Suppl 4h/4i — the "air" panel cannot be reproduced.** `wi_20250203` is the WI
acquisition, but there are two non-WI ones and **no code combines them**: "air" appears
nowhere in either AZ folder, `3_PCA.ipynb` runs one plate at a time, `3_Fig_TechnicalReplicates`
groups by `Metadata_Barcode`, and `2_DetectandCombine` keeps all three distinct. Indirect
evidence favours air = both non-WI combined — reproducing Suppl 4i's null 95th percentile
gives 0.486 combined vs a published line at ≈0.45, against 0.553 and 0.589 for each alone
(WI: 0.434 vs ≈0.40; the air−WI gap matches at ~0.05). The ported notebooks emit one output
per acquisition; no combining step was invented.

**Fig 5b / Suppl 5a — 2D UMAP unverified.** `PCAUMAP_pathway_v2` supports `data_type='2D'`
but no 2D output survives upstream. Marked `UNVERIFIED` in its `PANEL` map.

**Suppl 5e is a reconstruction.** `09_panel_c_recolor.py` was edited in place into a
cycling-dependence recolour and the MoA version was lost; `09b` rebuilds it (palette matches)
but may not be pixel-identical. `06_analyze_similarity.py` is gone — harmless, the MoA map is
hardcoded in `09b`.

**Fig 5f cannot run — two helpers are missing from the source.** The fingerprint cells call
`normalize_feat` (which "normalises the illum prefix so feature names match 3D") and
`parse_channel`. `normalize_feat` is **defined nowhere in `colopaint3D`, `colopaint3D_fork` or
`colopaint3D_AZ`**, and since it decides which features are compared between 2D and 3D it has
not been reinvented. `parse_channel` is recoverable — it is at line 200 of
`plot_cluster_signature.py`, which this triage had wrongly excluded as exploratory.
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

## Current verification

```
31 notebooks · 0 absolute paths · 0 os.chdir · 0 syntax errors · outputs stripped
25 save_panel calls · 46 panels · 2 live savefig (both intentional)
21 non-panel savefig commented, not deleted
```

**Not done:** the notebooks have not been executed end to end. `run_all.py` has been
exercised on `3_Figure2/CellCoverage` only (12 s, passed `--verify`).
