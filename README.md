# Price Tracker Ai

> By [MEOK AI Labs](https://meok.ai) — Track product prices over time, set price drop alerts, and compare across retailers. By MEOK AI Labs.

Price Tracker AI — track product prices, monitor drops, set alerts, and compare across retailers. MEOK AI Labs.

## Installation

```bash
pip install price-tracker-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install price-tracker-ai-mcp
```

## Tools

### `track_price`
Record a price observation for a product. Tracks history and detects drops automatically.

**Parameters:**
- `product` (str)
- `price` (float)
- `retailer` (str)
- `currency` (str)

### `get_price_history`
Get the price history for a tracked product. Returns most recent entries up to limit.

**Parameters:**
- `product` (str)
- `limit` (int)

### `set_alert`
Set a price alert. Get notified when a product drops to or below the target price.

**Parameters:**
- `product` (str)
- `target_price` (float)

### `compare_prices`
Compare current prices across multiple tracked products. Provide comma-separated product names.

**Parameters:**
- `products` (str)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/price-tracker-ai-mcp](https://github.com/CSOAI-ORG/price-tracker-ai-mcp)
- **PyPI**: [pypi.org/project/price-tracker-ai-mcp](https://pypi.org/project/price-tracker-ai-mcp/)

## License

MIT — MEOK AI Labs
