import pytest  # type: ignore



@pytest.fixture
def app_key(client):
    res = client.post("/api/applications/keys", json={"application_name": "Test Auth App"})
    return res.json()["api_key"]


def test_user_registration_and_duplicate(client, app_key):
    headers = {"X-Application-Key": app_key}
    payload = {"email": "testuser@example.com", "password": "SecurePassword123!", "name": "Test User"}

    # 1. Register User
    res = client.post("/api/auth/register", json=payload, headers=headers)
    assert res.status_code == 201
    user = res.json()
    assert user["email"] == "testuser@example.com"
    assert user["name"] == "Test User"
    assert user["is_verified"] is False
    assert user["is_active"] is True

    # 2. Duplicate Registration
    res = client.post("/api/auth/register", json=payload, headers=headers)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_user_login_and_me_endpoint(client, app_key):
    headers = {"X-Application-Key": app_key}
    payload = {"email": "loginuser@example.com", "password": "CorrectPassword123!", "name": "Login User"}

    # Register
    client.post("/api/auth/register", json=payload, headers=headers)

    # Invalid Password Login
    res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "WrongPassword"}, headers=headers)
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

    # Valid Login
    res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "CorrectPassword123!"}, headers=headers)
    assert res.status_code == 200
    auth_data = res.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    assert auth_data["token_type"] == "bearer"

    access_token = auth_data["access_token"]
    refresh_token = auth_data["refresh_token"]

    # Call /me with valid JWT
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert res.status_code == 200
    me_data = res.json()
    assert me_data["email"] == "loginuser@example.com"

    # Call /me with invalid JWT
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_jwt_token_12345"})
    assert res.status_code == 401

    # Refresh Token
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token}, headers=headers)
    assert res.status_code == 200
    new_tokens = res.json()
    assert "access_token" in new_tokens

    # Logout
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
