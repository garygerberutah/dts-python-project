# Copyright 2026 by GuidoGerb Publishing, LLC
"""Tests for mcp.servers.example — the example MCP server."""

from __future__ import annotations

import json

from mcp.servers.example import server
from mcp.transport.stdio import StdioTransport


class TestExampleTools:
    def test_add_tool(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "add", "arguments": {"a": 1.5, "b": 2.5}},
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        text = msg["result"]["content"][0]["text"]
        assert json.loads(text) == {"result": 4.0}

    def test_sha256_tool(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "sha256", "arguments": {"text": "hello"}},
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        text = msg["result"]["content"][0]["text"]
        result = json.loads(text)
        assert "hash" in result
        assert len(result["hash"]) == 64

    def test_distance_3d_tool(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "distance_3d",
                    "arguments": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0, "z2": 0},
                },
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        text = msg["result"]["content"][0]["text"]
        assert json.loads(text) == {"distance": 1.0}


class TestExampleResources:
    def test_server_info(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "info://server"},
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        content = msg["result"]["contents"][0]
        data = json.loads(content["text"])
        assert data["name"] == "ggp3d-example"

    def test_capabilities_resource(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {"uri": "info://capabilities"},
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        text = msg["result"]["contents"][0]["text"]
        assert "Tools" in text
        assert "Resources" in text


class TestExamplePrompts:
    def test_summarize_prompt(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "prompts/get",
                "params": {"name": "summarize", "arguments": {"topic": "AI"}},
            }
        )
        response = transport.process_one(raw)
        msg = json.loads(response)
        text = msg["result"]["messages"][0]["content"]["text"]
        assert "AI" in text


class TestExampleInitialize:
    def test_server_info(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        response = transport.process_one(raw)
        msg = json.loads(response)
        assert msg["result"]["serverInfo"]["name"] == "ggp3d-example"
        assert msg["result"]["serverInfo"]["version"] == "0.1.0"

    def test_all_capabilities_present(self) -> None:
        transport = StdioTransport(server.handler)
        raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        response = transport.process_one(raw)
        msg = json.loads(response)
        caps = msg["result"]["capabilities"]
        assert "tools" in caps
        assert "resources" in caps
        assert "prompts" in caps
