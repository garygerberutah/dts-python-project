# Copyright 2026 by GuidoGerb Publishing, LLC
"""Example MCP server — demonstrates tools, resources, and prompts.

Run locally::

    python -m mcp.servers.example            # stdio
    python -m mcp.servers.example --http 3000 # HTTP on port 3000
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime

from mcp import McpServer

server = McpServer(name="ggp3d-example", version="0.1.0")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(description="Add two numbers")
def add(a: float, b: float) -> str:
    """Add two numbers and return the result."""
    return json.dumps({"result": a + b})


@server.tool(description="Compute the SHA-256 hash of a string")
def sha256(text: str) -> str:
    """Return the hex-encoded SHA-256 hash of the input text."""
    import hashlib

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return json.dumps({"hash": digest})


@server.tool(description="Calculate the distance between two 3D points")
def distance_3d(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> str:
    """Euclidean distance between (x1,y1,z1) and (x2,y2,z2)."""
    d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    return json.dumps({"distance": d})


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@server.resource(uri="info://server", description="Server metadata", mime_type="application/json")
def server_info() -> str:
    """Return server name, version, and current UTC time."""
    return json.dumps(
        {
            "name": server.name,
            "version": server.version,
            "utc_time": datetime.now(tz=UTC).isoformat(),
        }
    )


@server.resource(uri="info://capabilities", description="Server capabilities")
def capabilities() -> str:
    """Return a human-readable summary of what this server can do."""
    tools = server.registry.list_tools()
    resources = server.registry.list_resources()
    prompts = server.registry.list_prompts()
    lines = [
        f"Tools ({len(tools)}): " + ", ".join(t["name"] for t in tools),
        f"Resources ({len(resources)}): " + ", ".join(r["uri"] for r in resources),
        f"Prompts ({len(prompts)}): " + ", ".join(p["name"] for p in prompts),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@server.prompt(description="Summarize a topic for a given audience")
def summarize(topic: str, audience: str = "general") -> str:
    """Generate a summarization prompt."""
    return (
        f"Please summarize the topic '{topic}' in a way that is "
        f"accessible to a {audience} audience.  Keep it concise "
        f"and factual."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for the example server."""
    transport = "stdio"
    port = 3000

    args = sys.argv[1:]
    if "--http" in args:
        transport = "http"
        idx = args.index("--http")
        if idx + 1 < len(args):
            port = int(args[idx + 1])

    server.run(transport=transport, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
