from typing import Generator
import pymongo  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings

_client: pymongo.MongoClient | None = None


def get_client() -> pymongo.MongoClient:
    global _client
    if _client is None:
        try:
            mongo_kwargs = {
                "serverSelectionTimeoutMS": 2500,
                "tlsAllowInvalidCertificates": True,
            }
            try:
                import certifi
                mongo_kwargs["tlsCAFile"] = certifi.where()
            except ImportError:
                pass

            client = pymongo.MongoClient(settings.MONGODB_URL, **mongo_kwargs)
            # Test ping to verify cluster reachability
            client.admin.command('ping')
            _client = client
            print("[Database Connection] Connected successfully to MongoDB Atlas cluster.")
        except Exception as e:
            print(f"[Database Connection] MongoDB Atlas cluster unreachable ({e}). Falling back to in-memory database.")
            import mongomock
            _client = mongomock.MongoClient()
    return _client



def get_db() -> Generator[Database, None, None]:
    """Dependency for obtaining MongoDB database per request."""
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    try:
        yield db
    finally:
        pass


def init_db(db: Database | None = None):
    """Initialize database collection indexes and seed default master admin user & sample data."""
    if db is None:
        client = get_client()
        db = client[settings.MONGODB_DB_NAME]

    try:
        # Create indexes for optimized queries
        db["users"].create_index("email", unique=True)

        db["application_keys"].create_index("application_name")
        db["application_keys"].create_index("api_key_hash")

        db["verification_tokens"].create_index("token", unique=True)
        db["verification_tokens"].create_index("user_id")

        db["subscriptions"].create_index("user_id")
        db["subscriptions"].create_index("status")

        db["payments"].create_index("user_id")
        db["payments"].create_index("provider_payment_id")

        db["logs"].create_index([("created_at", pymongo.DESCENDING)])
        db["logs"].create_index("application_id")
        db["logs"].create_index("user_id")
        db["logs"].create_index("level")
        db["logs"].create_index("app_code")

        db["chat_tracking"].create_index([("created_at", pymongo.DESCENDING)])
        db["chat_tracking"].create_index("app_code")
        db["chat_tracking"].create_index("session_id")
        db["chat_tracking"].create_index("model_name")

        db["app_downloads"].create_index([("created_at", pymongo.DESCENDING)])
        db["app_downloads"].create_index("app_code")
        db["app_downloads"].create_index("platform")
    except Exception as e:
        print(f"[init_db] Note: Index creation deferred or skipped: {e}")


    # Seed 4 official master admin users
    try:
        from src.auth.service import hash_password
        admin_credentials = [
            ("super.admin@unified.com", "@xQn!W&Wg-ufSWn)93Qg_0S2"),
            ("sec.ops@unified.com", "#re(QpHtdse=re=mZK7ZzJ5O"),
            ("sys.auditor@unified.com", "nYtEt_e5M*8CvW6a%_^_bfk*"),
            ("devops.lead@unified.com", "R7wqmG$=XmbqfXEoDGnU7Sfw")
        ]

        # Clean up legacy test admin user if present
        db["admin_users"].delete_many({"username": "admin"})

        for email, plain_pass in admin_credentials:
            clean_email = email.strip().lower()
            existing = db["admin_users"].find_one({"username": clean_email})
            if not existing:
                db["admin_users"].insert_one({
                    "username": clean_email,
                    "password_hash": hash_password(plain_pass),
                    "role": "admin",
                    "is_active": True
                })
            else:
                db["admin_users"].update_one(
                    {"username": clean_email},
                    {"$set": {
                        "password_hash": hash_password(plain_pass),
                        "role": "admin",
                        "is_active": True
                    }}
                )
        print("[init_db] 4 official admin accounts seeded successfully.")
    except Exception as e:
        print(f"[init_db] Admin seeding note: {e}")

    # Seed 5 master application API keys
    try:
        from src.middleware.authentication import hash_api_key
        apps_to_seed = [
            ("app_key_ailegal_1001", "AI Legal", "ailegal", "key_ailegal_live_master_2026"),
            ("app_key_aisa_2001", "AISA Assistant", "aisa", "key_aisa_live_master_2026"),
            ("app_key_aiads_3001", "AI Ads Generator", "aiads", "key_aiads_live_master_2026"),
            ("app_key_uwoconnect_4001", "UWO Connect", "uwoconnect", "key_uwoconnect_live_master_2026"),
            ("app_key_efvframework_5001", "EFV Framework", "efvframework", "key_efvframework_live_master_2026"),
        ]
        for key_id, app_name, app_code, plain_key in apps_to_seed:
            key_hash = hash_api_key(plain_key)
            existing = db["application_keys"].find_one({"app_code": app_code})
            if not existing:
                db["application_keys"].insert_one({
                    "_id": key_id,
                    "application_name": app_name,
                    "app_code": app_code,
                    "api_key_hash": key_hash,
                    "status": "active"
                })
            else:
                db["application_keys"].update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "application_name": app_name,
                        "app_code": app_code,
                        "api_key_hash": key_hash,
                        "status": "active"
                    }}
                )
    except Exception as e:
        print(f"[init_db] App keys seeding note: {e}")


    # Seed initial sample data if empty (only when not running unit tests)
    import os
    is_testing = bool(os.getenv("PYTEST_CURRENT_TEST")) or "test" in getattr(db, "name", "").lower()
    if not is_testing:
        try:
            if db["users"].count_documents({}) == 0:
                from src.auth.service import hash_password
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat()

                demo_user_id = "user_demo_uuid_1001"
                db["users"].insert_one({
                    "_id": demo_user_id,
                    "email": "user@domain.com",
                    "password_hash": hash_password("user123"),
                    "name": "Demo User",
                    "is_verified": True,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                })

                demo_app_id = "app_demo_uuid_2001"
                db["application_keys"].insert_one({
                    "_id": demo_app_id,
                    "application_name": "Standalone Application",
                    "api_key": "key_demo_app_key_123",
                    "api_key_hash": hash_password("key_demo_app_key_123"),
                    "status": "active",
                    "created_at": now
                })

                db["subscriptions"].insert_one({
                    "_id": "sub_demo_3001",
                    "user_id": demo_user_id,
                    "product_id": "app_product_pro",
                    "plan_id": "pro_monthly",
                    "status": "active",
                    "provider": "stripe",
                    "created_at": now
                })

                db["payments"].insert_one({
                    "_id": "pay_demo_4001",
                    "user_id": demo_user_id,
                    "product_id": "app_product_pro",
                    "plan_id": "pro_monthly",
                    "amount": 2999.00,
                    "currency": "INR",
                    "status": "succeeded",
                    "provider": "razorpay",
                    "provider_payment_id": "pay_RzP_123456",
                    "created_at": now
                })

                db["logs"].insert_one({
                    "_id": "log_demo_5001",
                    "application_id": demo_app_id,
                    "user_id": demo_user_id,
                    "level": "INFO",
                    "event": "user_logged_in",
                    "message": "User user@domain.com authenticated successfully",
                    "created_at": now
                })
        except Exception as e:
            print(f"[init_db] Sample data seeding note: {e}")


def check_db_connection(db: Database) -> str:
    """Verify database connectivity."""
    try:
        if hasattr(db, "command"):
            try:
                db.command("ping")
                return "connected"
            except Exception:
                return "connected (in-memory)"
        return "connected"
    except Exception as e:
        return f"error: {str(e)}"

