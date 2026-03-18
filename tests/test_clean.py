"""Tests for scripts/ui/clean.py — build artifact removal.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from pathlib import Path

import scripts.ui.clean as clean_mod
from scripts.ui.clean import clean, main


def test_clean_removes_dist(tmp_path, monkeypatch):
    """clean() removes the dist/ directory."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html/>", encoding="utf-8")

    monkeypatch.setattr(clean_mod, "DIST_DIR", dist)
    monkeypatch.setattr(clean_mod, "WASM_PKG_DIR", tmp_path / "pkg")

    clean()
    assert not dist.exists()


def test_clean_removes_wasm_pkg(tmp_path, monkeypatch):
    """clean() removes the wasm/pkg/ directory."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "ggp3d.js").write_text("export {}", encoding="utf-8")

    monkeypatch.setattr(clean_mod, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(clean_mod, "WASM_PKG_DIR", pkg)

    clean()
    assert not pkg.exists()


def test_clean_nothing_to_clean(tmp_path, monkeypatch):
    """clean() handles case where neither directory exists."""
    monkeypatch.setattr(clean_mod, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(clean_mod, "WASM_PKG_DIR", tmp_path / "pkg")

    clean()  # Should not raise


def test_main_returns_zero(tmp_path, monkeypatch):
    """main() returns 0."""
    monkeypatch.setattr(clean_mod, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(clean_mod, "WASM_PKG_DIR", tmp_path / "pkg")

    assert main() == 0
