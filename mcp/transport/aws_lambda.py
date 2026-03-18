# Copyright 2026 by GuidoGerb Publishing, LLC
"""AWS Lambda transport for MCP servers.

Adapts an McpServer into an AWS Lambda handler function that receives
JSON-RPC requests via API Gateway (HTTP API v2) and returns responses.

Usage::

    from mcp.transport.aws_lambda import create_lambda_handler
    from my_server import server

    handler = create_lambda_handler(server)

Deploy ``handler`` as the Lambda entry point.  API Gateway routes
``POST /mcp`` to this function.

Security headers are applied to every response per project standards.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.protocol.errors import INTERNAL_ERROR, McpError
from mcp.protocol.jsonrpc import parse_message, serialize_error, serialize_response

if TYPE_CHECKING:
    from mcp.server.base import McpServer

# Security headers applied to every Lambda response.
_SECURITY_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def _cors_headers(origin: str, allowed_origins: list[str]) -> dict[str, str]:
    """Build CORS headers if the origin is allowed."""
    if not origin or not allowed_origins:
        return {}
    if origin not in allowed_origins:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
    }


def _lambda_response(status: int, body: str, extra_headers: dict | None = None) -> dict:
    """Build an API Gateway v2 Lambda proxy response."""
    headers = dict(_SECURITY_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status,
        "headers": headers,
        "body": body,
    }


def create_lambda_handler(
    server: McpServer,
    *,
    allowed_origins: list[str] | None = None,
) -> Any:
    """Create an AWS Lambda handler function for the given MCP server.

    Parameters
    ----------
    server:
        The McpServer instance with registered tools/resources/prompts.
    allowed_origins:
        Whitelist of CORS origins. Pass ``None`` to disable CORS.

    Returns
    -------
    A callable ``handler(event, context)`` suitable for Lambda.
    """
    origins = allowed_origins or []
    handler_obj = server.handler

    def handler(event: dict, context: Any) -> dict:
        """AWS Lambda entry point for MCP over API Gateway HTTP API v2."""
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
        origin = (event.get("headers") or {}).get("origin", "")
        cors = _cors_headers(origin, origins)

        # OPTIONS — CORS preflight
        if http_method == "OPTIONS":
            return _lambda_response(204, "", cors)

        # Only POST is supported for JSON-RPC
        if http_method != "POST":
            return _lambda_response(
                405,
                json.dumps({"error": "method_not_allowed", "message": "Use POST"}),
                cors,
            )

        raw_body = event.get("body", "")
        if not raw_body:
            return _lambda_response(
                400,
                json.dumps({"error": "bad_request", "message": "Empty body"}),
                cors,
            )

        # Handle base64 encoded body from API Gateway
        if event.get("isBase64Encoded"):
            import base64

            raw_body = base64.b64decode(raw_body).decode("utf-8")

        try:
            msg = parse_message(raw_body)
        except McpError as exc:
            body = serialize_error(None, exc)
            return _lambda_response(400, body, cors)

        request_id = msg.get("id")
        method = msg.get("method")

        # Notification — accept, no response body
        if request_id is None and method:
            handler_obj.handle_notification(method, msg.get("params"))
            return _lambda_response(202, "", cors)

        # Request
        try:
            result = handler_obj.handle(method, msg.get("params"))
            body = serialize_response(request_id, result)
        except McpError as exc:
            body = serialize_error(request_id, exc)
        except Exception as exc:
            err = McpError(INTERNAL_ERROR, f"Internal server error: {exc}")
            body = serialize_error(request_id, err)

        return _lambda_response(200, body, cors)

    return handler
