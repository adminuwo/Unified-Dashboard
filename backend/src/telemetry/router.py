from typing import Optional
from fastapi import APIRouter, Depends, status, Query  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import ApplicationKey
from src.middleware.authentication import get_current_application
from src.telemetry.schemas import (
    ChatTrackingCreateRequest,
    ChatTrackingResponse,
    AppDownloadCreateRequest,
    AppDownloadResponse,
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
    app: ApplicationKey = Depends(get_current_application),
    db: Database = Depends(get_db)
):
    """Log app download/install event (requires X-Application-Key header)."""
    entry = service.record_app_download(db, app, data)
    return AppDownloadResponse(**entry.to_dict())


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

