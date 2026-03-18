# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.server.registry."""

from __future__ import annotations

import json

import pytest

from mcp.protocol.errors import INVALID_PARAMS, METHOD_NOT_FOUND, McpError
from mcp.protocol.types import PromptArgument, PromptMessage
from mcp.server.registry import Registry


class TestToolRegistration:
    def test_add_tool(self, registry: Registry) -> None:
        def add(a: int, b: int) -> str:
            return json.dumps({"result": a + b})

        tool = registry.add_tool("add", "Add numbers", add)
        assert tool.name == "add"
        assert tool.description == "Add numbers"
        assert tool.inputSchema.required == ["a", "b"]

    def test_add_tool_with_defaults(self, registry: Registry) -> None:
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        tool = registry.add_tool("greet", "Greet", greet)
        assert "name" in tool.inputSchema.required
        assert "greeting" not in tool.inputSchema.required

    def test_list_tools(self, registry: Registry) -> None:
        registry.add_tool("a", "A", lambda: "a")
        registry.add_tool("b", "B", lambda: "b")
        tools = registry.list_tools()
        assert len(tools) == 2
        names = {t["name"] for t in tools}
        assert names == {"a", "b"}

    def test_call_tool_success(self, registry: Registry) -> None:
        def multiply(x: int, y: int) -> str:
            return json.dumps({"result": x * y})

        registry.add_tool("multiply", "Multiply", multiply)
        result = registry.call_tool("multiply", {"x": 3, "y": 4})
        assert json.loads(result) == {"result": 12}

    def test_call_tool_unknown_raises(self, registry: Registry) -> None:
        with pytest.raises(McpError) as exc_info:
            registry.call_tool("nonexistent", {})
        assert exc_info.value.code == METHOD_NOT_FOUND

    def test_call_tool_bad_args_raises(self, registry: Registry) -> None:
        def add(a: int, b: int) -> str:
            return str(a + b)

        registry.add_tool("add", "Add", add)
        with pytest.raises(McpError) as exc_info:
            registry.call_tool("add", {"wrong": 1})
        assert exc_info.value.code == INVALID_PARAMS


class TestResourceRegistration:
    def test_add_resource(self, registry: Registry) -> None:
        resource = registry.add_resource(
            "test://data",
            "data",
            "Test data",
            "application/json",
            lambda: "{}",
        )
        assert resource.uri == "test://data"
        assert resource.mimeType == "application/json"

    def test_list_resources(self, registry: Registry) -> None:
        registry.add_resource("a://1", "a", "", "text/plain", lambda: "a")
        registry.add_resource("b://2", "b", "", "text/plain", lambda: "b")
        resources = registry.list_resources()
        assert len(resources) == 2

    def test_read_resource_success(self, registry: Registry) -> None:
        registry.add_resource(
            "test://x",
            "x",
            "",
            "text/plain",
            lambda: "hello",
        )
        content, mime = registry.read_resource("test://x")
        assert content == "hello"
        assert mime == "text/plain"

    def test_read_resource_unknown_raises(self, registry: Registry) -> None:
        with pytest.raises(McpError) as exc_info:
            registry.read_resource("unknown://x")
        assert exc_info.value.code == METHOD_NOT_FOUND


class TestPromptRegistration:
    def test_add_prompt(self, registry: Registry) -> None:
        args = [PromptArgument(name="name", required=True)]
        prompt = registry.add_prompt("greet", "Greet", args, lambda name: f"Hi {name}")
        assert prompt.name == "greet"
        assert len(prompt.arguments) == 1

    def test_list_prompts(self, registry: Registry) -> None:
        registry.add_prompt("a", "A", [], lambda: "a")
        registry.add_prompt("b", "B", [], lambda: "b")
        prompts = registry.list_prompts()
        assert len(prompts) == 2

    def test_get_prompt_returns_string(self, registry: Registry) -> None:
        registry.add_prompt("greet", "Greet", [], lambda name: f"Hi {name}")
        messages = registry.get_prompt("greet", {"name": "World"})
        assert len(messages) == 1
        assert isinstance(messages[0], PromptMessage)
        assert messages[0].text == "Hi World"

    def test_get_prompt_returns_list(self, registry: Registry) -> None:
        def multi() -> list:
            return [
                PromptMessage(role="user", content_type="text", text="Q"),
                PromptMessage(role="assistant", content_type="text", text="A"),
            ]

        registry.add_prompt("multi", "Multi", [], multi)
        messages = registry.get_prompt("multi", {})
        assert len(messages) == 2

    def test_get_prompt_unknown_raises(self, registry: Registry) -> None:
        with pytest.raises(McpError) as exc_info:
            registry.get_prompt("nonexistent", {})
        assert exc_info.value.code == METHOD_NOT_FOUND

    def test_get_prompt_bad_args_raises(self, registry: Registry) -> None:
        registry.add_prompt(
            "strict",
            "Strict",
            [],
            lambda required_arg: f"Got {required_arg}",
        )
        with pytest.raises(McpError) as exc_info:
            registry.get_prompt("strict", {})
        assert exc_info.value.code == INVALID_PARAMS


class TestCapabilityFlags:
    def test_empty_registry_has_nothing(self, registry: Registry) -> None:
        assert registry.has_tools is False
        assert registry.has_resources is False
        assert registry.has_prompts is False

    def test_has_tools_true_after_add(self, registry: Registry) -> None:
        registry.add_tool("t", "T", lambda: "t")
        assert registry.has_tools is True

    def test_has_resources_true_after_add(self, registry: Registry) -> None:
        registry.add_resource("u://x", "x", "", "text/plain", lambda: "")
        assert registry.has_resources is True

    def test_has_prompts_true_after_add(self, registry: Registry) -> None:
        registry.add_prompt("p", "P", [], lambda: "p")
        assert registry.has_prompts is True
