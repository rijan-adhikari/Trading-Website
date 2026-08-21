import enum


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    # Reserved for future versions — not executable yet, kept here so the
    # schema/enum doesn't need a migration when they're implemented.
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    FEE = "FEE"
    ADJUSTMENT = "ADJUSTMENT"  # admin balance adjustments — always audit-logged


class StockStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"


class MarketStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"


class AlertCondition(str, enum.Enum):
    GTE = "GTE"  # price >=
    LTE = "LTE"  # price <=


class NotificationType(str, enum.Enum):
    TRADE_EXECUTED = "TRADE_EXECUTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    PRICE_ALERT = "PRICE_ALERT"
    SYSTEM = "SYSTEM"
