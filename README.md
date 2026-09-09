[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22013751.svg)](https://doi.org/10.5281/zenodo.22013751)

# Cell Painting in 3D spheroids — paper analysis

## Summary

Analysis code for **"High-content morphological profiling by Cell Painting in 3D
spheroids."** 

Cell Painting is a popular assay for morphological profiling of 2D monolayer cell cultures.
In the paper, we propose a scalable method to apply Cell Painting in 3D. 
The workflow is largely based on existing analysis strategies, with some adaptations to enable single-cell morphological profiling of 3D spheroids.

This repository contains a collection of notebooks for processing CellProfiler features of 3D spheroids and creating figures that accompany the manuscript.

## Installation

```bash
python3.10 -m venv .venv                # Python 3.10
source .venv/bin/activate
pip install -r requirements.txt         

python utils/download_data.py         # download raw and processed feature tables from the BioImage Archive
python run_all.py                       # every figure and source-data table
```

## Downloading data

Everything comes from BioImage Archive accession **S-BIAD2254**. The figures read processed tables deposited there. 
It is also possible to download raw CellProfiler data: (`python run_all.py --stage 0_Download`) and the
19.5 GB per-slice feature tables. 

The archive contains:

* Raw images — 16-bit OME-TIFF, organised across per-plate result folders under Files/results/.
* Single-cell feature tables — per-compartment CellProfiler features (featICF_cells.parquet, featICF_cytoplasm.parquet, featICF_nuclei.parquet) within each acquisition's results folder (e.g. Files/results/PB000137/).
* Processed feature tables
* Segmentation masks — Cellpose masks in the segmentation/ subfolder of each results folder.
* Detection demonstrator dataset — an example dataset for benchmarking spheroid detection, at Files/detection_example_dataset/.
* CellProfiler pipeline + cellpose models - the pipeline is provided at Files/feature_extraction/.
* Image acquisition files - JOBS, OCs, and GA3 pipelines are provided at Files/image_acquisition/.


RNA data is deposited in https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE343958 

## Layout

```
run_all.py       Single entry point
utils/           paths.py (path resolution), panels.py (figure + source data)
                 palettes.py, download_data.py, make_source_data.py,
                 check_panels_nonblank.py
analysis/        1_Data → 2_Processing → one folder per paper figure
source_data/     One table per panel
figures/         Rendered panels
downloaded_data/ Downloaded profile tables
input/           Other inputs not in downloads            
derived/         Anything a run regenerates 
```


## Citation

See `CITATION.cff`. Licence: `LICENSE`.

## References

- [CellProfiler](https://github.com/CellProfiler)
- [Pycytominer](https://github.com/cytomining/pycytominer)
- [Spheroid detection](https://github.com/pharmbio/SphereDetect)
