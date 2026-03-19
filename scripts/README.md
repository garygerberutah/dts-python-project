<!-- Copyright 2026 by DTS, The State of Utah -->

# scripts/ — Python Toolchain

All build, lint, format, test, validation, and deployment automation for the
project. Python is the **only** scripting language in the toolchain — no
Node.js, no npm, no JS-ecosystem tools.

These scripts **never ship** — they run on the developer machine only. The
`dist/` directory is the sole deployment artefact.

## Directory Layout

```
scripts/
├── __init__.py              # Package marker
├── build_all.py             # Master automation pipeline (13 stages)
├── api/                     # API build tooling (placeholder)
│   └── __init__.py
├── blockchain/              # SBOM generation, blockchain ledger, PostgreSQL storage
│   ├── __init__.py
│   ├── generate_sbom.py     # Build SBOM manifest from git-tracked files
│   ├── sbom.py              # Append-only blockchain with proof-of-work
│   ├── db.py                # PostgreSQL storage and SQL export
│   ├── sbom.json            # Current SBOM manifest (generated)
│   ├── chain.json           # Current blockchain state (generated)
│   └── README.md
├── ui/                      # UI build, lint, format, test, validate, serve
│   ├── __init__.py
│   ├── build.py             # WASM compile + Jinja2 render + asset copy
│   ├── clean.py             # Remove dist/ artefacts
│   ├── format_code.py       # rustfmt + ruff format
│   ├── lint.py              # ruff check + cargo clippy + JS linter
│   ├── lint_js.py           # Python-based JavaScript linter
│   ├── name_mime_type.py    # Rename assets to camelCase-<sha256>.ext
│   ├── serve.py             # Local HTTP dev server from dist/
│   ├── test_components.py   # Run pytest suites for Web Components
│   ├── validate_assets.py   # Asset naming + SHA-256 hash validation
│   ├── validate_copyright.py    # Copyright notice enforcement
│   ├── validate_mime_type_content.py  # Binary file mime-type validation
│   ├── validate_wcag.py     # WCAG 2.1 Level AA accessibility checks
│   └── README.md
└── util/                    # Standalone utility scripts (not in pipeline)
    ├── __init__.py
    ├── add_guidogerb_submodules.py  # Sync GitHub org submodules
    ├── list_all_guidogerb_repos.py  # Fetch repo listing from GitHub
    ├── model-downloader.py          # Stream ML models to S3
    ├── scrape_directory_listing.py  # Recursive directory → CSV
    └── README.md
```

## Master Pipeline

`build_all.py` orchestrates all stages in strict order with **fail-fast**
semantics — the first failure aborts the entire pipeline.

| Stage | Name                   | Script                              | CLI Command                      |
|------:|------------------------|-------------------------------------|----------------------------------|
|     1 | Test (global)          | pytest `tests/`                     | `python run.py test`             |
|     2 | Format                 | `format_code.py`                    | `python run.py format`           |
|     3 | Lint                   | `lint.py`                           | `python run.py lint`             |
|     4 | Validate (copyright)   | `validate_copyright.py`             | `python run.py validate-copyright` |
|     5 | Validate (assets)      | `validate_assets.py`                | —                                |
|     6 | Validate (mime-type)   | `validate_mime_type_content.py`     | `python run.py validate-mime`    |
|     7 | Clean                  | `clean.py`                          | `python run.py clean`            |
|     8 | Build                  | `build.py`                          | `python run.py build`            |
|     9 | Validate (WCAG 2.1)   | `validate_wcag.py`                  | `python run.py validate`         |
|    10 | Test (Web Components)  | `test_components.py`                | `python run.py test`             |
|    11 | Validate (SBOM-DB)     | `db.validate_sbom_db_sync()`        | —                                |
|    12 | SBOM (blockchain)      | `generate_sbom.py` + `sbom.py` + `db.py` | `python run.py sbom`       |
|    13 | Deploy                 | `git add -A && commit && push`      | `python run.py pipeline`         |

Stages 1–11 must pass before any git commit is allowed. Stage 13 is skipped
with `--skip-deploy`.

## Quick Reference

```bash
python run.py pipeline --skip-deploy   # Full pipeline (skip git push)
python run.py pipeline                 # Full pipeline + deploy
python run.py build                    # WASM + Jinja2 + assets → dist/
python run.py test                     # pytest (all test suites)
python run.py format                   # rustfmt + ruff format
python run.py lint                     # ruff check + clippy + JS lint
python run.py validate                 # WCAG 2.1 on dist/ HTML
python run.py validate-copyright       # Copyright headers
python run.py validate-copyright --fix # Auto-insert missing copyright
python run.py validate-mime            # Binary mime-type encoding
python run.py serve                    # Dev server on localhost:8080
python run.py clean                    # Delete dist/ and wasm/pkg/
python run.py sbom                     # Generate SBOM + blockchain
python run.py sbom-db                  # Create PostgreSQL table
python run.py setup                    # Install pre-commit hooks
```

## Script Conventions

- Every script exposes `main() -> int` (0 = success, 1 = failure).
- Shared subprocess runner: `_run(cmd, cwd, label) -> bool`.
- Project root: `ROOT = Path(__file__).resolve().parent.parent`.
- **No graceful skipping** — missing tools or empty directories cause hard
  failures, never silent passes.
- Every `.py` file starts with `Copyright 2026 by DTS, The State of Utah`.

## Dependencies

All Python — installed via `pip install -r requirements.txt`:

| Package            | Purpose                          |
|--------------------|----------------------------------|
| jinja2 ≥ 3.1.4    | Build-time HTML template engine  |
| pre-commit ≥ 3.7.0| Git hook framework               |
| psycopg2-binary ≥ 2.9.0 | PostgreSQL database driver |
| pytest ≥ 8.0.0    | Test framework                   |
| ruff ≥ 0.4.0      | Python formatter and linter      |

External tools (manual install):

| Tool       | Purpose                                |
|------------|----------------------------------------|
| rustfmt    | Rust code formatter (via `rustup`)     |
| cargo      | Rust build system                      |
| clippy     | Rust linter (via `rustup component`)   |
| wasm-pack  | Compile Rust to WebAssembly            |

## Filename Protection

**Never rename or move** any file in `scripts/` without explicit user
permission. The pipeline, `run.py`, and import paths all depend on the current
filenames.
