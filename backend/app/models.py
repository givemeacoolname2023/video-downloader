"""
ORM models for membership & payments.

Four small tables:

- ``users``         — email+password accounts (membership belongs to a user).
- ``memberships``   — one active record per user; mirrors a Stripe subscription.
- ``daily_usage``   — per-subject-per-day counters for the free quota.
- ``processed_events`` — already-handled Stripe webhook event ids (idempotency).

``subject`` on ``daily_usage`` is a string of the form either ``user:<id>`` or
``device:<uuid>`` so we can count quota for logged-in users AND anonymous
visitors (a device id stored by the frontend) with one code path.

Python 3.9 compatible: ``from __future__ import annotations`` lets us use
``Mapped[Optional[...]]`` / forward refs without runtime evaluation problems.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # One user has 0..1 membership record (the latest; see memberships).
    membership: Mapped[Optional["Membership"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan: Mapped[str] = mapped_column(String(16), nullable=False, default="monthly")  # monthly|yearly
    # Stripe subscription status: active|trialing|past_due|unpaid|canceled|incomplete
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    price_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="membership")


class DailyUsage(Base):
    __tablename__ = "daily_usage"
    __table_args__ = (UniqueConstraint("subject", "date", name="uq_subject_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    handled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
