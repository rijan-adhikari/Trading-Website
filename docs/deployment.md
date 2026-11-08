# Render deployment

This repository includes a Render Blueprint at the repository root. It defines one FastAPI web service, one static Vite frontend, and one managed PostgreSQL database.

## Deploy

1. Push or merge the intended release branch into the GitHub branch you want Render to deploy.
2. In Render, choose **New → Blueprint** and connect this repository.
3. Review the three resources before applying the Blueprint.
4. Allow the API build to install `backend/requirements.txt`. Its start command runs `alembic upgrade head` before starting Uvicorn.
5. Allow the static site to run `npm ci && npm run build`. The `VITE_API_URL` value is embedded into the frontend at build time.
6. Confirm the API's `/ready` endpoint returns HTTP 200 and the static site can reach the API.
7. If the generated frontend hostname changes, update the API's `CORS_ORIGINS` environment variable to the exact HTTPS origin and redeploy the API.

The Blueprint pins the API runtime to Python 3.12.16, matching CI, and generates `SECRET_KEY` and `JWT_SECRET` values. Do not replace them with the example development values. The backend rejects short production secrets and refuses to start in production with SQLite.

## Important hosting limitation

The Blueprint intentionally uses Render's Free PostgreSQL plan to avoid silently creating a paid resource. This is suitable for a temporary demo, **not a durable production launch**:

- Free Render Postgres databases expire 30 days after creation. After expiry, there is a 14-day upgrade grace period before deletion.
- Free web services spin down after 15 minutes without inbound traffic and can take about a minute to wake.
- Free web services have ephemeral local filesystems; the application database must remain in PostgreSQL.

Before accepting real users or relying on saved accounts, upgrade the database to a paid PostgreSQL plan, verify backups/restore procedures, and choose an appropriate paid API service plan. Do not rely on the Free database for user records or trading history.

## Functional scope and data integrity

This release is a paper-trading MVP. It uses five hardcoded sample quotes and generated OHLCV candles. It does **not** connect to NEPSE or a licensed market-data provider. All quotes and orders are simulated. Do not advertise the current feed as live NEPSE data.

Market orders execute immediately against the configured demo quote, even outside NEPSE's trading session. Limit/stop orders, real-time market-session enforcement, user watchlists, price alerts, notification delivery, refresh-token revocation, and full operational monitoring are not implemented.

The simulated fee schedule is configurable and is not represented as the official current broker/SEBON fee schedule. Buy-side fees are included in the position cost basis and sell-side fees are deducted from realized proceeds.

## Local verification

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -q tests
```

Then build the frontend:

```bash
cd ../frontend
npm ci
npm run build
```

The GitHub Actions workflow runs these checks on pushes to `main` and `production-hardening`, and on pull requests targeting `main`.
