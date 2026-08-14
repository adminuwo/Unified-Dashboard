import os
from src.database.connection import get_client, get_db
from src.analytics.google_play.sync_service import run_sync
from src.config.settings import settings

def main():
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    
    # Run the sync process
    apps = [
        {"app_code": "aisa", "package_name": "com.uwo.aisa"},
        {"app_code": "ailegal", "package_name": "com.uwo.ailegal"}
    ]
    
    bucket_name = "pubsite_prod_5002243960657921085"
    
    print("Starting sync...")
    result = run_sync(db=db, apps=apps, bucket_name=bucket_name, auth_mode="application_default")
    print("Sync complete!")
    print(result)
    
    # Print metrics collected
    metrics = db["play_install_metrics"].count_documents({})
    print(f"Total metrics in DB: {metrics}")

if __name__ == "__main__":
    main()
