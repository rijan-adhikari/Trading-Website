# Architecture — NEPSE Paper Trader

## 1. Overview

NEPSE Paper Trader is a full-stack paper-trading simulator. Users trade
NEPSE-listed stocks with virtual money (default NPR 1,000,000 starting
balance). No real securities transactions ever occur; all market data is
either clearly labeled demo/simulated data or, in a future phase, sourced
from a real provider behind the same abstraction.

## 2. Tech stack

| Layer      | Choice                                   |
|------------|-------------------------------------------|
| Backend    | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Database   | PostgreSQL 16                             |
| Auth       | JWT (access + refresh), Argon2 password hashing |
| Frontend   | React + Vite + TypeScript (Phase 8)       |
| Charts     | Recharts (Phase 8)                        |
| Containers | Docker + docker-compose                   |

## 3. Layered backend architecture

```
api/          → FastAPI routers. Thin — parse request, call a service, return SuccessResponse.
schemas/      → Pydantic request/response models. Validation lives here (and in services for business rules).
services/     → Business logic. AuthService, OrderExecutionService, PortfolioService, etc.
repositories/ → DB access, one per aggregate root (UserRepository, StockRepository, ...).
models/       → SQLAlchemy ORM models — the schema, nothing else.
middleware/   → Cross-cutting request handling (rate limiting is wired in main.py via slowapi).
utils/        → security.py (hashing/JWT), errors.py (API error types).
```

Rule: routes never touch the DB directly, and services never know about
HTTP (no `Request`/`Response` objects) — that keeps trading logic testable
without spinning up FastAPI.

## 4. Authentication & authorization

- Registration hashes the password with Argon2, creates the `User`, a
  funded `Portfolio`, and a default `Watchlist` in one DB transaction.
- Login issues a short-lived access token (60 min default) and a
  longer-lived refresh token (7 days default), both JWTs signed with
  `JWT_SECRET`.
- `get_current_user` (in `app/api/deps.py`) is the **only** way a route
  determines the caller's identity — it decodes the bearer token and loads
  the user from the DB. Routes/services never trust a `user_id` passed in
  the request body or query string.
- `require_admin` gates admin-only routes.

## 5. Market data abstraction

```
MarketDataProvider (interface, Phase 2)
        ↑
DemoMarketDataProvider   ← generates/serves simulated prices, seeded from stocks table
        ↑ (future)
RealNEPSEMarketDataProvider   ← not implemented; slots in without changing callers
```

The rest of the app (stock routes, order execution, charts) depends only
on the `MarketDataProvider` interface, never on the demo implementation
directly, so swapping in a real feed later is a config change
(`MARKET_MODE=real`), not a rewrite.

## 6. Trading engine (Phase 2/3)

`OrderExecutionService` is the single place that: validates an order,
checks market status via `MarketSessionService`, checks cash/position,
calculates fees via `TradingFeeService`, executes the trade, updates
`Position`/`Portfolio.cash_balance`, writes a `Transaction`, writes an
`AuditLog` entry, and creates a `Notification` — all inside one DB
transaction (see `docs/trading-engine.md`, added when that phase lands).

## 7. Error handling contract

Every error response has the shape:

```json
{ "success": false, "error": { "code": "INSUFFICIENT_FUNDS", "message": "..." } }
```

Raise an `APIError` subclass (see `app/utils/errors.py`) from a service;
the global exception handler in `main.py` converts it to the right HTTP
status. Unhandled exceptions are logged server-side and returned to the
client as a generic `INTERNAL_ERROR` — stack traces never leave the server.

## 8. Deployment shape (Phase 15 will detail this fully)

- Frontend → static build → Vercel/Netlify
- Backend → containerized ASGI app → Render/Railway/Fly.io
- Database → managed Postgres
- All three are decoupled by config (`CORS_ORIGINS`, `DATABASE_URL`,
  `VITE_API_BASE_URL`) — nothing provider-specific is hardcoded.
