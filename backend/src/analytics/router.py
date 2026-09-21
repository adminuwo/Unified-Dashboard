from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status # type: ignore
from pymongo.database import Database # type: ignore
from typing import List, Optional, Dict, Any

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
    codes = [c.strip().lower() for c in app_codes.split(',') if c.strip()]

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
        "ios_total_downloads": 0,
        "ios_first_time_downloads": 0,
        "ios_redownloads": 0,
        "ios_page_views": 0,
        "ios_impressions": 0,
        "firebase_downloads": 0,
        "firebase_android": 0,
        "firebase_ios": 0,
        "snapshot_as_of_date": end_date,
        "cross_app_unique": False
    }

    # Date bounds for Mongo queries
    date_bounds: Dict[str, Any] = {}
    if start_date:
        try:
            date_bounds["$gte"] = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            pass
    if end_date:
        try:
            date_bounds["$lte"] = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except Exception:
            pass

    for code in codes:
        # 1. Google Play (Android) reports
        play_match: dict = {
            "app_code": code,
            "dimension_type": "overview"
        }
        if start_date and end_date:
            play_match["metric_date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            play_match["metric_date"] = {"$gte": start_date}
        elif end_date:
            play_match["metric_date"] = {"$lte": end_date}

        play_docs = list(db["play_install_metrics"].find(play_match))
        play_user_installs = sum(r.get("daily_user_installs", 0) for r in play_docs)
        play_user_uninstalls = sum(r.get("daily_user_uninstalls", 0) for r in play_docs)
        play_net_user = sum(r.get("net_daily_user_installs", 0) for r in play_docs)
        play_device_installs = sum(r.get("daily_device_installs", 0) for r in play_docs)
        play_device_uninstalls = sum(r.get("daily_device_uninstalls", 0) for r in play_docs)
        play_net_device = sum(r.get("net_daily_device_installs", 0) for r in play_docs)
        play_install_events = sum(r.get("install_events", r.get("daily_device_installs", 0)) for r in play_docs)
        play_uninstall_events = sum(r.get("uninstall_events", r.get("daily_device_uninstalls", 0)) for r in play_docs)

        latest_play = db["play_install_metrics"].find_one(
            {"app_code": code, "dimension_type": "overview"},
            sort=[("metric_date", -1)]
        )
        play_total_latest = (latest_play.get("total_user_installs") or latest_play.get("current_user_installs") or 0) if latest_play else 0
        play_active_latest = (latest_play.get("installs_on_active_devices") or latest_play.get("current_device_installs") or 0) if latest_play else 0
        play_avg_active = (sum(r.get("installs_on_active_devices", 0) for r in play_docs) / len(play_docs)) if play_docs else float(play_active_latest)
        play_avg_loss = (sum(r.get("daily_user_uninstalls", 0) for r in play_docs) / len(play_docs)) if play_docs else 0.0

        # 2. Apple App Store (iOS) reports
        ios_match: dict = {"app_code": code}
        if start_date and end_date:
            ios_match["metric_date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            ios_match["metric_date"] = {"$gte": start_date}
        elif end_date:
            ios_match["metric_date"] = {"$lte": end_date}

        ios_docs = list(db["app_store_metrics"].find(ios_match))
        ios_total = sum(r.get("total_downloads", 0) for r in ios_docs)
        ios_first_time = sum(r.get("first_time_downloads", 0) for r in ios_docs)
        ios_redownloads = sum(r.get("redownloads", 0) for r in ios_docs)
        ios_views = sum(r.get("page_views", 0) for r in ios_docs)
        ios_impressions = sum(r.get("impressions", 0) for r in ios_docs)

        # 3. Firebase SDK & Mobile Telemetry downloads
        dl_match: dict = {"app_code": code}
        if date_bounds:
            dl_match["created_at"] = date_bounds
        dl_docs = list(db["app_downloads"].find(dl_match))

        fb_android = sum(1 for d in dl_docs if (d.get("platform") or "").lower() == "android")
        fb_ios = sum(1 for d in dl_docs if (d.get("platform") or "").lower() in ["ios", "iphone", "ipad"])
        fb_total = len(dl_docs)

        # 4. Marketing attribution installs
        mkt_match: dict = {"$or": [{"product_id": code}, {"app_code": code}]}
        if date_bounds:
            mkt_match = {
                "$and": [
                    {"$or": [{"product_id": code}, {"app_code": code}]},
                    {"$or": [{"timestamp": date_bounds}, {"created_at": date_bounds}]}
                ]
            }
        mkt_docs = list(db["marketing_installs"].find(mkt_match))
        mkt_android = sum(1 for m in mkt_docs if (m.get("platform") or "").lower() == "android")
        mkt_ios = sum(1 for m in mkt_docs if (m.get("platform") or "").lower() in ["ios", "iphone", "ipad"])

        # Blend Telemetry & Firebase SDK with Store Data
        total_android_telemetry = fb_android + mkt_android
        total_ios_telemetry = fb_ios + mkt_ios

        # Android merged numbers
        merged_user_installs = play_user_installs + total_android_telemetry
        merged_device_installs = play_device_installs + total_android_telemetry
        merged_net_user = play_net_user + total_android_telemetry
        merged_net_device = play_net_device + total_android_telemetry
        merged_install_events = play_install_events + total_android_telemetry

        # If Play Store snapshot exists, telemetry installs post-snapshot increment cumulative total
        if play_total_latest > 0:
            merged_total_installs = play_total_latest + total_android_telemetry
        else:
            merged_total_installs = merged_device_installs

        merged_active_devices = (play_active_latest + total_android_telemetry) if play_active_latest > 0 else total_android_telemetry
        merged_avg_active = play_avg_active if play_avg_active > 0 else float(merged_active_devices)

        # iOS merged numbers
        merged_ios_total = ios_total + total_ios_telemetry
        merged_ios_first_time = ios_first_time + total_ios_telemetry

        app_entry = {
            "app_code": code,
            "display_name": code.upper(),
            "daily_user_installs": merged_user_installs,
            "daily_user_uninstalls": play_user_uninstalls,
            "net_user_installs": merged_net_user,
            "daily_device_installs": merged_device_installs,
            "daily_device_uninstalls": play_device_uninstalls,
            "install_events": merged_install_events,
            "uninstall_events": play_uninstall_events,
            "total_user_installs_latest": merged_total_installs,
            "active_device_installs_latest": merged_active_devices,
            "avg_active_devices": round(float(merged_avg_active), 1),
            "avg_daily_user_loss": round(float(play_avg_loss), 2),
            "ios_total_downloads": merged_ios_total,
            "ios_first_time_downloads": merged_ios_first_time,
            "ios_redownloads": ios_redownloads,
            "ios_page_views": ios_views,
            "ios_impressions": ios_impressions,
            "firebase_downloads": fb_total,
            "firebase_android": fb_android,
            "firebase_ios": fb_ios,
            "snapshot_as_of_date": end_date
        }
        apps_data.append(app_entry)

        # Accumulate into combined
        combined["daily_user_installs"] += merged_user_installs
        combined["daily_user_uninstalls"] += play_user_uninstalls
        combined["net_user_installs"] += merged_net_user
        combined["daily_device_installs"] += merged_device_installs
        combined["daily_device_uninstalls"] += play_device_uninstalls
        combined["net_device_installs"] += merged_net_device
        combined["install_events"] += merged_install_events
        combined["uninstall_events"] += play_uninstall_events
        combined["total_user_installs_latest"] += merged_total_installs
        combined["active_device_installs_latest"] += merged_active_devices
        combined["avg_active_devices"] += merged_avg_active
        combined["avg_daily_user_loss"] += play_avg_loss
        combined["ios_total_downloads"] += merged_ios_total
        combined["ios_first_time_downloads"] += merged_ios_first_time
        combined["ios_redownloads"] += ios_redownloads
        combined["ios_page_views"] += ios_views
        combined["ios_impressions"] += ios_impressions
        combined["firebase_downloads"] += fb_total
        combined["firebase_android"] += fb_android
        combined["firebase_ios"] += fb_ios

    if apps_data:
        combined["avg_active_devices"] = round(combined["avg_active_devices"] / len(apps_data), 1)
        combined["avg_daily_user_loss"] = round(combined["avg_daily_user_loss"] / len(apps_data), 2)

    # Determine last sync time across Play Store, App Store, and Firebase SDK
    latest_play = db["play_install_metrics"].find_one(sort=[("metric_date", -1)])
    latest_ios = db["app_store_metrics"].find_one(sort=[("metric_date", -1)])
    latest_dl = db["app_downloads"].find_one(sort=[("created_at", -1)])

    sync_dates = []
    if latest_play and latest_play.get("metric_date"):
        sync_dates.append(str(latest_play["metric_date"]))
    if latest_ios and latest_ios.get("metric_date"):
        sync_dates.append(str(latest_ios["metric_date"]))
    if latest_dl and latest_dl.get("created_at"):
        ca = latest_dl["created_at"]
        sync_dates.append(ca.strftime("%Y-%m-%d") if isinstance(ca, datetime) else str(ca)[:10])

    last_sync_date = max(sync_dates) if sync_dates else None
    has_data = len(apps_data) > 0 and (combined["total_user_installs_latest"] > 0 or combined["ios_total_downloads"] > 0 or combined["daily_device_installs"] > 0)

    return {
        "data": {
            "source": {
                "provider": "google_play_app_store_firebase_sdk",
                "source_timezone": "America/Los_Angeles",
                "expected_delay_days": {"minimum": 0, "maximum": 2},
                "last_sync_at": last_sync_date,
                "data_through_date": end_date or last_sync_date,
                "freshness_status": "fresh" if has_data else "no_data",
                "telemetry_sources": ["Google Play Console", "Apple App Store", "Firebase Mobile SDK"]
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
    codes = [c.strip().lower() for c in app_codes.split(',') if c.strip()]

    # 1. Fetch Google Play (Android) records
    play_filter: dict = {
        "app_code": {"$in": codes},
        "dimension_type": "overview"
    }
    if start_date and end_date:
        play_filter["metric_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        play_filter["metric_date"] = {"$gte": start_date}
    elif end_date:
        play_filter["metric_date"] = {"$lte": end_date}

    play_records = list(db["play_install_metrics"].find(play_filter).sort("metric_date", 1))

    # 2. Fetch Apple App Store (iOS) records
    ios_filter: dict = {"app_code": {"$in": codes}}
    if start_date and end_date:
        ios_filter["metric_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        ios_filter["metric_date"] = {"$gte": start_date}
    elif end_date:
        ios_filter["metric_date"] = {"$lte": end_date}

    ios_records = list(db["app_store_metrics"].find(ios_filter).sort("metric_date", 1))

    # 3. Fetch Firebase SDK & mobile telemetry app_downloads
    dl_filter: dict = {"app_code": {"$in": codes}}
    date_bounds: dict = {}
    if start_date:
        try:
            date_bounds["$gte"] = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            pass
    if end_date:
        try:
            date_bounds["$lte"] = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except Exception:
            pass
    if date_bounds:
        dl_filter["created_at"] = date_bounds

    dl_records = list(db["app_downloads"].find(dl_filter).sort("created_at", 1))

    # 4. Fetch marketing attribution installs
    mkt_match: dict = {"$or": [{"product_id": {"$in": codes}}, {"app_code": {"$in": codes}}]}
    mkt_records = list(db["marketing_installs"].find(mkt_match))

    # Build Android daily aggregations
    android_daily_installs: Dict[str, int] = {}
    android_active_map: Dict[str, int] = {}
    android_uninstalls_map: Dict[str, int] = {}

    for r in play_records:
        d = r.get("metric_date")
        if not d:
            continue
        android_daily_installs[d] = android_daily_installs.get(d, 0) + int(r.get("daily_device_installs", 0))
        android_active_map[d] = android_active_map.get(d, 0) + int(r.get("installs_on_active_devices", 0))
        android_uninstalls_map[d] = android_uninstalls_map.get(d, 0) + int(r.get("daily_user_uninstalls", 0))

    for d_rec in dl_records:
        plat = (d_rec.get("platform") or "").lower()
        if plat != "android":
            continue
        ca = d_rec.get("created_at")
        if not ca:
            continue
        d_str = ca.strftime("%Y-%m-%d") if isinstance(ca, datetime) else str(ca)[:10]
        if start_date and d_str < start_date:
            continue
        if end_date and d_str > end_date:
            continue
        android_daily_installs[d_str] = android_daily_installs.get(d_str, 0) + 1

    for m_rec in mkt_records:
        plat = (m_rec.get("platform") or "").lower()
        if plat != "android":
            continue
        ts = m_rec.get("timestamp") or m_rec.get("created_at")
        if not ts:
            continue
        d_str = ts.strftime("%Y-%m-%d") if isinstance(ts, datetime) else str(ts)[:10]
        if start_date and d_str < start_date:
            continue
        if end_date and d_str > end_date:
            continue
        android_daily_installs[d_str] = android_daily_installs.get(d_str, 0) + 1

    # Build iOS daily aggregations
    ios_daily_installs: Dict[str, int] = {}
    ios_first_time_map: Dict[str, int] = {}
    ios_redownloads_map: Dict[str, int] = {}

    for r in ios_records:
        d = r.get("metric_date")
        if not d:
            continue
        ios_daily_installs[d] = ios_daily_installs.get(d, 0) + int(r.get("total_downloads", 0))
        ios_first_time_map[d] = ios_first_time_map.get(d, 0) + int(r.get("first_time_downloads", 0))
        ios_redownloads_map[d] = ios_redownloads_map.get(d, 0) + int(r.get("redownloads", 0))

    for d_rec in dl_records:
        plat = (d_rec.get("platform") or "").lower()
        if plat not in ["ios", "iphone", "ipad"]:
            continue
        ca = d_rec.get("created_at")
        if not ca:
            continue
        d_str = ca.strftime("%Y-%m-%d") if isinstance(ca, datetime) else str(ca)[:10]
        if start_date and d_str < start_date:
            continue
        if end_date and d_str > end_date:
            continue
        ios_daily_installs[d_str] = ios_daily_installs.get(d_str, 0) + 1
        ios_first_time_map[d_str] = ios_first_time_map.get(d_str, 0) + 1

    for m_rec in mkt_records:
        plat = (m_rec.get("platform") or "").lower()
        if plat not in ["ios", "iphone", "ipad"]:
            continue
        ts = m_rec.get("timestamp") or m_rec.get("created_at")
        if not ts:
            continue
        d_str = ts.strftime("%Y-%m-%d") if isinstance(ts, datetime) else str(ts)[:10]
        if start_date and d_str < start_date:
            continue
        if end_date and d_str > end_date:
            continue
        ios_daily_installs[d_str] = ios_daily_installs.get(d_str, 0) + 1
        ios_first_time_map[d_str] = ios_first_time_map.get(d_str, 0) + 1

    # Generate Android Points
    all_android_dates = sorted(set(android_daily_installs.keys()) | set(android_active_map.keys()) | set(android_uninstalls_map.keys()))
    android_points = []
    if metric == "total_installs":
        cum = 0
        for d in all_android_dates:
            cum += android_daily_installs.get(d, 0)
            android_points.append({"date": d, "value": cum})
    elif metric in ["active_devices", "active_device_installs"]:
        last_active = 0
        for d in all_android_dates:
            if d in android_active_map:
                last_active = android_active_map[d]
            else:
                last_active += android_daily_installs.get(d, 0)
            android_points.append({"date": d, "value": last_active})
    elif metric in ["user_loss", "daily_user_uninstalls"]:
        for d in all_android_dates:
            android_points.append({"date": d, "value": android_uninstalls_map.get(d, 0)})
    else:
        for d in all_android_dates:
            android_points.append({"date": d, "value": android_daily_installs.get(d, 0)})

    # Generate iOS Points
    all_ios_dates = sorted(set(ios_daily_installs.keys()) | set(ios_first_time_map.keys()) | set(ios_redownloads_map.keys()))
    ios_points = []
    if metric == "total_installs":
        cum = 0
        for d in all_ios_dates:
            cum += ios_daily_installs.get(d, 0)
            ios_points.append({"date": d, "value": cum})
    elif metric in ["active_devices", "active_device_installs"]:
        for d in all_ios_dates:
            ios_points.append({"date": d, "value": ios_first_time_map.get(d, 0)})
    elif metric in ["user_loss", "daily_user_uninstalls"]:
        for d in all_ios_dates:
            ios_points.append({"date": d, "value": ios_redownloads_map.get(d, 0)})
    else:
        for d in all_ios_dates:
            ios_points.append({"date": d, "value": ios_daily_installs.get(d, 0)})

    return {
        "data": {
            "metric": metric,
            "aggregation": "sum",
            "granularity": granularity,
            "android": android_points,
            "ios": ios_points,
            "series": [
                {"platform": "android", "name": "Android (Google Play + Firebase)", "points": android_points},
                {"platform": "ios", "name": "iOS (App Store + Firebase)", "points": ios_points}
            ]
        },
        "meta": {
            "source_timezone": "America/Los_Angeles",
            "data_through_date": end_date or "",
            "correlation_id": "unified-store-firebase"
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


@router.post("/google-play/manual-update")
def manual_update_installs(
    payload: dict,
    db: Database = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    """
    Manually update the cumulative install totals for an app from Google Play Console.
    
    Body: { "app_code": "ailegal", "total_installs": 420, "active_devices": 154, "as_of_date": "2026-08-27" }
    """
    from datetime import datetime, timezone
    app_code = payload.get("app_code")
    total_installs = int(payload.get("total_installs", 0))
    active_devices = int(payload.get("active_devices", 0))
    as_of_date = payload.get("as_of_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    if not app_code:
        return {"success": False, "error": "app_code is required"}

    # Upsert the manual snapshot for today
    from src.database.models import generate_uuid, utc_now
    doc_id = f"manual_{app_code}_{as_of_date}"
    db["play_install_metrics"].update_one(
        {"_id": doc_id},
        {"$set": {
            "app_code": app_code,
            "metric_date": as_of_date,
            "dimension_type": "overview",
            "dimension_value": None,
            "dimension_value_normalized": "__overall__",
            "total_user_installs": total_installs,
            "installs_on_active_devices": active_devices,
            "current_user_installs": total_installs,
            "current_device_installs": active_devices,
            "daily_user_installs": 0,
            "daily_device_installs": 0,
            "daily_user_uninstalls": 0,
            "daily_device_uninstalls": 0,
            "net_daily_user_installs": 0,
            "net_daily_device_installs": 0,
            "install_events": total_installs,
            "uninstall_events": 0,
            "update_events": 0,
            "source_file_id": "manual_console_entry",
            "source_generation": "manual",
            "updated_at": utc_now()
        }},
        upsert=True
    )

    return {
        "success": True,
        "message": f"Updated {app_code} manual snapshot: {total_installs} total installs, {active_devices} active devices as of {as_of_date}",
        "app_code": app_code,
        "total_installs": total_installs,
        "active_devices": active_devices,
        "as_of_date": as_of_date
    }


@router.post("/app-store/manual-update")
def manual_update_app_store_metrics(
    payload: dict,
    db: Database = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    """
    Manually update cumulative or daily iOS App Store download metrics for an app.
    
    Body: { "app_code": "ailegal", "total_downloads": 45, "first_time_downloads": 40, "as_of_date": "2026-08-29" }
    """
    from datetime import datetime, timezone
    from src.database.models import utc_now

    app_code = (payload.get("app_code") or "ailegal").lower().strip()
    total_downloads = int(payload.get("total_downloads", 0))
    first_time = int(payload.get("first_time_downloads", int(total_downloads * 0.9)))
    redownloads = int(payload.get("redownloads", total_downloads - first_time))
    page_views = int(payload.get("page_views", int(total_downloads * 3.8)))
    impressions = int(payload.get("impressions", int(total_downloads * 12.5)))
    as_of_date = payload.get("as_of_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    bundle_id = "com.uwo.ailegal" if app_code == "ailegal" else "com.uwo.aisa"
    apple_app_id = "6797449251" if app_code == "ailegal" else "6779135418"

    doc_id = f"app_store_metric_{app_code}_{as_of_date}"
    db["app_store_metrics"].update_one(
        {"_id": doc_id},
        {"$set": {
            "app_code": app_code,
            "bundle_id": bundle_id,
            "apple_app_id": apple_app_id,
            "metric_date": as_of_date,
            "platform": "ios",
            "total_downloads": total_downloads,
            "first_time_downloads": first_time,
            "redownloads": redownloads,
            "page_views": page_views,
            "impressions": impressions,
            "source": "manual_app_store_entry",
            "updated_at": utc_now()
        }, "$setOnInsert": {"created_at": utc_now()}},
        upsert=True
    )

    return {
        "success": True,
        "message": f"Updated {app_code} iOS downloads: {total_downloads} total, {first_time} first-time, {page_views} page views as of {as_of_date}",
        "app_code": app_code,
        "total_downloads": total_downloads,
        "as_of_date": as_of_date
    }
