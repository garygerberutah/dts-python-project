# Copyright 2026 by GuidoGerb Publishing, LLC
"""McpServer — the main entry point for building MCP servers.

Usage::

    from mcp import McpServer

    server = McpServer(name="my-server", version="1.0.0")

    @server.tool(description="Add two numbers")
    def add(a: int, b: int) -> int:
        return a + b

    @server.resource(uri="config://app", description="App config")
    def app_config() -> str:
        return '{"debug": false}'

    @server.prompt(description="Greet someone")
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    # Run locally via stdio
    server.run()

    # Or run on a local HTTP port
    server.run(transport="http", port=8090)
"""

from __future__ import annotations

from collections.abc import Callable

from mcp.protocol.types import PromptArgument
from mcp.server.handler import Handler
from mcp.server.registry import Registry


class McpServer:
    """Decorator-based MCP server builder.

    Register tools, resources, and prompts with ``@server.tool()``,
    ``@server.resource()``, and ``@server.prompt()`` decorators, then
    call ``server.run()`` to start serving.
    """

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self._registry = Registry()
        self._handler = Handler(self._registry, name, version)

    # ------------------------------------------------------------------
    # Decorators
    # ------------------------------------------------------------------

    def tool(
        self,
        *,
        name: str | None = None,
        description: str = "",
    ) -> Callable:
        """Register a function as an MCP tool.

        Parameters
        ----------
        name:
            Tool name exposed to the client.  Defaults to the
            function name.
        description:
            Human-readable description of what the tool does.
        """

        def decorator(fn: Callable) -> Callable:
            tool_name = name or fn.__name__
            desc = description or fn.__doc__ or ""
            self._registry.add_tool(tool_name, desc.strip(), fn)
            return fn

        return decorator

    def resource(
        self,
        *,
        uri: str,
        name: str | None = None,
        description: str = "",
        mime_type: str = "text/plain",
    ) -> Callable:
        """Register a function as an MCP resource reader.

        Parameters
        ----------
        uri:
            The resource URI (e.g. ``config://app``).
        name:
            Display name. Defaults to the function name.
        description:
            Human-readable description.
        mime_type:
            MIME type of the returned content.
        """

        def decorator(fn: Callable) -> Callable:
            res_name = name or fn.__name__
            desc = description or fn.__doc__ or ""
            self._registry.add_resource(uri, res_name, desc.strip(), mime_type, fn)
            return fn

        return decorator

    def prompt(
        self,
        *,
        name: str | None = None,
        description: str = "",
        arguments: list[PromptArgument] | None = None,
    ) -> Callable:
        """Register a function as an MCP prompt template.

        Parameters
        ----------
        name:
            Prompt name. Defaults to the function name.
        description:
            Human-readable description.
        arguments:
            Explicit argument list. If omitted, derived from the
            function signature (all params treated as required strings).
        """

        def decorator(fn: Callable) -> Callable:
            prompt_name = name or fn.__name__
            desc = description or fn.__doc__ or ""
            prompt_args = arguments or _derive_prompt_args(fn)
            self._registry.add_prompt(prompt_name, desc.strip(), prompt_args, fn)
            return fn

        return decorator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def handler(self) -> Handler:
        """The JSON-RPC method dispatcher (used by transports)."""
        return self._handler

    @property
    def registry(self) -> Registry:
        """The internal tool/resource/prompt registry."""
        return self._registry

    def run(
        self,
        *,
        transport: str = "stdio",
        host: str = "127.0.0.1",
        port: int = 3000,
    ) -> None:
        """Start serving requests.

        Parameters
        ----------
        transport:
            ``"stdio"`` for stdin/stdout (default) or ``"http"``
            for Streamable HTTP on localhost.
        host:
            Bind address for HTTP transport.
        port:
            Listen port for HTTP transport.
        """
        if transport == "stdio":
            from mcp.transport.stdio import StdioTransport

            StdioTransport(self._handler).serve()
        elif transport == "http":
            from mcp.transport.http import HttpTransport

            HttpTransport(self._handler, host=host, port=port).serve()
        else:
            raise ValueError(f"Unknown transport: {transport!r} (use 'stdio' or 'http')")


def _derive_prompt_args(fn: Callable) -> list[PromptArgument]:
    """Derive PromptArgument list from function signature."""
    import inspect

    sig = inspect.signature(fn)
    result: list[PromptArgument] = []
    for param_name, param in sig.parameters.items():
        required = param.default is inspect.Parameter.empty
        result.append(PromptArgument(name=param_name, required=required))
    return result
