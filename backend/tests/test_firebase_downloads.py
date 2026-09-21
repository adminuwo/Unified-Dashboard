import pytest  # type: ignore
from datetime import datetime, timezone


def test_firebase_event_ingestion(client):
    # Post first_open install event from mobile app
    payload = {
        "event_name": "first_open",
        "app_code": "aisa",
        "platform": "android",
        "device_id": "test_device_firebase_001",
        "version": "1.0.4",
        "metadata": {"network": "wifi", "campaign": "launch"}
    }
    res = client.post("/api/telemetry/firebase-event", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["event_name"] == "first_open"
    assert data["app_code"] == "aisa"
    assert data["platform"] == "android"
    assert data["is_new_install"] is True

    # Post duplicate event with same device_id - verify deduplication
    res2 = client.post("/api/telemetry/firebase-event", json=payload)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["is_new_install"] is False


def test_firebase_install_alias(client):
    payload = {
        "app_code": "ailegal",
        "platform": "ios",
        "device_id": "test_device_ios_002",
        "version": "2.0.0"
    }
    res = client.post("/api/telemetry/firebase/install", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["event_name"] == "first_open"
    assert data["platform"] == "ios"
    assert data["is_new_install"] is True


def test_direct_download_telemetry_without_app_key(client):
    payload = {
        "platform": "android",
        "app_code": "aisa",
        "version": "1.0.5",
        "device_id": "test_device_direct_003"
    }
    res = client.post("/api/telemetry/download", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["platform"] == "android"
    assert data["app_code"] == "aisa"


def test_analytics_overview_blends_firebase_downloads(client, admin_headers):
    # Ingest 2 Firebase downloads: 1 Android (AISA) and 1 iOS (AI Legal)
    client.post("/api/telemetry/firebase-event", json={
        "event_name": "first_open",
        "app_code": "aisa",
        "platform": "android",
        "device_id": "aisa_android_dev_01"
    })
    client.post("/api/telemetry/firebase-event", json={
        "event_name": "first_open",
        "app_code": "ailegal",
        "platform": "ios",
        "device_id": "ailegal_ios_dev_02"
    })

    # Query overview endpoint
    res = client.get("/api/admin/analytics/google-play/overview?app_codes=aisa,ailegal", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Verify provider and telemetry source metadata
    assert "firebase" in data["source"]["provider"]
    assert "Firebase Mobile SDK" in data["source"]["telemetry_sources"]

    # Verify combined stats reflect the Firebase downloads
    assert data["combined"]["firebase_downloads"] >= 2
    assert data["combined"]["firebase_android"] >= 1
    assert data["combined"]["firebase_ios"] >= 1
    assert data["combined"]["total_user_installs_latest"] >= 1
    assert data["combined"]["ios_total_downloads"] >= 1


def test_analytics_timeseries_blends_firebase_downloads(client, admin_headers):
    # Ingest downloads
    client.post("/api/telemetry/firebase-event", json={
        "event_name": "first_open",
        "app_code": "aisa",
        "platform": "android",
        "device_id": "aisa_ts_dev_01"
    })
    client.post("/api/telemetry/firebase-event", json={
        "event_name": "first_open",
        "app_code": "aisa",
        "platform": "ios",
        "device_id": "aisa_ts_dev_02"
    })

    # Test total_installs timeseries
    res_installs = client.get(
        "/api/admin/analytics/google-play/timeseries?app_codes=aisa&metric=total_installs",
        headers=admin_headers
    )
    assert res_installs.status_code == 200
    ts_installs = res_installs.json()["data"]
    assert len(ts_installs["android"]) >= 1
    assert len(ts_installs["ios"]) >= 1

    # Test active_devices timeseries
    res_active = client.get(
        "/api/admin/analytics/google-play/timeseries?app_codes=aisa&metric=active_devices",
        headers=admin_headers
    )
    assert res_active.status_code == 200
    ts_active = res_active.json()["data"]
    assert len(ts_active["android"]) >= 1

    # Test user_loss timeseries
    res_loss = client.get(
        "/api/admin/analytics/google-play/timeseries?app_codes=aisa&metric=user_loss",
        headers=admin_headers
    )
    assert res_loss.status_code == 200
    ts_loss = res_loss.json()["data"]
    assert len(ts_loss["android"]) >= 1
