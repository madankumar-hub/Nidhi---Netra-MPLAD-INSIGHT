"""Schema creation / bootstrap.

For the hackathon build the schema is created directly from the SQLAlchemy
metadata, which keeps `docker compose up` a single step. A production
deployment would introduce Alembic revisions; see docs/DATABASE.md.
"""
from __future__ import annotations

import logging

from app.database.base import Base
from app.database.session import engine

logger = logging.getLogger("mplad.db")


def init_database() -> None:
    import app.models  # noqa: F401  - registers every mapper

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema verified (%s tables).", len(Base.metadata.tables))


def drop_database() -> None:
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped.")
