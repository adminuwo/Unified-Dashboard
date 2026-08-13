import random
from datetime import datetime, timezone, timedelta
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db, init_db
from src.database.models import (
    ApplicationKey,
    ChatTrackingEntry,
    AppDownloadEntry,
    LogEntry,
    User,
    generate_uuid,
    utc_now
)
from src.auth.service import hash_password


def seed_multi_app_telemetry(db: Database):
    """Seed rich historical telemetry data across all 5 applications for live dashboard analytics."""
    print("[seeder] Starting multi-tenant telemetry data seeding...")

    apps_info = [
        {"code": "ailegal", "name": "AI Legal", "key": "key_ailegal_live_master_2026", "app_id": "app_key_ailegal_1001"},
        {"code": "aisa", "name": "AISA Assistant", "key": "key_aisa_live_master_2026", "app_id": "app_key_aisa_2001"},
        {"code": "aiads", "name": "AI Ads Generator", "key": "key_aiads_live_master_2026", "app_id": "app_key_aiads_3001"},
        {"code": "uwoconnect", "name": "UWO Connect", "key": "key_uwoconnect_live_master_2026", "app_id": "app_key_uwoconnect_4001"},
        {"code": "efvframework", "name": "EFV Framework", "key": "key_efvframework_live_master_2026", "app_id": "app_key_efvframework_5001"},
    ]

    models_list = ["gpt-4o", "claude-3-5", "gemini-1.5", "llama-3-70b"]
    platforms_list = ["android", "ios", "windows", "web_pwa"]
    countries_list = ["IN", "US", "GB", "DE", "CA", "AU"]

    # 1. Seed 50+ AI Chat Tracking Sessions
    db["chat_tracking"].delete_many({})
    chat_entries = []
    for _ in range(60):
        app = random.choice(apps_info)
        model = random.choice(models_list)
        prompt_tokens = random.randint(50, 600)
        completion_tokens = random.randint(100, 1200)
        total_tokens = prompt_tokens + completion_tokens
        latency = round(random.uniform(85.0, 450.0), 2)
        sess_id = f"sess_{generate_uuid()[:8]}"

        created_time = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 120))

        entry_dict = ChatTrackingEntry.create_dict(
            application_id=app["app_id"],
            app_code=app["code"],
            session_id=sess_id,
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
            user_id=f"usr_demo_{random.randint(100, 999)}"
        )
        entry_dict["created_at"] = created_time.isoformat()
        chat_entries.append(entry_dict)

    db["chat_tracking"].insert_many(chat_entries)
    print(f"[seeder] Seeded {len(chat_entries)} AI chat tracking entries.")

    # 2. Seed 120+ App Download & Install Events
    db["app_downloads"].delete_many({})
    download_entries = []
    for _ in range(120):
        app = random.choice(apps_info)
        platform = random.choice(platforms_list)
        country = random.choice(countries_list)
        version = random.choice(["1.0.0", "1.2.0", "2.0.1", "2.1.5"])

        created_time = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168))

        entry_dict = AppDownloadEntry.create_dict(
            application_id=app["app_id"],
            app_code=app["code"],
            platform=platform,
            version=version,
            ip_country=country,
            user_id=f"usr_demo_{random.randint(100, 999)}"
        )
        entry_dict["created_at"] = created_time.isoformat()
        download_entries.append(entry_dict)

    db["app_downloads"].insert_many(download_entries)
    print(f"[seeder] Seeded {len(download_entries)} app download entries.")

    # 3. Seed Central Application Security & Error Logs with Redacted Tokens
    db["logs"].delete_many({})
    log_samples = [
        ("ERROR", "AUTH_FAILURE", "Authentication failed for user user_99@domain.com with token Bearer [REDACTED_JWT]"),
        ("WARN", "RATE_LIMIT_EXCEEDED", "Rate limit exceeded for app key_[REDACTED_API_KEY] on endpoint /api/v1/generate"),
        ("INFO", "USER_LOGIN_SUCCESS", "User usr_demo_204 successfully authenticated via UWO SSO"),
        ("CRITICAL", "DATABASE_TIMEOUT", "Connection pool exhausted during peak request volume; reconnected successfully"),
        ("ERROR", "PAYMENT_WEBHOOK_RETRY", "Stripe payment verification retry attempt 2 for charge ch_live_[REDACTED_SECRET]"),
        ("WARN", "DEPRECATED_API_CALL", "Client invoked legacy v1 chat endpoint; auto-redirected to v2"),
    ]

    log_entries = []
    for _ in range(35):
        app = random.choice(apps_info)
        level, event, msg = random.choice(log_samples)
        created_time = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))

        log_dict = LogEntry.create_dict(
            application_id=app["app_id"],
            level=level,
            event=event,
            message=msg,
            user_id=f"usr_demo_{random.randint(100, 999)}",
            extra_metadata={"app_code": app["code"], "environment": "production"}
        )
        log_dict["app_code"] = app["code"]
        log_dict["created_at"] = created_time.isoformat()
        log_entries.append(log_dict)

    db["logs"].insert_many(log_entries)
    print(f"[seeder] Seeded {len(log_entries)} central security log entries.")

    # 4. Seed Subscriptions and Payments (Revenue in ₹ INR)
    db["subscriptions"].delete_many({})
    db["payments"].delete_many({})

    demo_subscriptions = [
        {"_id": "sub_pro_1001", "user_id": "usr_demo_101", "product_id": "ailegal_pro", "plan_id": "pro_monthly", "status": "active", "created_at": utc_now()},
        {"_id": "sub_pro_1002", "user_id": "usr_demo_102", "product_id": "aisa_enterprise", "plan_id": "enterprise_annual", "status": "active", "created_at": utc_now()},
        {"_id": "sub_pro_1003", "user_id": "usr_demo_103", "product_id": "aiads_agency", "plan_id": "agency_monthly", "status": "active", "created_at": utc_now()},
        {"_id": "sub_pro_1004", "user_id": "usr_demo_104", "product_id": "uwoconnect_starter", "plan_id": "starter_annual", "status": "active", "created_at": utc_now()},
        {"_id": "sub_pro_1005", "user_id": "usr_demo_105", "product_id": "efv_developer", "plan_id": "dev_monthly", "status": "active", "created_at": utc_now()},
    ]
    db["subscriptions"].insert_many(demo_subscriptions)

    demo_payments = [
        {"_id": "pay_1001", "user_id": "usr_demo_101", "product_id": "ailegal_pro", "amount": 2499.0, "currency": "INR", "status": "succeeded", "provider_payment_id": "pay_stripe_1001", "created_at": utc_now()},
        {"_id": "pay_1002", "user_id": "usr_demo_102", "product_id": "aisa_enterprise", "amount": 14999.0, "currency": "INR", "status": "succeeded", "provider_payment_id": "pay_stripe_1002", "created_at": utc_now()},
        {"_id": "pay_1003", "user_id": "usr_demo_103", "product_id": "aiads_agency", "amount": 4999.0, "currency": "INR", "status": "succeeded", "provider_payment_id": "pay_stripe_1003", "created_at": utc_now()},
        {"_id": "pay_1004", "user_id": "usr_demo_104", "product_id": "uwoconnect_starter", "amount": 999.0, "currency": "INR", "status": "succeeded", "provider_payment_id": "pay_stripe_1004", "created_at": utc_now()},
        {"_id": "pay_1005", "user_id": "usr_demo_105", "product_id": "efv_developer", "amount": 1999.0, "currency": "INR", "status": "succeeded", "provider_payment_id": "pay_stripe_1005", "created_at": utc_now()},
    ]
    db["payments"].insert_many(demo_payments)
    print("[seeder] Seeded revenue payments (INR 25,495.00 total) and active subscriptions.")


    print("[seeder] Multi-tenant telemetry seeding complete!")



if __name__ == "__main__":
    db = get_db().__next__()
    seed_multi_app_telemetry(db)
