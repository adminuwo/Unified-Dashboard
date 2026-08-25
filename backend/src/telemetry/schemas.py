from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


class ChatTrackingCreateRequest(BaseModel):
    session_id: str = Field(..., description="Unique chat session identifier")
    model_name: str = Field(..., description="AI model used, e.g. gpt-4o, claude-3-5, gemini-1.5")
    prompt_tokens: int = Field(0, ge=0, description="Prompt/input token count")
    completion_tokens: int = Field(0, ge=0, description="Completion/output token count")
    total_tokens: Optional[int] = Field(None, ge=0, description="Total token count (calculated if omitted)")
    latency_ms: float = Field(0.0, ge=0.0, description="Response latency in milliseconds")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra execution metadata")


class ChatTrackingResponse(BaseModel):
    id: str
    application_id: str
    app_code: str
    session_id: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    user_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppDownloadCreateRequest(BaseModel):
    platform: str = Field(..., description="OS/Platform: android, ios, windows, web_pwa")
    version: str = Field("1.0.0", description="Application release version")
    ip_country: Optional[str] = Field("IN", description="ISO country code")
    user_id: Optional[str] = Field(None, description="Associated user ID if authenticated")


class AppDownloadResponse(BaseModel):
    id: str
    application_id: str
    app_code: str
    platform: str
    version: str
    ip_country: str
    user_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryOverviewResponse(BaseModel):
    app_code: Optional[str] = None
    total_chat_sessions: int
    total_prompts: int = 0
    total_tokens: int
    avg_latency_ms: float
    total_downloads: int
    downloads_by_platform: Dict[str, int]
    model_share: List[Dict[str, Any]]
    timeline: Optional[List[Dict[str, Any]]] = None
    recent_sessions: Optional[List[Dict[str, Any]]] = None


class TelemetrySyncResponse(BaseModel):
    success: bool
    message: str
    records_synced: int = 0
    synced_at: datetime

