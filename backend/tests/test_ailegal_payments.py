import pytest
import mongomock
from datetime import datetime, timezone

from src.modules.revenue.checkout_service import RevenueCheckoutService
from src.integrations.app_store.iap_service import AppleIAPService
from src.modules.revenue.aggregation import RevenueAggregator
from src.modules.revenue.service import RevenueService


def test_android_web_checkout_and_verification():
    """Verify Android web-checkout session creation and payment verification."""
    db = mongomock.MongoClient().db

    checkout_service = RevenueCheckoutService(db)

    # 1. Create Android Web checkout session
    session = checkout_service.create_checkout_session(
        product_code="ailegal",
        platform="android",
        plan_id="ailegal_pro_monthly",
        amount=999.0,
        currency="INR",
        customer_id="advocate_user_456",
        customer_email="advocate@ailegal.app",
        customer_name="Advocate Sharma",
        callback_url="ailegal://payment-callback"
    )

    assert session["success"] is True
    assert session["product_code"] == "ailegal"
    assert session["platform"] == "android"
    assert session["callback_url"] == "ailegal://payment-callback"
    assert session["amount"] == 999.0
    assert "order_id" in session

    order_id = session["order_id"]

    # 2. Verify payment captured via web
    verify_res = checkout_service.verify_checkout_payment(
        order_id=order_id,
        payment_id="pay_rzp_mock_android_999",
        signature="",
        product_code="ailegal",
        platform="android",
        provider="razorpay",
        plan_id="ailegal_pro_monthly",
        amount=999.0,
        customer_id="advocate_user_456",
        customer_email="advocate@ailegal.app"
    )

    assert verify_res["success"] is True
    assert verify_res["platform"] == "android"
    assert verify_res["product_code"] == "ailegal"

    # 3. Check revenue_transactions record in DB
    tx = db["revenue_transactions"].find_one({"external_transaction_id": "pay_rzp_mock_android_999"})
    assert tx is not None
    assert tx["product_code"] == "ailegal"
    assert tx["platform"] == "android"
    assert tx["provider"] == "razorpay"
    assert tx["gross_amount"] == 999.0

    # 4. Check unified cross-platform entitlement
    status_res = checkout_service.get_unified_subscription_status(
        customer_id_or_email="advocate_user_456",
        product_code="ailegal"
    )
    assert status_res["is_active"] is True
    assert status_res["platform_source"] == "android"
    assert status_res["plan_name"] == "AI Legal Pro"


def test_ios_apple_in_app_purchase_verification():
    """Verify iOS Apple In-App Purchase StoreKit 2 verification and ledger ingestion."""
    db = mongomock.MongoClient().db

    iap_service = AppleIAPService(db)

    # Verify Apple IAP
    verify_res = iap_service.verify_and_ingest_purchase(
        transaction_id="apple_sk2_tx_778899",
        product_code="ailegal",
        bundle_id="com.uwo.ailegal",
        customer_id="advocate_ios_user_123",
        customer_email="senior_counsel@ailegal.app",
        plan_id="com.uwo.ailegal.sub.monthly",
        amount=999.0,
        is_sandbox=True
    )

    assert verify_res["success"] is True
    assert verify_res["product_code"] == "ailegal"
    assert verify_res["bundle_id"] == "com.uwo.ailegal"
    assert verify_res["is_active"] is True

    # Check revenue_transactions record in DB
    tx = db["revenue_transactions"].find_one({"external_transaction_id": "apple_apple_sk2_tx_778899"})
    assert tx is not None
    assert tx["product_code"] == "ailegal"
    assert tx["platform"] == "ios"
    assert tx["provider"] == "app_store"
    assert tx["gross_amount"] == 999.0

    # Check unified entitlement
    checkout_service = RevenueCheckoutService(db)
    status_res = checkout_service.get_unified_subscription_status(
        customer_id_or_email="advocate_ios_user_123",
        product_code="ailegal"
    )
    assert status_res["is_active"] is True
    assert status_res["platform_source"] == "ios"
    assert status_res["provider"] == "app_store"


def test_unified_dashboard_channel_breakdown():
    """Verify Unified Dashboard correctly reflects Android Web and iOS Apple channels for AI Legal."""
    db = mongomock.MongoClient().db

    checkout_service = RevenueCheckoutService(db)
    iap_service = AppleIAPService(db)
    aggregator = RevenueAggregator(db)

    # 1. Android Web transaction: ₹999.0
    checkout_service.create_checkout_session(
        product_code="ailegal", platform="android", amount=999.0, customer_id="user_and_1"
    )
    checkout_service.verify_checkout_payment(
        order_id="order_1", payment_id="pay_and_1", signature="",
        product_code="ailegal", platform="android", amount=999.0, customer_id="user_and_1"
    )

    # 2. iOS Apple transaction: ₹2,499.0
    iap_service.verify_and_ingest_purchase(
        transaction_id="tx_ios_1", product_code="ailegal", amount=2499.0,
        customer_id="user_ios_1", is_sandbox=True
    )

    # Query Platform breakdown in dashboard
    platform_stats = aggregator.get_by_platform()
    stats_map = {p["platform"]: p for p in platform_stats}

    assert "android" in stats_map
    assert "ios" in stats_map
    assert stats_map["android"]["gross"] == 999.0
    assert stats_map["ios"]["gross"] == 2499.0

    # Query Product breakdown in dashboard
    product_stats = aggregator.get_by_product()
    prod_map = {p["product_code"]: p for p in product_stats}

    assert "ailegal" in prod_map
    assert prod_map["ailegal"]["gross"] == 999.0 + 2499.0  # 3498.0
