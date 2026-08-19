import pymongo  # type: ignore
from typing import List, Optional, Dict, Any, cast
from datetime import datetime
from pymongo.database import Database  # type: ignore

from fastapi import HTTPException, status  # type: ignore
from src.config.settings import settings
from src.auth.service import verify_password
from src.admin.schemas import (
    PlatformStatsResponse,
    AdminUserListItem,
    AdminPaymentListItem,
    AdminSubscriptionListItem,
    AdminLogListItem
)


def authenticate_admin(db: Database, username: str, password: str) -> Dict[str, Any]:
    """Authenticate admin credentials against MongoDB admin_users collection using bcrypt."""
    clean_username = username.strip().lower()
    admin_doc = db["admin_users"].find_one({"username": clean_username})

    if admin_doc:
        if verify_password(password, admin_doc.get("password_hash", "")):
            if not admin_doc.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is deactivated."
                )
            return admin_doc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin username or password."
    )


def get_platform_stats(db: Database) -> PlatformStatsResponse:
    """Compute aggregate platform metrics across users, apps, revenue, subscriptions, and logs."""
    total_users = db["users"].count_documents({})
    verified_users = db["users"].count_documents({"is_verified": True})

    total_apps = db["application_keys"].count_documents({})
    active_apps = db["application_keys"].count_documents({"status": "active"})

    # Total revenue from succeeded payments via MongoDB aggregation pipeline
    pipeline: List[Dict[str, Any]] = [
        {"$match": {"status": "succeeded"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    agg_result = list(db["payments"].aggregate(pipeline))
    total_revenue = float(agg_result[0]["total"]) if agg_result else 0.0

    active_subscriptions = db["subscriptions"].count_documents({"status": "active"})
    total_logs = db["logs"].count_documents({})

    return PlatformStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        total_applications=total_apps,
        active_applications=active_apps,
        total_revenue=total_revenue,
        currency="INR",
        active_subscriptions=active_subscriptions,
        total_logs=total_logs
    )


def list_users(db: Database, limit: int = 100) -> List[AdminUserListItem]:
    """Retrieve list of central user identities."""
    cursor = db["users"].find().sort("created_at", pymongo.DESCENDING).limit(limit)
    results: List[AdminUserListItem] = []
    for u in cursor:
        user_id = str(u.get("_id") or u.get("id"))
        sub_count = db["subscriptions"].count_documents({"user_id": user_id})
        results.append(AdminUserListItem(
            id=user_id,
            email=str(u.get("email", "")),
            name=str(u.get("name", "")),
            is_verified=bool(u.get("is_verified", False)),
            is_active=bool(u.get("is_active", True)),
            subscriptions_count=sub_count,
            created_at=u.get("created_at"),
            updated_at=u.get("updated_at")
        ))
    return results


def list_payments(db: Database, limit: int = 100) -> List[AdminPaymentListItem]:
    """Retrieve payment transactions."""
    cursor = db["payments"].find().sort("created_at", pymongo.DESCENDING).limit(limit)
    results: List[AdminPaymentListItem] = []
    for p in cursor:
        user_id = str(p.get("user_id", ""))
        user_doc = db["users"].find_one({"_id": user_id}) if user_id else None
        user_email = str(user_doc["email"]) if user_doc and "email" in user_doc else None

        results.append(AdminPaymentListItem(
            id=str(p.get("_id") or p.get("id")),
            user_id=user_id,
            user_email=user_email,
            product_id=str(p.get("product_id", "")),
            plan_id=str(p.get("plan_id", "")),
            amount=float(p.get("amount", 0.0)),
            currency=str(p.get("currency", "INR")),
            status=str(p.get("status", "pending")),
            provider=str(p.get("provider", "razorpay")),
            provider_payment_id=str(p["provider_payment_id"]) if p.get("provider_payment_id") else None,
            created_at=p.get("created_at")
        ))
    return results


def list_subscriptions(db: Database, limit: int = 100) -> List[AdminSubscriptionListItem]:
    """Retrieve application subscriptions."""
    cursor = db["subscriptions"].find().sort("created_at", pymongo.DESCENDING).limit(limit)
    results: List[AdminSubscriptionListItem] = []
    for s in cursor:
        user_id = str(s.get("user_id", ""))
        user_doc = db["users"].find_one({"_id": user_id}) if user_id else None
        user_email = str(user_doc["email"]) if user_doc and "email" in user_doc else None

        results.append(AdminSubscriptionListItem(
            id=str(s.get("_id") or s.get("id")),
            user_id=user_id,
            user_email=user_email,
            product_id=str(s.get("product_id", "")),
            plan_id=str(s.get("plan_id", "")),
            status=str(s.get("status", "active")),
            provider=str(s.get("provider", "stripe")),
            provider_subscription_id=str(s["provider_subscription_id"]) if s.get("provider_subscription_id") else None,
            created_at=s.get("created_at")
        ))
    return results


def list_logs(db: Database, level: Optional[str] = None, app_id: Optional[str] = None, limit: int = 100) -> List[AdminLogListItem]:
    """Retrieve centralized logs with filtering options."""
    query_filter: Dict[str, Any] = {}
    if level:
        query_filter["level"] = level.upper()
    if app_id:
        query_filter["application_id"] = app_id

    cursor = db["logs"].find(query_filter).sort("created_at", pymongo.DESCENDING).limit(limit)
    results: List[AdminLogListItem] = []
    for l in cursor:
        application_id = str(l.get("application_id", ""))
        app_doc = db["application_keys"].find_one({"_id": application_id}) if application_id else None
        app_name = str(app_doc["application_name"]) if app_doc and "application_name" in app_doc else None

        results.append(AdminLogListItem(
            id=str(l.get("_id") or l.get("id")),
            application_id=application_id,
            application_name=app_name,
            user_id=str(l["user_id"]) if l.get("user_id") else None,
            level=str(l.get("level", "")),
            event=str(l.get("event", "")),
            message=str(l.get("message", "")),
            metadata=l.get("metadata"),
            created_at=l.get("created_at")
        ))
    return results
