#!/usr/bin/env python3
"""Record a fixed reference point for the source tree this repo was ported from.

Writes provenance/SOURCE_SNAPSHOT.tsv: one row per file in the upstream working
tree, with a content hash for code/text files and size+mtime for everything else.

Why: the upstream tree is a live working directory and it changed during the
audit that produced this port (a figure folder moved mid-read). This manifest
pins exactly which version of each notebook was ported, so a later diff can show
what drifted. It is read-only with respect to the source.

Usage:  python provenance/make_snapshot.py [--source DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SOURCE = Path("/share/data/analyses/christa/colopaint3D")

# Directories that never enter the published port; skipped to keep this fast.
SKIP_DIRS = {
    ".git", ".ipynb_checkpoints", "__pycache__", ".venv", ".venv_map",
    ".claude", "not_to_git", "_archive",
}
# Suffixes we hash. Everything else is recorded by size+mtime only, because the
# feature tables run to hundreds of MB and hashing them buys nothing here.
HASH_SUFFIXES = {".ipynb", ".py", ".md", ".txt", ".yml", ".yaml", ".json", ".cfg", ".toml"}
HASH_MAX_BYTES = 50 * 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "SOURCE_SNAPSHOT.tsv",
    )
    args = ap.parse_args()

    src: Path = args.source
    if not src.is_dir():
        print(f"source not found: {src}", file=sys.stderr)
        return 1

    rows: list[tuple[str, str, str, str]] = []
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        if SKIP_DIRS & set(path.relative_to(src).parts):
            continue
        rel = path.relative_to(src).as_posix()
        try:
            stat = path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            # Extensionless files (LICENSE, .gitignore) are small and worth pinning too.
            hashable = path.suffix in HASH_SUFFIXES or (
                path.suffix == "" and stat.st_size <= 1 << 20
            )
            if hashable and stat.st_size <= HASH_MAX_BYTES:
                digest = sha256(path)
            else:
                digest = "-"
            rows.append((rel, str(stat.st_size), mtime, digest))
        except OSError as exc:  # unreadable file: record it rather than dying
            rows.append((rel, "?", "?", f"ERROR:{exc.errno}"))

    with args.out.open("w") as fh:
        fh.write(f"# source\t{src}\n")
        fh.write(f"# taken\t{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
        fh.write(f"# files\t{len(rows)}\n")
        fh.write("path\tsize_bytes\tmtime_utc\tsha256\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")

    hashed = sum(1 for r in rows if r[3] not in ("-",) and not r[3].startswith("ERROR"))
    print(f"wrote {args.out}")
    print(f"  {len(rows)} files recorded, {hashed} content-hashed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
