"""Tests for scripts/format_code.py.

Copyright 2026 by DTS, The State of Utah
"""

from scripts.ui.format_code import format_python


def test_format_python_succeeds():
    """Formatting the project Python files should succeed (they are already formatted)."""
    assert format_python() is True
