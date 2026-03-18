# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.transport.stdio — stdin/stdout transport."""

from __future__ import annotations

import json

from mcp.protocol.errors import PARSE_ERROR
from mcp.transport.stdio import StdioTransport


class TestStdioProcessOne:
    """Test the process_one method which doesn't require actual stdin."""

    def test_valid_request(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        response = stdio.process_one(raw)
        assert response is not None
        msg = json.loads(response)
        assert msg["id"] == 1
        assert msg["result"] == {}

    def test_initialize(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert msg["result"]["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in msg["result"]

    def test_tools_list(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        response = stdio.process_one(raw)
        msg = json.loads(response)
        tools = msg["result"]["tools"]
        assert any(t["name"] == "add" for t in tools)

    def test_tools_call(self, stdio: StdioTransport) -> None:
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "add", "arguments": {"a": 10, "b": 20}},
            }
        )
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert msg["result"]["isError"] is False
        text = msg["result"]["content"][0]["text"]
        assert json.loads(text) == {"result": 30}

    def test_resources_list(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "resources/list"})
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert "resources" in msg["result"]

    def test_resources_read(self, stdio: StdioTransport) -> None:
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {"uri": "test://data"},
            }
        )
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert msg["result"]["contents"][0]["uri"] == "test://data"

    def test_prompts_list(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 6, "method": "prompts/list"})
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert "prompts" in msg["result"]

    def test_prompts_get(self, stdio: StdioTransport) -> None:
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "prompts/get",
                "params": {"name": "greet", "arguments": {"name": "World"}},
            }
        )
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert "World" in msg["result"]["messages"][0]["content"]["text"]

    def test_notification_returns_none(self, stdio: StdioTransport) -> None:
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
        )
        response = stdio.process_one(raw)
        assert response is None

    def test_invalid_json_returns_error(self, stdio: StdioTransport) -> None:
        response = stdio.process_one("{bad json}")
        assert response is not None
        msg = json.loads(response)
        assert msg["error"]["code"] == PARSE_ERROR

    def test_unknown_method_returns_error(self, stdio: StdioTransport) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "unknown/xyz"})
        response = stdio.process_one(raw)
        msg = json.loads(response)
        assert "error" in msg
        assert msg["error"]["code"] == -32601
