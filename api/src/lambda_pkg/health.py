"""
health — Lambda handler for GET /health endpoint.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

from typing import Any

from api.src.lambda_pkg import response


def handler(event: dict, context: Any) -> dict:
    """Return 200 OK with status healthy."""
    origin = None
    headers = event.get("headers") or {}
    origin = headers.get("origin") or headers.get("Origin")
    return response.success({"status": "healthy"}, origin=origin)
