"""Tests for scripts/validate_assets.py.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import hashlib

from scripts.ui.validate_assets import (
    ASSET_EXTENSIONS,
    NAMING_PATTERN,
    find_asset_files,
    sha256_of_file,
    validate,
    validate_file,
)


def test_sha256_of_file_correct(tmp_path):
    f = tmp_path / "data.bin"
    content = b"hello world"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert sha256_of_file(f) == expected


def test_naming_pattern_matches_valid_name():
    match = NAMING_PATTERN.match("myIcon-" + "a" * 64 + ".png")
    assert match is not None
    assert match.group("name") == "myIcon"
    assert match.group("ext") == ".png"


def test_naming_pattern_rejects_invalid_name():
    assert NAMING_PATTERN.match("bad_name.png") is None
    assert NAMING_PATTERN.match("MyCap-" + "a" * 64 + ".png") is None
    assert NAMING_PATTERN.match("icon-short.png") is None


def test_validate_file_valid_asset(tmp_path):
    content = b"fake png data"
    sha = hashlib.sha256(content).hexdigest()
    f = tmp_path / f"iconLogo-{sha}.png"
    f.write_bytes(content)
    errors = validate_file(f, tmp_path)
    assert errors == []


def test_validate_file_hash_mismatch(tmp_path):
    f = tmp_path / ("testFile-" + "0" * 64 + ".png")
    f.write_bytes(b"some data")
    errors = validate_file(f, tmp_path)
    assert any("hash" in e.lower() or "mismatch" in e.lower() for e in errors)


def test_find_asset_files_finds_images(tmp_path):
    (tmp_path / "icon.png").write_bytes(b"\x89PNG")
    (tmp_path / "readme.md").write_text("# hi\n", encoding="utf-8")
    files = find_asset_files([tmp_path])
    names = {f.name for f in files}
    assert "icon.png" in names
    assert "readme.md" not in names


def test_validate_empty_directory(tmp_path):
    errors = validate(directories=[tmp_path])
    assert errors == []


def test_asset_extensions_include_common_formats():
    assert ".png" in ASSET_EXTENSIONS
    assert ".jpg" in ASSET_EXTENSIONS
    assert ".svg" in ASSET_EXTENSIONS
    assert ".gif" in ASSET_EXTENSIONS


def test_validate_file_invalid_name(tmp_path):
    """A file that doesn't match the naming pattern returns an error."""
    f = tmp_path / "bad_name.png"
    f.write_bytes(b"\x89PNG")
    errors = validate_file(f, tmp_path)
    assert len(errors) == 1
    assert "does not match pattern" in errors[0]


def test_validate_with_errors(tmp_path):
    """validate() returns errors for invalid asset files."""
    import scripts.ui.validate_assets as va_mod

    f = tmp_path / "bad.png"
    f.write_bytes(b"\x89PNG")
    # Use tmp_path as root so relative_to works
    old_root = va_mod.ROOT
    va_mod.ROOT = tmp_path
    try:
        errors = validate(directories=[tmp_path])
    finally:
        va_mod.ROOT = old_root
    assert len(errors) >= 1


def test_main_returns_zero_no_assets(tmp_path, monkeypatch):
    """main() returns 0 with no asset files."""
    import scripts.ui.validate_assets as va_mod

    monkeypatch.setattr(va_mod, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["validate_assets.py"])
    result = va_mod.main()
    assert result == 0


def test_main_returns_one_on_errors(tmp_path, monkeypatch):
    """main() returns 1 when validation finds errors."""
    import scripts.ui.validate_assets as va_mod

    (tmp_path / "bad.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(va_mod, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["validate_assets.py", str(tmp_path)])
    result = va_mod.main()
    assert result == 1


def test_find_asset_files_nonexistent_directory(tmp_path):
    """find_asset_files skips directories that don't exist."""
    files = find_asset_files([tmp_path / "nope"])
    assert files == []
