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

# Paths excluded from the manifest — these are outputs of the SBOM stage.
_CHAIN_PATH = Path(__file__).resolve().parent / "chain.json"
_EXCLUDED_RELS = {
    SBOM_PATH.relative_to(ROOT).as_posix(),
    _CHAIN_PATH.relative_to(ROOT).as_posix(),
}


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


def verify_index_worktree() -> list[str]:
    """Check that tracked files in the working tree match the git index.

    Returns a list of error strings (empty == pass).  Any tracked file
    whose working-tree content differs from the staged index version is
    reported, because the SBOM hashes the working tree — a mismatch
    means the SBOM would not reflect what is actually committed.

    Files in ``_EXCLUDED_RELS`` (sbom.json, chain.json) are ignored
    because they are regenerated during the SBOM stage itself.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"git diff failed: {result.stderr.strip()}"]

    dirty = [f for f in result.stdout.splitlines() if f and f not in _EXCLUDED_RELS]
    if not dirty:
        return []
    return [
        f"[sbom] Working tree differs from index for {len(dirty)} file(s) — "
        "stage or discard changes before generating the SBOM:\n  " + "\n  ".join(sorted(dirty))
    ]


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
    Fails if the working tree diverges from the git index for any tracked
    file, preventing TOCTOU hash mismatches.
    """
    worktree_errors = verify_index_worktree()
    if worktree_errors:
        for err in worktree_errors:
            print(err, file=sys.stderr)
        print("[sbom] SBOM generation aborted — index/working-tree mismatch.", file=sys.stderr)
        sys.exit(1)

    tracked = _git_ls_files()

    entries: list[dict[str, str]] = []
    for rel in tracked:
        if rel in _EXCLUDED_RELS:
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
