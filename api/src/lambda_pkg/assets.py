"""
assets — Lambda handler for /assets REST endpoints.

Copyright 2026 by GuidoGerb Publishing, LLC

Routes:
    GET    /assets          — list assets
    GET    /assets/{id}     — get single asset
    POST   /assets          — create asset (authenticated)
    PUT    /assets/{id}     — update asset (authenticated, owner only)
    DELETE /assets/{id}     — delete asset (authenticated, owner only)
    OPTIONS /assets         — CORS preflight
"""

from __future__ import annotations

import json
import logging
from typing import Any

from api.src.auth import AuthError, extract_bearer_token, get_user_id, validate_token
from api.src.lambda_pkg import response
from api.src.lambda_pkg.repository import (
    create_asset,
    delete_asset,
    get_asset,
    list_assets,
    update_asset,
)
from api.src.schema import ValidationError, validate_asset_create, validate_asset_update

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_origin(event: dict) -> str | None:
    """Extract the Origin header from the event."""
    headers = event.get("headers") or {}
    return headers.get("origin") or headers.get("Origin")


def _authenticate(event: dict) -> dict[str, Any]:
    """Extract and validate the bearer token. Returns claims."""
    headers = event.get("headers") or {}
    token = extract_bearer_token(headers)
    return validate_token(token)


def _get_path_param(event: dict, param: str) -> str:
    """Extract a path parameter from the event."""
    params = event.get("pathParameters") or {}
    return params.get(param, "")


def _parse_body(event: dict) -> dict[str, Any]:
    """Parse the JSON body from the event."""
    body = event.get("body", "")
    if not body:
        raise ValidationError("Request body is required")
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("Request body must be a JSON object")
    return parsed


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


def _handle_list(event: dict) -> dict:
    """GET /assets"""
    origin = _get_origin(event)
    items = list_assets()
    return response.success({"assets": items}, origin=origin)


def _handle_get(event: dict) -> dict:
    """GET /assets/{id}"""
    origin = _get_origin(event)
    asset_id = _get_path_param(event, "id")
    if not asset_id:
        return response.error("Asset ID is required", origin=origin)

    item = get_asset(asset_id)
    if item is None:
        return response.not_found(origin=origin)

    return response.success(item, origin=origin)


def _handle_create(event: dict) -> dict:
    """POST /assets"""
    origin = _get_origin(event)
    claims = _authenticate(event)
    user_id = get_user_id(claims)

    body = _parse_body(event)
    validated = validate_asset_create(body)
    item = create_asset(validated, user_id)

    return response.created(item, origin=origin)


def _handle_update(event: dict) -> dict:
    """PUT /assets/{id}"""
    origin = _get_origin(event)
    claims = _authenticate(event)
    user_id = get_user_id(claims)

    asset_id = _get_path_param(event, "id")
    if not asset_id:
        return response.error("Asset ID is required", origin=origin)

    body = _parse_body(event)
    validated = validate_asset_update(body)
    item = update_asset(asset_id, validated, user_id)

    if item is None:
        return response.not_found(origin=origin)

    return response.success(item, origin=origin)


def _handle_delete(event: dict) -> dict:
    """DELETE /assets/{id}"""
    origin = _get_origin(event)
    claims = _authenticate(event)
    user_id = get_user_id(claims)

    asset_id = _get_path_param(event, "id")
    if not asset_id:
        return response.error("Asset ID is required", origin=origin)

    deleted = delete_asset(asset_id, user_id)
    if not deleted:
        return response.not_found(origin=origin)

    return response.no_content(origin=origin)


def _handle_options(event: dict) -> dict:
    """OPTIONS /assets — CORS preflight."""
    origin = _get_origin(event)
    return response.no_content(origin=origin)


# ---------------------------------------------------------------------------
# Main Lambda entry point
# ---------------------------------------------------------------------------

_ROUTES = {
    "GET": {
        "/assets": _handle_list,
        "/assets/{id}": _handle_get,
    },
    "POST": {
        "/assets": _handle_create,
    },
    "PUT": {
        "/assets/{id}": _handle_update,
    },
    "DELETE": {
        "/assets/{id}": _handle_delete,
    },
    "OPTIONS": {
        "/assets": _handle_options,
        "/assets/{id}": _handle_options,
    },
}


def handler(event: dict, context: Any) -> dict:
    """AWS Lambda handler — routes API Gateway proxy events to handlers."""
    origin = _get_origin(event)

    try:
        http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", ""))
        resource = event.get("resource", "")

        method_routes = _ROUTES.get(http_method)
        if not method_routes:
            return response.error(
                "Method not allowed",
                status_code=405,
                error_code="METHOD_NOT_ALLOWED",
                origin=origin,
            )

        route_handler = method_routes.get(resource)
        if not route_handler:
            return response.not_found(origin=origin)

        return route_handler(event)

    except AuthError as exc:
        logger.warning("Auth error: %s", exc)
        return response.unauthorized(str(exc), origin=origin)

    except ValidationError as exc:
        logger.info("Validation error: %s", exc)
        return response.error(str(exc), origin=origin)

    except Exception:
        logger.exception("Unhandled exception in Lambda handler")
        return response.server_error(origin=origin)
