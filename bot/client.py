"""Thin wrapper around the Binance Futures Testnet (USDT-M) REST API.

Uses signed HMAC-SHA256 requests via the `requests` library so the bot has
no hard dependency on python-binance. Targets:
    https://testnet.binancefuture.com
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import setup_logging

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000


class BinanceAPIError(RuntimeError):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, status_code: int, payload: Any):
        super().__init__(f"Binance API error {status_code}: {payload}")
        self.status_code = status_code
        self.payload = payload


class BasicBot:
    """Minimal Binance USDT-M Futures Testnet client."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        logger: Optional[logging.Logger] = None,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret are required")
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or setup_logging()
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        self.logger.debug("BasicBot initialized for %s", self.base_url)

    # ---------- low-level helpers ----------
    def _sign(self, params: Dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        self.logger.info("REQUEST %s %s params=%s", method, path, safe_params)

        request_kwargs = {"timeout": self.timeout}
        if method.upper() == "GET":
            request_kwargs["params"] = params
        else:
            request_kwargs["data"] = params

        try:
            resp = self.session.request(method, url, **request_kwargs)
        except requests.RequestException as e:
            self.logger.exception("Network error calling %s %s", method, path)
            raise BinanceAPIError(-1, {"network_error": str(e)}) from e

        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}

        self.logger.info("RESPONSE %s %s status=%s body=%s", method, path, resp.status_code, payload)

        if resp.status_code >= 400 or (isinstance(payload, dict) and payload.get("code", 0) and int(payload.get("code", 0)) < 0):
            self.logger.error("API error on %s %s: %s", method, path, payload)
            raise BinanceAPIError(resp.status_code, payload)

        return payload

    # ---------- public API ----------
    def ping(self) -> Dict[str, Any]:
        url = f"{self.base_url}/fapi/v1/ping"
        self.logger.info("REQUEST GET /fapi/v1/ping")
        r = self.session.get(url, timeout=self.timeout)
        self.logger.info("RESPONSE /fapi/v1/ping status=%s", r.status_code)
        return {"status": r.status_code}

    def account(self) -> Dict[str, Any]:
        return self._signed_request("GET", "/fapi/v2/account", {})

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        return self._signed_request(
            "POST",
            "/fapi/v1/order",
            {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity},
        )

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        return self._signed_request(
            "POST",
            "/fapi/v1/order",
            {
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "quantity": quantity,
                "price": price,
                "timeInForce": time_in_force,
            },
        )

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Bonus: STOP-LIMIT order (type=STOP on Futures)."""
        return self._signed_request(
            "POST",
            "/fapi/v1/order",
            {
                "symbol": symbol,
                "side": side,
                "type": "STOP",
                "quantity": quantity,
                "price": price,
                "stopPrice": stop_price,
                "timeInForce": time_in_force,
            },
        )
