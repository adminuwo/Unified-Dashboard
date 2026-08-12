from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class AppKeyCreate(BaseModel):
    application_name: str = Field(..., min_length=2, max_length=100, description="Generic application name")


class AppKeyResponse(BaseModel):
    id: str
    application_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class AppKeyCreatedResponse(AppKeyResponse):
    api_key: str = Field(..., description="Plaintext API key. Store securely as it will not be shown again.")
