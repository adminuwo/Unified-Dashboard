import asyncio
from src.database.connection import get_client
from src.config.settings import settings
from src.analytics.google_play.sync_service import run_sync

def run_real_sync():
    print("Clearing dummy data...")
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    
    result = db["play_install_metrics"].delete_many({})
    print(f"Deleted {result.deleted_count} dummy records.")
    
    print("Running real Google Play sync...")
    apps = [
        {"app_code": "aisa", "package_name": "com.uwo.aisa"},
        {"app_code": "ailegal", "package_name": "com.uwo.ailegal"}
    ]
    bucket = settings.GOOGLE_PLAY_GCS_BUCKET_ID
    
    try:
        res = run_sync(db, apps, bucket, auth_mode="adc")
        print(f"Sync complete! Result: {res}")
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    run_real_sync()
