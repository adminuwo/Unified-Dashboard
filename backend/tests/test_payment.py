import hmac
import hashlib
import json
import pytest  # type: ignore

from src.config.settings import settings


@pytest.fixture
def payment_setup(client):
    app_res = client.post("/api/applications/keys", json={"application_name": "Payment App"})
    api_key = app_res.json()["api_key"]

    reg_res = client.post(
        "/api/auth/register",
        json={"email": "payer@example.com", "password": "Password123!", "name": "Payer User"},
        headers={"X-Application-Key": api_key}
    )
    user_id = reg_res.json()["id"]

    return api_key, user_id


def test_create_and_get_payment_status(client, payment_setup):
    api_key, user_id = payment_setup
    headers = {"X-Application-Key": api_key}

    # 1. Create Payment
    pay_req = {
        "user_id": user_id,
        "product_id": "product_cloud_analytics",
        "plan_id": "plan_pro_monthly",
        "amount": 1499.00,
        "currency": "INR",
        "provider": "razorpay"
    }
    res = client.post("/api/payment/create", json=pay_req, headers=headers)
    assert res.status_code == 201
    pay_data = res.json()
    assert pay_data["user_id"] == user_id
    assert pay_data["amount"] == 1499.00
    assert pay_data["currency"] == "INR"
    assert pay_data["status"] == "pending"
    assert "provider_payment_id" in pay_data
    payment_id = pay_data["id"]

    # 2. Query Payment Status
    res = client.get(f"/api/payment/status/{payment_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "pending"
    assert res.json()["amount"] == 1499.00


def test_invalid_user_payment_creation(client, payment_setup):
    api_key, _ = payment_setup
    headers = {"X-Application-Key": api_key}

    pay_req = {
        "user_id": "invalid_user_id_12345",
        "product_id": "product_cloud_analytics",
        "plan_id": "plan_pro_monthly",
        "amount": 1499.00
    }
    res = client.post("/api/payment/create", json=pay_req, headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_payment_webhook(client, payment_setup):
    api_key, user_id = payment_setup
    headers = {"X-Application-Key": api_key}

    # Create Payment
    pay_req = {
        "user_id": user_id,
        "product_id": "product_subscription_app",
        "plan_id": "plan_starter",
        "amount": 10.00
    }
    pay_res = client.post("/api/payment/create", json=pay_req, headers=headers).json()
    provider_payment_id = pay_res["provider_payment_id"]

    # Prepare Webhook Payload
    webhook_data = {
        "event": "payment.succeeded",
        "provider_payment_id": provider_payment_id,
        "status": "succeeded",
        "metadata": {"test": "true"}
    }
    raw_payload = json.dumps(webhook_data).encode('utf-8')
    sig = hmac.new(settings.PAYMENT_WEBHOOK_SECRET.encode('utf-8'), raw_payload, hashlib.sha256).hexdigest()

    # Send Webhook with HMAC signature
    res = client.post(
        "/api/payment/webhook",
        content=raw_payload,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res.status_code == 200
    assert res.json()["payment_status"] == "succeeded"

    # Verify status updated
    status_res = client.get(f"/api/payment/status/{provider_payment_id}", headers=headers)
    assert status_res.json()["status"] == "succeeded"
