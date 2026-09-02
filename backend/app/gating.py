"""
Free quota enforcement.

Decision (confirmed with owner): free accounts get a daily allowance of
downloads and AI calls, but the *output is not degraded* — a free user still
downloads at the platform's best available quality and gets full AI results.
Only the *count* is capped. Members are unlimited.

Counting model:
- ``category`` is ``download`` or ``ai``.
- A unit is consumed per attempt (a download task started, or an AI endpoint
  call). An attempt that later fails is not refunded (simplest, matches most
  download services).
- Each subject (``user:<id>`` or ``device:<id>``) is counted per calendar day.
- On login-free users, free quota is keyed by account; anonymous visitors are
  keyed by the device id the frontend sends.

Server authority: this is the only place that decides whether an action is
allowed. The frontend merely displays what the backend reports.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError

from . import security
from .db import SessionLocal
from .models import DailyUsage, Membership, User

logger = logging.getLogger(__name__)

# Category labels used inside daily_usage columns.
CATEGORY_DOWNLOAD = "download"
CATEGORY_AI = "ai"

_COLUMN_BY_CATEGORY = {
    CATEGORY_DOWNLOAD: "download_count",
    CATEGORY_AI: "ai_count",
}

_LIMIT_BY_CATEGORY = {
    CATEGORY_DOWNLOAD: security.FREE_DAILY_DOWNLOADS,
    CATEGORY_AI: security.FREE_DAILY_AI,
}


class QuotaExceeded(Exception):
    """Raised when a free subject has exhausted today's allowance for a category."""

    def __init__(self, category: str, limit: int):
        self.category = category
        self.limit = limit
        label = "下载" if category == CATEGORY_DOWNLOAD else "AI 功能"
        super().__init__(
            f"今日免费{label}次数已用完（每天 {limit} 次）。开通会员即可无限使用。"
        )


def today_str() -> str:
    """Return the quota day string (YYYY-MM-DD). Uses configured tz if available."""
    tz = security.QUOTA_TZ
    now = datetime.now()
    try:
        from zoneinfo import ZoneInfo

        if tz:
            now = datetime.now(ZoneInfo(tz))
    except Exception:  # noqa: BLE001 — fall back to server local date
        now = datetime.now()
    return now.strftime("%Y-%m-%d")


def _load_usage(session, subject: str, date: str) -> DailyUsage:
    """Return the DailyUsage row for (subject, date), creating it if missing."""
    row = session.query(DailyUsage).filter_by(subject=subject, date=date).first()
    if row:
        return row
    row = DailyUsage(subject=subject, date=date, download_count=0, ai_count=0)
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
    except IntegrityError:
        # Another thread created the row first — re-read it.
        session.rollback()
        row = session.query(DailyUsage).filter_by(subject=subject, date=date).first()
        if row is None:
            raise
    return row


def _membership_for_user_id(session, user_id: int) -> Optional[Membership]:
    return session.query(Membership).filter_by(user_id=user_id).order_by(Membership.id.desc()).first()


def is_member_user(user_id: Optional[int]) -> bool:
    """True when the user has an active, unexpired membership."""
    if not user_id:
        return False
    session = SessionLocal()
    try:
        return security.membership_active(_membership_for_user_id(session, user_id))
    finally:
        session.close()


def enforce_quota(subject: str, category: str, user_id: Optional[int] = None) -> dict:
    """Authorize (and record) one unit of *category* for *subject*.

    - If *user_id* is an active member, allow without counting (unlimited).
    - Otherwise enforce a daily cap, incrementing the counter for today.

    Returns a small ``used/limit/unlimited`` snapshot for logging/telemetry.
    Raises QuotaExceeded when the daily limit would be exceeded.
    """
    if category not in _COLUMN_BY_CATEGORY:
        raise ValueError(f"unknown quota category: {category}")

    column = _COLUMN_BY_CATEGORY[category]
    limit = _LIMIT_BY_CATEGORY[category]

    session = SessionLocal()
    try:
        # Members are unlimited regardless of daily counters.
        if user_id and security.membership_active(_membership_for_user_id(session, user_id)):
            return {"category": category, "used": 0, "limit": None, "unlimited": True}

        row = _load_usage(session, subject, today_str())
        used = getattr(row, column)
        if used >= limit:
            raise QuotaExceeded(category, limit)

        setattr(row, column, used + 1)
        session.commit()
        return {"category": category, "used": used + 1, "limit": limit, "unlimited": False}
    finally:
        session.close()


def quota_snapshot(subject: str, user_id: Optional[int] = None) -> dict:
    """Read-only snapshot for the frontend: current usage vs daily limits.

    Returns ``downloads`` and ``ai`` objects with ``used/limit/unlimited``.
    ``unlimited`` is true for members.
    """
    session = SessionLocal()
    try:
        membership = _membership_for_user_id(session, user_id) if user_id else None
        unlimited = security.membership_active(membership) if membership else False
        row = session.query(DailyUsage).filter_by(subject=subject, date=today_str()).first()
        used_dl = row.download_count if row else 0
        used_ai = row.ai_count if row else 0
    finally:
        session.close()

    return {
        "is_member": bool(unlimited),
        "downloads": {
            "used": used_dl,
            "limit": None if unlimited else security.FREE_DAILY_DOWNLOADS,
            "unlimited": unlimited,
        },
        "ai": {
            "used": used_ai,
            "limit": None if unlimited else security.FREE_DAILY_AI,
            "unlimited": unlimited,
        },
    }
