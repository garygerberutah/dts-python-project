"""
lint.py — static analysis for JS (ESLint), Rust (Clippy), and Python (Ruff).

Runs:
  • ruff check  — Python
  • cargo clippy — Rust (strict)
  • eslint       — JavaScript (via npx)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], cwd: Path | None = None, label: str = "") -> bool:
    """Run a linting command. Returns True on success."""
    print(f"  [lint:{label}] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if result.returncode != 0:
        print(f"  [lint:{label}] FAILED (exit {result.returncode})", file=sys.stderr)
        return False
    return True


def lint_python() -> bool:
    """Run ruff check over Python sources."""
    return _run(
        ["ruff", "check", "scripts/", "run.py"],
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
        cwd=ROOT / "wasm",
        label="clippy",
    )


def lint_js() -> bool:
    """Run ESLint over frontend JavaScript sources."""
    return _run(
        [
            "npx",
            "--yes",
            "eslint",
            "frontend/",
            "--ext",
            ".js",
            "--max-warnings",
            "0",
        ],
        cwd=ROOT,
        label="eslint",
    )


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
