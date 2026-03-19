# Security Policy

## Overview

This repository implements a zero-dependency, highly-audited architecture to minimize security risks, especially those introduced by AI-assisted development. The project is designed for government systems, handling sensitive data and critical infrastructure, and enforces strict guardrails to ensure code provenance, supply chain integrity, and compliance with accessibility and security standards.

## Supported Versions

Only the latest version of the repository is actively maintained and supported. All users are expected to keep their local clones up to date and to follow the enforced pre-commit and CI/CD policies.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it immediately to the repository maintainers (see repository author in README). Do **not** create a public issue. Instead, email the author directly at ggerber@utah.gov with a detailed description and steps to reproduce. Responsible disclosure is required.

## Security Features

- **Zero-Dependency Web Application**: No Node.js, npm, or third-party JS libraries. Only native HTML5, vanilla JavaScript, and Rust WebAssembly are used in the application layer.
- **Python-Only Toolchain**: All build, lint, test, and validation scripts are written in Python. No JS build tools or test frameworks are used.
- **Fail-Fast Pipeline**: All code must pass a strict, multi-stage validation pipeline before it can be committed or deployed. The pipeline includes:
  - Static analysis and linting (Python, Rust, JS)
  - Asset and mime-type validation
  - Automated accessibility (WCAG 2.1 Level AA)
  - Static component testing (pytest source-analysis)
  - Copyright and license checks
  - SBOM generation and blockchain-based audit trail
- **Immutable Audit Trail**: Every build generates a cryptographically signed Software Bill of Materials (SBOM), which is appended to a local blockchain and mirrored to a PostgreSQL database for auditability.
- **Strict Pre-Commit Enforcement**: Pre-commit hooks run the full pipeline locally. The `--no-verify` flag is strictly forbidden. Commits are rejected if any stage fails.
- **No External Resources**: All assets are self-hosted. No CDN, remote scripts, or external fonts/images are used.
- **RESTful API Security**: All API endpoints require authentication, use HTTPS, and enforce strict input validation and rate limiting. No anonymous write endpoints are allowed.
- **WebSocket Security**: WebSockets are push-only for plain text notifications. All messages are sanitized and authenticated.

## Known Security Limitations

- The local blockchain SBOM can be vulnerable if a developer's machine or CI server is compromised. Plans are in place to migrate to a centralized, state-controlled immutable ledger and to implement cryptographic signing with hardware keys.
- The custom Python-based JS linter currently lacks AST-level analysis. Future improvements will add semantic analysis to detect more subtle vulnerabilities.
- Pre-commit hooks are enforced locally, but ultimate enforcement is via CI/CD with branch protection rules.

## Best Practices for Contributors

- Never bypass or disable pre-commit hooks.
- Do not introduce new dependencies or external resources without explicit approval.
- Follow all coding, security, and accessibility guidelines as described in the README and .github/copilot-instructions.md.
- Disclose any potential security issues privately and promptly.

## Contact

For all security concerns, contact Gary Gerber at ggerber@utah.gov.

---

Copyright 2026 by DTS, The State of Utah

