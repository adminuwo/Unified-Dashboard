from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Request  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import ApplicationKey
from src.middleware.authentication import get_current_application, validate_optional_app_key
from src.telemetry.schemas import (
    ChatTrackingCreateRequest,
    ChatTrackingResponse,
    AppDownloadCreateRequest,
    AppDownloadResponse,
    FirebaseEventCreateRequest,
    FirebaseEventResponse,
    TelemetryOverviewResponse,
    TelemetrySyncResponse
)
from src.telemetry import service, schemas


router = APIRouter(prefix="/telemetry", tags=["Telemetry & AI Tracking"])


@router.post("/chat", response_model=ChatTrackingResponse, status_code=status.HTTP_201_CREATED)
def submit_chat_tracking(
    data: ChatTrackingCreateRequest,
    app: ApplicationKey = Depends(get_current_application),
    db: Database = Depends(get_db)
):
    """Log AI Chat session prompt/token consumption (requires X-Application-Key header)."""
    entry = service.record_chat_tracking(db, app, data)
    return ChatTrackingResponse(**entry.to_dict())


@router.post("/download", response_model=AppDownloadResponse, status_code=status.HTTP_201_CREATED)
def submit_app_download(
    data: AppDownloadCreateRequest,
    request: Request,
    app: Optional[ApplicationKey] = Depends(validate_optional_app_key),
    db: Database = Depends(get_db)
):
    """Log app download/install event (supports Firebase SDK & direct mobile telemetry)."""
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    entry = service.record_app_download(db, app, data, client_ip=client_ip)
    return AppDownloadResponse(**entry.to_dict())


@router.post("/firebase-event", response_model=FirebaseEventResponse, status_code=status.HTTP_201_CREATED)
def submit_firebase_event(
    data: FirebaseEventCreateRequest,
    request: Request,
    db: Database = Depends(get_db)
):
    """Log incoming event directly from mobile client Firebase SDK (first_open, app_install, download, etc.)."""
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    return service.record_firebase_event(db, data, client_ip=client_ip)


@router.post("/firebase/install", response_model=FirebaseEventResponse, status_code=status.HTTP_201_CREATED)
def submit_firebase_install_alias(
    data: FirebaseEventCreateRequest,
    request: Request,
    db: Database = Depends(get_db)
):
    """Alias for Firebase mobile install telemetry."""
    data.event_name = "first_open"
    return submit_firebase_event(data, request, db)


@router.post("/sync", response_model=schemas.TelemetrySyncResponse)
def trigger_telemetry_sync(
    db: Database = Depends(get_db)
):
    """Trigger real-time telemetry sync from connected AI applications."""
    return service.sync_connected_apps_telemetry(db)


@router.get("/overview", response_model=TelemetryOverviewResponse)
def get_telemetry_overview(
    app_code: Optional[str] = Query(None, description="Filter by application code: ailegal, aisa, aiads, uwoconnect, efvframework"),
    db: Database = Depends(get_db)
):
    """Fetch aggregated chat tracking, token consumption, and app download metrics."""
    return service.get_telemetry_overview(db, app_code=app_code)

