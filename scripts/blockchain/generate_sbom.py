"""
generate_sbom.py — Build a Software Bill of Materials from git-tracked files.

Copyright 2026 by GuidoGerb Publishing, LLC

Walks all files returned by ``git ls-files``, computes a SHA-256 hash for
each one, and writes the manifest to ``scripts/blockchain/sbom.json``.
The ``sbom.json`` file itself is excluded from the manifest to avoid a
circular dependency.
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SBOM_PATH = Path(__file__).resolve().parent / "sbom.json"

# Relative path of sbom.json from the repo root — excluded from the manifest.
_SBOM_REL = SBOM_PATH.relative_to(ROOT).as_posix()


def _git_ls_files() -> list[str]:
    """Return sorted list of git-tracked file paths (relative to repo root)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[sbom] git ls-files failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    paths = sorted(line for line in result.stdout.splitlines() if line)
    return paths


def _sha256(filepath: Path) -> str:
    """Return hex-encoded SHA-256 digest of *filepath*."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate() -> tuple[dict, str]:
    """Generate the SBOM manifest and return ``(manifest_dict, composite_sha256)``.

    The manifest is also written to ``scripts/blockchain/sbom.json``.
    """
    tracked = _git_ls_files()

    entries: list[dict[str, str]] = []
    for rel in tracked:
        if rel == _SBOM_REL:
            continue
        full = ROOT / rel
        if not full.is_file():
            continue
        entries.append({"path": rel, "sha256": _sha256(full)})

    manifest = {
        "version": "1.0",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),  # noqa: UP017
        "file_count": len(entries),
        "files": entries,
    }

    # Write the manifest
    SBOM_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Composite hash: deterministic hash of the entire sorted manifest
    composite = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()

    print(f"[sbom] Generated SBOM: {len(entries)} files, composite SHA-256: {composite}")
    return manifest, composite


def main() -> int:
    """CLI entry-point for standalone SBOM generation."""
    generate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
