from fastapi import APIRouter, Depends, Header, Request, HTTPException, status  # type: ignore
from pymongo.database import Database  # type: ignore
from typing import Optional

from src.database.connection import get_db
from src.database.models import ApplicationKey
from src.middleware.authentication import get_current_application
from src.payment.schemas import PaymentCreateRequest, PaymentResponse, PaymentStatusResponse, WebhookPayload
from src.payment import service

router = APIRouter(prefix="/payment", tags=["Payments"])


@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    req: PaymentCreateRequest,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Create a new payment request for a standalone application."""
    payment, checkout_url = service.create_payment(db, req)
    return PaymentResponse(
        id=payment.id,
        user_id=payment.user_id,
        product_id=payment.product_id,
        plan_id=payment.plan_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        provider=payment.provider,
        provider_payment_id=payment.provider_payment_id,
        checkout_url=checkout_url,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: str,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Query current status of a payment by ID or provider payment ID."""
    payment = service.get_payment_by_id(db, payment_id)
    return PaymentStatusResponse(
        payment_id=payment.id,
        user_id=payment.user_id,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        updated_at=payment.updated_at
    )


@router.post("/webhook")
async def handle_payment_webhook(
    request: Request,
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    db: Database = Depends(get_db)
):
    """Process incoming payment webhook with HMAC signature verification."""
    raw_body = await request.body()

    # Optional signature check: if X-Signature header is provided, verify it
    if x_signature is not None:
        if not service.verify_webhook_signature(raw_body, x_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook HMAC signature."
            )

    payment = service.process_webhook_event(db, payload)
    return {
        "status": "success",
        "payment_id": payment.id,
        "payment_status": payment.status
    }
