"""
Tests for api.src.lambda_pkg.assets — Lambda handler routing.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import base64
import json
import time
from unittest import mock

import pytest

from api.src.auth import AuthError
from api.src.lambda_pkg.assets import handler
from api.src.schema import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _b64url(data: dict) -> str:
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _make_jwt(payload: dict) -> str:
    h = _b64url({"alg": "RS256", "typ": "JWT"})
    p = _b64url(payload)
    s = _b64url({"fake": "sig"})
    return f"{h}.{p}.{s}"


_VALID_CLAIMS = {
    "sub": "user-1",
    "iss": "https://cognito-idp.us-east-1.amazonaws.com/pool",
    "aud": "client-1",
    "exp": time.time() + 3600,
    "token_use": "access",
}

_VALID_TOKEN = _make_jwt(_VALID_CLAIMS)


def _event(
    method: str,
    resource: str,
    *,
    body: dict | None = None,
    path_params: dict | None = None,
    token: str = _VALID_TOKEN,
    origin: str | None = None,
) -> dict:
    """Build a mock API Gateway proxy event."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if origin:
        headers["origin"] = origin
    ev = {
        "httpMethod": method,
        "resource": resource,
        "headers": headers,
        "pathParameters": path_params,
    }
    if body is not None:
        ev["body"] = json.dumps(body)
    return ev


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class TestRouting:
    """Tests for method/resource routing."""

    @mock.patch("api.src.lambda_pkg.assets.list_assets", return_value=[])
    def test_get_assets_routes_to_list(self, mock_list):
        event = _event("GET", "/assets", token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 200
        mock_list.assert_called_once()

    @mock.patch("api.src.lambda_pkg.assets.get_asset", return_value={"id": "abc"})
    def test_get_asset_routes_to_get(self, mock_get):
        event = _event("GET", "/assets/{id}", path_params={"id": "abc"}, token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 200
        mock_get.assert_called_once_with("abc")

    def test_unknown_method_returns_405(self):
        event = _event("PATCH", "/assets")
        resp = handler(event, None)
        assert resp["statusCode"] == 405

    def test_unknown_resource_returns_404(self):
        event = _event("GET", "/unknown")
        resp = handler(event, None)
        assert resp["statusCode"] == 404


# ---------------------------------------------------------------------------
# OPTIONS (CORS preflight)
# ---------------------------------------------------------------------------


class TestOptions:
    """Tests for OPTIONS preflight handling."""

    def test_options_returns_204(self):
        event = _event("OPTIONS", "/assets", token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 204


# ---------------------------------------------------------------------------
# GET /assets (list)
# ---------------------------------------------------------------------------


class TestListAssets:
    """Tests for GET /assets."""

    @mock.patch("api.src.lambda_pkg.assets.list_assets")
    def test_returns_assets_list(self, mock_list):
        mock_list.return_value = [{"id": "1", "name": "A"}]
        event = _event("GET", "/assets", token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert len(body["assets"]) == 1


# ---------------------------------------------------------------------------
# GET /assets/{id}
# ---------------------------------------------------------------------------


class TestGetAsset:
    """Tests for GET /assets/{id}."""

    @mock.patch("api.src.lambda_pkg.assets.get_asset")
    def test_returns_asset(self, mock_get):
        mock_get.return_value = {"id": "abc", "name": "Test"}
        event = _event("GET", "/assets/{id}", path_params={"id": "abc"}, token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 200

    @mock.patch("api.src.lambda_pkg.assets.get_asset")
    def test_returns_404_when_not_found(self, mock_get):
        mock_get.return_value = None
        event = _event("GET", "/assets/{id}", path_params={"id": "nope"}, token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 404

    def test_missing_id_returns_400(self):
        event = _event("GET", "/assets/{id}", path_params={}, token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 400


# ---------------------------------------------------------------------------
# POST /assets
# ---------------------------------------------------------------------------


class TestCreateAsset:
    """Tests for POST /assets."""

    @mock.patch("api.src.lambda_pkg.assets.create_asset")
    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_creates_asset(self, mock_validate, mock_create):
        mock_create.return_value = {"id": "new-1", "name": "Model"}
        event = _event(
            "POST",
            "/assets",
            body={"name": "Model", "asset_type": "model"},
        )
        resp = handler(event, None)
        assert resp["statusCode"] == 201

    @mock.patch("api.src.lambda_pkg.assets.validate_token")
    def test_auth_error_returns_401(self, mock_validate):
        mock_validate.side_effect = AuthError("Invalid token")
        event = _event("POST", "/assets", body={"name": "X", "asset_type": "model"})
        resp = handler(event, None)
        assert resp["statusCode"] == 401

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_validation_error_returns_400(self, mock_validate):
        event = _event("POST", "/assets", body={"name": "X"})
        resp = handler(event, None)
        assert resp["statusCode"] == 400

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_missing_body_returns_400(self, mock_validate):
        event = _event("POST", "/assets")
        resp = handler(event, None)
        assert resp["statusCode"] == 400


# ---------------------------------------------------------------------------
# PUT /assets/{id}
# ---------------------------------------------------------------------------


class TestUpdateAsset:
    """Tests for PUT /assets/{id}."""

    @mock.patch("api.src.lambda_pkg.assets.update_asset")
    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_updates_asset(self, mock_validate, mock_update):
        mock_update.return_value = {"id": "abc", "name": "Updated"}
        event = _event(
            "PUT",
            "/assets/{id}",
            body={"name": "Updated"},
            path_params={"id": "abc"},
        )
        resp = handler(event, None)
        assert resp["statusCode"] == 200

    @mock.patch("api.src.lambda_pkg.assets.update_asset")
    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_returns_404_when_not_found(self, mock_validate, mock_update):
        mock_update.return_value = None
        event = _event(
            "PUT",
            "/assets/{id}",
            body={"name": "X"},
            path_params={"id": "gone"},
        )
        resp = handler(event, None)
        assert resp["statusCode"] == 404


# ---------------------------------------------------------------------------
# DELETE /assets/{id}
# ---------------------------------------------------------------------------


class TestDeleteAsset:
    """Tests for DELETE /assets/{id}."""

    @mock.patch("api.src.lambda_pkg.assets.delete_asset")
    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_deletes_asset(self, mock_validate, mock_delete):
        mock_delete.return_value = True
        event = _event(
            "DELETE",
            "/assets/{id}",
            path_params={"id": "abc"},
        )
        resp = handler(event, None)
        assert resp["statusCode"] == 204

    @mock.patch("api.src.lambda_pkg.assets.delete_asset")
    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_returns_404_when_not_found(self, mock_validate, mock_delete):
        mock_delete.return_value = False
        event = _event(
            "DELETE",
            "/assets/{id}",
            path_params={"id": "gone"},
        )
        resp = handler(event, None)
        assert resp["statusCode"] == 404


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for global error handling in handler."""

    @mock.patch("api.src.lambda_pkg.assets.list_assets")
    def test_unhandled_exception_returns_500(self, mock_list):
        mock_list.side_effect = RuntimeError("boom")
        event = _event("GET", "/assets", token="")
        resp = handler(event, None)
        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert body["error"] == "INTERNAL_ERROR"
        # Must not leak internal details
        assert "boom" not in body["message"]

    def test_security_headers_on_error(self):
        event = _event("PATCH", "/assets")
        resp = handler(event, None)
        assert resp["headers"]["X-Content-Type-Options"] == "nosniff"
        assert resp["headers"]["X-Frame-Options"] == "DENY"


# ---------------------------------------------------------------------------
# Edge cases for body parsing and missing IDs
# ---------------------------------------------------------------------------


class TestBodyParsing:
    """Tests for JSON body edge cases."""

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_invalid_json_body_returns_400(self, mock_validate):
        event = _event("POST", "/assets")
        event["body"] = "not json"
        resp = handler(event, None)
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert "Invalid JSON" in body["message"]

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_non_dict_body_returns_400(self, mock_validate):
        event = _event("POST", "/assets")
        event["body"] = json.dumps(["a", "b"])
        resp = handler(event, None)
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert "JSON object" in body["message"]


class TestMissingIdParams:
    """Tests for missing path parameters on PUT and DELETE."""

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_put_missing_id_returns_400(self, mock_validate):
        event = _event("PUT", "/assets/{id}", body={"name": "X"}, path_params={})
        resp = handler(event, None)
        assert resp["statusCode"] == 400

    @mock.patch("api.src.lambda_pkg.assets.validate_token", return_value=_VALID_CLAIMS)
    def test_delete_missing_id_returns_400(self, mock_validate):
        event = _event("DELETE", "/assets/{id}", path_params={})
        resp = handler(event, None)
        assert resp["statusCode"] == 400
