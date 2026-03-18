# Copyright 2026 by GuidoGerb Publishing, LLC
"""MCP protocol data types (2024-11-05 specification)."""

from __future__ import annotations

from dataclasses import dataclass, field

PROTOCOL_VERSION = "2024-11-05"


@dataclass(frozen=True)
class ToolInputSchema:
    """JSON Schema describing a tool's input parameters."""

    type: str = "object"
    properties: dict[str, dict] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "properties": dict(self.properties),
            "required": list(self.required),
        }


@dataclass(frozen=True)
class Tool:
    """An MCP tool that can be invoked by the client."""

    name: str
    description: str
    inputSchema: ToolInputSchema

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema.to_dict(),
        }


@dataclass(frozen=True)
class Resource:
    """A readable resource exposed by the server."""

    uri: str
    name: str
    description: str = ""
    mimeType: str = "text/plain"

    def to_dict(self) -> dict:
        result = {"uri": self.uri, "name": self.name}
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        return result


@dataclass(frozen=True)
class PromptArgument:
    """A single argument for a prompt template."""

    name: str
    description: str = ""
    required: bool = False

    def to_dict(self) -> dict:
        result: dict = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = True
        return result


@dataclass(frozen=True)
class Prompt:
    """A prompt template exposed by the server."""

    name: str
    description: str = ""
    arguments: list[PromptArgument] = field(default_factory=list)

    def to_dict(self) -> dict:
        result: dict = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = [a.to_dict() for a in self.arguments]
        return result


@dataclass(frozen=True)
class PromptMessage:
    """A single message in a prompt response."""

    role: str
    content_type: str
    text: str

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": {"type": self.content_type, "text": self.text},
        }
