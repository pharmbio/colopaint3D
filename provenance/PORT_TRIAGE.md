# Port triage

What gets ported into this release and why. Audited from notebook inputs, outputs, and
surviving output files; `SOURCE_SNAPSHOT.tsv` pins the exact versions audited.

## Panel map

6 main + 6 supplementary figures. *image* / *schematic* panels need no code.

| Panel | Content | Produced by |
|---|---|---|
| **Fig 1** | *schematic* | — |
| **Fig 2d** | cells per spheroid | `CellCoverage/3_CellCoverage` |
| **Fig 2f** | detected-cell sanity check (spheroid plot) | `CellDetectionSanityCheck/3_Plot_Spheroids` |
| **Fig 2g** | PCA before / after batch stratification | `RemoveNoise/5_PCA_RemoveNoise_BatchStratified` |
| **Fig 3c** | grit, MIP *(was `Figure3A2`)* | `GritScores/3_GritScores_Figure3A2B2` |
| **Fig 3d** | grit, scAgg *(was `Figure3B2`)* | same |
| **Fig 4a–d** | UMAP: supervised & unsupervised × MIP & scAgg | `PCAUMAP/PCAUMAP_pathway_v2` |
| **Fig 4e–f** | clustermap × MIP & scAgg | `PairwiseCorrelations/3_PairwiseCorrlations copy` |
| **Fig 5a** | compound grit counting | `GritScores` |
| **Fig 5b** | 2D UMAP | `PCAUMAP_pathway_v2` (`2D`) |
| **Fig 5c** | 2D clustermap | `3_PairwiseCorrlations copy` (`2D`) |
| **Fig 5d** | 2D − 3D difference map | same → `Difference_*_colored_tails` |
| **Fig 5e** | *image of cells* | — |
| **Fig 5f** | 2D + 3D fingerprints, 5-FU & olaparib | same → `fingerprints_2D/3D` — **only the `copy` makes these** |
| **Fig 6b** | EdU / γH2AX: DNA damage, S-phase entry, size | `EdU/EdU_analysis` |
| **Fig 6c** | hallmark GSEA scatter | `DEG/hallmark_nes_scatter` → `hallmark_nes_scatter` |
| **Fig 6d** | dumbbells: p53 pathway → E2F targets → p53 apoptosis | same → *subset of* `signature_dumbbells_combined` |
| **Fig 6e** | top-10 most similar to 5-FU, HCT116 & HT29 | `fig_5fu_neighbours_frozen_doses.py` |
| **Suppl 1d** | detected-cell spheroid plot, **HT29** | `3_Plot_Spheroids` |
| **Suppl 1** rest | *images* | — |
| **Suppl 2a–b** | *images* | — |
| **Suppl 2c** | mean focus per compound × z | `david_revision/focus_estimates` |
| **Suppl 2d** | expert-annotation IoU | `expert-annotation/quantify_segmentation_error` |
| **Suppl 2e** | error propagation with depth | `expert-annotation/error_propegation` |
| **Suppl 3a–e, g–h** | z-subsampling · z-density · spheroid size · clearing · magnification · intensity-vs-depth · detection-vs-depth | `3_Robustness_Combined_Final` (all of them) |
| **Suppl 3f** | *image* | — |
| **Suppl 4a–f** | Fig 4a–f for **HT29** | same notebooks, `cell_line='HT29'` |
| **Suppl 4g** | *images* | — |
| **Suppl 4h** | UMAP unsup. + labelled, air vs WI | **exp4** `UMAP/3_PCA.ipynb` — per compound×conc, **not** per well |
| **Suppl 4i** | reproducibility vs concentration, same objectives | **exp4** `3_Fig_TechnicalReplicates.ipynb` — Spearman, `pos_con` only, null 95th pct as the dashed line |
| **Suppl 5a** | 2D UMAP fingerprints, HT29 | `PCAUMAP_pathway_v2` |
| **Suppl 5b** | 2D clustermap, HT29 | `3_PairwiseCorrlations copy` |
| **Suppl 5c** | difference in similarity | same → `Difference_HT29_colored_tails` |
| **Suppl 5d** | grit dose example, HCT116 2D vs 3D | `S_dose_similarity_5FU_Olaparib` |
| **Suppl 5e** | drug-pair similarity 2D vs 3D by MoA | `09b_panel_c_moa_class.py` |
| **Suppl 6a** | DEG volcano (Plasmidsaurus) — *external* | — |
| **Suppl 6b** | gene-level log₂FC, G2M + SASP | `hallmark_nes_scatter` → *subset of* `signature_dumbbells_combined` |

`PCAUMAP_pathway_v2` and `3_PairwiseCorrlations copy` are parameterised by `data_type` and
`cell_line`, so each emits panels into Fig 4, Fig 5 **and** Suppl 4/5 in one run — which is
why `save_panel` derives the target figure from the panel name.

## Files to port

| | File | Note |
|---|---|---|
| IN | `1_Data/1_FeatureSorting` (exp1–4) | one per experiment |
| IN | `2_Processing/2_Pycytominer` (exp1–4) | exp1: repoint `150125` → `011225` |
| IN | `2_Processing/2_Pycytominer_certain_slices` (exp1) | `291025` correct as-is |
| IN | `2_Processing/2_DetectandCombine`, `1_Data/Prepare_metadata` (exp4) | |
| IN | `MIP_features/Pycytominer_MIP`, `2D_features/2D_profiles` | `selected_data_{MIP,2D}_*`, needed by Fig 4/5 |
| IN | `4_BioImageArchive/4_ImageBioArchive_Metadata` | deposition metadata; basis for the image downloader |
| IN | `GritScores/3_GritScores` | **code byte-identical to its `copy`** (337 lines each; the 17-byte delta is stored outputs) |
| IN | `RemoveNoise/Prepare_Slice_Features` | writes the PCA inputs; repoint `150125` → `011225` |
| IN | `expert-annotation/convert_npy_to_tiff.py` | utility for Suppl 2d/2e |
| IN → move | GritScores *computation* | compute in `2_Processing`, plot in the figure folder |
| OUT | `3_PairwiseCorrlations.ipynb` (plain) | subset of the `copy` |
| OUT | `3_GritScores copy.ipynb` | pure duplicate |
| OUT | `PCAUMAP_pathway.ipynb` | superseded by `_v2` |
| OUT | `RemoveNoise/old/*` | superseded by `BatchStratified` |
| OUT | exp1 + exp2 `3_PercentReplicating*`, exp3 `clearing_comparison{,_stats}` | superseded by `3_Robustness_Combined_Final` |
| OUT | exp2 `3_MAP.ipynb` | mAP dropped from the paper |
| OUT | exp4 `Radarplots/feature_heatmaps`, `0_Inspection`, `old/` | not in the paper |
| OUT | `1_Data/syto14_boxplot` | not in the paper |
| OUT | `gsea_nes_overview`, `oxphos_logfc_dumbbell` outputs | not in the paper |
| OUT | `focus_normalized_var_by_{compound,cellline}_z` outputs | not panels; only `focus_by_compound_z` is (Suppl 2c) |
| OUT | `REPRODUCIBILITY_METHODS.md` | dropped — documented three superseded notebooks |
| OUT | single-cell / Harmony: `1_SC_Harmony_streamlined*`, `reapply_harmony.py`, `sc_preprocess_harmony.py`, `olaparib_direction_magnitude.py` | never in the paper |
| OUT | organoids / colo8: `not_to_git/organoids_colo8/`, `colo8*-input/` | never in the paper |
| OUT | `generate_network_html*.py` ×4, `plot_similarity_*.py` ×4, `radial_*.py`, `force_graph_diff.py`, `plot_cluster_signature.py` *(but see KNOWN_ISSUES — it holds `parse_channel`, which Fig 5f needs)*, `10_5fu_top_neighbours.py`, `09_panel_c_recolor.py` | exploratory or superseded |
| OUT | `_archive/`, `.venv*/`, screenshots | not analysis |

> Exclusion means "not copied into the paper repo". Nothing is deleted from the source
> tree, and anything here can be pulled back in.

## Feature-set versions

Dumps are stamped `FeaturesImages_<DDMMYY>_none`; **the stamps are re-runs on the same
images, not different data** (identical schema/rows/wells, 99.5% bitwise equal, max diff
exactly 2⁻¹⁴). `150125` lives in `colopaint3D_fork` — which is why some notebooks `chdir`
there — and is the source of the published tables. exp1 therefore repoints to `011225` in
the main tree and the fork dependency disappears. `291025` is HCT116-only by design
(Suppl 3). `100125` is gone everywhere; the notebook written against it needs a column
translation:

| `100125` | current |
|---|---|
| `Cytoplasm_ObjectNumber` / `Nuclei_ObjectNumber` | `ObjectNumber_cytoplasm` / `ObjectNumber_nuclei` |
| `Cytoplasm_AreaShape_Area` | `AreaShape_Area_cytoplasm` |
| `Metadata_cmpd_cmpdname` / `Metadata_cmpd_cell_line` | `Metadata_cmpdname` / `Metadata_cell_line` |

The fork's `results/` tables are the same data as the main tree's (identical rows, columns
and features; only a pandas index artefact and one extra `Metadata_name` differ).

## exp4 — objective comparison (`colopaint3D_AZ`)

A fourth experiment, in a **separate repository**. Three acquisitions in one table, split by
`Metadata_Barcode`:

| Key | Dataset | Wells |
|---|---|---|
| `bomi_20241220` | `…20241220clearedspheroidsBOMI…` | 185 |
| `cleared3d_20250127` | `…20250127Cellpaintcleared3D…` | 160 |
| `wi_20250203` | `…CellPaint3DBomi_**WI**_for_Jordi…` | 132 |

All 8 compounds × 11 concentrations in each. No objective column anywhere, so air vs WI is
recoverable only from the acquisition name — see `KNOWN_ISSUES.md`. exp4 also carries three
near-identical copies of `utils/`; diff before collapsing, since a `replicate.py` divergence
would move Suppl 4i's numbers.

> Defects found on both sides of the port are in **`KNOWN_ISSUES.md`**.

## Open decisions

1. **`similarities_2D.csv`** — **decided: recompute** from `grit_data_2D_HCT116.parquet`
   in-repo, validating the regenerated 3D matrix against the surviving `similarities.csv`
   (38 drugs / 703 pairs).

### Settled

exp4 air = both non-WI acquisitions combined · Fig 2d = cell coverage · Fig 2f = spheroid plot · Fig 2g = PCA before/after · Fig 3c/3d = grit MIP/scAgg (renamed from A2/B2) · Fig 6b = EdU /
γH2AX · Fig 6c = hallmark GSEA scatter · Fig 6d = p53/E2F/p53-apoptosis dumbbells · Fig 6e =
`fig_5fu_neighbours_frozen_doses` · Suppl 1 (except 1d) and Suppl 2a/2b are images ·
Suppl 5e = `09b_panel_c_moa_class` (confirmed by its grey/blue/red/orange palette) ·
Suppl 6a external, 6b = G2M + SASP · Suppl 3 = `3_Robustness_Combined_Final` alone with
cached g/h tables · `3_PairwiseCorrlations` = the `copy` · `3_GritScores` = the original ·
mAP, Radarplots, `syto14_boxplot`, the `focus_normalized_var_*` outputs,
`gsea_nes_overview`, `oxphos_logfc_dumbbell` and `REPRODUCIBILITY_METHODS.md` are all out.
