def test_create_and_list_application_keys(client):
    # 1. Create Application API Key
    response = client.post("/api/applications/keys", json={"application_name": "Application Alpha"})
    assert response.status_code == 201
    data = response.json()
    assert data["application_name"] == "Application Alpha"
    assert data["status"] == "active"
    assert "api_key" in data
    assert data["api_key"].startswith("key_")

    key_id = data["id"]
    api_key = data["api_key"]

    # 2. List Application Keys
    response = client.get("/api/applications/keys")
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) == 1
    assert keys[0]["id"] == key_id
    assert "api_key" not in keys[0]  # Plaintext key must not be returned in list endpoint


def test_application_key_authentication(client):
    # Create key
    res = client.post("/api/applications/keys", json={"application_name": "Application Beta"})
    api_key = res.json()["api_key"]
    key_id = res.json()["id"]

    # Valid Key Header
    user_payload = {"email": "user1@example.com", "password": "password123", "name": "User One"}
    res = client.post("/api/auth/register", json=user_payload, headers={"X-Application-Key": api_key})
    assert res.status_code == 201

    # Invalid Key Header
    res = client.post("/api/auth/register", json=user_payload, headers={"X-Application-Key": "key_invalid_key_12345"})
    assert res.status_code == 401
    assert "Invalid or revoked" in res.json()["detail"]

    # Revoke Key
    res = client.delete(f"/api/applications/keys/{key_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "revoked"

    # Revoked Key Header
    res = client.post("/api/auth/register", json=user_payload, headers={"X-Application-Key": api_key})
    assert res.status_code == 401
    assert "Invalid or revoked" in res.json()["detail"]
