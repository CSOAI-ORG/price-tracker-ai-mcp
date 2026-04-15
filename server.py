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

from datetime import datetime, timezone
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

# In-memory store (replace with DB in production)
_store = {}

server = Server("price-tracker-ai")

@server.list_resources()
def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="track_price", description="Track a product price", inputSchema={"type":"object","properties":{"product":{"type":"string"},"price":{"type":"number"}},"required":["product","price"]}),
        Tool(name="get_alerts", description="Get price drop alerts", inputSchema={"type":"object","properties":{}}),
    ]

@server.call_tool()
def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [TextContent(type="text", text=json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"}))]
    if err := _rl():
        return [TextContent(type="text", text=err)]
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