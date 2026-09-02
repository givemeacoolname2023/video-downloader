"""
Auth & account routes.

- POST /api/auth/register — create an account (email+password), returns a JWT.
- POST /api/auth/login    — verify credentials, returns a JWT.
- GET  /api/auth/me       — current user + membership + quota (Bearer required).
- GET  /api/auth/device   — issue a stable, anonymous device id (for free-quota
                            counting without an account).
- GET  /api/quota         — public quota snapshot (works for anon via device id
                            or for a logged-in user via Bearer).

Password hashing + JWT live in ``security``; quota in ``gating``.
"""
import re
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from . import security, gating
from .db import SessionLocal
from .models import Membership, User

router = APIRouter(prefix="/api", tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


def _auth_user(token: str) -> Optional[User]:
    """Load a User from a decoded JWT, or None."""
    user_id = security.user_id_from_token(token)
    if not user_id:
        return None
    session = SessionLocal()
    try:
        return session.get(User, user_id)
    finally:
        session.close()


def current_user_id(request: Request) -> Optional[int]:
    """Resolve the authenticated user id from the request's Bearer token, or None."""
    return security.user_id_from_token(
        security.parse_bearer(request.headers.get("authorization"))
    )


def _membership_payload(member: Optional[Membership]) -> Optional[dict]:
    if not member:
        return None
    return {
        "plan": member.plan,
        "status": member.status,
        "current_period_end": member.current_period_end.isoformat()
        if member.current_period_end
        else None,
        "cancel_at_period_end": member.cancel_at_period_end,
    }


def _me_payload(user: User) -> dict:
    member = user.membership if hasattr(user, "membership") else None
    active = security.membership_active(
        {"status": member.status, "current_period_end": member.current_period_end}
        if member
        else None
    )
    quota = gating.quota_snapshot(f"user:{user.id}", user_id=user.id)
    return {
        "user": {"id": user.id, "email": user.email},
        "is_member": active,
        "membership": _membership_payload(member),
        "quota": quota,
    }


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """Create a new account and return a JWT."""
    email = req.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少需要 8 位")

    session = SessionLocal()
    try:
        if session.query(User).filter_by(email=email).first():
            raise HTTPException(status_code=409, detail="该邮箱已注册，请直接登录")

        user = User(email=email, password_hash=security.hash_password(req.password))
        session.add(user)
        session.commit()
        session.refresh(user)

        token = security.create_access_token(user.id, email)
        return {"token": token, "user": {"id": user.id, "email": email}}
    finally:
        session.close()


@router.post("/auth/login")
def login(req: LoginRequest):
    """Verify credentials and return a JWT."""
    email = req.email.strip().lower()
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        # Same message for unknown email vs wrong password (avoid account probing).
        if not user or not security.verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        token = security.create_access_token(user.id, user.email)
        return {"token": token, "user": {"id": user.id, "email": user.email}}
    finally:
        session.close()


@router.get("/auth/me")
def me(request: Request):
    """Return the current user, membership and quota (Bearer required)."""
    user = _auth_user(security.parse_bearer(request.headers.get("authorization")) or "")
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return _me_payload(user)


@router.get("/auth/device")
def device():
    """Issue a fresh anonymous device id for free-quota counting."""
    return {"device_id": uuid.uuid4().hex}


@router.get("/quota")
def quota(request: Request):
    """Public quota snapshot for the current user or anonymous device."""
    user_id = current_user_id(request)
    subject = security.resolve_subject(request, user_id)
    return gating.quota_snapshot(subject, user_id=user_id)
