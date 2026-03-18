<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# Tests

pytest test suites — source-analysis only, no browser or JS runtime needed.

## Structure

```
tests/
├── conftest.py                      # Global test fixtures
├── test_all.py                      # Smoke test (all imports resolve)
├── test_format.py                   # Format script tests
├── test_format_full.py              # Extended format coverage tests
├── test_lint.py                     # Lint script tests
├── test_lint_full.py                # Extended lint coverage tests
├── test_build.py                    # Build script tests (templates, assets, WASM)
├── test_build_all.py                # Master pipeline tests
├── test_clean.py                    # Clean script tests
├── test_serve.py                    # Dev server tests
├── test_test_components.py          # Test runner script tests
├── test_validate_assets.py          # Asset validation tests
├── test_validate_copyright.py       # Copyright validation tests
├── test_validate_mime_type_content.py  # Mime-type validation tests
├── test_validate_wcag.py            # WCAG 2.1 validation tests
├── test_blockchain_sbom.py          # Blockchain (append-only ledger) tests
├── test_blockchain_generate.py      # SBOM generation tests
├── test_blockchain_db.py            # PostgreSQL SBOM storage tests
└── ui/
    ├── conftest.py                  # Source-analysis fixtures (component_source, etc.)
    ├── test_app_root.py             # app-root Web Component tests
    ├── test_app_header.py           # app-header Web Component tests
    └── test_app_3d_viewer.py        # app-3d-viewer Web Component tests
```

## Running Tests

```bash
python run.py test                           # All tests via pipeline runner
pytest tests/ tests/ui/ -v                   # Direct pytest invocation
pytest tests/ tests/ui/ --cov=scripts        # With coverage report
```

## Test Approach

Tests verify component and script behavior through **source analysis** — parsing
JavaScript source files and Python script logic without executing them in a browser.
Web Component tests check Shadow DOM structure, ARIA attributes, event patterns,
and WASM integration by reading the source files directly.
