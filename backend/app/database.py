"""
SQLAlchemy engine + session management.

`get_db` is the FastAPI dependency every route/service uses to obtain a
scoped session. Nothing outside this module should construct an engine.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


def normalize_database_url(url: str) -> str:
    """Normalize provider URLs before passing them to SQLAlchemy 2.x."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


database_url = normalize_database_url(settings.DATABASE_URL)
is_sqlite = database_url.startswith("sqlite")

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    # Keep the connection footprint small for Neon Free and Render Free.
    # Neon suspends idle compute; pre-ping/recycle discard stale connections.
    pool_size=2,
    max_overflow=1,
    pool_timeout=20,
    pool_recycle=300,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db() -> Generator:
    """FastAPI dependency: yields a request-scoped DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Context manager for scripts/services that aren't inside a FastAPI request
    (e.g. seed script, demo market engine background task). Commits on success,
    rolls back on error, always closes.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
