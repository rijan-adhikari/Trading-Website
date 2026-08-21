from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AlertCondition
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

MONEY = Numeric(18, 4)


class Watchlist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user can have multiple named watchlists (architecture supports
    it now even though v1 UI only surfaces the default "My Watchlist").
    """
    __tablename__ = "watchlists"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), default="My Watchlist", nullable=False)
    is_default: Mapped[bool] = mapped_column(default=True, nullable=False)

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("watchlist_id", "stock_id", name="uq_watchlist_stock"),)

    watchlist_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("watchlists.id"), nullable=False)
    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")
    stock = relationship("Stock")


class PriceAlert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User-defined trigger, e.g. "alert me when NABIL >= 600". Evaluated
    by the demo market engine on every price tick; once triggered it fires
    a Notification and is marked is_active=False (one-shot, not recurring).
    """
    __tablename__ = "price_alerts"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    condition: Mapped[AlertCondition] = mapped_column(Enum(AlertCondition, name="alert_condition"), nullable=False)
    target_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
