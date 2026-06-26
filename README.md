
## Analysis pipelines for Cell Painting in 3D spheroids

This repository contains supporting scripts and codes used in the analysis for the paper: 
"High-content morphological profiling by Cell Painting in 3D spheroids".

### Summary

Cell Painting is a popular assay for morphological profiling of 2D monolayer cell cultures.  
In the paper, we propose a scalable method to apply Cell Painting in 3D. 
The workflow is largely based on existing analysis strategies, 
with some adaptations to enable single-cell morphological profiling of 3D spheroids.

This repository contains a collection of notebooks for processing CellProfiler features of 3D spheroids 
and creating figures that accompany the manuscript. 

### Reproducing the analysis

A one-click reproducible Code Ocean capsule is available at: <DOI — to be added upon publication>.
The capsule bundles the environment, a data subset, and the notebooks so the analysis can be
re-run without local setup.

To run locally instead, follow Installation and Test dataset below.

## Installation

Requires Python 3.10

python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### Downloading data
The data underlying this analysis are deposited in the BioImage Archive under accession S-BIAD2254 (https://www.ebi.ac.uk/biostudies/studies/S-BIAD2254).

The archive contains:

* Raw images — 16-bit OME-TIFF, organised across per-plate result folders under Files/results/.
* Single-cell feature tables — per-compartment CellProfiler features (featICF_cells.parquet, featICF_cytoplasm.parquet, featICF_nuclei.parquet) within each acquisition's results folder (e.g. Files/results/PB000137/).
* Segmentation masks — Cellpose masks in the segmentation/ subfolder of each results folder.
* Detection demonstrator dataset — an example dataset for benchmarking spheroid detection, at Files/detection_example_dataset/.
* CellProfiler pipeline + cellpose models - the pipeline is provided at Files/feature_extraction/.
* Image acquisition files - JOBS, OCs, and GA3 pipelines are provided at Files/image_acquisition/.


### References
* [CellProfiler](https://github.com/CellProfiler)
* [Pycytominer](https://github.com/cytomining/pycytominer)
* [Spheroid detection](https://github.com/Ionshiv/SphereDetect)

