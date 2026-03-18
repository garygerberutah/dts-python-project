# Copyright 2026 by GuidoGerb Publishing, LLC
"""Internal registry for tools, resources, and prompts."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from mcp.protocol.errors import INVALID_PARAMS, METHOD_NOT_FOUND, McpError
from mcp.protocol.types import (
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    Tool,
    ToolInputSchema,
)

# Python type → JSON Schema type
_PY_TO_JSON: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _json_type(annotation: Any) -> str:
    """Convert a Python type annotation to a JSON Schema type string."""
    return _PY_TO_JSON.get(annotation, "string")


def _build_input_schema(fn: Callable) -> ToolInputSchema:
    """Derive a JSON Schema from the callable's type hints."""
    sig = inspect.signature(fn)
    hints = {}
    try:
        hints = inspect.get_annotations(fn, eval_str=True)
    except Exception:
        hints = getattr(fn, "__annotations__", {})

    properties: dict[str, dict] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        json_t = _json_type(hints.get(name, str))
        prop: dict[str, str] = {"type": json_t}
        properties[name] = prop
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return ToolInputSchema(properties=properties, required=required)


class Registry:
    """Stores tools, resources, and prompts with their callables."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[Tool, Callable]] = {}
        self._resources: dict[str, tuple[Resource, Callable]] = {}
        self._prompts: dict[str, tuple[Prompt, Callable]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add_tool(self, name: str, description: str, fn: Callable) -> Tool:
        """Register a callable as a tool. Returns the Tool descriptor."""
        schema = _build_input_schema(fn)
        tool = Tool(name=name, description=description, inputSchema=schema)
        self._tools[name] = (tool, fn)
        return tool

    def add_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        fn: Callable,
    ) -> Resource:
        """Register a callable as a resource reader."""
        resource = Resource(uri=uri, name=name, description=description, mimeType=mime_type)
        self._resources[uri] = (resource, fn)
        return resource

    def add_prompt(
        self,
        name: str,
        description: str,
        arguments: list[PromptArgument],
        fn: Callable,
    ) -> Prompt:
        """Register a callable as a prompt template."""
        prompt = Prompt(name=name, description=description, arguments=arguments)
        self._prompts[name] = (prompt, fn)
        return prompt

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_tools(self) -> list[dict]:
        return [t.to_dict() for t, _ in self._tools.values()]

    def list_resources(self) -> list[dict]:
        return [r.to_dict() for r, _ in self._resources.values()]

    def list_prompts(self) -> list[dict]:
        return [p.to_dict() for p, _ in self._prompts.values()]

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------

    def call_tool(self, name: str, arguments: dict) -> Any:
        """Invoke a registered tool. Raises McpError on failure."""
        entry = self._tools.get(name)
        if entry is None:
            raise McpError(METHOD_NOT_FOUND, f"Unknown tool: {name}")
        _, fn = entry
        try:
            return fn(**arguments)
        except TypeError as exc:
            raise McpError(INVALID_PARAMS, f"Invalid arguments for tool '{name}': {exc}") from exc

    def read_resource(self, uri: str) -> tuple[str, str]:
        """Read a resource. Returns (content, mime_type)."""
        entry = self._resources.get(uri)
        if entry is None:
            raise McpError(METHOD_NOT_FOUND, f"Unknown resource: {uri}")
        resource, fn = entry
        content = fn()
        return (content, resource.mimeType)

    def get_prompt(self, name: str, arguments: dict) -> list[PromptMessage]:
        """Render a prompt template. Returns list of PromptMessage."""
        entry = self._prompts.get(name)
        if entry is None:
            raise McpError(METHOD_NOT_FOUND, f"Unknown prompt: {name}")
        _, fn = entry
        try:
            result = fn(**arguments)
        except TypeError as exc:
            raise McpError(INVALID_PARAMS, f"Invalid arguments for prompt '{name}': {exc}") from exc

        if isinstance(result, str):
            return [PromptMessage(role="assistant", content_type="text", text=result)]
        if isinstance(result, list):
            return result
        raise McpError(
            INVALID_PARAMS,
            f"Prompt '{name}' must return str or list[PromptMessage]",
        )

    # ------------------------------------------------------------------
    # Capability flags
    # ------------------------------------------------------------------

    @property
    def has_tools(self) -> bool:
        return bool(self._tools)

    @property
    def has_resources(self) -> bool:
        return bool(self._resources)

    @property
    def has_prompts(self) -> bool:
        return bool(self._prompts)
