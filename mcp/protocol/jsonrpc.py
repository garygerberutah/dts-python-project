# Copyright 2026 by GuidoGerb Publishing, LLC
"""JSON-RPC 2.0 message parsing and serialization for MCP."""

from __future__ import annotations

import json
from typing import Any

from mcp.protocol.errors import INVALID_REQUEST, PARSE_ERROR, McpError


def parse_message(raw: str | bytes) -> dict:
    """Parse a JSON-RPC 2.0 message from raw text.

    Returns the parsed dict. Raises ``McpError`` on parse or
    structural failures.
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    raw = raw.strip()
    if not raw:
        raise McpError(PARSE_ERROR, "Empty message")
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise McpError(PARSE_ERROR, f"Invalid JSON: {exc}") from exc
    if not isinstance(msg, dict):
        raise McpError(INVALID_REQUEST, "Message must be a JSON object")
    if msg.get("jsonrpc") != "2.0":
        raise McpError(INVALID_REQUEST, "Missing or invalid 'jsonrpc' field")
    if "method" not in msg and "result" not in msg and "error" not in msg:
        raise McpError(INVALID_REQUEST, "Message must contain 'method', 'result', or 'error'")
    return msg


def serialize_response(request_id: Any, result: Any) -> str:
    """Serialize a JSON-RPC 2.0 success response."""
    return json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "result": result},
        separators=(",", ":"),
    )


def serialize_error(request_id: Any, error: McpError) -> str:
    """Serialize a JSON-RPC 2.0 error response."""
    return json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "error": error.to_dict()},
        separators=(",", ":"),
    )


def serialize_notification(method: str, params: dict | None = None) -> str:
    """Serialize a JSON-RPC 2.0 notification (no id)."""
    msg: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg, separators=(",", ":"))
