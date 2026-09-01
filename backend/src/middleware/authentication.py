import hashlib
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends  # type: ignore
from pymongo.database import Database  # type: ignore
from jose import JWTError, jwt  # type: ignore

from src.config.settings import settings
from src.database.connection import get_db
from src.database.models import ApplicationKey, User, utc_now


# ─── Built-in Platform Master Application Keys ─────────────────────────────────
MASTER_APPLICATION_KEYS: Dict[str, Dict[str, Any]] = {
    "key_aimall_live_master_2026": {
        "id": "app_aimall_master",
        "application_name": "AI Mall (aimall24.com)",
        "app_code": "aimall",
        "allowed_domains": ["aimall24.com", "www.aimall24.com", "localhost"]
    },
    "key_aisa_live_master_2026": {
        "id": "app_aisa_master",
        "application_name": "AISA (aisa24.com)",
        "app_code": "aisa",
        "allowed_domains": ["aisa24.com", "beta.aisa24.com", "www.aisa24.com", "localhost"]
    },
    "key_ailegal_live_master_2026": {
        "id": "app_ailegal_master",
        "application_name": "AI Legal",
        "app_code": "ailegal",
        "allowed_domains": ["localhost"]
    },
    "key_uwoconnect_live_master_2026": {
        "id": "app_uwoconnect_master",
        "application_name": "UWO Connect",
        "app_code": "uwoconnect",
        "allowed_domains": ["uwo24.com", "admin.uwo24.com", "localhost"]
    },
    "key_efv_live_master_2026": {
        "id": "app_efv_master",
        "application_name": "EFV Framework",
        "app_code": "efvframework",
        "allowed_domains": ["localhost"]
    },
    "key_yugamc_live_master_2026": {
        "id": "app_yugamc_master",
        "application_name": "Yuga MC",
        "app_code": "yugamc",
        "allowed_domains": ["yugamc.com", "localhost"]
    },
    "key_uwo_live_master_2026": {
        "id": "app_uwo_master",
        "application_name": "UWO Central",
        "app_code": "uwo",
        "allowed_domains": ["uwo24.com", "admin.uwo24.com", "localhost"]
    },
}


def hash_api_key(key: str) -> str:
    """Compute SHA-256 hash of plaintext API key."""
    return hashlib.sha256(key.strip().encode('utf-8')).hexdigest()


def resolve_application_key(key_str: str, db: Database) -> Optional[ApplicationKey]:
    """Resolve an API key from built-in master keys or the database."""
    cleaned_key = key_str.strip()
    
    # 1. Check built-in master keys
    if cleaned_key in MASTER_APPLICATION_KEYS:
        info = MASTER_APPLICATION_KEYS[cleaned_key]
        key_hash = hash_api_key(cleaned_key)
        now = utc_now()
        doc = {
            "_id": info["id"],
            "application_name": info["application_name"],
            "app_code": info["app_code"],
            "api_key_hash": key_hash,
            "status": "active",
            "allowed_domains": info.get("allowed_domains", []),
            "created_at": now,
            "updated_at": now
        }
        # Upsert in DB in background for analytics/consistency
        try:
            db["application_keys"].update_one(
                {"_id": info["id"]},
                {"$setOnInsert": doc, "$set": {"status": "active", "updated_at": now}},
                upsert=True
            )
        except Exception:
            pass
        return ApplicationKey(doc)

    # 2. Check Database by SHA-256 hash
    key_hash = hash_api_key(cleaned_key)
    app_doc = db["application_keys"].find_one({
        "api_key_hash": key_hash,
        "status": "active"
    })
    if app_doc:
        return ApplicationKey(app_doc)

    # 3. Check if key is an app_code alias (e.g. 'aimall', 'aisa')
    lower_code = cleaned_key.lower()
    app_doc = db["application_keys"].find_one({
        "app_code": lower_code,
        "status": "active"
    })
    if app_doc:
        return ApplicationKey(app_doc)

    return None


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

    app_key = resolve_application_key(x_application_key, db)
    if not app_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked application API key."
        )

    return app_key


def validate_optional_app_key(
    x_application_key: Optional[str] = Header(None, alias="X-Application-Key"),
    db: Database = Depends(get_db)
) -> Optional[ApplicationKey]:
    """Validate X-Application-Key if header is present in request."""
    if x_application_key:
        app_key = resolve_application_key(x_application_key, db)
        if not app_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked application API key."
            )
        return app_key
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
