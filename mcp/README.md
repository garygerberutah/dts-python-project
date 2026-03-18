# MCP Server Framework

Copyright 2026 by GuidoGerb Publishing, LLC

## Overview

A Python framework for building and publishing [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) servers. Supports running locally over **stdio** or **HTTP**, and deploying to **AWS Lambda** behind API Gateway.

Zero external dependencies — built entirely with Python's standard library.

## Architecture

```
mcp/
├── protocol/           # MCP protocol types + JSON-RPC 2.0
│   ├── types.py        # Tool, Resource, Prompt dataclasses
│   ├── jsonrpc.py      # Message parsing and serialization
│   └── errors.py       # Standard error codes
├── server/             # Server core
│   ├── base.py         # McpServer — decorator-based API
│   ├── registry.py     # Tool/Resource/Prompt registry
│   └── handler.py      # JSON-RPC method dispatcher
├── transport/          # Transport implementations
│   ├── stdio.py        # stdin/stdout (local)
│   ├── http.py         # Streamable HTTP (localhost dev)
│   └── aws_lambda.py   # AWS Lambda + API Gateway
├── deploy/             # Deployment utilities
│   └── __init__.py     # Lambda zip packaging
└── servers/            # Server implementations
    ├── example.py      # Example server with tools/resources/prompts
    └── example_lambda.py  # Lambda entry point for example server
```

## Quick Start

### 1. Define a Server

```python
from mcp import McpServer

server = McpServer(name="my-server", version="1.0.0")

@server.tool(description="Add two numbers")
def add(a: int, b: int) -> str:
    import json
    return json.dumps({"result": a + b})

@server.resource(uri="config://app", description="App config")
def app_config() -> str:
    return '{"debug": false}'

@server.prompt(description="Greet someone")
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### 2. Run Locally

```bash
# stdio transport (pipe JSON-RPC messages via stdin)
python run.py mcp-serve

# HTTP transport on localhost
python run.py mcp-serve --http --port 3000

# Then POST JSON-RPC to http://127.0.0.1:3000/mcp
```

### 3. Deploy to AWS

```bash
# Package for Lambda
python run.py mcp-package
# → dist/mcp-lambda.zip

# Deploy infrastructure
cd infra/mcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### 4. Run Tests

```bash
python run.py mcp-test
```

## Protocol

Implements the **MCP 2024-11-05** specification over JSON-RPC 2.0.

### Supported Methods

| Method | Description |
|--------|-------------|
| `initialize` | Capability negotiation |
| `ping` | Keepalive |
| `tools/list` | List available tools |
| `tools/call` | Execute a tool |
| `resources/list` | List available resources |
| `resources/read` | Read a resource |
| `prompts/list` | List available prompts |
| `prompts/get` | Render a prompt |

### Transports

| Transport | Use Case | Command |
|-----------|----------|---------|
| **stdio** | Local tool invocation by IDE/CLI | `python run.py mcp-serve` |
| **HTTP** | Local development & testing | `python run.py mcp-serve --http` |
| **Lambda** | Production on AWS | `python run.py mcp-package` + Terraform |

## Creating a New Server

1. Create a module in `mcp/servers/`:

```python
# mcp/servers/my_server.py
from mcp import McpServer

server = McpServer(name="my-server", version="1.0.0")

@server.tool(description="My custom tool")
def my_tool(input: str) -> str:
    return f"Processed: {input}"
```

2. Create a Lambda entry point:

```python
# mcp/servers/my_server_lambda.py
import os
from mcp.servers.my_server import server
from mcp.transport.aws_lambda import create_lambda_handler

_allowed_origins = [
    o.strip()
    for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
handler = create_lambda_handler(server, allowed_origins=_allowed_origins)
```

3. Update the `--server` option in `scripts/mcp/serve_mcp.py` to add your server.

## AWS Infrastructure

Terraform files in `infra/mcp/`:

| File | Purpose |
|------|---------|
| `main.tf` | Provider, backend, data sources |
| `variables.tf` | Input variables |
| `lambda.tf` | Lambda function + IAM + CloudWatch |
| `api-gateway.tf` | HTTP API + routes + access logging |
| `outputs.tf` | Exported endpoint URL + ARNs |

### Security

- Lambda IAM: least-privilege (CloudWatch Logs only)
- API Gateway: CORS whitelist, access logging enabled
- Response headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, HSTS
- No secrets in Terraform — use `terraform.tfvars` (gitignored)

## CLI Commands

```bash
python run.py mcp-serve                     # stdio transport
python run.py mcp-serve --http              # HTTP on port 3000
python run.py mcp-serve --http --port 8090  # HTTP on custom port
python run.py mcp-package                   # Create Lambda zip
python run.py mcp-test                      # Run MCP tests
```
