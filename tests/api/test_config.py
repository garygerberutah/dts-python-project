"""
Tests for api.src.config — configuration from environment variables.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import importlib
import os
from unittest import mock


def _reload_config(**env_vars):
    """Reload config module with the given environment variables."""
    import api.src.config as config_mod

    with mock.patch.dict(os.environ, env_vars, clear=False):
        importlib.reload(config_mod)
    return config_mod


class TestAWSConfig:
    """AWS / Cognito configuration tests."""

    def test_default_region(self):
        mod = _reload_config()
        assert mod.AWS_REGION == os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    def test_custom_region(self):
        mod = _reload_config(AWS_DEFAULT_REGION="eu-west-1")
        assert mod.AWS_REGION == "eu-west-1"

    def test_cognito_user_pool_id_default_empty(self):
        env = {k: v for k, v in os.environ.items() if k != "COGNITO_USER_POOL_ID"}
        with mock.patch.dict(os.environ, env, clear=True):
            mod = _reload_config()
        assert mod.COGNITO_USER_POOL_ID == ""

    def test_cognito_issuer_built_from_pool_id(self):
        mod = _reload_config(
            COGNITO_USER_POOL_ID="us-east-1_ABC123",
            AWS_DEFAULT_REGION="us-east-1",
        )
        assert "us-east-1_ABC123" in mod.COGNITO_ISSUER
        assert "cognito-idp.us-east-1.amazonaws.com" in mod.COGNITO_ISSUER

    def test_cognito_jwks_url_from_issuer(self):
        mod = _reload_config(
            COGNITO_USER_POOL_ID="us-east-1_XYZ",
            AWS_DEFAULT_REGION="us-east-1",
        )
        assert mod.COGNITO_JWKS_URL.endswith("/.well-known/jwks.json")

    def test_empty_pool_id_means_empty_issuer(self):
        env = {k: v for k, v in os.environ.items() if k != "COGNITO_USER_POOL_ID"}
        with mock.patch.dict(os.environ, env, clear=True):
            mod = _reload_config()
        assert mod.COGNITO_ISSUER == ""
        assert mod.COGNITO_JWKS_URL == ""


class TestDynamoDBConfig:
    """DynamoDB configuration tests."""

    def test_default_table_name(self):
        env = {k: v for k, v in os.environ.items() if k != "DYNAMODB_TABLE"}
        with mock.patch.dict(os.environ, env, clear=True):
            mod = _reload_config()
        assert mod.DYNAMODB_TABLE == "ggp3d-assets"

    def test_custom_table_name(self):
        mod = _reload_config(DYNAMODB_TABLE="my-custom-table")
        assert mod.DYNAMODB_TABLE == "my-custom-table"


class TestCORSConfig:
    """CORS configuration tests."""

    def test_empty_origins_by_default(self):
        env = {k: v for k, v in os.environ.items() if k != "CORS_ALLOWED_ORIGINS"}
        with mock.patch.dict(os.environ, env, clear=True):
            mod = _reload_config()
        assert mod.CORS_ALLOWED_ORIGINS == []

    def test_single_origin(self):
        mod = _reload_config(CORS_ALLOWED_ORIGINS="https://example.com")
        assert mod.CORS_ALLOWED_ORIGINS == ["https://example.com"]

    def test_multiple_origins(self):
        mod = _reload_config(
            CORS_ALLOWED_ORIGINS="https://a.com, https://b.com"
        )
        assert mod.CORS_ALLOWED_ORIGINS == ["https://a.com", "https://b.com"]

    def test_trailing_whitespace_stripped(self):
        mod = _reload_config(CORS_ALLOWED_ORIGINS="  https://x.com  ")
        assert mod.CORS_ALLOWED_ORIGINS == ["https://x.com"]


class TestSecurityHeaders:
    """Security headers configuration tests."""

    def test_contains_nosniff(self):
        mod = _reload_config()
        assert mod.SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"

    def test_contains_deny_framing(self):
        mod = _reload_config()
        assert mod.SECURITY_HEADERS["X-Frame-Options"] == "DENY"

    def test_contains_hsts(self):
        mod = _reload_config()
        assert "max-age" in mod.SECURITY_HEADERS["Strict-Transport-Security"]

    def test_contains_no_store_cache(self):
        mod = _reload_config()
        assert mod.SECURITY_HEADERS["Cache-Control"] == "no-store"

    def test_content_type_json(self):
        mod = _reload_config()
        assert mod.SECURITY_HEADERS["Content-Type"] == "application/json"


class TestRateLimitConfig:
    """Rate limiting configuration tests."""

    def test_default_rate_limit(self):
        env = {k: v for k, v in os.environ.items() if k != "RATE_LIMIT_RPS"}
        with mock.patch.dict(os.environ, env, clear=True):
            mod = _reload_config()
        assert mod.RATE_LIMIT_REQUESTS_PER_SECOND == 10

    def test_custom_rate_limit(self):
        mod = _reload_config(RATE_LIMIT_RPS="50")
        assert mod.RATE_LIMIT_REQUESTS_PER_SECOND == 50
