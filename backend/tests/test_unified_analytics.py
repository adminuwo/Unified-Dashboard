import pytest
from fastapi.testclient import TestClient


def test_collect_web_event(client: TestClient):
    payload = {
        "app_code": "aisa",
        "event_type": "pageview",
        "path": "/chat",
        "visitor_id": "test_vis_123",
        "session_id": "test_ses_456",
        "device": "desktop",
        "browser": "Chrome",
        "country": "IN",
        "duration_seconds": 45.2
    }
    res = client.post("/api/web-stats/collect", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "recorded"
    assert "id" in data


def test_tracker_script(client: TestClient):
    res = client.get("/api/web-stats/tracker.js")
    assert res.status_code == 200
    assert "unifiedTrack" in res.text
    assert "application/javascript" in res.headers["content-type"]


def test_unified_analytics_overview(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/overview?days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_web_pageviews" in data
    assert "total_mobile_installs" in data
    assert "total_revenue" in data
    assert "platform_breakdown" in data
    assert "sync_status" in data


def test_unified_analytics_web(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/web?app_code=aisa&days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_pageviews" in data
    assert "unique_visitors" in data
    assert "device_split" in data
    assert "browser_split" in data
    assert "top_pages" in data
    assert "traffic_sources" in data


def test_unified_analytics_mobile(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/mobile?project=AISA&days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_android_installs" in data
    assert "total_ios_units" in data
    assert "android_timeline" in data


def test_unified_analytics_backend_monitoring(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/backend-monitoring?hours=24", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_api_requests" in data
    assert "avg_latency_ms" in data
    assert "error_5xx_rate" in data
    assert "timeline" in data


def test_unified_analytics_user_activity(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/user-activity?days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "feature_usage" in data
    assert "ai_token_usage" in data


def test_unified_analytics_revenue(client: TestClient, admin_headers: dict):
    res = client.get("/api/admin/unified-analytics/revenue?days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_revenue" in data
    assert "plan_distribution" in data
    assert "timeline" in data


def test_unified_analytics_sync(client: TestClient, admin_headers: dict):
    res = client.post("/api/admin/unified-analytics/sync?provider=all", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["provider"] == "all"
