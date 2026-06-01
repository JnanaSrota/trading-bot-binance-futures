"""CLI entry point for the Binance Futures Testnet trading bot.

Examples
--------
Market BUY:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Limit SELL:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT \\
        --quantity 0.001 --price 65000

Stop-Limit (bonus):
    python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \\
        --quantity 0.001 --price 66000 --stop-price 65500

API credentials are read from env vars BINANCE_API_KEY / BINANCE_API_SECRET,
or can be passed via --api-key / --api-secret.
"""
from __future__ import annotations

import argparse
import os
import sys

from bot.client import BasicBot, BinanceAPIError, TESTNET_BASE_URL
from bot.logging_config import setup_logging
from bot.orders import format_response, place_order
from bot.validators import ValidationError, validate_order_input


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simplified Binance Futures Testnet (USDT-M) trading bot",
    )
    p.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    p.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"])
    p.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
    )
    p.add_argument("--quantity", required=True, type=float)
    p.add_argument("--price", type=float, help="required for LIMIT / STOP_LIMIT")
    p.add_argument("--stop-price", dest="stop_price", type=float, help="required for STOP_LIMIT")
    p.add_argument("--api-key", default=os.getenv("BINANCE_API_KEY"))
    p.add_argument("--api-secret", default=os.getenv("BINANCE_API_SECRET"))
    p.add_argument("--base-url", default=TESTNET_BASE_URL)
    return p


def main(argv=None) -> int:
    logger = setup_logging()
    args = build_parser().parse_args(argv)

    if not args.api_key or not args.api_secret:
        print(
            "ERROR: Provide API credentials via --api-key/--api-secret "
            "or BINANCE_API_KEY / BINANCE_API_SECRET env vars.",
            file=sys.stderr,
        )
        return 2

    try:
        req = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as e:
        logger.error("Validation failed: %s", e)
        print(f"Invalid input: {e}", file=sys.stderr)
        return 2

    print("=" * 60)
    print("ORDER REQUEST")
    print("=" * 60)
    print(req.summary())
    print()

    bot = BasicBot(args.api_key, args.api_secret, base_url=args.base_url, logger=logger)

    try:
        resp = place_order(bot, req)
    except BinanceAPIError as e:
        logger.error("Order failed: %s", e)
        print(f"\n❌ FAILURE: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error")
        print(f"\n❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("ORDER RESPONSE")
    print("=" * 60)
    print(format_response(resp))
    print("\n✅ SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
