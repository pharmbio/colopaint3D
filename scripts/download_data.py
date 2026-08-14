#!/usr/bin/env python3
"""Fetch the processed profile tables every figure is built from.

The figures do not run on raw images. They run on well-level and section-level
feature tables produced by ``1_Data`` and ``2_Processing`` — 30 files, about
206 MB. Those are published as a dataset rather than committed here.

    python scripts/download_data.py                 # fetch the required tier
    python scripts/download_data.py --check         # verify what is already present
    python scripts/download_data.py --include-normalized   # + the 306 MB PCA input

Populating from a local checkout instead of the archive (what to use before the
dataset is deposited, and much faster on the same filesystem)::

    python scripts/download_data.py --from-local /share/data/analyses/christa/colopaint3D --link

Tiers
-----
``required``    the parquet profiles; every figure needs some of these.
``normalized``  ``normalized_data_merged_HCT116.csv``, used only by the Figure 2g
                PCA panel. Skipped unless asked for, because it is 306 MB.

Not covered here: ``FeaturesImages_<date>_none/``
-------------------------------------------------
``2_Processing`` does not read the tables above — it *produces* them, from
per-slice CellProfiler feature dumps in ``1_Data/FeaturesImages_<date>_none/``.
Those run to **19.5 GB** across the three experiments and are not part of any
tier, so re-running ``1_Data``/``2_Processing`` needs the feature dumps fetched
separately once the dataset is deposited.

Regenerating the *figures* needs none of that: the tiers above start downstream
of ``2_Processing``, which is why they are the default entry point.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.paths import DATA_ROOT, UPSTREAM_NAMES  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "data_manifest.tsv"

# The BioImage Archive deposition. `Files/` is the root of everything in the study:
# spher-colo52/ (raw OME-TIFFs), results/ (CellProfiler output + segmentation masks),
# feature_extraction/ (the .cppipe and Cellpose folders) and image_acquisition/.
BIA_ACCESSION = "S-BIAD2254"
BIA_FILES_URL = ("https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/254/"
                 f"{BIA_ACCESSION}/Files")

# Folder inside the deposit holding the processed profile tables. Must match the name
# used when uploading; change it here rather than in several places.
BIA_DATA_SUBDIR = "processed_profiles"

# Base URL of the published profile tables. Override with COLOPAINT3D_DATA_URL to point
# somewhere else (a mirror, a staging copy, a Zenodo record).
BASE_URL = os.environ.get("COLOPAINT3D_DATA_URL",
                          f"{BIA_FILES_URL}/{BIA_DATA_SUBDIR}").rstrip("/")

# Raw CellProfiler output: 3 objects x 6 plates, 16.6 GB. Not a tier in the manifest --
# it is fetched per-plate by analysis/0_Download, which needs the per-plate image_id/cp_id
# from the shipped metadata to know where each file goes.
CP_PLATES = ["PB000137", "PB000138", "PB000139", "PB000140", "PB000141", "PB000142"]
CP_OBJECTS = ["featICF_nuclei", "featICF_cells", "featICF_cytoplasm"]

# Where each destination subtree came from upstream, as
#   dest_subdir -> (upstream experiment folder, relative results path, glob, tier)
SOURCE_MAP = [
    ("exp1_main",                    "exp1_main", "1_Data/results",          "*.parquet", "required"),
    ("exp1_main/slices",             "exp1_main", "1_Data/results/slices",   "*.parquet", "required"),
    ("exp2_spheroid_size",           "exp2_spheroid_size", "1_Data/results", "*.parquet", "required"),
    ("exp2_spheroid_size/sections",  "exp2_spheroid_size", "1_Data/results/sections", "*.parquet", "required"),
    ("exp3_clearing_mag_z/sections", "exp3_clearing_mag_z", "1_Data/results/sections", "*.parquet", "required"),
    ("exp1_main",                    "exp1_main", "1_Data/results",          "normalized_data_*.csv", "normalized"),
]

CHUNK = 1 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with MANIFEST.open(newline="") as fh:
        # Strip the leading comment block before the header row, or DictReader
        # would take the first comment line as the field names.
        lines = [ln for ln in fh if not ln.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def _tier_for(rel: str) -> str:
    """Which download tier a path belongs to."""
    return "normalized" if Path(rel).name.startswith("normalized_data_") else "required"


def write_manifest_from_data() -> int:
    """Hash ``data/`` itself, rather than the upstream checkout it was copied from.

    This is the manifest that matches what gets deposited: once a table has been
    regenerated locally it no longer matches upstream, and a manifest describing files
    nobody will download is worse than none. ``features/`` and ``cellprofiler_results/``
    are excluded — they are separate tiers, far too large to ship with the profiles.
    """
    rows: list[dict] = []
    for path in sorted(DATA_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(DATA_ROOT).as_posix()
        if rel.startswith(("features/", "cellprofiler_results/")):
            continue
        rows.append({
            "path": rel,
            "size_bytes": str(path.stat().st_size),
            "sha256": sha256(path),
            "tier": _tier_for(rel),
        })
        print(f"  hashed {rel}")
    return _save_manifest(rows)


def write_manifest(source: Path) -> int:
    """Build the checksum manifest from a local copy of the data."""
    if source.resolve() == DATA_ROOT.resolve():
        return write_manifest_from_data()
    rows: list[dict] = []
    for dest_sub, exp, results_rel, pattern, tier in SOURCE_MAP:
        src_dir = source / UPSTREAM_NAMES[exp] / results_rel
        if not src_dir.is_dir():
            print(f"  skip (absent): {src_dir}", file=sys.stderr)
            continue
        for path in sorted(src_dir.glob(pattern)):
            if not path.is_file():
                continue
            rows.append(
                {
                    "path": f"{dest_sub}/{path.name}",
                    "size_bytes": str(path.stat().st_size),
                    "sha256": sha256(path),
                    "tier": tier,
                }
            )
            print(f"  hashed {dest_sub}/{path.name}")

    return _save_manifest(rows)


def _save_manifest(rows: list[dict]) -> int:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as fh:
        fh.write("# Processed profile tables for the colopaint3D paper analysis.\n")
        fh.write("# Generated by scripts/download_data.py --write-manifest\n")
        writer = csv.DictWriter(
            fh, fieldnames=["path", "size_bytes", "sha256", "tier"], delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(rows)
    total = sum(int(r["size_bytes"]) for r in rows)
    print(f"\nwrote {MANIFEST}: {len(rows)} files, {total / 1048576:.1f} MB")
    return 0


def _verify(dest: Path, row: dict) -> str:
    """Return "ok", "missing", "size", or "hash"."""
    if not dest.exists():
        return "missing"
    if dest.stat().st_size != int(row["size_bytes"]):
        return "size"
    if sha256(dest) != row["sha256"]:
        return "hash"
    return "ok"


def fetch_local(row: dict, source: Path, link: bool) -> None:
    """Copy or symlink one file out of a local colopaint3D checkout."""
    dest_sub, name = row["path"].rsplit("/", 1)
    exp = dest_sub.split("/")[0]
    for cand_sub, cand_exp, results_rel, pattern, _tier in SOURCE_MAP:
        if cand_sub != dest_sub:
            continue
        src = source / UPSTREAM_NAMES[cand_exp] / results_rel / name
        if src.exists():
            dest = DATA_ROOT / row["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            if link:
                dest.symlink_to(src.resolve())
            else:
                shutil.copy2(src, dest)
            return
    raise FileNotFoundError(f"{row['path']} not found under {source} (experiment {exp})")


def fetch_url(url: str, dest: Path, skip_existing: bool = True,
              attempts: int = 4) -> Path:
    """Stream ``url`` to ``dest``, via a .part file so a kill cannot leave a truncated
    table that looks complete.

    Retries on transient network errors: the CellProfiler tier is 16.6 GB across 18
    files of ~400 MB each, and EBI drops a connection often enough that a single-shot
    fetch will not get through the set. Retries are whole-file, not ranged — the archive
    does not reliably honour Range on these objects, and a silently-resumed-wrong file
    is worse than a slow one.

    Shared with ``analysis/0_Download``, so both fetchers behave the same way and there
    is one place where download semantics live.
    """
    dest = Path(dest)
    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "colopaint3D-paper/1.0"})

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
                expected = resp.headers.get("Content-Length")
                shutil.copyfileobj(resp, out, CHUNK)
            if expected is not None and tmp.stat().st_size != int(expected):
                raise OSError(f"short read: {tmp.stat().st_size} of {expected} bytes")
            tmp.replace(dest)
            return dest
        except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
            tmp.unlink(missing_ok=True)
            if attempt == attempts:
                raise SystemExit(
                    f"download failed for {url} after {attempts} attempts: {exc}")
            wait = 2 ** attempt
            print(f"    retry {attempt}/{attempts - 1} in {wait}s ({exc})", flush=True)
            time.sleep(wait)
    return dest  # unreachable


def check_parquet_intact(path: Path | str) -> str | None:
    """Return a complaint if ``path`` is not a complete parquet file, else None.

    A parquet file opens and closes with the 4-byte magic ``PAR1``; the footer holds the
    schema, so a file missing it is unreadable no matter how much of the data arrived.
    Checked here because a truncated upload is indistinguishable from a good one by size
    alone — Content-Length matches whatever was actually stored — and the failure would
    otherwise surface as an opaque pyarrow error hours later.
    """
    path = Path(path)
    if not path.exists():
        return "missing"
    size = path.stat().st_size
    if size < 8:
        return f"too small ({size} bytes)"
    with path.open("rb") as fh:
        head = fh.read(4)
        fh.seek(-4, os.SEEK_END)
        tail = fh.read(4)
    if head != b"PAR1":
        return "not a parquet file (bad header)"
    if tail != b"PAR1":
        extra = ("; size is an exact multiple of 64 KiB, which is the signature of an "
                 "interrupted upload" if size % 65536 == 0 else "")
        return f"truncated — no PAR1 footer{extra}"
    return None


def fetch_remote(row: dict) -> None:
    if not BASE_URL:
        raise SystemExit(
            "No dataset URL configured — set COLOPAINT3D_DATA_URL, or populate from a "
            "local checkout instead:\n"
            "    python scripts/download_data.py --from-local "
            "/share/data/analyses/christa/colopaint3D --link"
        )
    # skip_existing=False: the caller has already decided this file needs (re)fetching,
    # having checked size and sha256 against the manifest.
    fetch_url(f"{BASE_URL}/{row['path']}", DATA_ROOT / row["path"], skip_existing=False)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--from-local", type=Path, metavar="DIR",
                    help="populate from a local colopaint3D checkout instead of the archive")
    ap.add_argument("--link", action="store_true",
                    help="symlink instead of copying (only with --from-local)")
    ap.add_argument("--check", action="store_true",
                    help="verify files already in data/ against the manifest, then exit")
    ap.add_argument("--write-manifest", type=Path, metavar="DIR",
                    help="regenerate the checksum manifest from a local checkout; pass "
                         "the data/ directory itself to hash what will be deposited")
    ap.add_argument("--include-normalized", action="store_true",
                    help="also fetch the 306 MB normalized_data_merged_HCT116.csv (Fig 2g only)")
    ap.add_argument("--force", action="store_true", help="re-fetch files that already verify")
    args = ap.parse_args()

    if args.write_manifest:
        return write_manifest(args.write_manifest)

    rows = read_manifest()
    if not rows:
        print(f"no manifest at {MANIFEST}.\nGenerate it with:\n"
              f"    python scripts/download_data.py --write-manifest "
              f"/share/data/analyses/christa/colopaint3D", file=sys.stderr)
        return 1

    tiers = {"required"} | ({"normalized"} if args.include_normalized else set())
    wanted = [r for r in rows if r["tier"] in tiers]
    skipped = len(rows) - len(wanted)

    if args.check:
        bad = 0
        for row in wanted:
            status = _verify(DATA_ROOT / row["path"], row)
            if status != "ok":
                print(f"  {status:8s} {row['path']}")
                bad += 1
        print(f"\n{len(wanted) - bad}/{len(wanted)} files verify"
              + (f"; {skipped} not requested" if skipped else ""))
        return 1 if bad else 0

    total_mb = sum(int(r["size_bytes"]) for r in wanted) / 1048576
    print(f"{len(wanted)} files, {total_mb:.1f} MB -> {DATA_ROOT}")
    if skipped:
        print(f"({skipped} normalized_data files skipped; --include-normalized to fetch)")
    print()

    ok = fetched = 0
    for row in wanted:
        dest = DATA_ROOT / row["path"]
        if not args.force and _verify(dest, row) == "ok":
            ok += 1
            continue
        print(f"  {row['path']} ... ", end="", flush=True)
        if args.from_local:
            fetch_local(row, args.from_local, args.link)
        else:
            fetch_remote(row)
        status = _verify(dest, row)
        if status != "ok":
            print(f"FAILED ({status})")
            return 1
        print("ok")
        fetched += 1

    print(f"\ndone: {fetched} fetched, {ok} already present and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
