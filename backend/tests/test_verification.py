import pytest  # type: ignore

from datetime import datetime, timedelta, timezone
from src.database.models import VerificationToken, User


import uuid

@pytest.fixture
def setup_user_and_app(client):
    app_res = client.post("/api/applications/keys", json={"application_name": f"Verification App {uuid.uuid4().hex[:6]}"})
    api_key = app_res.json()["api_key"]


    email = f"verifyuser_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!", "name": "Verify User"},
        headers={"X-Application-Key": api_key}
    )
    user_id = reg_res.json()["id"]

    return api_key, user_id



def test_send_and_verify_token(client, setup_user_and_app):
    api_key, user_id = setup_user_and_app
    headers = {"X-Application-Key": api_key}

    # 1. Send Verification Token
    res = client.post("/api/verification/send", json={"user_id": user_id}, headers=headers)
    assert res.status_code == 200
    token_str = res.json()["token"]

    # 2. Verify Token
    res = client.post("/api/verification/verify", json={"token": token_str}, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_verified"] is True
    assert res.json()["user_id"] == user_id

    # 3. Attempt to reuse used token
    res = client.post("/api/verification/verify", json={"token": token_str}, headers=headers)
    assert res.status_code == 400
    assert "already been used" in res.json()["detail"]

    # 4. Request token for already verified user
    res = client.post("/api/verification/send", json={"user_id": user_id}, headers=headers)
    assert res.status_code == 400
    assert "already verified" in res.json()["detail"]


def test_invalid_and_expired_verification_token(client, setup_user_and_app, db_session):
    api_key, user_id = setup_user_and_app
    headers = {"X-Application-Key": api_key}

    # Invalid token test
    res = client.post("/api/verification/verify", json={"token": "non_existent_token_1234567890"}, headers=headers)
    assert res.status_code == 404

    expired_token_str = "expired_token_abcdef1234567890"
    vt_dict = VerificationToken.create_dict(
        user_id=user_id,
        token=expired_token_str,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        is_used=False
    )
    db_session["verification_tokens"].insert_one(vt_dict)

    # Expired token test
    res = client.post("/api/verification/verify", json={"token": expired_token_str}, headers=headers)
    assert res.status_code == 400
    assert "expired" in res.json()["detail"]
