from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database

from src.database.connection import get_db
from src.admin.router import get_current_admin
from src.store_analytics.schemas import (
    StoreAnalyticsSummaryResponse,
    SyncStatusResponse,
    StoreAnalyticsItem
)
from src.store_analytics import service

router = APIRouter(prefix="/admin/store-analytics", tags=["App Store Analytics"])


@router.get("", response_model=StoreAnalyticsSummaryResponse)
@router.get("/", response_model=StoreAnalyticsSummaryResponse, include_in_schema=False)
def get_store_analytics_summary(
    project: Optional[str] = Query(None, description="Filter by project: AISA, AI_LEGAL, or ALL"),
    platform: Optional[str] = Query(None, description="Filter by platform: android, ios"),
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch store analytics metrics, project-wise breakdown, and daily timeline for dashboard UI."""
    return service.get_store_analytics_summary(
        db=db,
        project=project,
        platform=platform,
        date_range=date_range
    )


@router.get("/downloads", response_model=List[StoreAnalyticsItem])
def get_store_downloads(
    project: Optional[str] = Query(None, description="Filter by project"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(100, ge=1, le=500),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Retrieve detailed store download records from MongoDB."""
    query_filter = {}
    if project and project.upper() != "ALL":
        query_filter["project"] = project.upper()
    if platform:
        query_filter["platform"] = platform.lower()

    cursor = db["store_analytics"].find(query_filter).sort("date", -1).limit(limit)
    items = []
    for doc in cursor:
        doc["id"] = str(doc.get("_id") or doc.get("id"))
        items.append(StoreAnalyticsItem(**doc))
    return items


@router.post("/sync", response_model=SyncStatusResponse)
def trigger_manual_sync(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Manually trigger background synchronization of Google Play Store analytics."""
    return service.sync_google_play_data(db)
