"""
Central application configuration.

Every value that could plausibly need to change between environments
(dev / staging / production) or that a future engineer might otherwise
hardcode lives here, sourced from environment variables / .env.

Nothing in the rest of the codebase should read os.environ directly —
always go through `get_settings()`.
"""
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    # --- App ---
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "NEPSE Paper Trader"

    # --- Database ---
    # SQLite keeps a fresh checkout runnable locally; Render overrides this
    # with its managed PostgreSQL connection string.
    DATABASE_URL: str = "sqlite:///./nepse_paper_trader.db"

    # --- Security ---
    SECRET_KEY: str = "dev-secret-key-change-me"
    JWT_SECRET: str = "dev-jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- Paper trading ---
    INITIAL_VIRTUAL_BALANCE: Decimal = Decimal("1000000")
    BASE_CURRENCY: str = "NPR"

    # --- Fees (demo/simulation values — NOT real NEPSE/broker charges) ---
    FEE_COMMISSION_PCT: Decimal = Decimal("0.36")
    FEE_REGULATORY_PCT: Decimal = Decimal("0.015")
    FEE_SEBON_PCT: Decimal = Decimal("0.015")
    FEE_SETTLEMENT_PCT: Decimal = Decimal("0.01")

    # --- Market data ---
    MARKET_MODE: str = "demo"  # "demo" | "real" (future)
    MARKET_API_BASE_URL: str = ""
    MARKET_API_KEY: str = ""
    MARKET_DATA_DELAY_SECONDS: int = 0
    MARKET_TIMEZONE: str = "Asia/Kathmandu"
    MARKET_OPEN: str = "11:00"
    MARKET_CLOSE: str = "15:00"
    TRADING_DAYS: str = "SUN,MON,TUE,WED,THU"

    @property
    def trading_days_list(self) -> List[str]:
        return [d.strip().upper() for d in self.TRADING_DAYS.split(",") if d.strip()]

    # --- Demo market engine ---
    DEMO_PRICE_VOLATILITY_PCT: Decimal = Decimal("1.5")
    DEMO_TICK_INTERVAL_SECONDS: int = 5

    # --- Rate limiting ---
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_ORDERS: str = "20/minute"

    # --- Demo account ---
    CREATE_DEMO_ACCOUNT: bool = True
    DEMO_ACCOUNT_EMAIL: str = "demo@example.com"
    DEMO_ACCOUNT_PASSWORD: str = "DemoPassword123!"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENV.lower() == "production":
            placeholders = {
                "dev-secret-key-change-me",
                "dev-jwt-secret-change-me",
                "change-this-to-a-long-random-string",
                "change-this-to-a-different-long-random-string",
            }
            if self.SECRET_KEY in placeholders or self.JWT_SECRET in placeholders:
                raise ValueError("SECRET_KEY and JWT_SECRET must be real secrets in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
