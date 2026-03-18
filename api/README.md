# API

Copyright 2026 by GuidoGerb Publishing, LLC

RESTful API — AWS Lambda + API Gateway (HTTP API v2) + DynamoDB.

## Structure

```
api/
├── __init__.py
└── src/
    ├── __init__.py
    ├── auth/           # JWT / Cognito OIDC token validation
    │   └── __init__.py
    ├── config/         # Environment-based configuration
    │   └── __init__.py
    ├── lambda_pkg/     # Lambda function handlers
    │   ├── __init__.py
    │   ├── assets.py   # CRUD handler for /assets
    │   ├── health.py   # GET /health
    │   ├── repository.py # DynamoDB data access
    │   └── response.py # HTTP response builders
    └── schema/         # Request/response validation
        └── __init__.py
```

## Endpoints

| Method | Resource         | Auth     | Description          |
|--------|-----------------|----------|----------------------|
| GET    | /health         | None     | Health check         |
| GET    | /assets         | None     | List assets          |
| GET    | /assets/{id}    | None     | Get single asset     |
| POST   | /assets         | Bearer   | Create asset         |
| PUT    | /assets/{id}    | Bearer   | Update asset (owner) |
| DELETE | /assets/{id}    | Bearer   | Delete asset (owner) |
| OPTIONS| /assets         | None     | CORS preflight       |

## Authentication

OIDC + PKCE via AWS Cognito. API Gateway validates JWT signatures before
the Lambda is invoked. The handler verifies issuer, audience, expiry, and
`token_use` claims from the `Authorization: Bearer <token>` header.

Write operations (POST, PUT, DELETE) require authentication. Assets have
owner-based access control — only the creator can update or delete.

## Security

Every response includes:
- `Content-Type: application/json`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cache-Control: no-store`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

CORS is whitelist-only — `Access-Control-Allow-Origin` is set only for
origins in the `CORS_ALLOWED_ORIGINS` environment variable.

Error responses never expose internal details (stack traces, DB schema).

## Configuration

All settings are read from environment variables:

| Variable                | Default           | Description                     |
|------------------------|-------------------|---------------------------------|
| AWS_DEFAULT_REGION     | us-east-1         | AWS region                      |
| COGNITO_USER_POOL_ID   | (empty)           | Cognito User Pool ID            |
| COGNITO_APP_CLIENT_ID  | (empty)           | Cognito App Client ID           |
| DYNAMODB_TABLE         | ggp3d-assets      | DynamoDB table name             |
| CORS_ALLOWED_ORIGINS   | (empty)           | Comma-separated allowed origins |
| RATE_LIMIT_RPS         | 10                | Requests per second (at APIGW)  |

## Testing

```bash
python -m pytest tests/api/ -v              # Run API tests
python -m pytest tests/api/ --cov=api       # With coverage
```

136 tests — 100% coverage across all API modules.
