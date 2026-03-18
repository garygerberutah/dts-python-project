# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.transport.http — Streamable HTTP transport."""

from __future__ import annotations

import io
import json

import pytest

from mcp import McpServer
from mcp.transport.http import HttpTransport, _McpHttpHandler


@pytest.fixture()
def http_server() -> McpServer:
    """Server with a tool for HTTP testing."""
    srv = McpServer(name="http-test", version="0.1.0")

    @srv.tool(description="Echo")
    def echo(text: str) -> str:
        return text

    return srv


def _make_handler(server: McpServer, method: str, path: str, body: str = "") -> _McpHttpHandler:
    """Create a mock HTTP handler instance for testing."""
    handler_class = type(
        "_TestHandler",
        (_McpHttpHandler,),
        {"mcp_handler": server.handler},
    )

    # Mock the request
    body_bytes = body.encode("utf-8")
    rfile = io.BytesIO(body_bytes)

    # Mock wfile
    wfile = io.BytesIO()

    # Create handler instance without calling __init__ (which does handling)
    handler = object.__new__(handler_class)
    handler.mcp_handler = server.handler
    handler.rfile = rfile
    handler.wfile = wfile
    handler.path = path
    handler.command = method
    handler.headers = {"Content-Length": str(len(body_bytes))}
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.client_address = ("127.0.0.1", 9999)
    handler.request_version = "HTTP/1.1"
    handler.close_connection = True

    # Collect response data
    handler._response_code = None
    handler._response_headers = {}
    handler._response_body = b""

    _orig_send_response = handler_class.send_response
    _orig_send_header = handler_class.send_header
    _orig_end_headers = handler_class.end_headers

    def mock_send_response(self, code, message=None):
        self._response_code = code

    def mock_send_header(self, keyword, value):
        self._response_headers[keyword] = value

    def mock_end_headers(self):
        pass

    handler.send_response = mock_send_response.__get__(handler)
    handler.send_header = mock_send_header.__get__(handler)
    handler.end_headers = mock_end_headers.__get__(handler)

    return handler


class TestHttpPost:
    def test_ping(self, http_server: McpServer) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        handler = _make_handler(http_server, "POST", "/mcp", body)
        handler.do_POST()
        written = handler.wfile.getvalue()
        msg = json.loads(written)
        assert msg["result"] == {}

    def test_tools_call(self, http_server: McpServer) -> None:
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"text": "hi"}},
            }
        )
        handler = _make_handler(http_server, "POST", "/mcp", body)
        handler.do_POST()
        written = handler.wfile.getvalue()
        msg = json.loads(written)
        assert msg["result"]["content"][0]["text"] == "hi"

    def test_wrong_path_returns_404(self, http_server: McpServer) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        handler = _make_handler(http_server, "POST", "/wrong", body)
        handler.do_POST()
        assert handler._response_code == 404

    def test_empty_body_returns_400(self, http_server: McpServer) -> None:
        handler = _make_handler(http_server, "POST", "/mcp", "")
        handler.headers = {"Content-Length": "0"}
        handler.do_POST()
        assert handler._response_code == 400

    def test_notification_returns_202(self, http_server: McpServer) -> None:
        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        handler = _make_handler(http_server, "POST", "/mcp", body)
        handler.do_POST()
        assert handler._response_code == 202


class TestHttpGet:
    def test_mcp_endpoint_returns_info(self, http_server: McpServer) -> None:
        handler = _make_handler(http_server, "GET", "/mcp")
        handler.do_GET()
        written = handler.wfile.getvalue()
        msg = json.loads(written)
        assert msg["status"] == "ok"

    def test_wrong_path_returns_404(self, http_server: McpServer) -> None:
        handler = _make_handler(http_server, "GET", "/wrong")
        handler.do_GET()
        assert handler._response_code == 404


class TestHttpOptions:
    def test_returns_204(self, http_server: McpServer) -> None:
        handler = _make_handler(http_server, "OPTIONS", "/mcp")
        handler.headers = {"Content-Length": "0", "Origin": "http://localhost"}
        handler.do_OPTIONS()
        assert handler._response_code == 204


class TestHttpTransportInit:
    def test_default_host_port(self, http_server: McpServer) -> None:
        transport = HttpTransport(http_server.handler)
        assert transport._host == "127.0.0.1"
        assert transport._port == 3000

    def test_custom_host_port(self, http_server: McpServer) -> None:
        transport = HttpTransport(http_server.handler, host="0.0.0.0", port=8080)
        assert transport._host == "0.0.0.0"
        assert transport._port == 8080
