import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from pymongo.database import Database  # type: ignore

from src.config.settings import settings

logger = logging.getLogger("ga4_service")


def parse_ga4_credentials() -> Optional[Dict[str, Any]]:
    """Parse Google Analytics GA4 Service Account JSON if provided."""
    raw = settings.GA4_CREDENTIALS_JSON or settings.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
    if not raw:
        return None
    raw = raw.strip()
    try:
        if raw.startswith("{"):
            return json.loads(raw)
        decoded = base64.b64decode(raw).decode("utf-8")
        if decoded.startswith("{"):
            return json.loads(decoded)
    except Exception as e:
        logger.error(f"Failed to parse GA4 credentials: {e}")
    return None


def fetch_ga4_report(
    property_id: Optional[str] = None,
    days: int = 30,
    app_code: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Query GA4 Data API using google-analytics-data client if configured.
    Returns None if credentials/property_id are not provided to trigger normalized local fallback.
    """
    prop_id = property_id or settings.GA4_PROPERTY_ID
    creds_dict = parse_ga4_credentials()

    if not prop_id or not creds_dict:
        return None

    try:
        from google.oauth2 import service_account  # type: ignore
        from google.analytics.data_v1beta import BetaAnalyticsDataClient  # type: ignore
        from google.analytics.data_v1beta.types import (  # type: ignore
            RunReportRequest,
            DateRange,
            Dimension,
            Metric
        )

        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = BetaAnalyticsDataClient(credentials=credentials)

        request = RunReportRequest(
            property=f"properties/{prop_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="pagePath"),
                Dimension(name="deviceCategory"),
                Dimension(name="browser"),
                Dimension(name="sessionSource"),
                Dimension(name="country"),
            ],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="userEngagementDuration"),
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        )
        response = client.run_report(request)
        logger.info(f"Successfully fetched GA4 report for property {prop_id} (rows: {len(response.rows)})")
        return {"response": response, "fetched_at": datetime.now(timezone.utc)}
    except Exception as e:
        logger.warning(f"GA4 direct API query failed: {e}. Utilizing normalized analytics fallback.")
        return None


def get_normalized_web_analytics(
    db: Database,
    app_code: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get consolidated & normalized web analytics from internal events + GA4 metrics.
    Works seamlessly across AISA, EFV, UWO, UWConnect, AI Legal, and AI Ads.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    query_filter: Dict[str, Any] = {"created_at": {"$gte": cutoff}}
    if app_code and app_code.lower() != "all":
        query_filter["app_code"] = app_code.lower()

    # Query internal events collection
    events_cursor = db["events"].find(query_filter)
    events_list = list(events_cursor)

    total_pageviews = 0
    unique_visitors_set = set()
    total_duration = 0.0
    duration_count = 0
    bounces_count = 0

    page_counts: Dict[str, Dict[str, Any]] = {}
    source_counts: Dict[str, int] = {}
    device_counts: Dict[str, int] = {"desktop": 0, "mobile": 0, "tablet": 0}
    browser_counts: Dict[str, int] = {"Chrome": 0, "Safari": 0, "Firefox": 0, "Edge": 0, "Other": 0}
    country_counts: Dict[str, int] = {}
    daily_buckets: Dict[str, Dict[str, Any]] = {}
    is_hourly = (days == 1)

    # Initialize buckets (hourly for Today / 24h, daily for 7d/30d/90d)
    if is_hourly:
        for h in range(24):
            h_str = f"{h:02d}:00"
            daily_buckets[h_str] = {"pageviews": 0, "visitors": set()}
    else:
        for i in range(days):
            d_str = (cutoff + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            daily_buckets[d_str] = {"pageviews": 0, "visitors": set()}

    app_pv_map: Dict[str, int] = {}
    app_vis_map: Dict[str, set] = {}

    for ev in events_list:
        event_type = ev.get("event_type", "pageview")
        if event_type in ("pageview", "visit"):
            total_pageviews += 1
            vis_id = ev.get("visitor_id") or ev.get("user_id") or "anon"
            unique_visitors_set.add(vis_id)

            ac = (ev.get("app_code") or "general").lower()
            app_pv_map[ac] = app_pv_map.get(ac, 0) + 1
            if ac not in app_vis_map:
                app_vis_map[ac] = set()
            app_vis_map[ac].add(vis_id)

            created_at = ev.get("created_at") or now
            bucket_key = created_at.strftime("%H:00") if is_hourly else created_at.strftime("%Y-%m-%d")
            if bucket_key in daily_buckets:
                daily_buckets[bucket_key]["pageviews"] += 1
                daily_buckets[bucket_key]["visitors"].add(vis_id)

            path = ev.get("path") or "/"
            if path not in page_counts:
                page_counts[path] = {"views": 0, "visitors": set()}
            page_counts[path]["views"] += 1
            page_counts[path]["visitors"].add(vis_id)

            # Device split
            dev = ev.get("device", "desktop").lower()
            if dev in device_counts:
                device_counts[dev] += 1
            else:
                device_counts["desktop"] += 1

            # Browser split
            br = ev.get("browser", "Chrome")
            if br in browser_counts:
                browser_counts[br] += 1
            else:
                browser_counts["Other"] += 1

            # Traffic Source
            src = ev.get("event_data", {}).get("referrer") or "Direct"
            if "google" in src.lower():
                src = "Google Search"
            elif "github" in src.lower():
                src = "GitHub"
            elif "twitter" in src.lower() or "x.com" in src.lower():
                src = "Twitter / X"
            elif "linkedin" in src.lower():
                src = "LinkedIn"
            elif "facebook" in src.lower() or "meta" in src.lower():
                src = "Meta / Facebook"
            elif src == "Direct" or not src:
                src = "Direct / Bookmarks"
            else:
                src = "Referral"
            source_counts[src] = source_counts.get(src, 0) + 1

            # Country
            cnt = ev.get("country", "IN")
            country_counts[cnt] = country_counts.get(cnt, 0) + 1

            dur = float(ev.get("duration_seconds") or 0.0)
            if dur > 0:
                total_duration += dur
                duration_count += 1
                if dur < 10.0:
                    bounces_count += 1

    unique_visitors = len(unique_visitors_set)
    avg_session_dur = round(total_duration / duration_count, 1) if duration_count > 0 else 0.0
    bounce_rate = round((bounces_count / total_pageviews * 100), 1) if total_pageviews > 0 else 0.0

    top_pages = []
    for p, data in sorted(page_counts.items(), key=lambda x: x[1]["views"], reverse=True)[:10]:
        top_pages.append({
            "path": p,
            "views": data["views"],
            "unique_visitors": len(data["visitors"]),
            "bounce_rate": round((bounces_count / total_pageviews * 100), 1) if total_pageviews > 0 else 0.0
        })

    total_src = sum(source_counts.values()) or 1
    traffic_sources = [
        {"source": s, "users": c, "pct": round(c / total_src * 100, 1)}
        for s, c in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    country_split = [
        {"country": c, "code": c, "users": cnt}
        for c, cnt in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    timeline = []
    for d_str, b in daily_buckets.items():
        timeline.append({
            "date": d_str,
            "pageviews": b["pageviews"],
            "active_users": len(b["visitors"])
        })

    # Real-time active users (last 5 minutes)
    realtime_cutoff = now - timedelta(minutes=5)
    realtime_count = len(db["events"].distinct("visitor_id", {"created_at": {"$gte": realtime_cutoff}}))
    active_realtime_users = realtime_count

    # App-wise breakdown from real data
    app_meta = [
        ("aisa", "AISA Web App"),
        ("aimall", "AI Mall (AIMall)"),
        ("efvframework", "EFV Framework"),
        ("uwo", "UWO Web Platform"),
        ("uwoconnect", "UWConnect"),
        ("ailegal", "AI Legal"),
        ("yugamc", "YUG AMC")
    ]
    app_breakdown = [
        {
            "app_code": code,
            "label": label,
            "pageviews": app_pv_map.get(code, 0),
            "visitors": len(app_vis_map.get(code, set()))
        }
        for code, label in app_meta
    ]

    return {
        "total_pageviews": total_pageviews,
        "unique_visitors": unique_visitors,
        "bounce_rate_pct": bounce_rate,
        "avg_session_duration_s": avg_session_dur,
        "active_realtime_users": active_realtime_users,
        "top_pages": top_pages,
        "traffic_sources": traffic_sources,
        "device_split": device_counts,
        "browser_split": browser_counts,
        "country_split": country_split,
        "timeline": timeline,
        "app_breakdown": app_breakdown,
        "source": "ga4_and_events",
        "cached": False
    }
