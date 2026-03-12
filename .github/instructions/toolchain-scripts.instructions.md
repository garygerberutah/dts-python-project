---
applyTo: "scripts/**/*.py"
description: "Use when editing Python toolchain scripts (build, lint, format, test, validate, pipeline). Covers subprocess patterns, fail-fast, and build/app separation."
---
# Toolchain Script Standards

## Copyright
- Every `.py` script must contain `Copyright 2026 by GuidoGerb Publishing, LLC` in the module docstring or a `#` comment at the top

## Core Principle
Python is **build tooling only** — it never ships, never runs at request time, never appears in `dist/`.

## Patterns
- Each script exposes a `main() -> int` entry point (0 = success, 1 = failure)
- Shared runner: `_run(cmd, cwd, label) -> bool` for subprocess calls
- Pipeline uses fail-fast: first `False` return aborts everything
- `ROOT = Path(__file__).resolve().parent.parent` for project root

## Build Script
- 3 stages: WASM compile → Jinja2 render → asset copy
- `StrictUndefined` for templates — crash on typos, never render blank
- Exclude `*.test.js` from `dist/` via `shutil.ignore_patterns`

## Pre-Commit Requirement
- All format, lint, validation, clean, build, and test scripts must run and pass before committing
- Use `python run.py pipeline --skip-deploy` to run all stages
- Commits are rejected by the pre-commit hook if any stage fails

## Forbidden
- **Never** use `--no-verify` or `-n` on any git command — never bypass pre-commit hooks; fix the code instead
- Never call `npx`, `node`, `npm`, or any JS-ecosystem tool
- Never import jinja2 outside build scripts
- Never add Node.js dependencies — Python is the only scripting language
- No base64 data URIs or inline binary encodings in Python source files — reference assets by path
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
- `application/octet-stream` and opaque binary blobs are forbidden in git
