from fastapi import APIRouter, Depends, status  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import User, ApplicationKey
from src.middleware.authentication import get_current_application, get_current_user
from src.auth.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest
from src.auth import service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Register a new user under central identity via standalone application."""
    user, _ = service.register_user(db, user_in)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    login_in: UserLogin,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Authenticate user credentials and issue JWT tokens for standalone application."""
    user = service.authenticate_user(db, login_in)
    tokens = service.generate_auth_tokens(user)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Obtain new access token using a valid refresh token."""
    tokens = service.refresh_access_token(db, refresh_in.refresh_token)
    payload = service.jwt.decode(tokens["access_token"], service.settings.JWT_SECRET, algorithms=[service.settings.JWT_ALGORITHM])
    user_doc = db["users"].find_one({"_id": payload["sub"]})
    user = User(user_doc) if user_doc else None
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=user
    )


@router.post("/logout")
def logout():
    """Logout current user session."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of currently authenticated user."""
    return current_user
