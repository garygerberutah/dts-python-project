---
applyTo: "tests/**/*.py"
description: "Use when writing or editing pytest component tests. Covers source-analysis fixtures, template extraction, and assertion patterns."
---
# Component Test Standards

## Copyright
- Every test `.py` file must contain `Copyright 2026 by DTS, The State of Utah` in the module docstring or a `#` comment at the top

## Missing Python Dependencies
- If a test fails with `ModuleNotFoundError` or `ImportError`, **ask the user for permission** before adding the missing package to `requirements.txt`, then run `pip install -r requirements.txt` and retry

## Approach
- Tests verify component JS **source code** — no browser, no DOM engine, no JS runtime
- Parse source text and extracted Shadow DOM templates via fixtures in `conftest.py`
- Test structure, patterns, and accessibility attributes — not runtime behavior

## Fixtures (from conftest.py)
- `app_root_source` / `app_root_template` — raw source / extracted innerHTML template
- `app_header_source` / `app_header_template`
- `app_viewer_source` / `app_viewer_template`

## What to Test
- Class extends `HTMLElement`
- `attachShadow({ mode: "open" })` present
- `customElements.define("tag-name", ...)` registers component
- `export { ClassName }` at module level
- ARIA attributes in template: `role`, `aria-label`, `aria-live`, `aria-current`
- Event patterns: `CustomEvent`, `bubbles: true`, `composed: true`, `once: true`
- No forbidden patterns: `var `, `==` (without `===`), `console.log`

## What NOT to Test
- Private `#fields` directly — they're inaccessible; test through source grep
- Runtime rendering — no DOM engine available
- WebGL output — no GPU in test environment

## Binary Content Rule
- No base64 data URIs or inline binary encodings in test source files — reference assets by path
- Binary test fixtures (`.png`, `.jpg`, etc.) may be versioned if their content matches the extension's mime-type
- `application/octet-stream` and opaque binary blobs are forbidden in git
