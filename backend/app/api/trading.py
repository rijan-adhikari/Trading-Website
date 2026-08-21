from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.trading import OrderCreateRequest, OrderResponse, PortfolioResponse, PositionResponse, TransactionResponse
from app.services.trading_service import TradingService

router = APIRouter(tags=["trading"])


def order_response(order: Order) -> OrderResponse:
    return OrderResponse(id=order.id, symbol=order.stock.symbol, side=order.side, order_type=order.order_type, quantity=order.quantity, executed_quantity=order.executed_quantity, average_fill_price=order.average_fill_price, status=order.status, created_at=order.created_at)


@router.post("/orders", response_model=SuccessResponse[OrderResponse], status_code=201)
def create_order(payload: OrderCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return SuccessResponse(data=order_response(TradingService(db).execute_market_order(user, payload.symbol, payload.side, payload.quantity, payload.order_type)))


@router.get("/orders", response_model=SuccessResponse[list[OrderResponse]])
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())).all()
    return SuccessResponse(data=[order_response(order) for order in orders])


@router.get("/portfolio", response_model=SuccessResponse[PortfolioResponse])
def portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
    if account is None:
        from app.utils.errors import NotFoundError
        raise NotFoundError("Portfolio not found.")
    positions = []
    market_value = 0
    unrealized = 0
    for position in account.positions:
        price = position.stock.current_price
        value = price * position.quantity
        pnl = (price - position.average_price) * position.quantity
        market_value += value
        unrealized += pnl
        positions.append(PositionResponse(symbol=position.stock.symbol, company_name=position.stock.company_name, quantity=position.quantity, average_price=position.average_price, current_price=price, market_value=value, unrealized_pl=pnl))
    return SuccessResponse(data=PortfolioResponse(cash_balance=account.cash_balance, initial_balance=account.initial_balance, realized_pl=account.realized_pl, market_value=market_value, total_value=account.cash_balance + market_value, unrealized_pl=unrealized, positions=positions))


@router.get("/transactions", response_model=SuccessResponse[list[TransactionResponse]])
def transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc())).all()
    return SuccessResponse(data=[TransactionResponse(id=row.id, symbol=row.stock.symbol if row.stock else None, type=row.type, side=row.side, quantity=row.quantity, price=row.price, gross_amount=row.gross_amount, fees=row.fees, net_amount=row.net_amount, realized_pl=row.realized_pl, balance_after=row.balance_after, created_at=row.created_at) for row in rows])