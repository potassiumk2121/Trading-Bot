"""
Binance Futures Testnet client wrapper.

Uses the official `python-binance` library under the hood and points it at
the Binance USDT-M Futures Testnet (https://testnet.binancefuture.com).

All API calls are logged (request + response + errors) via the shared logger.
"""

import logging
from typing import Any, Dict, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException


# Binance Futures Testnet base URL (USDT-M)
FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"


class BinanceFuturesClientError(Exception):
    """Raised when the Binance Futures client encounters an unrecoverable error."""


class BinanceFuturesClient:
    """
    Thin wrapper around `python-binance` configured for the USDT-M Futures Testnet.

    Responsibilities:
    - Hold credentials + testnet configuration
    - Expose order-related helpers (market, limit, stop-limit)
    - Centralize logging and error handling for every API call
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        if not api_key or not api_secret:
            raise BinanceFuturesClientError(
                "API key and secret are required. "
                "Pass them via CLI args or BINANCE_API_KEY / BINANCE_API_SECRET env vars."
            )

        self.logger = logger or logging.getLogger("trading_bot")
        self.testnet = testnet

        # `python-binance` supports testnet via the `testnet=True` flag for spot,
        # but for futures we must explicitly override the FUTURES_URL.
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            # Override the futures REST endpoint to testnet
            self.client.FUTURES_URL = FUTURES_TESTNET_URL + "/fapi"

        self.logger.info(
            "Initialized Binance Futures client (testnet=%s, base=%s)",
            testnet,
            self.client.FUTURES_URL,
        )

    # ------------------------------------------------------------------ #
    # Connectivity / sanity checks
    # ------------------------------------------------------------------ #
    def ping(self) -> Dict[str, Any]:
        """Ping the futures endpoint to verify connectivity."""
        try:
            self.logger.debug("REQUEST  ping futures endpoint")
            resp = self.client.futures_ping()
            self.logger.debug("RESPONSE ping -> %s", resp)
            return resp
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error("Ping failed: %s", e)
            raise BinanceFuturesClientError(f"Ping failed: {e}") from e

    def get_account_balance(self) -> Any:
        """Return the futures account balances (useful for diagnostics)."""
        try:
            self.logger.debug("REQUEST  futures_account_balance")
            resp = self.client.futures_account_balance()
            self.logger.debug("RESPONSE futures_account_balance -> %s", resp)
            return resp
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error("Failed to fetch account balance: %s", e)
            raise BinanceFuturesClientError(f"Balance fetch failed: {e}") from e

    # ------------------------------------------------------------------ #
    # Order placement
    # ------------------------------------------------------------------ #
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a MARKET order on USDT-M Futures Testnet."""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }
        return self._send_order(params)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Place a LIMIT order on USDT-M Futures Testnet."""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
        }
        return self._send_order(params)

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a STOP-LIMIT order (Binance Futures type = 'STOP').
        Triggers a LIMIT order at `price` once the market crosses `stop_price`.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
        }
        return self._send_order(params)

    # ------------------------------------------------------------------ #
    # Internal helper
    # ------------------------------------------------------------------ #
    def _send_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a futures order request and log everything that happens."""
        self.logger.info("REQUEST  futures_create_order params=%s", params)
        try:
            response = self.client.futures_create_order(**params)
            self.logger.info("RESPONSE futures_create_order -> %s", response)
            return response
        except BinanceAPIException as e:
            # API-level rejection (e.g., insufficient margin, bad symbol)
            self.logger.error(
                "Binance API error: code=%s message=%s params=%s",
                e.code, e.message, params,
            )
            raise BinanceFuturesClientError(
                f"Binance API error [{e.code}]: {e.message}"
            ) from e
        except BinanceRequestException as e:
            # Network / request-formation problem
            self.logger.error("Binance request error: %s params=%s", e, params)
            raise BinanceFuturesClientError(f"Binance request error: {e}") from e
        except Exception as e:
            # Anything else (e.g., connection reset, JSON decode)
            self.logger.exception("Unexpected error placing order: %s", e)
            raise BinanceFuturesClientError(f"Unexpected error: {e}") from e
