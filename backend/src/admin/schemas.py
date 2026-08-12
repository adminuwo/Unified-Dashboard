from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict  # type: ignore
from typing import Optional, List, Dict, Any


class AdminLoginRequest(BaseModel):
    username: str = Field(..., description="Master Admin username/email")
    password: str = Field(..., description="Master Admin password")


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_username: str


class PlatformStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    total_applications: int
    active_applications: int
    total_revenue: float
    currency: str = "INR"
    active_subscriptions: int
    total_logs: int


class AdminUserListItem(BaseModel):
    id: str
    email: str
    name: str
    is_verified: bool
    is_active: bool
    subscriptions_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentListItem(BaseModel):
    id: str
    user_id: str
    user_email: Optional[str]
    product_id: str
    plan_id: str
    amount: float
    currency: str
    status: str
    provider: str
    provider_payment_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionListItem(BaseModel):
    id: str
    user_id: str
    user_email: Optional[str]
    product_id: str
    plan_id: str
    status: str
    provider: str
    provider_subscription_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminLogListItem(BaseModel):
    id: str
    application_id: str
    application_name: Optional[str]
    user_id: Optional[str]
    level: str
    event: str
    message: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
