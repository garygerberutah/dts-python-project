"""Tests for scripts/util/add_guidogerb_submodules.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import scripts.util.add_guidogerb_submodules as ags_mod
from scripts.util.add_guidogerb_submodules import (
    _extract_readme_description,
    _get_existing_submodules,
    _name_from_path,
    _submodule_path,
    main,
    run,
)


def test_submodule_path_returns_prefixed():
    """_submodule_path returns 'submodules/<name>'."""
    assert _submodule_path("my-repo") == "submodules/my-repo"


def test_name_from_path_strips_prefix():
    """_name_from_path extracts repo name from submodule path."""
    assert _name_from_path("submodules/my-repo") == "my-repo"
    assert _name_from_path("my-repo") == "my-repo"


def test_get_existing_submodules_no_gitmodules(tmp_path):
    """_get_existing_submodules returns empty dict when .gitmodules is absent."""
    result = _get_existing_submodules(tmp_path)
    assert result == {}


def test_get_existing_submodules_parses_gitmodules(tmp_path):
    """_get_existing_submodules parses .gitmodules file via git config."""
    (tmp_path / ".gitmodules").write_text(
        '[submodule "foo"]\n\tpath = submodules/foo\n\turl = https://github.com/x/foo.git\n'
    )

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        "submodule.foo.path=submodules/foo\nsubmodule.foo.url=https://github.com/x/foo.git\n"
    )

    with patch("scripts.util.add_guidogerb_submodules.subprocess.run", return_value=mock_result):
        result = _get_existing_submodules(tmp_path)

    assert result == {"submodules/foo": "https://github.com/x/foo.git"}


def test_get_existing_submodules_git_config_fails(tmp_path):
    """_get_existing_submodules returns empty dict when git config fails."""
    (tmp_path / ".gitmodules").write_text("[submodule]")
    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("scripts.util.add_guidogerb_submodules.subprocess.run", return_value=mock_result):
        result = _get_existing_submodules(tmp_path)

    assert result == {}


def test_extract_readme_description_no_readme(tmp_path):
    """_extract_readme_description returns empty string when no README exists."""
    sub_dir = tmp_path / "submodules" / "no-readme"
    sub_dir.mkdir(parents=True)

    assert _extract_readme_description(tmp_path, "no-readme") == ""


def test_extract_readme_description_extracts_first_paragraph(tmp_path):
    """_extract_readme_description extracts first non-heading paragraph."""
    sub_dir = tmp_path / "submodules" / "my-repo"
    sub_dir.mkdir(parents=True)
    (sub_dir / "README.md").write_text(
        "# My Repo\n\nThis is the best repo ever.\n\nMore details here.\n"
    )

    desc = _extract_readme_description(tmp_path, "my-repo")

    assert desc == "This is the best repo ever."


def test_extract_readme_description_skips_badges(tmp_path):
    """_extract_readme_description skips badge image lines."""
    sub_dir = tmp_path / "submodules" / "badge-repo"
    sub_dir.mkdir(parents=True)
    (sub_dir / "README.md").write_text(
        "# Badge Repo\n\n[![CI](https://img.shields.io/badge)]\n\nActual description.\n"
    )

    desc = _extract_readme_description(tmp_path, "badge-repo")

    assert "Actual description" in desc


def test_extract_readme_description_truncates_long_text(tmp_path):
    """_extract_readme_description truncates descriptions over 150 chars."""
    sub_dir = tmp_path / "submodules" / "long-repo"
    sub_dir.mkdir(parents=True)
    (sub_dir / "README.md").write_text(f"# Long\n\n{'A' * 200}\n")

    desc = _extract_readme_description(tmp_path, "long-repo")

    assert len(desc) <= 150
    assert desc.endswith("...")


def test_run_requires_git_repo(tmp_path):
    """run() returns False for a directory that is not a git repo."""
    result = run(str(tmp_path))
    assert result is False


@patch("scripts.util.add_guidogerb_submodules._fetch_all_repos")
def test_run_handles_http_error(mock_fetch, tmp_path):
    """run() returns False when GitHub API fails."""
    import urllib.error

    (tmp_path / ".git").mkdir()
    mock_fetch.side_effect = urllib.error.HTTPError(
        url="http://test", code=403, msg="Forbidden", hdrs={}, fp=None
    )

    result = run(str(tmp_path))
    assert result is False


def test_main_exits_on_failure(monkeypatch):
    """main() exits with code 1 when run() fails."""
    monkeypatch.setattr("sys.argv", ["add_guidogerb_submodules.py", "/nonexistent"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@patch.object(ags_mod, "run", return_value=True)
def test_main_succeeds(mock_run, monkeypatch):
    """main() completes without error when run() succeeds."""
    monkeypatch.setattr("sys.argv", ["add_guidogerb_submodules.py", "/some/path"])
    main()  # should not raise
    mock_run.assert_called_once()
