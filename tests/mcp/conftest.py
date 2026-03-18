# Copyright 2026 by GuidoGerb Publishing, LLC
"""Shared fixtures for MCP tests."""

from __future__ import annotations

import json

import pytest

from mcp import McpServer
from mcp.server.handler import Handler
from mcp.server.registry import Registry
from mcp.transport.stdio import StdioTransport


@pytest.fixture()
def registry() -> Registry:
    """A fresh empty registry."""
    return Registry()


@pytest.fixture()
def sample_server() -> McpServer:
    """An McpServer with a few tools, resources, and prompts registered."""
    srv = McpServer(name="test-server", version="0.0.1")

    @srv.tool(description="Add two integers")
    def add(a: int, b: int) -> str:
        return json.dumps({"result": a + b})

    @srv.tool(description="Echo text")
    def echo(text: str) -> str:
        return text

    @srv.resource(uri="test://data", description="Test data")
    def test_data() -> str:
        return '{"key": "value"}'

    @srv.resource(
        uri="test://readme",
        description="Readme",
        mime_type="text/markdown",
    )
    def readme() -> str:
        return "# Hello"

    @srv.prompt(description="Greet someone")
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    @srv.prompt(description="Summarize a topic")
    def summarize(topic: str, audience: str = "general") -> str:
        return f"Summarize {topic} for {audience}"

    return srv


@pytest.fixture()
def handler(sample_server: McpServer) -> Handler:
    """Handler wired to the sample server."""
    return sample_server.handler


@pytest.fixture()
def stdio(handler: Handler) -> StdioTransport:
    """StdioTransport wired to the sample handler."""
    return StdioTransport(handler)
