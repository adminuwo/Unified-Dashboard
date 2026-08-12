from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SendVerificationRequest(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None


class VerifyTokenRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Verification token")


class VerificationResponse(BaseModel):
    message: str
    is_verified: bool
    user_id: str
