"""
SQLAlchemy engine / session for the membership & payments data layer.

The project previously had no persistence (tasks & transcripts were in-memory
dicts). This module adds a small SQLite database so we can store users,
memberships, daily usage counters and already-processed Stripe webhook events
(for idempotency). SQLite keeps deployment trivial; for a light traffic site
this is plenty and avoids a migration tool.

Python 3.9 compatible: no PEP 604 ``X | Y`` unions, no ``match``.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# The DB lives under backend/data/ (already git-ignored via ``backend/data/``).
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(exist_ok=True)

_DEFAULT_DB = f"sqlite:///{(_DATA_DIR / 'app.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# ``check_same_thread=False``: FastAPI runs sync ``def`` endpoints in a thread
# pool, so a session may be used from a different thread than the one that made
# it. SQLite handles this fine with a per-request session + WAL not needed at
# our scale.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create all tables (idempotent — SQLAlchemy uses ``IF NOT EXISTS``)."""
    # Import models so they register on Base.metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI-style dependency yielding a scoped session.

    Because quota / membership checks are short-lived and self-contained we
    mostly open our own sessions inside the helpers; this generator is provided
    for routes that want an explicit injected session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
