from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

MONEY = Numeric(18, 4)


class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One-per-user paper-trading account. `cash_balance` is the single
    source of truth for spendable virtual money; it is only ever mutated
    inside TradingService's database transaction, never set directly by
    an API route. `realized_pl` accumulates every SELL's realized P/L.
    """
    __tablename__ = "portfolios"

    user_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    cash_balance: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    initial_balance: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    realized_pl: Mapped[MONEY] = mapped_column(MONEY, default=0, nullable=False)

    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class Position(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Open holding of one stock within a portfolio. Weighted-average cost
    method: average_price is recomputed on
    every buy; sells reduce quantity without touching average_price.
    A position with quantity == 0 is deleted rather than kept at zero.
    """
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("portfolio_id", "stock_id", name="uq_position_portfolio_stock"),)

    portfolio_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    stock_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    average_price: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    portfolio = relationship("Portfolio", back_populates="positions")
    stock = relationship("Stock")


class PortfolioSnapshot(UUIDPrimaryKeyMixin, Base):
    """Reserved schema for future point-in-time portfolio history.
    This release does not write snapshots or expose a snapshot-history API.
    """
    __tablename__ = "portfolio_snapshots"

    portfolio_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    cash_balance: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    market_value: Mapped[MONEY] = mapped_column(MONEY, nullable=False)
    total_value: Mapped[MONEY] = mapped_column(MONEY, nullable=False)

    portfolio = relationship("Portfolio", back_populates="snapshots")
