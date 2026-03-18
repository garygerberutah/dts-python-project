# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.transport.aws_lambda — Lambda handler adapter."""

from __future__ import annotations

import json

import pytest

from mcp import McpServer
from mcp.transport.aws_lambda import create_lambda_handler


@pytest.fixture()
def lambda_server() -> McpServer:
    """Server with a single tool for Lambda testing."""
    srv = McpServer(name="lambda-test", version="0.1.0")

    @srv.tool(description="Echo text")
    def echo(text: str) -> str:
        return text

    @srv.resource(uri="test://r", description="Test")
    def res() -> str:
        return "data"

    return srv


@pytest.fixture()
def handler(lambda_server: McpServer):
    """Lambda handler function with CORS."""
    return create_lambda_handler(
        lambda_server,
        allowed_origins=["https://example.com"],
    )


def _api_event(method: str, body: str = "", origin: str = "") -> dict:
    """Build a minimal API Gateway HTTP API v2 event."""
    headers = {}
    if origin:
        headers["origin"] = origin
    return {
        "requestContext": {"http": {"method": method}},
        "headers": headers,
        "body": body,
        "isBase64Encoded": False,
    }


class TestLambdaPost:
    def test_ping(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body), None)
        assert resp["statusCode"] == 200
        msg = json.loads(resp["body"])
        assert msg["result"] == {}

    def test_initialize(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        resp = handler(_api_event("POST", body), None)
        msg = json.loads(resp["body"])
        assert msg["result"]["serverInfo"]["name"] == "lambda-test"

    def test_tools_call(self, handler) -> None:
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"text": "hello"}},
            }
        )
        resp = handler(_api_event("POST", body), None)
        msg = json.loads(resp["body"])
        assert msg["result"]["content"][0]["text"] == "hello"

    def test_empty_body_returns_400(self, handler) -> None:
        resp = handler(_api_event("POST", ""), None)
        assert resp["statusCode"] == 400

    def test_invalid_json_returns_400(self, handler) -> None:
        resp = handler(_api_event("POST", "{bad}"), None)
        assert resp["statusCode"] == 400

    def test_notification_returns_202(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        resp = handler(_api_event("POST", body), None)
        assert resp["statusCode"] == 202


class TestLambdaCors:
    def test_options_returns_204(self, handler) -> None:
        resp = handler(_api_event("OPTIONS", origin="https://example.com"), None)
        assert resp["statusCode"] == 204

    def test_allowed_origin_header(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body, origin="https://example.com"), None)
        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://example.com"

    def test_disallowed_origin_no_cors_header(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body, origin="https://evil.com"), None)
        assert "Access-Control-Allow-Origin" not in resp["headers"]


class TestLambdaSecurityHeaders:
    def test_content_type(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body), None)
        assert resp["headers"]["Content-Type"] == "application/json"

    def test_nosniff(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body), None)
        assert resp["headers"]["X-Content-Type-Options"] == "nosniff"

    def test_frame_deny(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body), None)
        assert resp["headers"]["X-Frame-Options"] == "DENY"

    def test_hsts(self, handler) -> None:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        resp = handler(_api_event("POST", body), None)
        hsts = resp["headers"]["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts


class TestLambdaMethodRestriction:
    def test_get_returns_405(self, handler) -> None:
        resp = handler(_api_event("GET"), None)
        assert resp["statusCode"] == 405

    def test_put_returns_405(self, handler) -> None:
        resp = handler(_api_event("PUT"), None)
        assert resp["statusCode"] == 405


class TestLambdaBase64:
    def test_base64_body_decoded(self, handler) -> None:
        import base64

        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        encoded = base64.b64encode(raw.encode()).decode()
        event = _api_event("POST", encoded)
        event["isBase64Encoded"] = True
        resp = handler(event, None)
        assert resp["statusCode"] == 200
        msg = json.loads(resp["body"])
        assert msg["result"] == {}
