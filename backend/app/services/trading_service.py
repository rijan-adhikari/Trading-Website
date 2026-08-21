from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.enums import OrderSide, OrderStatus, OrderType, TransactionType
from app.models.order import Order
from app.models.portfolio import Portfolio, Position
from app.models.stock import Sector, Stock
from app.models.transaction import Trade, Transaction
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.errors import InsufficientFundsError, InsufficientSharesError, NotFoundError, ValidationAPIError

settings = get_settings()
MONEY_PLACES = Decimal("0.0001")


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


class TradingService:
    def __init__(self, db: Session):
        self.db = db

    def _stock(self, symbol: str) -> Stock:
        from app.api.market import STOCKS

        quote = STOCKS.get(symbol.upper())
        if quote is None:
            raise NotFoundError("Symbol is not available in the current market feed.")
        stock = self.db.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
        if stock:
            stock.current_price = _money(quote["price"])
            return stock
        sector = self.db.scalar(select(Sector).where(Sector.name == "Demo Market"))
        if sector is None:
            sector = Sector(name="Demo Market")
            self.db.add(sector)
            self.db.flush()
        stock = Stock(
            symbol=symbol.upper(), company_name=quote["name"], sector_id=sector.id,
            listed_shares=0, current_price=_money(quote["price"]), previous_close=_money(quote["price"]),
            open_price=_money(quote["price"]), high_price=_money(quote["price"]), low_price=_money(quote["price"]),
            week_52_high=_money(quote["price"]), week_52_low=_money(quote["price"]),
        )
        self.db.add(stock)
        self.db.flush()
        return stock

    def execute_market_order(self, user: User, symbol: str, side: OrderSide, quantity: int, order_type: OrderType) -> Order:
        if order_type != OrderType.MARKET:
            raise ValidationAPIError("Only MARKET orders are enabled in this paper-trading release.")
        portfolio = self.db.scalar(select(Portfolio).where(Portfolio.user_id == user.id).with_for_update())
        if portfolio is None:
            raise NotFoundError("Portfolio not found.")
        stock = self._stock(symbol)
        price = _money(stock.current_price)
        gross = _money(price * quantity)
        fee_rate = sum((settings.FEE_COMMISSION_PCT, settings.FEE_REGULATORY_PCT, settings.FEE_SEBON_PCT, settings.FEE_SETTLEMENT_PCT), Decimal("0")) / Decimal("100")
        fees = _money(gross * fee_rate)
        position = self.db.scalar(select(Position).where(Position.portfolio_id == portfolio.id, Position.stock_id == stock.id).with_for_update())
        realized_pl = Decimal("0")
        if side == OrderSide.BUY:
            total = gross + fees
            if portfolio.cash_balance < total:
                raise InsufficientFundsError()
            old_quantity = position.quantity if position else 0
            if position:
                position.average_price = _money(((position.average_price * old_quantity) + (price * quantity)) / (old_quantity + quantity))
                position.quantity += quantity
            else:
                position = Position(portfolio_id=portfolio.id, stock_id=stock.id, quantity=quantity, average_price=price)
                self.db.add(position)
            portfolio.cash_balance = _money(portfolio.cash_balance - total)
            net = -total
        else:
            if position is None or position.quantity < quantity:
                raise InsufficientSharesError()
            realized_pl = _money((price - position.average_price) * quantity)
            position.quantity -= quantity
            if position.quantity == 0:
                self.db.delete(position)
            portfolio.cash_balance = _money(portfolio.cash_balance + gross - fees)
            portfolio.realized_pl = _money(portfolio.realized_pl + realized_pl)
            net = _money(gross - fees)

        order = Order(user_id=user.id, stock_id=stock.id, side=side, order_type=order_type, quantity=quantity, executed_quantity=quantity, average_fill_price=price, status=OrderStatus.FILLED)
        self.db.add(order)
        self.db.flush()
        self.db.add(Trade(order_id=order.id, quantity=quantity, price=price))
        self.db.add(Transaction(user_id=user.id, order_id=order.id, stock_id=stock.id, type=TransactionType.BUY if side == OrderSide.BUY else TransactionType.SELL, side=side, quantity=quantity, price=price, gross_amount=gross, fees=fees, net_amount=net, realized_pl=realized_pl if side == OrderSide.SELL else None, balance_after=portfolio.cash_balance))
        AuditService(self.db).log(action="PAPER_ORDER_FILLED", user_id=user.id, entity_type="order", entity_id=order.id, metadata={"symbol": stock.symbol, "side": side.value, "quantity": quantity})
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_orders(self, user_id: UUID) -> list[Order]:
        return list(self.db.scalars(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())))