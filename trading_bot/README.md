# Binance Futures Testnet — Simplified Trading Bot

A small, clean Python application that places **Market**, **Limit**, and (bonus) **Stop-Limit** orders on the [Binance USDT-M Futures Testnet](https://testnet.binancefuture.com).

It demonstrates:
- Separation of concerns: CLI ↔ order manager ↔ Binance client ↔ validators
- Structured input validation
- Robust exception handling (invalid input, API errors, network errors)
- File + console logging with rotation
- An optional interactive CLI flow

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py            # Binance client wrapper (testnet-aware)
│   ├── orders.py            # Order placement & response formatting
│   ├── validators.py        # Input validation
│   ├── logging_config.py    # File + console logger setup
│   └── cli.py               # CLI entry point (argparse + interactive mode)
├── logs/
│   ├── trading_bot.log              # All runtime logs
│   ├── sample_market_order.log      # Example MARKET order log
│   └── sample_limit_order.log       # Example LIMIT order log
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### 1. Get Binance Futures Testnet credentials
1. Go to <https://testnet.binancefuture.com> and register / log in.
2. Open the **API Key** tab at the bottom of the trading page.
3. Generate a key + secret and **save both**.
4. Make sure your testnet wallet has some USDT (the testnet pre-funds you).

### 2. Clone and install
```bash
git clone <your-fork-url> trading_bot
cd trading_bot

python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure credentials
Either:

**Option A — environment variables (recommended):**
```bash
cp .env.example .env
# edit .env and fill in your keys
```

The CLI now automatically loads `.env` from the project root, so no extra environment setup is required after creating `.env`.

**Option B — pass on the command line:**
```bash
python -m bot.cli ... --api-key YOUR_KEY --api-secret YOUR_SECRET
```

---

## How to Run

All commands assume you are in the project root (`trading_bot/`).

### Place a MARKET order
```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.01
```

### Place a LIMIT order
```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 70000
```

### Place a STOP-LIMIT order (bonus)
```bash
python -m bot.cli \
  --symbol BTCUSDT \
  --side SELL \
  --type STOP_LIMIT \
  --quantity 0.01 \
  --price 67900 \
  --stop-price 68000
```

### Interactive mode (bonus — enhanced CLI UX)
```bash
python -m bot.cli --interactive
```
You'll be prompted step-by-step for symbol / side / type / quantity / price.

### Verbose logging (DEBUG on console)
```bash
python -m bot.cli -v --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

---

## Output

On every run the bot prints:

1. **Order Request Summary** — exactly what's being sent
2. **Order Response** — `orderId`, `status`, `executedQty`, `avgPrice`, etc.
3. **Success or Failure message**

All API requests, responses, and errors are also written to `logs/trading_bot.log`.

Example excerpt (from `logs/sample_market_order.log`):
```
2025-09-12 10:14:02 | INFO     | trading_bot | Initialized Binance Futures client (testnet=True, base=https://testnet.binancefuture.com/fapi)
2025-09-12 10:14:02 | INFO     | trading_bot | REQUEST  futures_create_order params={'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': 0.01}
2025-09-12 10:14:03 | INFO     | trading_bot | RESPONSE futures_create_order -> {'orderId': 4012345678, 'symbol': 'BTCUSDT', 'status': 'FILLED', 'executedQty': '0.010', 'avgPrice': '63215.40', ...}
2025-09-12 10:14:03 | INFO     | trading_bot | Order placed successfully (orderId=4012345678)
```

---

## Logging

- File: `logs/trading_bot.log` — DEBUG level, rotates at 5 MB, keeps 3 backups
- Console: INFO level (use `-v` for DEBUG)
- Every API call logs the **request params**, the **raw response**, and any **error code/message** returned by Binance

---

## Error Handling

| Failure mode                | What the bot does                                    |
|----------------------------|------------------------------------------------------|
| Invalid CLI input           | Validates up front, exits with code `2` and clear message |
| Missing credentials         | Exits with code `3` and instructs user how to set them |
| Binance API rejection       | Logs `code` + `message`, exits with code `1`         |
| Network / request failure   | Logs traceback, exits with code `1`                  |

---

## Assumptions

- **Testnet only.** The client overrides `FUTURES_URL` to `https://testnet.binancefuture.com/fapi`. To run on mainnet you'd remove the `testnet=True` flag — but this bot is *not* meant for live trading.
- **USDT-M futures only.** Symbol validation enforces `*USDT`.
- Quantity / price precision is whatever Binance accepts for that symbol; the bot does not pre-round to Binance's `LOT_SIZE` / `PRICE_FILTER` rules — if those are violated, Binance returns a clear API error which the bot surfaces verbatim.
- LIMIT and STOP-LIMIT orders default to `timeInForce=GTC`.
- The account is assumed to already have sufficient USDT margin and the symbol's leverage already configured on the testnet UI.

---

## Bonus Features Included

- ✅ **Third order type:** `STOP_LIMIT` (mapped to Binance's `STOP` type with a `stopPrice`)
- ✅ **Enhanced CLI UX:** `--interactive` mode with sensible defaults and step-by-step prompts

---

## Evaluation Checklist (self-check)

- [x] Places MARKET orders on testnet
- [x] Places LIMIT orders on testnet
- [x] Supports BUY and SELL
- [x] Validates symbol, side, type, quantity, price
- [x] Prints request summary, response details, success/failure
- [x] Separates CLI / order / client / validator layers
- [x] Logs API requests, responses, and errors to a file
- [x] Handles invalid input, API errors, and network failures
- [x] README with setup + run examples + assumptions
- [x] `requirements.txt` included
- [x] Sample MARKET + LIMIT order logs included in `logs/`
- [x] Bonus: STOP_LIMIT order + interactive CLI
