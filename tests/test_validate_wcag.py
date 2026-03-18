"""Tests for scripts/validate_wcag.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from scripts.ui.validate_wcag import (
    Violation,
    WCAGParser,
    _check_file,
    _ParseContext,
    validate,
)


def test_validate_valid_html_no_violations(sample_html):
    violations = validate(sample_html)
    assert violations == []


def test_validate_missing_lang_reports_violation(sample_html_no_lang):
    violations = validate(sample_html_no_lang)
    rules = [v.rule for v in violations]
    assert "3.1.1" in rules


def test_violation_dataclass_fields():
    v = Violation(rule="1.1.1", message="Missing alt", file="test.html", line=5)
    assert v.rule == "1.1.1"
    assert v.message == "Missing alt"
    assert v.file == "test.html"
    assert v.line == 5


def test_wcag_parser_img_without_alt():
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed('<html lang="en"><head><title>T</title></head><body><img src="x"></body></html>')
    rules = [v.rule for v in ctx.violations]
    assert "1.1.1" in rules


def test_wcag_parser_img_with_alt():
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head>'
        '<body><img src="x" alt="description"></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "1.1.1" not in rules


def test_validate_empty_directory(tmp_path):
    violations = validate(tmp_path)
    assert violations == []


def test_wcag_parser_missing_title(tmp_path):
    html_file = tmp_path / "no_title.html"
    html_file.write_text('<html lang="en"><head></head><body></body></html>', encoding="utf-8")
    violations = _check_file(html_file)
    rules = [v.rule for v in violations]
    assert "2.4.2" in rules


def test_wcag_parser_link_without_text():
    """An anchor with no text and no aria-label is a 2.4.4 violation."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head><body><a href="/page"></a></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "2.4.4" in rules


def test_wcag_parser_link_with_text():
    """An anchor with text is not a 2.4.4 violation."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head>'
        '<body><a href="/page">About Us</a></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "2.4.4" not in rules


def test_wcag_parser_link_with_aria_label():
    """An anchor with aria-label is not a 2.4.4 violation."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head>'
        '<body><a href="/page" aria-label="About page"></a></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "2.4.4" not in rules


def test_wcag_parser_input_without_label():
    """An input without accessible name is a 4.1.2 violation."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head><body><input type="text"></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "4.1.2" in rules


def test_wcag_parser_input_with_id_not_flagged():
    """An input with id (for label association) passes 4.1.2."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head>'
        '<body><input type="text" id="name-input"></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "4.1.2" not in rules


def test_wcag_parser_hidden_input_not_flagged():
    """A hidden input does not need an accessible name."""
    ctx = _ParseContext(file="test.html")
    parser = WCAGParser(ctx)
    parser.feed(
        '<html lang="en"><head><title>T</title></head>'
        '<body><input type="hidden" name="csrf"></body></html>'
    )
    rules = [v.rule for v in ctx.violations]
    assert "4.1.2" not in rules


def test_validate_dist_not_found(tmp_path):
    """validate returns a BUILD violation when dist doesn't exist."""
    violations = validate(tmp_path / "nonexistent")
    rules = [v.rule for v in violations]
    assert "BUILD" in rules


def test_validate_main_returns_zero(tmp_path, monkeypatch):
    """main() returns 0 with valid HTML."""
    import scripts.ui.validate_wcag as wcag_mod

    html_dir = tmp_path / "dist"
    html_dir.mkdir()
    (html_dir / "ok.html").write_text(
        '<!DOCTYPE html><html lang="en"><head><title>X</title></head>'
        "<body><h1>Hi</h1></body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(wcag_mod, "DIST_DIR", html_dir)
    result = wcag_mod.main()
    assert result == 0


def test_validate_main_returns_one(tmp_path, monkeypatch):
    """main() returns 1 with invalid HTML."""
    import scripts.ui.validate_wcag as wcag_mod

    (tmp_path / "bad.html").write_text(
        "<!DOCTYPE html><html><head></head><body></body></html>",
        encoding="utf-8",
    )
    # Patch validate to call with our tmp_path instead of default DIST_DIR
    original_validate = wcag_mod.validate
    monkeypatch.setattr(wcag_mod, "validate", lambda dist_dir=tmp_path: original_validate(tmp_path))
    result = wcag_mod.main()
    assert result == 1
