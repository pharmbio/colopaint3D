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
| **Fig 6** ? | hallmark NES scatter | `DEG/hallmark_nes_scatter` → `hallmark_nes_scatter` | — |
| **Fig 6** ? | GSEA NES overview | same → `gsea_nes_overview` | — |
| **Fig 6** ? | OXPHOS gene-level log₂FC | same → `oxphos_logfc_dumbbell` — **panel or unused?** | — |
| **Fig 6** ? | EdU + γH2AX | `EdU/EdU_analysis` | — |
| **Fig 6e** | top-10 most similar to 5-FU, HCT116 & HT29 | `10_5fu_top_neighbours` **or** `fig_5fu_neighbours_frozen_doses` — **which?** | — |
| **Suppl 1d** | detected-cell spheroid plot, **HT29** | `CellDetectionSanityCheck/3_Plot_Spheroids` | — |
| **Suppl 1** (rest) | *images* — no code | — | — |
| **Suppl 2c** | mean focus per compound × z-slice | `david_revision/focus_estimates` | — |
| **Suppl 2d** | expert-annotation IoU / segmentation error | `expert-annotation/quantify_segmentation_error` | — |
| **Suppl 2e** | error propagation with depth | `expert-annotation/error_propegation` | — |
| **Suppl 2a, 2b** | **? presumed images** | | |
| **Suppl 3a** | z-plane subsampling | `3_Robustness_Combined_Final` → `A_zplane_subsampling` | exp1 slices |
| **Suppl 3b** | z-sampling density | same → `A2_zdensity` | exp3 sections |
| **Suppl 3c** | spheroid size (270/540/810 seeded) | same → `A3_spheroid_size` | exp2 `grit_section*` |
| **Suppl 3d** | clearing | same → `A4_clearing` | exp3 sections |
| **Suppl 3e** | magnification | same → `A5_magnification` | exp3 sections |
| **Suppl 3f** | *image* — no code | — | — |
| **Suppl 3g** | intensity vs depth, two sizes | same → `B_bleaching` | **feature dumps** |
| **Suppl 3h** | cell detection vs depth by clearing | same → `C_detection_depth` | **feature dumps** |
| **Suppl 4a–f** | exactly Fig 4a–f but for **HT29** | same notebooks, `cell_line='HT29'` | `MIP`, `aggregates` |
| **Suppl 4g** | *images* — no code | — | — |
| **Suppl 4h** | UMAP unsupervised + labelled, air vs WI objective | **`colopaint3D_AZ`** `3_Figure3/UMAP/3_PCA.ipynb` | exp4 |
| **Suppl 4i** | reproducibility, same objectives | **`colopaint3D_AZ`** `PercentReplicating/3_Fig_TechnicalReplicates.ipynb` | exp4 |
| **Suppl 5a** | 2D UMAP fingerprints, **HT29** | `PCAUMAP/PCAUMAP_pathway_v2` | `2D`, HT29 |
| **Suppl 5b** | 2D clustermap, **HT29** | `3_PairwiseCorrlations` → `PairwiseCorrelations_HT29_2D` | `2D`, HT29 |
| **Suppl 5c** | difference in similarity | same → `Difference_HT29_colored_tails` | HT29 |
| **Suppl 5d** | grit-score dose example, HCT116 2D vs 3D | `S_dose_similarity_5FU_Olaparib` | — |
| **Suppl 5e** | drug-pair similarity 2D vs 3D, HCT116, coloured by MoA | `09b_panel_c_moa_class` (MoA colouring matches; `09_panel_c_recolor` looks like its predecessor) | — |
| **Suppl 6a** | DEG volcano (Plasmidsaurus) — *not in this analysis* | external / vendor | — |
| **Suppl 6b** | gene-level log₂FC, G2M checkpoint + SASP | `DEG/hallmark_nes_scatter` → `signature_dumbbells_combined` | — |

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

**Resolved: one notebook makes the whole figure.** `3_Robustness_Combined_Final.ipynb`
emits all seven code panels (a–e, g, h) into `result-images/combined/`, and its output
names map 1:1 onto the paper's lettering. It reads all three experiments itself.

| | File | Note |
|---|---|---|
| IN | v3 `3_Robustness_Combined_Final.ipynb` | **canonical** — the entire Suppl Fig 3 |
| OUT | v3 `clearing_comparison.ipynb`, `clearing_comparison_stats.ipynb` | predecessors, superseded by `Combined_Final` |
| OUT | v1 `3_PercentReplicating_certain_slices.ipynb` | superseded: panel a now comes from `Combined_Final` |
| OUT | v2 `3_PercentReplicating.ipynb` | superseded: panel c now comes from `Combined_Final` |
| OUT | v1 `3_PercentReplicating{,copy,copy 2}.ipynb`, v2 `_copy` | duplicates |
| OUT | v2 `3_MAP.ipynb` | **mAP dropped from the paper** |
| ? | v2+v3 `GritScores/3_GritScores.ipynb` | grit for the robustness experiments — in the paper or not |

> ⚠️ **`METHODS.md` is now stale.** It documents the metric, null model and tests as
> implemented in `_certain_slices` (exp1), `3_PercentReplicating` (exp2) and
> `clearing_comparison` (exp3) — **all three of which are superseded**. The statistics
> actually behind the published panels live in `Combined_Final`'s `panel_analysis()`.
> The doc must be re-derived from that notebook before submission, including whether its
> null and multiple-comparison handling match what `METHODS.md` claims.

> ⚠️ **Panels g and h do not run from the downloaded profile tier.** They read
> `FeaturesImages_*/SingleSlice` and `SingleCell` for exp1 and exp3 — part of the
> 19.5 GB that no tier covers. Either deposit those dumps, or have `Combined_Final`
> cache the per-depth intensity and detection summaries as small tables that ship with
> the repo. Without one of the two, "every figure regenerates from the download" is
> false for Suppl 3g/h.

## Suppl Fig 4h/i — exp4, objective comparison (`colopaint3D_AZ`)

A **fourth experiment**, in a **separate repository** from the colopaint3D tree. Three
acquisitions; `_WI_` is the water-immersion set:

| Key | Upstream dataset name |
|---|---|
| `bomi_20241220` | `CellPainting_20241220clearedspheroidsBOMI_20241220_151510` |
| `cleared3d_20250127` | `CellPainting_20250127Cellpaintcleared3D_20250127_171120` |
| `wi_20250203` | `CellPainting_CellPaint3DBomi_**WI**_for_Jordi_20250203_155142` |

| | File | Note |
|---|---|---|
| IN | `1_Data/1_FeatureSorting.ipynb` (+ `_script.py`) | exp4 feature sorting |
| IN | `1_Data/Prepare_metadata.ipynb` | exp4 metadata |
| IN | `2_Processing/2_Pycytominer.ipynb` | exp4 processing |
| IN | `2_Processing/2_DetectandCombine.ipynb` | exp4 detection/combination |
| IN | `3_Figure3/UMAP/3_PCA.ipynb` | **Suppl 4h** — `UMAP_labeled/unlabeled_*`, `PCA_unlabeled_*` |
| IN | `3_Figure3/PercentReplicating/3_Fig_TechnicalReplicates.ipynb` | **Suppl 4i** — `TechnicalReplicates_repl_corrs_*` |
| ? | `3_Figure3/Radarplots/feature_heatmaps.ipynb` | radar / feature heatmaps — not in the Suppl 4 lettering; in the paper? |
| OUT | `0_Inspection/0_renderImages.ipynb`, `old/` | inspection / superseded |

**Which dataset is "air"?** The lettering says *air vs WI*, and `wi_20250203` is clearly
WI — but there are two non-WI acquisitions (`bomi_20241220`, `cleared3d_20250127`) and
outputs exist for all three. Needs confirming which is the air comparator, and whether
the third is used at all.

**Duplicated utils.** exp4 carries three near-identical copies of `utils/` (`utils.py`,
`replicate.py`) under `PercentReplicating/`, `Radarplots/` and `UMAP/`, with differing
dates. These should collapse into the repo-level `utils/`, after diffing them — a
`replicate.py` divergence would change Suppl 4i's numbers.

## Suppl Fig 5

| | File | Note |
|---|---|---|
| IN | `S_dose_similarity_5FU_Olaparib.ipynb` | = suppl5d dose-response grit 2D vs 3D |
| ? | `09b_panel_c_moa_class.py` vs `09_panel_c_recolor.py` | which makes suppl5e |

## Supplementary 1 & 2 analyses (placed)

| | File | Panel |
|---|---|---|
| IN | `CellDetectionSanityCheck/3_Plot_Spheroids` (HT29 output) | Suppl 1d |
| IN | `david_revision/focus_estimates` | Suppl 2c |
| IN | `expert-annotation/quantify_segmentation_error` | Suppl 2d |
| IN | `expert-annotation/error_propegation` | Suppl 2e |
| IN | `expert-annotation/convert_npy_to_tiff.py` | utility for the annotation work (339 chars) |

`focus_estimates` emits three figure pairs; only `focus_by_compound_z` is assigned to
2c. Whether `focus_normalized_var_by_compound_z` and
`focus_normalized_var_by_cellline_z` are further panels is **unresolved**.

## Unplaced — still need a figure assignment

`1_Data/syto14_boxplot.ipynb` → `syto14_boxplot_HCT116.png`

## Excluded

- **Single-cell / Harmony** (never in the paper): `1_SC_Harmony_streamlined{,_copy,_new}.ipynb`, `reapply_harmony.py`, `sc_preprocess_harmony.py`, `olaparib_direction_magnitude.py`
- **Organoids / colo8** (never in the paper): `not_to_git/organoids_colo8/`, `colo8*-input/`
- **Exploratory**: `generate_network_html*.py` ×4 (HTML only) · `plot_similarity_*.py` ×4 (superseded by `09*_panel_c`) · `radial_analysis.py`, `radial_profile_analysis.py` (5 parameter-sweep output folders) · `force_graph_diff.py`, `plot_cluster_signature.py` (no surviving output) · screenshots · `_archive/`, `.venv*/`

> Exclusion means "not copied into the paper repo" — nothing is deleted from the
> source tree, and any of it can be pulled back in.

## Open decisions

1. **Panel lettering** — Fig 2 (cells-per-spheroid, spheroid plot, PCA before/after), Fig 3 (are there A1/B1 alongside A2/B2?), Suppl 4 (HT29). The CellCoverage panel is currently written as `Fig2d`, **a guess**, and that name is baked into the figure file, source-data filename and manifest.
2. **Suppl 6** — entirely unknown.
3. **Suppl 2a/2b** — presumed images; confirm.
4. **`3_PairwiseCorrlations`** — plain or `copy`. Recommend `copy` (only it makes Fig 5f).
5. **v3 robustness** — `Combined_Final` or `clearing_comparison{,_stats}`; files and `METHODS.md` disagree.
6. **`3_GritScores`** — which of the two.
7. **Fig 6e / Suppl 5e** — which script of each pair.
8. **`syto14_boxplot`** — which figure, if any.
9. **`focus_estimates`** — are the two `normalized_var` outputs also panels?
