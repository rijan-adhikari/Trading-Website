# Database — NEPSE Paper Trader

PostgreSQL, accessed via SQLAlchemy 2.0 ORM, versioned with Alembic.
All monetary columns are `NUMERIC(18,4)` — never `FLOAT` — so trading
math never suffers floating-point rounding error.

## Tables

| Table                | Purpose |
|-----------------------|---------|
| `users`               | Account, credentials (Argon2 hash), role (`USER`/`ADMIN`) |
| `sectors`              | NEPSE sector taxonomy (Banking, Hydropower, ...) |
| `stocks`               | One row per tradable symbol; current OHLCV + 52wk range + `is_simulated` flag |
| `market_prices`        | OHLCV candle history per stock, powers the price chart timeframes |
| `market_sessions`      | Per-date trading-day overrides (holidays) for `MarketSessionService` |
| `portfolios`           | One per user: `cash_balance`, `initial_balance`, `realized_pl` |
| `positions`            | Open holdings: `quantity`, weighted-average `average_price` per stock |
| `portfolio_snapshots`  | Point-in-time `(cash, market_value, total_value)` for the performance chart |
| `orders`               | User's buy/sell instructions (MARKET/LIMIT), status lifecycle |
| `trades`               | Individual fills against an order (supports partial fills architecturally) |
| `transactions`         | The ledger — every cash-affecting event, with fees + realized P/L |
| `watchlists` / `watchlist_items` | User's tracked stocks |
| `price_alerts`         | User-defined trigger conditions, evaluated on each price tick |
| `notifications`        | In-app notification feed |
| `audit_logs`           | Immutable log of every sensitive action |
| `system_settings`      | Admin-editable overrides for config defaults (fees, initial balance) |

## Key relationships

```
User 1─1 Portfolio 1─* Position ─* Stock
User 1─* Watchlist 1─* WatchlistItem ─* Stock
User 1─* Order 1─* Trade
User 1─* Transaction
Stock *─1 Sector
Stock 1─* MarketPrice
```

## Indexing

Indexed for the query patterns the API actually needs:
- `users.email`, `users.username` — unique + lookup on login
- `stocks.symbol` — unique + lookup/search
- `orders.user_id`, `orders.status` — "my open orders" queries
- `transactions.user_id` — "my transaction history"
- `market_prices.(stock_id, timestamp)` — chart range queries
- `audit_logs.user_id`, `audit_logs.action`, `audit_logs.created_at`

## Financial accounting rules encoded in the schema

- **Average cost method**: buying more of a stock recomputes
  `positions.average_price` as a weighted average; selling reduces
  `quantity` only — `average_price` is untouched by sells.
- **Realized P/L** is computed at sell time and stored both on the
  `transactions` row (`realized_pl`) and accumulated into
  `portfolios.realized_pl`.
- **Cash balance** is mutated exclusively inside
  `OrderExecutionService`'s DB transaction — no route sets it directly.

## Migrations

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

`alembic/env.py` reads `DATABASE_URL` from `app.config.get_settings()`
and imports `app.models` so autogenerate sees every table — there is no
separate copy of the schema to keep in sync.
