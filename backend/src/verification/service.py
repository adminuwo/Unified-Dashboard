import secrets
from datetime import datetime, timedelta, timezone
from pymongo.database import Database  # type: ignore
from fastapi import HTTPException, status  # type: ignore

from src.database.models import User, VerificationToken, utc_now
from src.verification.schemas import SendVerificationRequest, VerifyTokenRequest


def send_verification_token(db: Database, req: SendVerificationRequest) -> tuple[User, str]:
    """Generate and record a new verification token for a user."""
    user_doc = None
    if req.user_id:
        user_doc = db["users"].find_one({"_id": req.user_id})
    elif req.email:
        user_doc = db["users"].find_one({"email": req.email.lower()})

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for verification token generation."
        )

    user = User(user_doc)
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is already verified."
        )

    # Invalidate any prior unused tokens for this user
    db["verification_tokens"].update_many(
        {"user_id": user.id, "is_used": False},
        {"$set": {"is_used": True}}
    )

    # Generate new token
    token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    vt_dict = VerificationToken.create_dict(
        user_id=user.id,
        token=token_str,
        expires_at=expires_at,
        is_used=False
    )
    db["verification_tokens"].insert_one(vt_dict)

    return user, token_str


def verify_user_token(db: Database, req: VerifyTokenRequest) -> User:
    """Verify user account using provided verification token."""
    vt_doc = db["verification_tokens"].find_one({"token": req.token})
    if not vt_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or unrecognized verification token."
        )

    vt = VerificationToken(vt_doc)
    if vt.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has already been used."
        )

    now = datetime.now(timezone.utc)
    expires_at = vt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired."
        )

    user_doc = db["users"].find_one({"_id": vt.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user not found."
        )

    now_time = utc_now()
    db["users"].update_one(
        {"_id": vt.user_id},
        {"$set": {"is_verified": True, "updated_at": now_time}}
    )
    db["verification_tokens"].update_one(
        {"_id": vt.id},
        {"$set": {"is_used": True}}
    )

    user_doc["is_verified"] = True
    user_doc["updated_at"] = now_time
    return User(user_doc)
