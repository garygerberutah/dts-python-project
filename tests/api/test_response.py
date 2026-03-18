"""
Tests for api.src.lambda_pkg.response — HTTP response builders.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import json
from unittest import mock

from api.src.lambda_pkg.response import (
    _cors_headers,
    created,
    error,
    forbidden,
    no_content,
    not_found,
    server_error,
    success,
    unauthorized,
)


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------


class TestCorsHeaders:
    """Tests for _cors_headers."""

    @mock.patch("api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS", ["https://ok.com"])
    def test_allowed_origin(self):
        headers = _cors_headers("https://ok.com")
        assert headers["Access-Control-Allow-Origin"] == "https://ok.com"
        assert "GET" in headers["Access-Control-Allow-Methods"]

    @mock.patch("api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS", ["https://ok.com"])
    def test_disallowed_origin(self):
        headers = _cors_headers("https://evil.com")
        assert "Access-Control-Allow-Origin" not in headers

    @mock.patch("api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS", [])
    def test_no_origin(self):
        headers = _cors_headers(None)
        assert headers == {}


# ---------------------------------------------------------------------------
# success
# ---------------------------------------------------------------------------


class TestSuccess:
    """Tests for success response."""

    def test_default_200(self):
        resp = success({"key": "val"})
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["key"] == "val"

    def test_custom_status_code(self):
        resp = success({"ok": True}, status_code=202)
        assert resp["statusCode"] == 202

    def test_security_headers_present(self):
        resp = success({})
        assert resp["headers"]["X-Content-Type-Options"] == "nosniff"
        assert resp["headers"]["X-Frame-Options"] == "DENY"

    @mock.patch("api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS", ["https://a.com"])
    def test_cors_headers_included(self):
        resp = success({}, origin="https://a.com")
        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://a.com"


# ---------------------------------------------------------------------------
# created
# ---------------------------------------------------------------------------


class TestCreated:
    """Tests for created response."""

    def test_status_201(self):
        resp = created({"id": "abc"})
        assert resp["statusCode"] == 201


# ---------------------------------------------------------------------------
# no_content
# ---------------------------------------------------------------------------


class TestNoContent:
    """Tests for no_content response."""

    def test_status_204(self):
        resp = no_content()
        assert resp["statusCode"] == 204
        assert resp["body"] == ""

    def test_security_headers(self):
        resp = no_content()
        assert "X-Frame-Options" in resp["headers"]


# ---------------------------------------------------------------------------
# error
# ---------------------------------------------------------------------------


class TestError:
    """Tests for error response."""

    def test_default_400(self):
        resp = error("Bad input")
        assert resp["statusCode"] == 400
        body = json.loads(resp["body"])
        assert body["error"] == "BAD_REQUEST"
        assert body["message"] == "Bad input"

    def test_custom_status_and_code(self):
        resp = error("Conflict", status_code=409, error_code="CONFLICT")
        assert resp["statusCode"] == 409
        body = json.loads(resp["body"])
        assert body["error"] == "CONFLICT"


# ---------------------------------------------------------------------------
# unauthorized
# ---------------------------------------------------------------------------


class TestUnauthorized:
    """Tests for unauthorized response."""

    def test_status_401(self):
        resp = unauthorized()
        assert resp["statusCode"] == 401
        body = json.loads(resp["body"])
        assert body["error"] == "UNAUTHORIZED"

    def test_custom_message(self):
        resp = unauthorized("Token expired")
        body = json.loads(resp["body"])
        assert body["message"] == "Token expired"


# ---------------------------------------------------------------------------
# forbidden
# ---------------------------------------------------------------------------


class TestForbidden:
    """Tests for forbidden response."""

    def test_status_403(self):
        resp = forbidden()
        assert resp["statusCode"] == 403
        body = json.loads(resp["body"])
        assert body["error"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# not_found
# ---------------------------------------------------------------------------


class TestNotFound:
    """Tests for not_found response."""

    def test_status_404(self):
        resp = not_found()
        assert resp["statusCode"] == 404
        body = json.loads(resp["body"])
        assert body["error"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# server_error
# ---------------------------------------------------------------------------


class TestServerError:
    """Tests for server_error response."""

    def test_status_500(self):
        resp = server_error()
        assert resp["statusCode"] == 500

    def test_no_internal_details(self):
        resp = server_error()
        body = json.loads(resp["body"])
        assert body["message"] == "Internal server error"
        assert body["error"] == "INTERNAL_ERROR"
