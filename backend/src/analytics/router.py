from fastapi import APIRouter, Depends, Query, status # type: ignore
from pymongo.database import Database # type: ignore
from typing import List, Optional

from src.database.connection import get_db
from src.admin.router import get_current_admin

router = APIRouter(prefix="/api/admin/analytics", tags=["Analytics"])

@router.get("/google-play/overview")
def get_overview(
    app_codes: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Database = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    codes = app_codes.split(',')
    
    # Build match condition
    match_filter: dict = {
        "app_code": {"$in": codes},
        "dimension_type": "overview"
    }
    
    if start_date and end_date:
        match_filter["metric_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        match_filter["metric_date"] = {"$gte": start_date}
    elif end_date:
        match_filter["metric_date"] = {"$lte": end_date}
    
    # Simple aggregation to fetch real data from DB
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": "$app_code",
            "daily_user_installs": {"$sum": "$daily_user_installs"},
            "daily_user_uninstalls": {"$sum": "$daily_user_uninstalls"},
            "net_user_installs": {"$sum": "$net_daily_user_installs"},
            "daily_device_installs": {"$sum": "$daily_device_installs"},
            "daily_device_uninstalls": {"$sum": "$daily_device_uninstalls"},
            "net_device_installs": {"$sum": "$net_daily_device_installs"},
            "install_events": {"$sum": "$install_events"},
            "uninstall_events": {"$sum": "$uninstall_events"},
            "total_user_installs_latest": {"$max": "$total_user_installs"},
            "active_device_installs_latest": {"$max": "$installs_on_active_devices"},
            "avg_active_devices": {"$avg": "$installs_on_active_devices"},
            "avg_daily_user_loss": {"$avg": "$daily_user_uninstalls"}
        }}
    ]
    
    results = list(db["play_install_metrics"].aggregate(pipeline))
    
    apps_data = []
    combined = {
        "daily_user_installs": 0,
        "daily_user_uninstalls": 0,
        "net_user_installs": 0,
        "daily_device_installs": 0,
        "daily_device_uninstalls": 0,
        "net_device_installs": 0,
        "install_events": 0,
        "uninstall_events": 0,
        "total_user_installs_latest": 0,
        "active_device_installs_latest": 0,
        "avg_active_devices": 0.0,
        "avg_daily_user_loss": 0.0,
        "snapshot_as_of_date": end_date,
        "cross_app_unique": False
    }
    
    for res in results:
        # Get latest active device snapshot
        latest_doc = db["play_install_metrics"].find_one(
            {"app_code": res["_id"], "dimension_type": "overview"},
            sort=[("metric_date", -1)]
        )
        current_active = latest_doc.get("installs_on_active_devices", 0) if latest_doc else 0

        # Query iOS downloads for this app
        ios_records = list(db["app_store_metrics"].find({"app_code": res["_id"]}))
        ios_total = sum(r.get("total_downloads", 0) for r in ios_records)
        ios_first_time = sum(r.get("first_time_downloads", 0) for r in ios_records)
        ios_redownloads = sum(r.get("redownloads", 0) for r in ios_records)
        ios_views = sum(r.get("page_views", 0) for r in ios_records)
        ios_impressions = sum(r.get("impressions", 0) for r in ios_records)

        apps_data.append({
            "app_code": res["_id"],
            "display_name": res["_id"].upper(),
            "daily_user_installs": res["daily_user_installs"],
            "daily_user_uninstalls": res["daily_user_uninstalls"],
            "net_user_installs": res["net_user_installs"],
            "daily_device_installs": res["daily_device_installs"],
            "daily_device_uninstalls": res["daily_device_uninstalls"],
            "install_events": res.get("install_events", res["daily_device_installs"]),
            "uninstall_events": res.get("uninstall_events", res["daily_device_uninstalls"]),
            "total_user_installs_latest": res["total_user_installs_latest"],
            "active_device_installs_latest": current_active,
            "avg_active_devices": round(float(res.get("avg_active_devices") or 0.0), 1),
            "avg_daily_user_loss": round(float(res.get("avg_daily_user_loss") or 0.0), 2),
            "ios_total_downloads": ios_total,
            "ios_first_time_downloads": ios_first_time,
            "ios_redownloads": ios_redownloads,
            "ios_page_views": ios_views,
            "ios_impressions": ios_impressions,
            "snapshot_as_of_date": end_date
        })
        # Add to combined
        combined["daily_user_installs"] += res["daily_user_installs"]
        combined["daily_user_uninstalls"] += res["daily_user_uninstalls"]
        combined["net_user_installs"] += res["net_user_installs"]
        combined["daily_device_installs"] += res["daily_device_installs"]
        combined["daily_device_uninstalls"] += res["daily_device_uninstalls"]
        combined["net_device_installs"] += res["net_device_installs"]
        combined["install_events"] += res.get("install_events", res["daily_device_installs"])
        combined["uninstall_events"] += res.get("uninstall_events", res["daily_device_uninstalls"])
        combined["total_user_installs_latest"] += res.get("total_user_installs_latest", 0)
        combined["active_device_installs_latest"] += current_active
        combined["avg_active_devices"] = round(float(res.get("avg_active_devices") or 0.0), 1)
        combined["avg_daily_user_loss"] = round(float(res.get("avg_daily_user_loss") or 0.0), 2)
        if "ios_total_downloads" not in combined:
            combined["ios_total_downloads"] = 0
            combined["ios_first_time_downloads"] = 0
            combined["ios_redownloads"] = 0
            combined["ios_page_views"] = 0
            combined["ios_impressions"] = 0
        combined["ios_total_downloads"] += ios_total
        combined["ios_first_time_downloads"] += ios_first_time
        combined["ios_redownloads"] += ios_redownloads
        combined["ios_page_views"] += ios_views
        combined["ios_impressions"] += ios_impressions

    # If DB is empty (i.e. sync hasn't run yet due to permissions), fallback to 0
    if not apps_data:
        for code in codes:
            apps_data.append({
                "app_code": code,
                "display_name": code.upper(),
                "daily_user_installs": 0,
                "daily_user_uninstalls": 0,
                "net_user_installs": 0,
                "total_user_installs_latest": 0,
                "active_device_installs_latest": 0,
                "snapshot_as_of_date": end_date
            })
            
    # Determine last sync time from latest record
    latest_record = db["play_install_metrics"].find_one(
        sort=[("metric_date", -1)]
    )
    last_sync_date = latest_record["metric_date"] if latest_record else None
    has_data = len(results) > 0

    return {
        "data": {
            "source": {
                "provider": "google_play_bulk_reports",
                "source_timezone": "America/Los_Angeles",
                "expected_delay_days": {"minimum": 3, "maximum": 7},
                "last_sync_at": last_sync_date,
                "data_through_date": end_date,
                "freshness_status": "fresh" if has_data else "no_data"
            },
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "combined": combined,
            "apps": apps_data
        }
    }

@router.get("/google-play/timeseries")
def get_timeseries(
    app_codes: str = Query(...),
    metric: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    granularity: str = Query("day"),
    db: Database = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    codes = app_codes.split(',')
    
    match_filter: dict = {
        "app_code": {"$in": codes},
        "dimension_type": "overview"
    }
    if start_date and end_date:
        match_filter["metric_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        match_filter["metric_date"] = {"$gte": start_date}
    elif end_date:
        match_filter["metric_date"] = {"$lte": end_date}

    # Fetch Google Play (Android) records
    play_records = list(db["play_install_metrics"].find(match_filter).sort("metric_date", 1))

    # Fetch Apple App Store (iOS) records
    ios_filter: dict = {"app_code": {"$in": codes}}
    if start_date and end_date:
        ios_filter["metric_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        ios_filter["metric_date"] = {"$gte": start_date}
    elif end_date:
        ios_filter["metric_date"] = {"$lte": end_date}

    ios_records = list(db["app_store_metrics"].find(ios_filter).sort("metric_date", 1))

    android_points = []
    android_cum = 0
    for r in play_records:
        date_val = r.get("metric_date")
        if metric == "total_installs":
            android_cum += r.get("daily_device_installs", 0)
            val = android_cum
        elif metric in ["active_devices", "active_device_installs"]:
            val = r.get("installs_on_active_devices", 0)
        elif metric in ["user_loss", "daily_user_uninstalls"]:
            val = r.get("daily_user_uninstalls", 0)
        else:
            val = r.get("daily_device_installs", 0)
        android_points.append({"date": date_val, "value": val})

    ios_points = []
    ios_cum = 0
    for r in ios_records:
        date_val = r.get("metric_date")
        if metric == "total_installs":
            ios_cum += r.get("total_downloads", 0)
            val = ios_cum
        elif metric in ["active_devices", "active_device_installs"]:
            val = r.get("first_time_downloads", 0)
        elif metric in ["user_loss", "daily_user_uninstalls"]:
            val = r.get("redownloads", 0)
        else:
            val = r.get("total_downloads", 0)
        ios_points.append({"date": date_val, "value": val})

    return {
        "data": {
            "metric": metric,
            "aggregation": "sum",
            "granularity": granularity,
            "android": android_points,
            "ios": ios_points,
            "series": [
                {"platform": "android", "name": "Android (Google Play)", "points": android_points},
                {"platform": "ios", "name": "iOS (App Store)", "points": ios_points}
            ]
        },
        "meta": {
            "source_timezone": "America/Los_Angeles",
            "data_through_date": end_date or "",
            "correlation_id": "real-time-db"
        }
    }

@router.get("/google-play/status")
def get_status(
    db: Database = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Check actual data presence per app in the DB
    app_codes = ["aisa", "ailegal"]
    app_statuses = []
    for code in app_codes:
        count = db["play_install_metrics"].count_documents({"app_code": code})
        app_statuses.append({
            "app_code": code,
            "freshness_status": "fresh" if count > 0 else "no_data"
        })

    has_any_data = any(a["freshness_status"] == "fresh" for a in app_statuses)
    return {
        "data": {
            "connectors": [
                {
                    "connector_id": "gplay_main",
                    "status": "healthy" if has_any_data else "no_data",
                    "apps": app_statuses
                }
            ]
        }
    }

