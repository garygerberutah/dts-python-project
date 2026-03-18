# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.protocol.errors."""

from __future__ import annotations

from mcp.protocol.errors import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    McpError,
)


class TestErrorCodes:
    def test_parse_error(self) -> None:
        assert PARSE_ERROR == -32700

    def test_invalid_request(self) -> None:
        assert INVALID_REQUEST == -32600

    def test_method_not_found(self) -> None:
        assert METHOD_NOT_FOUND == -32601

    def test_invalid_params(self) -> None:
        assert INVALID_PARAMS == -32602

    def test_internal_error(self) -> None:
        assert INTERNAL_ERROR == -32603


class TestMcpError:
    def test_basic(self) -> None:
        err = McpError(-32600, "Bad request")
        assert err.code == -32600
        assert err.message == "Bad request"
        assert str(err) == "Bad request"
        assert err.data is None

    def test_with_data(self) -> None:
        err = McpError(-32602, "Invalid", data={"field": "a"})
        assert err.data == {"field": "a"}

    def test_to_dict_minimal(self) -> None:
        err = McpError(-32600, "Bad")
        d = err.to_dict()
        assert d == {"code": -32600, "message": "Bad"}

    def test_to_dict_with_data(self) -> None:
        err = McpError(-32600, "Bad", data="extra")
        d = err.to_dict()
        assert d == {"code": -32600, "message": "Bad", "data": "extra"}

    def test_is_exception(self) -> None:
        err = McpError(-32600, "Bad")
        assert isinstance(err, Exception)
