<!-- Copyright 2026 by GuidoGerb Publishing, LLC -->

# scripts/ui/ — UI Build & Validation Tools

Python scripts that build, lint, format, test, validate, and serve the
browser-based application. Every script in this package is invoked by the
master pipeline (`scripts/build_all.py`) or directly through `run.py`.

## Modules

### build.py — Build Pipeline (Stage 8)

Compiles the Rust WASM module, renders Jinja2 templates into static HTML, and
copies frontend assets to `dist/`.

Three sequential sub-stages:

1. **WASM compile** — runs `wasm-pack build --target web --release` on
   `ui/src/wasm/`, producing `pkg/` with `.wasm` and JS bindings.
2. **Jinja2 render** — loads `ui/src/templates/*.j2` with `StrictUndefined`,
   injects context variables (`app_title`, `app_description`, `lang`,
   `favicon_filename`), and writes `.html` to `dist/`.
3. **Asset copy** — copies JS components, SCSS-compiled CSS, WASM output, and
   static images to `dist/`, excluding `*.test.js`.

```bash
python run.py build
```

**Key functions:**

| Function                 | Description                                    |
|--------------------------|------------------------------------------------|
| `build_wasm()`           | Run `wasm-pack` on the Rust crate              |
| `render_templates(…)`    | Render Jinja2 templates → `dist/`              |
| `copy_assets()`          | Copy JS/CSS/WASM/static assets → `dist/`       |
| `build()`                | Orchestrate all three sub-stages               |
| `_load_site_config()`    | Parse `resources/config/site.json` for metadata|

---

### clean.py — Artefact Removal (Stage 7)

Deletes `dist/` and `ui/src/wasm/pkg/` directories to ensure a fresh build.

```bash
python run.py clean
```

---

### format_code.py — Code Formatting (Stage 2)

Auto-formats source code using two formatters:

| Language | Formatter       | Scope                       |
|----------|-----------------|-----------------------------|
| Rust     | `cargo fmt`     | `ui/src/wasm/`              |
| Python   | `ruff format`   | `scripts/`, `tests/`, `run.py` |

Both must succeed for the stage to pass. Missing tools cause hard failure.

```bash
python run.py format
```

---

### lint.py — Static Analysis (Stage 3)

Runs three linters in sequence — all must pass:

| Linter           | Language   | Key Flags                                   |
|------------------|------------|---------------------------------------------|
| `ruff check`     | Python     | Rules E, F, W, I, UP, B; double quotes      |
| `cargo clippy`   | Rust       | `-D warnings` (deny all warnings)           |
| `lint_js_files()`| JavaScript | eqeqeq, no-var, no-console.log              |

```bash
python run.py lint
```

---

### lint_js.py — JavaScript Linter

A lightweight, Python-based JS linter that enforces coding standards without
requiring Node.js or ESLint. Scans all `.js` files under `ui/src/`, excluding
`*.test.js` and the `wasm/` directory.

**Rules enforced:**

| Rule          | Description                                             |
|---------------|---------------------------------------------------------|
| `eqeqeq`     | Forbid `==` and `!=` (require `===` and `!==`)         |
| `no-var`      | Forbid `var` declarations (use `const`/`let`)           |
| `no-console`  | Forbid `console.log` (allow `info`, `warn`, `error`)   |

String literals are stripped before analysis to avoid false positives.

---

### validate_copyright.py — Copyright Enforcement (Stage 4)

Verifies every source file contains `Copyright 2026 by GuidoGerb Publishing,
LLC` in a comment near the top. Supports auto-fix mode.

**Supported extensions:** `.py`, `.js`, `.rs`, `.css`, `.html`, `.j2`, `.toml`,
`.cfg`, `.yml`, `.yaml`, `.tf`, `.scss`, `.sh`

**Skipped directories:** `dist/`, `.git/`, `node_modules/`, `__pycache__/`,
`venv/`, `.pytest_cache/`, `.ruff_cache/`

```bash
python run.py validate-copyright          # Check only
python run.py validate-copyright --fix    # Auto-insert/replace
```

---

### validate_wcag.py — WCAG 2.1 Accessibility Validation (Stage 9)

Parses compiled HTML in `dist/` and checks for WCAG 2.1 Level AA compliance
using a custom `HTMLParser` subclass. No external tools required.

**Rules checked:**

| WCAG SC  | Rule                      | Check                                       |
|----------|---------------------------|---------------------------------------------|
| 1.1.1    | Non-text Content          | `<img>` must have non-empty `alt`           |
| 1.3.1    | Info & Relationships      | `<form>` inputs need `<label>`              |
| 2.4.2    | Page Titled               | Every page must have non-empty `<title>`    |
| 2.4.4    | Link Purpose              | `<a>` must have text or `aria-label`        |
| 3.1.1    | Language of Page          | `<html>` must have `lang` attribute         |
| 4.1.2    | Name, Role, Value         | Interactive elements need accessible names  |

```bash
python run.py validate
```

---

### validate_assets.py — Asset Hash Validation (Stage 5)

Validates that static resource files follow the naming convention
`camelCaseDescription-<sha256hex>.ext` and that embedded SHA-256 hashes match
actual file content.

```bash
# Runs as part of the pipeline (no standalone CLI command)
```

---

### validate_mime_type_content.py — Mime-Type Validation (Stage 6)

Validates that binary files contain data matching their extension's mime-type
encoding. Checks magic bytes, file signatures, and structural validity.

**Recognised mime-types:**

| Extension   | Mime-Type             | Validation Method          |
|-------------|-----------------------|----------------------------|
| `.png`      | image/png             | PNG signature (8 bytes)    |
| `.jpg`/`.jpeg` | image/jpeg         | JPEG SOI marker            |
| `.gif`      | image/gif             | GIF87a/GIF89a header       |
| `.svg`      | image/svg+xml         | XML with SVG content       |
| `.mp4`      | video/mp4             | ISOBMFF `ftyp` box         |
| `.mp3`      | audio/mpeg            | ID3 tag or sync word       |
| `.pdf`      | application/pdf       | `%PDF` magic number        |
| `.json`     | application/json      | Valid JSON syntax           |
| `.xml`      | application/xml       | Valid XML syntax            |

**Forbidden:** `application/octet-stream` and unmarked binary blobs.

```bash
python run.py validate-mime
```

---

### test_components.py — Web Component Test Runner (Stage 10)

Invokes pytest on the `tests/` directory to run all Web Component
source-analysis tests. Returns `True` only if all tests pass.

```bash
python run.py test
```

---

### serve.py — Development Server

Starts a local HTTP server from `dist/` with CORS headers and the
`application/wasm` mime-type for `.wasm` files. Not part of the pipeline.

```bash
python run.py serve           # Default port 8080
python run.py serve 3000      # Custom port
```

---

### name_mime_type.py — Asset Renamer (Utility)

Renames static resource files to match the naming convention
`<camelCaseDescription>-<sha256>.ext`. Not part of the automated pipeline.

```bash
python scripts/ui/name_mime_type.py                          # Scan all asset dirs
python scripts/ui/name_mime_type.py <filepath>               # Rename one file
python scripts/ui/name_mime_type.py <filepath> "description" # Rename with label
```
