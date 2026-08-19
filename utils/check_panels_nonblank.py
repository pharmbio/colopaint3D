#!/usr/bin/env python3
"""Assert every rendered panel PDF has ink on it.

Matching panels against manifest rows and source tables cannot catch a panel that saved
an *empty page* — healthy row, correct table, blank PDF. This is the other half of that
check, and runs beside it at the end of `run_all.py`.

    python utils/check_panels_nonblank.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGURES = REPO / "figures"


def main() -> int:
    try:
        import numpy as np
        import pymupdf
    except ImportError:
        print("needs pymupdf and numpy: pip install pymupdf", file=sys.stderr)
        return 2

    if not FIGURES.is_dir():
        print(f"no {FIGURES} yet — run run_all.py first")
        return 0

    blank, checked = [], 0
    for pdf in sorted(FIGURES.rglob("*.pdf")):
        if ".ipynb_checkpoints" in pdf.parts or "actual_panels" in pdf.parts:
            continue
        checked += 1
        rel = pdf.relative_to(FIGURES).as_posix()
        # A truncated or zero-byte PDF is a failure to report, not a crash: it happens
        # when a run is interrupted mid-write, and it is exactly what this check is for.
        try:
            pix = pymupdf.open(pdf)[0].get_pixmap(dpi=72)
        except Exception as e:
            blank.append(f"{rel}  ({type(e).__name__})")
            continue
        if int((np.frombuffer(pix.samples, dtype=np.uint8) < 250).sum()) == 0:
            blank.append(rel)

    if blank:
        print(f"{len(blank)} of {checked} rendered panels are blank:", file=sys.stderr)
        for b in blank:
            print(f"  - {b}", file=sys.stderr)
        return 1
    print(f"all {checked} rendered panels have content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
