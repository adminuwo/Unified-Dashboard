from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    name: Optional[str] = Field("User", description="Display name")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class ValidateRequest(BaseModel):
    token: str


class ValidateResponseUser(BaseModel):
    id: str
    email: str


class ValidateResponse(BaseModel):
    valid: bool
    user: Optional[ValidateResponseUser] = None
    message: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    otp_preview: Optional[str] = None


class VerifyResetOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class VerifyResetOtpResponse(BaseModel):
    valid: bool
    message: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)
    new_password: str = Field(..., min_length=6, description="New password (min 6 characters)")


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str

