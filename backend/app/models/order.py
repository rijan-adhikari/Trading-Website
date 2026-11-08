from sqlalchemy import BigInteger, Enum, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import OrderSide, OrderStatus, OrderType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

MONEY = Numeric(18, 4)


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's buy/sell instruction. This release creates and fills MARKET
    orders synchronously. LIMIT-related columns are reserved for future
    functionality; there is no limit-order execution worker.
    """
    __tablename__ = "orders"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="order_side"), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType, name="order_type"), nullable=False)

    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    limit_price: Mapped[MONEY] = mapped_column(MONEY, nullable=True)  # required for LIMIT, null for MARKET

    executed_quantity: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    average_fill_price: Mapped[MONEY] = mapped_column(MONEY, nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.PENDING, nullable=False, index=True
    )
    rejection_reason: Mapped[str] = mapped_column(nullable=True)

    user = relationship("User", back_populates="orders")
    stock = relationship("Stock")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")
