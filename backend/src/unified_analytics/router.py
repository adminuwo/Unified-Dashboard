from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Response, Request
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import EventLog
from src.admin.router import get_current_admin
from src.unified_analytics.schemas import (
    PlatformOverviewResponse,
    WebAnalyticsResponse,
    MobileAnalyticsResponse,
    GcpMonitoringResponse,
    UserActivityResponse,
    RevenueBreakdownResponse,
    SyncStatusResponse,
    EventCollectRequest
)
from src.unified_analytics import aggregator_service

router = APIRouter(tags=["Unified Analytics & Intelligence Platform (Phase 3)"])


# ─── Public Tracking & Collector Endpoints ────────────────────────────────────

@router.post("/web-stats/collect", status_code=status.HTTP_201_CREATED)
@router.post("/events/collect", status_code=status.HTTP_201_CREATED)
def collect_web_event(
    data: EventCollectRequest,
    request: Request,
    db: Database = Depends(get_db)
):
    """
    Public non-blocking collector endpoint for web & mobile client events.
    Captures pageviews, route transitions, durations, and custom events.
    """
    # Extract client country or fallback from headers
    country = request.headers.get("CF-IPCountry") or data.country or "IN"
    user_agent = request.headers.get("user-agent", "")

    # Basic device & browser detection if not provided
    device = data.device or ("mobile" if "mobile" in user_agent.lower() else "desktop")
    browser = data.browser or ("Chrome" if "chrome" in user_agent.lower() else "Safari" if "safari" in user_agent.lower() else "Firefox" if "firefox" in user_agent.lower() else "Other")

    event_dict = EventLog.create_dict(
        app_code=data.app_code,
        event_type=data.event_type,
        path=data.path,
        visitor_id=data.visitor_id,
        session_id=data.session_id,
        device=device,
        browser=browser,
        os_name=data.os_name or "other",
        country=country,
        event_name=data.event_name,
        event_data=data.event_data,
        duration_seconds=data.duration_seconds
    )
    db["events"].insert_one(event_dict)
    return {"status": "recorded", "id": event_dict["_id"]}


@router.get("/web-stats/tracker.js")
def get_tracker_script():
    """
    Serves the ultra-lightweight (~1.5 KB) client JavaScript auto-tracker.
    Automatically intercepts SPA route changes, page durations, and sends beacons.
    """
    script_content = """
(function(){
  'use strict';
  var script = document.currentScript || document.querySelector('script[data-site]');
  var site = (script && script.getAttribute('data-site')) || 'general';
  var endpoint = (script && script.getAttribute('data-endpoint')) || window.location.origin + '/api/web-stats/collect';
  var visitorId = localStorage.getItem('_unf_vis') || (function(){
    var id = 'v_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem('_unf_vis', id);
    return id;
  })();
  var sessionId = sessionStorage.getItem('_unf_ses') || (function(){
    var id = 's_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    sessionStorage.setItem('_unf_ses', id);
    return id;
  })();
  var startTime = Date.now();

  function getDevice(){
    var ua = navigator.userAgent;
    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) return 'tablet';
    if (/Mobile|iP(hone|od)|Android|BlackBerry|IEMobile|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/i.test(ua)) return 'mobile';
    return 'desktop';
  }

  function getBrowser(){
    var ua = navigator.userAgent;
    if (ua.indexOf('Firefox') > -1) return 'Firefox';
    if (ua.indexOf('SamsungBrowser') > -1) return 'Samsung';
    if (ua.indexOf('Opera') > -1 || ua.indexOf('OPR') > -1) return 'Opera';
    if (ua.indexOf('Edge') > -1 || ua.indexOf('Edg') > -1) return 'Edge';
    if (ua.indexOf('Chrome') > -1) return 'Chrome';
    if (ua.indexOf('Safari') > -1) return 'Safari';
    return 'Other';
  }

  function send(type, extra, duration){
    var payload = JSON.stringify({
      app_code: site,
      event_type: type || 'pageview',
      path: window.location.pathname || '/',
      visitor_id: visitorId,
      session_id: sessionId,
      device: getDevice(),
      browser: getBrowser(),
      os_name: navigator.platform || 'other',
      duration_seconds: duration || 0.0,
      event_data: Object.assign({
        title: document.title,
        referrer: document.referrer || '',
        screen: window.screen.width + 'x' + window.screen.height
      }, extra || {})
    });
    if (navigator.sendBeacon) {
      navigator.sendBeacon(endpoint, new Blob([payload], {type: 'application/json'}));
    } else {
      fetch(endpoint, {method: 'POST', body: payload, headers: {'Content-Type': 'application/json'}, keepalive: true}).catch(function(){});
    }
  }

  // Initial pageview
  send('pageview');

  // SPA Route Change Listener
  var pushState = history.pushState;
  if (pushState) {
    history.pushState = function(){
      var dur = (Date.now() - startTime) / 1000;
      send('duration', {}, dur);
      startTime = Date.now();
      var ret = pushState.apply(this, arguments);
      send('pageview');
      return ret;
    };
  }
  window.addEventListener('popstate', function(){
    send('pageview');
  });

  // Page Exit Duration
  window.addEventListener('beforeunload', function(){
    var dur = (Date.now() - startTime) / 1000;
    send('duration', {}, dur);
  });

  // Global helper for custom event tracking
  window.unifiedTrack = function(eventName, eventData){
    send('custom_event', Object.assign({event_name: eventName}, eventData || {}));
  };
})();
    """.strip()
    return Response(content=script_content, media_type="application/javascript")


# ─── Admin Unified Analytics Endpoints (Phase 3) ──────────────────────────────

@router.get("/admin/unified-analytics/overview", response_model=PlatformOverviewResponse)
def get_unified_overview(
    app_code: Optional[str] = Query(None, description="Filter by app code: aisa, efvframework, uwo, uwoconnect, ailegal, aiads, or all"),
    days: int = Query(30, description="Date range in days (e.g. 7, 30, 90)"),
    force_refresh: bool = Query(False, description="Bypass cache and force recalculate"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch Consolidated Executive Overview metrics across Web, Mobile, Revenue, and GCP Health."""
    return aggregator_service.get_unified_overview(
        db=db,
        app_code=app_code,
        days=days,
        force_refresh=force_refresh
    )


@router.get("/admin/unified-analytics/web", response_model=WebAnalyticsResponse)
def get_web_analytics(
    app_code: Optional[str] = Query(None, description="Filter by app code"),
    days: int = Query(30, description="Date range in days"),
    force_refresh: bool = Query(False),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch GA4 & Web Analytics (pageviews, visitors, bounce rate, top pages, traffic sources)."""
    return aggregator_service.get_web_analytics(
        db=db,
        app_code=app_code,
        days=days,
        force_refresh=force_refresh
    )


@router.get("/admin/unified-analytics/mobile", response_model=MobileAnalyticsResponse)
def get_mobile_analytics(
    project: Optional[str] = Query(None, description="Filter by project: AISA, AI_LEGAL, ALL"),
    days: int = Query(30, description="Date range in days"),
    force_refresh: bool = Query(False),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch Mobile Analytics combining Google Play Store (Android) and Apple App Store Connect (iOS)."""
    return aggregator_service.get_mobile_analytics(
        db=db,
        project=project,
        days=days,
        force_refresh=force_refresh
    )


@router.get("/admin/unified-analytics/backend-monitoring", response_model=GcpMonitoringResponse)
def get_backend_monitoring(
    hours: int = Query(24, description="Hourly window for GCP telemetry"),
    force_refresh: bool = Query(False),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch GCP Cloud Monitoring & server latency, CPU/memory, and 5xx error metrics."""
    return aggregator_service.get_gcp_monitoring(
        db=db,
        hours=hours,
        force_refresh=force_refresh
    )


@router.get("/admin/unified-analytics/user-activity", response_model=UserActivityResponse)
def get_user_activity(
    app_code: Optional[str] = Query(None, description="Filter by app code"),
    days: int = Query(30, description="Date range in days"),
    force_refresh: bool = Query(False),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch behavioral analytics, mode/feature usage shares, and AI token consumption."""
    return aggregator_service.get_user_activity(
        db=db,
        app_code=app_code,
        days=days,
        force_refresh=force_refresh
    )


@router.get("/admin/unified-analytics/revenue", response_model=RevenueBreakdownResponse)
def get_revenue_breakdown(
    days: int = Query(30, description="Date range in days"),
    force_refresh: bool = Query(False),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Fetch revenue breakdown (₹ INR), transactions, subscription plans, and MRR."""
    return aggregator_service.get_revenue_breakdown(
        db=db,
        days=days,
        force_refresh=force_refresh
    )


@router.post("/admin/unified-analytics/sync", response_model=SyncStatusResponse)
def trigger_provider_sync(
    provider: str = Query("all", description="Provider to sync: all, ga4, play_store, app_store, gcp"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Manually trigger background sync across all external providers."""
    return aggregator_service.sync_all_providers(db)
