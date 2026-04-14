#!/usr/bin/env python3
"""MEOK AI Labs — price-tracker-ai-mcp MCP Server. Track product prices across retailers and alert on drops."""

import asyncio
import json
from datetime import datetime
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent)
import mcp.types as types
import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
import json

# In-memory store (replace with DB in production)
_store = {}

server = Server("price-tracker-ai-mcp")

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="track_price", description="Track a product price", inputSchema={"type":"object","properties":{"product":{"type":"string"},"price":{"type":"number"}},"required":["product","price"]}),
        Tool(name="get_alerts", description="Get price drop alerts", inputSchema={"type":"object","properties":{}}),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    if name == "track_price":
        old = _store.get(args["product"], {}).get("price", float("inf"))
        _store[args["product"]] = {"price": args["price"], "date": datetime.now().isoformat()}
        alert = args["price"] < old
        return [TextContent(type="text", text=json.dumps({"alert": alert, "old_price": old if old != float("inf") else None}, indent=2))]
    if name == "get_alerts":
        return [TextContent(type="text", text=json.dumps({"tracked": list(_store.keys())}, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))]

async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="price-tracker-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={})))

if __name__ == "__main__":
    asyncio.run(main())