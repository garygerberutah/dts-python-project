<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# tests/ — Test Suites

All project tests, run via **pytest**. No browser, no DOM engine, no JS
runtime — tests verify source code structure and toolchain correctness through
Python-only analysis.

## Directory Layout

```
tests/
├── __init__.py                        # Package marker
├── conftest.py                        # Shared fixtures (tmp trees, sample files)
├── test_all.py                        # Meta-runner for all test suites
├── test_db.py                         # PostgreSQL storage & SQL export
├── test_format.py                     # Code formatter verification
├── test_lint.py                       # JavaScript linter rules
├── test_sbom.py                       # SBOM manifest integrity
├── test_validate_assets.py            # Asset naming & SHA-256 hashes
├── test_validate_copyright.py         # Copyright notice enforcement
├── test_validate_mime_type_content.py # Binary file mime-type encoding
├── test_validate_wcag.py              # WCAG 2.1 accessibility parser
├── api/                               # API test suite (placeholder)
│   ├── __init__.py
│   └── README.md
└── ui/                                # Web Component source-analysis tests
    ├── __init__.py
    ├── conftest.py                    # Component source & template fixtures
    ├── test_app_3d_viewer.py          # app-3d-viewer component tests
    ├── test_app_header.py             # app-header component tests
    ├── test_app_root.py               # app-root component tests
    └── README.md
```

## Running Tests

```bash
python run.py test               # Run all test suites (pipeline stages 1 & 10)
pytest tests/ -v                 # Run all tests directly with verbose output
pytest tests/ui/ -v              # Web Component tests only
pytest tests/test_db.py -v       # Database tests only
pytest tests/test_sbom.py -v     # SBOM manifest tests only
```

## Pipeline Integration

Tests run in **two** pipeline stages:

| Stage | Name                | Scope                        | Directory   |
|------:|---------------------|------------------------------|-------------|
|     1 | Test (global)       | Toolchain + infrastructure   | `tests/`    |
|    10 | Test (Web Components)| UI component source analysis| `tests/ui/` |

Both stages must pass before any commit is allowed. The pipeline is fail-fast —
the first test failure aborts everything.

## Test Suites

### Global Toolchain Tests (`tests/`)

These tests verify the Python toolchain scripts themselves — formatting, linting,
validation, database storage, and SBOM integrity. All database tests use mocked
connections (no live PostgreSQL required).

#### test_format.py

| Test                          | Verifies                                      |
|-------------------------------|-----------------------------------------------|
| `test_format_python_succeeds` | Project Python files are already formatted     |

#### test_lint.py

| Test                              | Verifies                                  |
|-----------------------------------|-------------------------------------------|
| `test_lint_js_clean_file`         | Valid JS produces no lint errors           |
| `test_lint_js_catches_double_equals` | `==` flagged (require `===`)           |
| `test_lint_js_catches_var`        | `var` declarations flagged                 |
| `test_lint_js_catches_console_log`| `console.log` flagged                      |
| `test_lint_js_allows_console_info`| `console.info` permitted                   |
| `test_lint_js_skips_test_files`   | `*.test.js` files excluded from lint       |
| `test_lint_js_skips_wasm_directory`| `wasm/` directory excluded                |
| `test_lint_js_empty_directory`    | Empty directory doesn't cause failure      |

#### test_validate_copyright.py

| Test                                        | Verifies                                |
|---------------------------------------------|-----------------------------------------|
| `test_validate_file_passes_with_correct_copyright` | Correct header passes            |
| `test_validate_returns_errors_for_file_without_copyright` | Missing header detected  |
| `test_validate_returns_empty_for_valid_tree`| Valid tree produces no errors            |
| `test_validate_returns_errors_for_missing_copyright` | Missing copyright detected    |
| `test_validate_fix_inserts_copyright`       | `--fix` inserts missing copyright        |
| `test_find_source_files_respects_extensions`| Only source extensions discovered        |
| `test_find_source_files_skips_git_dir`      | `.git/` directory excluded               |
| `test_comment_styles_cover_all_source_extensions` | All extensions have comment styles|
| `test_validate_fix_replaces_wrong_copyright`| `--fix` replaces incorrect copyright     |

#### test_validate_assets.py

| Test                                      | Verifies                                  |
|-------------------------------------------|-------------------------------------------|
| `test_sha256_of_file_correct`             | SHA-256 computation is accurate            |
| `test_naming_pattern_matches_valid_name`  | Pattern accepts `camelCase-hash.ext`       |
| `test_naming_pattern_rejects_invalid_name`| Pattern rejects invalid names              |
| `test_validate_file_valid_asset`          | Valid asset passes validation              |
| `test_validate_file_hash_mismatch`        | Hash mismatch detected                     |
| `test_find_asset_files_finds_images`      | Asset discovery finds image files          |
| `test_validate_empty_directory`           | Empty directory passes                     |
| `test_asset_extensions_include_common_formats` | Common formats covered              |

#### test_validate_mime_type_content.py

| Test                                      | Verifies                                  |
|-------------------------------------------|-------------------------------------------|
| `test_validators_cover_expected_extensions`| All required validators present           |
| `test_validate_valid_png`                 | Valid PNG accepted                          |
| `test_validate_invalid_png`               | Invalid PNG rejected                       |
| `test_validate_valid_json`                | Valid JSON accepted                         |
| `test_validate_invalid_json`              | Invalid JSON rejected                      |
| `test_find_binary_files_finds_images`     | Binary file discovery works                |
| `test_validate_empty_directory`           | Empty directory passes                     |
| `test_validate_valid_xml`                 | Valid XML accepted                          |
| `test_validate_invalid_xml`               | Invalid XML rejected                       |

#### test_validate_wcag.py

| Test                                         | Verifies                               |
|----------------------------------------------|-----------------------------------------|
| `test_validate_valid_html_no_violations`     | Compliant HTML passes                   |
| `test_validate_missing_lang_reports_violation`| Missing `lang` attribute detected      |
| `test_violation_dataclass_fields`            | `Violation` dataclass structure         |
| `test_wcag_parser_img_without_alt`           | Missing `alt` on `<img>` detected       |
| `test_wcag_parser_img_with_alt`              | Valid `alt` accepted                    |
| `test_validate_empty_directory`              | Empty directory passes                  |
| `test_wcag_parser_missing_title`             | Missing `<title>` detected              |

#### test_db.py

Tests are organised into five categories, all using mocked DB connections:

**Schema tests** — verify SQL string constants contain expected columns and
placeholders without connecting to a database.

| Test                                    | Verifies                                    |
|-----------------------------------------|---------------------------------------------|
| `test_create_table_includes_chain_content` | CREATE TABLE defines `chain_content` JSONB|
| `test_create_table_includes_sbom_content`  | CREATE TABLE defines `sbom_content` JSONB |
| `test_alter_adds_chain_column`          | ALTER TABLE adds `chain_content`             |
| `test_insert_sql_includes_chain_content`| INSERT includes both content columns         |
| `test_insert_sql_has_six_placeholders`  | INSERT has exactly 6 `%s` placeholders       |

**store_sbom tests** — verify insertion logic with mocked cursors.

| Test                                         | Verifies                              |
|----------------------------------------------|---------------------------------------|
| `test_store_sbom_passes_chain_data`          | Chain data sent as JSON parameter     |
| `test_store_sbom_defaults_chain_to_empty_list`| Missing chain defaults to `[]`       |

**SQL export tests** — verify file generation with mocked query results.

| Test                                    | Verifies                                    |
|-----------------------------------------|---------------------------------------------|
| `test_export_sbom_version_sql_creates_file` | `.sql` file written with INSERTs        |
| `test_export_sql_escapes_single_quotes` | Single quotes doubled for SQL safety         |
| `test_export_sql_empty_table`           | Empty table produces header-only file        |

**Infrastructure tests** — verify Docker Compose and init SQL exist on disk.

| Test                        | Verifies                                          |
|-----------------------------|---------------------------------------------------|
| `test_docker_compose_exists`| `docker-compose.yml` present                      |
| `test_init_sql_exists`      | `001-create-tables.sql` present                   |
| `test_init_sql_matches_schema` | Init SQL contains expected column names        |

**Connection fallback tests** — verify the 5432 → 5433 → Docker strategy.

| Test                                       | Verifies                               |
|--------------------------------------------|-----------------------------------------|
| `test_connect_tries_5432_first`            | `localhost:5432` tried first            |
| `test_connect_tries_gateway_then_localhost` | WSL2 gateway tried before localhost    |
| `test_connect_falls_back_to_5433`          | Port 5433 used when 5432 unavailable   |
| `test_connect_starts_docker_when_both_fail`| Docker started when both ports fail    |

**SBOM-DB sync tests** — verify SQL export ↔ DB row count validation.

| Test                                   | Verifies                                     |
|----------------------------------------|----------------------------------------------|
| `test_validate_sync_empty_db_no_files` | Empty DB + no exports = pass                  |
| `test_validate_sync_db_rows_no_files`  | DB rows with no exports = error               |
| `test_validate_sync_counts_match`      | Matching counts = pass                        |
| `test_validate_sync_db_exceeds_exports`| More DB rows than INSERTs = error             |
| `test_validate_sync_picks_best_file`   | Multiple files — best match used              |

#### test_sbom.py

| Test                                 | Verifies                                       |
|--------------------------------------|-------------------------------------------------|
| `test_sbom_has_valid_structure`      | SBOM JSON has required top-level keys           |
| `test_sbom_files_match_git_tracked`  | SBOM entries match `git ls-files` output        |
| `test_sbom_sha256_hashes_correct`    | Every SHA-256 matches actual file content       |
| `test_sbom_file_count_matches`       | `file_count` matches entries array length       |
| `test_sbom_entries_have_required_fields` | Every entry has `path` and `sha256`         |

## Shared Fixtures (`conftest.py`)

The root `tests/conftest.py` provides reusable fixtures for toolchain tests:

| Fixture                    | Description                                       |
|----------------------------|---------------------------------------------------|
| `tmp_tree(tmp_path)`       | Minimal project tree with `COPYRIGHT` file        |
| `tmp_py_file(tmp_tree)`    | Python file with correct copyright                |
| `tmp_js_file(tmp_tree)`    | JS file with correct copyright                    |
| `tmp_js_file_no_copyright` | JS file without copyright (for negative tests)    |
| `scripts_dir()`            | Path to the `scripts/` directory                  |
| `valid_png_bytes()`        | 8-byte PNG signature for mime-type tests          |
| `valid_json_file(tmp_tree)`| Valid JSON file on disk                           |
| `sample_html(tmp_path)`    | Minimal WCAG-compliant HTML file                  |
| `sample_html_no_lang`      | HTML file missing `lang` attribute                |

## Testing Philosophy

- **Source analysis, not runtime** — tests parse JavaScript source and Shadow
  DOM templates as text. No browser, no DOM engine, no JS runtime.
- **Mocked infrastructure** — database tests use `unittest.mock.patch` for all
  connections. No live PostgreSQL is required.
- **Deterministic** — no network calls, no timing dependencies, no random data.
- **Fast** — the full suite runs in ~1.5 seconds.
