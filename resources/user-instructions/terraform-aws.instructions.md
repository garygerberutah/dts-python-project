---
applyTo: ["**/*.tf", "**/*.tfvars"]
description: "Use when writing or editing Terraform infrastructure. Covers API Gateway, Lambda, S3, CloudFront patterns, state management, and security."
---
# Terraform Infrastructure Standards

## Stack
- **API Gateway** (HTTP API v2) — REST endpoints, Lambda integration
- **Lambda** — Python 3.12 runtime, minimal IAM roles
- **S3** — static site hosting (private bucket, CloudFront OAC)
- **CloudFront** — CDN distribution, HTTPS termination, origin access control

## Structure
```
infra/
├── main.tf           # Provider, backend
├── variables.tf      # Input variables
├── outputs.tf        # Exported values
├── api-gateway.tf    # API Gateway + routes
├── lambda.tf         # Lambda functions + IAM
├── s3.tf             # Buckets + policies
├── cloudfront.tf     # Distribution + OAC
└── terraform.tfvars  # Environment values (gitignored)
```

## Conventions
- Remote state in S3 + DynamoDB locking
- One resource per logical block — no mega-files
- Use `locals` for computed values, `variable` for inputs
- Tag all resources: `Project`, `Environment`, `ManagedBy = "terraform"`
- Use `data` sources to reference existing resources — don't hardcode ARNs

## Security
- S3 buckets: block all public access, serve only via CloudFront OAC
- Lambda: least-privilege IAM — one role per function, no `*` actions
- API Gateway: attach Cognito authorizer to all protected routes
- CloudFront: HTTPS-only, redirect HTTP → HTTPS, TLS 1.2 minimum
- No secrets in `.tf` files — use `terraform.tfvars` (gitignored) or SSM Parameter Store
- Enable access logging on API Gateway and CloudFront

## Forbidden
- No `*` in IAM policy actions or resources (except `logs:*` for CloudWatch)
- No public S3 bucket policies
- No inline Lambda code — deploy from packaged zip
- No hardcoded account IDs or ARNs — use `data.aws_caller_identity` and variables
- No base64 data URIs or inline binary encodings in `.tf` files — reference assets by path
- `application/octet-stream` and opaque binary blobs are forbidden in git
