from typing import Optional, Any
from fastapi import APIRouter, Depends, Request, Header, status, HTTPException  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.middleware.authentication import validate_optional_app_key
from src.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    UserResponse,
    ValidateRequest,
    ValidateResponse
)
from src.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Unified Auth Service"])


def get_auth_service(db: Database = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    _app: Optional[Any] = Depends(validate_optional_app_key),
    service: AuthService = Depends(get_auth_service)
):
    """Register a new central user identity."""
    app_id = getattr(_app, "id", None) if _app else None
    return service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name or "User",
        application_id=app_id
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: LoginRequest,
    request: Request,
    _app: Optional[Any] = Depends(validate_optional_app_key),
    service: AuthService = Depends(get_auth_service)
):
    """Authenticate credentials, create session, and issue access & refresh tokens."""
    device_info = request.headers.get("User-Agent", "Unknown Device")
    client_ip = request.client.host if request.client else "127.0.0.1"

    app_id = getattr(_app, "id", None) if _app else None
    return service.login(
        email=payload.email,
        password=payload.password,
        device=device_info,
        ip_address=client_ip,
        application_id=app_id
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    request: Request,
    _app: Optional[Any] = Depends(validate_optional_app_key),
    service: AuthService = Depends(get_auth_service)
):
    """Rotate refresh token and issue a new JWT access & refresh token pair."""
    device_info = request.headers.get("User-Agent", "Unknown Device")
    client_ip = request.client.host if request.client else "127.0.0.1"

    return service.refresh_tokens(
        refresh_token=payload.refresh_token,
        device=device_info,
        ip_address=client_ip
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    authorization: Optional[str] = Header(None),
    service: AuthService = Depends(get_auth_service)
):
    """Fetch profile of currently authenticated user using Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer Authorization header"
        )
    token = authorization.split(" ")[1]
    return service.get_current_user_profile(token)


@router.post("/logout")
def logout_user(
    payload: Optional[LogoutRequest] = None,
    authorization: Optional[str] = Header(None),
    service: AuthService = Depends(get_auth_service)
):
    """Revoke user session and log out."""
    refresh_token_str = payload.refresh_token if payload else None
    user_id_str = None

    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            user = service.get_current_user_profile(token)
            user_id_str = user.get("id")
        except Exception:
            pass

    return service.logout(refresh_token=refresh_token_str, user_id=user_id_str)


@router.post("/validate", response_model=ValidateResponse)
def validate_token(
    payload: ValidateRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Validate a JWT token for external product integrations (SSO Integration Bridge)."""
    return service.validate_token(payload.token)
