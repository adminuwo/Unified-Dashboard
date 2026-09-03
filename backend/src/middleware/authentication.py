import hashlib
from typing import Optional
from fastapi import Header, HTTPException, status, Depends  # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # type: ignore
from pymongo.database import Database  # type: ignore
from jose import JWTError, jwt  # type: ignore

from src.config.settings import settings
from src.database.connection import get_db
from src.database.models import ApplicationKey, User


def hash_api_key(key: str) -> str:
    """Compute SHA-256 hash of plaintext API key."""
    return hashlib.sha256(key.strip().encode('utf-8')).hexdigest()


def get_current_application(
    x_application_key: Optional[str] = Header(None, alias="X-Application-Key"),
    db: Database = Depends(get_db)
) -> ApplicationKey:
    """Validate Application API Key from X-Application-Key header."""
    if not x_application_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing application API key header 'X-Application-Key'."
        )

    key_hash = hash_api_key(x_application_key)
    app_doc = db["application_keys"].find_one({
        "api_key_hash": key_hash,
        "status": "active"
    })

    if not app_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked application API key."
        )

    return ApplicationKey(app_doc)


def validate_optional_app_key(
    x_application_key: Optional[str] = Header(None, alias="X-Application-Key"),
    db: Database = Depends(get_db)
) -> Optional[ApplicationKey]:
    """Validate X-Application-Key if header is present in request."""
    if x_application_key:
        key_hash = hash_api_key(x_application_key)
        app_doc = db["application_keys"].find_one({
            "api_key_hash": key_hash,
            "status": "active"
        })
        if not app_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked application API key."
            )
        return ApplicationKey(app_doc)
    return None


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db)
) -> User:
    """Validate User JWT from Authorization Bearer header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer authorization header."
        )

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type", "access")

        if not user_id or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload or token type."
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials / invalid JWT token."
        )

    user_doc = db["users"].find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    user = User(user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    return user


class AppAndUserAuth:
    def __init__(self, application: ApplicationKey, user: User):
        self.application = application
        self.user = user


def get_current_user_and_application(
    app: ApplicationKey = Depends(get_current_application),
    user: User = Depends(get_current_user)
) -> AppAndUserAuth:
    """Validate both Application API Key and User JWT."""
    return AppAndUserAuth(application=app, user=user)


admin_bearer_security = HTTPBearer(auto_error=False)


def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(admin_bearer_security)) -> str:
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
