#!/usr/bin/env python3
"""Verify the published BioImage Archive deposit without downloading it.

    python scripts/verify_deposit.py              # the 18 CellProfiler tables
    python scripts/verify_deposit.py --profiles   # + the processed profile tier

Why this exists: the first upload of the CellProfiler tables to S-BIAD2254 was
truncated. Every file started with the parquet magic ``PAR1`` and ended without it, so
none could be opened -- but each was served with a ``Content-Length`` matching whatever
had actually been stored, and the archive listed them as complete. Size alone therefore
proves nothing, and neither the archive nor a downloader that only checks length would
ever notice.

Parquet keeps its schema and row count in a footer at the end of the file, so a
file-like object backed by HTTP range requests lets pyarrow read the metadata after
fetching a few hundred KB instead of 16.6 GB. Comparing that against the local
originals checks what the footer bytes alone cannot: that the file parses, and that it
holds the rows it should.

Run this after any re-upload, against the archive rather than your own copy -- the local
files were never the problem; the transfer was.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.paths import DATA_ROOT, cellprofiler_results, metadata  # noqa: E402

from download_data import BIA_FILES_URL, CP_OBJECTS, CP_PLATES  # noqa: E402

UA = {"User-Agent": "colopaint3D-paper/1.0"}


class HTTPFile:
    """Minimal seekable read-only file over HTTP Range, for pyarrow."""

    def __init__(self, url: str):
        self.url = url
        self.pos = 0
        self.closed = False
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(
            self.url, headers={**UA, "Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        self.pos += len(data)
        return data

    def seek(self, off: int, whence: int = 0) -> int:
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def tell(self) -> int:
        return self.pos

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def close(self) -> None:
        self.closed = True


def _compare(label: str, url: str, local: Path) -> bool:
    import pyarrow.parquet as pq

    if not local.is_file():
        print(f"  {label:<42} local original missing at {local}")
        return False
    try:
        remote = pq.ParquetFile(HTTPFile(url))
        rmd, rsize = remote.metadata, HTTPFile(url).size
    except Exception as exc:                     # noqa: BLE001 - report, do not raise
        print(f"  {label:<42} UNREADABLE — {type(exc).__name__}: {str(exc)[:60]}")
        return False

    lmd = pq.ParquetFile(local).metadata
    lsize = os.path.getsize(local)
    ok = (rsize == lsize and rmd.num_rows == lmd.num_rows
          and rmd.num_columns == lmd.num_columns)
    print(f"  {label:<42} {rsize:>14,} B {rmd.num_rows:>10,} rows  "
          f"{'identical' if ok else 'DIFFERS'}")
    if not ok:
        print(f"      local: {lsize:,} B, {lmd.num_rows:,} rows, {lmd.num_columns} cols")
    return ok


def check_cellprofiler() -> bool:
    """The 18 raw CellProfiler tables, against the cluster originals."""
    import pandas as pd

    meta = pd.read_csv(metadata("spher_colo52-metadata.csv", "exp1_main"))
    ids = meta[["barcode", "image_id", "cp_id"]].drop_duplicates().set_index("barcode")

    print("CellProfiler tables (vs the originals under cellprofiler_results):")
    ok = True
    for bc in CP_PLATES:
        # PB000137 has two cp_id runs; the metadata names the real one (11613 is a
        # 147-row test run, 0.03% of 5532). Deriving the path from the metadata rather
        # than globbing is what keeps the wrong one out of the deposit.
        base = (cellprofiler_results("exp1_main") / bc
                / str(ids.loc[bc, "image_id"]) / str(ids.loc[bc, "cp_id"]))
        for obj in CP_OBJECTS:
            ok &= _compare(f"{bc}/{obj}",
                           f"{BIA_FILES_URL}/results/{bc}/{obj}.parquet",
                           base / f"{obj}.parquet")
    return ok


def check_profiles() -> bool:
    """The processed profile tier, against data/ and the manifest checksums."""
    man = Path(__file__).resolve().parent / "data_manifest.tsv"
    rows = list(csv.DictReader([l for l in man.open() if not l.startswith("#")],
                               delimiter="\t"))
    print(f"\nProcessed profiles ({len(rows)} files, vs data/):")
    ok = True
    for r in rows:
        if not r["path"].endswith(".parquet"):
            # CSVs have no footer to inspect; length is all there is to compare
            try:
                fh = HTTPFile(f"{BIA_FILES_URL}/processed_profiles/{r['path']}")
                good = fh.size == int(r["size_bytes"])
            except Exception as exc:             # noqa: BLE001
                print(f"  {r['path']:<42} UNREACHABLE — {type(exc).__name__}")
                ok = False
                continue
            print(f"  {r['path']:<42} {fh.size:>14,} B (size only)  "
                  f"{'ok' if good else 'DIFFERS'}")
            ok &= good
            continue
        ok &= _compare(r["path"],
                       f"{BIA_FILES_URL}/processed_profiles/{r['path']}",
                       DATA_ROOT / r["path"])
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profiles", action="store_true",
                    help="also verify the processed_profiles/ tier")
    ap.add_argument("--only-profiles", action="store_true",
                    help="verify only the processed_profiles/ tier")
    args = ap.parse_args()

    ok = True
    if not args.only_profiles:
        ok &= check_cellprofiler()
    if args.profiles or args.only_profiles:
        ok &= check_profiles()

    print("\n" + ("everything published matches the originals" if ok
                  else "MISMATCHES FOUND — do not cite the deposit until fixed"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
