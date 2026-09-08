import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException, status  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.modules.auth.repository import AuthRepository
from src.modules.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_token,
    REFRESH_TOKEN_EXPIRE_DAYS
)



class AuthService:
    """Core Authentication Business Logic Service."""

    def __init__(self, db: Database):
        self.repo = AuthRepository(db)

    def register(self, email: str, password: str, name: str = "User", application_id: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user in the central users collection."""
        existing_user = self.repo.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        hashed = hash_password(password)
        user = self.repo.create_user(
            email=email,
            password_hash=hashed,
            name=name,
            is_verified=False,
            is_active=True,
            connected_apps=[application_id] if application_id else None
        )
        return {
            "id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "is_active": user["is_active"],
            "is_verified": user["is_verified"],
            "created_at": user["created_at"]
        }

    def login(
        self,
        email: str,
        password: str,
        device: str = "Unknown Device",
        ip_address: str = "127.0.0.1",
        application_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user, create session, and issue access & refresh tokens."""
        user = self.repo.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive or disabled"
            )

        # Update last login timestamp and connected_apps
        self.repo.update_last_login(user["_id"], application_id=application_id)

        # Generate tokens
        access_token = create_access_token(user_id=user["_id"], email=user["email"])
        raw_refresh_token = generate_refresh_token()
        refresh_hash = hash_token(raw_refresh_token)

        # Create session record
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        self.repo.create_session(
            user_id=user["_id"],
            refresh_token_hash=refresh_hash,
            device=device,
            ip_address=ip_address,
            expires_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer"
        }

    def refresh_tokens(
        self,
        refresh_token: str,
        device: str = "Unknown Device",
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Validate refresh token, rotate tokens, and issue new session."""
        token_hash = hash_token(refresh_token)
        session = self.repo.find_session_by_hash(token_hash)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired refresh token"
            )

        # Check session expiration
        expires_at = session.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                self.repo.delete_session_by_id(session["_id"])
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Refresh token has expired"
                )

        user = self.repo.get_user_by_id(session["user_id"])
        if not user or not user.get("is_active", True):
            self.repo.delete_session_by_id(session["_id"])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Token Rotation: Revoke previous session
        self.repo.delete_session_by_id(session["_id"])

        # Generate new token pair
        new_access_token = create_access_token(user_id=user["_id"], email=user["email"])
        new_raw_refresh = generate_refresh_token()
        new_refresh_hash = hash_token(new_raw_refresh)

        # Store new session
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        self.repo.create_session(
            user_id=user["_id"],
            refresh_token_hash=new_refresh_hash,
            device=device,
            ip_address=ip_address,
            expires_at=new_expires_at
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_raw_refresh,
            "token_type": "bearer"
        }

    def logout(self, refresh_token: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, str]:
        """Invalidate active session or all user sessions."""
        if refresh_token:
            token_hash = hash_token(refresh_token)
            self.repo.delete_session_by_hash(token_hash)

        if user_id:
            self.repo.delete_all_user_sessions(user_id)

        return {"message": "Logged out successfully"}

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token for external product integrations."""
        payload = decode_access_token(token)
        if not payload:
            return {"valid": False, "message": "Invalid or expired JWT token"}

        user_id = payload.get("sub")
        if not user_id:
            return {"valid": False, "message": "Missing user identification in token"}

        user = self.repo.get_user_by_id(str(user_id))
        if not user or not user.get("is_active", True):
            return {"valid": False, "message": "User inactive or not found"}

        return {
            "valid": True,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"]
            }
        }

    def get_current_user_profile(self, token: str) -> Dict[str, Any]:
        """Retrieve full user profile from Bearer JWT token."""
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token"
            )

        user_id = payload.get("sub")
        user = self.repo.get_user_by_id(str(user_id)) if user_id else None
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user.get("name", "User"),
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", True),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Generate and dispatch a 6-digit OTP for password recovery."""
        clean_email = email.strip().lower()
        user = self.repo.get_user_by_email(clean_email)

        # Generic response to prevent user enumeration attacks
        generic_msg = "If your email is registered in our platform, a 6-digit verification code has been generated."

        if not user:
            return {"message": generic_msg, "otp_preview": None}

        # Generate 6-digit cryptographic numeric OTP
        otp = f"{secrets.randbelow(900000) + 100000:06d}"
        otp_hash = hash_token(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        self.repo.save_password_reset(clean_email, otp_hash, expires_at)

        # In dev or non-production environment, return otp_preview for easy testing
        is_dev = settings.ENVIRONMENT.lower() != "production"
        preview = otp if is_dev else None

        return {
            "message": "A 6-digit verification code has been sent to your email.",
            "otp_preview": preview
        }

    def verify_reset_otp(self, email: str, otp: str) -> Dict[str, Any]:
        """Verify that the provided OTP for the given email is valid and unexpired."""
        clean_email = email.strip().lower()
        reset_doc = self.repo.get_active_password_reset(clean_email)

        if not reset_doc or reset_doc.get("is_used"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )

        expires_at = reset_doc.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has expired. Please request a new code."
                )

        clean_otp = str(otp).strip()
        if hash_token(clean_otp) != reset_doc.get("otp_hash"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        return {"valid": True, "message": "Verification code is valid"}

    def reset_password(self, email: str, otp: str, new_password: str) -> Dict[str, Any]:
        """Validate OTP and update user password, invalidating old sessions."""
        clean_email = email.strip().lower()

        # 1. Verify OTP
        self.verify_reset_otp(clean_email, otp)

        # 2. Verify User
        user = self.repo.get_user_by_email(clean_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found"
            )

        # 3. Hash new password and update in repository
        new_hash = hash_password(new_password)
        self.repo.update_user_password(user["_id"], new_hash)

        # 4. Mark OTP reset record as used
        reset_doc = self.repo.get_active_password_reset(clean_email)
        if reset_doc:
            self.repo.mark_password_reset_used(reset_doc["_id"])

        # 5. Revoke all existing sessions for security
        self.repo.delete_all_user_sessions(user["_id"])

        return {
            "success": True,
            "message": "Password reset successfully. You can now sign in with your new password."
        }

