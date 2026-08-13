import pytest  # type: ignore
from src.database.models import PROJECT_MAPPINGS
from src.store_analytics.service import upsert_store_analytic_record, sync_google_play_data


def test_project_package_mapping():
    """Verify package name mapping for AISA and AI Legal apps."""
    assert "AISA" in PROJECT_MAPPINGS
    assert PROJECT_MAPPINGS["AISA"]["package_name"] == "com.uwo.aisa"
    assert PROJECT_MAPPINGS["AISA"]["platform"] == "android"

    assert "AI_LEGAL" in PROJECT_MAPPINGS
    assert PROJECT_MAPPINGS["AI_LEGAL"]["package_name"] == "com.uwo.ailegal"
    assert PROJECT_MAPPINGS["AI_LEGAL"]["platform"] == "android"


def test_idempotent_upsert_store_analytics(db_session):
    """Verify upserting same record multiple times does not produce duplicate records."""
    # First insert
    res1 = upsert_store_analytic_record(
        db=db_session,
        project="AISA",
        platform="android",
        package_name="com.uwo.aisa",
        date_str="2026-08-12",
        metric="installs",
        value=150,
        source="test_source"
    )
    assert res1 is True

    # Second upsert (update existing value)
    res2 = upsert_store_analytic_record(
        db=db_session,
        project="AISA",
        platform="android",
        package_name="com.uwo.aisa",
        date_str="2026-08-12",
        metric="installs",
        value=200,
        source="test_source"
    )
    assert res2 is True

    # Verify only 1 document exists in MongoDB
    docs = list(db_session["store_analytics"].find({
        "project": "AISA",
        "date": "2026-08-12",
        "metric": "installs"
    }))
    assert len(docs) == 1
    assert docs[0]["value"] == 200


def test_get_store_analytics_unauthorized(client):
    """Verify unauthorized request is rejected."""
    res = client.get("/api/admin/store-analytics")
    assert res.status_code == 401


def test_get_store_analytics_summary(client, admin_headers, db_session):
    """Verify fetching store analytics summary and project breakdown."""
    # Seed test analytics data
    upsert_store_analytic_record(db_session, "AISA", "android", "com.uwo.aisa", "2026-08-10", "installs", 100)
    upsert_store_analytic_record(db_session, "AI_LEGAL", "android", "com.uwo.ailegal", "2026-08-10", "installs", 250)

    res = client.get("/api/admin/store-analytics?date_range=30d", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_android_downloads"] >= 350
    assert len(data["projects"]) == 2

    # Check project breakdown
    aisa_proj = next(p for p in data["projects"] if p["project"] == "AISA")
    ai_legal_proj = next(p for p in data["projects"] if p["project"] == "AI_LEGAL")

    assert aisa_proj["package_name"] == "com.uwo.aisa"
    assert aisa_proj["total_downloads"] >= 100

    assert ai_legal_proj["package_name"] == "com.uwo.ailegal"
    assert ai_legal_proj["total_downloads"] >= 250


def test_manual_sync_trigger(client, admin_headers):
    """Verify manual sync trigger endpoint executes cleanly and returns status."""
    res = client.post("/api/admin/store-analytics/sync", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "records_inserted_or_updated" in data
    assert "synced_at" in data
