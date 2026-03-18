"""Tests for scripts/lint.py and scripts/lint_js.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""


from scripts.ui.lint_js import lint_js_files


def test_lint_js_clean_file(tmp_path):
    """A valid JS file should produce no lint errors."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "app-test.js").write_text(
        '/** Copyright 2026 by GuidoGerb Publishing, LLC */\n'
        'const x = 1;\n'
        'if (x === 1) {\n'
        '  console.info("ok");\n'
        '}\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is True


def test_lint_js_catches_double_equals(tmp_path):
    """The linter must flag == usage."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "bad.js").write_text(
        'const x = 1;\n'
        'if (x == 1) {\n'
        '  console.info("bad");\n'
        '}\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is False


def test_lint_js_catches_var(tmp_path):
    """The linter must flag var declarations."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "bad.js").write_text(
        'var x = 1;\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is False


def test_lint_js_catches_console_log(tmp_path):
    """The linter must flag console.log (but not console.info/warn/error)."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "bad.js").write_text(
        'console.log("debug");\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is False


def test_lint_js_allows_console_info(tmp_path):
    """console.info should not be flagged."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "ok.js").write_text(
        'console.info("ok");\nconsole.warn("ok");\nconsole.error("ok");\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is True


def test_lint_js_skips_test_files(tmp_path):
    """*.test.js files should be excluded from linting."""
    comp_dir = tmp_path / "ui" / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "widget.test.js").write_text(
        'var bad = true;\nif (bad == false) {}\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is True


def test_lint_js_skips_wasm_directory(tmp_path):
    """wasm/ directory is exclusively Rust — JS files there should be excluded."""
    pkg_dir = tmp_path / "ui" / "src" / "wasm" / "pkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "ggp3d_wasm.js").write_text(
        'var heap = new Array();\n',
        encoding="utf-8",
    )
    assert lint_js_files(root=tmp_path) is True


def test_lint_js_empty_directory(tmp_path):
    """No JS files should not cause failure."""
    assert lint_js_files(root=tmp_path) is True
