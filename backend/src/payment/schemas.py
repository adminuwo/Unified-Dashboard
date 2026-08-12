from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict


class PaymentCreateRequest(BaseModel):
    user_id: str = Field(..., description="Unified user ID")
    product_id: str = Field(..., description="Generic product ID")
    plan_id: str = Field(..., description="Generic plan ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field("INR", max_length=10)
    provider: str = Field("razorpay", max_length=50)


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    plan_id: str
    amount: float
    currency: str
    status: str
    provider: str
    provider_payment_id: Optional[str]
    checkout_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class PaymentStatusResponse(BaseModel):
    payment_id: str
    user_id: str
    status: str
    amount: float
    currency: str
    updated_at: datetime


class WebhookPayload(BaseModel):
    event: str  # e.g., payment.succeeded, payment.failed
    provider_payment_id: str
    payment_id: Optional[str] = None
    status: str  # succeeded, failed, refunded
    metadata: Optional[Dict[str, Any]] = None
