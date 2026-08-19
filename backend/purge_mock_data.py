"""
One-time cleanup script to purge all previously seeded mock/demo data
from the MongoDB database collections.

Collections cleaned:
  - chat_tracking      (seeded by seeder.py)
  - app_downloads      (seeded by seeder.py)
  - logs               (seeded by seeder.py)
  - subscriptions      (seeded by seeder.py with demo user IDs like usr_demo_*)
  - payments           (seeded by seeder.py with demo payment IDs like pay_100*)
  - play_install_metrics (seeded by seed_db.py with source_file_id = "seed_data")

This script does NOT touch real user data or application keys.
Run once and then delete this file.
"""
import sys
import os

# Ensure the backend src is on the path
sys.path.insert(0, os.path.dirname(__file__))

from src.database.connection import get_client
from src.config.settings import settings


def purge_mock_data():
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]

    print("=" * 60)
    print("  PURGING ALL SEEDED / MOCK DATA FROM MONGODB")
    print("=" * 60)

    # 1. play_install_metrics — seeded by seed_db.py (source_file_id = "seed_data")
    result = db["play_install_metrics"].delete_many({"source_file_id": "seed_data"})
    print(f"[play_install_metrics] Deleted {result.deleted_count} seed_data records.")

    # 2. chat_tracking — seeded entries have user_id like "usr_demo_*"
    result = db["chat_tracking"].delete_many({"user_id": {"$regex": "^usr_demo_"}})
    print(f"[chat_tracking] Deleted {result.deleted_count} demo user records.")

    # 3. app_downloads — seeded entries have user_id like "usr_demo_*"
    result = db["app_downloads"].delete_many({"user_id": {"$regex": "^usr_demo_"}})
    print(f"[app_downloads] Deleted {result.deleted_count} demo user records.")

    # 4. logs — seeded entries have user_id like "usr_demo_*"
    result = db["logs"].delete_many({"user_id": {"$regex": "^usr_demo_"}})
    print(f"[logs] Deleted {result.deleted_count} demo user records.")

    # 5. subscriptions — seeded entries have _id like "sub_pro_*" and user_id like "usr_demo_*"
    result = db["subscriptions"].delete_many({"user_id": {"$regex": "^usr_demo_"}})
    print(f"[subscriptions] Deleted {result.deleted_count} demo subscription records.")

    # 6. payments — seeded entries have _id like "pay_*" and user_id like "usr_demo_*"
    result = db["payments"].delete_many({"user_id": {"$regex": "^usr_demo_"}})
    print(f"[payments] Deleted {result.deleted_count} demo payment records.")

    print()
    print("=" * 60)
    print("  PURGE COMPLETE — Remaining real data counts:")
    print("=" * 60)
    for coll_name in ["play_install_metrics", "chat_tracking", "app_downloads", "logs", "subscriptions", "payments"]:
        count = db[coll_name].count_documents({})
        print(f"  {coll_name}: {count} records")
    print()


if __name__ == "__main__":
    purge_mock_data()
