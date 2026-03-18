# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.protocol.jsonrpc."""

from __future__ import annotations

import json

import pytest

from mcp.protocol.errors import INVALID_REQUEST, PARSE_ERROR, McpError
from mcp.protocol.jsonrpc import (
    parse_message,
    serialize_error,
    serialize_notification,
    serialize_response,
)


class TestParseMessage:
    def test_valid_request(self) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        msg = parse_message(raw)
        assert msg["jsonrpc"] == "2.0"
        assert msg["id"] == 1
        assert msg["method"] == "ping"

    def test_valid_notification(self) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        msg = parse_message(raw)
        assert "id" not in msg
        assert msg["method"] == "notifications/initialized"

    def test_valid_response(self) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
        msg = parse_message(raw)
        assert msg["result"] == {"ok": True}

    def test_bytes_input(self) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode()
        msg = parse_message(raw)
        assert msg["method"] == "ping"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(McpError, match="Empty message"):
            parse_message("")

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(McpError) as exc_info:
            parse_message("{bad json")
        assert exc_info.value.code == PARSE_ERROR

    def test_non_object_raises(self) -> None:
        with pytest.raises(McpError) as exc_info:
            parse_message("[1, 2, 3]")
        assert exc_info.value.code == INVALID_REQUEST

    def test_missing_jsonrpc_raises(self) -> None:
        with pytest.raises(McpError) as exc_info:
            parse_message('{"id": 1, "method": "ping"}')
        assert exc_info.value.code == INVALID_REQUEST

    def test_wrong_jsonrpc_version_raises(self) -> None:
        with pytest.raises(McpError) as exc_info:
            parse_message('{"jsonrpc": "1.0", "id": 1, "method": "ping"}')
        assert exc_info.value.code == INVALID_REQUEST

    def test_missing_method_and_result_raises(self) -> None:
        with pytest.raises(McpError) as exc_info:
            parse_message('{"jsonrpc": "2.0", "id": 1}')
        assert exc_info.value.code == INVALID_REQUEST

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(McpError, match="Empty message"):
            parse_message("   \n  ")


class TestSerializeResponse:
    def test_simple(self) -> None:
        s = serialize_response(1, {"ok": True})
        msg = json.loads(s)
        assert msg["jsonrpc"] == "2.0"
        assert msg["id"] == 1
        assert msg["result"] == {"ok": True}

    def test_null_id(self) -> None:
        s = serialize_response(None, {})
        msg = json.loads(s)
        assert msg["id"] is None


class TestSerializeError:
    def test_error_response(self) -> None:
        err = McpError(-32600, "Bad request")
        s = serialize_error(1, err)
        msg = json.loads(s)
        assert msg["error"]["code"] == -32600
        assert msg["error"]["message"] == "Bad request"
        assert msg["id"] == 1


class TestSerializeNotification:
    def test_without_params(self) -> None:
        s = serialize_notification("ping")
        msg = json.loads(s)
        assert msg["jsonrpc"] == "2.0"
        assert msg["method"] == "ping"
        assert "id" not in msg
        assert "params" not in msg

    def test_with_params(self) -> None:
        s = serialize_notification("update", {"key": "value"})
        msg = json.loads(s)
        assert msg["params"] == {"key": "value"}
