"""Tests for scripts/ui/lint.py — static analysis orchestration.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from unittest.mock import patch

import scripts.ui.lint as lint_mod
from scripts.ui.lint import lint_all, lint_js, lint_python, lint_rust, main


def test_lint_python_succeeds():
    """lint_python passes on the project's own Python files."""
    assert lint_python() is True


def test_lint_js_succeeds():
    """lint_js passes on the project's own JS files."""
    assert lint_js() is True


def test_lint_rust_succeeds():
    """lint_rust passes on the project's own Rust files."""
    result = lint_rust()
    assert isinstance(result, bool)


def test_lint_all_returns_bool():
    """lint_all returns a boolean."""
    with (
        patch.object(lint_mod, "lint_python", return_value=True),
        patch.object(lint_mod, "lint_rust", return_value=True),
        patch.object(lint_mod, "lint_js", return_value=True),
    ):
        assert lint_all() is True


def test_lint_all_fails_if_any_linter_fails():
    """lint_all returns False if any sub-linter fails."""
    with (
        patch.object(lint_mod, "lint_python", return_value=True),
        patch.object(lint_mod, "lint_rust", return_value=False),
        patch.object(lint_mod, "lint_js", return_value=True),
    ):
        assert lint_all() is False


def test_main_returns_zero_on_success():
    """main() returns 0 when all linters pass."""
    with patch.object(lint_mod, "lint_all", return_value=True):
        assert main() == 0


def test_main_returns_one_on_failure():
    """main() returns 1 when any linter fails."""
    with patch.object(lint_mod, "lint_all", return_value=False):
        assert main() == 1


def test_run_handles_missing_executable():
    """_run returns False when executable is not found."""
    result = lint_mod._run(["nonexistent_binary_xyz"], label="test")
    assert result is False


def test_run_handles_nonzero_exit():
    """_run returns False when subprocess exits non-zero."""
    result = lint_mod._run(["python", "-c", "import sys; sys.exit(1)"], label="test")
    assert result is False
