# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.server.base — McpServer decorator API."""

from __future__ import annotations

import pytest

from mcp import McpServer
from mcp.protocol.types import PromptArgument


class TestToolDecorator:
    def test_register_by_name(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.tool(name="my_tool", description="Does stuff")
        def fn(x: str) -> str:
            return x

        tools = srv.registry.list_tools()
        assert any(t["name"] == "my_tool" for t in tools)

    def test_register_uses_function_name(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.tool(description="Echo")
        def echo(text: str) -> str:
            return text

        tools = srv.registry.list_tools()
        assert any(t["name"] == "echo" for t in tools)

    def test_decorator_returns_original_function(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.tool(description="Add")
        def add(a: int, b: int) -> int:
            return a + b

        assert add(1, 2) == 3

    def test_description_from_docstring(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.tool()
        def documented(x: str) -> str:
            """This is the description."""
            return x

        tools = srv.registry.list_tools()
        tool = next(t for t in tools if t["name"] == "documented")
        assert tool["description"] == "This is the description."


class TestResourceDecorator:
    def test_register_resource(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.resource(uri="test://x", description="Test")
        def x_data() -> str:
            return "{}"

        resources = srv.registry.list_resources()
        assert any(r["uri"] == "test://x" for r in resources)

    def test_mime_type(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.resource(uri="test://j", mime_type="application/json")
        def json_data() -> str:
            return "{}"

        resources = srv.registry.list_resources()
        r = next(x for x in resources if x["uri"] == "test://j")
        assert r["mimeType"] == "application/json"


class TestPromptDecorator:
    def test_register_prompt(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.prompt(description="Say hello")
        def hello(name: str) -> str:
            return f"Hello {name}"

        prompts = srv.registry.list_prompts()
        assert any(p["name"] == "hello" for p in prompts)

    def test_explicit_arguments(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.prompt(
            description="Custom",
            arguments=[PromptArgument(name="topic", required=True)],
        )
        def custom(topic: str) -> str:
            return f"Topic: {topic}"

        prompts = srv.registry.list_prompts()
        p = next(x for x in prompts if x["name"] == "custom")
        assert p["arguments"][0]["name"] == "topic"
        assert p["arguments"][0]["required"] is True

    def test_auto_derived_arguments(self) -> None:
        srv = McpServer(name="t", version="0.1.0")

        @srv.prompt(description="Auto")
        def auto(required_arg: str, optional_arg: str = "default") -> str:
            return f"{required_arg} {optional_arg}"

        prompts = srv.registry.list_prompts()
        p = next(x for x in prompts if x["name"] == "auto")
        arg_names = {a["name"] for a in p["arguments"]}
        assert "required_arg" in arg_names
        assert "optional_arg" in arg_names


class TestServerProperties:
    def test_name_and_version(self) -> None:
        srv = McpServer(name="mysvr", version="2.0.0")
        assert srv.name == "mysvr"
        assert srv.version == "2.0.0"

    def test_handler_accessible(self) -> None:
        srv = McpServer(name="t", version="0.1.0")
        assert srv.handler is not None

    def test_registry_accessible(self) -> None:
        srv = McpServer(name="t", version="0.1.0")
        assert srv.registry is not None


class TestRunTransport:
    def test_unknown_transport_raises(self) -> None:
        srv = McpServer(name="t", version="0.1.0")
        with pytest.raises(ValueError, match="unknown"):
            srv.run(transport="unknown")
