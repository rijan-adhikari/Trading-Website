from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_client_ip
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    database_url = "sqlite:///" + str(tmp_path / "paper-trader-test.db")
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def register_and_get_token(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Trader",
            "username": "test_trader",
            "email": "trader@example.com",
            "password": "PaperTrade123!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["access_token"]


def test_health_and_readiness_endpoints(client):
    assert client.get("/health").status_code == 200
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] is True


def test_registered_user_can_buy_and_sell_virtual_shares(client):
    token = register_and_get_token(client)
    headers = {"Authorization": "Bearer " + token}

    buy = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"symbol": "NABIL", "side": "BUY", "quantity": 2, "order_type": "MARKET"},
    )
    assert buy.status_code == 201, buy.text
    assert buy.json()["data"]["status"] == "FILLED"

    portfolio = client.get("/api/v1/portfolio", headers=headers)
    assert portfolio.status_code == 200, portfolio.text
    data = portfolio.json()["data"]
    assert len(data["positions"]) == 1
    assert data["positions"][0]["quantity"] == 2
    assert Decimal(data["cash_balance"]) < Decimal("1000000")

    sell = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"symbol": "NABIL", "side": "SELL", "quantity": 2, "order_type": "MARKET"},
    )
    assert sell.status_code == 201, sell.text

    final_portfolio = client.get("/api/v1/portfolio", headers=headers).json()["data"]
    assert final_portfolio["positions"] == []
    assert Decimal(final_portfolio["cash_balance"]) < Decimal("1000000")
    transactions = client.get("/api/v1/transactions", headers=headers)
    assert transactions.status_code == 200
    rows = transactions.json()["data"]
    assert len(rows) == 2
    buy_row = next(row for row in rows if row["side"] == "BUY")
    sell_row = next(row for row in rows if row["side"] == "SELL")
    # Realized P&L includes the buy fee in cost basis and deducts the sell fee.
    assert Decimal(sell_row["realized_pl"]) == Decimal(sell_row["net_amount"]) - abs(Decimal(buy_row["net_amount"]))


def test_order_endpoint_requires_authentication(client):
    response = client.post(
        "/api/v1/orders",
        json={"symbol": "NABIL", "side": "BUY", "quantity": 1, "order_type": "MARKET"},
    )
    assert response.status_code == 401


def test_client_ip_does_not_trust_unverified_forwarded_header():
    request = Request({
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"x-forwarded-for", b"198.51.100.77")],
        "client": ("203.0.113.12", 12345),
        "server": ("testserver", 80),
    })
    assert get_client_ip(request) == "203.0.113.12"
