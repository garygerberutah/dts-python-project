"""
lint.py — static analysis for JS, Rust, and Python.

Copyright 2026 by GuidoGerb Publishing, LLC

Runs:
  • ruff check  — Python
  • cargo clippy — Rust (strict)
  • lint_js      — JavaScript (Python-based)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _run(cmd: list[str], cwd: Path | None = None, label: str = "") -> bool:
    """Run a linting command. Returns True on success."""
    print(f"  [lint:{label}] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, text=True)
    except FileNotFoundError:
        print(
            f"  [lint:{label}] FAILED — '{cmd[0]}' not found. Install it and retry.",
            file=sys.stderr,
        )
        return False
    if result.returncode != 0:
        print(f"  [lint:{label}] FAILED (exit {result.returncode})", file=sys.stderr)
        return False
    return True


def lint_python() -> bool:
    """Run ruff check over Python sources."""
    return _run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--config",
            "resources/config/ruff.toml",
            "scripts/",
            "mcp/",
            "tests/mcp/",
            "run.py",
        ],
        cwd=ROOT,
        label="ruff",
    )


def lint_rust() -> bool:
    """Run cargo clippy with deny(warnings)."""
    return _run(
        [
            "cargo",
            "clippy",
            "--",
            "-D",
            "warnings",
        ],
        cwd=ROOT / "ui" / "src" / "wasm",
        label="clippy",
    )


def lint_js() -> bool:
    """Run the Python-based JS linter over frontend sources."""
    from scripts.ui.lint_js import lint_js_files

    print("  [lint:js] Running Python JS linter…")
    return lint_js_files(ROOT)


def lint_all() -> bool:
    """Run all linters. Returns True only if every linter passes."""
    results = [
        lint_python(),
        lint_rust(),
        lint_js(),
    ]
    return all(results)


def main() -> int:
    print("[lint] Running static analysis…")
    ok = lint_all()
    if ok:
        print("[lint] All linters passed.")
        return 0
    print("[lint] One or more linters FAILED.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
