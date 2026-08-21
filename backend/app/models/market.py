from datetime import datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin

MONEY = Numeric(18, 4)


class MarketPrice(UUIDPrimaryKeyMixin, Base):
    """One OHLCV candle for a stock. Used to render price/volume charts
    across 1D/1W/1M/3M/6M/1Y/ALL timeframes.
    """
    __tablename__ = "market_prices"

    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    open_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    high_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    low_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    close_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    is_simulated: Mapped[bool] = mapped_column(default=True, nullable=False)

    stock = relationship("Stock", back_populates="price_history")


class MarketSession(UUIDPrimaryKeyMixin, Base):
    """A trading-day record used by MarketSessionService to answer
    is_market_open() / get_market_status() without hardcoding schedule
    logic across the app. Generated/looked up from config.MARKET_* settings;
    this table lets admins override a specific date (e.g. public holiday).
    """
    __tablename__ = "market_sessions"

    session_date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    is_trading_day: Mapped[bool] = mapped_column(default=True, nullable=False)
    open_time: Mapped[str] = mapped_column(nullable=True)   # "HH:MM", overrides config default if set
    close_time: Mapped[str] = mapped_column(nullable=True)
    note: Mapped[str] = mapped_column(nullable=True)  # e.g. "Public holiday"
