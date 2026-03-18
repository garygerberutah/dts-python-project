<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# Scripts

Python-only toolchain — build, lint, format, test, validate, and deploy.

No Node.js, npm, or JS-ecosystem tools. Python is the only scripting language.

## Structure

```
scripts/
├── build_all.py               # Master pipeline (12 stages, fail-fast)
├── ui/
│   ├── build.py               # WASM compile + Jinja2 render + asset copy → dist/
│   ├── clean.py               # Remove dist/ and wasm/pkg/
│   ├── serve.py               # Local HTTP dev server (port 8080)
│   ├── format_code.py         # rustfmt + ruff format
│   ├── lint.py                # ruff check + cargo clippy + JS linter
│   ├── lint_js.py             # Python-based JavaScript linter (eqeqeq, no-var, etc.)
│   ├── validate_wcag.py       # WCAG 2.1 Level AA HTML validator
│   ├── validate_copyright.py  # Copyright notice checker for all source files
│   ├── validate_assets.py     # Asset naming convention validator
│   ├── validate_mime_type_content.py  # Binary file mime-type validator
│   ├── name_mime_type.py      # Mime-type detection utilities
│   └── test_components.py     # pytest test runner (component + toolchain tests)
├── blockchain/
│   ├── sbom.py                # Append-only blockchain with SHA-256 + proof-of-work
│   ├── generate_sbom.py       # SBOM manifest generator (git ls-files → SHA-256)
│   ├── db.py                  # PostgreSQL SBOM version storage
│   ├── chain.json             # Blockchain data (append-only)
│   └── sbom.json              # Generated SBOM manifest
├── api/                       # API deployment scripts (placeholder)
└── util/
    ├── add_guidogerb_submodules.py    # Git submodule management
    ├── list_all_guidogerb_repos.py    # Repository listing utility
    ├── model-downloader.py            # ML model download utility
    └── scrape_directory_listing.py    # Directory listing scraper
```

## Pipeline Stages

All stages are fail-fast — the first failure aborts the pipeline.

| # | Stage | Script |
|---|-------|--------|
| 1 | Test (global) | `test_components.py` |
| 2 | Format | `format_code.py` |
| 3 | Lint | `lint.py` |
| 4 | Validate (copyright) | `validate_copyright.py` |
| 5 | Validate (assets) | `validate_assets.py` |
| 6 | Validate (mime-type) | `validate_mime_type_content.py` |
| 7 | Clean | `clean.py` |
| 8 | Build | `build.py` |
| 9 | Validate (WCAG 2.1) | `validate_wcag.py` |
| 10 | Test (components) | `test_components.py` |
| 11 | SBOM (blockchain) | `generate_sbom.py` + `sbom.py` + `db.py` |
| 12 | Deploy | `build_all.py` (git commit + push) |
