# Project Guidelines

## Rules Over Convention

- **Changing any rule in this file or any instruction file requires explicit user permission every time** — never add, remove, or modify a rule without asking first

## Architecture

Two completely separate concerns. Never mix them.


### Application (ships to `dist/`, runs in the browser)

Pure HTML5 + vanilla JavaScript + Rust WebAssembly. Zero server-side logic.

| Layer | Tech | Key Files |
|-------|------|-----------|
| UI | Web Components (Shadow DOM, private `#fields`) | `frontend/components/` |
| Rendering | WebGL via vanilla JS | `app-3d-viewer.js` |
| Math engine | Rust → WASM via wasm-bindgen | `wasm/src/lib.rs` |
| Styles | Shadow DOM `<style>` + global reset | `frontend/styles/main.css` |

No frameworks, no libraries, no abstractions — hand-written HTML5 and ES modules only.
Python never appears in `dist/`. Jinja2 never appears in `dist/`. Nothing generated at runtime.

## Binary Content Rule
- Binary files **may** be versioned in git if they represent a recognized, inspectable mime-type:
  `image/png`, `image/jpeg`, `image/gif`, `image/svg+xml`, `video/mp4`, `audio/mpeg`,
  `application/pdf`, `application/json`, `application/xml`
- The file's binary content must match the encoding of its extension's mime-type (e.g., a `.png` must be valid PNG data)
- **Strictly forbidden** in git: `application/octet-stream` and any binary data not clearly associated with an inspectable mime-type
- Never commit opaque binary blobs, arbitrary byte streams, or files whose content cannot be visually inspected with standard tools
- Base64 data URIs and inline binary encodings in text source files are still forbidden — reference assets by path
- Build scripts may embed assets inline for production `dist/` output — but source stays clean

### Toolchain (developer machine only, never ships)

Python scripts that build, lint, test, and deploy the application.

| Tool | Tech | Key Files |
|------|------|-----------|
| Build | Jinja2 templates → static HTML, wasm-pack, asset copy | `scripts/build.py` |
| Lint | Python JS linter, cargo clippy, ruff | `scripts/lint.py`, `scripts/lint_js.py` |
| Format | rustfmt, ruff | `scripts/format_code.py` |
| Test | pytest source-analysis | `tests/` |
| Validate | WCAG 2.1 HTML parser | `scripts/validate_wcag.py` |
| Pipeline | Orchestrates all stages | `scripts/pipeline.py` |

No Node.js, no npm, no JS-ecosystem tools — Python is the only scripting language in the toolchain.

## Build and Test

```bash
python run.py pipeline --skip-deploy   # Full pipeline: format → lint → validate → clean → build → validate → test
python run.py build                    # WASM compile + Jinja2 render + asset copy → dist/
python run.py test                     # Component tests (pytest)
python run.py format                   # rustfmt, ruff
python run.py lint                     # Python JS linter, cargo clippy -D warnings, ruff check
python run.py validate                 # WCAG 2.1 Level AA on rendered HTML
python run.py validate-copyright       # Copyright notice in all source files
python run.py validate-mime            # Binary files match their mime-type encoding
cd wasm && cargo test                  # Rust unit tests
pip install -r requirements.txt        # Only Python deps needed
```

Pipeline is **fail-fast** — first failure aborts all subsequent stages.

## Pre-Commit Requirement

All of the following must run and pass before committing to the git repository:
1. **Format** — `python run.py format`
2. **Lint** — `python run.py lint`
3. **Validate (copyright)** — `python run.py validate-copyright`
4. **Validate (mime-type)** — `python run.py validate-mime`
5. **Clean + Build** — `python run.py build`
6. **Validate (WCAG)** — `python run.py validate`
7. **Test** — `python run.py test`

Or run `python run.py pipeline --skip-deploy` which executes all stages in order.

Hooks are managed by the [pre-commit](https://pre-commit.com/) framework.
After cloning, run once:

```bash
pip install -r requirements.txt
python run.py setup              # pre-commit install
```

The `.pre-commit-config.yaml` calls `python run.py pipeline --skip-deploy` as a local hook.
The `.githooks/pre-commit` script is the versioned fallback — commits are rejected if any stage fails.

**Never bypass the pre-commit hook.** The flags `--no-verify` and `-n` are strictly
forbidden on `git commit` and `git push`. If the hook fails, fix the code — never skip the check.

## Copyright Notice

Every source file must contain the contents of the `COPYRIGHT` file in a comment at the top:

```
Copyright 2026 by GuidoGerb Publishing, LLC
```

Use the appropriate comment syntax for each file type:
- Python: inside the module docstring or `#` comment
- JavaScript: inside a `/** */` or `//` block comment
- Rust: `//` comment
- CSS: `/* */` comment
- HTML/Jinja2: `<!-- -->` comment
- TOML/YAML: `#` comment

## Banned Dependencies

- **No Node.js / npm / npx** — no `package.json`, no `node_modules`, no JS-ecosystem tools
- **No JS test frameworks** — no Jest, Vitest, Mocha, jsdom; tests are Python pytest
- **No JS build tools** — no Prettier, ESLint, Webpack, Vite, esbuild, Rollup
- **No 3rd-party JS libraries** — no lodash, jQuery, React, etc.; vanilla only
- **No external resources** — no CDN links, no Google Fonts, no remote CSS/JS/fonts/images; everything ships from `dist/`
- **No Python in the application** — Python never ships, never runs at request time, never serves templates
- **No server-side template rendering** — Jinja2 is a build tool; `dist/` is static files only

## Application Rules (HTML5 + JS + WASM)

### Browser-Native Only
- Every feature MUST use standard HTML5 / DOM / Web API — no polyfills, no shims, no compatibility layers
- CSS: hand-written only; system fonts via `font-family: system-ui, …`; no downloaded fonts, no icon fonts, no CSS frameworks
- JS: vanilla ES modules only; no transpilation, no bundling, no minification
- Images/icons: inline SVG or self-hosted assets in `dist/`; no CDN, no remote URLs
- Fonts: `system-ui` stack only — never load external font files
- **Zero network fetches for static resources** — everything the UI needs ships inside `dist/`

### JavaScript
- Files: kebab-case (`app-3d-viewer.js`)
- Components: extend `HTMLElement`, Shadow DOM `mode: "open"`, private `#fields` and `#methods()`
- Events: `CustomEvent` with `bubbles: true, composed: true` to cross shadow boundaries
- WASM handoff: `app-root` loads WASM and dispatches `wasm-ready`; children listen via `window.addEventListener("wasm-ready", …, { once: true })`
- `===` not `==`, `const`/`let` not `var`, no `console.log` (use `info`/`warn`/`error`)

### Rust (WASM)
- Expose types via `#[wasm_bindgen]`; return new instances (no in-place mutation)
- Optimize for size: `opt-level = "z"`, LTO enabled
- Column-major `Mat4`, standard `Vec3` — all `Clone + Copy + Debug + PartialEq`

### HTML
- Accessibility first: ARIA roles, labels, skip-to-content link, semantic HTML
- Shadow DOM queries only: `element.shadowRoot.querySelector()` — `document.querySelector()` cannot pierce shadow boundaries
- CSS isolation: component styles live inside Shadow DOM `<style>` blocks; global CSS is a minimal reset + CSS variables
- No `<link>` to external stylesheets, no `<script src="https://…">`, no remote `<img>` sources

### Client–Server Communication
- All HTTP interactions MUST be RESTful (GET, POST, PUT, DELETE) with JSON bodies
- No RPC-style endpoints, no GraphQL — strict REST resource semantics
- Validate all inputs server-side; never trust client data

### API Security
- All API requests use HTTPS in production; reject plain HTTP
- Authenticate every request — no anonymous write endpoints
- Rate-limit all endpoints; fail closed on auth errors (deny by default)
- Sanitize and validate all request parameters, headers, and body content server-side
- Never expose internal error details, stack traces, or database schema to the client
- Set strict response headers: `Content-Type`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- CORS: whitelist specific origins only; never use `Access-Control-Allow-Origin: *` in production

### WebSocket Rules
- WebSockets are **push-only for vetted plain text** — status updates, notifications
- **NEVER** send over WebSocket: SQL, binary blobs, executable scripts, HTML, serialized objects
- Server must sanitize/validate all outbound WebSocket messages before sending
- Client must treat all WebSocket data as untrusted display text
- Authenticate WebSocket connections at handshake; reject unauthenticated upgrades

## Toolchain Rules (Python only)

### Python
- Ruff rules: E, F, W, I, UP, B; double quotes
- The Python JS linter (`scripts/lint_js.py`) enforces `eqeqeq`, `no-var`, `no-console.log` on frontend JS

### Templates (build-time only)
- Jinja2 renders static HTML during `python run.py build` — never at request time
- `StrictUndefined` — undefined variables crash the build, never render blank
- `index.html.j2` extends `base.html.j2`; blocks: `title`, `body`, `scripts_extra`
- Context vars: `app_title`, `app_description`, `lang`
- Never pass user input into Jinja2 context variables
- Output lands in `dist/` as plain `.html` — serve as-is, no further processing

### Testing
- pytest + source-analysis fixtures in `tests/conftest.py`
- Tests parse component JS source files and verify structure, Shadow DOM patterns, and accessibility attributes
- No browser, no DOM engine, no JS runtime needed
- Test component behavior through source analysis, not internal state (`#private` fields are inaccessible)

## Script Filename Protection

- **Never rename or move** any file in `scripts/` without explicit user permission
- If a rename is truly necessary, explain the reason before making the change and wait for approval

## No Graceful Skipping

- Pipeline stages **must never skip gracefully** — if a required tool is missing, a directory is empty, or a resource is unavailable, the stage must **fail loudly** (`return False`, raise an exception, or `sys.exit(1)`)
- Never return `True` or silently pass when expected work cannot be performed
- A missing executable (e.g. `cargo`, `ruff`) is a hard failure, not a skip

## Pitfalls

- `StrictUndefined` means typos in template context variables crash the build
- `wasm-pack` must be installed separately (`curl` installer) — not in `requirements.txt`
- No `package.json` exists — **never** create one or suggest `npm install`
- `:root` CSS variables don't inherit into shadow trees unless explicitly opted in
- `dist/` is the only thing that runs — everything else is build tooling
- If a Python script fails with `ModuleNotFoundError` or `ImportError`, **ask the user for permission** before adding the missing package to `requirements.txt`, then run `pip install -r requirements.txt` and retry the failing command
