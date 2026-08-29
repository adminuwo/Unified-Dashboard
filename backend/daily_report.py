#!/usr/bin/env python3
"""
Daily Report Generator - Unified Dashboard
Generates a comprehensive daily summary report from live database data.
"""
import datetime
from pymongo import MongoClient

def format_currency(amount):
    return f"Rs.{amount:,.2f}"

def main():
    today = datetime.datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    report_date = today.strftime("%d %B %Y")
    
    client = MongoClient('mongodb+srv://admin_db_user:uSYUbw06q4coR6Nv@unified-dashboard.wisisoq.mongodb.net/?appName=Unified-Dashboard')
    db = client['unified_service_db']

    # ---- Google Play (Android) ----
    aisa_android = db.play_install_metrics.find_one(
        {'app_code': 'aisa', 'dimension_type': 'overview'},
        sort=[('metric_date', -1)]
    ) or {}
    ailegal_android = db.play_install_metrics.find_one(
        {'app_code': 'ailegal', 'dimension_type': 'overview'},
        sort=[('metric_date', -1)]
    ) or {}

    aisa_android_installs = aisa_android.get('total_user_installs') or 0
    aisa_android_devices  = aisa_android.get('installs_on_active_devices') or 0
    ailegal_android_installs = ailegal_android.get('total_user_installs') or 0
    ailegal_android_devices  = ailegal_android.get('installs_on_active_devices') or 0

    # ---- Apple App Store (iOS) ----
    aisa_ios = {}
    ailegal_ios = {}
    for rec in db.app_store_metrics.find({'app_code': 'aisa', 'platform': 'ios'}):
        for k in ['first_time_downloads', 'redownloads', 'total_downloads', 'impressions', 'page_views', 'updates', 'in_app_purchases']:
            aisa_ios[k] = aisa_ios.get(k, 0) + (rec.get(k) or 0)
        aisa_ios['proceeds_usd'] = aisa_ios.get('proceeds_usd', 0.0) + (rec.get('proceeds_usd') or 0.0)

    for rec in db.app_store_metrics.find({'app_code': 'ailegal', 'platform': 'ios'}):
        for k in ['first_time_downloads', 'redownloads', 'total_downloads', 'impressions', 'page_views', 'updates', 'in_app_purchases']:
            ailegal_ios[k] = ailegal_ios.get(k, 0) + (rec.get(k) or 0)
        ailegal_ios['proceeds_usd'] = ailegal_ios.get('proceeds_usd', 0.0) + (rec.get('proceeds_usd') or 0.0)

    # ---- Revenue ----
    revenue_total = 0.0
    for tx in db.revenue_transactions.find({}):
        revenue_total += tx.get('gross_amount') or 0.0

    # ---- Users ----
    total_users = db.users.count_documents({})
    aisa_users = db.users.count_documents({'connected_apps': {'$regex': 'aisa', '$options': 'i'}})
    ailegal_users = db.users.count_documents({'connected_apps': {'$regex': 'ailegal', '$options': 'i'}})

    # ---- Chat / AI Tokens ----
    aisa_prompts  = db.chat_tracking.count_documents({'app_code': 'aisa'})
    ailegal_prompts = db.chat_tracking.count_documents({'app_code': 'ailegal'})

    # ---- Build Report ----
    print("=" * 70)
    print(f"   UNIFIED DASHBOARD - DAILY REPORT")
    print(f"   Date: {report_date}")
    print(f"   Generated: {today.strftime('%H:%M:%S IST')}")
    print("=" * 70)

    print("\n[1] GOOGLE PLAY CONSOLE (Android)")
    print(f"   AISA App:")
    print(f"     Total User Installs    : {aisa_android_installs:,}")
    print(f"     Active Devices         : {aisa_android_devices:,}")
    print(f"     Last Report Date       : {aisa_android.get('metric_date', 'N/A')}")
    print(f"   AI Legal App:")
    print(f"     Total User Installs    : {ailegal_android_installs:,}")
    print(f"     Active Devices         : {ailegal_android_devices:,}")
    print(f"     Last Report Date       : {ailegal_android.get('metric_date', 'N/A')}")
    print(f"\n   Combined Android Total   : {aisa_android_installs + ailegal_android_installs:,}")

    print("\n[2] APPLE APP STORE CONNECT (iOS)")
    print(f"   AISA App (App ID: 6779135418):")
    print(f"     First-Time Downloads   : {aisa_ios.get('first_time_downloads', 0):,}")
    print(f"     Redownloads            : {aisa_ios.get('redownloads', 0):,}")
    print(f"     Total Downloads        : {aisa_ios.get('total_downloads', 0):,}")
    print(f"     Impressions            : {aisa_ios.get('impressions', 0):,}")
    print(f"     Product Page Views     : {aisa_ios.get('page_views', 0):,}")
    print(f"     App Updates            : {aisa_ios.get('updates', 0):,}")
    print(f"     In-App Purchases       : {aisa_ios.get('in_app_purchases', 0):,}")
    print(f"     Developer Proceeds     : ${aisa_ios.get('proceeds_usd', 0.0):.2f}")
    print(f"   AI Legal App (App ID: 6797449251):")
    print(f"     Total Downloads        : {ailegal_ios.get('total_downloads', 0):,}")
    print(f"     Impressions            : {ailegal_ios.get('impressions', 0):,}")
    print(f"\n   Combined iOS Total       : {aisa_ios.get('total_downloads', 0) + ailegal_ios.get('total_downloads', 0):,}")

    total_combined = (aisa_android_installs + ailegal_android_installs +
                      aisa_ios.get('total_downloads', 0) + ailegal_ios.get('total_downloads', 0))
    print(f"\n[3] TOTAL CROSS-PLATFORM DOWNLOADS: {total_combined:,}")
    print(f"   Android (Play Store)     : {aisa_android_installs + ailegal_android_installs:,}")
    print(f"   iOS (App Store)          : {aisa_ios.get('total_downloads', 0) + ailegal_ios.get('total_downloads', 0):,}")

    print(f"\n[4] REVENUE SUMMARY")
    print(f"   Total Gross Revenue      : {format_currency(revenue_total)}")

    print(f"\n[5] USER BASE")
    print(f"   Total Registered Users   : {total_users:,}")
    print(f"   AISA Users               : {aisa_users:,}")
    print(f"   AI Legal Users           : {ailegal_users:,}")

    print(f"\n[6] AI CHAT SESSIONS")
    print(f"   AISA Prompts             : {aisa_prompts:,}")
    print(f"   AI Legal Prompts         : {ailegal_prompts:,}")
    print(f"   Total Prompts            : {aisa_prompts + ailegal_prompts:,}")

    print("\n" + "=" * 70)
    print("   END OF REPORT")
    print("=" * 70)

if __name__ == "__main__":
    main()
