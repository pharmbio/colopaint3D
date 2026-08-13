# Port triage

Per-file porting status for the curated release. Audited from notebook inputs,
outputs and surviving output files; `SOURCE_SNAPSHOT.tsv` pins the exact versions.

**IN** = port · **OUT** = excluded · **?** = needs a decision

## Feature-set versions (resolved)

Feature dumps are versioned by extraction date, `FeaturesImages_<DDMMYY>_none/`.
**The date stamps are re-runs on the same images, not different data.** Comparing
`150125` vs `011225` over 4 `SingleSlice` files (both cell lines, 4 slices):
identical schema, rows and well coverage; 99.5% of values bitwise equal; max
absolute difference exactly 2⁻¹⁴ (the float32 quantum) in every file; the residue
sits in `ZernikePhase` arctan2 features.

| Set | Where | Cell lines | Role |
|---|---|---|---|
| `150125` | **`colopaint3D_fork`** (7.7 GB) | HCT116 + HT29 | source of the published tables |
| `011225` | main tree | HCT116 + HT29 | re-extraction of `150125` |
| `291025` | main tree | HCT116 only | Suppl Fig 3 reproducibility |
| `100125` | **gone** | — | was read by `3_CellCoverage` |
| `070426` / `150526` | main tree | — | exp2 / exp3 |

All exp1 sets carry the same 12-plane stack (z 0–11) and the same 873,550
single-cell rows. `150125` was never missing — it is in the fork, which is *why*
those notebooks `chdir` there. Verified as the published source: 834 wells, exact
match with `selected_data_aggregates_HCT116.parquet`.

**Consequences.** exp1 can be repointed at `011225` in the main tree, dropping the
fork dependency; differences are ~1e-7 and change no figure. `291025` is correct as
referenced. `100125` is gone but equivalent data exists — note that the notebook
written against it uses an **older column convention** that must be translated:

| `100125` name | Current name |
|---|---|
| `Cytoplasm_ObjectNumber` | `ObjectNumber_cytoplasm` |
| `Nuclei_ObjectNumber` | `ObjectNumber_nuclei` |
| `Cytoplasm_AreaShape_Area` | `AreaShape_Area_cytoplasm` |
| `Metadata_cmpd_cmpdname` | `Metadata_cmpdname` |
| `Metadata_cmpd_cell_line` | `Metadata_cell_line` |

*Caveat: 4 of 24 slice files compared, at well-aggregated level; the 4.8 GB
`SingleCell` parquets were not value-compared.*

## Panel map

6 main figures, 6 supplementary. Panels marked *image* or *schematic* need no analysis
code. Fig 4/5 panels are HCT116; every one also exists for HT29 (see Suppl 4).

| Panel | Content | Produced by | `data_type` |
|---|---|---|---|
| **Fig 1** | schematic — *no data* | — | — |
| **Fig 2** | cells per spheroid | `CellCoverage/3_CellCoverage` | SingleCell |
| | detected-cell sanity check | `CellDetectionSanityCheck/3_Plot_Spheroids` | — |
| | PCA before / after batch stratification | `RemoveNoise/5_PCA_RemoveNoise_BatchStratified` | — |
| **Fig 3** A2 | grit, MIP | `GritScores/3_GritScores_Figure3A2B2` | `MIP` |
| **Fig 3** B2 | grit, scAgg | same | `aggregates` |
| **Fig 4a** | labelled (supervised) UMAP, MIP | `PCAUMAP/PCAUMAP_pathway_v2` | `MIP` |
| **Fig 4b** | labelled (supervised) UMAP, sc | same | `aggregates` |
| **Fig 4c** | unsupervised UMAP, MIP | same | `MIP` |
| **Fig 4d** | unsupervised UMAP, sc | same | `aggregates` |
| **Fig 4e** | clustermap, MIP | `PairwiseCorrelations/3_PairwiseCorrlations` | `MIP` |
| **Fig 4f** | clustermap, sc | same | `aggregates` |
| **Fig 5a** | compound grit counting | `GritScores` | — |
| **Fig 5b** | 2D UMAP | `PCAUMAP/PCAUMAP_pathway_v2` | `2D` |
| **Fig 5c** | 2D hierarchical clustermap | `PairwiseCorrelations/3_PairwiseCorrlations` | `2D` |
| **Fig 5d** | 2D − 3D difference map | same (`Difference_*_colored_tails`) | — |
| **Fig 5e** | *image of cells* — no code | — | — |
| **Fig 5f** | 2D + 3D fingerprints, 5-FU & olaparib | `3_PairwiseCorrlations **copy**` only | — |
| **Fig 6** | GSEA / hallmark NES | `DEG/hallmark_nes_scatter` | — |
| | EdU + γH2AX | `EdU/EdU_analysis` | — |
| **Fig 6e** | top-10 most similar to 5-FU, HCT116 & HT29 | `10_5fu_top_neighbours` **or** `fig_5fu_neighbours_frozen_doses` — **which?** | — |
| **Suppl 1d** | detected-cell spheroid plot, **HT29** | `CellDetectionSanityCheck/3_Plot_Spheroids` | — |
| **Suppl 1** (rest) | *images* — no code | — | — |
| **Suppl 2** | **? unknown** | | |
| **Suppl 3** | reproducibility / Percent Replicating, all three experiments | exp1 `_certain_slices`, exp2 `3_PercentReplicating`, exp3 robustness | — |
| **Suppl 4** | *inferred:* Fig 4's six panels for **HT29** | same notebooks, `cell_line='HT29'` | `MIP`, `aggregates` |
| **Suppl 5d** | dose-response grit 2D vs 3D, ola + 5-FU | `S_dose_similarity_5FU_Olaparib` | — |
| **Suppl 5e** | drug-pair similarity 2D vs 3D by MoA class | `09b_panel_c_moa_class` / `09_panel_c_recolor` — **which?** | — |
| **Suppl 6** | **? unknown** | | |

Both `PCAUMAP_pathway_v2` and `3_PairwiseCorrlations` are parameterised by `data_type`
and `cell_line`, so each emits panels into Fig 4, Fig 5 **and** Suppl 4 from one run.
This is why `save_panel` derives the target figure from the panel name.

## Pipeline stages

| | File | Note |
|---|---|---|
| IN | `1_Data/1_FeatureSorting.ipynb` (v1, v2, v3) | one per experiment |
| IN | `2_Processing/2_Pycytominer.ipynb` (v1) | repoint `150125` → `011225` |
| IN | `2_Processing/2_Pycytominer.ipynb` (v2, v3) | reference existing sets |
| IN | `2_Processing/2_Pycytominer_certain_slices.ipynb` (v1) | `291025` correct as-is |
| IN | `4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb` | also the basis for WP7 |
| IN | `MIP_features/Pycytominer_MIP.ipynb` | `selected_data_MIP_*`, needed by Fig5 |
| IN | `2D_features/2D_profiles.ipynb` | `selected_data_2D_*`, needed by Fig5 |
| IN → move | GritScores *computation* | compute here, plot in the figure folder |

## Figure 2

| | File | Note |
|---|---|---|
| IN | `CellCoverage/3_CellCoverage.ipynb` | ported; `100125` → `011225` + column translation. Its `savefig` was commented out — the archived PDF was saved by hand |
| IN | `CellDetectionSanityCheck/3_Plot_Spheroids.ipynb` | repoint `150125` → `011225` |
| IN | `RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb` | canonical (newest PDFs) |
| IN | `RemoveNoise/Prepare_Slice_Features.ipynb` | repoint; writes the PCA inputs |
| OUT | `RemoveNoise/old/*` | superseded by BatchStratified |

## Figure 3

| | File | Note |
|---|---|---|
| IN | `GritScores/3_GritScores_Figure3A2B2.ipynb` | already panel-named |
| ? | `3_GritScores.ipynb` vs `3_GritScores copy.ipynb` | differ despite equal size |

## Figure 5 — 2D vs 3D
5a grit counting · 5b UMAP · 5c clustermap · 5d difference map · 5f fingerprints

| | File | Note |
|---|---|---|
| ? | `3_PairwiseCorrlations.ipynb` vs `... copy.ipynb` | **`copy` is the superset** — only it emits `fingerprints_2D/3D.pdf` (5f). Recommend `copy` |
| IN | `PCAUMAP/PCAUMAP_pathway_v2.ipynb` | canonical; its outputs are the ones on disk |
| OUT | `PCAUMAP/PCAUMAP_pathway.ipynb` | superseded by v2 |

## Figure 6

| | File | Note |
|---|---|---|
| IN | `DEG/hallmark_nes_scatter.ipynb` | ships its own dge + gsea CSVs |
| IN | `EdU/EdU_analysis.ipynb` | already writes `panel_source_data.csv` |
| ? | `10_5fu_top_neighbours.py` vs `fig_5fu_neighbours_frozen_doses.py` | which makes 6e |

## Suppl Fig 3 — reproducibility (the only figure `METHODS.md` covers)

| | File | Note |
|---|---|---|
| IN | v1 `3_PercentReplicating_certain_slices.ipynb` | 52 compounds; the well-powered one |
| IN | v2 `3_PercentReplicating.ipynb` | seeding density, incl. `seeding_brackets` |
| ? | v3 `3_Robustness_Combined_Final.ipynb` vs `clearing_comparison{,_stats}.ipynb` | `Combined_Final` looks canonical but `METHODS.md` cites `clearing_comparison` — **doc and files disagree** |
| OUT | v1 `3_PercentReplicating{,copy,copy 2}.ipynb`, v2 `_copy` | superseded / duplicates |
| OUT | v2 `3_MAP.ipynb` | **mAP dropped from the paper** |
| ? | v2+v3 `GritScores/3_GritScores.ipynb` | grit for the robustness experiments — in the paper or not |

## Suppl Fig 5

| | File | Note |
|---|---|---|
| IN | `S_dose_similarity_5FU_Olaparib.ipynb` | = suppl5d dose-response grit 2D vs 3D |
| ? | `09b_panel_c_moa_class.py` vs `09_panel_c_recolor.py` | which makes suppl5e |

## Unplaced — need a figure assignment

`expert-annotation/quantify_segmentation_error.ipynb` ·
`expert-annotation/error_propegation.ipynb` ·
`expert-annotation/convert_npy_to_tiff.py` ·
`david_revision/focus_estimates.ipynb` · `1_Data/syto14_boxplot.ipynb`

## Excluded

- **Single-cell / Harmony** (never in the paper): `1_SC_Harmony_streamlined{,_copy,_new}.ipynb`, `reapply_harmony.py`, `sc_preprocess_harmony.py`, `olaparib_direction_magnitude.py`
- **Organoids / colo8** (never in the paper): `not_to_git/organoids_colo8/`, `colo8*-input/`
- **Exploratory**: `generate_network_html*.py` ×4 (HTML only) · `plot_similarity_*.py` ×4 (superseded by `09*_panel_c`) · `radial_analysis.py`, `radial_profile_analysis.py` (5 parameter-sweep output folders) · `force_graph_diff.py`, `plot_cluster_signature.py` (no surviving output) · screenshots · `_archive/`, `.venv*/`

> Exclusion means "not copied into the paper repo" — nothing is deleted from the
> source tree, and any of it can be pulled back in.

## Open decisions

1. **The paper figure list** — Fig2/3/4 panel lists unknown, so those folders can't be finalised (Fig5, Fig6, Suppl3, Suppl5 are pinned).
2. **`3_PairwiseCorrlations`** — plain or `copy`. Recommend `copy`.
3. **v3 robustness** — `Combined_Final` or `clearing_comparison{,_stats}`.
4. **`3_GritScores`** — which of the two.
5. **Figure assignment** for the five unplaced files.
6. **Fig6e / Suppl5e** — which script of each pair.
