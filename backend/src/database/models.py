import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, List


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoModel:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def id(self) -> str:
        return str(self._data.get("_id") or self._data.get("id"))

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self._data)
        d["id"] = self.id
        return d


class User(MongoModel):
    @classmethod
    def create_dict(
        cls,
        email: str,
        password_hash: str,
        name: str,
        is_verified: bool = False,
        is_active: bool = True,
        user_id: Optional[str] = None,
        connected_apps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": user_id or generate_uuid(),
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "is_verified": is_verified,
            "is_active": is_active,
            "connected_apps": connected_apps or [],
            "created_at": now,
            "updated_at": now,
        }

    @property
    def email(self) -> str:
        return self._data.get("email", "")

    @property
    def connected_apps(self) -> List[str]:
        return self._data.get("connected_apps", [])

    @property
    def password_hash(self) -> str:
        return self._data.get("password_hash", "")

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def is_verified(self) -> bool:
        return self._data.get("is_verified", False)

    @is_verified.setter
    def is_verified(self, val: bool):
        self._data["is_verified"] = val

    @property
    def is_active(self) -> bool:
        return self._data.get("is_active", True)

    @is_active.setter
    def is_active(self, val: bool):
        self._data["is_active"] = val

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()

    @updated_at.setter
    def updated_at(self, val: datetime):
        self._data["updated_at"] = val

    @property
    def subscriptions(self) -> List[Any]:
        return self._data.get("subscriptions", [])


VALID_APP_CODES = {"ailegal", "aisa", "aiads", "uwoconnect", "efvframework", "uwo", "general"}


class ApplicationKey(MongoModel):
    @classmethod
    def create_dict(
        cls,
        application_name: str,
        api_key_hash: str,
        app_code: str = "general",
        status: str = "active",
        key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": key_id or generate_uuid(),
            "application_name": application_name,
            "app_code": app_code.lower(),
            "api_key_hash": api_key_hash,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }

    @property
    def application_name(self) -> str:
        return self._data.get("application_name", "")

    @property
    def app_code(self) -> str:
        return self._data.get("app_code", "general")

    @app_code.setter
    def app_code(self, val: str):
        self._data["app_code"] = val.lower()

    @property
    def api_key_hash(self) -> str:
        return self._data.get("api_key_hash", "")

    @property
    def status(self) -> str:
        return self._data.get("status", "active")

    @status.setter
    def status(self, val: str):
        self._data["status"] = val

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()

    @updated_at.setter
    def updated_at(self, val: datetime):
        self._data["updated_at"] = val


class VerificationToken(MongoModel):
    @classmethod
    def create_dict(
        cls,
        user_id: str,
        token: str,
        expires_at: datetime,
        is_used: bool = False,
        token_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": token_id or generate_uuid(),
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
            "is_used": is_used,
            "created_at": now,
        }

    @property
    def user_id(self) -> str:
        return self._data.get("user_id", "")

    @property
    def token(self) -> str:
        return self._data.get("token", "")

    @property
    def expires_at(self) -> datetime:
        return self._data.get("expires_at") or utc_now()

    @property
    def is_used(self) -> bool:
        return self._data.get("is_used", False)

    @is_used.setter
    def is_used(self, val: bool):
        self._data["is_used"] = val

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()


class Subscription(MongoModel):
    @classmethod
    def create_dict(
        cls,
        user_id: str,
        product_id: str,
        plan_id: str,
        status: str = "active",
        provider: str = "stripe",
        provider_subscription_id: Optional[str] = None,
        sub_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": sub_id or generate_uuid(),
            "user_id": user_id,
            "product_id": product_id,
            "plan_id": plan_id,
            "status": status,
            "provider": provider,
            "provider_subscription_id": provider_subscription_id,
            "created_at": now,
            "updated_at": now,
        }

    @property
    def user_id(self) -> str:
        return self._data.get("user_id", "")

    @property
    def product_id(self) -> str:
        return self._data.get("product_id", "")

    @property
    def plan_id(self) -> str:
        return self._data.get("plan_id", "")

    @plan_id.setter
    def plan_id(self, val: str):
        self._data["plan_id"] = val

    @property
    def status(self) -> str:
        return self._data.get("status", "active")

    @status.setter
    def status(self, val: str):
        self._data["status"] = val

    @property
    def provider(self) -> str:
        return self._data.get("provider", "")

    @property
    def provider_subscription_id(self) -> Optional[str]:
        return self._data.get("provider_subscription_id")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()

    @updated_at.setter
    def updated_at(self, val: datetime):
        self._data["updated_at"] = val


class Payment(MongoModel):
    @classmethod
    def create_dict(
        cls,
        user_id: str,
        product_id: str,
        plan_id: str,
        amount: float,
        currency: str = "INR",
        status: str = "pending",
        provider: str = "razorpay",
        provider_payment_id: Optional[str] = None,
        payment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": payment_id or generate_uuid(),
            "user_id": user_id,
            "product_id": product_id,
            "plan_id": plan_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "provider": provider,
            "provider_payment_id": provider_payment_id,
            "created_at": now,
            "updated_at": now,
        }

    @property
    def user_id(self) -> str:
        return self._data.get("user_id", "")

    @property
    def product_id(self) -> str:
        return self._data.get("product_id", "")

    @property
    def plan_id(self) -> str:
        return self._data.get("plan_id", "")

    @property
    def amount(self) -> float:
        return float(self._data.get("amount", 0.0))

    @property
    def currency(self) -> str:
        return self._data.get("currency", "INR")

    @property
    def status(self) -> str:
        return self._data.get("status", "pending")

    @status.setter
    def status(self, val: str):
        self._data["status"] = val

    @property
    def provider(self) -> str:
        return self._data.get("provider", "razorpay")

    @property
    def provider_payment_id(self) -> Optional[str]:
        return self._data.get("provider_payment_id")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()

    @updated_at.setter
    def updated_at(self, val: datetime):
        self._data["updated_at"] = val


class LogEntry(MongoModel):
    @classmethod
    def create_dict(
        cls,
        application_id: str,
        level: str,
        event: str,
        message: str,
        user_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        log_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": log_id or generate_uuid(),
            "application_id": application_id,
            "user_id": user_id,
            "level": level,
            "event": event,
            "message": message,
            "metadata": extra_metadata or {},
            "created_at": now,
        }

    @property
    def application_id(self) -> str:
        return self._data.get("application_id", "")

    @property
    def user_id(self) -> Optional[str]:
        return self._data.get("user_id")

    @property
    def level(self) -> str:
        return self._data.get("level", "")

    @property
    def event(self) -> str:
        return self._data.get("event", "")

    @property
    def message(self) -> str:
        return self._data.get("message", "")

    @property
    def extra_metadata(self) -> Optional[Dict[str, Any]]:
        return self._data.get("metadata")

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._data.get("metadata")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()


class ChatTrackingEntry(MongoModel):
    @classmethod
    def create_dict(
        cls,
        application_id: str,
        app_code: str,
        session_id: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        user_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        calc_total = total_tokens if total_tokens > 0 else (prompt_tokens + completion_tokens)
        return {
            "_id": entry_id or generate_uuid(),
            "application_id": application_id,
            "app_code": app_code.lower(),
            "session_id": session_id,
            "user_id": user_id,
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": calc_total,
            "latency_ms": latency_ms,
            "metadata": extra_metadata or {},
            "created_at": now,
        }

    @property
    def application_id(self) -> str:
        return self._data.get("application_id", "")

    @property
    def app_code(self) -> str:
        return self._data.get("app_code", "")

    @property
    def session_id(self) -> str:
        return self._data.get("session_id", "")

    @property
    def user_id(self) -> Optional[str]:
        return self._data.get("user_id")

    @property
    def model_name(self) -> str:
        return self._data.get("model_name", "unknown")

    @property
    def prompt_tokens(self) -> int:
        return int(self._data.get("prompt_tokens", 0))

    @property
    def completion_tokens(self) -> int:
        return int(self._data.get("completion_tokens", 0))

    @property
    def total_tokens(self) -> int:
        return int(self._data.get("total_tokens", 0))

    @property
    def latency_ms(self) -> float:
        return float(self._data.get("latency_ms", 0.0))

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()


class AppDownloadEntry(MongoModel):
    @classmethod
    def create_dict(
        cls,
        application_id: str,
        app_code: str,
        platform: str,
        version: str = "1.0.0",
        ip_country: str = "IN",
        user_id: Optional[str] = None,
        entry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": entry_id or generate_uuid(),
            "application_id": application_id,
            "app_code": app_code.lower(),
            "platform": platform.lower(),
            "version": version,
            "ip_country": ip_country,
            "user_id": user_id,
            "created_at": now,
        }

    @property
    def application_id(self) -> str:
        return self._data.get("application_id", "")

    @property
    def app_code(self) -> str:
        return self._data.get("app_code", "")

    @property
    def platform(self) -> str:
        return self._data.get("platform", "web")

    @property
    def version(self) -> str:
        return self._data.get("version", "1.0.0")

    @property
    def ip_country(self) -> str:
        return self._data.get("ip_country", "IN")

    @property
    def user_id(self) -> Optional[str]:
        return self._data.get("user_id")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()


PROJECT_MAPPINGS: Dict[str, Dict[str, str]] = {
    "AISA": {
        "project": "AISA",
        "platform": "android",
        "package_name": "com.uwo.aisa",
        "label": "AISA Android App"
    },
    "AI_LEGAL": {
        "project": "AI_LEGAL",
        "platform": "android",
        "package_name": "com.uwo.ailegal",
        "label": "AI Legal Android App"
    }
}


class StoreAnalytics(MongoModel):
    @classmethod
    def create_dict(
        cls,
        project: str,
        platform: str,
        package_name: str,
        date: str,
        metric: str,
        value: int,
        source: str = "google_play_reporting_api",
        record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": record_id or generate_uuid(),
            "project": project,
            "platform": platform,
            "package_name": package_name,
            "date": date,
            "metric": metric,
            "value": value,
            "source": source,
            "created_at": now,
            "updated_at": now,
        }

    @property
    def project(self) -> str:
        return self._data.get("project", "")

    @property
    def platform(self) -> str:
        return self._data.get("platform", "android")

    @property
    def package_name(self) -> str:
        return self._data.get("package_name", "")

    @property
    def date(self) -> str:
        return self._data.get("date", "")

    @property
    def metric(self) -> str:
        return self._data.get("metric", "installs")

    @property
    def value(self) -> int:
        return int(self._data.get("value", 0))

    @property
    def source(self) -> str:
        return self._data.get("source", "google_play_reporting_api")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()


class AnalyticsCache(MongoModel):
    @classmethod
    def create_dict(
        cls,
        cache_key: str,
        data: Any,
        ttl_seconds: int = 3600,
        record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        return {
            "_id": record_id or generate_uuid(),
            "cache_key": cache_key,
            "data": data,
            "updated_at": now,
            "expires_at": expires_at
        }

    @property
    def cache_key(self) -> str:
        return self._data.get("cache_key", "")

    @property
    def data(self) -> Any:
        return self._data.get("data")

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()

    @property
    def expires_at(self) -> datetime:
        return self._data.get("expires_at") or utc_now()


class EventLog(MongoModel):
    @classmethod
    def create_dict(
        cls,
        app_code: str,
        event_type: str,
        path: Optional[str] = None,
        visitor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        device: str = "desktop",
        browser: str = "other",
        os_name: str = "other",
        country: str = "IN",
        event_name: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[float] = None,
        user_id: Optional[str] = None,
        entry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": entry_id or generate_uuid(),
            "app_code": app_code.lower(),
            "event_type": event_type.lower(),
            "path": path or "/",
            "visitor_id": visitor_id or generate_uuid(),
            "session_id": session_id or generate_uuid(),
            "device": device.lower(),
            "browser": browser,
            "os": os_name,
            "country": country.upper(),
            "event_name": event_name,
            "event_data": event_data or {},
            "duration_seconds": duration_seconds or 0.0,
            "user_id": user_id,
            "created_at": now,
        }

    @property
    def app_code(self) -> str:
        return self._data.get("app_code", "general")

    @property
    def event_type(self) -> str:
        return self._data.get("event_type", "pageview")

    @property
    def path(self) -> str:
        return self._data.get("path", "/")

    @property
    def visitor_id(self) -> str:
        return self._data.get("visitor_id", "")

    @property
    def session_id(self) -> str:
        return self._data.get("session_id", "")

    @property
    def device(self) -> str:
        return self._data.get("device", "desktop")

    @property
    def browser(self) -> str:
        return self._data.get("browser", "other")

    @property
    def os(self) -> str:
        return self._data.get("os", "other")

    @property
    def country(self) -> str:
        return self._data.get("country", "IN")

    @property
    def event_name(self) -> Optional[str]:
        return self._data.get("event_name")

    @property
    def event_data(self) -> Dict[str, Any]:
        return self._data.get("event_data", {})

    @property
    def duration_seconds(self) -> float:
        return float(self._data.get("duration_seconds", 0.0))

    @property
    def user_id(self) -> Optional[str]:
        return self._data.get("user_id")

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()


class DailyMetric(MongoModel):
    @classmethod
    def create_dict(
        cls,
        date_str: str,
        app_code: str,
        platform: str,
        active_users: int = 0,
        pageviews: int = 0,
        sessions: int = 0,
        installs: int = 0,
        uninstalls: int = 0,
        revenue: float = 0.0,
        avg_latency_ms: float = 0.0,
        error_rate: float = 0.0,
        metric_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": metric_id or generate_uuid(),
            "date": date_str,
            "app_code": app_code.lower(),
            "platform": platform.lower(),
            "active_users": active_users,
            "pageviews": pageviews,
            "sessions": sessions,
            "installs": installs,
            "uninstalls": uninstalls,
            "revenue": float(revenue),
            "avg_latency_ms": float(avg_latency_ms),
            "error_rate": float(error_rate),
            "created_at": now,
            "updated_at": now,
        }

    @property
    def date(self) -> str:
        return self._data.get("date", "")

    @property
    def app_code(self) -> str:
        return self._data.get("app_code", "general")

    @property
    def platform(self) -> str:
        return self._data.get("platform", "web")

    @property
    def active_users(self) -> int:
        return int(self._data.get("active_users", 0))

    @property
    def pageviews(self) -> int:
        return int(self._data.get("pageviews", 0))

    @property
    def sessions(self) -> int:
        return int(self._data.get("sessions", 0))

    @property
    def installs(self) -> int:
        return int(self._data.get("installs", 0))

    @property
    def uninstalls(self) -> int:
        return int(self._data.get("uninstalls", 0))

    @property
    def revenue(self) -> float:
        return float(self._data.get("revenue", 0.0))

    @property
    def avg_latency_ms(self) -> float:
        return float(self._data.get("avg_latency_ms", 0.0))

    @property
    def error_rate(self) -> float:
        return float(self._data.get("error_rate", 0.0))

    @property
    def created_at(self) -> datetime:
        return self._data.get("created_at") or utc_now()

    @property
    def updated_at(self) -> datetime:
        return self._data.get("updated_at") or utc_now()
