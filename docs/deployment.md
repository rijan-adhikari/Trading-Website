# Free deployment: Render + Neon

This repository uses Render for the FastAPI API and static React frontend, with Neon Free for persistent PostgreSQL. The Blueprint intentionally does **not** create a Render database, paid service, custom domain, or other billable resource.

## Free-tier architecture

- **Render Free Web Service:** FastAPI backend. It sleeps after 15 minutes without inbound traffic and can take about a minute to wake.
- **Render Static Site:** React/Vite frontend. Static sites do not use a paid compute instance.
- **Neon Free:** PostgreSQL database. Free compute suspends after inactivity and wakes when a connection arrives. The free plan has a limited storage and compute allowance; check the current Neon plan page before relying on its quotas.
- **TLS:** Render-managed HTTPS for the frontend and API.
- **Domain:** Use the supplied `.onrender.com` hostname. A custom domain is optional and may cost money.

The free tiers have limitations. This setup is for a low-traffic educational paper-trading demo, not a production financial service or a guarantee of uninterrupted availability.

## 1. Create the Neon database

1. Create a free account at [Neon](https://neon.tech/).
2. Create a project, for example `nepse-paper-trader`.
3. Select a region geographically close to the expected users, if available.
4. Open the project's **Connect** dialog.
5. Select the database, role, and **Pooled connection** option.
6. Copy the PostgreSQL connection string. It should use the pooled hostname (usually includes `-pooler`) and require TLS, for example `postgresql://...@...-pooler.../neondb?sslmode=require`.
7. Treat this URL as a password: do not commit it, paste it into an issue, or share it publicly.

Use Neon's pooled connection string for the Render API. The application uses a small SQLAlchemy pool (2 persistent connections, 1 overflow) to limit connection usage and recycle stale connections after Neon suspends idle compute.

## 2. Deploy the Render Blueprint

1. Push or merge the intended release branch into the GitHub branch you want Render to deploy.
2. In Render, choose **New → Blueprint** and connect this repository.
3. Review the Blueprint resources: it should create only the free API web service and static frontend. It must not show a Render database or paid plan.
4. Apply the Blueprint.
5. Open the API service's **Environment** settings and set `DATABASE_URL` to the pooled Neon connection string copied above. Do not add quotation marks around it.
6. Save the variable and let Render redeploy the API.
7. Confirm the API's `/ready` endpoint returns HTTP 200 and reports `"database": true`.
8. Open the static frontend and test registration, login, paper orders, portfolio, and transaction history.

The Blueprint sets `DATABASE_URL` as `sync: false`, so Render asks you to provide the secret rather than storing it in Git. It generates a separate strong `JWT_SECRET`. The backend refuses to start in production with SQLite or a short/default JWT secret.

If the generated frontend hostname differs from `https://nepse-paper-trader-web.onrender.com`, update the API's `CORS_ORIGINS` environment variable to the exact frontend origin and redeploy.

## 3. Database migrations

The API start command runs `alembic upgrade head` before Uvicorn. On first deployment, this creates the application tables in the empty Neon database. Subsequent restarts apply only unapplied migrations.

Do not run migrations against an existing database until you have checked its contents and taken an export. If migrating existing user data from another database, export it first and import it into Neon; deploying the schema alone does not copy existing accounts or trades.

## 4. Free-tier limitations and data safety

- Render Free web services spin down after 15 minutes without inbound traffic. A first request after idle may be slow.
- Neon Free compute can suspend when idle and may take a moment to wake. Its storage, compute-hours, branches and other quotas are limited by the current free plan.
- Render's local filesystem is ephemeral. The app must store persistent records only in Neon, not local files.
- Free tiers can change, impose quotas, or suspend resources. Monitor both provider dashboards.
- This configuration does not create paid Render resources. Do not upgrade a plan or add a paid database.
- A free database is not a backup strategy. Periodically export the Neon database and keep a copy on your own computer. Test restoring an export before trusting it.
- Do not store real money, broker credentials, or sensitive financial data in this educational simulator.

## 5. Local verification

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

The GitHub Actions workflow runs backend tests, PostgreSQL migrations, dependency audits, and the frontend production build on pushes to `main` and `production-hardening`, and on pull requests targeting `main`.

## Functional scope and data integrity

This release is a paper-trading MVP. It uses five hardcoded sample quotes and generated OHLCV candles. It does **not** connect to NEPSE or a licensed market-data provider. All quotes and orders are simulated. Do not advertise the current feed as live NEPSE data.

Market orders execute immediately against the configured demo quote, even outside NEPSE's trading session. Limit/stop orders, real-time market-session enforcement, user watchlists, price alerts, notification delivery, refresh-token revocation, and full operational monitoring are not implemented.

The simulated fee schedule is configurable and is not represented as the official current broker/SEBON fee schedule. Buy-side fees are included in the position cost basis and sell-side fees are deducted from realized proceeds.
