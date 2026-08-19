from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AppStoreConnectorConfig(BaseModel):
    connector_id: str
    display_name: str
    provider: str
    issuer_id: str
    runtime_key_id: str
    runtime_private_key_secret_resource: str
    environment: str
    enabled: bool
    access_mode: str
    health: Dict[str, Any]
    last_successful_sync_at: Optional[datetime] = None

class AppMapping(BaseModel):
    mapping_id: str
    application_id: str
    app_code: str
    display_name: str
    platform: str = "ios"
    store: str = "app_store"
    app_store_connect_app_id: str
    app_apple_id: str
    bundle_id: str
    connector_id: str
    enabled: bool
    enabled_report_families: List[str]

class ReportRequest(BaseModel):
    report_request_record_id: str
    connector_id: str
    app_code: str
    app_store_connect_app_id: str
    apple_report_request_id: str
    access_type: str
    stopped_due_to_inactivity: bool = False
    status: str
    first_seen_at: datetime
    last_checked_at: datetime
    last_report_discovered_at: Optional[datetime] = None

class ReportSegment(BaseModel):
    segment_record_id: str
    connector_id: str
    app_code: str
    apple_report_id: str
    apple_instance_id: str
    apple_segment_id: str
    processing_date: str
    granularity: str
    checksum: str
    checksum_algorithm: str
    size_bytes: int
    detected_encoding: str
    detected_delimiter: str
    schema_fingerprint: str
    row_count: int
    status: str
    downloaded_at: datetime
    processed_at: Optional[datetime] = None
    sync_run_id: str
    error_code: Optional[str] = None
    error_message_safe: Optional[str] = None

class MetricRow(BaseModel):
    metric_row_id: str
    connector_id: str
    app_code: str
    application_id: str
    app_store_connect_app_id: str
    app_apple_id: str
    bundle_id: str
    report_family: str
    content_level: str
    granularity: str
    metric_date: str
    source_timezone: str
    processing_date: str
    partition_key: str
    revision_id: str
    row_key: str
    dimensions: Dict[str, Any]
    metrics: Dict[str, Any]
    quality: Dict[str, bool]
    active_revision: bool
    source_segment_id: str
    source_row_number: int
    sync_run_id: str

class PartitionRevision(BaseModel):
    revision_id: str
    provider: str
    connector_id: str
    app_code: str
    report_family: str
    content_level: str
    granularity: str
    metric_date: str
    partition_key: str
    processing_date: str
    status: str
    complete: bool
    corrected: bool
    row_count: int
    segment_count: int
    activated_at: Optional[datetime] = None
    superseded_revision_id: Optional[str] = None
    sync_run_id: str

class DailyRollup(BaseModel):
    rollup_id: str
    connector_id: str
    app_code: str
    application_id: str
    metric_date: str
    source_timezone: str
    first_time_downloads: int
    redownloads: int
    total_downloads: int
    installation_events_opt_in: int
    deletion_events_opt_in: int
    net_installation_events_opt_in: int
    download_revision_id: str
    usage_revision_id: str
    download_data_complete: bool
    usage_data_complete: bool
    quality: Dict[str, bool]
