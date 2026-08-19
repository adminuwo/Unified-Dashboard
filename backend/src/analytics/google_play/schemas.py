from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PlayMetricRow(BaseModel):
    metric_date: str
    dimension_type: str
    dimension_value: Optional[str] = None
    dimension_value_normalized: str
    
    current_device_installs: int = 0
    installs_on_active_devices: int = 0
    daily_device_installs: int = 0
    daily_device_uninstalls: int = 0
    daily_device_upgrades: int = 0
    current_user_installs: int = 0
    total_user_installs: int = 0
    daily_user_installs: int = 0
    daily_user_uninstalls: int = 0
    
class SyncRequest(BaseModel):
    app_codes: List[str]
    mode: str = "incremental"

class AppOverview(BaseModel):
    app_code: str
    display_name: str
    platform: str
    store: str
    package_name: str
    enabled: bool
    data_through_date: Optional[str]
    freshness_status: str

class OverviewResponse(BaseModel):
    data: Dict[str, List[AppOverview]]
    meta: Dict[str, str]

class TimeSeriesPoint(BaseModel):
    date: str
    value: Optional[int]

class AppTimeSeries(BaseModel):
    app_code: str
    points: List[TimeSeriesPoint]

class TimeSeriesData(BaseModel):
    metric: str
    aggregation: str
    granularity: str
    series: List[AppTimeSeries]

class TimeSeriesResponse(BaseModel):
    data: TimeSeriesData
    meta: Dict[str, str]

class BreakdownItem(BaseModel):
    value: str
    label: str
    metric_value: int
    percentage: float

class BreakdownData(BaseModel):
    dimension: str
    metric: str
    items: List[BreakdownItem]
    other: Dict[str, float]

class BreakdownResponse(BaseModel):
    data: BreakdownData
