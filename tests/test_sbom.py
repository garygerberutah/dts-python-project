"""Tests for scripts/blockchain/sbom.json integrity.

Copyright 2026 by GuidoGerb Publishing, LLC

Verifies that the SBOM manifest matches the actual repository filesystem:
  - Every git-tracked file (except sbom.json itself) appears in the manifest
  - Every entry in the manifest corresponds to an existing file
  - Every SHA-256 hash in the manifest matches the file's actual content
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SBOM_PATH = ROOT / "scripts" / "blockchain" / "sbom.json"
CHAIN_PATH = ROOT / "scripts" / "blockchain" / "chain.json"
# These files are outputs of the SBOM stage — excluded from the manifest.
_EXCLUDED_RELS = {
    SBOM_PATH.relative_to(ROOT).as_posix(),
    CHAIN_PATH.relative_to(ROOT).as_posix(),
}


@pytest.fixture(scope="module")
def sbom_manifest():
    """Load the SBOM manifest from disk."""
    assert SBOM_PATH.exists(), f"SBOM file not found: {SBOM_PATH}"
    return json.loads(SBOM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def git_tracked_files():
    """Return the set of git-tracked file paths (relative to repo root)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git ls-files failed: {result.stderr}"
    paths = {line for line in result.stdout.splitlines() if line}
    paths -= _EXCLUDED_RELS
    return paths


def _sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_sbom_has_valid_structure(sbom_manifest):
    """SBOM manifest contains expected top-level keys."""
    assert sbom_manifest["version"] == "1.0"
    assert "timestamp" in sbom_manifest
    assert isinstance(sbom_manifest["file_count"], int)
    assert isinstance(sbom_manifest["files"], list)
    assert sbom_manifest["file_count"] == len(sbom_manifest["files"])


def test_sbom_files_match_git_tracked(sbom_manifest, git_tracked_files):
    """Every git-tracked file appears in the SBOM and vice-versa."""
    sbom_paths = {entry["path"] for entry in sbom_manifest["files"]}

    missing_from_sbom = git_tracked_files - sbom_paths
    extra_in_sbom = sbom_paths - git_tracked_files

    errors = []
    if missing_from_sbom:
        errors.append(f"Files tracked by git but missing from SBOM: {sorted(missing_from_sbom)}")
    if extra_in_sbom:
        errors.append(f"Files in SBOM but not tracked by git: {sorted(extra_in_sbom)}")

    assert not errors, "\n".join(errors)


def test_sbom_sha256_hashes_correct(sbom_manifest):
    """Every SHA-256 hash in the SBOM matches the actual file content."""
    mismatches = []
    for entry in sbom_manifest["files"]:
        filepath = ROOT / entry["path"]
        if not filepath.is_file():
            mismatches.append(f"  {entry['path']}: file does not exist")
            continue
        actual = _sha256(filepath)
        if actual != entry["sha256"]:
            mismatches.append(
                f"  {entry['path']}: expected {entry['sha256']}, got {actual}"
            )

    assert not mismatches, "SHA-256 mismatches:\n" + "\n".join(mismatches)


def test_sbom_file_count_matches(sbom_manifest, git_tracked_files):
    """SBOM file_count matches the number of git-tracked files (minus sbom.json)."""
    assert sbom_manifest["file_count"] == len(git_tracked_files)


def test_sbom_entries_have_required_fields(sbom_manifest):
    """Every SBOM entry has both 'path' and 'sha256' keys."""
    for i, entry in enumerate(sbom_manifest["files"]):
        assert "path" in entry, f"Entry {i} missing 'path'"
        assert "sha256" in entry, f"Entry {i} missing 'sha256'"
        assert len(entry["sha256"]) == 64, f"Entry {i} has invalid SHA-256 length"
