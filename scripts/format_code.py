"""
format_code.py — auto-formats all JS, Rust, Python, and HTML source files.

Runs:
  • prettier   — JS / HTML (via npx)
  • rustfmt    — Rust
  • ruff format — Python
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], cwd: Path | None = None, label: str = "") -> bool:
    """
    Run a subprocess command.
    Returns True on success, False on failure (does NOT raise).
    """
    print(f"  [format:{label}] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if result.returncode != 0:
        print(f"  [format:{label}] FAILED (exit {result.returncode})", file=sys.stderr)
        return False
    return True


def format_js() -> bool:
    """Format JS and HTML with Prettier."""
    return _run(
        [
            "npx",
            "--yes",
            "prettier",
            "--write",
            "frontend/**/*.js",
            "frontend/**/*.css",
            "templates/**/*.j2",
        ],
        cwd=ROOT,
        label="prettier",
    )


def format_rust() -> bool:
    """Format Rust source with rustfmt via cargo fmt."""
    return _run(["cargo", "fmt"], cwd=ROOT / "wasm", label="rustfmt")


def format_python() -> bool:
    """Format Python source with ruff."""
    return _run(
        ["ruff", "format", "scripts/", "run.py"],
        cwd=ROOT,
        label="ruff",
    )


def format_all() -> bool:
    """Run all formatters. Returns True only if every formatter succeeds."""
    results = [
        format_python(),
        format_rust(),
        format_js(),
    ]
    return all(results)


def main() -> int:
    print("[format] Formatting all source files…")
    ok = format_all()
    if ok:
        print("[format] All formatters passed.")
        return 0
    print("[format] One or more formatters FAILED.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
