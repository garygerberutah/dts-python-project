# User-Level Instruction Files

Reusable Copilot instruction files that apply across **all** your workspaces, not just this project.

## Installation

Copy all `.instructions.md` files to your VS Code user prompts directory:

```bash
cp resources/user-instructions/*.instructions.md \
   ~/.vscode-server/data/User/prompts/instructions/
```

Create the directory first if it doesn't exist:

```bash
mkdir -p ~/.vscode-server/data/User/prompts/instructions
```

On desktop VS Code (non-remote), the path is:
- **macOS**: `~/Library/Application Support/Code/User/prompts/instructions/`
- **Windows**: `%APPDATA%\Code\User\prompts\instructions\`
- **Linux**: `~/.config/Code/User/prompts/instructions/`

## Files

| File | Triggers On | What It Enforces |
|------|-------------|-----------------|
| `scss-itcss.instructions.md` | `**/*.scss` | ITCSS layer ordering, BEM naming, libsass, no external fonts/frameworks |
| `vanilla-javascript.instructions.md` | `**/*.js` | ES6+ modules only, zero dependencies, browser-native APIs, no bundlers |
| `testing-pytest-selenium.instructions.md` | `test_*.py` | pytest conventions, Selenium 4 explicit waits, coverage, no JS test frameworks |
| `python-build-toolchain.instructions.md` | `scripts/**/*.py`, `run.py` | Python 3.12 build scripts, fail-fast pipelines, no npm/node |
| `auth-oidc-cognito.instructions.md` | On-demand (auth tasks) | OIDC + PKCE flow, Cognito config, token handling, no implicit grant |
| `terraform-aws.instructions.md` | `**/*.tf`, `**/*.tfvars` | API Gateway + Lambda + S3 + CloudFront, least-privilege IAM, remote state |
| `api-security.instructions.md` | On-demand (API tasks) | REST-only, strict headers, CORS whitelist, WebSocket text-only, rate limiting |

## How They Work

### Explicit mode (`applyTo`)
Files with `applyTo` in their frontmatter automatically load when you create or edit matching files. For example, `vanilla-javascript.instructions.md` loads whenever you touch a `.js` file in any workspace.

### On-demand mode (`description` only)
Files without `applyTo` (like `auth-oidc-cognito.instructions.md`) load when Copilot detects task relevance from the `description` keywords. They also appear in the **Add Context → Instructions** menu for manual attachment.

## Customization

Edit any file to match your preferences. The frontmatter fields:

```yaml
---
applyTo: "**/*.js"              # Glob pattern — auto-attach for matching files
description: "Use when..."      # Keyword-rich — enables on-demand discovery
---
```

## Scope Differences

| Scope | Location | Shared via git? | Applies to |
|-------|----------|-----------------|------------|
| **Project** | `.github/instructions/` | Yes | This workspace only |
| **User** | `~/.vscode-server/data/User/prompts/instructions/` | No | All workspaces |

The project-level instructions in `.github/instructions/` are specific to ggp3d. These user-level files are portable standards you carry across all projects.
