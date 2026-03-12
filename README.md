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

# Install wasm-pack
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
| `test` | Run all component test suites (pytest) |
| `pipeline` | Full automation: format → lint → clean → build → validate → test → deploy |
| `pipeline --skip-deploy` | As above but skip the git commit/push stage |

---

## Master Pipeline

```
python run.py pipeline --skip-deploy
```

Stages (fail-fast):

1. **Format** — auto-formats Rust, Python
2. **Lint** — Python JS linter, cargo clippy (`-D warnings`), ruff
3. **Clean** — purge prior artefacts
4. **Build** — compile WASM, render templates, copy assets
5. **Validate** — WCAG 2.1 Level AA checks on rendered HTML
6. **Test** — pytest component tests (source analysis, Shadow DOM patterns, accessibility)
7. **Deploy** — `git commit` + `git push` *(gated behind 100% success)*

---

## Project Structure

```
ggp3d/
├── wasm/                   # Rust WASM crate (3D math engine)
│   ├── Cargo.toml
│   └── src/lib.rs
├── frontend/
│   ├── components/         # Web Components (source only, no test files)
│   │   ├── app-root.js
│   │   ├── app-header.js
│   │   └── app-3d-viewer.js
│   ├── js/main.js          # ES module entry point
│   └── styles/main.css     # Global CSS reset
├── tests/                  # pytest component test suites
│   ├── conftest.py         # Source-analysis fixtures
│   ├── test_app_root.py
│   ├── test_app_header.py
│   └── test_app_3d_viewer.py
├── templates/              # Jinja2 HTML templates (build-time only)
│   ├── base.html.j2
│   └── index.html.j2
├── scripts/                # Python toolchain scripts
│   ├── build.py
│   ├── clean.py
│   ├── serve.py
│   ├── format_code.py
│   ├── lint.py
│   ├── lint_js.py
│   ├── validate_wcag.py
│   ├── test_components.py
│   └── pipeline.py
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/
│       ├── ci.yml
│       └── deploy-dev.yml
├── run.py                  # Single CLI entry point
├── requirements.txt        # Python deps only (jinja2, pytest, ruff)
└── ruff.toml
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
cd wasm && cargo test
```

### Web Components (pytest)
```bash
python run.py test
# or directly:
pytest tests/ -v
```

### WCAG Validation (after build)
```bash
python run.py validate
```

---

## License

MIT — see [LICENSE](LICENSE).