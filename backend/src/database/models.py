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


VALID_APP_CODES = {"ailegal", "aisa", "aiads", "uwoconnect", "efvframework", "uwo", "aimall", "general", "other"}



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


class RevenueTransaction(MongoModel):
    @classmethod
    def create_dict(
        cls,
        source: str,
        provider: str,
        product_code: str,
        platform: str,
        external_transaction_id: str,
        external_order_id: Optional[str] = None,
        transaction_type: str = "payment",
        gross_amount: float = 0.0,
        tax_amount: float = 0.0,
        fee_amount: float = 0.0,
        refund_amount: float = 0.0,
        net_amount: float = 0.0,
        currency: str = "INR",
        reporting_amount: Optional[float] = None,
        reporting_currency: str = "INR",
        exchange_rate: float = 1.0,
        transaction_date: Optional[datetime] = None,
        country: str = "IN",
        status: str = "completed",
        is_test: bool = False,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        raw_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tx_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        dt = transaction_date or now
        rep_amt = reporting_amount if reporting_amount is not None else (gross_amount * exchange_rate)
        return {
            "_id": tx_id or generate_uuid(),
            "source": source.lower(),
            "provider": provider.lower(),
            "product_code": product_code.lower(),
            "platform": platform.lower(),
            "external_transaction_id": external_transaction_id,
            "external_order_id": external_order_id,
            "transaction_type": transaction_type.lower(),
            "gross_amount": float(gross_amount),
            "tax_amount": float(tax_amount),
            "fee_amount": float(fee_amount),
            "refund_amount": float(refund_amount),
            "net_amount": float(net_amount),
            "currency": currency.upper(),
            "reporting_amount": float(rep_amt),
            "reporting_currency": reporting_currency.upper(),
            "exchange_rate": float(exchange_rate),
            "transaction_date": dt,
            "country": country.upper(),
            "status": status.lower(),
            "is_test": is_test,
            "customer_id": customer_id,
            "customer_email": customer_email,
            "subscription_id": subscription_id,
            "plan_id": plan_id,
            "raw_reference": raw_reference,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }


class RevenueRawEvent(MongoModel):
    @classmethod
    def create_dict(
        cls,
        provider: str,
        product_code: str,
        external_id: str,
        event_type: str,
        payload: Dict[str, Any],
        file_hash: Optional[str] = None,
        processed: bool = True,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": event_id or generate_uuid(),
            "provider": provider.lower(),
            "product_code": product_code.lower(),
            "external_id": external_id,
            "event_type": event_type.lower(),
            "payload": payload,
            "file_hash": file_hash,
            "received_at": now,
            "processed": processed,
            "created_at": now,
        }


class RevenueSyncJob(MongoModel):
    @classmethod
    def create_dict(
        cls,
        provider: str,
        product_code: str,
        sync_type: str = "realtime",
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        status: str = "running",
        records_processed: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        error_count: int = 0,
        error_message: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": job_id or generate_uuid(),
            "provider": provider.lower(),
            "product_code": product_code.lower(),
            "sync_type": sync_type.lower(),
            "started_at": started_at or now,
            "completed_at": completed_at,
            "status": status.lower(),
            "records_processed": records_processed,
            "records_created": records_created,
            "records_updated": records_updated,
            "error_count": error_count,
            "error_message": error_message,
            "created_at": now,
            "updated_at": now,
        }


class ProductRegistryEntry(MongoModel):
    @classmethod
    def create_dict(
        cls,
        product_code: str,
        name: str,
        status: str = "active",
        platforms: Optional[List[str]] = None,
        google_play: Optional[Dict[str, Any]] = None,
        app_store: Optional[Dict[str, Any]] = None,
        razorpay: Optional[Dict[str, Any]] = None,
        stripe: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": entry_id or product_code.lower(),
            "product_code": product_code.lower(),
            "name": name,
            "status": status.lower(),
            "platforms": platforms or ["web"],
            "google_play": google_play or {"enabled": False},
            "app_store": app_store or {"enabled": False},
            "razorpay": razorpay or {"enabled": True},
            "stripe": stripe or {"enabled": False},
            "created_at": now,
            "updated_at": now,
        }


class RevenueReconciliation(MongoModel):
    @classmethod
    def create_dict(
        cls,
        provider: str,
        product_code: str,
        period: str,
        provider_reported_amount: float,
        database_amount: float,
        difference: float,
        status: str = "RECONCILED",
        currency: str = "INR",
        notes: Optional[str] = None,
        recon_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": recon_id or generate_uuid(),
            "provider": provider.lower(),
            "product_code": product_code.lower(),
            "period": period,
            "provider_reported_amount": float(provider_reported_amount),
            "database_amount": float(database_amount),
            "difference": float(difference),
            "status": status,
            "currency": currency.upper(),
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }


class RevenueAuditLog(MongoModel):
    @classmethod
    def create_dict(
        cls,
        admin_user: str,
        action: str,
        provider: Optional[str] = None,
        product_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        log_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": log_id or generate_uuid(),
            "admin_user": admin_user,
            "action": action,
            "provider": provider,
            "product_code": product_code,
            "ip_address": ip_address,
            "result": result,
            "details": details or {},
            "created_at": now,
        }
