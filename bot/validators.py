"""Input validation for CLI arguments before they reach the API layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


class ValidationError(ValueError):
    """Raised when user-supplied order parameters are invalid."""


@dataclass
class OrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None  # for STOP_LIMIT

    def summary(self) -> str:
        parts = [
            f"symbol={self.symbol}",
            f"side={self.side}",
            f"type={self.order_type}",
            f"quantity={self.quantity}",
        ]
        if self.price is not None:
            parts.append(f"price={self.price}")
        if self.stop_price is not None:
            parts.append(f"stopPrice={self.stop_price}")
        return " | ".join(parts)


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> OrderRequest:
    if not symbol or not symbol.isalnum():
        raise ValidationError(f"Invalid symbol: {symbol!r}")
    symbol = symbol.upper()

    side = side.upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"side must be one of {VALID_SIDES}, got {side!r}")

    order_type = order_type.upper()
    if order_type not in VALID_TYPES:
        raise ValidationError(f"order type must be one of {VALID_TYPES}, got {order_type!r}")

    try:
        quantity = float(quantity)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"quantity must be numeric, got {quantity!r}") from e
    if quantity <= 0:
        raise ValidationError(f"quantity must be > 0, got {quantity}")

    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders")
        price = float(price)
        if price <= 0:
            raise ValidationError(f"price must be > 0, got {price}")

    if order_type == "STOP_LIMIT":
        if price is None or stop_price is None:
            raise ValidationError("STOP_LIMIT requires both --price and --stop-price")
        price = float(price)
        stop_price = float(stop_price)
        if price <= 0 or stop_price <= 0:
            raise ValidationError("price and stop_price must be > 0")

    return OrderRequest(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )
