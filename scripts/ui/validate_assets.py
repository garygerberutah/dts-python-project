"""
validate_assets.py — validates that all static resource files follow the
naming convention and that their SHA-256 hashes match.

Copyright 2026 by GuidoGerb Publishing, LLC

Convention:  camelCaseDescription-<sha256hex>.ext

Checks:
  1. Filename matches the pattern: camelCase-<64 hex chars>.ext
  2. The SHA-256 hash in the filename matches the actual file content hash
  3. The camelCase prefix is valid (starts lowercase, no spaces/underscores)

Usage:
    python scripts/validate_assets.py [directory ...]

Defaults to scanning: frontend/  assets/  dist/ (if they exist)
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Extensions considered static resources (images, vectors, fonts)
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

# Pattern: camelCase prefix, dash, 64 hex chars, dot extension
NAMING_PATTERN = re.compile(
    r"^(?P<name>[a-z][a-zA-Z0-9]*)"
    r"-(?P<hash>[0-9a-f]{64})"
    r"(?P<ext>\.[a-zA-Z0-9]+)$"
)


def sha256_of_file(filepath: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_file(filepath: Path, root: Path) -> list[str]:
    """Validate a single asset file. Returns list of error messages (empty if valid)."""
    errors: list[str] = []
    rel = filepath.relative_to(root)
    name = filepath.name

    match = NAMING_PATTERN.match(name)
    if not match:
        errors.append(
            f"  {rel}: filename does not match pattern 'camelCase-<sha256>.ext' (got '{name}')"
        )
        return errors

    expected_hash = match.group("hash")
    actual_hash = sha256_of_file(filepath)

    if expected_hash != actual_hash:
        errors.append(
            f"  {rel}: SHA-256 mismatch\n"
            f"    filename hash: {expected_hash}\n"
            f"    actual hash:   {actual_hash}"
        )

    return errors


def find_asset_files(search_dirs: list[Path]) -> list[Path]:
    """Find all asset files in the given directories."""
    files: list[Path] = []
    for directory in search_dirs:
        if not directory.exists():
            continue
        for filepath in sorted(directory.rglob("*")):
            if filepath.is_file() and filepath.suffix.lower() in ASSET_EXTENSIONS:
                files.append(filepath)
    return files


def validate(directories: list[Path] | None = None) -> list[str]:
    """Validate all asset files. Returns list of all errors."""
    if directories is None:
        directories = [
            ROOT / "ui",
            ROOT / "assets",
            ROOT / "dist",
        ]

    asset_files = find_asset_files(directories)
    if not asset_files:
        print("[assets] No asset files found to validate.")
        return []

    print(f"[assets] Validating {len(asset_files)} asset file(s)…")
    all_errors: list[str] = []
    for filepath in asset_files:
        errors = validate_file(filepath, ROOT)
        all_errors.extend(errors)

    return all_errors


def main() -> int:
    print("[assets] Running asset naming and hash validation…")

    directories = None
    if len(sys.argv) > 1:
        directories = [Path(d) for d in sys.argv[1:]]

    errors = validate(directories)
    if not errors:
        print("[assets] ✓ All asset files pass naming and hash validation.")
        return 0

    print(f"[assets] ✗ {len(errors)} issue(s) found:", file=sys.stderr)
    for error in errors:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
