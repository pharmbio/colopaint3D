# TODO before submission

Things that need a human decision or an external action. Kept here because it is the
one file that stayed behind when `provenance/`, `checks/` and the porting tools left the
public repo.

Grouped by who has to act.


## Locked to the current re-run values (decided)

The published clustering numbers predate a code edit made after the PDFs were exported,
so they do not re-derive. The manuscript is being updated to match this version.

- [ ] Manuscript hierarchical-clustering text: SC 0.614 / 0.473 → **0.682 / 0.432**;
      ARI 0.006 → 0.159 → 0.233 → **−0.013 → 0.105 → 0.171**.
- [ ] Fig 4c/4d legend ARI/NMI/SC values.
- [ ] Fig 2g axis labels: PC1/PC2 variance explained (was 22.78 / 15.49%).

## External actions

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

- [x] ~~Strip `provenance/`, `checks/` and the porting tools.~~ **DONE (2026-08-15).**
      Moved to the archive, not deleted — see below. `checks/` was already untracked.
      `build_caches.py` was kept and moved to `scripts/`: it is a live tool that rebuilds
      the eight committed cache tables, and it is the only record of how they derive.
      `data_inventory.py` went to the archive with the file it generates.
- [ ] Drop the heavy regenerable files (~160 MB of the 184 MB tracked): `Source Data.xlsx`
      (46 MB, rebuilt by `scripts/make_source_data.py`, and it goes to the journal), the
      BioImage Archive manifests (47 MB, rebuilt by `4_ImageBioArchive_Metadata` and
      hosted at BIA), and the six source tables over 6 MB (rebuilt by `run_all.py`).
      That leaves ~13 MB. The blocker on this — `data/` not being fetchable — cleared on
      2026-08-15 when `processed_profiles/` went up and verified.
- [ ] Nine notebooks still cite `KNOWN_ISSUES.md` / `PORT_TRIAGE.md` in comments, which no
      longer resolve from a clone. Only `3_Figure4/3_PairwiseCorrelations.ipynb` is worth
      fixing: eight of its mentions are runtime `print()` strings a reader will see.

**Everything not shipped lives in `../colopaint3D_paper_archive/`.** It is checking and
provenance material — none of it belongs in the public repo, but none of it can be
regenerated either, so it sits where no release step can reach it:

- `provenance/` — `PORT_TRIAGE.md` (panel map, what was included and why),
  `KNOWN_ISSUES.md` (open blockers, source and port defects), `SOURCE_SNAPSHOT.tsv`,
  and the porting tools `port_notebook.py`, `make_snapshot.py`, `data_inventory.py`.

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
