"""
Tests for api.src.lambda_pkg.repository — DynamoDB data access.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

from unittest import mock

import pytest

# Reset the lazy singleton before each import so patches take effect
import api.src.lambda_pkg.repository as repo_mod


@pytest.fixture(autouse=True)
def _reset_dynamodb():
    """Reset the module-level _dynamodb singleton before each test."""
    repo_mod._dynamodb = None
    yield
    repo_mod._dynamodb = None


@pytest.fixture
def mock_table():
    """Return a mocked DynamoDB Table resource."""
    table = mock.MagicMock()
    resource = mock.MagicMock()
    resource.Table.return_value = table
    with mock.patch("api.src.lambda_pkg.repository.boto3") as mock_boto3:
        mock_boto3.resource.return_value = resource
        yield table


# ---------------------------------------------------------------------------
# create_asset
# ---------------------------------------------------------------------------


class TestCreateAsset:
    """Tests for create_asset."""

    def test_creates_item_with_required_fields(self, mock_table):
        data = {"name": "Test Model", "asset_type": "model"}
        result = repo_mod.create_asset(data, "user-1")

        assert result["name"] == "Test Model"
        assert result["asset_type"] == "model"
        assert result["owner"] == "user-1"
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result
        mock_table.put_item.assert_called_once()

    def test_preserves_optional_fields(self, mock_table):
        data = {
            "name": "Texture",
            "asset_type": "texture",
            "description": "A texture",
            "tags": ["diffuse"],
        }
        result = repo_mod.create_asset(data, "user-2")
        assert result["description"] == "A texture"
        assert result["tags"] == ["diffuse"]


# ---------------------------------------------------------------------------
# get_asset
# ---------------------------------------------------------------------------


class TestGetAsset:
    """Tests for get_asset."""

    def test_returns_item_when_found(self, mock_table):
        mock_table.get_item.return_value = {"Item": {"id": "abc", "name": "Test"}}
        result = repo_mod.get_asset("abc")
        assert result["id"] == "abc"

    def test_returns_none_when_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        result = repo_mod.get_asset("missing")
        assert result is None


# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------


class TestListAssets:
    """Tests for list_assets."""

    def test_returns_items(self, mock_table):
        mock_table.scan.return_value = {"Items": [{"id": "1"}, {"id": "2"}]}
        result = repo_mod.list_assets()
        assert len(result) == 2

    def test_default_limit(self, mock_table):
        mock_table.scan.return_value = {"Items": []}
        repo_mod.list_assets()
        mock_table.scan.assert_called_once_with(Limit=50)

    def test_custom_limit(self, mock_table):
        mock_table.scan.return_value = {"Items": []}
        repo_mod.list_assets(limit=10)
        mock_table.scan.assert_called_once_with(Limit=10)

    def test_empty_results(self, mock_table):
        mock_table.scan.return_value = {"Items": []}
        result = repo_mod.list_assets()
        assert result == []


# ---------------------------------------------------------------------------
# update_asset
# ---------------------------------------------------------------------------


class TestUpdateAsset:
    """Tests for update_asset."""

    def test_updates_own_asset(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"id": "abc", "owner": "user-1", "name": "Old"}
        }
        mock_table.update_item.return_value = {
            "Attributes": {"id": "abc", "owner": "user-1", "name": "New"}
        }
        result = repo_mod.update_asset("abc", {"name": "New"}, "user-1")
        assert result["name"] == "New"
        mock_table.update_item.assert_called_once()

    def test_returns_none_when_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        result = repo_mod.update_asset("missing", {"name": "X"}, "user-1")
        assert result is None

    def test_returns_none_when_not_owner(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"id": "abc", "owner": "other-user"}
        }
        result = repo_mod.update_asset("abc", {"name": "X"}, "user-1")
        assert result is None
        mock_table.update_item.assert_not_called()

    def test_updates_timestamp(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"id": "abc", "owner": "user-1"}
        }
        mock_table.update_item.return_value = {"Attributes": {"id": "abc"}}
        repo_mod.update_asset("abc", {"name": "New"}, "user-1")
        call_kwargs = mock_table.update_item.call_args[1]
        assert ":updated_at" in call_kwargs["ExpressionAttributeValues"]


# ---------------------------------------------------------------------------
# delete_asset
# ---------------------------------------------------------------------------


class TestDeleteAsset:
    """Tests for delete_asset."""

    def test_deletes_own_asset(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"id": "abc", "owner": "user-1"}
        }
        result = repo_mod.delete_asset("abc", "user-1")
        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={"id": "abc"})

    def test_returns_false_when_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        result = repo_mod.delete_asset("missing", "user-1")
        assert result is False

    def test_returns_false_when_not_owner(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"id": "abc", "owner": "other-user"}
        }
        result = repo_mod.delete_asset("abc", "user-1")
        assert result is False
        mock_table.delete_item.assert_not_called()
