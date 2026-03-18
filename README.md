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