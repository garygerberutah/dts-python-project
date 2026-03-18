"""
Tests for api.src.schema — request validation.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import pytest

from api.src.schema import (
    ValidationError,
    validate_asset_create,
    validate_asset_update,
    validate_positive_int,
    validate_string,
    validate_uuid,
)


# ---------------------------------------------------------------------------
# validate_string
# ---------------------------------------------------------------------------


class TestValidateString:
    """Tests for validate_string."""

    def test_valid_string(self):
        assert validate_string("hello", "name") == "hello"

    def test_strips_whitespace(self):
        assert validate_string("  spaced  ", "name") == "spaced"

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string(123, "name")

    def test_rejects_empty_string(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            validate_string("   ", "name")

    def test_rejects_too_long(self):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_string("a" * 100, "name", max_length=50)

    def test_respects_custom_max_length(self):
        result = validate_string("short", "name", max_length=10)
        assert result == "short"


# ---------------------------------------------------------------------------
# validate_uuid
# ---------------------------------------------------------------------------


class TestValidateUuid:
    """Tests for validate_uuid."""

    def test_valid_uuid(self):
        uid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid(uid, "id") == uid

    def test_uppercase_normalised_to_lower(self):
        uid = "550E8400-E29B-41D4-A716-446655440000"
        assert validate_uuid(uid, "id") == uid.lower()

    def test_rejects_invalid_uuid(self):
        with pytest.raises(ValidationError, match="valid UUID"):
            validate_uuid("not-a-uuid", "id")

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_uuid(123, "id")


# ---------------------------------------------------------------------------
# validate_positive_int
# ---------------------------------------------------------------------------


class TestValidatePositiveInt:
    """Tests for validate_positive_int."""

    def test_valid_positive(self):
        assert validate_positive_int(5, "count") == 5

    def test_rejects_zero(self):
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_int(0, "count")

    def test_rejects_negative(self):
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_int(-1, "count")

    def test_rejects_string(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int("5", "count")

    def test_rejects_bool(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int(True, "count")

    def test_rejects_float(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int(3.14, "count")


# ---------------------------------------------------------------------------
# validate_asset_create
# ---------------------------------------------------------------------------


class TestValidateAssetCreate:
    """Tests for validate_asset_create."""

    def test_valid_minimal(self):
        result = validate_asset_create({"name": "My Model", "asset_type": "model"})
        assert result["name"] == "My Model"
        assert result["asset_type"] == "model"

    def test_valid_with_description_and_tags(self):
        body = {
            "name": "Texture A",
            "asset_type": "texture",
            "description": "A nice texture",
            "tags": ["diffuse", "4k"],
        }
        result = validate_asset_create(body)
        assert result["description"] == "A nice texture"
        assert result["tags"] == ["diffuse", "4k"]

    def test_missing_name(self):
        with pytest.raises(ValidationError, match="Missing required field: name"):
            validate_asset_create({"asset_type": "model"})

    def test_missing_asset_type(self):
        with pytest.raises(ValidationError, match="Missing required field: asset_type"):
            validate_asset_create({"name": "Test"})

    def test_invalid_asset_type(self):
        with pytest.raises(ValidationError, match="asset_type must be one of"):
            validate_asset_create({"name": "Test", "asset_type": "invalid"})

    def test_all_valid_asset_types(self):
        for t in ("model", "texture", "material", "scene", "animation"):
            result = validate_asset_create({"name": "Test", "asset_type": t})
            assert result["asset_type"] == t

    def test_tags_must_be_list(self):
        with pytest.raises(ValidationError, match="tags must be an array"):
            validate_asset_create({"name": "Test", "asset_type": "model", "tags": "not-a-list"})

    def test_non_dict_body(self):
        with pytest.raises(ValidationError, match="must be a JSON object"):
            validate_asset_create("not a dict")


# ---------------------------------------------------------------------------
# validate_asset_update
# ---------------------------------------------------------------------------


class TestValidateAssetUpdate:
    """Tests for validate_asset_update."""

    def test_valid_name_only(self):
        result = validate_asset_update({"name": "Updated Name"})
        assert result["name"] == "Updated Name"

    def test_valid_asset_type(self):
        result = validate_asset_update({"asset_type": "scene"})
        assert result["asset_type"] == "scene"

    def test_invalid_asset_type(self):
        with pytest.raises(ValidationError, match="asset_type must be one of"):
            validate_asset_update({"asset_type": "bad"})

    def test_empty_body_rejected(self):
        with pytest.raises(ValidationError, match="At least one field"):
            validate_asset_update({})

    def test_description_update(self):
        result = validate_asset_update({"description": "New desc"})
        assert result["description"] == "New desc"

    def test_tags_update(self):
        result = validate_asset_update({"tags": ["a", "b"]})
        assert result["tags"] == ["a", "b"]

    def test_tags_must_be_list(self):
        with pytest.raises(ValidationError, match="tags must be an array"):
            validate_asset_update({"tags": "not-a-list"})

    def test_non_dict_body(self):
        with pytest.raises(ValidationError, match="must be a JSON object"):
            validate_asset_update("string")
