from typing import Dict, Any, Optional, List
from pymongo.database import Database  # type: ignore

from src.database.models import ChatTrackingEntry, AppDownloadEntry, ApplicationKey
from src.telemetry.schemas import ChatTrackingCreateRequest, AppDownloadCreateRequest, TelemetryOverviewResponse


def record_chat_tracking(
    db: Database,
    app: ApplicationKey,
    data: ChatTrackingCreateRequest
) -> ChatTrackingEntry:
    """Record AI chat prompt/token usage telemetry."""
    calc_tokens = data.total_tokens if data.total_tokens and data.total_tokens > 0 else (data.prompt_tokens + data.completion_tokens)

    entry_dict = ChatTrackingEntry.create_dict(
        application_id=app.id,
        app_code=app.app_code or "general",
        session_id=data.session_id,
        model_name=data.model_name,
        prompt_tokens=data.prompt_tokens,
        completion_tokens=data.completion_tokens,
        total_tokens=calc_tokens,
        latency_ms=data.latency_ms,
        user_id=data.user_id,
        extra_metadata=data.metadata
    )

    db["chat_tracking"].insert_one(entry_dict)
    return ChatTrackingEntry(entry_dict)


def record_app_download(
    db: Database,
    app: ApplicationKey,
    data: AppDownloadCreateRequest
) -> AppDownloadEntry:
    """Record an app download/install telemetry event."""
    entry_dict = AppDownloadEntry.create_dict(
        application_id=app.id,
        app_code=app.app_code or "general",
        platform=data.platform,
        version=data.version,
        ip_country=data.ip_country or "IN",
        user_id=data.user_id
    )

    db["app_downloads"].insert_one(entry_dict)
    return AppDownloadEntry(entry_dict)


def get_telemetry_overview(
    db: Database,
    app_code: Optional[str] = None
) -> TelemetryOverviewResponse:
    """Compute aggregated telemetry stats per application or globally."""
    query_filter: Dict[str, Any] = {}
    if app_code and app_code.lower() != "all":
        query_filter["app_code"] = app_code.lower()

    # Total unique chat sessions & total tokens
    pipeline_chat = [
        {"$match": query_filter},
        {
            "$group": {
                "_id": None,
                "total_tokens": {"$sum": "$total_tokens"},
                "avg_latency": {"$avg": "$latency_ms"},
                "sessions": {"$addToSet": "$session_id"}
            }
        }
    ]
    chat_agg = list(db["chat_tracking"].aggregate(pipeline_chat))
    total_tokens = int(chat_agg[0]["total_tokens"]) if chat_agg else 0
    avg_latency = float(chat_agg[0]["avg_latency"]) if chat_agg and chat_agg[0].get("avg_latency") else 0.0
    total_sessions = len(chat_agg[0]["sessions"]) if chat_agg else 0

    # Total downloads & platform breakdown
    downloads_filter = {"app_code": app_code.lower()} if app_code and app_code.lower() != "all" else {}
    total_downloads = db["app_downloads"].count_documents(downloads_filter)

    platform_pipeline = [
        {"$match": downloads_filter},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
    ]
    platform_agg = list(db["app_downloads"].aggregate(platform_pipeline))
    downloads_by_platform = {p["_id"]: p["count"] for p in platform_agg if p.get("_id")}

    # AI Model Share
    model_pipeline = [
        {"$match": query_filter},
        {"$group": {"_id": "$model_name", "count": {"$sum": 1}, "tokens": {"$sum": "$total_tokens"}}},
        {"$sort": {"count": -1}}
    ]
    model_agg = list(db["chat_tracking"].aggregate(model_pipeline))
    model_share = [
        {"model": m["_id"], "count": m["count"], "tokens": m["tokens"]}
        for m in model_agg if m.get("_id")
    ]

    return TelemetryOverviewResponse(
        app_code=app_code,
        total_chat_sessions=total_sessions,
        total_tokens=total_tokens,
        avg_latency_ms=round(avg_latency, 2),
        total_downloads=total_downloads,
        downloads_by_platform=downloads_by_platform,
        model_share=model_share
    )
