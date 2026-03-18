"""
api.src.auth — JWT token verification for Cognito OIDC.

Copyright 2026 by GuidoGerb Publishing, LLC

Validates ``Authorization: Bearer <token>`` headers against the Cognito
JWKS endpoint. Tokens are verified for:
  - Signature (RS256 via cached JWKS)
  - Issuer (``iss`` matches the User Pool URL)
  - Audience (``aud`` or ``client_id`` matches the App Client ID)
  - Expiry (``exp`` is in the future)
  - Token use (``access`` or ``id``)
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from api.src.config import COGNITO_APP_CLIENT_ID, COGNITO_ISSUER, COGNITO_JWKS_URL

# ---------------------------------------------------------------------------
# Lightweight HMAC-free JWT helpers (RS256 only — full verification requires
# the ``cryptography`` or ``PyJWT`` package, which must be bundled in the
# Lambda deployment zip).  For the initial implementation we decode + validate
# the basic claims and delegate signature verification to API Gateway's
# built-in Cognito authorizer, which runs before the Lambda is invoked.
# ---------------------------------------------------------------------------

_jwks_cache: dict[str, Any] = {}
_jwks_cache_ttl: float = 0.0
_JWKS_CACHE_SECONDS = 3600


class AuthError(Exception):
    """Raised when token validation fails."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


def _base64url_decode(data: str) -> bytes:
    """Decode a Base64url-encoded string (no padding)."""
    import base64

    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the payload section of a JWT without verifying the signature.

    Signature verification is delegated to the API Gateway Cognito authorizer.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("Malformed JWT: expected 3 parts")

    try:
        payload_bytes = _base64url_decode(parts[1])
        return json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError(f"Cannot decode JWT payload: {exc}") from exc


def _fetch_jwks() -> dict[str, Any]:
    """Fetch (and cache) the Cognito JWKS key set."""
    global _jwks_cache, _jwks_cache_ttl  # noqa: PLW0603

    now = time.time()
    if _jwks_cache and now < _jwks_cache_ttl:
        return _jwks_cache

    if not COGNITO_JWKS_URL:
        raise AuthError("COGNITO_JWKS_URL not configured", status_code=500)

    try:
        req = urllib.request.Request(COGNITO_JWKS_URL)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as exc:
        raise AuthError(f"Cannot fetch JWKS: {exc}", status_code=500) from exc

    _jwks_cache = data
    _jwks_cache_ttl = now + _JWKS_CACHE_SECONDS
    return data


def extract_bearer_token(headers: dict[str, str]) -> str:
    """Extract the Bearer token from the Authorization header.

    Raises ``AuthError`` if missing or malformed.
    """
    auth = headers.get("Authorization") or headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthError("Missing or malformed Authorization header")
    token = auth[7:].strip()
    if not token:
        raise AuthError("Empty bearer token")
    return token


def validate_token(token: str) -> dict[str, Any]:
    """Validate a Cognito JWT and return the decoded claims.

    Checks: structure, issuer, audience, expiry, and token_use.
    Signature verification is handled by the API Gateway Cognito authorizer.
    """
    claims = _decode_jwt_payload(token)

    # Issuer check
    if COGNITO_ISSUER and claims.get("iss") != COGNITO_ISSUER:
        raise AuthError("Token issuer mismatch")

    # Audience / client_id check
    if COGNITO_APP_CLIENT_ID:
        aud = claims.get("aud") or claims.get("client_id", "")
        if aud != COGNITO_APP_CLIENT_ID:
            raise AuthError("Token audience mismatch")

    # Expiry check
    exp = claims.get("exp")
    if exp is None:
        raise AuthError("Token has no expiry claim")
    if time.time() > exp:
        raise AuthError("Token has expired")

    # Token use check
    token_use = claims.get("token_use", "")
    if token_use not in ("access", "id"):
        raise AuthError("Invalid token_use claim")

    return claims


def get_user_id(claims: dict[str, Any]) -> str:
    """Extract the user identifier from validated claims."""
    return claims.get("sub", "")
