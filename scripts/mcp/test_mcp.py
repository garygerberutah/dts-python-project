"""
test_mcp.py — run MCP framework tests.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MCP_TESTS_DIR = ROOT / "tests" / "mcp"


def main() -> int:
    """Run all MCP tests via pytest."""
    if not MCP_TESTS_DIR.exists():
        print("[mcp:test] Test directory not found — FAILING.", file=sys.stderr)
        return 1
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(MCP_TESTS_DIR), "-v"],
        cwd=ROOT,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
