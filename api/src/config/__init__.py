"""
api.src.config — API configuration and environment settings.

Copyright 2026 by GuidoGerb Publishing, LLC

All configuration is read from environment variables. No secrets in source.
"""

from __future__ import annotations

import os


# -- AWS / Cognito -----------------------------------------------------------

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "")
COGNITO_ISSUER = (
    f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
    if COGNITO_USER_POOL_ID
    else ""
)
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json" if COGNITO_ISSUER else ""

# -- DynamoDB -----------------------------------------------------------------

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "ggp3d-assets")

# -- CORS ---------------------------------------------------------------------

# Comma-separated list of allowed origins (no trailing slashes)
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in _raw_origins.split(",") if o.strip()
]

# -- Response headers applied to every response -------------------------------

SECURITY_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

# -- Rate limiting defaults (enforced at API Gateway level) -------------------

RATE_LIMIT_REQUESTS_PER_SECOND = int(
    os.environ.get("RATE_LIMIT_RPS", "10")
)
