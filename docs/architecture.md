# Architecture

## Product boundary

NEPSE Paper Trader is an educational paper-trading MVP. The current market source is a five-symbol in-code demo fixture with generated OHLCV candles. There is no broker integration and no licensed NEPSE market-data provider.

## Runtime components

- **React + Vite frontend**: authentication modal, simulated market list/chart, order ticket, portfolio view and basic admin screen.
- **FastAPI backend**: JSON API, request validation, authentication dependencies, rate limiting and error envelope.
- **SQLAlchemy 2 + Alembic**: relational persistence and schema migrations.
- **PostgreSQL**: required for production. SQLite is allowed only for local development.
- **Render**: API web service, static frontend and managed PostgreSQL, defined in `render.yaml`.

## Backend structure

```text
app/
├── api/
│   ├── auth.py       # register, login, refresh, logout acknowledgement, profile
│   ├── admin.py      # admin-only user status controls
│   ├── market.py     # five demo quotes and generated candles
│   ├── trading.py    # market orders, portfolio and transaction history
│   └── deps.py       # current-user/admin dependencies and rate limiter
├── models/           # SQLAlchemy entities
├── schemas/          # Pydantic request and response types
├── repositories/     # user lookup/create
├── services/
│   ├── auth_service.py
│   ├── audit_service.py
│   └── trading_service.py
├── config.py
├── database.py
└── utils/
    ├── security.py
    └── errors.py
```

## Request and trade flow

1. Registration validates input, hashes the password with Argon2, creates the user, initial virtual portfolio and default watchlist in one transaction.
2. Login issues an access JWT and refresh JWT.
3. Protected routes decode the access token, load the user from the database and reject missing, invalid or suspended accounts.
4. A market-order request is validated by Pydantic and the configured IP rate limiter.
5. `TradingService` locks the user's portfolio row, resolves a symbol from the demo quote fixture, checks cash or available shares, applies illustrative fees, updates the position and cash balance, then records the order, trade, transaction and audit event in one database transaction.
6. Portfolio and transaction endpoints read persisted database state.

## Financial accounting

- Money uses Python `Decimal` and database `NUMERIC(18,4)`.
- Buy-side fees are included in the weighted-average position cost basis.
- Sell-side fees are deducted from sale proceeds before realized P&L is calculated.
- A sell cannot exceed the user's available position.
- A buy cannot exceed available virtual cash including fees.

The fee schedule is illustrative and must not be described as the official NEPSE/broker/SEBON fee schedule.

## Security and operational boundaries

- User identity comes from the validated bearer token, never a user ID supplied by the client.
- Passwords are Argon2 hashes; tokens are signed JWTs.
- Admin routes require the ADMIN role server-side.
- Login, registration and order endpoints have IP-based rate limits.
- Production requires long random secrets and PostgreSQL.
- `/health` is a liveness endpoint; `/ready` checks database connectivity and returns HTTP 503 when the database is unavailable.
- Frontend tokens are stored in localStorage. Logout clears them client-side, but server-side token revocation/rotation is not implemented.

## Explicitly deferred

Live market data, the full NEPSE symbol universe, official index values, limit/stop orders, exchange-session enforcement, holiday calendars, user watchlist CRUD, price alerts, notification delivery, password recovery, email verification, MFA, refresh-token revocation, portfolio snapshots/charts, and complete operational monitoring are not implemented. Do not configure `MARKET_MODE=real`; settings validation rejects it until a provider integration exists.
