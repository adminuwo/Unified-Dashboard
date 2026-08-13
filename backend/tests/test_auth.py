import pytest  # type: ignore


def test_user_registration_and_duplicate(client):
    payload = {"email": "testuser@example.com", "password": "SecurePassword123!", "name": "Test User"}

    # 1. Register User
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    user = res.json()
    assert user["email"] == "testuser@example.com"
    assert user["name"] == "Test User"
    assert user["is_active"] is True

    # 2. Duplicate Registration
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_user_login_and_me_endpoint(client):
    payload = {"email": "loginuser@example.com", "password": "CorrectPassword123!", "name": "Login User"}

    # Register
    client.post("/api/auth/register", json=payload)

    # Invalid Password Login
    res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

    # Valid Login
    res = client.post("/api/auth/login", json={"email": "loginuser@example.com", "password": "CorrectPassword123!"})
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

    # Call /validate with valid token (SSO integration bridge)
    val_res = client.post("/api/auth/validate", json={"token": access_token})
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is True
    assert val_data["user"]["email"] == "loginuser@example.com"

    # Call /validate with invalid token
    val_invalid = client.post("/api/auth/validate", json={"token": "bad_token"})
    assert val_invalid.status_code == 200
    assert val_invalid.json()["valid"] is False

    # Refresh Token Rotation
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    new_tokens = res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Verify old refresh token is now invalidated (due to rotation)
    old_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert old_res.status_code == 403

    # Logout
    res = client.post("/api/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert res.status_code == 200
