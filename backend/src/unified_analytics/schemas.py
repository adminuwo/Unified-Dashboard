from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TimelinePoint(BaseModel):
    date: str
    value: float = 0.0
    breakdown: Optional[Dict[str, Any]] = None


class PlatformOverviewResponse(BaseModel):
    total_users: int = 0
    active_users_24h: int = 0
    total_web_pageviews: int = 0
    total_mobile_installs: int = 0
    total_revenue: float = 0.0
    backend_health: str = "healthy"
    avg_backend_latency_ms: float = 0.0
    error_rate_pct: float = 0.0
    platform_breakdown: Dict[str, Any] = Field(default_factory=dict)
    app_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    sync_status: Dict[str, Any] = Field(default_factory=dict)
    last_synced_at: Optional[datetime] = None


class WebAnalyticsResponse(BaseModel):
    total_pageviews: int = 0
    unique_visitors: int = 0
    bounce_rate_pct: float = 0.0
    avg_session_duration_s: float = 0.0
    active_realtime_users: int = 0
    top_pages: List[Dict[str, Any]] = Field(default_factory=list)
    traffic_sources: List[Dict[str, Any]] = Field(default_factory=list)
    device_split: Dict[str, int] = Field(default_factory=dict)
    browser_split: Dict[str, int] = Field(default_factory=dict)
    country_split: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    app_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "ga4_and_collector"
    cached: bool = False


class MobileAnalyticsResponse(BaseModel):
    total_android_installs: int = 0
    total_ios_units: int = 0
    total_mobile_downloads: int = 0
    active_devices: int = 0
    uninstalls_android: int = 0
    crash_rate_pct: float = 0.0
    avg_rating: float = 0.0
    android_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    ios_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    app_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "google_play_and_appstore"
    cached: bool = False


class GcpMonitoringResponse(BaseModel):
    total_api_requests: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_5xx_rate: float = 0.0
    error_4xx_rate: float = 0.0
    cpu_utilization_pct: float = 0.0
    memory_utilization_pct: float = 0.0
    active_instances: int = 1
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    top_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "healthy"
    cached: bool = False


class UserActivityResponse(BaseModel):
    total_sessions: int = 0
    total_events: int = 0
    feature_usage: List[Dict[str, Any]] = Field(default_factory=list)
    ai_token_usage: Dict[str, Any] = Field(default_factory=dict)
    recent_events: List[Dict[str, Any]] = Field(default_factory=list)
    cached: bool = False


class RevenueBreakdownResponse(BaseModel):
    total_revenue: float = 0.0
    currency: str = "INR"
    active_subscribers: int = 0
    transactions_count: int = 0
    mrr: float = 0.0
    plan_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    app_revenue: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    cached: bool = False


class SyncStatusResponse(BaseModel):
    success: bool
    provider: str
    message: str
    synced_at: datetime


class EventCollectRequest(BaseModel):
    app_code: str = "general"
    event_type: str = "pageview"
    path: str = "/"
    visitor_id: Optional[str] = None
    session_id: Optional[str] = None
    device: Optional[str] = "desktop"
    browser: Optional[str] = "other"
    os_name: Optional[str] = "other"
    country: Optional[str] = "IN"
    event_name: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = 0.0
