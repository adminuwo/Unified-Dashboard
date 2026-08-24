import pymongo
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo.database import Database  # type: ignore

from src.database.models import utc_now


class RevenueRepository:
    """Database repository for all Revenue Intelligence collections."""

    def __init__(self, db: Database):
        self.db = db
        self._ensure_indexes()
        self._seed_default_product_registry()

    def _ensure_indexes(self):
        """Create necessary indexes for high-speed queries and unique deduplication."""
        try:
            # 1. Transactions compound unique index for idempotency
            self.db["revenue_transactions"].create_index(
                [
                    ("provider", pymongo.ASCENDING),
                    ("product_code", pymongo.ASCENDING),
                    ("external_transaction_id", pymongo.ASCENDING),
                    ("transaction_type", pymongo.ASCENDING)
                ],
                unique=True,
                name="idx_revenue_tx_dedup"
            )
            self.db["revenue_transactions"].create_index([("transaction_date", pymongo.DESCENDING)], name="idx_tx_date")
            self.db["revenue_transactions"].create_index([("product_code", pymongo.ASCENDING)], name="idx_tx_product")
            self.db["revenue_transactions"].create_index([("platform", pymongo.ASCENDING)], name="idx_tx_platform")
            self.db["revenue_transactions"].create_index([("provider", pymongo.ASCENDING)], name="idx_tx_provider")

            # 2. Raw Events index
            self.db["revenue_raw_events"].create_index(
                [("provider", pymongo.ASCENDING), ("external_id", pymongo.ASCENDING)],
                unique=True,
                name="idx_raw_event_dedup"
            )

            # 3. Sync jobs index
            self.db["revenue_sync_jobs"].create_index([("started_at", pymongo.DESCENDING)], name="idx_sync_started")

        except Exception as e:
            # If indexes already exist or minor conflict
            pass

    def _seed_default_product_registry(self):
        """Seed canonical registry for all 5 enterprise products if not present."""
        defaults = [
            {
                "_id": "aisa",
                "product_code": "aisa",
                "name": "AISA Assistant",
                "status": "active",
                "platforms": ["android", "ios", "web"],
                "app_store": {"enabled": True, "app_id": "6779135418"},
                "razorpay": {"enabled": True},
                "razorpay_efv": {"enabled": False},
                "cashfree": {"enabled": False}
            },
            {
                "_id": "ailegal",
                "product_code": "ailegal",
                "name": "AI Legal",
                "status": "active",
                "platforms": ["android", "ios", "web"],
                "app_store": {"enabled": True, "app_id": "6797449251"},
                "razorpay": {"enabled": True},
                "razorpay_efv": {"enabled": False},
                "cashfree": {"enabled": False}
            },
            {
                "_id": "uwoconnect",
                "product_code": "uwoconnect",
                "name": "UWO Connect",
                "status": "active",
                "platforms": ["web"],
                "app_store": {"enabled": False},
                "razorpay": {"enabled": True},
                "razorpay_efv": {"enabled": False},
                "cashfree": {"enabled": False}
            },
            {
                "_id": "efvframework",
                "product_code": "efvframework",
                "name": "EFV Framework",
                "status": "active",
                "platforms": ["web"],
                "app_store": {"enabled": False},
                "razorpay": {"enabled": False},
                "razorpay_efv": {"enabled": True},
                "cashfree": {"enabled": True}
            },
            {
                "_id": "aiads",
                "product_code": "aiads",
                "name": "AI Ads",
                "status": "active",
                "platforms": ["web"],
                "app_store": {"enabled": False},
                "razorpay": {"enabled": True},
                "razorpay_efv": {"enabled": False},
                "cashfree": {"enabled": False}
            }
        ]

        for p in defaults:
            self.db["product_registry"].update_one(
                {"_id": p["_id"]},
                {"$set": p},
                upsert=True
            )


    def get_product_registry(self) -> List[Dict[str, Any]]:
        return list(self.db["product_registry"].find())

    def get_transactions_paginated(
        self,
        filter_query: Dict[str, Any],
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        total = self.db["revenue_transactions"].count_documents(filter_query)
        skip = (page - 1) * page_size
        cursor = self.db["revenue_transactions"].find(filter_query).sort("transaction_date", pymongo.DESCENDING).skip(skip).limit(page_size)
        items = list(cursor)
        for it in items:
            it["id"] = str(it.get("_id"))
        return items, total

    def get_transaction_by_id(self, tx_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db["revenue_transactions"].find_one({"$or": [{"_id": tx_id}, {"external_transaction_id": tx_id}]})
        if doc:
            doc["id"] = str(doc.get("_id"))
        return doc

    def get_sync_health(self) -> List[Dict[str, Any]]:
        return list(self.db["revenue_sync_jobs"].find().sort("started_at", pymongo.DESCENDING).limit(50))

    def get_reconciliation_records(self) -> List[Dict[str, Any]]:
        return list(self.db["revenue_reconciliation"].find().sort("created_at", pymongo.DESCENDING).limit(100))
