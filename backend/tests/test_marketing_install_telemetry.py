import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from src.main import app
from src.marketing.service import MarketingService
from src.marketing.models import MarketingLinkCreate, InstallTelemetryCreate


@pytest.fixture
def client():
    return TestClient(app)


def test_marketing_link_initialization():
    """Verify that newly created marketing links initialize download counters to 0."""
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="instagram",
        campaign_name="test_campaign",
        post_name="test_post_init",
        channel_type="referral"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000", creator="TestAdmin")
    assert link["total_clicks"] == 0
    assert link["unique_clicks"] == 0
    assert link["total_downloads"] == 0
    assert link["android_downloads"] == 0
    assert link["ios_downloads"] == 0
    assert link["unique_installs"] == 0
    assert isinstance(link["unique_devices"], list)


def test_android_install_referrer_attribution(client):
    """Verify that Android Play Store install referrer attributes to the correct link."""
    # 1. Create link
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="youtube",
        campaign_name="android_test_camp",
        post_name="android_reel",
        channel_type="referral"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    # 2. Simulate raw Android Google Play install referrer with URL-encoding
    raw_referrer = f"utm_source%3Dyoutube%26utm_campaign%3Dandroid_test_camp%26slug%3D{slug}%26ref%3D{slug}"
    payload = {
        "product_id": "aisa",
        "install_referrer": raw_referrer,
        "platform": "android",
        "device_id": "device_pixel_8_android",
        "version": "1.2.0",
        "ip": "103.21.244.1"
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "install_referrer"
    assert data["platform"] == "android"
    assert data["total_downloads"] >= 1
    assert data["android_downloads"] >= 1


def test_ios_ip_matching_attribution(client):
    """Verify that iOS installations attribute via probabilistic IP matching."""
    # 1. Create iOS App Store link
    data = MarketingLinkCreate(
        product_id="ailegal",
        platform="instagram",
        campaign_name="ios_launch",
        post_name="ios_story_1",
        custom_target_url="https://apps.apple.com/app/id6797449251"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    # 2. Simulate click from iOS device IP
    test_ip = "182.74.120.45"
    MarketingService.record_click(
        slug=slug,
        ip=test_ip,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
        referrer="https://instagram.com"
    )

    # 3. Simulate first launch of iOS app from same IP without slug
    payload = {
        "product_id": "ailegal",
        "platform": "ios",
        "device_id": "idfv_ios_iphone_15",
        "version": "1.0.0",
        "ip": test_ip
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "ip_match"
    assert data["platform"] == "ios"
    assert data["ios_downloads"] >= 1


def test_direct_referral_code_attribution(client):
    """Verify that passing referral_code or ref_code directly attributes to the link."""
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="whatsapp",
        campaign_name="wa_share",
        post_name="wa_chat"
    )
    link = MarketingService.create_link(data)
    slug = link["slug"]

    payload = {
        "referral_code": slug,
        "platform": "android",
        "device_id": "dev_samsung_s24",
        "version": "1.0.0"
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "direct"


def test_legacy_link_safe_integer_update():
    """Ensure that links with missing or null numeric fields never crash on install."""
    db = MarketingService._sanitize_slug
    from src.marketing.service import _get_db
    db = _get_db()

    # Insert a dummy link with None values
    slug = f"legacy-test-{datetime.now(timezone.utc).timestamp()}"
    link_id = db.marketing_links.insert_one({
        "slug": slug,
        "product_id": "aisa",
        "platform": "other",
        "campaign_name": "legacy",
        "post_name": "legacy_post",
        "total_downloads": None,
        "android_downloads": None,
        "ios_downloads": None,
        "unique_installs": None,
        "unique_devices": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }).inserted_id

    # Record install on this link — should NOT throw MongoDB WriteError
    res = MarketingService.record_install(
        slug=slug,
        platform="android",
        device_id="legacy_dev_1"
    )

    assert res["success"] is True
    assert res["attributed"] is True
    assert res["total_downloads"] == 1
    assert res["android_downloads"] == 1

    # Cleanup test doc
    db.marketing_links.delete_one({"_id": link_id})
    db.marketing_installs.delete_many({"slug": slug})
