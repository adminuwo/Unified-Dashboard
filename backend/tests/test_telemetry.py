import pytest  # type: ignore


@pytest.fixture
def telemetry_app_key(client):
    res = client.post("/api/applications/keys", json={"application_name": "Telemetry Test App"})
    return res.json()["api_key"]


def test_record_chat_tracking(client, telemetry_app_key):
    headers = {"X-Application-Key": telemetry_app_key}
    chat_payload = {
        "session_id": "sess_test_1001",
        "model_name": "gpt-4o",
        "prompt_tokens": 150,
        "completion_tokens": 300,
        "latency_ms": 250.5,
        "user_id": "usr_test_1001"
    }

    res = client.post("/api/telemetry/chat", json=chat_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["session_id"] == "sess_test_1001"
    assert data["model_name"] == "gpt-4o"
    assert data["prompt_tokens"] == 150
    assert data["completion_tokens"] == 300
    assert data["total_tokens"] == 450
    assert data["latency_ms"] == 250.5


def test_record_app_download(client, telemetry_app_key):
    headers = {"X-Application-Key": telemetry_app_key}
    download_payload = {
        "platform": "android",
        "version": "2.1.0",
        "ip_country": "IN",
        "user_id": "usr_test_1001"
    }

    res = client.post("/api/telemetry/download", json=download_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["platform"] == "android"
    assert data["version"] == "2.1.0"
    assert data["ip_country"] == "IN"


def test_unauthorized_telemetry(client):
    chat_payload = {
        "session_id": "sess_invalid",
        "model_name": "claude-3-5",
        "prompt_tokens": 10,
        "completion_tokens": 10
    }
    res = client.post("/api/telemetry/chat", json=chat_payload, headers={"X-Application-Key": "invalid_key"})
    assert res.status_code == 401


def test_telemetry_overview(client, telemetry_app_key):
    headers = {"X-Application-Key": telemetry_app_key}

    # Post 2 chat events
    client.post("/api/telemetry/chat", json={
        "session_id": "sess_1",
        "model_name": "gpt-4o",
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "latency_ms": 100.0
    }, headers=headers)

    client.post("/api/telemetry/chat", json={
        "session_id": "sess_2",
        "model_name": "claude-3-5",
        "prompt_tokens": 50,
        "completion_tokens": 150,
        "latency_ms": 200.0
    }, headers=headers)

    # Post 2 download events
    client.post("/api/telemetry/download", json={"platform": "android"}, headers=headers)
    client.post("/api/telemetry/download", json={"platform": "ios"}, headers=headers)

    # Fetch global telemetry overview
    res = client.get("/api/telemetry/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_chat_sessions"] == 2
    assert data["total_tokens"] == 500
    assert data["total_downloads"] == 2
    assert data["downloads_by_platform"]["android"] == 1
    assert data["downloads_by_platform"]["ios"] == 1
