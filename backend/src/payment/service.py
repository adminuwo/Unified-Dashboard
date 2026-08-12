import hmac
import hashlib
import secrets
from typing import Optional
from pymongo.database import Database  # type: ignore
from fastapi import HTTPException, status  # type: ignore

from src.config.settings import settings
from src.database.models import User, Payment, Subscription, utc_now
from src.payment.schemas import PaymentCreateRequest, WebhookPayload


def create_payment(db: Database, req: PaymentCreateRequest) -> tuple[Payment, str]:
    """Create a new payment intent and record in the Unified Backend."""
    user_doc = db["users"].find_one({"_id": req.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{req.user_id}' not found."
        )

    provider_payment_id = f"pay_{secrets.token_hex(16)}"
    checkout_url = f"https://checkout.provider.mock/pay/{provider_payment_id}"

    pay_dict = Payment.create_dict(
        user_id=req.user_id,
        product_id=req.product_id,
        plan_id=req.plan_id,
        amount=req.amount,
        currency=req.currency,
        status="pending",
        provider=req.provider,
        provider_payment_id=provider_payment_id
    )
    db["payments"].insert_one(pay_dict)

    # Upsert subscription in pending state
    sub_doc = db["subscriptions"].find_one({
        "user_id": req.user_id,
        "product_id": req.product_id
    })

    if not sub_doc:
        sub_dict = Subscription.create_dict(
            user_id=req.user_id,
            product_id=req.product_id,
            plan_id=req.plan_id,
            status="pending",
            provider=req.provider,
            provider_subscription_id=f"sub_{secrets.token_hex(16)}"
        )
        db["subscriptions"].insert_one(sub_dict)
    else:
        db["subscriptions"].update_one(
            {"_id": sub_doc["_id"]},
            {"$set": {
                "plan_id": req.plan_id,
                "status": "pending",
                "updated_at": utc_now()
            }}
        )

    return Payment(pay_dict), checkout_url


def get_payment_by_id(db: Database, payment_id: str) -> Payment:
    """Retrieve payment status by internal payment_id or provider_payment_id."""
    pay_doc = db["payments"].find_one({
        "$or": [
            {"_id": payment_id},
            {"provider_payment_id": payment_id}
        ]
    })

    if not pay_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID '{payment_id}' not found."
        )

    return Payment(pay_doc)


def verify_webhook_signature(payload_bytes: bytes, signature: Optional[str]) -> bool:
    """Verify HMAC-SHA256 signature of incoming payment webhook."""
    if not signature:
        return False

    secret = settings.PAYMENT_WEBHOOK_SECRET.encode('utf-8')
    computed_signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed_signature, signature)


def process_webhook_event(db: Database, payload: WebhookPayload) -> Payment:
    """Update payment and associated subscription status based on provider webhook payload."""
    pay_doc = db["payments"].find_one({"provider_payment_id": payload.provider_payment_id})

    if not pay_doc and payload.payment_id:
        pay_doc = db["payments"].find_one({"_id": payload.payment_id})

    if not pay_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment record for provider_payment_id '{payload.provider_payment_id}' not found."
        )

    new_status = payload.status.lower()
    now = utc_now()

    db["payments"].update_one(
        {"_id": pay_doc["_id"]},
        {"$set": {"status": new_status, "updated_at": now}}
    )
    pay_doc["status"] = new_status
    pay_doc["updated_at"] = now

    sub_doc = db["subscriptions"].find_one({
        "user_id": pay_doc["user_id"],
        "product_id": pay_doc["product_id"]
    })

    if sub_doc:
        if new_status == "succeeded":
            new_sub_status = "active"
        elif new_status in ["failed", "canceled", "refunded"]:
            new_sub_status = "inactive"
        else:
            new_sub_status = sub_doc.get("status", "pending")

        db["subscriptions"].update_one(
            {"_id": sub_doc["_id"]},
            {"$set": {"status": new_sub_status, "updated_at": now}}
        )

    return Payment(pay_doc)
