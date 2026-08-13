from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict  # type: ignore
from typing import Optional, Dict, Any


class LogCreate(BaseModel):
    level: str = Field(..., description="Log level: INFO, WARNING, ERROR")
    event: str = Field(..., description="Application event identifier")
    message: str = Field(..., description="Descriptive log message")
    user_id: Optional[str] = Field(None, description="Optional user UUID related to this log")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context or key-value metadata")


class LogResponse(BaseModel):
    id: str
    application_id: str
    level: str
    event: str
    message: str
    user_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
