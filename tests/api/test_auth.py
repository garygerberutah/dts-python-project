"""
Tests for api.src.auth — JWT token verification.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
from unittest import mock

import pytest

from api.src.auth import (
    AuthError,
    _base64url_decode,
    _decode_jwt_payload,
    _fetch_jwks,
    extract_bearer_token,
    get_user_id,
    validate_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _b64url(data: dict) -> str:
    """Encode a dict as a base64url string (no padding)."""
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _make_jwt(header: dict | None = None, payload: dict | None = None) -> str:
    """Build a mock JWT from header + payload dicts."""
    h = header or {"alg": "RS256", "typ": "JWT"}
    p = payload or {}
    sig = _b64url({"fake": "sig"})
    return f"{_b64url(h)}.{_b64url(p)}.{sig}"


# ---------------------------------------------------------------------------
# base64url decode
# ---------------------------------------------------------------------------


class TestBase64UrlDecode:
    """Tests for _base64url_decode."""

    def test_decode_padded(self):
        encoded = base64.urlsafe_b64encode(b"hello").rstrip(b"=").decode()
        assert _base64url_decode(encoded) == b"hello"

    def test_decode_longer_value(self):
        original = b"test data with extra characters"
        encoded = base64.urlsafe_b64encode(original).rstrip(b"=").decode()
        assert _base64url_decode(encoded) == original


# ---------------------------------------------------------------------------
# JWT payload decode
# ---------------------------------------------------------------------------


class TestDecodeJWTPayload:
    """Tests for _decode_jwt_payload."""

    def test_valid_jwt(self):
        payload = {"sub": "user123", "exp": 9999999999}
        token = _make_jwt(payload=payload)
        result = _decode_jwt_payload(token)
        assert result["sub"] == "user123"

    def test_malformed_jwt_no_dots(self):
        with pytest.raises(AuthError, match="Malformed JWT"):
            _decode_jwt_payload("nodots")

    def test_malformed_jwt_two_parts(self):
        with pytest.raises(AuthError, match="Malformed JWT"):
            _decode_jwt_payload("part1.part2")

    def test_invalid_base64_payload(self):
        with pytest.raises(AuthError, match="Cannot decode"):
            _decode_jwt_payload("aaa.!!!invalid!!!.ccc")


# ---------------------------------------------------------------------------
# extract_bearer_token
# ---------------------------------------------------------------------------


class TestExtractBearerToken:
    """Tests for extract_bearer_token."""

    def test_valid_bearer(self):
        token = extract_bearer_token({"Authorization": "Bearer abc123"})
        assert token == "abc123"

    def test_lowercase_authorization(self):
        token = extract_bearer_token({"authorization": "Bearer xyz"})
        assert token == "xyz"

    def test_missing_header(self):
        with pytest.raises(AuthError, match="Missing or malformed"):
            extract_bearer_token({})

    def test_no_bearer_prefix(self):
        with pytest.raises(AuthError, match="Missing or malformed"):
            extract_bearer_token({"Authorization": "Basic abc"})

    def test_empty_token(self):
        with pytest.raises(AuthError, match="Empty bearer token"):
            extract_bearer_token({"Authorization": "Bearer    "})

    def test_token_trimmed(self):
        token = extract_bearer_token({"Authorization": "Bearer  tok  "})
        assert token == "tok"


# ---------------------------------------------------------------------------
# validate_token
# ---------------------------------------------------------------------------


class TestValidateToken:
    """Tests for validate_token."""

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "client-id-1")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "https://cognito-idp.us-east-1.amazonaws.com/pool")
    def test_valid_token(self):
        payload = {
            "sub": "user-1",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/pool",
            "aud": "client-id-1",
            "exp": time.time() + 3600,
            "token_use": "access",
        }
        token = _make_jwt(payload=payload)
        claims = validate_token(token)
        assert claims["sub"] == "user-1"

    @mock.patch("api.src.auth.COGNITO_ISSUER", "https://expected-issuer")
    def test_issuer_mismatch(self):
        payload = {
            "iss": "https://wrong-issuer",
            "exp": time.time() + 3600,
            "token_use": "access",
        }
        token = _make_jwt(payload=payload)
        with pytest.raises(AuthError, match="issuer mismatch"):
            validate_token(token)

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "expected-client")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "")
    def test_audience_mismatch(self):
        payload = {
            "aud": "wrong-client",
            "exp": time.time() + 3600,
            "token_use": "access",
        }
        token = _make_jwt(payload=payload)
        with pytest.raises(AuthError, match="audience mismatch"):
            validate_token(token)

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "")
    def test_missing_expiry(self):
        token = _make_jwt(payload={"token_use": "access"})
        with pytest.raises(AuthError, match="no expiry"):
            validate_token(token)

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "")
    def test_expired_token(self):
        payload = {"exp": time.time() - 100, "token_use": "access"}
        token = _make_jwt(payload=payload)
        with pytest.raises(AuthError, match="expired"):
            validate_token(token)

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "")
    def test_invalid_token_use(self):
        payload = {"exp": time.time() + 3600, "token_use": "refresh"}
        token = _make_jwt(payload=payload)
        with pytest.raises(AuthError, match="Invalid token_use"):
            validate_token(token)

    @mock.patch("api.src.auth.COGNITO_APP_CLIENT_ID", "client-1")
    @mock.patch("api.src.auth.COGNITO_ISSUER", "")
    def test_client_id_claim_fallback(self):
        """Uses client_id claim when aud is missing."""
        payload = {
            "client_id": "client-1",
            "exp": time.time() + 3600,
            "token_use": "id",
        }
        token = _make_jwt(payload=payload)
        claims = validate_token(token)
        assert claims["client_id"] == "client-1"


# ---------------------------------------------------------------------------
# get_user_id
# ---------------------------------------------------------------------------


class TestGetUserId:
    """Tests for get_user_id."""

    def test_extracts_sub(self):
        assert get_user_id({"sub": "user-42"}) == "user-42"

    def test_missing_sub_returns_empty(self):
        assert get_user_id({}) == ""


# ---------------------------------------------------------------------------
# _fetch_jwks
# ---------------------------------------------------------------------------


class TestFetchJwks:
    """Tests for _fetch_jwks."""

    @pytest.fixture(autouse=True)
    def _clear_jwks_cache(self):
        """Clear the module-level JWKS cache before each test."""
        import api.src.auth as auth_mod
        auth_mod._jwks_cache = {}
        auth_mod._jwks_cache_ttl = 0.0
        yield
        auth_mod._jwks_cache = {}
        auth_mod._jwks_cache_ttl = 0.0

    @mock.patch("api.src.auth.COGNITO_JWKS_URL", "")
    def test_raises_when_url_not_configured(self):
        with pytest.raises(AuthError, match="not configured"):
            _fetch_jwks()

    @mock.patch("api.src.auth.COGNITO_JWKS_URL", "https://example.com/.well-known/jwks.json")
    @mock.patch("api.src.auth.urllib.request.urlopen")
    def test_fetches_and_caches(self, mock_urlopen):
        fake_jwks = {"keys": [{"kid": "abc"}]}
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = json.dumps(fake_jwks).encode()
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = _fetch_jwks()
        assert result["keys"][0]["kid"] == "abc"

        # Second call should use cache (no second urlopen)
        result2 = _fetch_jwks()
        assert result2 == result
        mock_urlopen.assert_called_once()

    @mock.patch("api.src.auth.COGNITO_JWKS_URL", "https://example.com/.well-known/jwks.json")
    @mock.patch("api.src.auth.urllib.request.urlopen")
    def test_raises_on_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with pytest.raises(AuthError, match="Cannot fetch JWKS"):
            _fetch_jwks()
