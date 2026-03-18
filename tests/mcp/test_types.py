# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.protocol.types."""

from __future__ import annotations

import pytest

from mcp.protocol.types import (
    PROTOCOL_VERSION,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    Tool,
    ToolInputSchema,
)


class TestProtocolVersion:
    def test_version_format(self) -> None:
        assert PROTOCOL_VERSION == "2024-11-05"


class TestToolInputSchema:
    def test_default_values(self) -> None:
        schema = ToolInputSchema()
        assert schema.type == "object"
        assert schema.properties == {}
        assert schema.required == []

    def test_to_dict(self) -> None:
        schema = ToolInputSchema(
            properties={"a": {"type": "integer"}},
            required=["a"],
        )
        d = schema.to_dict()
        assert d == {
            "type": "object",
            "properties": {"a": {"type": "integer"}},
            "required": ["a"],
        }

    def test_frozen(self) -> None:
        schema = ToolInputSchema()
        with pytest.raises(AttributeError):
            schema.type = "array"  # type: ignore[misc]


class TestTool:
    def test_to_dict(self) -> None:
        tool = Tool(
            name="add",
            description="Add numbers",
            inputSchema=ToolInputSchema(
                properties={"a": {"type": "integer"}, "b": {"type": "integer"}},
                required=["a", "b"],
            ),
        )
        d = tool.to_dict()
        assert d["name"] == "add"
        assert d["description"] == "Add numbers"
        assert "inputSchema" in d
        assert d["inputSchema"]["required"] == ["a", "b"]


class TestResource:
    def test_to_dict_minimal(self) -> None:
        r = Resource(uri="file://x", name="x")
        d = r.to_dict()
        assert d["uri"] == "file://x"
        assert d["name"] == "x"

    def test_to_dict_full(self) -> None:
        r = Resource(
            uri="file://x",
            name="X File",
            description="Test",
            mimeType="application/json",
        )
        d = r.to_dict()
        assert d["description"] == "Test"
        assert d["mimeType"] == "application/json"


class TestPromptArgument:
    def test_to_dict_minimal(self) -> None:
        a = PromptArgument(name="topic")
        d = a.to_dict()
        assert d == {"name": "topic"}

    def test_to_dict_full(self) -> None:
        a = PromptArgument(name="topic", description="The topic", required=True)
        d = a.to_dict()
        assert d["name"] == "topic"
        assert d["description"] == "The topic"
        assert d["required"] is True


class TestPrompt:
    def test_to_dict_no_args(self) -> None:
        p = Prompt(name="simple")
        d = p.to_dict()
        assert d == {"name": "simple"}

    def test_to_dict_with_args(self) -> None:
        p = Prompt(
            name="greet",
            description="Greet someone",
            arguments=[
                PromptArgument(name="name", required=True),
            ],
        )
        d = p.to_dict()
        assert d["name"] == "greet"
        assert d["description"] == "Greet someone"
        assert len(d["arguments"]) == 1


class TestPromptMessage:
    def test_to_dict(self) -> None:
        m = PromptMessage(role="assistant", content_type="text", text="Hello")
        d = m.to_dict()
        assert d == {
            "role": "assistant",
            "content": {"type": "text", "text": "Hello"},
        }
