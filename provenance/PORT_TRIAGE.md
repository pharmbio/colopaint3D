# Port triage — what goes in, what stays out, what needs a decision

Every notebook and script in the upstream tree, with its porting status. Derived
from a mechanical audit of inputs, outputs, and surviving output files (see
`SOURCE_SNAPSHOT.tsv` for the exact versions audited).

Status key: **IN** = port it · **OUT** = excluded · **?** = needs your decision

---

## Blocking problem found during the port

**Three notebooks read feature dumps that no longer exist.** Feature sets are
versioned by date (`FeaturesImages_<DDMMYY>_none/`), and the code references two
versions that are not on disk:

| Referenced | Exists? | Referenced by |
|---|---|---|
| `FeaturesImages_150125_none` | **NO** | `2_Processing/2_Pycytominer.ipynb` (v1), `RemoveNoise/Prepare_Slice_Features.ipynb`, `CellDetectionSanityCheck/3_Plot_Spheroids.ipynb` |
| `FeaturesImages_100125_none` | **NO** | `CellCoverage/3_CellCoverage.ipynb` |
| `FeaturesImages_291025_none` | yes (2025-11-30) | `2_Pycytominer_certain_slices.ipynb` (v1) |
| `FeaturesImages_011225_none` | yes (2026-03-26) | `1_FeatureSorting.ipynb` (v1) |
| `FeaturesImages_070426_none` | yes (2026-04-07) | v2 `1_FeatureSorting`, `2_Pycytominer` |
| `FeaturesImages_150526_none` | yes (2026-05-15) | v3 `1_FeatureSorting`, `2_Pycytominer`, robustness notebooks |

So **experiment 1's own pipeline is internally inconsistent**: `1_FeatureSorting`
writes `011225`, `2_Pycytominer` reads `150125` (gone), and
`2_Pycytominer_certain_slices` reads `291025`. Three feature versions in one chain,
two of them referencing deleted directories.

This cannot be fixed by rewriting paths — it needs you to say **which feature set
the published `selected_data_*` / `grit_data_*` tables were actually built from.**
Until then those four notebooks are ported with their original reference preserved
and a `TODO` marker, rather than silently repointed at a version that would
produce different numbers.

---

## Pipeline stages

| Status | File | Note |
|---|---|---|
| IN | `1_Data/1_FeatureSorting.ipynb` (v1, v2, v3) | 3 notebooks, one per experiment |
| ? | `2_Processing/2_Pycytominer.ipynb` (v1) | reads the missing `150125` |
| IN | `2_Processing/2_Pycytominer.ipynb` (v2, v3) | reference existing feature sets |
| ? | `2_Processing/2_Pycytominer_certain_slices.ipynb` (v1) | reads `291025`, unlike its own v1 chain |
| IN | `4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb` | deposition metadata; also the basis for WP7 |
| IN | `MIP_features/Pycytominer_MIP.ipynb` | produces `selected_data_MIP_*`, needed by Fig5 |
| IN | `2D_features/2D_profiles.ipynb` | produces `selected_data_2D_*`, needed by Fig5. Has a fork path |
| IN → move | GritScores *computation* | per your decision: compute in `2_Processing`, plot in the figure folder |

## Figure 2

| Status | File | Note |
|---|---|---|
| ? | `CellCoverage/3_CellCoverage.ipynb` | reads the missing `100125`. Output `CellsPerSpheroid.pdf` |
| ? | `CellDetectionSanityCheck/3_Plot_Spheroids.ipynb` | reads the missing `150125` |
| IN | `RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb` | canonical — its PDFs are the newest on disk (2026-08-13) |
| ? | `RemoveNoise/Prepare_Slice_Features.ipynb` | reads the missing `150125`; writes the `normalized_data_*` PCA inputs |
| OUT | `RemoveNoise/old/5_PCA_RemoveNoise.ipynb` | superseded by BatchStratified |
| OUT | `RemoveNoise/old/5_PCA_RemoveNoise_and_FeatureImportance.ipynb` | superseded |

## Figure 3

| Status | File | Note |
|---|---|---|
| IN | `GritScores/3_GritScores_Figure3A2B2.ipynb` | makes `Figure3A2_grit_MIP`, `Figure3B2_grit_scAgg` — already panel-named |
| ? | `GritScores/3_GritScores.ipynb` vs `3_GritScores copy.ipynb` | **differ** despite identical size; needs a diff to pick |

## Figure 5 — 2D vs 3D (confirmed: 5a grit counting, 5b UMAP, 5c clustermap, 5d difference map, 5f fingerprints)

| Status | File | Note |
|---|---|---|
| ? | `PairwiseCorrelations/3_PairwiseCorrlations.ipynb` vs `... copy.ipynb` | **`copy` is the superset** — only it emits `fingerprints_2D/3D.pdf` (= 5f). Recommend `copy`; cost is rewriting its fork path |
| IN | `PCAUMAP/PCAUMAP_pathway_v2.ipynb` | canonical: `UMAP_supervised/unsupervised_pathway_*` on disk are its outputs |
| OUT | `PCAUMAP/PCAUMAP_pathway.ipynb` | superseded by v2 |

## Figure 6

| Status | File | Note |
|---|---|---|
| IN | `3_Figure6/DEG/hallmark_nes_scatter.ipynb` | GSEA/hallmark panels; ships its own dge + gsea CSVs |
| IN | `3_Figure6/EdU/EdU_analysis.ipynb` | already writes `panel_source_data.csv` — the pattern WP3 generalises |
| ? | `10_5fu_top_neighbours.py` / `fig_5fu_neighbours_frozen_doses.py` | you identified 6e as "top-10 similar to 5-FU in HCT116 and HT29" — which of these two is it? |

## Suppl Fig 3 — reproducibility (the only figure the reproducibility methods doc covers)

| Status | File | Note |
|---|---|---|
| IN | v1 `3_PercentReplicating_certain_slices.ipynb` | z-slice sampling, 52 compounds. The one well-powered comparison |
| IN | v2 `3_PercentReplicating.ipynb` | spheroid size / seeding density, incl. `seeding_brackets` |
| ? | v3: `3_Robustness_Combined_Final.ipynb` vs `clearing_comparison.ipynb` vs `clearing_comparison_stats.ipynb` | `Combined_Final` looks canonical (newest; its `combined/A2…C_*.pdf` panel names look final) but the methods doc cites `clearing_comparison.ipynb`. **Doc and files disagree** |
| OUT | v1 `3_PercentReplicating.ipynb`, `copy`, `copy 2` | superseded by `_certain_slices` |
| OUT | v2 `3_PercentReplicating_copy.ipynb` | duplicate |
| ? | v2 `3_MAP.ipynb`, v2/v3 `GritScores/3_GritScores.ipynb` | mAP + grit for the robustness experiments — in the paper or not? |

## Suppl Fig 5

| Status | File | Note |
|---|---|---|
| IN | `S_dose_similarity_5FU_Olaparib.ipynb` | = your "suppl5d dose-response grit 2D vs 3D ola+5-FU". `S_` prefix and surviving PDF agree |
| ? | `09b_panel_c_moa_class.py`, `09_panel_c_recolor.py` | = your "suppl5e drug-pair similarity 2D vs 3D coloured by antimetabolites/PARPi/DNA-damage"? Which of the two |

## Unplaced — needs a figure assignment

| Status | File | Note |
|---|---|---|
| ? | `expert-annotation/quantify_segmentation_error.ipynb` | `segmentation_error_analysis.svg` — segmentation validation |
| ? | `expert-annotation/error_propegation.ipynb` | `error_propagation_depth.svg` |
| ? | `expert-annotation/convert_npy_to_tiff.py` | 339 chars, utility for the annotation work |
| ? | `david_revision/focus_estimates.ipynb` | 6 focus-vs-z figures; "revision" suggests a reviewer response |
| ? | `1_Data/syto14_boxplot.ipynb` | `syto14_boxplot_HCT116.png` |

## Excluded — single-cell (your decision: out entirely, incl. feature extraction)

`1_SC_Harmony_streamlined.ipynb`, `..._copy.ipynb`, `..._new.ipynb`,
`reapply_harmony.py`, `sc_preprocess_harmony.py`,
`PairwiseCorrelations/olaparib_direction_magnitude.py` (reads `adata_qc_harmony.h5ad`)

## Excluded — organoids / colo8 (your decision: never made the paper)

`not_to_git/organoids_colo8/`, `not_to_git/colo8-input/`, `not_to_git/colo8-6sect-input/`

## Excluded — exploratory

| File | Why |
|---|---|
| `generate_network_html.py` + `copy`, `_p53pull`, `_profile_corr` | emit only interactive `.html`; no paper figure |
| `plot_similarity_network.py`, `plot_similarity_scatter.py`, `_cycling.py`, `_interactive.py` | superseded by the `09*_panel_c` scripts |
| `radial_analysis.py` (71 k), `radial_profile_analysis.py` | produced 5 `result-images-radial*` parameter-sweep folders |
| `force_graph_diff.py`, `plot_cluster_signature.py` | no surviving paper output |
| `result-images/Screenshot 2026-*.png` | screenshots |
| `_archive/`, `.venv/`, `.venv_map/` | not analysis |

> These are the "~19 Figure-4 extras" you wanted to discuss. Nothing here is
> deleted from the source tree — exclusion only means "not copied into the paper
> repo", and any of it can be pulled in later.

---

## Decisions needed, in priority order

1. **Which feature set (`FeaturesImages_*`) the published profiles came from** — blocks 4 notebooks.
2. **The definitive paper figure list** — Fig2/Fig3/Fig4 panel lists are still unknown, so those folders cannot be finalised. (Fig5, Fig6, Suppl3, Suppl5 are pinned.)
3. **`3_PairwiseCorrlations`**: plain or `copy`. Recommend `copy` (superset, makes 5f).
4. **v3 robustness**: `Combined_Final` or `clearing_comparison`(`_stats`).
5. **`3_GritScores`**: which of the two.
6. **Figure assignment** for the five unplaced files above.
7. **Fig6e / Suppl5e**: which script of each pair.
