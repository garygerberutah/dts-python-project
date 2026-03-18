"""
api.src.schema — Request/response validation for REST endpoints.

Copyright 2026 by GuidoGerb Publishing, LLC

Validates inbound JSON payloads against known schemas. All validation
happens server-side — never trust client data.
"""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "") -> None:
        super().__init__(message)
        self.field = field


# ---------------------------------------------------------------------------
# Primitive validators
# ---------------------------------------------------------------------------

_SAFE_STRING_RE = re.compile(r"^[\w\s.,!?@#$%^&*()\-+=:;'\"/\[\]{}|~`]+$", re.UNICODE)
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_MAX_STRING_LENGTH = 1024


def validate_string(value: Any, field: str, *, max_length: int = _MAX_STRING_LENGTH) -> str:
    """Validate that *value* is a non-empty safe string."""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string", field)
    stripped = value.strip()
    if not stripped:
        raise ValidationError(f"{field} must not be empty", field)
    if len(stripped) > max_length:
        raise ValidationError(f"{field} exceeds maximum length of {max_length}", field)
    return stripped


def validate_uuid(value: Any, field: str) -> str:
    """Validate that *value* is a well-formed UUID v4."""
    s = validate_string(value, field, max_length=36)
    if not _UUID_RE.match(s.lower()):
        raise ValidationError(f"{field} must be a valid UUID", field)
    return s.lower()


def validate_positive_int(value: Any, field: str) -> int:
    """Validate that *value* is a positive integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field} must be an integer", field)
    if value <= 0:
        raise ValidationError(f"{field} must be positive", field)
    return value


# ---------------------------------------------------------------------------
# Asset schema — the primary resource in the ggp3d API
# ---------------------------------------------------------------------------

ASSET_REQUIRED_FIELDS = ("name", "asset_type")
ASSET_VALID_TYPES = ("model", "texture", "material", "scene", "animation")


def validate_asset_create(body: dict[str, Any]) -> dict[str, Any]:
    """Validate the body of a POST /assets request."""
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")

    for f in ASSET_REQUIRED_FIELDS:
        if f not in body:
            raise ValidationError(f"Missing required field: {f}", f)

    name = validate_string(body["name"], "name", max_length=256)

    asset_type = validate_string(body["asset_type"], "asset_type", max_length=32)
    if asset_type not in ASSET_VALID_TYPES:
        raise ValidationError(
            f"asset_type must be one of: {', '.join(ASSET_VALID_TYPES)}",
            "asset_type",
        )

    result: dict[str, Any] = {"name": name, "asset_type": asset_type}

    # Optional fields
    if "description" in body:
        result["description"] = validate_string(
            body["description"], "description", max_length=2048
        )
    if "tags" in body:
        tags = body["tags"]
        if not isinstance(tags, list):
            raise ValidationError("tags must be an array", "tags")
        result["tags"] = [validate_string(t, "tags[]", max_length=64) for t in tags]

    return result


def validate_asset_update(body: dict[str, Any]) -> dict[str, Any]:
    """Validate the body of a PUT /assets/{id} request."""
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")

    result: dict[str, Any] = {}

    if "name" in body:
        result["name"] = validate_string(body["name"], "name", max_length=256)
    if "asset_type" in body:
        asset_type = validate_string(body["asset_type"], "asset_type", max_length=32)
        if asset_type not in ASSET_VALID_TYPES:
            raise ValidationError(
                f"asset_type must be one of: {', '.join(ASSET_VALID_TYPES)}",
                "asset_type",
            )
        result["asset_type"] = asset_type
    if "description" in body:
        result["description"] = validate_string(
            body["description"], "description", max_length=2048
        )
    if "tags" in body:
        tags = body["tags"]
        if not isinstance(tags, list):
            raise ValidationError("tags must be an array", "tags")
        result["tags"] = [validate_string(t, "tags[]", max_length=64) for t in tags]

    if not result:
        raise ValidationError("At least one field must be provided for update")

    return result
