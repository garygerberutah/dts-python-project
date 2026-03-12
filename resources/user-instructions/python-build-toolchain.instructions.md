---
applyTo: ["scripts/**/*.py", "run.py", "build.py", "Makefile"]
description: "Use when writing or editing Python build scripts. Covers Python 3.12 toolchain patterns, subprocess handling, fail-fast pipelines, and banned JS tools."
---
# Python Build Toolchain Standards

## Core Principle
Python 3.12 is the sole build/scripting language. No Node.js, no npm, no Make (unless wrapping Python).

## Patterns
- Single CLI entry point: `python run.py <command>`
- Each script: `main() -> int` (0 success, 1 failure)
- Subprocess runner: `_run(cmd, cwd, label) -> bool`
- `ROOT = Path(__file__).resolve().parent.parent` for project root
- Pipeline stages are fail-fast — first failure aborts all subsequent stages

## Formatting & Linting
- **ruff** for Python formatting and linting (rules: E, F, W, I, UP, B; double quotes)
- **rustfmt** for Rust code
- **Custom Python linter** for JS static analysis (no ESLint/Prettier)
- **cargo clippy -D warnings** for Rust

## Build Steps (typical)
1. Format source → 2. Lint → 3. Clean → 4. Compile (WASM, SCSS, etc.) → 5. Validate → 6. Test → 7. Deploy

## Forbidden
- Never call `npx`, `node`, `npm`, or any JS-ecosystem CLI
- Never create `package.json` or `node_modules`
- Never use JS build tools (Webpack, Vite, esbuild, Rollup, Prettier, ESLint)
- No base64 data URIs or inline binary encodings in Python source files — reference assets by path
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
- `application/octet-stream` and opaque binary blobs are forbidden in git
