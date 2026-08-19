from typing import Generator, Dict, Any
import pymongo  # type: ignore
from pymongo.database import Database  # type: ignore

from src.config.settings import settings

_client: pymongo.MongoClient | None = None
_last_db_error: str | None = None
_is_mongomock: bool = False


def get_client() -> pymongo.MongoClient:
    global _client, _last_db_error, _is_mongomock
    if _client is None:
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
            client = pymongo.MongoClient(settings.MONGODB_URL, **mongo_kwargs)

            # Test ping to verify cluster reachability
            client.admin.command('ping')
            _client = client
            _is_mongomock = False
            _last_db_error = None
            print("[Database Connection] Connected successfully to MongoDB Atlas cluster.")
        except Exception as e:
            _last_db_error = str(e)
            _is_mongomock = True
            print(f"[Database Connection] MongoDB Atlas cluster unreachable ({e}). Falling back to in-memory database.")
            import mongomock
            _client = mongomock.MongoClient()
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


# Seeding of admin users and application keys has been removed per request.





def check_db_connection(db: Database) -> str:
    """Verify database connectivity."""
    global _is_mongomock, _last_db_error
    if _is_mongomock:
        err_msg = f" (error: {_last_db_error})" if _last_db_error else ""
        return f"in-memory fallback{err_msg}"
    try:
        db.command("ping")
        return "connected (Atlas)"
    except Exception as e:
        return f"error: {str(e)}"


