import uuid
from datetime import datetime, timezone
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


class ApplicationKey(MongoModel):
    @classmethod
    def create_dict(
        cls,
        application_name: str,
        api_key_hash: str,
        status: str = "active",
        key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "_id": key_id or generate_uuid(),
            "application_name": application_name,
            "api_key_hash": api_key_hash,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }

    @property
    def application_name(self) -> str:
        return self._data.get("application_name", "")

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
