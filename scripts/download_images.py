#!/usr/bin/env python3
"""Retrieve selected raw images from the BioImage Archive deposition.

NOT YET FUNCTIONAL — the dataset has not been deposited, so there is no accession
to fetch from. This is a scaffold that fixes the interface and records the design,
so the layout and documentation do not have to change once the accession exists.

Intended behaviour
------------------
Resolve images through the deposition's own file list rather than a second
hand-maintained index. ``analysis/4_BioImageArchive/`` generates
``spher_colo52-FileList.tsv`` and ``spher_colo52-Annotations.tsv`` — the same
tables the archive indexes the submission by — so those are the single source of
truth for what an image is::

    python scripts/download_images.py --plate PB000137 --well D12
    python scripts/download_images.py --compound olaparib --channel HOECHST
    python scripts/download_images.py --plate PB000137 --well D12 --all-z

Selective by design: this is a 384-well screen at 9 sites, 5 channels and many
z-planes per well. A whole-dataset download runs to terabytes, so filtering is
required and ``--everything`` must be explicit.

Blocked on
----------
1. **The BIA accession number** — does not exist until deposition.
2. **Where the file list ships.** The downloader needs ``FileList.tsv`` present,
   which means either committing it (it is a TSV, so the ``.gitignore`` must allow
   it) or fetching it from the archive first.
3. **CellProfiler pipelines and Cellpose models.** Raw images alone do not
   reproduce the feature tables — that needs the ``.cppipe`` pipelines and the
   segmentation models. Neither is currently in this repository and no ``.cppipe``
   was found in the source tree. They need a home here
   (``pipelines/cellprofiler/``, ``models/cellpose/``) or an archive DOI to
   point at.
"""
from __future__ import annotations

import argparse
import sys

ACCESSION = None  # e.g. "S-BIAD1234" once deposited


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--plate", help="plate barcode, e.g. PB000137")
    ap.add_argument("--well", help="well, e.g. D12")
    ap.add_argument("--compound", help="compound name, e.g. olaparib")
    ap.add_argument("--channel", help="HOECHST | SYTO | PHAandWGA | MITO | CONC")
    ap.add_argument("--site", type=int, help="site index (1-9)")
    ap.add_argument("--all-z", action="store_true", help="every z-plane, not just the mid-stack")
    ap.add_argument("--everything", action="store_true", help="the entire dataset (terabytes)")
    ap.parse_args()

    print(
        "Raw image download is not available yet: the image data has not been\n"
        "deposited, so there is no BioImage Archive accession to fetch from.\n"
        "\n"
        "What is available now:\n"
        "    python scripts/download_data.py      # processed profiles (147 MB)\n"
        "\n"
        "The processed profiles are what every figure is built from — see the\n"
        "Data availability section of README.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
