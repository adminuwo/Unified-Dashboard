from typing import List, Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status, Header  # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # type: ignore
from jose import jwt, JWTError  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.database.connection import get_db
from src.auth.service import create_jwt_token
from src.admin.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    PlatformStatsResponse,
    AdminUserListItem,
    AdminPaymentListItem,
    AdminSubscriptionListItem,
    AdminLogListItem
)
from src.admin import service, analytics

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
security = HTTPBearer(auto_error=False)


def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Validate Admin Bearer JWT Token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        is_admin_role = role and ("admin" in role.lower())
        if not username or not is_admin_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token credentials."
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired or invalid admin token."
        )


verify_admin_token = get_current_admin


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    req: AdminLoginRequest,
    db: Database = Depends(get_db)
):
    """Authenticate master admin account credentials against MongoDB database."""
    admin_user = service.authenticate_admin(db, req.username, req.password)

    access_token = create_jwt_token(
        data={"sub": admin_user["username"], "role": admin_user.get("role", "admin")},
        expires_delta=timedelta(hours=24),
        token_type="admin"
    )

    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        admin_username=admin_user["username"]
    )


@router.get("/stats", response_model=PlatformStatsResponse)
def get_stats(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch overview metrics for the admin dashboard."""
    return service.get_platform_stats(db)


@router.get("/users", response_model=List[AdminUserListItem])
def get_users(
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """List central users."""
    return service.list_users(db, limit=limit)


@router.get("/payments", response_model=List[AdminPaymentListItem])
def get_payments(
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """List payment transactions."""
    return service.list_payments(db, limit=limit)


@router.get("/subscriptions", response_model=List[AdminSubscriptionListItem])
def get_subscriptions(
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """List product subscriptions."""
    return service.list_subscriptions(db, limit=limit)


@router.get("/logs", response_model=List[AdminLogListItem])
def get_logs(
    level: Optional[str] = Query(None, description="Filter by level: INFO, WARNING, ERROR"),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """List centralized logs."""
    return service.list_logs(db, level=level, app_id=application_id, limit=limit)


@router.get("/analytics/overlap")
def get_analytics_overlap(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Retrieve crossover engagement and overlap stats for connected standalone apps."""
    return analytics.get_app_overlap_stats(db)
