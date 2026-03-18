"""Tests for scripts/ui/serve.py — local dev server.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from unittest.mock import patch

import scripts.ui.serve as serve_mod


def test_cors_handler_guess_type_wasm():
    """WASM files return application/wasm mime type."""
    handler = serve_mod._CORSHTTPRequestHandler.__new__(
        serve_mod._CORSHTTPRequestHandler
    )
    mime = handler.guess_type("module.wasm")
    assert mime == "application/wasm"


def test_cors_handler_guess_type_js():
    """JS files return a JavaScript mime type."""
    handler = serve_mod._CORSHTTPRequestHandler.__new__(
        serve_mod._CORSHTTPRequestHandler
    )
    mime = handler.guess_type("app.js")
    assert "javascript" in mime or "ecmascript" in mime.lower()


def test_default_port():
    """DEFAULT_PORT is 8080."""
    assert serve_mod.DEFAULT_PORT == 8080


def test_serve_exits_if_no_dist(tmp_path):
    """serve() exits with code 1 when dist/ does not exist."""
    import pytest

    with patch.object(serve_mod, "DIST_DIR", tmp_path / "missing"):
        with pytest.raises(SystemExit) as exc_info:
            serve_mod.serve()
        assert exc_info.value.code == 1
