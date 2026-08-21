from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import OrderSide, OrderStatus, OrderType, TransactionType


class OrderCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: OrderSide
    quantity: int = Field(gt=0, le=1_000_000)
    order_type: OrderType = OrderType.MARKET


class OrderResponse(BaseModel):
    id: UUID
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    executed_quantity: int
    average_fill_price: Decimal | None
    status: OrderStatus
    created_at: datetime


class PositionResponse(BaseModel):
    symbol: str
    company_name: str
    quantity: int
    average_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal


class PortfolioResponse(BaseModel):
    cash_balance: Decimal
    initial_balance: Decimal
    realized_pl: Decimal
    market_value: Decimal
    total_value: Decimal
    unrealized_pl: Decimal
    positions: list[PositionResponse]


class TransactionResponse(BaseModel):
    id: UUID
    symbol: str | None
    type: TransactionType
    side: OrderSide | None
    quantity: int | None
    price: Decimal | None
    gross_amount: Decimal
    fees: Decimal
    net_amount: Decimal
    realized_pl: Decimal | None
    balance_after: Decimal
    created_at: datetime