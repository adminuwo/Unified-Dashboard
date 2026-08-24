import pytest
from datetime import datetime, timezone
from src.integrations.razorpay.provider import RazorpayProvider


def test_ingest_aisa_payment(client, admin_headers, db_session):
    payload = {
        "product_code": "aisa",
        "product_name": "AISA Assistant",
        "platform": "web",
        "provider": "razorpay",
        "transaction_id": "pay_test_aisa_12345",
        "order_id": "order_test_98765",
        "transaction_type": "payment",
        "amount": 499.0,
        "tax_amount": 76.12,
        "fee_amount": 9.98,
        "net_amount": 412.90,
        "currency": "INR",
        "status": "completed",
        "customer_id": "user_123",
        "customer_email": "testuser@aisa.com",
        "customer_name": "Test User",
        "plan_id": "Plan_1",
        "plan_name": "Creator",
        "billing_cycle": "monthly",
        "transaction_date": "2026-08-21T12:00:00Z",
        "metadata": {
            "source": "aisa_app_test",
            "invoice_number": "INV-2026-000001"
        }
    }

    # 1. Test POST /api/revenue/ingest
    res = client.post("/api/revenue/ingest", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True
    assert data["transaction_id"] == "pay_test_aisa_12345"
    assert data["product_code"] == "aisa"
    assert data["status"] == "completed"

    # 2. Verify stored in revenue_transactions
    tx = db_session["revenue_transactions"].find_one({"external_transaction_id": "pay_test_aisa_12345"})
    assert tx is not None
    assert tx["product_code"] == "aisa"
    assert tx["gross_amount"] == 499.0
    assert tx["customer_email"] == "testuser@aisa.com"

    # 3. Verify stored in revenue_raw_events
    raw = db_session["revenue_raw_events"].find_one({"external_id": "pay_test_aisa_12345"})
    assert raw is not None
    assert raw["payload"]["product_name"] == "AISA Assistant"


def test_ingest_other_unassigned_payment(client, admin_headers, db_session):
    # Ingesting payment without explicit known product code
    payload = {
        "product_code": "other",
        "product_name": "Unknown Gateway Charge",
        "platform": "web",
        "provider": "razorpay",
        "transaction_id": "pay_test_unmapped_999",
        "amount": 1299.0,
        "currency": "INR",
        "status": "completed",
        "customer_email": "unknown@example.com"
    }

    res = client.post("/api/revenue/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["product_code"] == "other"

    # Query product breakdown
    prod_res = client.get("/api/admin/revenue/products", headers=admin_headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()["products"]

    # Verify both 'aisa' and 'other' are present
    codes = [p["product_code"] for p in prod_data]
    assert "aisa" in codes
    assert "other" in codes

    other_item = next(p for p in prod_data if p["product_code"] == "other")
    assert other_item["gross"] >= 1299.0
    assert other_item["name"] == "Other Applications"


def test_razorpay_infer_product_code_fallback_to_other(db_session):
    provider = RazorpayProvider(db_session)
    
    # 1. Matches aisa
    item_aisa = {"id": "pay_1", "description": "AISA Pro plan upgrade", "notes": {}}
    assert provider._infer_product_code(item_aisa) == "aisa"

    # 2. Matches legal
    item_legal = {"id": "pay_2", "description": "Legal drafting subscription", "notes": {}}
    assert provider._infer_product_code(item_legal) == "ailegal"

    # 3. Matches notes
    item_notes = {"id": "pay_3", "notes": {"product_code": "efvframework"}}
    assert provider._infer_product_code(item_notes) == "efvframework"

    # 4. Unknown payment with no keywords or notes -> MUST fallback to 'other'
    item_unknown = {"id": "pay_4", "description": "Generic Store Item #404", "notes": {}}
    assert provider._infer_product_code(item_unknown) == "other"
