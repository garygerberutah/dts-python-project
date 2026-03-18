"""
package_mcp.py — package an MCP server for AWS Lambda deployment.

Copyright 2026 by GuidoGerb Publishing, LLC

Creates a zip archive containing the mcp/ package ready for Lambda.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    """Package the MCP server for Lambda deployment."""
    from mcp.deploy import package_lambda

    output = ROOT / "dist" / "mcp-lambda.zip"
    result = package_lambda(output_path=output)
    print(f"[mcp:package] Created {result} ({result.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
