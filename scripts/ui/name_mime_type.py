"""
name_mime_type.py — renames static resource files using the convention:
    <stem>-<sha256>.ext

Copyright 2026 by DTS, The State of Utah

Usage:
    python scripts/name_mime_type.py                          # Scan static dirs, rename all
    python scripts/name_mime_type.py <filepath>               # Rename one file (keep stem)
    python scripts/name_mime_type.py <filepath> <description> # Rename with camelCase desc

Examples:
    python scripts/name_mime_type.py                          # Renames all in frontend/ assets/
    python scripts/name_mime_type.py assets/logo.png          # → assets/logo-a1b2c3…f6.png
    python scripts/name_mime_type.py assets/logo.png "app logo dark"
                                                              # → assets/appLogoDark-a1b2…f6.png
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

ASSET_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
    ".bmp",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
}

NAMING_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*-[0-9a-f]{64}\.[a-zA-Z0-9]+$")

STATIC_DIRS = [
    ROOT / "ui",
    ROOT / "assets",
]


def to_camel_case(description: str) -> str:
    """Convert a space-separated description to camelCase."""
    words = re.split(r"[\s_\-]+", description.strip())
    if not words:
        raise ValueError("Description must contain at least one word.")
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def sha256_of_file(filepath: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def rename_file(filepath: Path, description: str) -> Path:
    """Rename a file to camelCaseDescription-<sha256>.ext and return the new path."""
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    camel = to_camel_case(description)
    file_hash = sha256_of_file(filepath)
    ext = filepath.suffix
    new_name = f"{camel}-{file_hash}{ext}"
    new_path = filepath.parent / new_name

    if new_path.exists() and new_path != filepath:
        raise FileExistsError(f"Target already exists: {new_path}")

    filepath.rename(new_path)
    return new_path


def rename_with_stem(filepath: Path) -> Path | None:
    """Rename using existing filename stem + sha256. Returns None if already correct."""
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    stem = filepath.stem
    file_hash = sha256_of_file(filepath)
    ext = filepath.suffix
    new_name = f"{stem}-{file_hash}{ext}"
    new_path = filepath.parent / new_name

    if new_path == filepath:
        return None

    if new_path.exists():
        raise FileExistsError(f"Target already exists: {new_path}")

    filepath.rename(new_path)
    return new_path


def find_asset_files(directories: list[Path]) -> list[Path]:
    """Find all asset files in the given directories."""
    files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            continue
        for filepath in sorted(directory.rglob("*")):
            if filepath.is_file() and filepath.suffix.lower() in ASSET_EXTENSIONS:
                files.append(filepath)
    return files


def scan_and_rename(directories: list[Path] | None = None) -> int:
    """Scan static directories and rename all assets that need it."""
    if directories is None:
        directories = STATIC_DIRS

    assets = find_asset_files(directories)
    if not assets:
        print("[name] No asset files found to rename.")
        return 0

    renamed = 0
    skipped = 0
    errors = 0

    for filepath in assets:
        if NAMING_PATTERN.match(filepath.name):
            skipped += 1
            continue

        try:
            new_path = rename_with_stem(filepath)
            if new_path:
                print(f"[name] {filepath.name} → {new_path.name}")
                renamed += 1
            else:
                skipped += 1
        except (FileExistsError, FileNotFoundError) as exc:
            print(f"[name] ERROR: {exc}", file=sys.stderr)
            errors += 1

    print(f"[name] Done: {renamed} renamed, {skipped} skipped, {errors} errors")
    return 1 if errors else 0


def main() -> int:
    if len(sys.argv) < 2:
        return scan_and_rename()

    filepath = Path(sys.argv[1])

    if len(sys.argv) >= 3:
        description = sys.argv[2]
        try:
            new_path = rename_file(filepath, description)
        except (FileNotFoundError, FileExistsError, ValueError) as exc:
            print(f"[name] ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"[name] Renamed: {filepath}")
        print(f"[name]      → {new_path}")
        return 0

    try:
        new_path = rename_with_stem(filepath)
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"[name] ERROR: {exc}", file=sys.stderr)
        return 1

    if new_path:
        print(f"[name] Renamed: {filepath}")
        print(f"[name]      → {new_path}")
    else:
        print(f"[name] Already correct: {filepath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
