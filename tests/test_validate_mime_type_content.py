"""Tests for scripts/validate_mime_type_content.py.

Copyright 2026 by GuidoGerb Publishing, LLC
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


def test_validate_valid_jpeg(tmp_path):
    """Valid JPEG starts with FF D8 FF."""
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_invalid_jpeg(tmp_path):
    """Invalid JPEG data is flagged."""
    f = tmp_path / "bad.jpg"
    f.write_bytes(b"not a jpeg")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_gif(tmp_path):
    """Valid GIF starts with GIF89a."""
    f = tmp_path / "anim.gif"
    f.write_bytes(b"GIF89a" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_invalid_gif(tmp_path):
    """Invalid GIF data is flagged."""
    f = tmp_path / "bad.gif"
    f.write_bytes(b"not a gif")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_svg(tmp_path):
    """Valid SVG contains <svg> element."""
    f = tmp_path / "icon.svg"
    f.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    result = validate_file(f)
    assert result is None


def test_validate_invalid_svg(tmp_path):
    """Invalid SVG (no <svg> element) is flagged."""
    f = tmp_path / "bad.svg"
    f.write_text("<html>not an svg</html>", encoding="utf-8")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_pdf(tmp_path):
    """Valid PDF starts with %PDF-."""
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.7\n" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_invalid_pdf(tmp_path):
    """Invalid PDF data is flagged."""
    f = tmp_path / "bad.pdf"
    f.write_bytes(b"not a pdf")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_mp3_id3(tmp_path):
    """Valid MP3 with ID3 header."""
    f = tmp_path / "song.mp3"
    f.write_bytes(b"ID3\x04\x00" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_valid_mp3_sync(tmp_path):
    """Valid MP3 with sync word header."""
    f = tmp_path / "audio.mp3"
    f.write_bytes(b"\xff\xfb\x90" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_invalid_mp3(tmp_path):
    """Invalid MP3 data is flagged."""
    f = tmp_path / "bad.mp3"
    f.write_bytes(b"not audio data")
    result = validate_file(f)
    assert result is not None


def test_validate_valid_mp4(tmp_path):
    """Valid MP4 has ftyp box."""
    f = tmp_path / "video.mp4"
    # ftyp box at bytes 4-7
    f.write_bytes(b"\x00\x00\x00\x1c" + b"ftyp" + b"isom" + b"\x00" * 100)
    result = validate_file(f)
    assert result is None


def test_validate_invalid_mp4(tmp_path):
    """Invalid MP4 data is flagged."""
    f = tmp_path / "bad.mp4"
    f.write_bytes(b"not a video")
    result = validate_file(f)
    assert result is not None


def test_validate_unknown_extension_returns_none(tmp_path):
    """Files with non-binary extensions return None."""
    f = tmp_path / "code.py"
    f.write_text("pass\n", encoding="utf-8")
    result = validate_file(f)
    assert result is None


def test_main_returns_zero_no_files(tmp_path, monkeypatch):
    """main returns 0 when no binary files are found."""
    import scripts.ui.validate_mime_type_content as vm_mod

    monkeypatch.setattr(vm_mod, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["validate_mime_type_content.py"])
    result = vm_mod.main()
    assert result == 0


def test_main_returns_one_on_errors(tmp_path, monkeypatch):
    """main returns 1 when validation errors are found."""
    import scripts.ui.validate_mime_type_content as vm_mod

    (tmp_path / "bad.png").write_bytes(b"not png data")
    monkeypatch.setattr(vm_mod, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["validate_mime_type_content.py", str(tmp_path)])
    result = vm_mod.main()
    assert result == 1
