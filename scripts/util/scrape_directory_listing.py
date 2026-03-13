"""
scrape_directory_listing.py — recursively lists every file under a given
directory and writes the fully-qualified paths to a timestamped CSV in
resources/fs-info/.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FS_INFO_DIR = ROOT / "resources" / "fs-info"


def _collect_files(directory: Path) -> list[str]:
    """Return sorted fully-qualified paths of every file under *directory*."""
    return sorted(str(p) for p in directory.rglob("*") if p.is_file())


def run(target_dir: str) -> bool:
    """Scrape *target_dir* and write the listing CSV. Returns True on success."""
    target = Path(target_dir).resolve()
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory", file=sys.stderr)
        return False

    files = _collect_files(target)
    if not files:
        print(f"Warning: no files found under '{target}'", file=sys.stderr)

    FS_INFO_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    out_path = FS_INFO_DIR / f"fs-{timestamp}.csv"

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path"])
        for fqp in files:
            writer.writerow([fqp])

    print(f"Wrote {len(files)} entries to {out_path}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively list files and write a timestamped CSV.",
    )
    parser.add_argument("directory", help="Directory to scrape")
    args = parser.parse_args()

    if not run(args.directory):
        sys.exit(1)


if __name__ == "__main__":
    main()
