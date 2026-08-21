from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StockStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# All monetary/price columns use Numeric(18, 4) — never Float — so
# calculations never suffer floating point rounding error.
MONEY = Numeric(18, 4)


class Sector(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sectors"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    stocks = relationship("Stock", back_populates="sector")


class Stock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("sectors.id"), nullable=False)

    listed_shares: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    current_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    previous_close: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    open_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    high_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    low_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    turnover: Mapped[MONEY] = mapped_column(MONEY, default=0, nullable=False)
    market_cap: Mapped[MONEY] = mapped_column(MONEY, default=0, nullable=False)

    week_52_high: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    week_52_low: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    status: Mapped[StockStatus] = mapped_column(
        Enum(StockStatus, name="stock_status"), default=StockStatus.ACTIVE, nullable=False
    )
    last_price_update: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Every seeded row is demo data unless a real provider is wired in later
    # (see MarketDataProvider). This flag lets the frontend show the
    # "Simulated market data" label without guessing.
    is_simulated: Mapped[bool] = mapped_column(default=True, nullable=False)

    sector = relationship("Sector", back_populates="stocks")
    price_history = relationship("MarketPrice", back_populates="stock", cascade="all, delete-orphan")
