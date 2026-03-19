"""
Shared fixtures for toolchain script tests.

Copyright 2026 by DTS, The State of Utah
"""

import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"


@pytest.fixture
def tmp_tree(tmp_path):
    """Create a minimal project tree for validation tests."""
    (tmp_path / "COPYRIGHT").write_text(
        "Copyright 2026 by DTS, The State of Utah\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def tmp_py_file(tmp_tree):
    """Create a Python file with correct copyright."""
    f = tmp_tree / "example.py"
    f.write_text(
        '# Copyright 2026 by DTS, The State of Utah\nprint("hello")\n',
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_js_file(tmp_tree):
    """Create a JS file with correct copyright."""
    f = tmp_tree / "example.js"
    f.write_text(
        '/** Copyright 2026 by DTS, The State of Utah */\nconst x = 1;\n',
        encoding="utf-8",
    )
    return f


@pytest.fixture
def tmp_js_file_no_copyright(tmp_tree):
    """Create a JS file without copyright."""
    f = tmp_tree / "example.js"
    f.write_text("const x = 1;\n", encoding="utf-8")
    return f


@pytest.fixture
def scripts_dir():
    """Return the scripts directory path."""
    return SCRIPTS_DIR


@pytest.fixture
def valid_png_bytes():
    """Return the minimal 8-byte PNG signature."""
    return b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def valid_json_file(tmp_tree):
    """Create a valid JSON file."""
    f = tmp_tree / "data.json"
    f.write_text('{"key": "value"}\n', encoding="utf-8")
    return f


@pytest.fixture
def sample_html(tmp_path):
    """Create a minimal valid WCAG-compliant HTML file."""
    html = textwrap.dedent("""\
        <!DOCTYPE html>
        <html lang="en">
        <head><title>Test Page</title></head>
        <body><h1>Hello</h1></body>
        </html>
    """)
    f = tmp_path / "index.html"
    f.write_text(html, encoding="utf-8")
    return tmp_path


@pytest.fixture
def sample_html_no_lang(tmp_path):
    """Create HTML missing the lang attribute."""
    html = textwrap.dedent("""\
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body><h1>Hello</h1></body>
        </html>
    """)
    f = tmp_path / "bad.html"
    f.write_text(html, encoding="utf-8")
    return tmp_path
