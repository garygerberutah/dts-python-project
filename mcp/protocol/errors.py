# Copyright 2026 by GuidoGerb Publishing, LLC
"""JSON-RPC 2.0 and MCP standard error codes."""

from __future__ import annotations

# JSON-RPC 2.0 standard error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class McpError(Exception):
    """Error with a JSON-RPC error code and user-safe message."""

    def __init__(self, code: int, message: str, data: object = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict:
        result: dict = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result
