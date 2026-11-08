# Database

PostgreSQL is the production database. SQLAlchemy 2.0 manages ORM access and Alembic manages schema migrations. Local development can use SQLite. Production startup rejects SQLite to avoid ephemeral account and ledger data.

All monetary columns use `NUMERIC(18,4)`; application calculations use Python `Decimal`.

## Tables

| Table | Purpose | Current use |
|---|---|---|
| `users` | Credentials, profile, role and active status | Registration, login and admin status |
| `sectors` | Stock sector taxonomy | Demo sector created when a symbol is first traded |
| `stocks` | Tradable symbol and current quote fields | Demo symbol rows created on first trade |
| `market_prices` | OHLCV history | Schema reserved; current chart candles are generated in memory |
| `market_sessions` | Trading-day overrides and holidays | Schema reserved; not enforced by order execution |
| `portfolios` | Cash, initial balance and realized P&L | One funded portfolio per user |
| `positions` | Quantity and weighted-average cost | Updated by paper BUY/SELL orders |
| `portfolio_snapshots` | Point-in-time portfolio values | Schema reserved; no snapshot job |
| `orders` | Order instructions and status | Immediate MARKET orders only |
| `trades` | Individual fills | One fill per current market order |
| `transactions` | Cash ledger with fees and realized P&L | Written for every executed BUY/SELL |
| `watchlists`, `watchlist_items` | User watchlists | Default list created; CRUD API not implemented |
| `price_alerts` | Price trigger configuration | Schema reserved; no evaluator |
| `notifications` | In-app notification records | Schema reserved; delivery/API not implemented |
| `audit_logs` | Security and trading events | Auth, trades and admin status changes |
| `system_settings` | Potential runtime overrides | Schema reserved; no admin settings API |

## Relationships

```text
User 1─1 Portfolio 1─* Position *─1 Stock
User 1─* Watchlist 1─* WatchlistItem *─1 Stock
User 1─* Order 1─* Trade
User 1─* Transaction
Stock *─1 Sector
```

## Accounting rules

- **Buy:** cash is reduced by gross value plus simulated fees. Fees are included in the weighted-average cost basis.
- **Sell:** cash increases by gross value less simulated fees. Realized P&L equals net sale proceeds minus the cost basis of the shares sold.
- **Partial sell:** the remaining shares retain the same weighted-average cost basis.
- **Position closure:** a position is deleted when its quantity reaches zero.
- **Atomicity:** portfolio, position, order, trade, transaction and audit updates share one SQLAlchemy transaction.

The fee values in `.env.example` are simulator assumptions only, not official current market charges.

## Migrations

The initial schema migration is committed in `backend/alembic/versions/`. Apply it to a new PostgreSQL database with:

```bash
cd backend
alembic upgrade head
```

Do not generate a replacement initial migration for an existing deployment. Create a new migration only when the ORM schema intentionally changes, review the generated SQL, then commit it with the model change.
