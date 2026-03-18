"""
Tests for api.src.lambda_pkg.health — health endpoint.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import json

from api.src.lambda_pkg.health import handler


class TestHealthHandler:
    """Tests for the /health Lambda handler."""

    def test_returns_200(self):
        event = {"headers": {}}
        resp = handler(event, None)
        assert resp["statusCode"] == 200

    def test_body_contains_healthy(self):
        event = {"headers": {}}
        resp = handler(event, None)
        body = json.loads(resp["body"])
        assert body["status"] == "healthy"

    def test_security_headers_present(self):
        event = {"headers": {}}
        resp = handler(event, None)
        assert resp["headers"]["X-Content-Type-Options"] == "nosniff"
        assert resp["headers"]["X-Frame-Options"] == "DENY"

    def test_cors_from_origin(self):
        from unittest import mock

        with mock.patch(
            "api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS",
            ["https://app.example.com"],
        ):
            event = {"headers": {"origin": "https://app.example.com"}}
            resp = handler(event, None)
            assert resp["headers"]["Access-Control-Allow-Origin"] == "https://app.example.com"

    def test_no_cors_for_unknown_origin(self):
        from unittest import mock

        with mock.patch("api.src.lambda_pkg.response.CORS_ALLOWED_ORIGINS", []):
            event = {"headers": {"origin": "https://evil.com"}}
            resp = handler(event, None)
            assert "Access-Control-Allow-Origin" not in resp["headers"]
