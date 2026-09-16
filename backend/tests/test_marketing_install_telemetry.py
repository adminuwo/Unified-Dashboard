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


def test_react_native_play_install_referrer_payload(client):
    """Verify that the exact payload format from react-native-play-install-referrer works flawlessly."""
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="instagram",
        campaign_name="rn_campaign",
        post_name="rn_reel"
    )
    link = MarketingService.create_link(data)
    slug = link["slug"]

    # Exact payload structure from react-native-play-install-referrer
    rn_payload = {
        "platform": "android",
        "installReferrer": f"utm_source=friend_promo&utm_content={slug}",
        "clickTimestamp": 1725883200,
        "installTimestamp": 1725883260
    }

    res = client.post("/api/marketing/telemetry/install", json=rn_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "install_referrer"
    assert data["android_downloads"] >= 1


def test_android_does_not_attribute_via_ip_match(client):
    """Verify that Android strictly requires Google Play Install Referrer and rejects IP matching."""
    # 1. Create Android link
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="youtube",
        campaign_name="android_strict_google_api",
        post_name="video_strict_test"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    # 2. Simulate click from device IP
    test_ip = "192.168.100.200"
    MarketingService.record_click(
        slug=slug,
        ip=test_ip,
        user_agent="Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0 Mobile",
        referrer="https://youtube.com"
    )

    # 3. Simulate first launch of Android app from same IP WITHOUT Google Play referrer token
    payload = {
        "product_id": "aisa",
        "platform": "android",
        "device_id": "device_no_referrer_token",
        "version": "1.0.0",
        "ip": test_ip
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Must NOT attribute to the link because Android only accepts Google Play Install Referrer API
    assert data["attributed"] is False
    assert data["slug"] == "unknown"
    assert data["attribution_method"] == "none"


def test_ios_ip_and_fingerprint_matching_attribution(client):
    """Verify that iOS installations attribute with high confidence when both IP and fingerprint match."""
    # 1. Create iOS link
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="instagram",
        campaign_name="ios_fp_campaign",
        post_name="ios_fp_story",
        custom_target_url="https://apps.apple.com/app/id6779135418"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    test_ip = "49.37.112.55"
    test_fp = "fp_ios_iphone_15_pro_abc123"

    # 2. Simulate click passing fingerprint and IP
    MarketingService.record_click(
        slug=slug,
        ip=test_ip,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
        referrer="https://instagram.com",
        fingerprint=test_fp
    )

    # 3. Simulate first launch of iOS app with both matching IP and fingerprint
    payload = {
        "product_id": "aisa",
        "platform": "ios",
        "device_id": "ios_device_uuid_999",
        "fingerprint": test_fp,
        "version": "1.0.8",
        "ip": test_ip
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "ip_fingerprint_match"
    assert data["platform"] == "ios"
    assert data["fingerprint"] == test_fp
    assert data["ios_downloads"] >= 1


def test_ios_fingerprint_only_matching_attribution(client):
    """Verify that iOS installations attribute when user rotates network (IP changes) but device fingerprint matches."""
    data = MarketingLinkCreate(
        product_id="ailegal",
        platform="twitter",
        campaign_name="ios_network_hop_test",
        post_name="ios_tweet_link",
        custom_target_url="https://apps.apple.com/app/id6797449251"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    click_ip = "122.161.45.10"       # Cellular IP on click
    install_ip = "106.213.88.99"     # Home Wi-Fi IP on install
    device_fp = "fp_ios_ipad_air_m2_xyz789"

    # 1. Click on cellular
    MarketingService.record_click(
        slug=slug,
        ip=click_ip,
        user_agent="Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
        referrer="https://t.co",
        fingerprint=device_fp
    )

    # 2. Install / launch on home Wi-Fi with same device fingerprint
    payload = {
        "product_id": "ailegal",
        "platform": "ios",
        "device_id": "ipad_device_uuid_888",
        "fingerprint": device_fp,
        "version": "1.0.11",
        "ip": install_ip
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["attributed"] is True
    assert data["slug"] == slug
    assert data["attribution_method"] == "fingerprint_match"
    assert data["platform"] == "ios"
    assert data["ios_downloads"] >= 1


def test_android_rejects_fingerprint_matching(client):
    """Verify that Android strictly rejects fingerprint matching and requires Google Play Install Referrer."""
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="linkedin",
        campaign_name="android_reject_fp",
        post_name="post_no_referrer"
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]

    test_ip = "115.98.220.10"
    test_fp = "fp_android_samsung_s24"

    # 1. Click
    MarketingService.record_click(
        slug=slug,
        ip=test_ip,
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B)",
        referrer="https://linkedin.com",
        fingerprint=test_fp
    )

    # 2. Launch with matching fingerprint and IP on Android without Google Play referrer token
    payload = {
        "product_id": "aisa",
        "platform": "android",
        "device_id": "android_dev_999",
        "fingerprint": test_fp,
        "version": "1.0.0",
        "ip": test_ip
    }

    res = client.post("/api/marketing/telemetry/install", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Android MUST be rejected from probabilistic attribution
    assert data["attributed"] is False
    assert data["slug"] == "unknown"
    assert data["attribution_method"] == "none"


def test_reinstall_same_device_id_does_not_increment_downloads(client):
    """Verify that reinstalling from the same device does NOT increment the download counter."""
    data = MarketingLinkCreate(
        product_id="ailegal",
        platform="instagram",
        campaign_name="reinstall_prevention_test",
        post_name="reinstall_post_1"
    )
    link = MarketingService.create_link(data)
    slug = link["slug"]

    # 1. First install
    payload1 = {
        "product_id": "ailegal",
        "slug": slug,
        "platform": "android",
        "device_id": "android_9876543210abcdef",
        "version": "1.0.12",
        "ip": "115.111.45.20",
        "install_referrer": f"utm_source=instagram&slug={slug}"
    }
    res1 = client.post("/api/marketing/telemetry/install", json=payload1)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["is_unique"] is True
    assert d1["is_reinstall"] is False
    assert d1["total_downloads"] == 1
    assert d1["android_downloads"] == 1

    # 2. Friend uninstalls and reinstalls through URL (same persistent Android ID)
    res2 = client.post("/api/marketing/telemetry/install", json=payload1)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["is_unique"] is False
    assert d2["is_reinstall"] is True
    # Download counter MUST NOT increment
    assert d2["total_downloads"] == 1
    assert d2["android_downloads"] == 1


def test_reinstall_after_uninstall_same_ip_and_slug_does_not_increment_downloads(client):
    """Verify that even if client device_id resets to a new ephemeral dev_ UUID upon reinstall,
    the backend heuristic detects matching IP + slug and prevents duplicate download counts."""
    data = MarketingLinkCreate(
        product_id="ailegal",
        platform="whatsapp",
        campaign_name="friend_referral",
        post_name="chat_link"
    )
    link = MarketingService.create_link(data)
    slug = link["slug"]
    friend_ip = "152.59.30.184"

    # 1. First install with ephemeral dev_ UUID
    payload1 = {
        "product_id": "ailegal",
        "slug": slug,
        "platform": "android",
        "device_id": "dev_pyvu3ndkx7_1789386802567",
        "version": "1.0.12",
        "ip": friend_ip,
        "install_referrer": f"utm_source=whatsapp&slug={slug}"
    }
    res1 = client.post("/api/marketing/telemetry/install", json=payload1)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["is_unique"] is True
    assert d1["total_downloads"] == 1

    # 2. Friend uninstalls, re-clicks link, reinstalls. App generates NEW ephemeral UUID
    payload2 = {
        "product_id": "ailegal",
        "slug": slug,
        "platform": "android",
        "device_id": "dev_g4aw3xd6ii8_1789386850468",  # brand new random ID
        "version": "1.0.12",
        "ip": friend_ip,  # same friend IP
        "install_referrer": f"utm_source=whatsapp&slug={slug}"
    }
    res2 = client.post("/api/marketing/telemetry/install", json=payload2)
    assert res2.status_code == 200
    d2 = res2.json()
    # MUST be detected as a reinstall
    assert d2["is_unique"] is False
    assert d2["is_reinstall"] is True
    assert d2["total_downloads"] == 1
    assert d2["android_downloads"] == 1


def test_distinct_devices_increment_download_counter(client):
    """Verify that distinct real devices increment the download counter properly."""
    data = MarketingLinkCreate(
        product_id="aisa",
        platform="youtube",
        campaign_name="multi_device_test",
        post_name="video_share"
    )
    link = MarketingService.create_link(data)
    slug = link["slug"]

    # User 1
    p1 = {
        "product_id": "aisa",
        "slug": slug,
        "platform": "android",
        "device_id": "android_device_user_1",
        "version": "1.0.0",
        "ip": "49.36.1.1",
        "install_referrer": f"utm_source=youtube&slug={slug}"
    }
    r1 = client.post("/api/marketing/telemetry/install", json=p1)
    assert r1.json()["total_downloads"] == 1

    # User 2 (different device)
    p2 = {
        "product_id": "aisa",
        "slug": slug,
        "platform": "android",
        "device_id": "android_device_user_2",
        "version": "1.0.0",
        "ip": "49.36.2.2",
        "install_referrer": f"utm_source=youtube&slug={slug}"
    }
    r2 = client.post("/api/marketing/telemetry/install", json=p2)
    assert r2.json()["total_downloads"] == 2
    assert r2.json()["is_unique"] is True


def test_smart_link_device_routing(client):
    """Verify that a single smart link routes Android to Play Store, iOS to App Store, and Desktop to Web."""
    # 1. Create Smart Link for AI Legal
    data = MarketingLinkCreate(
        product_id="ailegal",
        platform="instagram",
        campaign_name="smart_universal_campaign",
        post_name="smart_bio_link",
        is_smart_link=True,
    )
    link = MarketingService.create_link(data, base_request_url="http://localhost:8000")
    slug = link["slug"]
    assert link["is_smart_link"] is True

    # 2. Android Device Click (follow_redirects=False to inspect 302 Location header)
    android_ua = "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
    res_android = client.get(f"/r/{slug}", headers={"User-Agent": android_ua}, follow_redirects=False)
    assert res_android.status_code == 302
    loc_android = res_android.headers["location"]
    assert "play.google.com/store/apps/details?id=com.uwo.ailegal" in loc_android
    assert f"slug%3D{slug}" in loc_android or f"slug={slug}" in loc_android

    # 3. iOS Device Click
    ios_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
    res_ios = client.get(f"/r/{slug}", headers={"User-Agent": ios_ua}, follow_redirects=False)
    assert res_ios.status_code == 302
    loc_ios = res_ios.headers["location"]
    assert loc_ios == "https://apps.apple.com/app/id6797449251"

    # 4. Desktop Device Click
    desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    res_desktop = client.get(f"/r/{slug}", headers={"User-Agent": desktop_ua}, follow_redirects=False)
    assert res_desktop.status_code == 302
    loc_desktop = res_desktop.headers["location"]
    assert "https://ailegal.aisa24.com" in loc_desktop



