# NEPSE Paper Trader

**Practice NEPSE trading with virtual money.**

A full-stack paper-trading simulation platform for the Nepal Stock
Exchange. Every user starts with **NPR 1,000,000** in virtual cash and
trades against simulated (clearly labeled) market data. **No real
securities transactions ever occur.**

> ⚠️ This is a simulation platform. It does not execute real trades, is
> not affiliated with NEPSE, and does not provide investment advice.

## Status

This project is being built in phases. Current state:

- [x] Phase 1 — Architecture, database schema, backend foundation (auth, config, error handling)
- [x] Phase 2 — Market data abstraction + demo market engine
- [ ] Phase 3 — Trading engine (order execution, fees)
- [ ] Phase 4 — Portfolio calculations
- [ ] Phase 5 — Remaining REST API (stocks, market, orders, portfolio, transactions, watchlists, notifications)
- [ ] Phase 6 — Frontend (React + Vite + TS)
- [ ] Phase 7 — Dashboard
- [ ] Phase 8 — Admin panel
- [ ] Phase 9 — Notifications & price alerts
- [ ] Phase 10 — Testing
- [ ] Phase 11 — Docker polish
- [ ] Phase 12 — Full documentation
- [ ] Phase 13 — Deployment configuration

See `docs/architecture.md` and `docs/database.md` for design details.

The current market API serves clearly labeled simulated OHLCV candles for
paper-trading development. A real NEPSE data provider must be configured
separately after verifying its API terms and redistribution rights; the app
does not scrape or redistribute third-party chart data by default.

## Tech stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16
- **Auth**: JWT (access + refresh), Argon2 password hashing
- **Frontend** (Phase 6): React + Vite + TypeScript, Recharts
- **Containers**: Docker + docker-compose

## Project structure

```
nepse-paper-trader/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, middleware, error handlers
│   │   ├── config.py         # All settings, sourced from env
│   │   ├── database.py       # SQLAlchemy engine/session
│   │   ├── api/               # Routers (auth.py so far)
│   │   ├── models/            # SQLAlchemy ORM models (17 tables)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # DB access layer
│   │   └── utils/             # security.py, errors.py
│   ├── alembic/                # Migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Scaffolded, built starting Phase 6
├── docs/
│   ├── architecture.md
│   └── database.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Getting started (local development)

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (or Docker)
- Docker + docker-compose (recommended — simplest path)

### Option A — Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

This starts Postgres and the backend, running `alembic upgrade head`
automatically on boot. API docs at http://localhost:8000/docs.

### Option B — Local API without PostgreSQL

For frontend and auth development, the backend defaults to a local SQLite
database when `DATABASE_URL` is not set. This mode creates its tables on
startup and is not intended for production:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000. The market endpoints are:

```text
GET /api/v1/market/stocks
GET /api/v1/market/stocks/{symbol}/prices
```

Both return simulated data until a licensed provider is configured.

**Before the first run**, generate the initial migration (only needs to
be done once, after which it's committed to the repo):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# with DATABASE_URL pointed at a running Postgres (e.g. via `docker compose up postgres -d`):
alembic revision --autogenerate -m "initial schema"
```

### Option C — Manual PostgreSQL

```bash
# 1. Postgres
docker run -d --name nepse-db -p 5432:5432 \
  -e POSTGRES_USER=nepse -e POSTGRES_PASSWORD=nepse_dev_password \
  -e POSTGRES_DB=nepse_paper_trader postgres:16-alpine

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # edit DATABASE_URL if not using the defaults above
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
uvicorn app.main:app --reload
```

API now running at http://localhost:8000 — interactive docs at `/docs`,
ReDoc at `/redoc`.

## Environment variables

See `.env.example` for the full list (database, JWT secrets, initial
virtual balance, fee schedule, market hours, rate limits). Never commit
a real `.env` file.

## Testing

```bash
cd backend
pytest
```

(Test suite is built out in Phase 10.)

## API overview so far

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account, receive NPR 1,000,000 virtual balance |
| POST | `/api/v1/auth/login` | Get access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Exchange refresh token for a new access token |
| POST | `/api/v1/auth/logout` | Client-side token discard |
| GET  | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/auth/change-password` | Change password |
| GET  | `/health` | Liveness check |
| GET  | `/ready` | Readiness check (verifies DB connectivity) |

Full API surface grows through the remaining phases — see
`docs/architecture.md`.

## Security notes

- Passwords hashed with Argon2, never stored or logged in plaintext.
- JWT access tokens (60 min) + refresh tokens (7 days), both configurable.
- Every sensitive action (login, failed login, password change, trades,
  admin edits) is written to `audit_logs`.
- All monetary values use `NUMERIC(18,4)` — never floating point.
- Consistent `{success, error: {code, message}}` error envelope; no
  stack traces are ever returned to the client.

## Disclaimer

NEPSE Paper Trader is a paper-trading simulation platform. It does not
execute real securities transactions and does not provide investment
advice. Market data is simulated/demo data unless a real market-data
provider has been explicitly connected and documented as such.

## License

MIT (see `LICENSE`).
