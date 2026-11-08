"""
Central application configuration.

Every value that could plausibly need to change between environments
(dev / staging / production) or that a future engineer might otherwise
hardcode lives here, sourced from environment variables / .env files.

Nothing in the rest of the codebase should read os.environ directly —
always go through `get_settings()`.
"""
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Neon CLI writes to .env.local when no .env exists. Load both so
        # the local FastAPI app sees the same DATABASE_URL the CLI pulled.
        # Values in .env.local take precedence over .env.
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"),
        extra="ignore",
    )

    # --- App ---
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "NEPSE Paper Trader"

    # --- Database ---
    # SQLite is for local development only. Production supplies a persistent
    # PostgreSQL URL (Neon Free is the documented zero-cost hosted option).
    DATABASE_URL: str = "sqlite:///./nepse_paper_trader.db"

    # --- Security ---
    JWT_SECRET: str = "dev-jwt-secret-change-me-please-use-env"
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
    MARKET_MODE: str = "demo"  # demo-only release
    MARKET_TIMEZONE: str = "Asia/Kathmandu"
    MARKET_OPEN: str = "11:00"
    MARKET_CLOSE: str = "15:00"
    TRADING_DAYS: str = "MON,TUE,WED,THU,FRI"

    @property
    def trading_days_list(self) -> List[str]:
        return [d.strip().upper() for d in self.TRADING_DAYS.split(",") if d.strip()]

    # --- Rate limiting ---
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_ORDERS: str = "20/minute"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENV.lower() == "production":
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("Production requires a persistent PostgreSQL DATABASE_URL")
            placeholders = {
                "dev-jwt-secret-change-me",
                "dev-jwt-secret-change-me-please-use-env",
                "change-this-to-a-different-long-random-string",
            }
            if self.JWT_SECRET in placeholders or len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
        if self.MARKET_MODE.lower() != "demo":
            raise ValueError("Only MARKET_MODE=demo is supported until a licensed market-data provider is integrated")
        if self.JWT_ALGORITHM != "HS256":
            raise ValueError("Only HS256 JWT signing is supported")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
