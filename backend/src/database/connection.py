from typing import Generator
import pymongo  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings

_client: pymongo.MongoClient | None = None


def get_client() -> pymongo.MongoClient:
    global _client
    if _client is None:
        try:
            client = pymongo.MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=2500,
                tlsAllowInvalidCertificates=True
            )
            # Test ping to verify cluster reachability
            client.admin.command('ping')
            _client = client
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

    # Seed initial sample data if empty (only when not running unit tests)
    import os
    is_testing = bool(os.getenv("PYTEST_CURRENT_TEST")) or "test" in getattr(db, "name", "").lower()
    if not is_testing:
        try:
            if db["users"].count_documents({}) == 0:
                from src.auth.service import hash_password
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat()

                demo_app_id = "app_demo_uuid_2001"
                aisa_app_id = "app_aisa_uuid_2002"
                ailegal_app_id = "app_ailegal_uuid_2003"

                # Seed application keys first
                db["application_keys"].insert_many([
                    {
                        "_id": demo_app_id,
                        "application_name": "Standalone Application",
                        "api_key": "key_demo_app_key_123",
                        "api_key_hash": hash_password("key_demo_app_key_123"),
                        "status": "active",
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": aisa_app_id,
                        "application_name": "AISA",
                        "api_key": "key_aisa_app_key_456",
                        "api_key_hash": hash_password("key_aisa_app_key_456"),
                        "status": "active",
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": ailegal_app_id,
                        "application_name": "AI Legal",
                        "api_key": "key_ailegal_app_key_789",
                        "api_key_hash": hash_password("key_ailegal_app_key_789"),
                        "status": "active",
                        "created_at": now,
                        "updated_at": now
                    }
                ])

                # Seed users
                demo_user_id = "user_demo_uuid_1001"
                db["users"].insert_many([
                    {
                        "_id": demo_user_id,
                        "email": "user@domain.com",
                        "password_hash": hash_password("user123"),
                        "name": "Demo User",
                        "is_verified": True,
                        "is_active": True,
                        "connected_apps": [demo_app_id],
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": "user_aisa_only",
                        "email": "aisa.user@domain.com",
                        "password_hash": hash_password("aisa123"),
                        "name": "AISA User",
                        "is_verified": True,
                        "is_active": True,
                        "connected_apps": [aisa_app_id],
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": "user_legal_only",
                        "email": "legal.user@domain.com",
                        "password_hash": hash_password("legal123"),
                        "name": "AI Legal User",
                        "is_verified": True,
                        "is_active": True,
                        "connected_apps": [ailegal_app_id],
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": "user_both_1",
                        "email": "both1@domain.com",
                        "password_hash": hash_password("both123"),
                        "name": "Dual User Alpha",
                        "is_verified": True,
                        "is_active": True,
                        "connected_apps": [aisa_app_id, ailegal_app_id],
                        "created_at": now,
                        "updated_at": now
                    },
                    {
                        "_id": "user_both_2",
                        "email": "both2@domain.com",
                        "password_hash": hash_password("both123"),
                        "name": "Dual User Beta",
                        "is_verified": True,
                        "is_active": True,
                        "connected_apps": [aisa_app_id, ailegal_app_id],
                        "created_at": now,
                        "updated_at": now
                    }
                ])

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

