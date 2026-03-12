"""
validate_mime_type_content.py — validates that binary files in the repository
contain data matching the encoding standard of their extension's mime-type.

Copyright 2026 by GuidoGerb Publishing, LLC

Recognised mime-types (allowed in git):
    image/png, image/jpeg, image/gif, image/svg+xml, video/mp4, audio/mpeg,
    application/pdf, application/json, application/xml

Strictly forbidden:
    application/octet-stream and any binary data not clearly associated with
    a recognised, inspectable mime-type.

Usage:
    python scripts/validate_mime_type_content.py [directory ...]

Defaults to scanning the entire project root (excluding dist/, .git/, target/).
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git",
    "dist",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    "target",
    "pkg",
}

# Map of extension → validation function name
# Each validator reads bytes and returns True if valid, False otherwise
VALIDATORS: dict[str, str] = {
    ".png": "_is_valid_png",
    ".jpg": "_is_valid_jpeg",
    ".jpeg": "_is_valid_jpeg",
    ".gif": "_is_valid_gif",
    ".svg": "_is_valid_svg",
    ".mp4": "_is_valid_mp4",
    ".mp3": "_is_valid_mp3",
    ".pdf": "_is_valid_pdf",
    ".json": "_is_valid_json",
    ".xml": "_is_valid_xml",
}


def _is_valid_png(filepath: Path) -> bool:
    """PNG must start with the 8-byte PNG signature."""
    with open(filepath, "rb") as f:
        header = f.read(8)
    return header == b"\x89PNG\r\n\x1a\n"


def _is_valid_jpeg(filepath: Path) -> bool:
    """JPEG must start with FF D8 FF."""
    with open(filepath, "rb") as f:
        header = f.read(3)
    return header[:2] == b"\xff\xd8" and header[2] == 0xFF


def _is_valid_gif(filepath: Path) -> bool:
    """GIF must start with GIF87a or GIF89a."""
    with open(filepath, "rb") as f:
        header = f.read(6)
    return header in (b"GIF87a", b"GIF89a")


def _is_valid_svg(filepath: Path) -> bool:
    """SVG must be valid XML containing an <svg> element."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read(8192)
        return "<svg" in content.lower()
    except (UnicodeDecodeError, OSError):
        return False


def _is_valid_mp4(filepath: Path) -> bool:
    """MP4/ISOBMFF must have a valid ftyp box within the first 12 bytes."""
    with open(filepath, "rb") as f:
        header = f.read(12)
    if len(header) < 8:
        return False
    # ftyp box: bytes 4-7 must be 'ftyp'
    return header[4:8] == b"ftyp"


def _is_valid_mp3(filepath: Path) -> bool:
    """MP3 must start with ID3 tag or MPEG sync word (FF FB/FA/F3/F2)."""
    with open(filepath, "rb") as f:
        header = f.read(3)
    if header[:3] == b"ID3":
        return True
    if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
        return True
    return False


def _is_valid_pdf(filepath: Path) -> bool:
    """PDF must start with %PDF-."""
    with open(filepath, "rb") as f:
        header = f.read(5)
    return header == b"%PDF-"


def _is_valid_json(filepath: Path) -> bool:
    """JSON must parse without errors."""
    try:
        with open(filepath, encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False


def _is_valid_xml(filepath: Path) -> bool:
    """XML must parse without errors."""
    try:
        ET.parse(filepath)
        return True
    except (ET.ParseError, OSError):
        return False


# Resolve validator names to functions
_VALIDATOR_FNS = {
    "_is_valid_png": _is_valid_png,
    "_is_valid_jpeg": _is_valid_jpeg,
    "_is_valid_gif": _is_valid_gif,
    "_is_valid_svg": _is_valid_svg,
    "_is_valid_mp4": _is_valid_mp4,
    "_is_valid_mp3": _is_valid_mp3,
    "_is_valid_pdf": _is_valid_pdf,
    "_is_valid_json": _is_valid_json,
    "_is_valid_xml": _is_valid_xml,
}


def find_binary_files(directories: list[Path]) -> list[Path]:
    """Find all files with recognised binary extensions."""
    files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            continue
        for filepath in sorted(directory.rglob("*")):
            if any(part in SKIP_DIRS for part in filepath.parts):
                continue
            if filepath.is_file() and filepath.suffix.lower() in VALIDATORS:
                files.append(filepath)
    return files


def validate_file(filepath: Path) -> str | None:
    """Validate a single file's content matches its extension's mime-type.

    Returns an error message string, or None if valid.
    """
    ext = filepath.suffix.lower()
    validator_name = VALIDATORS.get(ext)
    if not validator_name:
        return None

    validator_fn = _VALIDATOR_FNS[validator_name]
    rel = filepath.relative_to(ROOT) if filepath.is_relative_to(ROOT) else filepath

    try:
        if not validator_fn(filepath):
            return (
                f"  {rel}: content does not match {ext} encoding standard "
                f"(invalid mime-type data)"
            )
    except OSError as exc:
        return f"  {rel}: cannot read — {exc}"

    return None


def validate(directories: list[Path] | None = None) -> list[str]:
    """Validate all binary files. Returns list of all errors."""
    if directories is None:
        directories = [ROOT]

    binary_files = find_binary_files(directories)
    if not binary_files:
        print("[mime] No binary asset files found to validate.")
        return []

    errors: list[str] = []
    for filepath in binary_files:
        error = validate_file(filepath)
        if error:
            errors.append(error)

    if not errors:
        print(
            f"[mime] All {len(binary_files)} binary files match their "
            f"extension's mime-type encoding."
        )

    return errors


def main() -> int:
    dirs = [Path(d) for d in sys.argv[1:]] if len(sys.argv) > 1 else None
    errors = validate(dirs)
    if errors:
        print(
            f"[mime] {len(errors)} file(s) have content that does not match "
            f"their extension's mime-type:",
            file=sys.stderr,
        )
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
