# Copyright 2026 by GuidoGerb Publishing, LLC
"""Lambda entry point for the example MCP server.

Deploy this module as the Lambda handler.  Configure the handler
setting as ``mcp.servers.example_lambda.handler``.
"""

from __future__ import annotations

import os

from mcp.servers.example import server
from mcp.transport.aws_lambda import create_lambda_handler

_allowed_origins = [
    o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]

handler = create_lambda_handler(server, allowed_origins=_allowed_origins)
