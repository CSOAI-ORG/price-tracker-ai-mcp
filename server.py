#!/usr/bin/env python3
"""Price Tracker AI — track product prices, monitor drops, set alerts, and compare across retailers. MEOK AI Labs."""
import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access
from persistence import ServerStore

import json
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

_store = ServerStore("price-tracker-ai")

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

mcp = FastMCP("price-tracker-ai", instructions="Track product prices over time, set price drop alerts, and compare across retailers. By MEOK AI Labs.")


@mcp.tool()
def track_price(product: str, price: float, retailer: str = "unknown", currency: str = "USD", api_key: str = "") -> str:
    """Record a price observation for a product. Tracks history and detects drops automatically."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err
    if price < 0:
        return json.dumps({"error": "Price cannot be negative"})
    product_key = product.lower().strip()
    history = _store.list(f"prices:{product_key}")
    entry = {
        "price": round(price, 2),
        "retailer": retailer,
        "currency": currency,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    # Detect price changes
    price_drop = False
    previous_price = None
    change_pct = 0.0
    if history:
        previous_price = history[-1]["price"]
        if previous_price > 0:
            change_pct = round((price - previous_price) / previous_price * 100, 2)
        price_drop = price < previous_price
    _store.append(f"prices:{product_key}", entry)
    _store.hset("tracked_products", product_key, product)
    # Check alerts
    triggered_alerts = []
    all_alerts = _store.list("alerts")
    for alert in all_alerts:
        if alert["product"] == product_key and price <= alert["target_price"] and alert["active"]:
            triggered_alerts.append({
                "alert_id": alert["id"],
                "target_price": alert["target_price"],
                "current_price": price,
                "savings": round(alert.get("original_price", price) - price, 2),
            })
            alert["active"] = False
            alert["triggered_at"] = datetime.now(timezone.utc).isoformat()
            _store.hset("alerts_by_id", str(alert["id"]), alert)
    # Stats
    all_prices = [h["price"] for h in history] + [entry["price"]]
    return json.dumps({
        "product": product,
        "recorded": entry,
        "price_change": {
            "previous_price": previous_price,
            "change_pct": change_pct,
            "direction": "drop" if price_drop else "increase" if previous_price and price > previous_price else "first_entry",
        },
        "stats": {
            "lowest_ever": min(all_prices),
            "highest_ever": max(all_prices),
            "observations": len(all_prices),
            "is_lowest": price <= min(all_prices),
        },
        "triggered_alerts": triggered_alerts if triggered_alerts else None,
    }, indent=2)


@mcp.tool()
def get_price_history(product: str, limit: int = 20, api_key: str = "") -> str:
    """Get the price history for a tracked product. Returns most recent entries up to limit."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err
    product_key = product.lower().strip()
    history = _store.list(f"prices:{product_key}")
    if not history:
        tracked = list(_store.hgetall("tracked_products").keys())
        return json.dumps({
            "error": f"No price history for '{product}'",
            "tracked_products": tracked[:20] if tracked else [],
        })
    limit = max(1, min(limit, 100))
    recent = list(reversed(history))[:limit]
    all_prices = [h["price"] for h in history]
    avg_price = sum(all_prices) / len(all_prices)
    # Price trend
    if len(all_prices) >= 2:
        first_half = sum(all_prices[:len(all_prices)//2]) / (len(all_prices)//2)
        second_half = sum(all_prices[len(all_prices)//2:]) / (len(all_prices) - len(all_prices)//2)
        trend = "decreasing" if second_half < first_half * 0.97 else "increasing" if second_half > first_half * 1.03 else "stable"
    else:
        trend = "insufficient data"
    return json.dumps({
        "product": product,
        "history": recent,
        "showing": len(recent),
        "total_observations": len(history),
        "stats": {
            "current_price": history[-1]["price"],
            "lowest": min(all_prices),
            "highest": max(all_prices),
            "average": round(avg_price, 2),
            "trend": trend,
        },
    }, indent=2)


@mcp.tool()
def set_alert(product: str, target_price: float, api_key: str = "") -> str:
    """Set a price alert. Get notified when a product drops to or below the target price."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err
    if target_price < 0:
        return json.dumps({"error": "Target price cannot be negative"})
    product_key = product.lower().strip()
    # Get current price if tracked
    current_price = None
    history = _store.list(f"prices:{product_key}")
    if history:
        current_price = history[-1]["price"]
        if current_price <= target_price:
            return json.dumps({
                "message": f"Current price (${current_price}) is already at or below target (${target_price})!",
                "current_price": current_price,
                "target_price": target_price,
            })
    alert_id = _store.list_length("alerts") + 1
    alert = {
        "id": alert_id,
        "product": product_key,
        "product_display": product,
        "target_price": round(target_price, 2),
        "original_price": current_price,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "triggered_at": None,
    }
    _store.append("alerts", alert)
    _store.hset("alerts_by_id", str(alert_id), alert)
    all_alerts = _store.list("alerts")
    active_alerts = [a for a in all_alerts if a["active"]]
    return json.dumps({
        "alert_created": alert,
        "current_price": current_price,
        "drop_needed": round(current_price - target_price, 2) if current_price else None,
        "drop_needed_pct": round((current_price - target_price) / current_price * 100, 1) if current_price else None,
        "total_active_alerts": len(active_alerts),
    }, indent=2)


@mcp.tool()
def compare_prices(products: str, api_key: str = "") -> str:
    """Compare current prices across multiple tracked products. Provide comma-separated product names."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err
    names = [p.strip() for p in products.split(",") if p.strip()]
    if len(names) < 2:
        return json.dumps({"error": "Provide at least 2 comma-separated product names to compare"})
    results = []
    for name in names:
        key = name.lower().strip()
        history = _store.list(f"prices:{key}")
        if history:
            all_prices = [h["price"] for h in history]
            current = history[-1]
            results.append({
                "product": name,
                "current_price": current["price"],
                "retailer": current["retailer"],
                "lowest_ever": min(all_prices),
                "highest_ever": max(all_prices),
                "observations": len(history),
                "vs_lowest_pct": round((current["price"] - min(all_prices)) / min(all_prices) * 100, 1) if min(all_prices) > 0 else 0,
            })
        else:
            results.append({"product": name, "error": "not tracked"})
    found = [r for r in results if "error" not in r]
    cheapest = min(found, key=lambda r: r["current_price"]) if found else None
    best_deal = min(found, key=lambda r: r["vs_lowest_pct"]) if found else None
    return json.dumps({
        "comparison": results,
        "cheapest": {"product": cheapest["product"], "price": cheapest["current_price"]} if cheapest else None,
        "closest_to_lowest": {"product": best_deal["product"], "vs_lowest_pct": best_deal["vs_lowest_pct"]} if best_deal else None,
        "products_found": len(found),
        "products_missing": len(results) - len(found),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
