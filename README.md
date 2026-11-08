# NEPSE Paper Trader

A browser-based paper-trading MVP for learning the mechanics of NEPSE share trading with virtual NPR. It does not connect to a broker, execute real securities transactions, or provide investment advice.

> **Data disclaimer:** the current market feed contains five hardcoded sample quotes and generated OHLCV candles. It is simulated development data, not live NEPSE market data.

## Current release

### Implemented
- Registration and login with Argon2 password hashing.
- JWT access tokens and refresh endpoint; the frontend stores both tokens and refreshes an expired access token.
- One virtual portfolio per user, initially funded with NPR 1,000,000 by default.
- Simulated market list and generated five-minute candles for five sample symbols.
- Immediate market BUY/SELL paper orders.
- Weighted-average position cost basis, including simulated buy-side fees.
- Sell-side fees deducted from realized proceeds and realized P&L.
- Persisted orders, trades, transactions and audit log entries.
- Basic admin user activation/suspension endpoints.
- Docker Compose and Render Blueprint deployment definitions.

### Not implemented
- Live NEPSE market data or a licensed data-provider integration.
- Full NEPSE symbol directory, company fundamentals, historical exchange candles or official index feed.
- Limit, stop or stop-limit order execution.
- Market-session/holiday enforcement; demo market orders fill immediately against the sample quote, including outside exchange hours.
- User-managed watchlists, price alerts, notification delivery or portfolio history charts.
- Refresh-token revocation/rotation, email verification, password reset or multi-factor authentication.
- Complete admin role provisioning, operational monitoring or comprehensive PostgreSQL integration tests.

The current simulator is an MVP and must not be marketed as a live-data or production brokerage product.

## Technology

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL
- **Authentication:** JWT, Argon2
- **Frontend:** React + Vite
- **Testing:** pytest, FastAPI TestClient
- **Deployment:** Docker Compose and Render Blueprint

## Repository layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/             # auth, admin, market and trading routes
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # authentication, audit and trading logic
│   │   └── utils/           # security and API errors
│   ├── alembic/             # database migrations
│   ├── tests/               # unit and API integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/main.jsx
│   ├── src/styles.css
│   └── package-lock.json
├── docs/
│   ├── architecture.md
│   ├── database.md
│   └── deployment.md
├── .github/workflows/ci.yml
├── docker-compose.yml
├── render.yaml
└── .env.example
```

## Run locally

### Backend with SQLite (development only)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload
```

The development app creates SQLite tables on startup. SQLite is not allowed when `ENV=production`.

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000/api/v1`. Override it with `VITE_API_URL` if the backend runs elsewhere.

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This starts PostgreSQL and the API. The backend container applies the committed Alembic migration before starting.

## API overview

All application routes are under `/api/v1`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register and create a funded paper portfolio |
| POST | `/auth/login` | Authenticate and issue access/refresh tokens |
| POST | `/auth/refresh` | Issue a new access token |
| POST | `/auth/logout` | Client-side logout acknowledgement; tokens are not revoked server-side |
| GET | `/auth/me` | Current user |
| POST | `/auth/change-password` | Change password |
| GET | `/market/stocks` | Five simulated sample quotes |
| GET | `/market/stocks/{symbol}/prices` | Generated demo candles |
| POST | `/orders` | Execute an immediate market paper order |
| GET | `/orders` | Current user's orders |
| GET | `/portfolio` | Current user's cash, holdings and P&L |
| GET | `/transactions` | Current user's transaction ledger |
| GET | `/admin/users` | Admin-only user directory |
| PATCH | `/admin/users/{user_id}` | Admin-only account activation status |

System endpoints: `GET /health` (liveness) and `GET /ready` (database readiness; returns 503 when the database is unavailable).

## Tests and build

```bash
cd backend
PYTHONPATH=. pytest -q tests
cd ../frontend
npm ci
npm run build
```

GitHub Actions runs backend tests and the frontend production build on pushes to `main` / `production-hardening` and pull requests targeting `main`.

## Deployment

See [docs/deployment.md](docs/deployment.md) for the Render Blueprint setup, required environment configuration and free-tier limitations.

The Blueprint currently uses Free Render Postgres to avoid creating a paid resource without approval. Free Postgres expires after 30 days, so upgrade to a paid database and verify backups before storing data for real users.

## Trading assumptions

- Default starting capital: NPR 1,000,000 virtual cash.
- The configured NEPSE trading week is Monday–Friday, 11:00–15:00 Nepal time. This is configuration/documentation only; the current demo execution endpoint does not enforce market sessions or holidays.
- All fee percentages are illustrative simulator settings, not the official current broker/SEBON/DP fee schedule.
- Buy fees are included in average cost basis; sell fees reduce net proceeds and realized P&L.
- All money calculations use `NUMERIC(18,4)` / Python `Decimal`, not binary floating point.

## Security notes

- Never commit `.env`, API keys, database URLs or production secrets.
- Production requires long random `SECRET_KEY` and `JWT_SECRET` values and a PostgreSQL `DATABASE_URL`.
- The frontend stores JWTs in browser localStorage. This is convenient for the MVP but increases exposure if an XSS vulnerability is introduced.
- Logout currently removes browser tokens only; previously issued refresh tokens remain valid until expiry.
- Admin endpoints enforce the ADMIN role server-side. Do not grant this role to untrusted users.

## Disclaimer

NEPSE Paper Trader is an educational simulation. It is not affiliated with NEPSE or SEBON, is not a broker or investment adviser, and does not place real orders or hold real money. Simulated performance is not evidence of future investment returns.

## Author

Developed by [Rijan Adhikari](https://github.com/rijan-adhikari).

- Portfolio: https://adhikari-rijan.onrender.com/
- GitHub: https://github.com/rijan-adhikari
