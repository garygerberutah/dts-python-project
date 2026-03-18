# Copyright 2026 by GuidoGerb Publishing, LLC
"""stdio transport — reads JSON-RPC messages from stdin, writes to stdout.

This is the standard MCP transport for local tool invocation.
Messages are newline-delimited JSON.
"""

from __future__ import annotations

import sys

from mcp.protocol.errors import INTERNAL_ERROR, McpError
from mcp.protocol.jsonrpc import parse_message, serialize_error, serialize_response
from mcp.server.handler import Handler


class StdioTransport:
    """Serve MCP requests over stdin/stdout.

    Each line on stdin is a JSON-RPC 2.0 message.  Responses are
    written to stdout, one JSON object per line.  Diagnostic output
    goes to stderr only.
    """

    def __init__(self, handler: Handler) -> None:
        self._handler = handler

    def serve(self) -> None:
        """Read from stdin until EOF, dispatching each message."""
        print("[mcp:stdio] Server ready — reading from stdin", file=sys.stderr)

        for raw_line in sys.stdin:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            response = self._process(raw_line)
            if response is not None:
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

        print("[mcp:stdio] stdin closed — shutting down", file=sys.stderr)

    def process_one(self, raw: str) -> str | None:
        """Process a single raw message string. Returns response or None."""
        return self._process(raw)

    def _process(self, raw: str) -> str | None:
        """Parse and dispatch a single message. Returns serialized response or None."""
        try:
            msg = parse_message(raw)
        except McpError as exc:
            return serialize_error(None, exc)

        request_id = msg.get("id")
        method = msg.get("method")

        # Notifications have no id — no response expected
        if request_id is None and method:
            self._handler.handle_notification(method, msg.get("params"))
            return None

        # Request — must have an id
        try:
            result = self._handler.handle(method, msg.get("params"))
            return serialize_response(request_id, result)
        except McpError as exc:
            return serialize_error(request_id, exc)
        except Exception as exc:
            err = McpError(INTERNAL_ERROR, f"Internal server error: {exc}")
            return serialize_error(request_id, err)


def run_stdio(handler: Handler) -> None:
    """Convenience function to start a stdio transport."""
    StdioTransport(handler).serve()
