"""Tests for scripts/util/list_all_guidogerb_repos.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import scripts.util.list_all_guidogerb_repos as lr_mod
from scripts.util.list_all_guidogerb_repos import _build_opener, _fetch_repos, main, run


def test_build_opener_without_token():
    """_build_opener creates an opener with standard headers."""
    opener = _build_opener(None)
    header_names = [h[0] for h in opener.addheaders]
    assert "Accept" in header_names
    assert "User-Agent" in header_names
    assert "Authorization" not in header_names


def test_build_opener_with_token():
    """_build_opener includes Authorization header when token is provided."""
    opener = _build_opener("test-token")
    header_names = [h[0] for h in opener.addheaders]
    assert "Authorization" in header_names
    auth = next(v for k, v in opener.addheaders if k == "Authorization")
    assert auth == "Bearer test-token"


@patch("scripts.util.list_all_guidogerb_repos.urllib.request.urlopen")
def test_fetch_repos_returns_sorted_names(mock_urlopen):
    """_fetch_repos returns a sorted list of full_name strings."""
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = json.dumps([
        {"full_name": "guidogerb/z-repo"},
        {"full_name": "guidogerb/a-repo"},
    ]).encode()
    mock_urlopen.return_value = mock_response

    repos = _fetch_repos(None)

    assert repos == ["guidogerb/a-repo", "guidogerb/z-repo"]


@patch("scripts.util.list_all_guidogerb_repos.urllib.request.urlopen")
def test_fetch_repos_empty_response(mock_urlopen):
    """_fetch_repos returns empty list when API returns no repos."""
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = json.dumps([]).encode()
    mock_urlopen.return_value = mock_response

    repos = _fetch_repos(None)

    assert repos == []


def test_run_writes_repos_file(tmp_path):
    """run() writes repo names to the output file."""
    out_file = tmp_path / "repos.txt"

    with (
        patch.object(lr_mod, "OUT_DIR", tmp_path),
        patch.object(lr_mod, "OUT_FILE", out_file),
        patch.object(lr_mod, "_fetch_repos", return_value=["guidogerb/foo", "guidogerb/bar"]),
    ):
        result = run()

    assert result is True
    content = out_file.read_text()
    assert "guidogerb/foo\n" in content
    assert "guidogerb/bar\n" in content


def test_run_returns_false_on_http_error(tmp_path):
    """run() returns False when the GitHub API raises an HTTP error."""
    import urllib.error

    with (
        patch.object(lr_mod, "OUT_DIR", tmp_path),
        patch.object(lr_mod, "OUT_FILE", tmp_path / "repos.txt"),
        patch.object(
            lr_mod,
            "_fetch_repos",
            side_effect=urllib.error.HTTPError(
                url="http://test", code=403, msg="Forbidden", hdrs={}, fp=None
            ),
        ),
    ):
        result = run()

    assert result is False


def test_main_exits_on_failure():
    """main() exits with code 1 when run() returns False."""
    import pytest

    with patch.object(lr_mod, "run", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_main_succeeds():
    """main() completes without error when run() returns True."""
    with patch.object(lr_mod, "run", return_value=True):
        main()  # should not raise
