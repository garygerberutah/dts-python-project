# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.deploy — Lambda packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path

from mcp.deploy import package_lambda


class TestPackageLambda:
    def test_creates_zip(self, tmp_path: Path) -> None:
        output = tmp_path / "test.zip"
        result = package_lambda(output_path=output)
        assert result == output
        assert output.exists()

    def test_zip_contains_mcp_package(self, tmp_path: Path) -> None:
        output = tmp_path / "test.zip"
        package_lambda(output_path=output)
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("mcp/__init__.py" in n for n in names)
            assert any("mcp/protocol/types.py" in n for n in names)
            assert any("mcp/server/base.py" in n for n in names)
            assert any("mcp/transport/aws_lambda.py" in n for n in names)

    def test_zip_contains_server_modules(self, tmp_path: Path) -> None:
        output = tmp_path / "test.zip"
        package_lambda(output_path=output)
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("mcp/servers/example.py" in n for n in names)
            assert any("mcp/servers/example_lambda.py" in n for n in names)

    def test_zip_is_valid(self, tmp_path: Path) -> None:
        output = tmp_path / "test.zip"
        package_lambda(output_path=output)
        assert zipfile.is_zipfile(output)

    def test_output_dir_created(self, tmp_path: Path) -> None:
        output = tmp_path / "deep" / "nested" / "test.zip"
        package_lambda(output_path=output)
        assert output.exists()
