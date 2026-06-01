"""
High-level order placement logic.

This module sits between the CLI and the low-level client. It:
- Accepts already-validated input
- Dispatches to the right client method (MARKET / LIMIT / STOP_LIMIT)
- Formats a human-readable summary of the order request + response
"""

import logging
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient, BinanceFuturesClientError


class OrderManager:
    """Coordinates order placement and result formatting."""

    def __init__(self, client: BinanceFuturesClient, logger: Optional[logging.Logger] = None):
        self.client = client
        self.logger = logger or logging.getLogger("trading_bot")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch an order to the appropriate client method.

        Returns the raw API response dict on success.
        Raises BinanceFuturesClientError on failure.
        """
        self.logger.info(
            "Placing %s %s order: symbol=%s qty=%s price=%s stop_price=%s",
            order_type, side, symbol, quantity, price, stop_price,
        )

        if order_type == "MARKET":
            return self.client.place_market_order(symbol, side, quantity)

        if order_type == "LIMIT":
            if price is None:
                raise BinanceFuturesClientError("LIMIT order requires a price.")
            return self.client.place_limit_order(symbol, side, quantity, price)

        if order_type == "STOP_LIMIT":
            if price is None or stop_price is None:
                raise BinanceFuturesClientError(
                    "STOP_LIMIT order requires both price and stop_price."
                )
            return self.client.place_stop_limit_order(
                symbol, side, quantity, price, stop_price
            )

        raise BinanceFuturesClientError(f"Unsupported order type: {order_type}")

    # ------------------------------------------------------------------ #
    # Pretty-printing helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def format_request_summary(
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
        stop_price: Optional[float],
    ) -> str:
        lines = [
            "=" * 60,
            "ORDER REQUEST SUMMARY",
            "=" * 60,
            f"  Symbol     : {symbol}",
            f"  Side       : {side}",
            f"  Type       : {order_type}",
            f"  Quantity   : {quantity}",
        ]
        if price is not None:
            lines.append(f"  Price      : {price}")
        if stop_price is not None:
            lines.append(f"  Stop Price : {stop_price}")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def format_response(response: Dict[str, Any]) -> str:
        """Pretty-print the key fields from a Binance order response."""
        lines = [
            "=" * 60,
            "ORDER RESPONSE",
            "=" * 60,
            f"  Order ID      : {response.get('orderId')}",
            f"  Client Ord ID : {response.get('clientOrderId')}",
            f"  Symbol        : {response.get('symbol')}",
            f"  Status        : {response.get('status')}",
            f"  Type          : {response.get('type')}",
            f"  Side          : {response.get('side')}",
            f"  Orig Qty      : {response.get('origQty')}",
            f"  Executed Qty  : {response.get('executedQty')}",
            f"  Avg Price     : {response.get('avgPrice', 'N/A')}",
            f"  Price         : {response.get('price', 'N/A')}",
            f"  Stop Price    : {response.get('stopPrice', 'N/A')}",
            f"  Time In Force : {response.get('timeInForce', 'N/A')}",
            f"  Update Time   : {response.get('updateTime')}",
            "=" * 60,
        ]
        return "\n".join(lines)
