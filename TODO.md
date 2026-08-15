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

- [x] ~~**The 18 CellProfiler tables in S-BIAD2254 are truncated — re-upload them.**~~
      **DONE (2026-08-15).** Re-uploaded and verified against the cluster originals with
      `python scripts/verify_deposit.py`: all 18 match on byte size, row count and column
      count (e.g. PB000137 nuclei, 1,351,678,271 B / 498,636 rows). Keep the note below
      as the record of what went wrong, and re-run that script after any future upload.

      <details><summary>what had happened</summary>
      Every one of `results/PB0001{37..42}/featICF_{nuclei,cells,cytoplasm}.parquet`
      started with the `PAR1` magic but had no closing `PAR1` footer, so none could be
      opened. All 18 carried the identical FTP timestamp **Apr 15 15:33**,
      every size is an exact multiple of 64 KiB, the truncated sizes cluster near 390 MB
      regardless of true size (correlation with the originals r = −0.075, and PB000140
      cells and cytoplasm stopped at byte-identical lengths). That is a concurrent upload
      of all 18 cut off at one moment, each stream left at a buffer boundary. For
      contrast `segmentation/` in the same folder is stamped Aug 10 09:00 and is intact.

      Not recoverable by retrying: HTTPS/FIRE, `www.ebi.ac.uk/biostudies/files`, the FTP
      protocol, the FTP listing and the BioStudies API all report the same short sizes,
      so the bytes are not in storage. No point reporting it as corruption either — from
      the archive's side ingestion succeeded and it recorded what arrived; the website
      declares exactly the truncated sizes with no error flag.

      Fixed by re-uploading from
      `/share/data/cellprofiler/automation/results/{barcode}/{image_id}/{cp_id}/`, taking
      the id pair from the shipped metadata — PB000137 has a second run at `4185/11613`
      that holds 147 rows against 5532's 498,636, and an early attempt uploaded that one
      by mistake.
      </details>
- [x] ~~**Upload the processed profile tables** to S-BIAD2254 as `processed_profiles/`
      (31 files, 488 MB — `data/` minus `features/`).~~ **DONE (2026-08-15).** Landed under
      the expected `processed_profiles/` name, so `BIA_DATA_SUBDIR` in
      `scripts/download_data.py` needs no change. `python scripts/verify_deposit.py
      --profiles` passes on both tiers: all 18 CellProfiler tables and all 31 profile
      files match the local originals on byte size, row count and column count (the one
      CSV, `normalized_data_merged_HCT116.csv` at 305,863,934 B, on size alone — it has no
      footer to read). A clone can now fetch everything the figures read.
- [ ] **Deposition covers exp1 only** (PB000137–142). The 2D monolayer arm and the exp2 /
      exp3 / exp4 robustness runs have no raw-data deposition, so for those panels the
      processed tables are the only reproducible artefact — worth one sentence in Data
      Availability.
- [ ] **RNA-seq DGE tables** (`3_Figure6/DEG/data`, ~11 MB) are inputs that nothing in the
      repo can regenerate. They need a GEO/ArrayExpress accession or to travel with the
      release.
- [ ] **Re-running `2_Processing` puts back tables the deposit deliberately omits.**
      `data/` was trimmed to the 31 files some figure actually reads. But exp2's and
      exp3's `2_Pycytominer` each process 8 cases and write a `selected_*` table for
      every one — including `37C` and `double_dens`, which no panel plots — so a full
      run on a machine with the feature dumps recreates ~16 of them. That is correct
      behaviour (they are pipeline outputs, and someone re-deriving will want them);
      it only becomes a problem if the manifest is regenerated afterwards, because the
      FileList would then grow by files nothing reads. **Before re-hashing with
      `--write-manifest data`, check `git diff scripts/data_manifest.tsv` for entries
      you did not mean to deposit.**
- [ ] **Nothing in the repo generates the exp2/exp3 `grit_*` tables.** Both
      `2_Pycytominer` notebooks write only `selected_*`; the grit tier came from upstream
      and has no derivation path here. **Decided (2026-08-15): document, do not port** —
      the methods will state that exp2 grit scores are provided rather than recomputed.
      Scope is narrower than this heading suggests: only **exp2** has grit tables, and
      only three, all read by Suppl 3c (`grit_section1_12planes`, `grit_section2`,
      `grit_section3`); exp3 has none at all. All three are deposited and verified, so
      nothing further is needed in the repo — this is now a manuscript sentence only.
- [ ] `CITATION.cff`: the BIA accession **is already there** (S-BIAD2254, under
      `identifiers` and `references`). What is still missing needs a human — the author
      list in publication order with ORCIDs and affiliations, the paper DOI under
      `preferred-citation` once it exists, and `version` / `date-released` at tag time.
- [x] ~~Pin `gseapy`.~~ **DONE (2026-08-15).** `gseapy==1.3.1`, the version in the upstream
      `colopaint3D/.venv` — the earlier note that it was in neither venv was wrong. It is
      needed by nothing on a clean clone: the one import in `hallmark_nes_scatter.ipynb`
      is behind a check for the committed `data/gsea_prerank_results.csv`, and it feeds a
      cell marked `# [not a paper panel]`.

### Closed

- ~~CellProfiler `.cppipe` pipelines and Cellpose models are in no repository.~~ They are
  in the deposit, under `feature_extraction/`
  (`HMPSC_FEAT_ICFImg_Cellpose_v2_152219_spheroids_v3.cppipe`, plus the `CP_2023*`
  folders). Acquisition configs are there too, under `image_acquisition/`.

## Repo shape for the public release

- [ ] Strip `provenance/`, `checks/` and the porting tools; keep the analysis, `utils/`,
      `run_all.py` and the figure code.
- [ ] Drop the heavy regenerable files (~160 MB of the 184 MB tracked): `Source Data.xlsx`
      (46 MB, rebuilt by `scripts/make_source_data.py`, and it goes to the journal), the
      BioImage Archive manifests (47 MB, rebuilt by `4_ImageBioArchive_Metadata` and
      hosted at BIA), and the six source tables over 6 MB (rebuilt by `run_all.py`).
      That leaves ~13 MB. The blocker on this — `data/` not being fetchable — cleared on
      2026-08-15 when `processed_profiles/` went up and verified.
- [ ] Carry the paper-facing caveats above into the manuscript before `provenance/` goes.
- [ ] When `scripts/data_inventory.py` goes, note that it writes into `provenance/` and
      `mkdir`s the directory back, so shipping it re-grows what the strip removed.

**The published figures live outside this repo, at `../colopaint3D_paper_reference/`.**
They are checking material and must not ship, but they also cannot be regenerated, so they
are deliberately somewhere no release step can reach:

- `actual_panels/` — the 12 published figure PNGs. Recovered 2026-08-15 from
  `/share/data/analyses/.Trash-1000/`, where they had been sitting since 2026-08-14,
  never committed, one trash purge from gone.
- `archived_originals/` — the 8 Jan-13 UMAP PDFs behind Fig 4a–d, the only record of the
  published Fig 4c/4d whose ARI/NMI/SC no longer re-derive. Committed at `53e1765`, then
  deleted from HEAD by `952803d` as collateral of an unrelated commit; recovered from
  history the same day. **A history rewrite is the one thing that would have lost them**
  — which is why they now live outside git as well.

Diff rebuilt panels against `actual_panels/` at the clean-clone rehearsal; that is the
last point they are useful.
