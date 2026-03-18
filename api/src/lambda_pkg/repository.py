"""
repository — DynamoDB data access for assets.

Copyright 2026 by GuidoGerb Publishing, LLC

Thin wrapper around DynamoDB operations for the ``ggp3d-assets`` table.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import boto3

from api.src.config import AWS_REGION, DYNAMODB_TABLE

_dynamodb = None


def _table():
    """Return the DynamoDB Table resource (lazy-initialised)."""
    global _dynamodb  # noqa: PLW0603
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return _dynamodb.Table(DYNAMODB_TABLE)


def create_asset(data: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Insert a new asset. Returns the created item."""
    item = {
        "id": str(uuid.uuid4()),
        "owner": user_id,
        "name": data["name"],
        "asset_type": data["asset_type"],
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    _table().put_item(Item=item)
    return item


def get_asset(asset_id: str) -> dict[str, Any] | None:
    """Fetch a single asset by ID. Returns ``None`` if not found."""
    resp = _table().get_item(Key={"id": asset_id})
    return resp.get("Item")


def list_assets(*, limit: int = 50) -> list[dict[str, Any]]:
    """Return up to *limit* assets (scan — suitable for small datasets)."""
    resp = _table().scan(Limit=limit)
    return resp.get("Items", [])


def update_asset(asset_id: str, data: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    """Update an existing asset. Returns the updated item or ``None``."""
    existing = get_asset(asset_id)
    if existing is None:
        return None

    if existing.get("owner") != user_id:
        return None

    update_parts: list[str] = []
    attr_names: dict[str, str] = {}
    attr_values: dict[str, Any] = {}

    for key, value in data.items():
        placeholder = f"#{key}"
        val_placeholder = f":{key}"
        update_parts.append(f"{placeholder} = {val_placeholder}")
        attr_names[placeholder] = key
        attr_values[val_placeholder] = value

    # Always update the timestamp
    update_parts.append("#updated_at = :updated_at")
    attr_names["#updated_at"] = "updated_at"
    attr_values[":updated_at"] = int(time.time())

    resp = _table().update_item(
        Key={"id": asset_id},
        UpdateExpression="SET " + ", ".join(update_parts),
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def delete_asset(asset_id: str, user_id: str) -> bool:
    """Delete an asset. Returns ``True`` if deleted, ``False`` otherwise."""
    existing = get_asset(asset_id)
    if existing is None:
        return False

    if existing.get("owner") != user_id:
        return False

    _table().delete_item(Key={"id": asset_id})
    return True
