import secrets
import pymongo  # type: ignore
from typing import List, Tuple
from pymongo.database import Database  # type: ignore
from fastapi import HTTPException, status  # type: ignore

from src.database.models import ApplicationKey, utc_now
from src.middleware.authentication import hash_api_key
from src.applications.schemas import AppKeyCreate


def generate_plaintext_api_key() -> str:
    """Generate secure random API key with prefix."""
    return f"key_{secrets.token_urlsafe(32)}"


def create_application_key(db: Database, data: AppKeyCreate) -> Tuple[ApplicationKey, str]:
    """Create a new application key, storing hash and returning model + plaintext key."""
    plaintext_key = generate_plaintext_api_key()
    key_hash = hash_api_key(plaintext_key)

    app_code = data.app_code or "general"
    app_key_dict = ApplicationKey.create_dict(
        application_name=data.application_name,
        app_code=app_code,
        api_key_hash=key_hash,
        status="active"
    )


    db["application_keys"].insert_one(app_key_dict)
    app_key = ApplicationKey(app_key_dict)

    return app_key, plaintext_key


def list_application_keys(db: Database) -> List[ApplicationKey]:
    """List all registered application keys."""
    cursor = db["application_keys"].find().sort("created_at", pymongo.DESCENDING)
    return [ApplicationKey(d) for d in cursor]


def revoke_application_key(db: Database, key_id: str) -> ApplicationKey:
    """Revoke an existing application key by ID."""
    app_key_doc = db["application_keys"].find_one({"_id": key_id})
    if not app_key_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application key with ID '{key_id}' not found."
        )

    now = utc_now()
    db["application_keys"].update_one(
        {"_id": key_id},
        {"$set": {"status": "revoked", "updated_at": now}}
    )
    app_key_doc["status"] = "revoked"
    app_key_doc["updated_at"] = now
    return ApplicationKey(app_key_doc)
