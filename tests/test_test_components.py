"""Tests for scripts/ui/test_components.py — pytest test runner.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from unittest.mock import MagicMock, patch

import scripts.ui.test_components as tc_mod
from scripts.ui.test_components import run_all_tests


def test_run_all_tests_returns_true_on_success():
    """run_all_tests returns True when pytest returns 0."""
    with patch("scripts.ui.test_components.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=0)
        assert run_all_tests() is True


def test_run_all_tests_returns_false_on_failure():
    """run_all_tests returns False when pytest returns nonzero."""
    with patch("scripts.ui.test_components.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=1)
        assert run_all_tests() is False


def test_run_all_tests_no_dirs(tmp_path):
    """run_all_tests returns False when no test directories exist."""
    with (
        patch.object(tc_mod, "UI_TESTS_DIR", tmp_path / "nonexistent"),
        patch.object(tc_mod, "TOOLCHAIN_TESTS_DIR", tmp_path / "also_nonexistent"),
    ):
        assert run_all_tests() is False


def test_main_returns_zero_on_success():
    """main() returns 0 when all tests pass."""
    with patch.object(tc_mod, "run_all_tests", return_value=True):
        assert tc_mod.main() == 0


def test_main_returns_one_on_failure():
    """main() returns 1 when tests fail."""
    with patch.object(tc_mod, "run_all_tests", return_value=False):
        assert tc_mod.main() == 1
