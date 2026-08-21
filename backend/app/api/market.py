from datetime import datetime, timedelta, timezone
import math

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/market", tags=["market"])

STOCKS = {
    "NABIL": {"name": "Nabil Bank", "price": 548.20, "change": 2.41},
    "NICA": {"name": "NIC Asia Bank", "price": 712.80, "change": 1.06},
    "SCB": {"name": "Standard Chartered", "price": 628.00, "change": -0.84},
    "HBL": {"name": "Himalayan Bank", "price": 265.40, "change": 0.57},
    "SHIVM": {"name": "Shivam Cement", "price": 532.00, "change": -1.28},
}


def candles_for(symbol: str, count: int = 48) -> list[dict]:
    stock = STOCKS[symbol]
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    candles = []
    for index in range(count):
        close = stock["price"] * (1 + 0.012 * math.sin(index / 4.2) + 0.004 * math.sin(index / 1.8))
        open_price = close * (1 - 0.003 * math.sin(index))
        high = max(open_price, close) * 1.006
        low = min(open_price, close) * 0.994
        candles.append({
            "timestamp": (now - timedelta(minutes=(count - index) * 5)).isoformat(),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": 1000 + index * 137,
            "is_simulated": True,
        })
    return candles


@router.get("/stocks")
def list_stocks():
    return {
        "success": True,
        "data": [
            {"symbol": symbol, "company_name": value["name"], "current_price": value["price"], "change_pct": value["change"], "is_simulated": True}
            for symbol, value in STOCKS.items()
        ],
    }


@router.get("/stocks/{symbol}/prices")
def stock_prices(symbol: str, limit: int = 48):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        raise HTTPException(status_code=404, detail="Stock symbol not found")
    return {"success": True, "data": {"symbol": symbol, "candles": candles_for(symbol, min(max(limit, 1), 500))}}
