import pytest  # type: ignore
from src.auth.service import hash_password


@pytest.fixture
def analytics_setup(client, db_session):
    # 1. Create AISA App Key
    aisa_res = client.post("/api/applications/keys", json={"application_name": "AISA"})
    aisa_key = aisa_res.json()["api_key"]
    aisa_id = aisa_res.json()["id"]

    # 2. Create AI Legal App Key
    legal_res = client.post("/api/applications/keys", json={"application_name": "AI Legal"})
    legal_key = legal_res.json()["api_key"]
    legal_id = legal_res.json()["id"]

    # 3. Seed admin user for getting overlap stats
    admin_doc = {
        "_id": "test_admin_id",
        "username": "analytics.admin@unified.com",
        "password_hash": hash_password("AnalyticsAdminPassword123!"),
        "role": "admin",
        "name": "Analytics Admin",
        "is_active": True
    }
    db_session["admin_users"].insert_one(admin_doc)

    # 4. Authenticate Admin
    login_res = client.post("/api/admin/login", json={
        "username": "analytics.admin@unified.com",
        "password": "AnalyticsAdminPassword123!"
    })
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    return {
        "aisa_key": aisa_key,
        "aisa_id": aisa_id,
        "legal_key": legal_key,
        "legal_id": legal_id,
        "admin_headers": admin_headers
    }


def test_user_cross_app_tracking_and_overlap(client, db_session, analytics_setup):
    setup = analytics_setup
    user_email = "crossover.user@example.com"
    user_password = "SecurePassword123!"
    user_name = "Crossover User"

    # Step 1: Register user on AISA
    headers_aisa = {"X-Application-Key": setup["aisa_key"]}
    reg_res = client.post(
        "/api/auth/register",
        json={"email": user_email, "password": user_password, "name": user_name},
        headers=headers_aisa
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    # Verify user record contains AISA application ID
    user_doc = db_session["users"].find_one({"_id": user_id})
    assert setup["aisa_id"] in user_doc.get("connected_apps", [])
    assert setup["legal_id"] not in user_doc.get("connected_apps", [])

    # Step 2: Login same user from AI Legal (simulating downloading and logging in to second app)
    headers_legal = {"X-Application-Key": setup["legal_key"]}
    login_res = client.post(
        "/api/auth/login",
        json={"email": user_email, "password": user_password},
        headers=headers_legal
    )
    assert login_res.status_code == 200

    # Verify user record now contains BOTH AISA and AI Legal application IDs
    user_doc = db_session["users"].find_one({"_id": user_id})
    assert setup["aisa_id"] in user_doc.get("connected_apps", [])
    assert setup["legal_id"] in user_doc.get("connected_apps", [])

    # Step 3: Fetch analytics overlap stats from admin dashboard api
    stats_res = client.get("/api/admin/analytics/overlap", headers=setup["admin_headers"])
    assert stats_res.status_code == 200
    stats = stats_res.json()

    # Validate stats contain the correct overlap metrics
    assert stats["aisa_app"]["users_count"] == 1
    assert stats["ailegal_app"]["users_count"] == 1
    assert stats["overlap"]["count"] == 1
    assert stats["overlap"]["percentage_aisa"] == 100.0
    assert stats["overlap"]["percentage_legal"] == 100.0

    # Verify general app list includes both apps
    app_names = [a["name"] for a in stats["apps"]]
    assert "AISA" in app_names
    assert "AI Legal" in app_names
