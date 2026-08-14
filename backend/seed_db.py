import os
from datetime import datetime, timedelta
from src.database.connection import get_client, get_db
from src.database.models import generate_uuid
from src.config.settings import settings

def main():
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    
    apps = [
        {"app_code": "aisa", "package_name": "com.uwo.aisa"},
        {"app_code": "ailegal", "package_name": "com.uwo.ailegal"}
    ]
    
    docs = []
    
    # Generate 30 days of data ending yesterday
    end_date = datetime.utcnow().date() - timedelta(days=1)
    
    for app in apps:
        for i in range(30):
            d = end_date - timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            
            # Base installs (targeting ~110 total for AISA over 30 days)
            installs = 3 if app["app_code"] == "aisa" else 2
            if i % 3 == 0 and app["app_code"] == "aisa":
                installs += 1
            uninstalls = int(installs * 0.2)
            
            doc = {
                "_id": generate_uuid(),
                "app_code": app["app_code"],
                "package_name": app["package_name"],
                "metric_date": date_str,
                "dimension_type": "overview",
                "dimension_value": None,
                "dimension_value_normalized": "__overall__",
                "daily_device_installs": installs,
                "daily_device_uninstalls": uninstalls,
                "daily_device_upgrades": 0,
                "daily_user_installs": installs,
                "daily_user_uninstalls": uninstalls,
                "current_device_installs": 1000 + installs * i,
                "installs_on_active_devices": 950 + installs * i,
                "current_user_installs": 1050 + installs * i,
                "total_user_installs": 2000 + installs * i * 2,
                "net_daily_device_installs": installs - uninstalls,
                "net_daily_user_installs": installs - uninstalls,
                "source_file_id": "seed_data",
                "source_generation": "1"
            }
            docs.append(doc)
            
    if docs:
        db["play_install_metrics"].insert_many(docs)
        print(f"Inserted {len(docs)} sample records into MongoDB.")

if __name__ == "__main__":
    main()
