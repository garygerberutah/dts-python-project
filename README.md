# ggp3d

**Zero-dependency 3D geometry processor** — native HTML5 Web Components + Rust WebAssembly.
**Python-only toolchain** — no Node.js, npm, or any JS build tools.

[![CI](https://github.com/guidogerb/ggp3d/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/guidogerb/ggp3d/actions/workflows/ci.yml)
[![Deploy (dev)](https://github.com/guidogerb/ggp3d/actions/workflows/deploy-dev.yml/badge.svg?branch=dev)](https://github.com/guidogerb/ggp3d/actions/workflows/deploy-dev.yml)

---

## Architecture

| Layer | Technology |
|---|---|
| UI | HTML5 Web Components (Shadow DOM), vanilla JS — **zero runtime dependencies** |
| Core | Rust compiled to WebAssembly (wasm-bindgen) |
| Templates | Python + Jinja2 (build-time rendering only — never served at runtime) |
| Toolchain | Python scripts (`run.py`) — no Node.js |
| Tests | pytest (source-analysis, no browser) |
| CI/CD | GitHub Actions → AWS S3 + CloudFront |

---

## Quick Start

### Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.12 |
| Rust (stable) | ≥ 1.75 |
| wasm-pack | latest |

```bash
# Install Python dependencies (only dependency: Python)
pip install -r requirements.txt

# Install Rust toolchain (Linux / WSL2)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Add WASM compile target and install wasm-pack
rustup target add wasm32-unknown-unknown
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
```

---

## Toolchain Commands

All commands are driven by a single entry point:

```bash
python run.py <command> [options]
```

| Command | Description |
|---|---|
| `clean` | Remove `dist/` and `wasm/pkg/` |
| `build` | Compile WASM → render Jinja2 templates → copy assets to `dist/` |
| `serve [port]` | Serve `dist/` locally (default port 8080) |
| `format` | Auto-format Rust (rustfmt), Python (ruff) |
| `lint` | Static analysis — Python JS linter, cargo clippy, ruff check |
| `validate` | WCAG 2.1 compliance check on compiled HTML |
| `validate-copyright` | Verify copyright notice in all source files |
| `validate-mime` | Verify binary files match their mime-type encoding |
| `test` | Run all component test suites (pytest) |
| `pipeline` | Full 12-stage automation: test → format → lint → validate → build → test → SBOM → deploy |
| `pipeline --skip-deploy` | As above but skip the git commit/push stage |

---

## Master Pipeline

```
python run.py pipeline --skip-deploy
```

Stages (fail-fast):

1. **Test (global)** — run toolchain tests (`tests/`)
2. **Format** — auto-format Rust (rustfmt), Python (ruff)
3. **Lint** — Python JS linter, cargo clippy (`-D warnings`), ruff check
4. **Validate (copyright)** — copyright notice in all source files
5. **Validate (assets)** — asset naming conventions
6. **Validate (mime-type)** — binary files match their extension encoding
7. **Clean** — purge prior artefacts (`dist/`, `wasm/pkg/`)
8. **Build** — compile WASM, render Jinja2 templates, copy assets → `dist/`
9. **Validate (WCAG 2.1)** — accessibility checks on rendered HTML
10. **Test (components)** — pytest Web Component source-analysis tests
11. **SBOM (blockchain)** — generate SBOM manifest, append to blockchain, store in PostgreSQL
12. **Deploy** — `git commit` + `git push` *(skipped with `--skip-deploy`)*

---

## Project Structure

```
ggp-python-project/
├── run.py                          # Single CLI entry point
├── requirements.txt                # Python deps (jinja2, pytest, ruff, etc.)
├── COPYRIGHT                       # Copyright notice (required in all source files)
├── LICENSE                         # MIT license
├── ui/
│   ├── scss/                       # ITCSS SCSS stylesheets
│   │   ├── index.scss
│   │   ├── 1-settings/             # Design tokens, CSS variables
│   │   ├── 2-tools/                # Mixins, functions
│   │   ├── 3-generic/              # Reset, normalize
│   │   ├── 4-elements/             # Bare element styles
│   │   ├── 5-objects/              # Layout patterns
│   │   ├── 6-components/           # Component styles
│   │   ├── 7-utilities/            # Utility classes
│   │   ├── 8-super/                # Print styles
│   │   └── 9-tip/                  # Tooltip styles
│   └── src/
│       ├── main.js                 # ES module entry point
│       ├── components/             # Web Components (Shadow DOM)
│       │   ├── app-root.js
│       │   ├── app-header.js
│       │   └── app-3d-viewer.js
│       ├── templates/              # Jinja2 build-time templates
│       │   ├── base.html.j2
│       │   └── index.html.j2
│       └── wasm/                   # Rust → WASM crate (3D math engine)
│           ├── Cargo.toml
│           └── src/lib.rs
├── scripts/
│   ├── build_all.py                # Master pipeline (12 stages, fail-fast)
│   └── ui/
│       ├── build.py                # WASM compile + Jinja2 render + asset copy
│       ├── clean.py                # Remove dist/ and wasm/pkg/
│       ├── serve.py                # Local HTTP dev server
│       ├── format_code.py          # rustfmt + ruff format
│       ├── lint.py                 # ruff check + cargo clippy + JS linter
│       ├── lint_js.py              # Python-based JS linter
│       ├── validate_wcag.py        # WCAG 2.1 Level AA validator
│       ├── validate_copyright.py   # Copyright notice checker
│       ├── validate_assets.py      # Asset naming convention checker
│       ├── validate_mime_type_content.py  # Binary mime-type validator
│       └── test_components.py      # pytest test runner
│   └── blockchain/
│       ├── sbom.py                 # Append-only blockchain with PoW
│       ├── generate_sbom.py        # SBOM manifest generator (SHA-256)
│       ├── db.py                   # PostgreSQL SBOM storage
│       ├── chain.json              # Blockchain data file
│       └── sbom.json               # Generated SBOM manifest
├── tests/
│   ├── conftest.py                 # Global test fixtures
│   ├── test_*.py                   # Toolchain script tests
│   └── ui/
│       ├── conftest.py             # Source-analysis fixtures
│       ├── test_app_root.py
│       ├── test_app_header.py
│       └── test_app_3d_viewer.py
├── resources/
│   ├── config/
│   │   ├── site.json               # Project metadata
│   │   └── ruff.toml               # Ruff linter config
│   └── user-instructions/          # Portable Copilot instruction files
├── api/                            # RESTful API (AWS Lambda + API Gateway)
└── .github/
    ├── copilot-instructions.md     # Project-level AI instructions
    └── instructions/               # Scope-specific instruction files
```

---

## SBOM Blockchain & PostgreSQL

### Overview

Every pipeline run (stage 11) generates a **Software Bill of Materials** (SBOM) — a SHA-256 manifest of all git-tracked files — and appends it to an append-only blockchain with proof-of-work. The blockchain is stored in `scripts/blockchain/chain.json` (git-tracked, the **single source of truth**). A PostgreSQL database mirrors the chain for queryable auditing.

### Data Flow

```
git ls-files → SHA-256 per file → composite hash → blockchain block (chain.json) → PostgreSQL (sbom_version)
```

### Source of Truth

| Artifact | Location | Versioned? | Purpose |
|---|---|---|---|
| Blockchain | `scripts/blockchain/chain.json` | **Yes** (git) | Authoritative append-only ledger |
| SBOM manifest | `scripts/blockchain/sbom.json` | Yes (git) | Latest file-level hashes |
| PostgreSQL | Docker volume `pgdata` | No | Queryable audit mirror |

`chain.json` travels with the repo. PostgreSQL is a **derived store** — it can be rebuilt from `chain.json` at any time.

### Docker PostgreSQL Setup

The pipeline auto-starts a Docker PostgreSQL container when no local instance is available.

```yaml
# docker-compose.yml
Container:  ggp3d-postgres
Image:      postgres:16-alpine
Port:       5433 (host) → 5432 (container)
Database:   asset_catalog
User:       assman
```

**Connection fallback order** (handled automatically by `scripts/blockchain/db.py`):

1. Localhost PostgreSQL on port **5432** (your dev machine)
2. Docker container `ggp3d-postgres` on port **5433** (auto-started if needed)

### Connecting to PostgreSQL

```bash
# Install psql client (if not available)
sudo apt-get install -y postgresql-client

# Connect to the Docker instance
PGPASSWORD='1324QEWRFD7sdf!1!' psql -h localhost -p 5433 -U assman -d asset_catalog

# Query SBOM records (exclude the large JSONB column)
SELECT id, commit_sha, branch, composite_sha256, file_count, created_at FROM sbom_version;
```

### Maintaining the Blockchain Across Instances

`chain.json` is the portable, git-tracked source of truth. PostgreSQL data does **not** transfer between machines — it must be rebuilt locally.

#### New Environment Setup (Codespace, new machine, CI runner)

```bash
# 1. Clone the repo — chain.json comes with it
git clone git@github.com:guidogerb/ggp-python-project.git
cd ggp-python-project

# 2. Start Docker PostgreSQL
docker compose up -d --wait

# 3. Rebuild the sbom_version table from chain.json
python run.py sync-db
```

#### Workflow Between Codespace and Localhost

```
┌─────────────────────┐         git push / pull        ┌─────────────────────┐
│   GitHub Codespace   │ ◄──────────────────────────► │      Localhost       │
│                       │                               │                     │
│  chain.json (git) ───────── shared via git ────────── chain.json (git)    │
│  PostgreSQL :5433    │   (independent instances)      │  PostgreSQL :5432   │
│  (Docker volume)     │                                │  (native or Docker) │
└─────────────────────┘                                └─────────────────────┘
```

**After pulling new commits** (either direction):

```bash
git pull
python run.py sync-db    # rebuild PostgreSQL from updated chain.json
```

**After running the pipeline** (commits a new block to chain.json):

```bash
python run.py pipeline   # stages 1-12: generates SBOM, mines block, stores in DB, pushes
```

The other environment pulls and runs `sync-db` to catch up.

#### Key Commands

| Command | Description |
|---|---|
| `python run.py pipeline` | Full pipeline — generates SBOM, mines block, stores in DB, deploys |
| `python run.py sync-db` | Rebuild PostgreSQL from `chain.json` (run after `git pull`) |
| `docker compose up -d` | Start PostgreSQL container |
| `docker compose down` | Stop PostgreSQL container (data persists in volume) |
| `docker compose down -v` | Stop and **destroy** PostgreSQL data volume |

---

## AWS Deployment

The `deploy-dev.yml` workflow triggers on every push to the `dev` branch.

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_DEFAULT_REGION` | e.g. `us-east-1` |
| `AWS_S3_BUCKET_DEV` | Target S3 bucket name |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID_DEV` | CloudFront distribution ID |

---

## Testing

### Rust (native)
```bash
cd ui/src/wasm && cargo test
```

### Web Components (pytest)
```bash
python run.py test
# or directly:
pytest tests/ tests/ui/ -v
```

### WCAG Validation (after build)
```bash
python run.py validate
```

---

## License

MIT — see [LICENSE](LICENSE).