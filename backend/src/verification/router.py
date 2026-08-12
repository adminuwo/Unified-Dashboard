from fastapi import APIRouter, Depends, status  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import ApplicationKey
from src.middleware.authentication import get_current_application
from src.verification.schemas import SendVerificationRequest, VerifyTokenRequest, VerificationResponse
from src.verification import service

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/send")
def send_verification(
    req: SendVerificationRequest,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Generate and dispatch verification token for user account."""
    user, token_str = service.send_verification_token(db, req)
    return {
        "message": "Verification token generated successfully.",
        "user_id": user.id,
        "token": token_str
    }


@router.post("/verify", response_model=VerificationResponse)
def verify_account(
    req: VerifyTokenRequest,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Verify user account with verification token."""
    user = service.verify_user_token(db, req)
    return VerificationResponse(
        message="Account verified successfully.",
        is_verified=user.is_verified,
        user_id=user.id
    )
