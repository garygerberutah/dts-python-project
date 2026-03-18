"""Tests for scripts/validate_copyright.py.

Copyright 2026 by GuidoGerb Publishing, LLC
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
        copyright_text = "Copyright 2026 by GuidoGerb Publishing, LLC"
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
        "# Copyright 2026 by GuidoGerb Publishing, LLC\n",
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
    assert "Copyright 2026 by GuidoGerb Publishing, LLC" in content


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
    assert "Copyright 2026 by GuidoGerb Publishing, LLC" in content
    assert "SomeOther Corp" not in content


def test_validate_missing_copyright_file(tmp_path, monkeypatch):
    """validate returns error when COPYRIGHT file doesn't exist."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_path)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_path / "COPYRIGHT")
    errors = validate(directories=[tmp_path])
    assert any("COPYRIGHT file not found" in e for e in errors)


def test_validate_no_source_files(tmp_tree, monkeypatch):
    """validate returns empty list when no source files are found."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    empty = tmp_tree / "empty_dir"
    empty.mkdir()
    errors = validate(directories=[empty])
    assert errors == []


def test_fix_inserts_into_python_docstring(tmp_tree, monkeypatch):
    """Fix inserts copyright into Python file starting with docstring."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "docstring.py"
    f.write_text('"""My module docstring.\n"""\npass\n', encoding="utf-8")
    errors = validate(directories=[tmp_tree], fix=True)
    assert errors == []
    content = f.read_text(encoding="utf-8")
    assert "Copyright 2026 by GuidoGerb Publishing, LLC" in content


def test_fix_inserts_after_shebang(tmp_tree, monkeypatch):
    """Fix inserts copyright after shebang line in Python file."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    f = tmp_tree / "shebang.py"
    f.write_text("#!/usr/bin/env python3\npass\n", encoding="utf-8")
    errors = validate(directories=[tmp_tree], fix=True)
    assert errors == []
    content = f.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env python3\n")
    assert "Copyright 2026 by GuidoGerb Publishing, LLC" in content


def test_make_comment_js():
    """_make_comment wraps copyright text in JS comment style."""
    from scripts.ui.validate_copyright import _make_comment

    result = _make_comment("Test", ".js")
    assert result == "/** Test */"


def test_make_comment_html():
    """_make_comment wraps copyright text in HTML comment style."""
    from scripts.ui.validate_copyright import _make_comment

    result = _make_comment("Test", ".html")
    assert result == "<!-- Test -->"


def test_main_returns_zero_on_success(tmp_tree, monkeypatch):
    """main returns 0 when all files pass."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    (tmp_tree / "ok.py").write_text(
        "# Copyright 2026 by GuidoGerb Publishing, LLC\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["validate_copyright.py"])
    from scripts.ui.validate_copyright import main

    assert main() == 0


def test_main_returns_one_on_errors(tmp_tree, monkeypatch):
    """main returns 1 when files have copyright issues."""
    monkeypatch.setattr(vc_mod, "ROOT", tmp_tree)
    monkeypatch.setattr(vc_mod, "COPYRIGHT_FILE", tmp_tree / "COPYRIGHT")
    (tmp_tree / "bad.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["validate_copyright.py"])
    from scripts.ui.validate_copyright import main

    assert main() == 1
