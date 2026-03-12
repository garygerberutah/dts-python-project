"""Tests for scripts/validate_wcag.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from scripts.validate_wcag import (
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
    html_file.write_text(
        '<html lang="en"><head></head><body></body></html>', encoding="utf-8"
    )
    violations = _check_file(html_file)
    rules = [v.rule for v in violations]
    assert "2.4.2" in rules
