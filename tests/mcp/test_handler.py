# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.server.handler — JSON-RPC method dispatch."""

from __future__ import annotations

import json

import pytest

from mcp.protocol.errors import INVALID_PARAMS, METHOD_NOT_FOUND, McpError
from mcp.protocol.types import PROTOCOL_VERSION
from mcp.server.handler import Handler


class TestInitialize:
    def test_returns_protocol_version(self, handler: Handler) -> None:
        result = handler.handle("initialize", {})
        assert result["protocolVersion"] == PROTOCOL_VERSION

    def test_returns_server_info(self, handler: Handler) -> None:
        result = handler.handle("initialize", {})
        assert result["serverInfo"]["name"] == "test-server"
        assert result["serverInfo"]["version"] == "0.0.1"

    def test_reports_capabilities(self, handler: Handler) -> None:
        result = handler.handle("initialize", {})
        caps = result["capabilities"]
        assert "tools" in caps
        assert "resources" in caps
        assert "prompts" in caps


class TestPing:
    def test_returns_empty_dict(self, handler: Handler) -> None:
        result = handler.handle("ping", {})
        assert result == {}


class TestToolsList:
    def test_lists_registered_tools(self, handler: Handler) -> None:
        result = handler.handle("tools/list", {})
        names = {t["name"] for t in result["tools"]}
        assert "add" in names
        assert "echo" in names

    def test_tool_has_input_schema(self, handler: Handler) -> None:
        result = handler.handle("tools/list", {})
        add_tool = next(t for t in result["tools"] if t["name"] == "add")
        assert "inputSchema" in add_tool
        assert "a" in add_tool["inputSchema"]["properties"]


class TestToolsCall:
    def test_call_success(self, handler: Handler) -> None:
        result = handler.handle("tools/call", {"name": "add", "arguments": {"a": 2, "b": 3}})
        assert result["isError"] is False
        text = result["content"][0]["text"]
        assert json.loads(text) == {"result": 5}

    def test_call_echo(self, handler: Handler) -> None:
        result = handler.handle("tools/call", {"name": "echo", "arguments": {"text": "hi"}})
        assert result["content"][0]["text"] == "hi"

    def test_missing_name_raises(self, handler: Handler) -> None:
        with pytest.raises(McpError) as exc_info:
            handler.handle("tools/call", {})
        assert exc_info.value.code == INVALID_PARAMS

    def test_unknown_tool_raises(self, handler: Handler) -> None:
        with pytest.raises(McpError) as exc_info:
            handler.handle("tools/call", {"name": "nonexistent"})
        assert exc_info.value.code == METHOD_NOT_FOUND


class TestResourcesList:
    def test_lists_resources(self, handler: Handler) -> None:
        result = handler.handle("resources/list", {})
        uris = {r["uri"] for r in result["resources"]}
        assert "test://data" in uris
        assert "test://readme" in uris


class TestResourcesRead:
    def test_read_success(self, handler: Handler) -> None:
        result = handler.handle("resources/read", {"uri": "test://data"})
        content = result["contents"][0]
        assert content["uri"] == "test://data"
        assert content["text"] == '{"key": "value"}'

    def test_read_mime_type(self, handler: Handler) -> None:
        result = handler.handle("resources/read", {"uri": "test://readme"})
        content = result["contents"][0]
        assert content["mimeType"] == "text/markdown"

    def test_missing_uri_raises(self, handler: Handler) -> None:
        with pytest.raises(McpError) as exc_info:
            handler.handle("resources/read", {})
        assert exc_info.value.code == INVALID_PARAMS


class TestPromptsList:
    def test_lists_prompts(self, handler: Handler) -> None:
        result = handler.handle("prompts/list", {})
        names = {p["name"] for p in result["prompts"]}
        assert "greet" in names
        assert "summarize" in names


class TestPromptsGet:
    def test_get_prompt(self, handler: Handler) -> None:
        result = handler.handle("prompts/get", {"name": "greet", "arguments": {"name": "Alice"}})
        assert len(result["messages"]) == 1
        assert "Alice" in result["messages"][0]["content"]["text"]

    def test_missing_name_raises(self, handler: Handler) -> None:
        with pytest.raises(McpError) as exc_info:
            handler.handle("prompts/get", {})
        assert exc_info.value.code == INVALID_PARAMS


class TestUnknownMethod:
    def test_raises_method_not_found(self, handler: Handler) -> None:
        with pytest.raises(McpError) as exc_info:
            handler.handle("unknown/method", {})
        assert exc_info.value.code == METHOD_NOT_FOUND


class TestNotifications:
    def test_initialized_notification(self, handler: Handler) -> None:
        handler.handle_notification("notifications/initialized", {})
        assert handler._initialized is True

    def test_unknown_notification_ignored(self, handler: Handler) -> None:
        handler.handle_notification("notifications/unknown", {})
