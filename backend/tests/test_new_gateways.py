import pytest
from src.integrations.cashfree.provider import CashfreeProvider
from src.integrations.razorpay_efv.provider import RazorpayEFVProvider

def test_cashfree_provider_init(db_session):
    provider = CashfreeProvider(db_session)
    assert provider.provider_name == "cashfree"
    # Credentials are configured in test/load_dotenv in test script, but here Settings defaults to None unless in env
    # conftest.py does not load .env files to keep in-memory mock environment clean.
    # So is_configured() is False during standard pytest unless populated in env.
    # That is the expected behavior.

def test_razorpay_efv_provider_init(db_session):
    provider = RazorpayEFVProvider(db_session)
    assert provider.provider_name == "razorpay_efv"
