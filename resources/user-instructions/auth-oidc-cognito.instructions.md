---
description: "Use when implementing authentication, login flows, token handling, or user session management. Covers OIDC + PKCE via AWS Cognito."
---
# Authentication Standards (OIDC + PKCE via AWS Cognito)

## Flow
- Authorization Code flow with PKCE — no implicit grant, no client secrets in browser
- Client generates `code_verifier` + `code_challenge` (S256) per session
- Redirect to Cognito `/authorize` → user authenticates → redirect back with `code`
- Exchange `code` + `code_verifier` at `/token` endpoint for ID/access/refresh tokens

## Token Handling
- Store tokens in memory only (JS variables) — never `localStorage`, never cookies with tokens
- Access token: short-lived, sent as `Authorization: Bearer <token>` header
- Refresh token: use to silently renew access token before expiry
- ID token: extract user claims for display — never trust client-side for authorization

## Cognito Configuration
- User Pool for authentication; Identity Pool only if AWS service access needed
- Enable MFA (at minimum optional TOTP)
- Custom domain for hosted UI or use `/oauth2` endpoints directly
- Callback URLs: explicit whitelist per environment — no wildcards

## Security Rules
- Validate all tokens server-side (check `iss`, `aud`, `exp`, `token_use` claims)
- Reject expired tokens immediately — no grace periods
- PKCE is mandatory — never use implicit flow
- Logout: revoke tokens at Cognito `/revoke` endpoint + clear client state
- CORS: whitelist Cognito domain and app origins only

## Forbidden
- No client secrets in frontend code
- No tokens in URLs, query parameters, or localStorage
- No implicit grant flow
- No custom auth schemes — use standard OIDC
- No base64 data URIs or inline binary encodings in source files — reference assets by path
- `application/octet-stream` and opaque binary blobs are forbidden in git
