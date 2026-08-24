import os
import pymongo
from dotenv import load_dotenv

# Load the .env from the backend directory
env_path = "c:/Users/saksh/OneDrive/Desktop/unified/Unified-Dashboard/backend/.env"
load_dotenv(env_path)

# Verify settings parsed correctly
from src.config.settings import settings
print(f"CASHFREE_APP_ID: {settings.CASHFREE_APP_ID}")
print(f"CASHFREE_SECRET_KEY: {settings.CASHFREE_SECRET_KEY[:10]}...")
print(f"RAZORPAY_EFV_KEY_ID: {settings.RAZORPAY_EFV_KEY_ID}")
print(f"RAZORPAY_EFV_KEY_SECRET: {settings.RAZORPAY_EFV_KEY_SECRET[:10]}...")

# Connect to database
url = settings.MONGODB_URL
client = pymongo.MongoClient(url)
db = client[settings.MONGODB_DB_NAME]

from src.integrations.cashfree.provider import CashfreeProvider
from src.integrations.razorpay_efv.provider import RazorpayEFVProvider

cf_prov = CashfreeProvider(db)
rz_efv_prov = RazorpayEFVProvider(db)

print("\nTesting Cashfree Connection:")
print(cf_prov.test_connection())

print("\nTesting Razorpay EFV Connection:")
print(rz_efv_prov.test_connection())
