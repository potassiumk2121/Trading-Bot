"""
Centralized logging configuration for the trading bot.

Logs are written to BOTH:
- A rotating log file (logs/trading_bot.log) — captures API requests,
  responses, and errors with full detail.
- The console (stdout) — shows INFO+ messages to the user.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

# Sensible default format: timestamp | level | module | message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "trading_bot", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger that writes to both file and console.

    Args:
        name: Logger name (defaults to "trading_bot").
        level: Console log level. File always logs at DEBUG.

    Returns:
        Configured logging.Logger instance.
    """
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Master level — handlers filter further.

    # Avoid attaching duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- File handler: rotates at 5 MB, keeps last 3 backups ---
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # --- Console handler: user-friendly INFO+ output ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Don't propagate to the root logger (avoids duplicate console lines)
    logger.propagate = False

    return logger
