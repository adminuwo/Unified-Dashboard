from typing import List
from fastapi import APIRouter, Depends, status  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.applications.schemas import AppKeyCreate, AppKeyResponse, AppKeyCreatedResponse
from src.applications import service

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/keys", response_model=AppKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_key(data: AppKeyCreate, db: Database = Depends(get_db)):
    """Generate a new API key for a standalone application."""
    app_key, plaintext_key = service.create_application_key(db, data)
    return AppKeyCreatedResponse(
        id=app_key.id,
        application_name=app_key.application_name,
        status=app_key.status,
        created_at=app_key.created_at,
        updated_at=app_key.updated_at,
        api_key=plaintext_key
    )


@router.get("/keys", response_model=List[AppKeyResponse])
def get_keys(db: Database = Depends(get_db)):
    """List all registered application API keys."""
    return service.list_application_keys(db)


@router.delete("/keys/{key_id}", response_model=AppKeyResponse)
def revoke_key(key_id: str, db: Database = Depends(get_db)):
    """Revoke an application API key."""
    return service.revoke_application_key(db, key_id)
