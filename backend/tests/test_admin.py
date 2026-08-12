import pytest  # type: ignore
from src.auth.service import hash_password


@pytest.fixture
def admin_setup(client, db_session):
    # Seed a test admin account into mongomock DB
    admin_doc = {
        "_id": "test_admin_id",
        "username": "test.admin@unified.com",
        "password_hash": hash_password("TestAdminPassword123!"),
        "role": "admin",
        "name": "Test Admin",
        "is_active": True
    }
    db_session["admin_users"].insert_one(admin_doc)

    # 1. Create app key
    app_res = client.post("/api/applications/keys", json={"application_name": "Admin Test App"})
    api_key = app_res.json()["api_key"]
    app_id = app_res.json()["id"]

    # 2. Register user
    headers = {"X-Application-Key": api_key}
    user_res = client.post(
        "/api/auth/register",
        json={"email": "adminuser@example.com", "password": "Password123!", "name": "Admin User"},
        headers=headers
    )
    user_id = user_res.json()["id"]

    # 3. Create payment
    client.post(
        "/api/payment/create",
        json={"user_id": user_id, "product_id": "product_x", "plan_id": "plan_y", "amount": 49.99},
        headers=headers
    )

    # 4. Submit log
    client.post(
        "/api/logs/",
        json={"level": "INFO", "event": "test_event", "message": "Test log message"},
        headers=headers
    )

    # 5. Authenticate Admin
    login_res = client.post("/api/admin/login", json={
        "username": "test.admin@unified.com",
        "password": "TestAdminPassword123!"
    })
    token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    return api_key, app_id, user_id, admin_headers


def test_admin_login(client, db_session):
    # Seed admin user
    db_session["admin_users"].insert_one({
        "_id": "test_admin_id",
        "username": "login.admin@unified.com",
        "password_hash": hash_password("ValidAdminPassword123!"),
        "role": "admin",
        "name": "Login Admin",
        "is_active": True
    })

    # Invalid credentials
    res = client.post("/api/admin/login", json={"username": "wrong", "password": "wrong"})
    assert res.status_code == 401

    # Valid credentials
    res = client.post("/api/admin/login", json={
        "username": "login.admin@unified.com",
        "password": "ValidAdminPassword123!"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_admin_unauthorized_access(client):
    # Request without token should return 401
    res = client.get("/api/admin/stats")
    assert res.status_code == 401


def test_admin_stats(client, admin_setup):
    _, _, _, admin_headers = admin_setup
    res = client.get("/api/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] == 1
    assert data["total_applications"] >= 1

    assert data["total_logs"] == 1


def test_admin_directories(client, admin_setup):
    _, _, user_id, admin_headers = admin_setup

    # Test users list
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == user_id

    # Test payments list
    res = client.get("/api/admin/payments", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Test subscriptions list
    res = client.get("/api/admin/subscriptions", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Test logs list
    res = client.get("/api/admin/logs?level=INFO", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["level"] == "INFO"
