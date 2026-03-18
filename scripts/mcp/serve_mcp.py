"""
serve_mcp.py — run an MCP server locally.

Copyright 2026 by GuidoGerb Publishing, LLC

Usage:
    python run.py mcp-serve                     # stdio
    python run.py mcp-serve --http              # HTTP on port 3000
    python run.py mcp-serve --http --port 8090  # HTTP on port 8090
"""

from __future__ import annotations

import argparse
import sys


def main(args: list[str] | None = None) -> int:
    """Run an MCP server locally."""
    parser = argparse.ArgumentParser(description="Run an MCP server locally")
    parser.add_argument(
        "--server",
        default="example",
        help="Server module to run (default: example)",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport instead of stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="HTTP port (default: 3000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind address (default: 127.0.0.1)",
    )
    parsed = parser.parse_args(args)

    transport = "http" if parsed.http else "stdio"

    if parsed.server == "example":
        from mcp.servers.example import server
    else:
        print(f"[mcp:serve] Unknown server: {parsed.server}", file=sys.stderr)
        return 1

    server.run(transport=transport, host=parsed.host, port=parsed.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
