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


def test_forgot_and_reset_password_flow(client):
    email = "forgotuser@example.com"
    initial_password = "InitialPassword123!"
    new_password = "BrandNewPassword456!"

    # 1. Register User
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": initial_password,
        "name": "Forgot User"
    })
    assert reg_res.status_code == 201

    # 2. Login to obtain session
    login_res = client.post("/api/auth/login", json={"email": email, "password": initial_password})
    assert login_res.status_code == 200
    active_refresh_token = login_res.json()["refresh_token"]

    # 3. Request Password Reset OTP
    forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    assert "message" in forgot_data
    otp = forgot_data.get("otp_preview")
    assert otp is not None
    assert len(otp) == 6

    # 4. Attempt Verify with Invalid OTP
    verify_bad = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": "000000"})
    assert verify_bad.status_code == 400

    # 5. Verify with Valid OTP
    verify_good = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": otp})
    assert verify_good.status_code == 200
    assert verify_good.json()["valid"] is True

    # 6. Reset Password with Valid OTP
    reset_res = client.post("/api/auth/reset-password", json={
        "email": email,
        "otp": otp,
        "new_password": new_password
    })
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    # 7. Old password should fail
    old_login = client.post("/api/auth/login", json={"email": email, "password": initial_password})
    assert old_login.status_code == 401

    # 8. New password should succeed
    new_login = client.post("/api/auth/login", json={"email": email, "password": new_password})
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

    # 9. Prior session refresh token should now be revoked
    revoked_res = client.post("/api/auth/refresh", json={"refresh_token": active_refresh_token})
    assert revoked_res.status_code == 403

    # 10. Reusing the already used OTP should fail
    reuse_res = client.post("/api/auth/reset-password", json={
        "email": email,
        "otp": otp,
        "new_password": "YetAnotherPassword789!"
    })
    assert reuse_res.status_code == 400

