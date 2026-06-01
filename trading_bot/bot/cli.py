"""
Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:

    # Market BUY 0.01 BTCUSDT
    python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit SELL 0.01 BTCUSDT @ 70000
    python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT \
        --quantity 0.01 --price 70000

    # Stop-limit (bonus): SELL 0.01 BTCUSDT, stop=68000, limit=67900
    python -m bot.cli --symbol BTCUSDT --side SELL --type STOP_LIMIT \
        --quantity 0.01 --price 67900 --stop-price 68000

    # Interactive menu mode
    python -m bot.cli --interactive

Credentials can be supplied via:
    --api-key / --api-secret CLI flags, OR
    BINANCE_API_KEY / BINANCE_API_SECRET environment variables.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .client import BinanceFuturesClient, BinanceFuturesClientError
from .logging_config import setup_logger
from .orders import OrderManager
from .validators import (
    VALID_ORDER_TYPES,
    VALID_SIDES,
    validate_order_inputs,
)


def load_dotenv_file(env_path: Optional[str] = None) -> None:
    """Load key=value pairs from a .env file into os.environ if not already set."""
    path = Path(env_path) if env_path else Path(__file__).resolve().parents[1] / ".env"
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place orders on Binance USDT-M Futures Testnet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--symbol", help="Trading pair, e.g., BTCUSDT")
    parser.add_argument(
        "--side", choices=sorted(VALID_SIDES), help="Order side"
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        choices=sorted(VALID_ORDER_TYPES),
        help="Order type",
    )
    parser.add_argument("--quantity", type=float, help="Order quantity (base asset)")
    parser.add_argument(
        "--price", type=float, default=None,
        help="Limit price (required for LIMIT / STOP_LIMIT)",
    )
    parser.add_argument(
        "--stop-price", type=float, default=None,
        help="Stop trigger price (required for STOP_LIMIT)",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="Binance Testnet API key (or env BINANCE_API_KEY)",
    )
    parser.add_argument(
        "--api-secret", default=None,
        help="Binance Testnet API secret (or env BINANCE_API_SECRET)",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Run in interactive prompt mode (ignores other order flags)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable DEBUG console logging",
    )
    return parser


def prompt(text: str, default: Optional[str] = None) -> str:
    """Prompt the user, optionally with a default value."""
    suffix = f" [{default}]" if default else ""
    val = input(f"{text}{suffix}: ").strip()
    return val or (default or "")


def interactive_flow() -> dict:
    """Ask the user for order parameters via prompts."""
    print("\n=== Binance Futures Testnet — Interactive Order ===\n")
    symbol = prompt("Symbol", "BTCUSDT")
    side = prompt("Side (BUY/SELL)", "BUY").upper()
    order_type = prompt("Type (MARKET/LIMIT/STOP_LIMIT)", "MARKET").upper()
    quantity = prompt("Quantity", "0.01")

    price = None
    stop_price = None
    if order_type in {"LIMIT", "STOP_LIMIT"}:
        price = prompt("Price")
    if order_type == "STOP_LIMIT":
        stop_price = prompt("Stop price")

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }


def main(argv: Optional[list] = None) -> int:
    load_dotenv_file()
    parser = build_parser()
    args = parser.parse_args(argv)

    # ---- Logging setup ----
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(level=level)

    # ---- Gather order parameters (CLI flags OR interactive) ----
    if args.interactive:
        raw = interactive_flow()
    else:
        missing = [
            n for n, v in (
                ("--symbol", args.symbol),
                ("--side", args.side),
                ("--type", args.order_type),
                ("--quantity", args.quantity),
            ) if v is None
        ]
        if missing:
            parser.error(
                f"Missing required arguments: {', '.join(missing)}. "
                f"Run with --interactive for guided prompts."
            )
        raw = {
            "symbol": args.symbol,
            "side": args.side,
            "order_type": args.order_type,
            "quantity": args.quantity,
            "price": args.price,
            "stop_price": args.stop_price,
        }

    # ---- Validate ----
    try:
        clean = validate_order_inputs(**raw)
    except ValueError as e:
        logger.error("Input validation failed: %s", e)
        print(f"\n[ERROR] Invalid input: {e}\n", file=sys.stderr)
        return 2

    # ---- Build client ----
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET")
    try:
        client = BinanceFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,
            logger=logger,
        )
    except BinanceFuturesClientError as e:
        logger.error("Client init failed: %s", e)
        print(f"\n[ERROR] {e}\n", file=sys.stderr)
        return 3

    manager = OrderManager(client, logger=logger)

    # ---- Print request summary ----
    summary = manager.format_request_summary(
        clean["symbol"],
        clean["side"],
        clean["order_type"],
        clean["quantity"],
        clean["price"],
        clean["stop_price"],
    )
    print(summary)
    logger.info("Submitting order...")

    # ---- Place order ----
    try:
        response = manager.place_order(
            symbol=clean["symbol"],
            side=clean["side"],
            order_type=clean["order_type"],
            quantity=clean["quantity"],
            price=clean["price"],
            stop_price=clean["stop_price"],
        )
    except BinanceFuturesClientError as e:
        logger.error("Order placement failed: %s", e)
        print(f"\n[FAILURE] Order rejected: {e}\n", file=sys.stderr)
        return 1
    except Exception as e:  # network errors, etc.
        logger.exception("Unexpected failure: %s", e)
        print(f"\n[FAILURE] Unexpected error: {e}\n", file=sys.stderr)
        return 1

    # ---- Print response ----
    print(manager.format_response(response))
    print("\n[SUCCESS] Order placed successfully.\n")
    logger.info("Order placed successfully (orderId=%s)", response.get("orderId"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
