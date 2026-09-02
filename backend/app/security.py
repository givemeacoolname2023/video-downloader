"""
Auth & quota helpers shared across the membership features.

- Password hashing: PBKDF2-SHA256 via stdlib ``hashlib`` (no bcrypt/passlib,
  avoids Windows build/install issues).
- JWT: PyJWT, HS256. Secret from ``.env`` ``JWT_SECRET`` (dev default only).
- Quota subject resolution: logged-in users are ``user:<id>``; anonymous
  visitors are keyed by an ``X-Device-Id`` header the frontend stores in
  localStorage. A per-IP fallback keeps curl/tests deterministic when no
  device id is present.
- Membership check: a user is a member when they have a membership record in
  an active state with a future ``current_period_end``.

Python 3.9 compatible.
"""
import os
import re
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# --- JWT ---
JWT_SECRET = os.getenv("JWT_SECRET", "yupi_test")  # dev-only default; change in prod
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))  # logged-in session length

# --- Free quota ---
FREE_DAILY_DOWNLOADS = int(os.getenv("FREE_DAILY_DOWNLOADS", "3"))
FREE_DAILY_AI = int(os.getenv("FREE_DAILY_AI", "3"))
# Quota day boundary; falls back to server-local date if tzdata is unavailable.
QUOTA_TZ = os.getenv("QUOTA_TZ", "Asia/Shanghai")

# --- Membership plan names ---
PLAN_MONTHLY = "monthly"
PLAN_YEARLY = "yearly"

# --- Password hashing ---
_PBKDF2_ITERATIONS = 210_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a self-contained ``pbkdf2_sha256$iter$salt_hex$hash_hex`` string."""
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verify of *password* against a stored hash string."""
    try:
        _alg, iters, salt_hex, hash_hex = stored.split("$")
        if _alg != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


# --- JWT ---
def create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Return the payload dict, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def parse_bearer(authorization: Optional[str]) -> Optional[str]:
    """Extract the token from an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def user_id_from_token(token: Optional[str]) -> Optional[int]:
    """Return the user id for a validated JWT, or None."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        return int(payload["sub"])
    except (ValueError, TypeError):
        return None


# --- Membership ---
def _mget(m, key, default=None):
    """Read ``key`` from a dict (``.get``) or an ORM object (attribute)."""
    return m.get(key, default) if isinstance(m, dict) else getattr(m, key, default)


def membership_active(membership) -> bool:
    """True when a membership record grants access right now.

    Accepts either a plain dict (built by the API) or a ``Membership`` ORM
    object (passed by ``gating``). Both shapes are read generically.
    """
    if not membership:
        return False
    if _mget(membership, "status") != "active":
        return False
    end = _mget(membership, "current_period_end")
    if end:
        if isinstance(end, datetime):
            end = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end
        if datetime.now(timezone.utc) > end:
            return False
    return True


# --- Quota subject ---
_DEVICE_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def get_client_ip(request) -> str:
    return (request.headers.get("x-forwarded-for") or request.client.host or "") # type: ignore


def resolve_subject(request, user_id: Optional[int] = None) -> str:
    """Return the quota key for this request: ``user:<id>`` or ``device:<id>``."""
    if user_id:
        return f"user:{user_id}"
    device = request.headers.get("x-device-id", "")
    if device and _DEVICE_RE.match(device):
        return f"device:{device}"
    ip = get_client_ip(request)
    return f"device:ip:{ip or 'unknown'}"


def is_anonymous(user_id: Optional[int]) -> bool:
    return user_id is None
