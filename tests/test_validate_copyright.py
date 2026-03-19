"""Tests for scripts/validate_copyright.py.

Copyright 2026 by DTS, The State of Utah
"""

from pathlib import Path

import scripts.ui.validate_copyright as vc_mod
from scripts.ui.validate_copyright import (
    COMMENT_STYLES,
    SOURCE_EXTENSIONS,
    find_source_files,
    validate,
    validate_file,
)

ROOT = Path(__file__).resolve().parent.parent


def test_validate_file_passes_with_correct_copyright():
    """A source file within the project tree with correct copyright passes."""
    candidate = ROOT / "run.py"
    if candidate.exists():
        copyright_text = "Copyright 2026 by DTS, The State of Utah"
        assert validate_file(candidate, copyright_text) is None


def test_validate_returns_errors_for_file_without_copyright(tmp_tree, monkeypatch):
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "bad.py"
    f.write_text('print("no copyright")\n', encoding="utf-8")
    errors = validate(directories=[tmp_tree])
    assert len(errors) > 0
    assert any("missing" in e.lower() or "incorrect" in e.lower() for e in errors)


def test_validate_returns_empty_for_valid_tree(tmp_tree, monkeypatch):
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "good.py"
    f.write_text(
        "# Copyright 2026 by DTS, The State of Utah\n",
        encoding="utf-8",
    )
    errors = validate(directories=[tmp_tree])
    assert errors == []


def test_validate_returns_errors_for_missing_copyright(tmp_tree, monkeypatch):
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "bad.py"
    f.write_text('print("hello")\n', encoding="utf-8")
    errors = validate(directories=[tmp_tree])
    assert len(errors) > 0


def test_validate_fix_inserts_copyright(tmp_tree, monkeypatch):
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "fix_me.js"
    f.write_text("const x = 1;\n", encoding="utf-8")
    errors = validate(directories=[tmp_tree], fix=True)
    assert errors == []
    content = f.read_text(encoding="utf-8")
    assert "Copyright 2026 by DTS, The State of Utah" in content


def test_find_source_files_respects_extensions(tmp_tree):
    (tmp_tree / "a.py").write_text("# test\n", encoding="utf-8")
    (tmp_tree / "b.txt").write_text("test\n", encoding="utf-8")
    files = find_source_files([tmp_tree])
    names = {f.name for f in files}
    assert "a.py" in names
    assert "b.txt" not in names


def test_find_source_files_skips_git_dir(tmp_tree):
    git_dir = tmp_tree / ".git"
    git_dir.mkdir()
    (git_dir / "config.py").write_text("# in git\n", encoding="utf-8")
    files = find_source_files([tmp_tree])
    assert not any(".git" in str(f) for f in files)


def test_comment_styles_cover_all_source_extensions():
    for ext in SOURCE_EXTENSIONS:
        assert ext in COMMENT_STYLES, f"No comment style defined for {ext}"


def test_validate_fix_replaces_wrong_copyright(tmp_tree, monkeypatch):
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "wrong.py"
    f.write_text(
        "# Copyright 2020 by SomeOther Corp\nprint('hi')\n",
        encoding="utf-8",
    )
    errors = validate(directories=[tmp_tree], fix=True)
    assert errors == []
    content = f.read_text(encoding="utf-8")
    assert "Copyright 2026 by DTS, The State of Utah" in content
    assert "SomeOther Corp" not in content
