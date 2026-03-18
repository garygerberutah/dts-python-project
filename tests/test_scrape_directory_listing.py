"""Tests for scripts/util/scrape_directory_listing.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.util.scrape_directory_listing as sdl_mod
from scripts.util.scrape_directory_listing import _collect_files, main, run


def test_collect_files_returns_sorted_paths(tmp_path):
    """_collect_files returns sorted fully-qualified file paths."""
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "a.txt").write_text("a")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("c")

    result = _collect_files(tmp_path)

    assert len(result) == 3
    assert result == sorted(result)
    assert all(isinstance(p, str) for p in result)


def test_collect_files_excludes_directories(tmp_path):
    """_collect_files only returns files, not directories."""
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "subdir").mkdir()

    result = _collect_files(tmp_path)

    assert len(result) == 1
    assert "file.txt" in result[0]


def test_collect_files_empty_directory(tmp_path):
    """_collect_files returns empty list for empty directory."""
    assert _collect_files(tmp_path) == []


def test_run_creates_csv(tmp_path):
    """run() creates a timestamped CSV with file listings."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "hello.txt").write_text("hello")
    out_dir = tmp_path / "output"

    with patch.object(sdl_mod, "FS_INFO_DIR", out_dir):
        result = run(str(target))

    assert result is True
    csv_files = list(out_dir.glob("fs-*.csv"))
    assert len(csv_files) == 1

    with open(csv_files[0], newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["path"]
    assert len(rows) == 2  # header + 1 file


def test_run_nonexistent_directory_returns_false():
    """run() returns False for a nonexistent directory."""
    assert run("/nonexistent/path/that/does/not/exist") is False


def test_run_empty_directory_still_creates_csv(tmp_path):
    """run() creates a CSV even for an empty directory (header only)."""
    out_dir = tmp_path / "output"

    with patch.object(sdl_mod, "FS_INFO_DIR", out_dir):
        result = run(str(tmp_path))

    assert result is True
    csv_files = list(out_dir.glob("fs-*.csv"))
    assert len(csv_files) == 1


def test_main_exits_on_failure(monkeypatch):
    """main() exits with code 1 when run() fails."""
    monkeypatch.setattr("sys.argv", ["scrape_directory_listing.py", "/nonexistent"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_succeeds(tmp_path, monkeypatch):
    """main() completes without error for a valid directory."""
    out_dir = tmp_path / "output"
    monkeypatch.setattr("sys.argv", ["scrape_directory_listing.py", str(tmp_path)])

    with patch.object(sdl_mod, "FS_INFO_DIR", out_dir):
        main()  # should not raise
