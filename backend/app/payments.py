"""
Stripe subscription payments + local "mock" mode.

Two code paths behind one API surface:

- Real mode (``PAYMENT_MOCK=0``, the default for production): talks to Stripe
  via the official SDK. Checkout creates a Subscription-mode Checkout Session;
  the webhook verifies the signature with ``stripe.Webhook.construct_event``
  and mirrors Stripe subscription state into our ``memberships`` table.
- Mock mode (``PAYMENT_MOCK=1``): never touches the network. The checkout
  endpoint returns our own redirect URL; a dev endpoint fabricates Stripe-like
  objects, signs a payload with the same webhook secret, and drives the *real*
  webhook pipeline offline. This lets the whole flow (subscribe -> paid ->
  entitlement -> quota refresh) be tested with no internet, and exercises the
  signature + idempotency logic honestly.

Security / money-safety notes:
- The webhook is the only trusted grant source; it always verifies the Stripe
  signature when not in mock mode.
- Idempotency: Stripe delivers events at least once. We store handled
  ``event.id`` in ``processed_events`` (unique PK). Already-seen events return
  immediately with ``duplicate: true`` and are NOT re-applied.
- Membership is upserted by ``user_id`` (one row per user), so a duplicate
  event cannot double-grant or create duplicate rows.
- Checkout session creation passes an idempotency key to avoid duplicate
  sessions on retry.

Python 3.9 compatible.
"""
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import security
from .auth import _me_payload, current_user_id
from .db import SessionLocal
from .models import Membership, ProcessedEvent, User

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# --- Stripe config ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID_MONTHLY = os.getenv("STRIPE_PRICE_ID_MONTHLY", "")
STRIPE_PRICE_ID_YEARLY = os.getenv("STRIPE_PRICE_ID_YEARLY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
PAYMENT_MOCK = os.getenv("PAYMENT_MOCK", "0") == "1"

PRICE_IDS = {
    security.PLAN_MONTHLY: STRIPE_PRICE_ID_MONTHLY,
    security.PLAN_YEARLY: STRIPE_PRICE_ID_YEARLY,
}

# Optional override to point the SDK at a local stripe-mock server (offline).
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
if os.getenv("STRIPE_API_BASE"):
    stripe.api_base = os.getenv("STRIPE_API_BASE")

# Events we subscribe to. ``invoice.paid`` is handled as a no-op "renewed"
# confirmation; activation/renewal state comes from the subscription events.
HANDLED_EVENT_TYPES = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
}


class CheckoutRequest(BaseModel):
    plan: str = "monthly"


# --------------------------------------------------------------------------- #
# Membership upsert helpers (shared by real & mock paths)
# --------------------------------------------------------------------------- #
def _upsert_membership(
    user_id: int,
    sub_id: Optional[str],
    plan: str,
    status: str,
    period_end: Optional[datetime],
    period_start: Optional[datetime],
    customer_id: Optional[str],
    cancel_at_period_end: bool,
) -> None:
    """Create or update the single membership row for *user_id*."""
    session = SessionLocal()
    try:
        membership = (
            session.query(Membership).filter_by(user_id=user_id).order_by(Membership.id.desc()).first()
        )
        if not membership:
            membership = Membership(user_id=user_id)
            session.add(membership)

        membership.stripe_subscription_id = sub_id
        membership.plan = plan
        membership.status = status
        membership.current_period_end = period_end
        membership.current_period_start = period_start
        membership.cancel_at_period_end = cancel_at_period_end

        user = session.get(User, user_id)
        if user and customer_id:
            user.stripe_customer_id = customer_id
        session.commit()
    finally:
        session.close()


def _apply_subscription(sub: dict) -> None:
    """Apply a ``customer.subscription.*`` object to the membership table."""
    metadata = sub.get("metadata") or {}
    user_id_raw = str(metadata.get("user_id") or "")
    # Fall back to the subscription's `client_reference_id` if metadata is missing.
    if not user_id_raw and sub.get("client_reference_id"):
        user_id_raw = str(sub["client_reference_id"])
    if not user_id_raw.isdigit():
        logger.warning("subscription %s has no usable user_id metadata", sub.get("id"))
        return

    user_id = int(user_id_raw)
    price_id = ""
    items = sub.get("items") or {}
    data = items.get("data") or []
    if data:
        price_id = (data[0].get("price") or {}).get("id") or ""
    plan = metadata.get("plan") or (_plan_from_price(price_id) or security.PLAN_MONTHLY)

    def _ts(value) -> Optional[datetime]:
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (TypeError, ValueError):
            return None

    _upsert_membership(
        user_id,
        sub.get("id"),
        plan,
        sub.get("status", "active"),
        _ts(sub.get("current_period_end")),
        _ts(sub.get("current_period_start")),
        sub.get("customer"),
        bool(sub.get("cancel_at_period_end")),
    )


def _plan_from_price(price_id: str) -> Optional[str]:
    for plan, pid in PRICE_IDS.items():
        if pid and price_id == pid:
            return plan
    return None


def _apply_session_completed(session_obj: dict) -> None:
    """Grant membership on ``checkout.session.completed``.

    The subscription detail (period, plan) is typically filled in by the
    following ``customer.subscription.created`` / ``updated`` event; here we
    mark the intent active so access is granted immediately.
    """
    metadata = session_obj.get("metadata") or {}
    user_id_raw = str(session_obj.get("client_reference_id") or metadata.get("user_id") or "")
    if not user_id_raw.isdigit():
        logger.warning("checkout session %s has no usable user_id", session_obj.get("id"))
        return
    user_id = int(user_id_raw)
    plan = metadata.get("plan") or security.PLAN_MONTHLY
    _upsert_membership(
        user_id=user_id,
        sub_id=session_obj.get("subscription"),
        plan=plan,
        status="active",
        period_end=None,
        period_start=None,
        customer_id=session_obj.get("customer"),
        cancel_at_period_end=False,
    )


def _set_sub_status(sub_id: Optional[str], status: str) -> None:
    if not sub_id:
        return
    session = SessionLocal()
    try:
        membership = (
            session.query(Membership)
            .filter_by(stripe_subscription_id=sub_id)
            .order_by(Membership.id.desc())
            .first()
        )
        if membership:
            membership.status = status
            session.commit()
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# Webhook processing (signature verification + idempotency + dispatch)
# --------------------------------------------------------------------------- #
def _already_handled(event_id: str) -> bool:
    session = SessionLocal()
    try:
        return session.get(ProcessedEvent, event_id) is not None
    finally:
        session.close()


def _mark_handled(event_id: str) -> None:
    session = SessionLocal()
    try:
        session.add(ProcessedEvent(event_id=event_id))
        session.commit()
    except Exception:  # noqa: BLE001 — unique PK; a concurrent insert is fine
        session.rollback()
    finally:
        session.close()


def _dispatch(event: dict) -> None:
    event_type = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        _apply_session_completed(obj)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        _apply_subscription(obj)
    elif event_type == "customer.subscription.deleted":
        _set_sub_status(obj.get("id"), "canceled")
    elif event_type == "invoice.payment_failed":
        _set_sub_status(obj.get("subscription"), "past_due")
    elif event_type == "invoice.paid":
        # Renewal — keep active; period handled by subscription.updated.
        _set_sub_status(obj.get("subscription"), "active")
    else:
        logger.info("ignoring unhandled webhook event type: %s", event_type)


def _process_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify the signature, dedupe by event id, dispatch. Returns a dict."""
    if PAYMENT_MOCK:
        # Offline: accept unsigned local payloads, but still verify when a
        # signature + secret are present so the mock can exercise verification.
        if sig_header and STRIPE_WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
            except Exception:  # noqa: BLE001
                return {"received": False, "error": "invalid signature (mock)"}
        else:
            event = json.loads(payload.decode("utf-8"))
    else:
        if not STRIPE_WEBHOOK_SECRET:
            return {"received": False, "error": "webhook secret not configured"}
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except ValueError:
            return {"received": False, "error": "invalid payload"}
        except Exception:  # noqa: BLE001
            return {"received": False, "error": "invalid signature"}

    event_id = event.get("id")
    if not event_id:
        return {"received": False, "error": "missing event id"}

    if _already_handled(event_id):
        return {"received": True, "duplicate": True, "type": event.get("type")}

    # Only process if it's an event type we subscribe to.
    if event.get("type") not in HANDLED_EVENT_TYPES:
        _mark_handled(event_id)
        return {"received": True, "duplicate": False, "type": event.get("type"), "ignored": True}

    try:
        _dispatch(event)
        _mark_handled(event_id)
    except Exception:  # noqa: BLE001
        logger.exception("webhook handling failed for %s", event_id)
        raise  # let Stripe retry — do not mark handled

    return {"received": True, "duplicate": False, "type": event.get("type")}


# --------------------------------------------------------------------------- #
# Stripe helper for the real path
# --------------------------------------------------------------------------- #
def _get_or_create_customer(session, user: User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    if PAYMENT_MOCK:
        customer_id = f"cus_mock_{user.id}"
    else:
        try:
            customer_id = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.id)},
                idempotency_key=f"customer-{user.id}",
            ).id
        except stripe.error.StripeError as exc:  # pragma: no cover
            raise HTTPException(status_code=502, detail=f"Stripe 客户创建失败：{exc}")
    user.stripe_customer_id = customer_id
    session.commit()
    return customer_id


# --------------------------------------------------------------------------- #
# Mock helpers (offline)
# --------------------------------------------------------------------------- #
def _sign_payload(payload: bytes, secret: Optional[str] = None) -> str:
    """Produce a valid Stripe ``t=…,v1=…`` signature for *payload*."""
    secret = secret or STRIPE_WEBHOOK_SECRET or "whsec_mock"
    ts = int(time.time())
    signed = f"{ts}.{payload.decode('utf-8')}"
    v1 = hmac.new(secret.encode("utf-8"), signed.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"t={ts},v1={v1}"


def _drive_event(event_type: str, obj: dict) -> dict:
    """Build an event, sign it, and run the real webhook pipeline offline."""
    event = {
        "id": f"evt_mock_{uuid.uuid4().hex[:12]}",
        "object": "event",
        "type": event_type,
        "data": {"object": obj},
    }
    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
    return _process_webhook(payload, _sign_payload(payload))


def _fake_subscription(user_id: int, plan: str, customer_id: str) -> dict:
    now = int(time.time())
    period = 31536000 if plan == security.PLAN_YEARLY else 2592000
    price_id = PRICE_IDS.get(plan, f"price_mock_{plan}")
    return {
        "id": f"sub_mock_{uuid.uuid4().hex[:12]}",
        "object": "subscription",
        "customer": customer_id,
        "status": "active",
        "current_period_end": now + period,
        "current_period_start": now,
        "cancel_at_period_end": False,
        "metadata": {"user_id": str(user_id), "plan": plan},
        "items": {"data": [{"price": {"id": price_id}}]},
    }


def _mock_grant(user_id: int, plan: str) -> None:
    """Fabricate a checkout + subscription and drive both through the webhook."""
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        customer_id = user.stripe_customer_id or f"cus_mock_{user_id}"
        if user and not user.stripe_customer_id:
            user.stripe_customer_id = customer_id
            session.commit()
    finally:
        session.close()

    sub = _fake_subscription(user_id, plan, customer_id)
    checkout_session = {
        "id": f"cs_mock_{uuid.uuid4().hex[:12]}",
        "object": "checkout.session",
        "client_reference_id": str(user_id),
        "subscription": sub["id"],
        "customer": customer_id,
        "payment_status": "paid",
        "metadata": {"user_id": str(user_id), "plan": plan},
    }
    _drive_event("checkout.session.completed", checkout_session)
    _drive_event("customer.subscription.created", sub)


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
router = APIRouter(prefix="/api", tags=["payments"])


@router.post("/payments/checkout")
def create_checkout(request: Request, req: CheckoutRequest):
    """Create a subscription Checkout Session for the logged-in user."""
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录后再订阅")
    if req.plan not in PRICE_IDS:
        raise HTTPException(status_code=400, detail="未知的会员方案")

    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="账号不存在")
        customer_id = _get_or_create_customer(session, user)
    finally:
        session.close()

    if PAYMENT_MOCK:
        session_id = f"cs_mock_{uuid.uuid4().hex[:12]}"
        url = f"{FRONTEND_URL}/mock-checkout?session_id={session_id}&plan={req.plan}"
        return {"url": url, "session_id": session_id, "mock": True}

    price_id = PRICE_IDS.get(req.plan)
    if not price_id:
        raise HTTPException(status_code=500, detail="未配置 Stripe 价格 ID")
    try:
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            client_reference_id=str(user_id),
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{FRONTEND_URL}/membership?success=1&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/membership?canceled=1",
            subscription_data={"metadata": {"user_id": str(user_id), "plan": req.plan}},
            metadata={"user_id": str(user_id), "plan": req.plan},
            allow_promotion_codes=True,
            # Stable per-user+plan window so a retry doesn't create a 2nd session.
            idempotency_key=f"checkout-{user_id}-{req.plan}-{int(time.time() // 60 * 60)}",
        )
    except stripe.error.StripeError as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Stripe 下单失败：{exc}")

    return {"url": checkout_session.url, "session_id": checkout_session.id, "mock": False}


@router.post("/payments/webhook")
async def payments_webhook(request: Request):
    """Receive and process Stripe webhooks (signature-verified, idempotent)."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    result = _process_webhook(payload, sig)
    if not result.get("received"):
        return JSONResponse(status_code=400, content=result)
    return result


@router.post("/dev/mock-activate")
def mock_activate(request: Request, req: CheckoutRequest):
    """Mock-only: simulate a successful subscription payment for the user."""
    if not PAYMENT_MOCK:
        raise HTTPException(status_code=404, detail="仅在 PAYMENT_MOCK=1 时可用")
    user_id = current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    plan = req.plan if req.plan in PRICE_IDS else security.PLAN_MONTHLY
    _mock_grant(user_id, plan)
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        return _me_payload(user)
    finally:
        session.close()


@router.post("/dev/webhook-drive")
def dev_webhook_drive(body: dict):
    """Mock-only: fire an arbitrary signed webhook event through the pipeline."""
    if not PAYMENT_MOCK:
        raise HTTPException(status_code=404, detail="仅在 PAYMENT_MOCK=1 时可用")
    event_type = body.get("event_type", "")
    data = body.get("data") or {}
    return _drive_event(event_type, data)
