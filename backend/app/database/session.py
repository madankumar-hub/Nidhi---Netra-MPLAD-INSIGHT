"""SQLAlchemy engine / session factory.

Supports PostgreSQL (recommended, per SRS section 2.3) and SQLite for
zero-config local development.
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

# Managed PostgreSQL services recycle idle connections aggressively, so the
# pool is kept small and every checkout is pinged first.
pool_kwargs = (
    {}
    if settings.is_sqlite
    else {"pool_size": 5, "max_overflow": 5, "pool_recycle": 280}
)

engine = create_engine(
    settings.sqlalchemy_url,
    connect_args=connect_args,
    pool_pre_ping=not settings.is_sqlite,
    future=True,
    **pool_kwargs,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
