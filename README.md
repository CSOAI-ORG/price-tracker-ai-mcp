<div align="center">

# Price Tracker Ai MCP

**MCP server for price tracker ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-price-tracker-ai-mcp)](https://pypi.org/project/meok-price-tracker-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Price Tracker Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `track_price` | Record a price observation for a product. Tracks history and detects drops autom |
| `get_price_history` | Get the price history for a tracked product. Returns most recent entries up to l |
| `set_alert` | Set a price alert. Get notified when a product drops to or below the target pric |
| `compare_prices` | Compare current prices across multiple tracked products. Provide comma-separated |

## Installation

```bash
pip install meok-price-tracker-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "price-tracker-ai": {
      "command": "python",
      "args": ["-m", "meok_price_tracker_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
