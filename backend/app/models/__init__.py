"""
Import every model module here. Alembic's env.py imports this package
so `Base.metadata` is fully populated before autogenerate diffs the schema.
Nothing else should need to import individual model modules directly —
`from app import models` then `models.User`, `models.Stock`, etc.
"""
from app.models.market import MarketPrice, MarketSession  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.portfolio import Portfolio, PortfolioSnapshot, Position  # noqa: F401
from app.models.stock import Sector, Stock  # noqa: F401
from app.models.system import AuditLog, Notification, SystemSetting  # noqa: F401
from app.models.transaction import Trade, Transaction  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.watchlist import PriceAlert, Watchlist, WatchlistItem  # noqa: F401
