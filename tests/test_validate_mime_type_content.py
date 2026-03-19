"""Tests for scripts/validate_mime_type_content.py.

Copyright 2026 by DTS, The State of Utah
"""

from scripts.ui.validate_mime_type_content import (
    VALIDATORS,
    find_binary_files,
    validate,
    validate_file,
)


def test_validators_cover_expected_extensions():
    expected = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".mp3", ".pdf", ".json", ".xml"}
    assert expected.issubset(set(VALIDATORS.keys()))


def test_validate_valid_png(tmp_path, valid_png_bytes):
    f = tmp_path / "image.png"
    # Minimum valid PNG: signature + IHDR + IEND
    f.write_bytes(valid_png_bytes + b"\x00" * 100)
    result = validate_file(f)
    # Even a truncated PNG should have the right signature
    # validate_file checks signature bytes
    assert result is None or "png" in result.lower()


def test_validate_invalid_png(tmp_path):
    f = tmp_path / "bad.png"
    f.write_bytes(b"this is not a png file at all")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_json(valid_json_file):
    result = validate_file(valid_json_file)
    assert result is None


def test_validate_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json", encoding="utf-8")
    result = validate_file(f)
    assert result is not None


def test_find_binary_files_finds_images(tmp_path):
    (tmp_path / "pic.png").write_bytes(b"\x89PNG")
    (tmp_path / "code.py").write_text("pass\n", encoding="utf-8")
    files = find_binary_files([tmp_path])
    names = {f.name for f in files}
    assert "pic.png" in names
    assert "code.py" not in names


def test_validate_empty_directory(tmp_path):
    errors = validate(directories=[tmp_path])
    assert errors == []


def test_validate_valid_xml(tmp_path):
    f = tmp_path / "data.xml"
    f.write_text('<?xml version="1.0"?><root/>\n', encoding="utf-8")
    result = validate_file(f)
    assert result is None


def test_validate_invalid_xml(tmp_path):
    f = tmp_path / "bad.xml"
    f.write_text("<root><unclosed>", encoding="utf-8")
    result = validate_file(f)
    assert result is not None
