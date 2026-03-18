"""
response — Shared HTTP response builder for Lambda handlers.

Copyright 2026 by GuidoGerb Publishing, LLC

Produces API Gateway proxy-integration responses with required security
headers on every response.
"""

from __future__ import annotations

import json
from typing import Any

from api.src.config import CORS_ALLOWED_ORIGINS, SECURITY_HEADERS


def _cors_headers(origin: str | None) -> dict[str, str]:
    """Return CORS headers if *origin* is in the allowed list."""
    headers: dict[str, str] = {}
    if origin and origin in CORS_ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        headers["Access-Control-Max-Age"] = "86400"
    return headers


def success(body: Any, *, status_code: int = 200, origin: str | None = None) -> dict:
    """Build a 2xx response."""
    headers = {**SECURITY_HEADERS, **_cors_headers(origin)}
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body, default=str),
    }


def created(body: Any, *, origin: str | None = None) -> dict:
    """Build a 201 Created response."""
    return success(body, status_code=201, origin=origin)


def no_content(*, origin: str | None = None) -> dict:
    """Build a 204 No Content response."""
    headers = {**SECURITY_HEADERS, **_cors_headers(origin)}
    return {
        "statusCode": 204,
        "headers": headers,
        "body": "",
    }


def error(
    message: str,
    *,
    status_code: int = 400,
    error_code: str = "BAD_REQUEST",
    origin: str | None = None,
) -> dict:
    """Build an error response with a safe message (no internal details)."""
    headers = {**SECURITY_HEADERS, **_cors_headers(origin)}
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps({"error": error_code, "message": message}),
    }


def unauthorized(message: str = "Unauthorized", *, origin: str | None = None) -> dict:
    """Build a 401 Unauthorized response."""
    return error(message, status_code=401, error_code="UNAUTHORIZED", origin=origin)


def forbidden(message: str = "Forbidden", *, origin: str | None = None) -> dict:
    """Build a 403 Forbidden response."""
    return error(message, status_code=403, error_code="FORBIDDEN", origin=origin)


def not_found(message: str = "Resource not found", *, origin: str | None = None) -> dict:
    """Build a 404 Not Found response."""
    return error(message, status_code=404, error_code="NOT_FOUND", origin=origin)


def server_error(*, origin: str | None = None) -> dict:
    """Build a 500 Internal Server Error response (no internal details exposed)."""
    return error(
        "Internal server error",
        status_code=500,
        error_code="INTERNAL_ERROR",
        origin=origin,
    )
