"""High-level order placement that dispatches to the right BasicBot method."""
from __future__ import annotations

from typing import Any, Dict

from .client import BasicBot
from .validators import OrderRequest


def place_order(bot: BasicBot, req: OrderRequest) -> Dict[str, Any]:
    if req.order_type == "MARKET":
        return bot.place_market_order(req.symbol, req.side, req.quantity)
    if req.order_type == "LIMIT":
        assert req.price is not None
        return bot.place_limit_order(req.symbol, req.side, req.quantity, req.price)
    if req.order_type == "STOP_LIMIT":
        assert req.price is not None and req.stop_price is not None
        return bot.place_stop_limit_order(
            req.symbol, req.side, req.quantity, req.price, req.stop_price
        )
    raise ValueError(f"Unsupported order type: {req.order_type}")


def format_response(resp: Dict[str, Any]) -> str:
    fields = ["orderId", "status", "executedQty", "avgPrice", "price", "type", "side", "symbol"]
    rows = [f"  {k:<13}: {resp.get(k)}" for k in fields if k in resp]
    return "\n".join(rows) if rows else str(resp)
