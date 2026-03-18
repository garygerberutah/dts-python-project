---
description: "Use when implementing API endpoints, HTTP handlers, REST routes, or any client-server communication. Covers REST semantics, security headers, CORS, and WebSocket rules."
---
# API Security Standards

## REST
- All endpoints: GET, POST, PUT, DELETE with JSON bodies — no RPC, no GraphQL
- `Content-Type: application/json` on all responses
- Validate all inputs server-side — never trust client data
- Return proper HTTP status codes (200, 201, 204, 400, 401, 403, 404, 500)

## Transport Security
- HTTPS only in production — reject plain HTTP
- HSTS header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Authentication
- Authenticate every request — no anonymous write endpoints
- Bearer tokens via `Authorization` header — never in query params or cookies
- Fail closed on auth errors: deny by default

## Response Headers (all responses)
- `Content-Type: application/json`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cache-Control: no-store` for authenticated responses
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## CORS
- Whitelist specific origins only — never `Access-Control-Allow-Origin: *` in production
- Explicit allowed methods and headers
- `Access-Control-Max-Age` for preflight caching

## Rate Limiting
- Rate-limit all endpoints
- Return `429 Too Many Requests` with `Retry-After` header

## Error Responses
- Never expose stack traces, internal paths, or database schema
- Consistent error shape: `{ "error": "<code>", "message": "<user-safe text>" }`

## WebSocket Rules
- Push-only for vetted plain text — status updates, notifications
- **NEVER** send: SQL, binary blobs, executable scripts, HTML, serialized objects
- Authenticate at handshake; reject unauthenticated upgrades
- Client treats all WebSocket data as untrusted display text

## Binary Content Rule
- Binary files **may** be versioned in git if they represent a recognized, inspectable mime-type (`image/png`, `image/jpeg`, `image/gif`, `image/svg+xml`, `video/mp4`, `audio/mpeg`, `application/pdf`, `application/json`, `application/xml`)
- The file's binary content must match the encoding of its extension's mime-type
- **Strictly forbidden**: `application/octet-stream` and any binary data not clearly associated with an inspectable mime-type
- No base64 data URIs or inline binary encodings in text source files — reference assets by path
