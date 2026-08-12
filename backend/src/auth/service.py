import secrets
import bcrypt  # type: ignore
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any
from pymongo.database import Database  # type: ignore
from fastapi import HTTPException, status  # type: ignore
from jose import jwt, JWTError  # type: ignore

from src.config.settings import settings
from src.database.models import User, VerificationToken, utc_now
from src.auth.schemas import UserRegister, UserLogin


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt directly."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_jwt_token(data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
    """Generate signed JWT token with expiry and type."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def register_user(db: Database, user_in: UserRegister) -> Tuple[User, str]:
    """Register a new user, returning the User object and a new verification token."""
    existing = db["users"].find_one({"email": user_in.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user_dict = User.create_dict(
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),
        name=user_in.name,
        is_verified=False,
        is_active=True
    )
    db["users"].insert_one(user_dict)
    db_user = User(user_dict)

    # Generate initial verification token
    verification_token_str = secrets.token_urlsafe(32)
    vt_dict = VerificationToken.create_dict(
        user_id=db_user.id,
        token=verification_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        is_used=False
    )
    db["verification_tokens"].insert_one(vt_dict)

    return db_user, verification_token_str


def authenticate_user(db: Database, login_in: UserLogin) -> User:
    """Authenticate user credentials."""
    user_doc = db["users"].find_one({"email": login_in.email.lower()})
    if not user_doc or not verify_password(login_in.password, user_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user = User(user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    return user


def generate_auth_tokens(user: User) -> Dict[str, str]:
    """Generate access and refresh tokens for user."""
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_create_token_helper(user.id, user.email, access_token_expires)
    refresh_token = create_jwt_token(
        data={"sub": user.id},
        expires_delta=refresh_token_expires,
        token_type="refresh"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def create_create_token_helper(user_id: str, email: str, expires_delta: timedelta) -> str:
    return create_jwt_token(
        data={"sub": user_id, "email": email},
        expires_delta=expires_delta,
        token_type="access"
    )


def refresh_access_token(db: Database, refresh_token: str) -> Dict[str, str]:
    """Verify refresh token and issue new access and refresh tokens."""
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload."
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_doc = db["users"].find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive."
        )
    user = User(user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive."
        )

    return generate_auth_tokens(user)
