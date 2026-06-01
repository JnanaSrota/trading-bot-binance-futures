# Simplified Binance Futures Testnet Trading Bot

A small, well-structured Python CLI that places **MARKET**, **LIMIT**, and
(bonus) **STOP-LIMIT** orders on the **Binance USDT-M Futures Testnet**
(`https://testnet.binancefuture.com`).

## Features

- BUY / SELL on Binance Futures Testnet (USDT-M)
- MARKET, LIMIT, and STOP-LIMIT (bonus) order types
- CLI built with `argparse`, with input validation
- Clear request summary + response details (`orderId`, `status`,
  `executedQty`, `avgPrice`, …)
- Structured code: separate **client/API layer** (`bot/client.py`)
  and **CLI layer** (`cli.py`)
- Rotating file logging of every request / response / error in
  `logs/trading_bot.log`
- Robust exception handling (validation, API errors, network failures)
- Uses plain `requests` — no hard dependency on `python-binance`

## Project structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client wrapper (signed requests)
│   ├── orders.py          # Order placement dispatch + formatting
│   ├── validators.py      # CLI input validation
│   └── logging_config.py  # Rotating-file + console logger
├── cli.py                 # CLI entry point
├── logs/
│   ├── trading_bot.log               # live log
│   ├── sample_market_order.log       # sample MARKET order run
│   └── sample_limit_order.log        # sample LIMIT order run
├── requirements.txt
└── README.md
```

## Setup

1. Register & activate an account on the Binance Futures Testnet:
   <https://testnet.binancefuture.com>
2. Generate API key + secret from the testnet dashboard.
3. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Export credentials (or pass via flags):

   ```bash
   export BINANCE_API_KEY="your_testnet_key"
   export BINANCE_API_SECRET="your_testnet_secret"
   ```

## Usage

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT \
    --quantity 0.001 --price 65000
```

### Stop-Limit (bonus)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \
    --quantity 0.001 --price 66000 --stop-price 65500
```

### Example output

```
============================================================
ORDER REQUEST
============================================================
symbol=BTCUSDT | side=BUY | type=MARKET | quantity=0.001

============================================================
ORDER RESPONSE
============================================================
  orderId      : 39847123
  status       : FILLED
  executedQty  : 0.001
  avgPrice     : 65123.40
  type         : MARKET
  side         : BUY
  symbol       : BTCUSDT

✅ SUCCESS
```

## Logging

All requests, responses, and errors are written to
`logs/trading_bot.log` (rotating, 2 MB × 5 backups) at DEBUG level.
Console output is INFO level. Sample logs for one MARKET and one LIMIT
order are included under `logs/sample_*.log`.

## Assumptions

- The account is funded with testnet USDT and the symbol (e.g. `BTCUSDT`)
  is tradable on USDT-M Futures Testnet.
- `LIMIT` orders use `timeInForce=GTC` by default.
- `STOP_LIMIT` is implemented as Futures order type `STOP` (stop-limit
  variant on USDT-M Futures), with both `price` and `stopPrice`.
- Quantity / price are sent as-is; users are expected to respect the
  symbol's `LOT_SIZE` / `PRICE_FILTER` step sizes shown by Binance.
- Server-time drift is handled with `recvWindow=5000`. If your clock is
  badly skewed, sync it with NTP.

## Error handling

- **Validation errors** (bad symbol/side/type/quantity, missing price for
  LIMIT, etc.) → exit code 2 with a clear message.
- **Binance API errors** (e.g. insufficient margin, invalid symbol,
  bad signature) → wrapped in `BinanceAPIError`, logged, exit code 1.
- **Network failures** → caught and re-raised as `BinanceAPIError(-1, …)`.
