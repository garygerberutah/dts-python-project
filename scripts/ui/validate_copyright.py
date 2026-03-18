"""
validate_copyright.py — validates that all source files contain the
COPYRIGHT notice in a comment at the top of the file. Automatically
inserts or replaces the copyright comment if it does not match.

Copyright 2026 by GuidoGerb Publishing, LLC

Usage:
    python scripts/validate_copyright.py [--fix] [directory ...]

Defaults to scanning the entire project root (excluding dist/, .git/, etc.)
The --fix flag auto-inserts or replaces mismatched copyright comments.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COPYRIGHT_FILE = ROOT / "COPYRIGHT"

# Extensions to validate and how many bytes from the top to search
SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".rs",
    ".css",
    ".html",
    ".j2",
    ".toml",
    ".cfg",
    ".yml",
    ".yaml",
    ".tf",
    ".scss",
    ".sh",
}

# Directories and files to skip entirely
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "dist",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    "target",
    "pkg",
}

SKIP_FILES = {
    "COPYRIGHT",
    "LICENSE",
    "README.md",
    "requirements.txt",
    "ruff.toml",
    "Cargo.lock",
    ".gitignore",
    ".gitattributes",
}

# Max bytes from start of file to search for the copyright notice
HEAD_BYTES = 1024

# Comment wrappers per file extension
COMMENT_STYLES: dict[str, tuple[str, str]] = {
    # (prefix, suffix) — suffix is empty for line-comment styles
    ".py": ("# ", ""),
    ".js": ("/** ", " */"),
    ".rs": ("// ", ""),
    ".css": ("/* ", " */"),
    ".scss": ("/* ", " */"),
    ".html": ("<!-- ", " -->"),
    ".j2": ("<!-- ", " -->"),
    ".toml": ("# ", ""),
    ".cfg": ("# ", ""),
    ".yml": ("# ", ""),
    ".yaml": ("# ", ""),
    ".tf": ("# ", ""),
    ".sh": ("# ", ""),
}

# Regex to match any existing copyright line (case-insensitive "Copyright" + year + any holder)
COPYRIGHT_LINE_RE = re.compile(
    r"(?:^|\n)[#/*<!-]*\s*Copyright\s+\d{4}\s+.*?(?:\n|$)",
    re.IGNORECASE,
)


def _load_copyright_text() -> str:
    """Load the first line of the COPYRIGHT file (the copyright notice)."""
    with open(COPYRIGHT_FILE, encoding="utf-8") as f:
        return f.readline().strip()


def _make_comment(text: str, ext: str) -> str:
    """Wrap text in the comment style appropriate for the file extension."""
    prefix, suffix = COMMENT_STYLES.get(ext, ("# ", ""))
    return f"{prefix}{text}{suffix}"


def find_source_files(directories: list[Path]) -> list[Path]:
    """Recursively find all source files to check."""
    files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            continue
        for filepath in sorted(directory.rglob("*")):
            if any(part in SKIP_DIRS for part in filepath.parts):
                continue
            if filepath.name in SKIP_FILES:
                continue
            if filepath.is_file() and filepath.suffix in SOURCE_EXTENSIONS:
                files.append(filepath)
    return files


def _has_copyright(head: str, copyright_text: str) -> bool:
    """Check if the copyright text appears in the file head."""
    return copyright_text in head


def _fix_file(filepath: Path, copyright_text: str) -> str | None:
    """Insert or replace the copyright comment in a file.

    Returns a message describing the action taken, or None if no change needed.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        return f"  {filepath.relative_to(ROOT)}: cannot read — {exc}"

    head = content[:HEAD_BYTES]
    ext = filepath.suffix
    comment = _make_comment(copyright_text, ext)

    # Already correct
    if copyright_text in head:
        return None

    # Check if there's an existing (wrong) copyright line to replace
    match = COPYRIGHT_LINE_RE.search(head)
    if match:
        old_line = match.group(0).strip()
        content = content.replace(old_line, comment, 1)
        filepath.write_text(content, encoding="utf-8")
        return f"  {filepath.relative_to(ROOT)}: replaced copyright comment"

    # No existing copyright — insert at the top
    # For Python files with docstrings, insert inside or after the docstring
    if ext == ".py" and content.startswith('"""'):
        # Insert copyright after the opening triple-quote line
        newline_idx = content.index("\n")
        content = content[:newline_idx] + "\n\n" + copyright_text + "\n" + content[newline_idx:]
    elif ext == ".py" and content.startswith("#!"):
        # Shebang — insert after it
        newline_idx = content.index("\n")
        content = content[: newline_idx + 1] + comment + "\n" + content[newline_idx + 1 :]
    else:
        content = comment + "\n" + content

    filepath.write_text(content, encoding="utf-8")
    return f"  {filepath.relative_to(ROOT)}: inserted copyright comment"


def validate_file(filepath: Path, copyright_text: str) -> str | None:
    """Check if a file contains the copyright notice near the top.

    Returns an error message string, or None if valid.
    """
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            head = f.read(HEAD_BYTES)
    except OSError as exc:
        return f"  {filepath.relative_to(ROOT)}: cannot read — {exc}"

    if _has_copyright(head, copyright_text):
        return None

    return f"  {filepath.relative_to(ROOT)}: missing or incorrect copyright notice"


def validate(directories: list[Path] | None = None, fix: bool = False) -> list[str]:
    """Validate all source files. Returns list of all errors."""
    if directories is None:
        directories = [ROOT]

    if not COPYRIGHT_FILE.exists():
        return ["  COPYRIGHT file not found in project root"]

    copyright_text = _load_copyright_text()
    source_files = find_source_files(directories)
    if not source_files:
        print("[copyright] No source files found to validate.")
        return []

    errors: list[str] = []
    fixed: list[str] = []

    for filepath in source_files:
        error = validate_file(filepath, copyright_text)
        if error:
            if fix:
                result = _fix_file(filepath, copyright_text)
                if result:
                    fixed.append(result)
            else:
                errors.append(error)

    if fixed:
        print(f"[copyright] Fixed {len(fixed)} file(s):")
        for msg in fixed:
            print(msg)
        # Re-validate after fixes
        remaining = []
        for filepath in source_files:
            error = validate_file(filepath, copyright_text)
            if error:
                remaining.append(error)
        if remaining:
            return remaining

    if not errors:
        print(f"[copyright] All {len(source_files)} files contain the correct copyright notice.")

    return errors


def main() -> int:
    fix = "--fix" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--fix"]
    dirs = [Path(d) for d in args] if args else None
    errors = validate(dirs, fix=fix)
    if errors:
        print(f"[copyright] {len(errors)} file(s) with copyright issues:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
