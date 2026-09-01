from typing import Generator, Dict, Any
import pymongo  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings

_client: pymongo.MongoClient | None = None
_last_db_error: str | None = None


def get_client() -> pymongo.MongoClient:
    global _client, _last_db_error
    import os
    if settings.ENVIRONMENT == "testing" or os.environ.get("ENVIRONMENT") == "testing":
        if _client is None:
            try:
                import mongomock  # type: ignore
                _client = mongomock.MongoClient()
                _last_db_error = None
            except ImportError:
                pass
        return _client

    if _client is None:
        if settings.ENVIRONMENT.lower() == "testing":
            import mongomock  # type: ignore
            _client = mongomock.MongoClient()
            return _client

        try:
            mongo_kwargs: Dict[str, Any] = {
                "serverSelectionTimeoutMS": 10000,
                "tlsAllowInvalidCertificates": True,
            }
            try:
                import certifi
                mongo_kwargs["tlsCAFile"] = certifi.where()
            except ImportError:
                pass
            try:
                import dns.resolver
                # Configure dnspython to use public DNS servers to resolve MongoDB SRV records reliably
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = ['8.8.8.8', '1.1.1.1']
                dns.resolver.default_resolver = resolver
                print("[Database Connection] Configured public DNS resolvers for MongoDB SRV resolution.")
            except Exception as dns_err:
                print(f"[Database Connection Warning] Failed to configure dns.resolver: {dns_err}")
                
            client = pymongo.MongoClient(settings.MONGODB_URL, **mongo_kwargs)

            # Test ping to verify cluster reachability
            client.admin.command('ping')
            _client = client
            _last_db_error = None
            print("[Database Connection] Connected successfully to MongoDB Atlas cluster.")
        except Exception as e:
            _last_db_error = str(e)
            err_msg = str(e)
            if "TLSV1_ALERT_INTERNAL_ERROR" in err_msg or "SSL handshake failed" in err_msg:
                print("\n" + "="*70)
                print("[MongoDB Atlas Connection Notice]")
                print("Your IP address is not whitelisted in MongoDB Atlas.")
                print("To fix this:")
                print("1. Go to https://cloud.mongodb.com")
                print("2. Navigate to 'Network Access' -> 'IP Access List'")
                print("3. Click 'Add IP Address' -> Add Current IP or 0.0.0.0/0 (Allow Anywhere)")
                print("="*70 + "\n")
            print(f"[Database Connection ERROR] Failed to connect to MongoDB Atlas cluster: {e}")
            if settings.ENVIRONMENT.lower() != "production":
                print("[Database Connection] Falling back to local in-memory database for development mode.")
                try:
                    import mongomock  # type: ignore
                    _client = mongomock.MongoClient()
                    return _client
                except Exception:
                    pass
            raise RuntimeError(f"Critical Database Error: Unable to connect to MongoDB Atlas cluster (Check Atlas Network Access / IP Whitelist): {e}")
    return _client




def get_db_instance() -> Database:
    """Return Database instance directly for background workers and schedulers."""
    client = get_client()
    return client[settings.MONGODB_DB_NAME]


def get_db() -> Generator[Database, None, None]:
    """Dependency for obtaining MongoDB database per request."""
    client = get_client()
    db = client[settings.MONGODB_DB_NAME]
    try:
        yield db
    finally:
        pass


def init_db(db: Database | None = None):
    """Initialize database collection indexes."""

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
        db["store_analytics"].create_index([
            ("project", 1),
            ("platform", 1),
            ("package_name", 1),
            ("date", 1),
            ("metric", 1)
        ], unique=True)
        db["store_analytics"].create_index("project")
        db["store_analytics"].create_index("date")

        db["analytics_cache"].create_index("cache_key", unique=True)
        db["analytics_cache"].create_index("expires_at")

        db["events"].create_index([("created_at", pymongo.DESCENDING)])
        db["events"].create_index("app_code")
        db["events"].create_index("event_type")
        db["events"].create_index("visitor_id")
        db["events"].create_index("session_id")

        db["metrics_daily"].create_index([("date", 1), ("app_code", 1), ("platform", 1)], unique=True)
    except Exception as e:
        print(f"[init_db] Note: Index creation deferred or skipped: {e}")

    # Ensure platform master keys and whitelisted domains exist in application_keys
    try:
        import hashlib
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        master_keys = [
            {
                "_id": "app_aimall_master",
                "application_name": "AI Mall (aimall24.com)",
                "app_code": "aimall",
                "api_key_hash": hashlib.sha256(b"key_aimall_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["aimall24.com", "www.aimall24.com", "localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_aisa_master",
                "application_name": "AISA (aisa24.com)",
                "app_code": "aisa",
                "api_key_hash": hashlib.sha256(b"key_aisa_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["aisa24.com", "beta.aisa24.com", "www.aisa24.com", "localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_ailegal_master",
                "application_name": "AI Legal",
                "app_code": "ailegal",
                "api_key_hash": hashlib.sha256(b"key_ailegal_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_uwoconnect_master",
                "application_name": "UWO Connect",
                "app_code": "uwoconnect",
                "api_key_hash": hashlib.sha256(b"key_uwoconnect_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["uwo24.com", "admin.uwo24.com", "localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_efv_master",
                "application_name": "EFV Framework",
                "app_code": "efvframework",
                "api_key_hash": hashlib.sha256(b"key_efv_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_yugamc_master",
                "application_name": "Yuga MC",
                "app_code": "yugamc",
                "api_key_hash": hashlib.sha256(b"key_yugamc_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["yugamc.com", "localhost"],
                "created_at": now,
                "updated_at": now
            },
            {
                "_id": "app_uwo_master",
                "application_name": "UWO Central",
                "app_code": "uwo",
                "api_key_hash": hashlib.sha256(b"key_uwo_live_master_2026").hexdigest(),
                "status": "active",
                "allowed_domains": ["uwo24.com", "admin.uwo24.com", "localhost"],
                "created_at": now,
                "updated_at": now
            }
        ]
        
        for k in master_keys:
            db["application_keys"].update_one(
                {"_id": k["_id"]},
                {"$setOnInsert": k, "$set": {"status": "active", "allowed_domains": k["allowed_domains"], "updated_at": now}},
                upsert=True
            )
    except Exception as e:
        print(f"[init_db] Note: Master keys registration: {e}")





def check_db_connection(db: Database) -> str:
    """Verify database connectivity."""
    try:
        db.command("ping")
        return "connected (Atlas)"
    except Exception as e:
        return f"error: {str(e)}"


