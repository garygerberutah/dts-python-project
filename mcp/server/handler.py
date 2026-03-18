# Copyright 2026 by GuidoGerb Publishing, LLC
"""JSON-RPC method dispatcher for MCP protocol methods."""

from __future__ import annotations

from typing import Any

from mcp.protocol.errors import INVALID_PARAMS, METHOD_NOT_FOUND, McpError
from mcp.protocol.types import PROTOCOL_VERSION
from mcp.server.registry import Registry


class Handler:
    """Dispatch incoming JSON-RPC requests to the appropriate registry method."""

    def __init__(
        self,
        registry: Registry,
        server_name: str,
        server_version: str,
    ) -> None:
        self._registry = registry
        self._server_name = server_name
        self._server_version = server_version
        self._initialized = False

    def handle(self, method: str, params: dict | None) -> Any:
        """Route a method call and return the result dict.

        Raises ``McpError`` for unknown methods or bad parameters.
        """
        dispatch = {
            "initialize": self._handle_initialize,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        }

        handler_fn = dispatch.get(method)
        if handler_fn is None:
            raise McpError(METHOD_NOT_FOUND, f"Unknown method: {method}")
        return handler_fn(params or {})

    def handle_notification(self, method: str, _params: dict | None) -> None:
        """Handle a client notification (no response expected)."""
        if method == "notifications/initialized":
            self._initialized = True
        # Other notifications are silently ignored per MCP spec.

    # ------------------------------------------------------------------
    # Method handlers
    # ------------------------------------------------------------------

    def _handle_initialize(self, _params: dict) -> dict:
        capabilities: dict[str, dict] = {}
        if self._registry.has_tools:
            capabilities["tools"] = {}
        if self._registry.has_resources:
            capabilities["resources"] = {}
        if self._registry.has_prompts:
            capabilities["prompts"] = {}
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": capabilities,
            "serverInfo": {
                "name": self._server_name,
                "version": self._server_version,
            },
        }

    def _handle_ping(self, _params: dict) -> dict:
        return {}

    def _handle_tools_list(self, _params: dict) -> dict:
        return {"tools": self._registry.list_tools()}

    def _handle_tools_call(self, params: dict) -> dict:
        name = params.get("name")
        if not name:
            raise McpError(INVALID_PARAMS, "Missing 'name' in tools/call")
        arguments = params.get("arguments", {})
        result = self._registry.call_tool(name, arguments)
        if isinstance(result, str):
            content = [{"type": "text", "text": result}]
        elif isinstance(result, dict):
            content = [{"type": "text", "text": str(result)}]
        elif isinstance(result, list):
            content = result
        else:
            content = [{"type": "text", "text": str(result)}]
        return {"content": content, "isError": False}

    def _handle_resources_list(self, _params: dict) -> dict:
        return {"resources": self._registry.list_resources()}

    def _handle_resources_read(self, params: dict) -> dict:
        uri = params.get("uri")
        if not uri:
            raise McpError(INVALID_PARAMS, "Missing 'uri' in resources/read")
        text, mime = self._registry.read_resource(uri)
        return {
            "contents": [
                {"uri": uri, "mimeType": mime, "text": text},
            ],
        }

    def _handle_prompts_list(self, _params: dict) -> dict:
        return {"prompts": self._registry.list_prompts()}

    def _handle_prompts_get(self, params: dict) -> dict:
        name = params.get("name")
        if not name:
            raise McpError(INVALID_PARAMS, "Missing 'name' in prompts/get")
        arguments = params.get("arguments", {})
        messages = self._registry.get_prompt(name, arguments)
        return {"messages": [m.to_dict() for m in messages]}
