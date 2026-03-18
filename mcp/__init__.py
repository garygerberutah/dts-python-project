# Copyright 2026 by GuidoGerb Publishing, LLC
"""
mcp — Model Context Protocol server framework.

Provides a decorator-based API for building MCP servers that can run
locally over stdio or deploy to AWS Lambda behind API Gateway.
"""

from mcp.server.base import McpServer

__all__ = ["McpServer"]
