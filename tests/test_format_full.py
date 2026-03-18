"""Tests for scripts/ui/format_code.py — auto-formatting orchestration.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from unittest.mock import patch

import scripts.ui.format_code as fmt_mod
from scripts.ui.format_code import format_all, format_python, format_rust, main


def test_format_python_succeeds():
    """format_python passes on the project's own Python files."""
    assert format_python() is True


def test_format_rust_returns_bool():
    """format_rust returns a boolean."""
    result = format_rust()
    assert isinstance(result, bool)


def test_format_all_returns_true_when_all_pass():
    """format_all returns True when all formatters succeed."""
    with (
        patch.object(fmt_mod, "format_python", return_value=True),
        patch.object(fmt_mod, "format_rust", return_value=True),
    ):
        assert format_all() is True


def test_format_all_returns_false_when_any_fails():
    """format_all returns False when any formatter fails."""
    with (
        patch.object(fmt_mod, "format_python", return_value=True),
        patch.object(fmt_mod, "format_rust", return_value=False),
    ):
        assert format_all() is False


def test_main_returns_zero_on_success():
    """main() returns 0 when all formatters succeed."""
    with patch.object(fmt_mod, "format_all", return_value=True):
        assert main() == 0


def test_main_returns_one_on_failure():
    """main() returns 1 when formatting fails."""
    with patch.object(fmt_mod, "format_all", return_value=False):
        assert main() == 1


def test_run_handles_missing_executable(tmp_path):
    """_run returns False when executable is not found."""
    result = fmt_mod._run(["nonexistent_binary_xyz"], label="test")
    assert result is False
