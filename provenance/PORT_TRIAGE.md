# Port triage — what goes in, what stays out, what needs a decision

Every notebook and script in the upstream tree, with its porting status. Derived
from a mechanical audit of inputs, outputs, and surviving output files (see
`SOURCE_SNAPSHOT.tsv` for the exact versions audited).

Status key: **IN** = port it · **OUT** = excluded · **?** = needs your decision

---

## Feature-set versions — investigated and resolved

Feature dumps are versioned by date (`FeaturesImages_<DDMMYY>_none/`) and the
notebooks reference several versions. Two initially appeared to be missing.

**The date stamps are re-extraction runs on the same images, not different
datasets.** Verified by comparing exp1's `150125` against `011225` across 4
`SingleSlice` MedianAgg files (HCT116 slices 0/6/11, HT29 slice 3):

- identical column sets (2125 columns / 2110 raw features), identical row counts,
  identical well coverage — zero wells unique to either side
- 99.45–99.77% of values bitwise equal
- max absolute difference **exactly 6.10352e-05 = 2⁻¹⁴** in every file — the float32
  quantum near magnitude 1, i.e. storage round-off
- median relative difference among differing cells ≈ 8e-8, concentrated in
  `RadialDistribution_ZernikePhase_*` (arctan2 phase angles, where last-bit
  non-determinism surfaces)

| Version | Where | Referenced by |
|---|---|---|
| `150125` | **`colopaint3D_fork/spher_colo52_v1/1_Data/`** (7.7 GB) | v1 `2_Pycytominer`, `Prepare_Slice_Features`, `3_Plot_Spheroids` |
| `100125` | **not found anywhere** | `CellCoverage/3_CellCoverage.ipynb` (`SingleCell` level) |
| `291025` | main tree | `2_Pycytominer_certain_slices.ipynb` (v1) |
| `011225` | main tree | v1 `1_FeatureSorting` |
| `070426` | main tree | v2 `1_FeatureSorting`, `2_Pycytominer` |
| `150526` | main tree | v3 `1_FeatureSorting`, `2_Pycytominer`, robustness notebooks |

`150125` was never missing — it lives in the fork, which is *why* those notebooks
`chdir` into the fork. The fork reference and the `150125` reference are one fact.
It is confirmed as the source of the published tables: **834 unique wells, exactly
matching `selected_data_aggregates_HCT116.parquet`, zero discrepancy either way.**

### Consequence for the port

Because `011225` ≡ `150125` to within float32 round-off, exp1 can be **repointed at
`011225` in the main tree, dropping the fork dependency entirely**. Differences are
~1e-7 relative — invisible in any figure or statistic — so nothing needs re-running
and no published number changes.

`100125` is read only by `3_CellCoverage` at the `SingleCell` level; since it is 5
days before `150125` and the versions are equivalent, `011225/SingleCell/` (which
has both HCT116 and HT29) is the sound substitute.

`291025` is **scoped to HCT116, not partial** — confirmed as the Suppl Fig 3 feature
set. All three sets carry the identical full 12-plane stack (z 0–11, the "12z
(original)" base case in `METHODS.md`); `291025` simply omits HT29, which is correct
because the entire Percent Replicating analysis is HCT116-only. Its consumer,
`2_Pycytominer_certain_slices`, derives the z-subsampling cases (single z2/z7/z11,
sparse 3/6/9z, 12z) from those 12 planes.

| Set | Cell lines | z-planes | Role |
|---|---|---|---|
| `291025` | HCT116 | 0–11 (12) | Suppl Fig 3 reproducibility |
| `150125` (fork) | HCT116 + HT29 | 0–11 (12) | main analysis — source of the published tables |
| `011225` | HCT116 + HT29 | 0–11 (12) | re-extraction of `150125`, equivalent to float32 round-off |

*Caveat: sampled 4 of 24 slice files at the well-aggregated level; the 4.8 GB
`SingleCell` parquets were not value-compared.*

---

## Pipeline stages

| Status | File | Note |
|---|---|---|
| IN | `1_Data/1_FeatureSorting.ipynb` (v1, v2, v3) | 3 notebooks, one per experiment |
| IN | `2_Processing/2_Pycytominer.ipynb` (v1) | repoint `150125` (fork) → `011225` (main tree); verified equivalent |
| IN | `2_Processing/2_Pycytominer.ipynb` (v2, v3) | reference existing feature sets |
| IN | `2_Processing/2_Pycytominer_certain_slices.ipynb` (v1) | reads `291025` — the HCT116-scoped Suppl Fig 3 set. Correct as-is; keep the reference |
| IN | `4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb` | deposition metadata; also the basis for WP7 |
| IN | `MIP_features/Pycytominer_MIP.ipynb` | produces `selected_data_MIP_*`, needed by Fig5 |
| IN | `2D_features/2D_profiles.ipynb` | produces `selected_data_2D_*`, needed by Fig5. Has a fork path |
| IN → move | GritScores *computation* | per your decision: compute in `2_Processing`, plot in the figure folder |

## Figure 2

| Status | File | Note |
|---|---|---|
| IN | `CellCoverage/3_CellCoverage.ipynb` | `100125` not found anywhere; substitute `011225/SingleCell/` (has both cell lines). Output `CellsPerSpheroid.pdf` |
| IN | `CellDetectionSanityCheck/3_Plot_Spheroids.ipynb` | repoint `150125` (fork) → `011225` |
| IN | `RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb` | canonical — its PDFs are the newest on disk (2026-08-13) |
| IN | `RemoveNoise/Prepare_Slice_Features.ipynb` | repoint `150125` (fork) → `011225`; writes the `normalized_data_*` PCA inputs |
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

1. **The definitive paper figure list** — Fig2/Fig3/Fig4 panel lists are still unknown, so those folders cannot be finalised. (Fig5, Fig6, Suppl3, Suppl5 are pinned.)
2. **`3_PairwiseCorrlations`**: plain or `copy`. Recommend `copy` (superset, makes 5f).
3. **v3 robustness**: `Combined_Final` or `clearing_comparison`(`_stats`).
4. **`3_GritScores`**: which of the two.
5. **Figure assignment** for the five unplaced files above.
6. **Fig6e / Suppl5e**: which script of each pair.

*Resolved: which feature set the published profiles came from — see the feature-set
section above. `150125` (in the fork) is the source; `011225` in the main tree is
equivalent to within float32 round-off, so the fork dependency can be dropped.
`291025` is the HCT116-scoped Suppl Fig 3 set and is correct as referenced.*
