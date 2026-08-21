from sqlalchemy import BigInteger, Enum, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import OrderSide, TransactionType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

MONEY = Numeric(18, 4)


class Trade(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single fill against an order. Most orders in v1 produce exactly
    one trade (full fill), but the table exists so PARTIALLY_FILLED orders
    can record multiple fills without a schema change later.
    """
    __tablename__ = "trades"

    order_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    order = relationship("Order", back_populates="trades")


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The ledger. Every cash-affecting event (buy, sell, fee, admin
    adjustment) creates exactly one row here — this is what /transactions
    and the profile's "total realized P/L" stat read from, so it must never
    be written to except inside OrderExecutionService's DB transaction.
    """
    __tablename__ = "transactions"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=True)

    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, name="transaction_type"), nullable=False)
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="txn_side"), nullable=True)

    quantity: Mapped[int] = mapped_column(BigInteger, nullable=True)
    price: Mapped[MONEY] = mapped_column(MONEY, nullable=True)
    gross_amount: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    fees: Mapped[MONEY] = mapped_column(MONEY, default=0, nullable=False)
    net_amount: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    realized_pl: Mapped[MONEY] = mapped_column(MONEY, nullable=True)  # populated for SELL rows only

    balance_after: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    user = relationship("User", back_populates="transactions")
    stock = relationship("Stock")
