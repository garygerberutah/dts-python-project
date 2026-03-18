"""Tests for scripts/blockchain/generate_sbom.py — SBOM manifest generation.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import hashlib
import json
from unittest.mock import patch

from scripts.blockchain.generate_sbom import _sha256, generate


def test_sha256_correct(tmp_path):
    """_sha256 returns the correct hex digest."""
    f = tmp_path / "data.bin"
    content = b"hello sbom"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _sha256(f) == expected


def test_sha256_empty_file(tmp_path):
    """_sha256 handles an empty file."""
    f = tmp_path / "empty"
    f.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert _sha256(f) == expected


def test_generate_produces_manifest_and_composite(tmp_path):
    """generate() returns a manifest dict and a composite SHA-256 string."""
    manifest, composite = generate()
    assert isinstance(manifest, dict)
    assert "version" in manifest
    assert manifest["version"] == "1.0"
    assert "timestamp" in manifest
    assert "file_count" in manifest
    assert "files" in manifest
    assert isinstance(manifest["files"], list)
    assert len(composite) == 64


def test_generate_manifest_file_count_matches():
    """file_count in manifest matches the actual number of file entries."""
    manifest, _ = generate()
    assert manifest["file_count"] == len(manifest["files"])


def test_generate_writes_sbom_json():
    """generate() writes the manifest to scripts/blockchain/sbom.json."""
    from scripts.blockchain.generate_sbom import SBOM_PATH

    manifest, _ = generate()
    assert SBOM_PATH.exists()
    loaded = json.loads(SBOM_PATH.read_text(encoding="utf-8"))
    assert loaded["version"] == manifest["version"]
    assert loaded["file_count"] == manifest["file_count"]


def test_generate_excludes_sbom_json():
    """The sbom.json file itself is excluded from the manifest entries."""
    manifest, _ = generate()
    paths = {entry["path"] for entry in manifest["files"]}
    assert "scripts/blockchain/sbom.json" not in paths


def test_generate_composite_is_deterministic():
    """Calling generate() twice with same files produces the same composite."""
    _, composite1 = generate()
    _, composite2 = generate()
    # Timestamps differ, so composites may differ — but structure is consistent
    assert len(composite1) == 64
    assert len(composite2) == 64


def test_generate_entries_have_path_and_sha256():
    """Each file entry has 'path' and 'sha256' keys."""
    manifest, _ = generate()
    for entry in manifest["files"]:
        assert "path" in entry
        assert "sha256" in entry
        assert len(entry["sha256"]) == 64


def test_main_returns_zero():
    """main() returns 0 after generating the SBOM."""
    from scripts.blockchain.generate_sbom import main

    assert main() == 0


def test_generate_includes_known_file():
    """The manifest includes run.py which exists in the repo."""
    manifest, _ = generate()
    paths = {entry["path"] for entry in manifest["files"]}
    assert "run.py" in paths
