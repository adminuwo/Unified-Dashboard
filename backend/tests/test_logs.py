import pytest  # type: ignore



@pytest.fixture
def logging_app_key(client):
    res = client.post("/api/applications/keys", json={"application_name": "Logging Test App"})
    return res.json()["api_key"]


def test_submit_valid_log(client, logging_app_key):
    headers = {"X-Application-Key": logging_app_key}
    log_payload = {
        "level": "INFO",
        "event": "user_logged_in",
        "message": "User login process completed successfully",
        "user_id": "usr_999",
        "metadata": {"request_id": "req_abc123", "ip": "127.0.0.1"}
    }

    res = client.post("/api/logs/", json=log_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["level"] == "INFO"
    assert data["event"] == "user_logged_in"
    assert data["user_id"] == "usr_999"
    assert data["metadata"]["request_id"] == "req_abc123"


def test_submit_log_unauthorized(client):
    log_payload = {
        "level": "ERROR",
        "event": "system_failure",
        "message": "Critical error"
    }
    res = client.post("/api/logs/", json=log_payload, headers={"X-Application-Key": "invalid_key"})
    assert res.status_code == 401


def test_submit_log_sensitive_data_redaction(client, logging_app_key):
    headers = {"X-Application-Key": logging_app_key}
    log_payload = {
        "level": "ERROR",
        "event": "authentication_failed",
        "message": "User failed auth with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.secret and key_1234567890abcdef",
        "user_id": "usr_123",
        "metadata": {
            "password": "SuperSecretPassword123!",
            "api_key": "key_secret_api_key_123",
            "access_token": "bearer_token_abc",
            "safe_field": "public_data"
        }
    }

    res = client.post("/api/logs/", json=log_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    # Verify sensitive metadata redacted
    meta = data["metadata"]
    assert meta["password"] == "[REDACTED_SENSITIVE_DATA]"
    assert meta["api_key"] == "[REDACTED_SENSITIVE_DATA]"
    assert meta["access_token"] == "[REDACTED_SENSITIVE_DATA]"
    assert meta["safe_field"] == "public_data"

    # Verify sensitive message patterns redacted
    msg = data["message"]
    assert "Bearer [REDACTED_JWT]" in msg
    assert "key_[REDACTED_API_KEY]" in msg
