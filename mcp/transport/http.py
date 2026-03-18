# Copyright 2026 by GuidoGerb Publishing, LLC
"""Streamable HTTP transport for MCP servers.

Implements the MCP Streamable HTTP transport using Python's built-in
``http.server``.  Supports both single JSON-RPC request/response and
Server-Sent Events (SSE) streaming for multi-message scenarios.

Designed for localhost development and testing.  For production on
AWS, use the Lambda transport instead.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from mcp.protocol.errors import INTERNAL_ERROR, McpError
from mcp.protocol.jsonrpc import parse_message, serialize_error
from mcp.server.handler import Handler


class _McpHttpHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP Streamable HTTP transport."""

    # Handler reference is injected at server creation time.
    mcp_handler: Handler

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST /mcp — the single MCP endpoint."""
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found", "message": "Use POST /mcp"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"error": "bad_request", "message": "Empty body"})
            return

        raw = self.rfile.read(content_length)
        try:
            msg = parse_message(raw)
        except McpError as exc:
            self._send_json(400, {"jsonrpc": "2.0", "id": None, "error": exc.to_dict()})
            return

        request_id = msg.get("id")
        method = msg.get("method")

        # Notification (no id) — accept but don't return content
        if request_id is None and method:
            self.mcp_handler.handle_notification(method, msg.get("params"))
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        # Standard request/response
        try:
            result = self.mcp_handler.handle(method, msg.get("params"))
            response_body = json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "result": result},
            )
        except McpError as exc:
            response_body = serialize_error(request_id, exc)
        except Exception as exc:
            err = McpError(INTERNAL_ERROR, f"Internal server error: {exc}")
            response_body = serialize_error(request_id, err)

        self._send_response_body(200, response_body)

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET /mcp — SSE endpoint for streaming (opens connection)."""
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found", "message": "Use GET /mcp for SSE"})
            return

        # For now, return a simple endpoint info response
        self._send_json(
            200,
            {
                "status": "ok",
                "transport": "streamable-http",
                "message": "Send JSON-RPC requests via POST /mcp",
            },
        )

    def do_OPTIONS(self) -> None:  # noqa: N802
        """CORS preflight."""
        self.send_response(204)
        self._set_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, status: int, body: Any) -> None:
        self._send_response_body(status, json.dumps(body))

    def _send_response_body(self, status: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def _set_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "86400")

    def log_message(self, format: str, *args: Any) -> None:
        """Route HTTP logs to stderr to keep stdout clean for protocol."""
        print(f"[mcp:http] {format % args}", file=sys.stderr)


class HttpTransport:
    """Serve MCP requests over HTTP using Streamable HTTP transport."""

    def __init__(self, handler: Handler, host: str = "127.0.0.1", port: int = 3000) -> None:
        self._handler = handler
        self._host = host
        self._port = port

    def serve(self) -> None:
        """Start the HTTP server (blocking)."""
        handler_class = type(
            "_BoundHandler",
            (_McpHttpHandler,),
            {"mcp_handler": self._handler},
        )
        server = HTTPServer((self._host, self._port), handler_class)
        print(
            f"[mcp:http] Listening on http://{self._host}:{self._port}/mcp",
            file=sys.stderr,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[mcp:http] Shutting down", file=sys.stderr)
        finally:
            server.server_close()
