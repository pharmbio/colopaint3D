# TODO before submission

Things that need a human decision or an external action. Kept here because it is the
one file that survives stripping `provenance/`, `checks/` and the porting tools out of
the public repo.

Grouped by who has to act.

## Must be stated in the paper

- [ ] **Fig 6e substitutes Crizotinib for Vinorelbine.** `fig_5fu_neighbours_frozen_doses`
      drops Vinorelbine because its matched dose fails the grit cutoff. The panel is
      correct; the legend does not currently say this.
- [ ] **Fig 3g/3h are a reconstruction, not the original code.** `AggVsMIP` exists in no
      notebook, script or checkpoint in any of the three source trees, and in none of the
      194 commits of history. Rebuilt from the same replicate correlations Fig 3e/3f use;
      axes, diagonal, palettes and the dot/plus convention match the surviving PDFs.
      n = 383 plotted perturbations. Compare against the archived PDFs before publishing.
- [ ] **Suppl 5e's four labelled MoA classes were chosen by hypothesis, not by a scan.**
      Of the 20 class pairings present, the two most 3D-similar are both shown
      (Antimetabolite × Topo I +0.334, Antimetabolite × MDM2i +0.252), but comparably
      extreme pairings are not (MAPKi × MDM2i −0.203 on n = 20; PARPi × PARPi −0.251).
      Three of the four labelled classes rest on n = 3–6 pairs. Defensible as an a-priori
      choice given the paper's 5-FU / olaparib focus — but say so in the legend.
- [ ] **Fig 5f's colour limits (±12 for 2D, ±2.7 for 3D) are not derived by any code.**
      Set interactively; the author's recollection is the only record. The 3D limit is the
      99th percentile of |value| of the plotted rows, but the same rule gives 4.3 for 2D,
      not 12 — so the two blocks were not scaled by one rule.

## Locked to the current re-run values (decided)

The published clustering numbers predate a code edit made after the PDFs were exported,
so they do not re-derive. The manuscript is being updated to match this version.

- [ ] Manuscript hierarchical-clustering text: SC 0.614 / 0.473 → **0.682 / 0.432**;
      ARI 0.006 → 0.159 → 0.233 → **−0.013 → 0.105 → 0.171**.
- [ ] Fig 4c/4d legend ARI/NMI/SC values.
- [ ] Fig 2g axis labels: PC1/PC2 variance explained (was 22.78 / 15.49%).

## External actions

- [ ] **BioImage Archive accession.** Nothing in the repo has one; `download_images.py` is
      a scaffold and `CITATION.cff` has a placeholder.
- [ ] **A public source for the processed profile tables.** `data/` is ~650 MB, is
      gitignored, and `download_data.py` has no URL — so a clone currently cannot run any
      figure. This is the single biggest reproducibility gap. Deposit `data/` and set
      `COLOPAINT3D_DATA_URL`.
- [ ] **CellProfiler `.cppipe` pipelines and Cellpose models are in no repository.** Raw
      images alone do not reproduce the features, so the image deposition does not close
      the loop by itself.
- [ ] **Deposition covers exp1 only** (PB000137–142). The 2D monolayer arm and the exp2 /
      exp3 / exp4 robustness runs have no raw-data deposition.
- [ ] **RNA-seq DGE tables** (`3_Figure6/DEG/data`, ~11 MB) are inputs that nothing in the
      repo can regenerate. They need a GEO/ArrayExpress accession or to travel with the
      release.
- [ ] Pin `gseapy` (Figure 6 hallmark panels); it is present in neither analysis venv.

## Known cosmetic defects

- [ ] Suppl 4i's x axis is built as `conc * 1000`, so it reads in nM (0.32 … 10000) where
      the published panel reads µM (0.00316 … 10.0).

## Repo shape for the public release

- [ ] Strip `provenance/`, `checks/` and the porting tools; keep the analysis, `utils/`,
      `run_all.py` and the figure code.
- [ ] Drop the heavy regenerable files (~160 MB of the 184 MB tracked): `Source Data.xlsx`
      (46 MB, rebuilt by `scripts/make_source_data.py`, and it goes to the journal), the
      BioImage Archive manifests (47 MB, rebuilt by `4_ImageBioArchive_Metadata` and
      hosted at BIA), and the six source tables over 6 MB (rebuilt by `run_all.py`).
      That leaves ~13 MB. **Only safe once `data/` is fetchable** — otherwise a clone can
      regenerate nothing.
- [ ] Carry the paper-facing caveats above into the manuscript before `provenance/` goes.
