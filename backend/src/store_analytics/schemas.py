from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class StoreAnalyticsItem(BaseModel):
    id: str
    project: str
    platform: str
    package_name: str
    date: str
    metric: str
    value: int
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectMetricSummary(BaseModel):
    project: str
    platform: str
    package_name: str
    total_downloads: int
    label: str


class TimelinePoint(BaseModel):
    date: str
    total: int
    aisa: int
    ai_legal: int


class StoreAnalyticsSummaryResponse(BaseModel):
    total_android_downloads: int
    projects: List[ProjectMetricSummary]
    timeline: List[TimelinePoint]
    last_synced_at: Optional[str] = None
    sync_status: str = "ok"
    status_message: Optional[str] = None


class SyncStatusResponse(BaseModel):
    success: bool
    message: str
    records_inserted_or_updated: int
    errors: List[str] = []
    synced_at: datetime
