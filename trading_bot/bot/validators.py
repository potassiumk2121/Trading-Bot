"""
Input validation utilities for the trading bot CLI.

Each validator raises ValueError with a descriptive message on failure
so that the CLI layer can present a clean error to the user.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


def validate_symbol(symbol: str) -> str:
    """
    Validate a trading symbol (e.g., BTCUSDT).

    Rules:
    - Non-empty string
    - Uppercased
    - Must end with 'USDT' for USDT-M futures
    - Alphanumeric only
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol is required and must be a string.")

    symbol = symbol.strip().upper()

    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' must be alphanumeric (e.g., BTCUSDT).")

    if not symbol.endswith("USDT"):
        raise ValueError(
            f"Symbol '{symbol}' must end with 'USDT' for USDT-M futures."
        )

    if len(symbol) < 5:
        raise ValueError(f"Symbol '{symbol}' looks too short to be valid.")

    return symbol


def validate_side(side: str) -> str:
    """Validate order side: BUY or SELL."""
    if not side:
        raise ValueError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type: MARKET, LIMIT, or STOP_LIMIT."""
    if not order_type:
        raise ValueError("Order type is required.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    """Validate quantity is a positive number."""
    if quantity is None:
        raise ValueError("Quantity is required.")
    try:
        q = Decimal(str(quantity))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if q <= 0:
        raise ValueError(f"Quantity must be > 0 (got {quantity}).")
    return float(q)


def validate_price(price, required: bool = False) -> Optional[float]:
    """
    Validate price.
    - If required=True (LIMIT/STOP_LIMIT orders), price must be present and > 0.
    - If required=False (MARKET orders), price may be None.
    """
    if price is None or price == "":
        if required:
            raise ValueError("Price is required for LIMIT / STOP_LIMIT orders.")
        return None
    try:
        p = Decimal(str(price))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValueError(f"Price must be > 0 (got {price}).")
    return float(p)


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> dict:
    """
    Run all validators and return a normalized dict of cleaned values.

    Raises ValueError on any invalid input.
    """
    clean = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }

    needs_price = clean["order_type"] in {"LIMIT", "STOP_LIMIT"}
    clean["price"] = validate_price(price, required=needs_price)

    if clean["order_type"] == "STOP_LIMIT":
        clean["stop_price"] = validate_price(stop_price, required=True)
    else:
        clean["stop_price"] = None

    return clean
