#!/usr/bin/env python3
"""Port a notebook from the upstream tree into this repo, changing only its paths.

Design rule: **the analysis code is copied verbatim.** This tool rewrites the
path preamble and known path literals, and *reports* anything it is not
confident about instead of guessing. Everything it cannot resolve is left in
place and listed, so the remaining work is visible rather than silently wrong.

    python provenance/port_notebook.py --list
    python provenance/port_notebook.py 1_FeatureSorting_exp1 --dry-run
    python provenance/port_notebook.py --all --dry-run

Each port emits a report of:
  * `os.chdir` calls removed
  * path literals rewritten
  * absolute paths still present  (MANUAL)
  * `savefig` calls not yet converted to `save_panel`  (MANUAL)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC_ROOT = Path("/share/data/analyses/christa")

BOOTSTRAP = [
    "# --- repo path bootstrap (added by the port) ---\n",
    "import sys, pathlib\n",
    'ROOT = next(p for p in pathlib.Path.cwd().parents if (p / "utils" / "paths.py").is_file())\n',
    "sys.path.insert(0, str(ROOT))\n",
    "from utils.paths import (profiles, features, feature_output, figdir, metadata,\n"
    "                         data_dir, external, require)\n",
    "from utils.panels import save_panel\n",
]

# Upstream absolute prefixes that must not survive the port.
ABS_PREFIXES = [
    "/share/data/analyses/christa/colopaint3D_fork/spher_colo52_v1",
    "/share/data/analyses/christa/colopaint3D_AZ/spher_colo52_v1",
    "/home/jovyan/share/data/analyses/christa/colopaint3D/spher_colo52_v1",
    "/share/data/analyses/christa/colopaint3D/spher_colo52_v1",
    "/share/data/analyses/christa/colopaint3D/spher_colo52_v2",
    "/share/data/analyses/christa/colopaint3D/spher_colo52_v3",
    "/home/jovyan/share/data/analyses/christa/colopaint3D",
    "/share/data/analyses/christa/colopaint3D",
]

# Relative paths the notebooks use *after* chdir, mapped to helper calls.
# (pattern, replacement template). Applied per experiment key.
REL_REWRITES = [
    (r"'1_Data/results/slices/([^']+)'", r'profiles("{exp}", "slices/\1")'),
    (r"'1_Data/results/sections/([^']+)'", r'profiles("{exp}", "sections/\1")'),
    (r"'1_Data/results/([^']+)'", r'profiles("{exp}", "\1")'),
    (r"'1_Data/results/'", r'str(profiles("{exp}", "")) + "/"'),
    (r"'1_Data/FeaturesImages_(\d+)_none/([A-Za-z]+)/'", r'str(features("{exp}", "\1", "\2")) + "/"'),
    (r"'1_Data/FeaturesImages_(\d+)_none/([A-Za-z]+)'", r'features("{exp}", "\1", "\2")'),
    (r"'1_Data/(spher[^']*\.csv)'", r'metadata("\1", "{exp}")'),
]

# Absolute upstream paths -> helper calls. Q matches either quote style.
Q = "['\"]"
ABS_ANY = r"/(?:home/jovyan/)?share/data/analyses/christa/colopaint3D(?:_fork|_AZ)?"
ABS_REWRITES = [
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/results/slices/([^'\"]+)" + Q,
     r'profiles("{exp}", "slices/\1")'),
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/results/sections/([^'\"]+)" + Q,
     r'profiles("{exp}", "sections/\1")'),
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/results/([^'\"]+)" + Q,
     r'profiles("{exp}", "\1")'),
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/FeaturesImages_(\d+)_none/([A-Za-z]+)/?([^'\"]*)" + Q,
     r'features("{exp}", "\1", "\2")'),
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/(spher[^'\"]*\.csv)" + Q,
     r'metadata("\1", "{exp}")'),
    (Q + ABS_ANY + r"/spher_colo52_v\d/1_Data/?" + Q,
     r'str(data_dir("{exp}")) + "/"'),
]

# What to port. dest is relative to analysis/.
JOBS = {
    "1_FeatureSorting_exp1": ("colopaint3D/spher_colo52_v1/1_Data/1_FeatureSorting.ipynb",
                              "1_Data/exp1_main/1_FeatureSorting.ipynb", "exp1_main"),
    "1_FeatureSorting_exp2": ("colopaint3D/spher_colo52_v2/1_Data/1_FeatureSorting.ipynb",
                              "1_Data/exp2_spheroid_size/1_FeatureSorting.ipynb", "exp2_spheroid_size"),
    "1_FeatureSorting_exp3": ("colopaint3D/spher_colo52_v3/1_Data/1_FeatureSorting.ipynb",
                              "1_Data/exp3_clearing_mag_z/1_FeatureSorting.ipynb", "exp3_clearing_mag_z"),
    "1_FeatureSorting_exp4": ("colopaint3D_AZ/spher_colo52_v1/1_Data/1_FeatureSorting.ipynb",
                              "1_Data/exp4_objective/1_FeatureSorting.ipynb", "exp4_objective"),
    "Prepare_metadata_exp4": ("colopaint3D_AZ/spher_colo52_v1/1_Data/Prepare_metadata.ipynb",
                              "1_Data/exp4_objective/Prepare_metadata.ipynb", "exp4_objective"),
    "2_Pycytominer_exp1": ("colopaint3D/spher_colo52_v1/2_Processing/2_Pycytominer.ipynb",
                           "2_Processing/exp1_main/2_Pycytominer.ipynb", "exp1_main"),
    "2_Pycytominer_slices_exp1": ("colopaint3D/spher_colo52_v1/2_Processing/2_Pycytominer_certain_slices.ipynb",
                                  "2_Processing/exp1_main/2_Pycytominer_certain_slices.ipynb", "exp1_main"),
    "2_Pycytominer_exp2": ("colopaint3D/spher_colo52_v2/2_Processing/2_Pycytominer.ipynb",
                           "2_Processing/exp2_spheroid_size/2_Pycytominer.ipynb", "exp2_spheroid_size"),
    "2_Pycytominer_exp3": ("colopaint3D/spher_colo52_v3/2_Processing/2_Pycytominer.ipynb",
                           "2_Processing/exp3_clearing_mag_z/2_Pycytominer.ipynb", "exp3_clearing_mag_z"),
    "2_Pycytominer_exp4": ("colopaint3D_AZ/spher_colo52_v1/2_Processing/2_Pycytominer.ipynb",
                           "2_Processing/exp4_objective/2_Pycytominer.ipynb", "exp4_objective"),
    "2_DetectandCombine_exp4": ("colopaint3D_AZ/spher_colo52_v1/2_Processing/2_DetectandCombine.ipynb",
                                "2_Processing/exp4_objective/2_DetectandCombine.ipynb", "exp4_objective"),
    "MIP_features": ("colopaint3D/MIP_features/Pycytominer_MIP.ipynb",
                     "2_Processing/exp1_main/Pycytominer_MIP.ipynb", "exp1_main"),
    "2D_features": ("colopaint3D/spher_colo52_v1/2D_features/2D_profiles.ipynb",
                    "2_Processing/exp1_main/2D_profiles.ipynb", "exp1_main"),
    "BioImageArchive": ("colopaint3D/spher_colo52_v1/4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb",
                        "../analysis/4_BioImageArchive/4_ImageBioArchive_Metadata.ipynb", "exp1_main"),
    "CellDetection": ("colopaint3D/spher_colo52_v1/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb",
                      "3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb", "exp1_main"),
    "PrepareSlices": ("colopaint3D/spher_colo52_v1/3_Figure2/RemoveNoise/Prepare_Slice_Features.ipynb",
                      "3_Figure2/RemoveNoise/Prepare_Slice_Features.ipynb", "exp1_main"),
    "PCA_RemoveNoise": ("colopaint3D/spher_colo52_v1/3_Figure2/RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb",
                        "3_Figure2/RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb", "exp1_main"),
    "GritScores": ("colopaint3D/spher_colo52_v1/3_Figure3/GritScores/3_GritScores.ipynb",
                   "2_Processing/exp1_main/3_GritScores.ipynb", "exp1_main"),
    "GritScores_Fig3": ("colopaint3D/spher_colo52_v1/3_Figure3/GritScores/3_GritScores_Figure3A2B2.ipynb",
                        "3_Figure3/3_GritScores_Fig3cd.ipynb", "exp1_main"),
    # Fig 3e/3f. Originally excluded as "superseded by 3_Robustness_Combined_Final",
    # but that notebook is the z-subsampling analysis behind Suppl Fig 3 — a different
    # question. Its result-images/PercentReplicating_{MIP,aggregates}.pdf are the
    # published 3e and 3f.
    "PercentReplicating": ("colopaint3D/spher_colo52_v1/3_Figure3/PercentReplicating/3_PercentReplicating.ipynb",
                           "3_Figure3/3_PercentReplicating.ipynb", "exp1_main"),
    "PCAUMAP": ("colopaint3D/spher_colo52_v1/3_Figure4/PCAUMAP/PCAUMAP_pathway_v2.ipynb",
                "3_Figure4/PCAUMAP_pathway_v2.ipynb", "exp1_main"),
    "PairwiseCorrelations": ("colopaint3D/spher_colo52_v1/3_Figure4/PairwiseCorrelations/3_PairwiseCorrlations copy.ipynb",
                             "3_Figure4/3_PairwiseCorrelations.ipynb", "exp1_main"),
    "DoseSimilarity": ("colopaint3D/spher_colo52_v1/3_Figure4/PairwiseCorrelations/S_dose_similarity_5FU_Olaparib.ipynb",
                       "3_SupplFigure5/S_dose_similarity_5FU_Olaparib.ipynb", "exp1_main"),
    "Robustness": ("colopaint3D/spher_colo52_v3/3_Figure3/3_Robustness_Combined_Final.ipynb",
                   "3_SupplFigure3/3_Robustness_Combined_Final.ipynb", "exp3_clearing_mag_z"),
    "EdU": ("colopaint3D/spher_colo52_v1/3_Figure6/EdU/EdU_analysis.ipynb",
            "3_Figure6/EdU/EdU_analysis.ipynb", "exp1_main"),
    "DEG": ("colopaint3D/spher_colo52_v1/3_Figure6/DEG/hallmark_nes_scatter.ipynb",
            "3_Figure6/DEG/hallmark_nes_scatter.ipynb", "exp1_main"),
    "SegError": ("colopaint3D/expert-annotation/quantify_segmentation_error.ipynb",
                 "3_SupplFigure2/quantify_segmentation_error.ipynb", "exp1_main"),
    "ErrorProp": ("colopaint3D/expert-annotation/error_propegation.ipynb",
                  "3_SupplFigure2/error_propegation.ipynb", "exp1_main"),
    "Focus": ("colopaint3D/david_revision/focus_estimates.ipynb",
              "3_SupplFigure2/focus_estimates.ipynb", "exp1_main"),
    "UMAP_exp4": ("colopaint3D_AZ/spher_colo52_v1/3_Figure3/UMAP/3_PCA.ipynb",
                  "3_SupplFigure4/3_PCA_objective.ipynb", "exp4_objective"),
    "TechRep_exp4": ("colopaint3D_AZ/spher_colo52_v1/3_Figure3/PercentReplicating/3_Fig_TechnicalReplicates.ipynb",
                     "3_SupplFigure4/3_Fig_TechnicalReplicates.ipynb", "exp4_objective"),
}

EXP4_TAGS = '\n# One output per acquisition. NOTE: the published Suppl 4h/4i "air" panel is the two\n# non-WI acquisitions COMBINED (see PORT_TRIAGE); this notebook emits them separately.\nPLATE_TAG = {\n    \'CellPainting_20241220clearedspheroidsBOMI_20241220_151510\': \'bomi\',\n    \'CellPainting_20250127Cellpaintcleared3D_20250127_171120\':   \'cleared3d\',\n    \'CellPainting_CellPaint3DBomi_WI_for_Jordi_20250203_155142\': \'wi\',\n}\n'

ROB_HELPERS = '\n# fname used by panel_analysis -> paper panel. Panels g and h (bleaching, detection\n# depth) are saved inline further down and need the feature dumps; see PORT_TRIAGE.\nFNAME_PANEL = {\n    "A_zplane_subsampling": "SupplFig3a",\n    "A2_zdensity":          "SupplFig3b",\n    "A3_spheroid_size":     "SupplFig3c",\n    "A4_clearing":          "SupplFig3d",\n    "A5_magnification":     "SupplFig3e",\n    "B_bleaching":          "SupplFig3g",\n    "C_detection_depth":    "SupplFig3h",\n}\n\n\ndef panel_source_table(order, repl, null):\n    """The per-compound replicate r and the null draw behind each box."""\n    import pandas as _pd\n    rows = []\n    for case in order:\n        s = repl[case]\n        rows.append(_pd.DataFrame({"case": case, "kind": "replicate",\n                                   "compound": list(s.index), "r": list(s.values)}))\n        rows.append(_pd.DataFrame({"case": case, "kind": "null",\n                                   "compound": None, "r": list(null[case])}))\n    return _pd.concat(rows, ignore_index=True)\n'

PW_PANEL_ESCAPED = '\n# Paper panel for this (cell_line, data_type). One run per combination; save_panel\n# routes each to its figure. The clustermap appears in Fig4, Fig5 and both supplements.\nCLUSTERMAP_PANEL = {\n    ("HCT116", "MIP"):        "Fig4e",\n    ("HCT116", "aggregates"): "Fig4f",\n    ("HCT116", "2D"):         "Fig5c",\n    ("HT29",   "MIP"):        "SupplFig4e",\n    ("HT29",   "aggregates"): "SupplFig4f",\n    ("HT29",   "2D"):         "SupplFig5b",\n}\n# The 2D-minus-3D difference map depends only on the cell line.\nDIFFERENCE_PANEL = {"HCT116": "Fig5d", "HT29": "SupplFig5c"}\n'

NOT_A_PANEL = {'DEG': ["fig\\.savefig\\(FIG_DIR / f'\\{OUT4\\}\\.(?:pdf|svg|png)'[^)]*\\)", "fig\\.savefig\\(FIG_DIR / f'gsea_nes_overview\\.\\{ext\\}'[^)]*\\)"], 'Focus': ['fig3\\.savefig\\(OUT_DIR / \\"focus_normalized_var_by_compound_z\\.(?:png|pdf)\\"[^)]*\\)', 'fig4\\.savefig\\(OUT_DIR / \\"focus_normalized_var_by_cellline_z\\.(?:png|pdf)\\"[^)]*\\)'], 'EdU': ["fig\\.savefig\\(FIG_DIR / 'EdU_threshold_histogram\\.png'[^)]*\\)", "fig\\.savefig\\(FIG_DIR / f'\\{metric\\}\\.png'[^)]*\\)", "fig\\.savefig\\(FIG_DIR / 'yH2AX_foci_3D_projections\\.png'[^)]*\\)"], 'MIP_features': ['plt\\.savefig\\(\\"\\{\\}/\\{\\}_QC\\.pdf\\"\\.format\\(OutputDir, plate\\)[^)]*\\)'], 'UMAP_exp4': ['fig\\.savefig\\(\\"\\{\\}/\\{\\}_\\{\\}_\\{\\}\\.\\{\\}\\"\\.format\\(dir, \\"PCA\\", \'unlabeled\', plate, \'pdf\'\\)[\\s\\S]*?\\n\\s*\\)'], 'GritScores': ['fig\\.savefig\\([\\s\\S]*?GritScores[\\s\\S]*?\\n\\s*\\)']}

PANEL_BLOCK_ESCAPED = '\n# Paper panel for this (cell_line, data_type, embedding) combination. The notebook is\n# run once per combination; save_panel routes each to the right figure folder.\nPANEL = {\n    ("HCT116", "MIP",        "supervised"):   "Fig4a",\n    ("HCT116", "aggregates", "supervised"):   "Fig4b",\n    ("HCT116", "MIP",        "unsupervised"): "Fig4c",\n    ("HCT116", "aggregates", "unsupervised"): "Fig4d",\n    ("HT29",   "MIP",        "supervised"):   "SupplFig4a",\n    ("HT29",   "aggregates", "supervised"):   "SupplFig4b",\n    ("HT29",   "MIP",        "unsupervised"): "SupplFig4c",\n    ("HT29",   "aggregates", "unsupervised"): "SupplFig4d",\n    # NOTE: no 2D outputs survive upstream, so these two are UNVERIFIED.\n    ("HCT116", "2D",         "supervised"):   "Fig5b",\n    ("HT29",   "2D",         "supervised"):   "SupplFig5a",\n}\n'

# Per-notebook edits that the generic rules cannot express. Kept HERE rather than
# applied by hand, because `--all` regenerates every notebook from source and would
# silently discard manual fixes.
POST_EDITS = {
    "Robustness": [
        (r"for ext in \('pdf', 'png'\): fig\.savefig\(f'\{OUT\}/B_bleaching\.\{ext\}', "
         r"dpi=DPI, bbox_inches='tight'\)",
         "save_panel(fig, 'SupplFig3g',\n"
         "           data=pd.read_csv(CACHE_3G),\n"
         "           caption='Channel intensity vs imaging depth, two spheroid sizes',\n"
         "           notebook='analysis/3_SupplFigure3/3_Robustness_Combined_Final.ipynb')"),
        (r"for ext in \('pdf', 'png'\): fig\.savefig\(f'\{OUT\}/C_detection_depth\.\{ext\}', "
         r"dpi=DPI, bbox_inches='tight'\)",
         "save_panel(fig, 'SupplFig3h',\n"
         "           data=pd.read_csv(CACHE_3H),\n"
         "           caption='Cell detection vs imaging depth by clearing condition',\n"
         "           notebook='analysis/3_SupplFigure3/3_Robustness_Combined_Final.ipynb')"),
        (r"MARGIN = 0\.10", ROB_HELPERS + "\nMARGIN = 0.10"),
        (r"for ext in \('pdf', 'png'\): fig\.savefig\(f'\{OUT\}/\{fname\}\.\{ext\}', "
         r"dpi=DPI, bbox_inches='tight'\)",
         "save_panel(fig, FNAME_PANEL[fname],\n"
         "               data=panel_source_table(order, repl, null),\n"
         "               caption=title,\n"
         "               notebook='analysis/3_SupplFigure3/3_Robustness_Combined_Final.ipynb')"),
        (r"ROOT\s*=\s*'/share/data/analyses/christa/colopaint3D'\n", ""),
        (r"V3SEC\s*=\s*f'\{ROOT\}/spher_colo52_v3/1_Data/results/sections'",
         'V3SEC      = profiles("exp3_clearing_mag_z", "sections")'),
        (r"V3_SLICE\s*=\s*f'\{ROOT\}/spher_colo52_v3/1_Data/FeaturesImages_150526_none/SingleSlice'",
         'V3_SLICE   = features("exp3_clearing_mag_z", "150526", "SingleSlice")'),
        (r"V3_SC\s*=\s*f'\{ROOT\}/spher_colo52_v3/1_Data/FeaturesImages_150526_none/SingleCell/HCT116\.parquet'",
         'V3_SC      = features("exp3_clearing_mag_z", "150526", "SingleCell", "HCT116.parquet")'),
        (r"V1_AGG\s*=\s*f'\{ROOT\}/spher_colo52_v1/1_Data/results/selected_data_aggregates_HCT116\.parquet'",
         'V1_AGG     = profiles("exp1_main", "selected_data_aggregates_HCT116.parquet")'),
        (r"V1_SLICE\s*=\s*f'\{ROOT\}/spher_colo52_v1/1_Data/FeaturesImages_011225_none/SingleSlice'",
         'V1_SLICE   = features("exp1_main", "011225", "SingleSlice")'),
        (r"V1_SC\s*=\s*f'\{ROOT\}/spher_colo52_v1/1_Data/FeaturesImages_011225_none/SingleCell/HCT116\.parquet'",
         'V1_SC      = features("exp1_main", "011225", "SingleCell", "HCT116.parquet")'),
        (r"V1_SLICES\s*=\s*f'\{ROOT\}/spher_colo52_v1/1_Data/results/slices'",
         'V1_SLICES  = profiles("exp1_main", "slices")'),
        (r"V2SEC\s*=\s*f'\{ROOT\}/spher_colo52_v2/1_Data/results/sections'",
         'V2SEC = profiles("exp2_spheroid_size", "sections")'),
        (r"OUT\s*=\s*f'\{ROOT\}/spher_colo52_v3/3_Figure3/result-images/combined'",
         'OUT        = figdir("SupplFig3")\n'
         '# Panels g/h aggregate the 19.5 GB feature dumps; the aggregation they plot is\n'
         '# committed here so the panels regenerate without the dumps.\n'
         'CACHE_3G   = ROOT / "analysis" / "3_SupplFigure3" / "data" / "suppl3g_bleaching_perwell.csv"\n'
         'CACHE_3H   = ROOT / "analysis" / "3_SupplFigure3" / "data" / "suppl3h_detection_perwell.csv"'),
    ],
    "Focus": [
        (r'BASE = Path\("/share/data/analyses/christa/colopaint3D/david_revision/spher-colo52"\)',
         '# Segmentation focus scores, shipped with the repo (18 small CSVs)\n'
         'BASE = ROOT / "analysis" / "3_SupplFigure2" / "data" / "spher-colo52"'),
        (r'OUT_DIR = Path\("/share/data/analyses/christa/colopaint3D/david_revision"\)',
         'OUT_DIR = figdir("SupplFig2")'),
        (r'fig\.savefig\(OUT_DIR / "focus_by_compound_z\.png", dpi=150, bbox_inches="tight"\)\n'
         r'fig\.savefig\(OUT_DIR / "focus_by_compound_z\.pdf", bbox_inches="tight"\)',
         'save_panel(fig, "SupplFig2c", data=mean_focus,\n'
         '           caption="Mean focus (Laplacian variance) per compound and z-slice",\n'
         '           notebook="analysis/3_SupplFigure2/focus_estimates.ipynb")'),
    ],
    "PCAUMAP": [
        (r'"3_Figure4/PCAUMAP/result-images/per_pathway_metrics_\{\}_\{\}\.csv"',
         'str(figdir("Fig4")) + "/per_pathway_metrics_{}_{}.csv"'),
        (r'"3_Figure4/PCAUMAP/result-images/permutation_test_results_\{\}_\{\}\.txt"',
         'str(figdir("Fig4")) + "/permutation_test_results_{}_{}.txt"'),
        (r"grit_threshold = 1\.96", "grit_threshold = 1.96\n" + PANEL_BLOCK_ESCAPED),
        # supervised UMAP -> Fig4a/4b, SupplFig4a/4b (or Fig5b / SupplFig5a for 2D)
        (r'fig\.savefig\(\n\s*"3_Figure4/PCAUMAP/result-images/UMAP_supervised_pathway_\{\}_\{\}\.\{\}"'
         r'\.format\(cell_line, data_type,figformat\), dpi=dpi, bbox_inches="tight"\n\s*\)',
         'save_panel(fig, PANEL[(cell_line, data_type, "supervised")],\n'
         '           data=results_supervised,\n'
         '           caption=f"Supervised UMAP coloured by pathway, {cell_line} {data_type}",\n'
         '           notebook="analysis/3_Figure4/PCAUMAP_pathway_v2.ipynb")'),
        # unsupervised KMeans/true-pathway pair -> Fig4c/4d, SupplFig4c/4d
        (r'fig\.savefig\(\n\s*"3_Figure4/PCAUMAP/result-images/UMAP_unsupervised_pathway_\{\}_\{\}\.\{\}"'
         r'\.format\(cell_line, data_type,figformat\), dpi=dpi, bbox_inches="tight"\n\s*\)',
         'save_panel(fig, PANEL[(cell_line, data_type, "unsupervised")],\n'
         '           data=pd.DataFrame({"umap1": embedding[:, 0], "umap2": embedding[:, 1],\n'
         '                              "kmeans_cluster": pred_labels,\n'
         '                              "pathway": pathway_labels_filtered}),\n'
         '           caption=f"Unsupervised UMAP, KMeans clusters vs pathway, {cell_line} {data_type}",\n'
         '           notebook="analysis/3_Figure4/PCAUMAP_pathway_v2.ipynb")'),
    ],
    "PairwiseCorrelations": [
        # data_2D is used by the fingerprint cells but is defined NOWHERE in the
        # source notebook — it survived from an earlier interactive session, so the
        # notebook could not run standalone. Restored as the 2D grit table, which is
        # the only value consistent with get_lowest_passing_profiles(). FLAGGED in
        # KNOWN_ISSUES.md: confirm this is what the published Fig 5f used.
        (r"(sim2D\['Match'\] = sim2D\['Pair'\]\.isin\(sim3D\['Pair'\]\))",
         r"\1\n\n# restored by the port — see KNOWN_ISSUES.md\n"
         "data_2D = pd.read_parquet(profiles('exp1_main', f'grit_data_2D_{cell_line}.parquet')).dropna(axis='columns', how='all')"),
        (r"ImagesOut = '3_Figure4/PairwiseCorrelations/result-images/'",
         "ImagesOut = str(figdir('Fig4')) + '/'"),
        (r"'3_Figure4/PairwiseCorrelations/result-images'", "str(figdir('Fig4'))"),
        # pandas >=2 copy-on-write makes .values read-only, so the in-place
        # fill_diagonal raises. Same result, works on any pandas/numpy.
        (r"    p_no_diag = similarity_pivot_table\.copy\(\)\n"
         r"    np\.fill_diagonal\(p_no_diag\.values, np\.nan\)",
         "    _arr = similarity_pivot_table.to_numpy(dtype=float, copy=True)\n"
         "    np.fill_diagonal(_arr, np.nan)\n"
         "    p_no_diag = pd.DataFrame(_arr, index=similarity_pivot_table.index,\n"
         "                             columns=similarity_pivot_table.columns)"),
        # development leftovers: existence probes and a self-referential path
        (r"^\s*print\(os\.path\.exists\([^\n]*\n?", ""),
        (r"^\s*notebook_path\s*=[^\n]*\n?", ""),
        (r"data_type = 'aggregates'", "data_type = 'aggregates'\n" + PW_PANEL_ESCAPED),
        # clustermap -> Fig4e/4f, Fig5c, SupplFig4e/4f, SupplFig5b
        (r'ax\.savefig\("\{\}/PairwiseCorrelations_\{\}_\{\}\.\{\}"\.format\('
         r'ImagesOut, cell_line, data_type, figformat\)[^)]*\)',
         'save_panel(ax.figure, CLUSTERMAP_PANEL[(cell_line, data_type)],\n'
         '           data=similarity_pivot_table,\n'
         '           caption=f"Pairwise compound similarity clustermap, {cell_line} {data_type}",\n'
         '           notebook="analysis/3_Figure4/3_PairwiseCorrelations.ipynb")'),
        # 2D-3D difference scatter -> Fig5d / SupplFig5c
        (r'fig\.savefig\("\{\}/Difference_\{\}_colored_tails\.\{\}"\.format\('
         r'ImagesOut, cell_line, figformat\)[^)]*\)',
         'save_panel(plt.gcf(), DIFFERENCE_PANEL[cell_line],\n'
         '           data=similarities,\n'
         '           caption=f"2D minus 3D pairwise similarity, {cell_line}",\n'
         '           notebook="analysis/3_Figure4/3_PairwiseCorrelations.ipynb")'),
        # fingerprints -> the two halves of Fig 5f
        (r"plt\.savefig\(ImagesOut \+ 'fingerprints_2D\.pdf', bbox_inches='tight'\)",
         'save_panel(g.figure, "Fig5f_2D", data=plot_2D,\n'
         '           caption="2D morphological fingerprints, 5-FU and olaparib",\n'
         '           notebook="analysis/3_Figure4/3_PairwiseCorrelations.ipynb")'),
        (r"plt\.savefig\(ImagesOut \+ 'fingerprints_3D\.pdf', bbox_inches='tight'\)",
         'save_panel(g.figure, "Fig5f_3D", data=plot_3D,\n'
         '           caption="3D morphological fingerprints, 5-FU and olaparib",\n'
         '           notebook="analysis/3_Figure4/3_PairwiseCorrelations.ipynb")'),
    ],
    "GritScores_Fig3": [
        # panels were renamed A2/B2 -> 3c/3d in the manuscript
        (r"FIGURES = \{'MIP': '3A2', 'aggregates': '3B2'\}",
         "FIGURES = {'MIP': '3c', 'aggregates': '3d'}"),
        (r"THRESHOLD_LEGEND_ON = \['3B2'\]", "THRESHOLD_LEGEND_ON = ['3d']"),
        (r"Figure3A2B2_n_per_condition\.csv", "Figure3cd_n_per_condition.csv"),
        (r"Figure3A2B2_legend\.txt", "Figure3cd_legend.txt"),
        (r"Figure3A2_grit_MIP", "Figure3c_grit_MIP"),
        (r"Figure3B2_grit_scAgg", "Figure3d_grit_scAgg"),
        (r"fig_3A2 = ", "fig_3c = "),
        (r"fig_3B2 = ", "fig_3d = "),
        (r"ImagesOut = '3_Figure3/GritScores/result-images/'",
         'ImagesOut = str(figdir("Fig3")) + "/"'),
        # keep the notebook's own save() (it writes svg/png and fixes the font stack,
        # and cell 20 reads that svg back); add save_panel for the source table.
        (r"(\n(\s*)save\(fig, 'Figure\{\}_grit_\{\}'\.format\(FIGURES\[data_type\], "
         r"FIG_DATA_LABEL\[data_type\]\)\))",
         "\\1\n\\2save_panel(fig, 'Fig' + FIGURES[data_type], data=sub,\n"
         "\\2           caption=f'Grit scores per compound, {FIG_DATA_LABEL[data_type]}',\n"
         "\\2           notebook='analysis/3_Figure3/3_GritScores_Fig3cd.ipynb')"),
    ],
    "DEG": [
        # inputs shipped under DEG/data; the two MSigDB .gmt stay external
        # DEG_DATA must be defined before its first use, which is OLA_GSEA
        (r"OLA_GSEA = Path\(",
         "DEG_DATA = ROOT / 'analysis' / '3_Figure6' / 'DEG' / 'data'\nOLA_GSEA = ("),
        (r"FU_GSEA(\s*)= Path\(", r"FU_GSEA\1= ("),
        (r"= \('(8d1de180[^']*|b21ff6ac[^']*)'\)", r"= DEG_DATA / '\1'"),
        (r"FIG_DIR(\s*)= Path\('figures'\)", r"FIG_DIR\1= figdir('Fig6')"),
        (r"Path\('(QMMFHL[^']*)'\)", r"DEG_DATA / '\1'"),
        (r"'genesets/gsea_prerank_results\.csv'",
         "str(ROOT / 'analysis' / '3_Figure6' / 'DEG' / 'data' / 'gsea_prerank_results.csv')"),
        (r"'genesets/(c2|h)\.all\.v2026\.1\.Hs\.symbols\.gmt'",
         r"str(external('spher_colo52_v1/3_Figure6/DEG/genesets/\1.all.v2026.1.Hs.symbols.gmt'))"),
        # Fig 6c — hallmark GSEA scatter (3 savefigs collapse to one panel)
        (r"fig\.savefig\(FIG_DIR / f'\{OUT_NAME\}\.pdf', bbox_inches='tight'\)\n"
         r"\s*fig\.savefig\(FIG_DIR / f'\{OUT_NAME\}\.svg', bbox_inches='tight'\)\n"
         r"\s*fig\.savefig\(FIG_DIR / f'\{OUT_NAME\}\.png', dpi=300, bbox_inches='tight'\)",
         "save_panel(fig, 'Fig6c', data=df,\n"
         "           caption='Hallmark GSEA NES, olaparib vs 5-FU',\n"
         "           notebook='analysis/3_Figure6/DEG/hallmark_nes_scatter.ipynb')"),
        # the dumbbell writer: outname is the panel name
        (r"for ext in \('pdf', 'svg', 'png'\):\n\s*fig\.savefig\(FIG_DIR / f'\{outname\}\.\{ext\}', "
         r"dpi=300, bbox_inches='tight'\)",
         "save_panel(fig, outname, data=d, caption=suptitle,\n"
         "               notebook='analysis/3_Figure6/DEG/hallmark_nes_scatter.ipynb')"),
        # SPLIT: one output fed two different paper figures
        (r"signature_dumbbell\(\n\s*SIGNATURE_PANELS,\n\s*suptitle=f'Gene-set signatures — \{CELL_LINE\} spheroids',\n\s*outname='signature_dumbbells_combined',\n\)",
         "# Fig 6d and Suppl 6b were one combined output upstream; they are separate\n"
         "# paper panels, so each is drawn from its own subset with its own source table.\n"
         "FIG6D_KEYS = ['p53 pathway (HALLMARK)', 'E2F targets (HALLMARK)',\n"
         "              'p53 apoptosis (REACTOME)']            # manuscript order\n"
         "SUPPL6B_KEYS = ['G2M checkpoint (HALLMARK)', 'SASP (SAUL_SEN_MAYO)']\n"
         "\n"
         "signature_dumbbell({k: SIGNATURE_PANELS[k] for k in FIG6D_KEYS},\n"
         "                   suptitle=f'Gene-set signatures — {CELL_LINE} spheroids',\n"
         "                   outname='Fig6d')\n"
         "\n"
         "signature_dumbbell({k: SIGNATURE_PANELS[k] for k in SUPPL6B_KEYS},\n"
         "                   suptitle=f'Gene-set signatures — {CELL_LINE} spheroids',\n"
         "                   outname='SupplFig6b')"),
    ],
    "EdU": [
        # 67 MB of per-object CSVs stay outside the repo; the small aggregated
        # tables that the panel is drawn from are committed under data/.
        (r"DATA_DIR = Path\('\.'\)\s*# run notebook from EdU/ directory",
         "DATA_DIR = external('spher_colo52_v1/3_Figure6/EdU')   # bulk per-object CSVs\n"
         "CACHED   = ROOT / 'analysis' / '3_Figure6' / 'EdU' / 'data'  # committed tables"),
        (r"FIG_DIR  = DATA_DIR / 'figures'", "FIG_DIR  = figdir('Fig6')"),
        # Fig 6b: gammaH2AX foci/nucleus, EdU+ fraction, nuclei/spheroid
        (r"fig\.savefig\(FIG_DIR / 'panels_AB\.png', dpi=300, bbox_inches='tight'\)\n"
         r"\s*fig\.savefig\(FIG_DIR / 'panels_AB\.pdf', bbox_inches='tight'\)",
         "pass  # panel written below, once panel_source exists"),
        # panel_source is built further down the same cell, so save after it
        (r"(panel_source\.to_csv\(CACHED / 'panel_source_data\.csv', index=False\))",
         r"\1\nsave_panel(fig, 'Fig6b', data=panel_source,\n"
         "           caption='DNA damage, S-phase entry and spheroid size by treatment',\n"
         "           notebook='analysis/3_Figure6/EdU/EdU_analysis.ipynb')"),
        (r"panel_source\.to_csv\(DATA_DIR / 'panel_source_data\.csv', index=False\)",
         "panel_source.to_csv(CACHED / 'panel_source_data.csv', index=False)"),
    ],
    "DoseSimilarity": [
        (r"OUT\s*=\s*'[^']*result-images[^']*'", 'OUT = str(figdir("SupplFig5"))'),
        (r"fig\.savefig\(out_pdf, dpi=300, metadata=\{'Creator': None, 'Producer': None\}\)\n"
         r"\s*fig\.savefig\(out_svg\)\n\s*fig\.savefig\(out_png, dpi=300\)",
         "save_panel(fig, 'SupplFig5d',\n"
         "           data=pd.concat([\n"
         "               sim2.stack().rename('cosine').reset_index().assign(representation='2D'),\n"
         "               sim3.stack().rename('cosine').reset_index().assign(representation='3D')],\n"
         "               ignore_index=True),\n"
         "           caption='Dose-resolved 5-FU vs olaparib similarity, 2D vs 3D',\n"
         "           notebook='analysis/3_SupplFigure5/S_dose_similarity_5FU_Olaparib.ipynb')"),
    ],
    "CellDetection": [
        (r"\('1_Data/FeaturesImages_150125_none/SingleCell/\{\}\.parquet'\)\.format\(cell_line\)",
         'features("exp1_main", "011225", "SingleCell", f"{cell_line}.parquet")'),
        (r"ImagesOut = '3_Figure2/CellDetectionSanityCheck/result-images/'",
         "ImagesOut = str(figdir('Fig2')) + '/'\n"
         "# HCT116 is the main-figure panel; HT29 is the supplementary counterpart.\n"
         "SPHEROID_PANEL = {'HCT116': 'Fig2f', 'HT29': 'SupplFig1d'}"),
        (r"fig\.savefig\([\s\S]*?Detected_Cells_Spheroid[\s\S]*?\n\s*\)",
         "save_panel(fig, SPHEROID_PANEL[cell_line], data=dfSingleSpheroid,\n"
         "           caption=f'Detected cell centroids through a spheroid, {cell_line}',\n"
         "           notebook='analysis/3_Figure2/CellDetectionSanityCheck/3_Plot_Spheroids.ipynb')"),
    ],
    "PCA_RemoveNoise": [
        (r"ImagesOut = '3_Figure2/RemoveNoise/result-images/'",
         "ImagesOut = str(figdir('Fig2')) + '/'"),
        (r"fig\.savefig\(\"\{\}PCA_BatchStratified_\{\}_\{\}\.\{\}\"\.format\("
         r"ImagesOut, state, cell_line, figformat\)[^)]*\)",
         "save_panel(fig, f'Fig2g_{state}', data=embedding1,\n"
         "           caption=f'PCA {state} batch stratification, {cell_line}',\n"
         "           notebook='analysis/3_Figure2/RemoveNoise/5_PCA_RemoveNoise_BatchStratified.ipynb')"),
    ],
    "UMAP_exp4": [
        (r"ImagesOut = '3_Figure3/UMAP/result-images/'",
         "ImagesOut = str(figdir('SupplFig4')) + '/'\n" + EXP4_TAGS + ""),
        # unsupervised then labelled UMAP; PCA_unlabeled is not a paper panel
        (r"""fig\.savefig\("\{\}/\{\}_\{\}_\{\}\.\{\}"\.format\(dir, "UMAP", 'unlabeled', plate,'pdf'\)[^)]*\)""",
         "save_panel(fig, f'SupplFig4h_unlab{PLATE_TAG[plate]}',\n"
         "           data=pd.DataFrame({'umap1': embedding[:, 0], 'umap2': embedding[:, 1],\n"
         "                              'compound': posconDf.Metadata_cmpdname.values}),\n"
         "           caption=f'Unsupervised UMAP, {plate}',\n"
         "           notebook='analysis/3_SupplFigure4/3_PCA_objective.ipynb')"),
        (r"""fig\.savefig\("\{\}/\{\}_\{\}_\{\}\.\{\}"\.format\(dir, "UMAP", 'labeled', plate,'pdf'\)[^)]*\)""",
         "save_panel(fig, f'SupplFig4h_lab{PLATE_TAG[plate]}',\n"
         "           data=pd.DataFrame({'umap1': embedding[:, 0], 'umap2': embedding[:, 1],\n"
         "                              'compound': posconDf.Metadata_cmpdname.values}),\n"
         "           caption=f'Labelled UMAP, {plate}',\n"
         "           notebook='analysis/3_SupplFigure4/3_PCA_objective.ipynb')"),
    ],
    "TechRep_exp4": [
        # exp4 ships its own `utils` package, which collides with the repo-level one.
        # Renamed to az_utils so both are importable.
        (r'sys\.path\.append\("\.\./"\)', 'sys.path.insert(0, str(pathlib.Path.cwd()))'),
        (r"import utils\.utils as utils", "import az_utils.utils as utils"),
        (r"from utils\.replicate import", "from az_utils.replicate import"),
        (r'OutputDir = "\./spher_colo52_v1/3_Figure3/PercentReplicating/result-images/"',
         'OutputDir = str(figdir("SupplFig4")) + "/"\n" + EXP4_TAGS + "'),
        (r'fig\.savefig\(\n\s*"\{\}/TechnicalReplicates_repl_corrs_\{\}\.\{\}"\.format\('
         r'OutputDir, plate, figformat\)[^)]*\)',
         "save_panel(fig, f'SupplFig4i_{PLATE_TAG[plate]}',\n"
         "               data=corrs2_df[corrs2_df.Metadata_Barcode == plate],\n"
         "               caption=f'Replicate Spearman correlation vs concentration, {plate}',\n"
         "               notebook='analysis/3_SupplFigure4/3_Fig_TechnicalReplicates.ipynb')"),
    ],
    "2D_features": [
        # The 2D profile CSVs live in colopaint3D_fork/2D_features (the main tree has
        # only the notebook) — the same split as FeaturesImages_150125.
        (r"'\.\./2D_features/(selected_data_[A-Za-z0-9]+\.csv)'",
         r"external('../colopaint3D_fork/2D_features/\1')"),
    ],
    "GritScores": [
        (r"ImagesOut = '3_Figure3/GritScores/result-images/'",
         "ImagesOut = str(figdir('Fig5')) + '/'"),
    ],
    "MIP_features": [
        (r"'\.\./spher_colo52_v1/1_Data/spher_colo52-metadata\.csv'",
         'metadata("spher_colo52-metadata.csv", "exp1_main")'),
        (r"OutputDir = '[^']*'", 'OutputDir = str(profiles("exp1_main", "")) + "/"'),
    ],
    "_unused_placeholder": [],
    "2_DetectandCombine_exp4": [
        (r"dir='1_Data/(FeaturesImages_030625_[A-Za-z0-9_]+)_none/SingleSlice/'",
         r'dir=str(features("exp4_objective", "\1".replace("FeaturesImages_", ""), "SingleSlice")) + "/"'),
        (r"pd\.read_parquet\('2_Processing/(sphere_detection_output_[^']+\.parquet)'\)",
         r'pd.read_parquet(ROOT / "analysis" / "2_Processing" / "exp4_objective" / "data" / "\1")'),
        (r"OutputDir = '1_Data/results/'", 'OutputDir = str(profiles("exp4_objective", "")) + "/"'),
    ],
    "SegError": [
        (r"fig\.savefig\('segmentation_error_analysis\.svg', format='svg'\)",
         "save_panel(fig, 'SupplFig2d', data=df_results,\n"
         "           caption='Cellpose vs expert-annotation IoU by depth and treatment',\n"
         "           notebook='analysis/3_SupplFigure2/quantify_segmentation_error.ipynb')"),
        (r"base_dir = Path\('/home/jovyan/share/data/analyses/christa/colopaint3D/expert-annotation'\)",
         "# 7.7 GB of expert + Cellpose masks, held outside the repo.\n"
         "# Absent? the committed table below is what the panel plots.\n"
         "base_dir = external('expert-annotation')\n"
         "CACHED_IOU = ROOT / 'analysis' / '3_SupplFigure2' / 'data' / 'segmentation_iou_cached.csv'\n"
         "HAVE_MASKS = base_dir.is_dir()"),
        (r"raw_dir = Path\('/home/jovyan/share/data/analyses/christa/colopaint3D/expert-annotation/raw_images'\)",
         "raw_dir = external('expert-annotation') / 'raw_images'"),
    ],
    "PercentReplicating": [
        (r"ImagesOut = '3_Figure3/PercentReplicating/result-images/'",
         "ImagesOut = str(figdir('Fig3')) + '/'"),
        # Parameterised by data_type only — it loops both cell lines internally.
        (r"^data_type = 'aggregates'$",
         "import os\n"
         "data_type = os.environ.get('COLOPAINT3D_DATA_TYPE', 'aggregates')  # 'MIP' or 'aggregates'\n"
         "\n"
         "# Paper panel for this data_type: reproducibility of MIP vs single-cell aggregates.\n"
         "PR_PANEL = {'MIP': 'Fig3e', 'aggregates': 'Fig3f'}\n"
         "print(f'data_type={data_type}')"),
        (r'fig\.savefig\(\n\s*"\{\}PercentReplicating_\{\}\.\{\}"\.format\('
         r'ImagesOut, data_type, figformat\), dpi=dpi, bbox_inches="tight"\n\s*\)',
         "save_panel(fig, PR_PANEL[data_type],\n"
         "           data=pd.concat([corr_dist_all.assign(kind='replicate'),\n"
         "                           null_dist_all.assign(kind='null')], ignore_index=True),\n"
         "           caption=f'Median pairwise Pearson correlation by concentration step, "
         "replicate vs null, {data_type}',\n"
         "           notebook='analysis/3_Figure3/3_PercentReplicating.ipynb')"),
    ],
    "ErrorProp": [
        (r"fig\.savefig\('error_propagation_depth\.svg', format='svg', bbox_inches='tight'\)",
         "save_panel(fig, 'SupplFig2e', data=df_corr_plane,\n"
         "           caption='Feature correlation vs imaging depth, by compartment',\n"
         "           notebook='analysis/3_SupplFigure2/error_propegation.ipynb')"),
        (r"results_dir = Path\('/home/jovyan/share/data/analyses/christa/colopaint3D/expert-annotation/results'\)",
         "# 519 MB of CellProfiler output, held outside the repo.\n"
         "results_dir = external('expert-annotation') / 'results'\n"
         "CACHED_CORR = ROOT / 'analysis' / '3_SupplFigure2' / 'data' / 'error_propagation_cached.csv'\n"
         "HAVE_RESULTS = results_dir.is_dir()"),
    ],
}


def _assert_no_duplicate_post_edit_keys() -> None:
    """Python silently keeps only the last of duplicate dict literal keys.

    That bit twice during the port: a second entry for a notebook shadowed the
    first, quietly dropping its rules and letting absolute paths reappear. Check
    the source text, since by runtime the duplicate is already gone.
    """
    import collections
    src = Path(__file__).read_text()
    keys = re.findall(r'^    "([A-Za-z0-9_]+)": \[', src, re.M)
    dupes = [k for k, n in collections.Counter(keys).items() if n > 1]
    if dupes:
        raise AssertionError(
            f"duplicate POST_EDITS keys would silently lose rules: {dupes}"
        )


_assert_no_duplicate_post_edit_keys()

RE_CHDIR = re.compile(r"^\s*os\.chdir\([^)]*\)\s*$", re.M)
RE_GETCWD_PRINT = re.compile(r"^\s*print\(os\.getcwd\(\)\)\s*$", re.M)
RE_SAVEFIG = re.compile(r"\.savefig\(")


def _comment_out(text: str, key: str) -> tuple[str, int]:
    """Comment out savefig calls whose output is not a paper panel.

    Commented, not deleted: the code stays readable and the intent is explicit,
    and it keeps `run_all --verify` honest by not emitting stray figure files.
    """
    n = 0
    for pat in NOT_A_PANEL.get(key, []):
        def _c(m: re.Match) -> str:
            nonlocal n
            n += 1
            body = m.group(0)
            # the match starts at `fig.savefig(`, so read the real indent from the
            # text before it; without this a lone statement inside a for/if body
            # gets commented out and leaves an empty block.
            line_start = m.string.rfind("\n", 0, m.start()) + 1
            prefix = m.string[line_start:m.start()]
            indent = prefix if not prefix.strip() else ""
            lines = [f"{indent}# [not a paper panel] " + l.strip() for l in body.split("\n")]
            if indent:
                # it was the only statement in a for/if body; keep the block valid
                lines.append(f"{indent}pass")
            return "\n".join(lines)
        text = re.sub(pat, _c, text)
    return text, n


def port(key: str, dry_run: bool = False) -> dict:
    src_rel, dest_rel, exp = JOBS[key]
    src = SRC_ROOT / src_rel
    dest = (REPO / "analysis" / dest_rel).resolve()
    if not src.is_file():
        return {"key": key, "error": f"source missing: {src}"}

    nb = json.loads(src.read_text(errors="replace"))
    report = {"key": key, "src": str(src), "dest": str(dest), "exp": exp,
              "chdir_removed": 0, "rewrites": [], "abs_left": [], "savefig": 0}

    first_code = True
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        text = "".join(cell.get("source", []))

        n_chdir = len(RE_CHDIR.findall(text))
        if n_chdir:
            def _drop(m: re.Match) -> str:
                line = m.group(0)
                indent = line[: len(line) - len(line.lstrip())]
                # Indented => inside an if/else guard, which would be left with an
                # empty body. Keep the guard valid rather than deleting it.
                return f"{indent}pass  # was os.chdir; the bootstrap above handles paths" if indent else ""
            text = RE_CHDIR.sub(_drop, text)
            text = RE_GETCWD_PRINT.sub("", text)
            report["chdir_removed"] += n_chdir

        for pat, rep in ABS_REWRITES + REL_REWRITES:
            rep_x = rep.replace("{exp}", exp)
            new, n = re.subn(pat, rep_x, text)
            if n:
                report["rewrites"].append((pat, n))
                text = new

        for pat, rep in POST_EDITS.get(key, []):
            text, k = re.subn(pat, rep, text, flags=re.M)
            if k:
                report["rewrites"].append((f"post:{pat[:28]}", k))

        for prefix in ABS_PREFIXES:
            if prefix in text:
                report["abs_left"].append(prefix)

        text, n_commented = _comment_out(text, key)
        report["commented"] = report.get("commented", 0) + n_commented

        report["savefig"] += len(RE_SAVEFIG.findall(text))

        lines = text.split("\n")
        cell["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]

        if first_code:
            cell["source"] = BOOTSTRAP + ["\n"] + cell["source"]
            first_code = False

        cell["outputs"] = []
        cell["execution_count"] = None

    # Every code cell must still parse. Magics and shell escapes are not Python,
    # so blank them before checking.
    report["syntax_errors"] = []
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        clean = "\n".join("" if l.strip().startswith(("%", "!", "?")) else l
                           for l in src.split("\n"))
        try:
            ast.parse(clean)
        except SyntaxError as exc:
            report["syntax_errors"].append(f"cell {i}: {exc.msg}")

    report["abs_left"] = sorted(set(report["abs_left"]))
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(nb, indent=1) + "\n")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list:
        for k, (s, d, e) in JOBS.items():
            print(f"  {k:28s} {e:20s} -> analysis/{d}")
        return 0

    keys = list(JOBS) if args.all else args.keys
    if not keys:
        ap.error("give keys, or --all, or --list")

    needs_work = []
    for k in keys:
        if k not in JOBS:
            print(f"unknown key: {k}", file=sys.stderr)
            continue
        r = port(k, dry_run=args.dry_run)
        if "error" in r:
            print(f"  !! {r['key']}: {r['error']}")
            needs_work.append(r)
            continue
        flags = []
        if r["abs_left"]:
            flags.append(f"ABS×{len(r['abs_left'])}")
        if r["savefig"]:
            flags.append(f"savefig×{r['savefig']}")
        if r.get("syntax_errors"):
            flags.append(f"SYNTAX×{len(r['syntax_errors'])}")
        status = ("MANUAL: " + ", ".join(flags)) if flags else "clean"
        print(f"  {r['key']:28s} chdir-{r['chdir_removed']} rewrites-{sum(n for _, n in r['rewrites']):<3} {status}")
        if flags:
            needs_work.append(r)

    print(f"\n{len(keys) - len(needs_work)}/{len(keys)} ported clean; {len(needs_work)} need manual work")
    for r in needs_work:
        if "error" in r:
            continue
        print(f"\n  {r['key']}")
        for p in r["abs_left"]:
            print(f"     absolute path still present: {p}")
        if r["savefig"]:
            print(f"     {r['savefig']} savefig call(s) to convert to save_panel()")
        for e in r.get("syntax_errors", []):
            print(f"     SYNTAX ERROR {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
