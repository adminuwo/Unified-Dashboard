import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider
from src.integrations.razorpay.client import RazorpayClient
from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueSyncJob, utc_now

logger = logging.getLogger("razorpay_provider")


class RazorpayProvider(BaseRevenueProvider):
    """Razorpay Revenue Provider Implementation."""

    def __init__(self, db: Database):
        self.db = db
        self.client = RazorpayClient(
            key_id=settings.RAZORPAY_KEY_ID or "",
            key_secret=settings.RAZORPAY_KEY_SECRET or "",
            webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET
        )

    @property
    def provider_name(self) -> str:
        return "razorpay"

    def is_configured(self) -> bool:
        return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Razorpay Key ID or Secret missing."}
        try:
            res = self.client.fetch_payments(count=1)
            return {"healthy": True, "message": "Successfully connected to Razorpay Live API."}
        except Exception as e:
            return {"healthy": False, "message": f"Connection failed: {str(e)}"}

    def _infer_product_code(self, item: Dict[str, Any]) -> str:
        """Infer canonical product code from notes, existing events, description, or fallback to 'other'."""
        pay_id = item.get("id")

        # 1. Check notes
        notes = item.get("notes") or {}
        if isinstance(notes, dict):
            for k in ["product_code", "app_code", "app", "product", "project"]:
                if k in notes and notes[k]:
                    val = str(notes[k]).lower().strip()
                    if val in ["aisa", "ailegal", "uwoconnect", "efvframework", "aiads", "other"]:
                        return val
                    if "legal" in val:
                        return "ailegal"
                    if "aisa" in val:
                        return "aisa"
                    if "connect" in val or "uwo" in val:
                        return "uwoconnect"
                    if "ads" in val:
                        return "aiads"
                    if "efv" in val:
                        return "efvframework"
                    return val

        # 2. Check if already recorded in revenue_raw_events or revenue_transactions
        if pay_id:
            existing_tx = self.db["revenue_transactions"].find_one({"provider": "razorpay", "external_transaction_id": pay_id})
            if existing_tx and existing_tx.get("product_code") and existing_tx.get("product_code") != "other":
                return existing_tx.get("product_code")

            existing_raw = self.db["revenue_raw_events"].find_one({"provider": "razorpay", "external_id": pay_id})
            if existing_raw and existing_raw.get("product_code") and existing_raw.get("product_code") != "other":
                return existing_raw.get("product_code")

        # 3. Check description
        desc = (item.get("description") or "").lower()
        if "legal" in desc or "ailegal" in desc:
            return "ailegal"
        if "uwo" in desc or "connect" in desc:
            return "uwoconnect"
        if "efv" in desc:
            return "efvframework"
        if "ads" in desc:
            return "aiads"
        if "aisa" in desc:
            return "aisa"

        # 4. Default fallback for unclassified/unmapped payments
        return "other"

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Razorpay credentials not configured.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }

        job_id = f"job_razorpay_{int(datetime.now(timezone.utc).timestamp())}"
        sync_job = RevenueSyncJob.create_dict(
            provider="razorpay",
            product_code=product_code or "all",
            sync_type="realtime_api",
            started_at=utc_now(),
            status="running",
            job_id=job_id
        )
        self.db["revenue_sync_jobs"].insert_one(sync_job)

        from_ts = int(from_date.timestamp()) if from_date else None
        to_ts = int(to_date.timestamp()) if to_date else None

        processed = 0
        created = 0
        updated = 0
        errors = 0
        error_msg = None

        try:
            # 1. Fetch Payments from Razorpay
            skip = 0
            count = 100
            has_more = True

            while has_more:
                resp = self.client.fetch_payments(count=count, skip=skip, from_ts=from_ts, to_ts=to_ts)
                items = resp.get("items", [])
                if not items:
                    break

                for pay in items:
                    processed += 1
                    try:
                        pay_id = pay.get("id")
                        raw_event = RevenueRawEvent.create_dict(
                            provider="razorpay",
                            product_code=self._infer_product_code(pay),
                            external_id=pay_id,
                            event_type="payment",
                            payload=pay,
                            processed=True
                        )
                        raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
                        self.db["revenue_raw_events"].update_one(
                            {"provider": "razorpay", "external_id": pay_id},
                            {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
                            upsert=True
                        )

                        # Razorpay currencies return subunits (e.g. paise for INR). Divide by 100
                        curr = (pay.get("currency") or "INR").upper()
                        divisor = 100.0 if curr in ["INR", "USD", "EUR", "GBP", "AUD", "CAD"] else 1.0

                        gross = float(pay.get("amount") or 0) / divisor
                        refunded = float(pay.get("amount_refunded") or 0) / divisor
                        fee = float(pay.get("fee") or 0) / divisor
                        tax = float(pay.get("tax") or 0) / divisor
                        net = gross - refunded - fee - tax

                        created_ts = pay.get("created_at")
                        tx_date = datetime.fromtimestamp(created_ts, timezone.utc) if created_ts else utc_now()
                        prod_code = self._infer_product_code(pay)

                        if product_code and product_code.lower() != "all" and prod_code != product_code.lower():
                            continue

                        status_raw = pay.get("status", "captured").lower()
                        status_norm = "completed" if status_raw in ["captured", "paid"] else status_raw

                        tx_dict = RevenueTransaction.create_dict(
                            source="razorpay",
                            provider="razorpay",
                            product_code=prod_code,
                            platform="web",
                            external_transaction_id=pay_id,
                            external_order_id=pay.get("order_id"),
                            transaction_type="payment",
                            gross_amount=gross,
                            tax_amount=tax,
                            fee_amount=fee,
                            refund_amount=refunded,
                            net_amount=net,
                            currency=curr,
                            reporting_amount=gross,  # 1:1 if INR
                            reporting_currency="INR",
                            exchange_rate=1.0 if curr == "INR" else 83.0,
                            transaction_date=tx_date,
                            country="IN",
                            status=status_norm,
                            is_test=(not pay.get("captured", True) and "test" in str(pay_id)),
                            customer_id=pay.get("customer_id"),
                            customer_email=pay.get("email"),
                            raw_reference=pay_id,
                            metadata={
                                "method": pay.get("method"),
                                "bank": pay.get("bank"),
                                "wallet": pay.get("wallet"),
                                "vpa": pay.get("vpa"),
                                "error_code": pay.get("error_code"),
                                "error_description": pay.get("error_description"),
                            }
                        )

                        query = {
                            "provider": "razorpay",
                            "external_transaction_id": pay_id,
                            "transaction_type": "payment"
                        }
                        existing = self.db["revenue_transactions"].find_one(query)
                        if existing:
                            update_dict = {k: v for k, v in tx_dict.items() if k != "_id"}
                            self.db["revenue_transactions"].update_one(query, {"$set": update_dict})
                            updated += 1
                        else:
                            self.db["revenue_transactions"].insert_one(tx_dict)
                            created += 1

                    except Exception as item_err:
                        logger.error(f"Error processing Razorpay payment item {pay.get('id')}: {item_err}")
                        errors += 1

                if len(items) < count:
                    has_more = False
                else:
                    skip += count

            # Update Sync Job status
            self.db["revenue_sync_jobs"].update_one(
                {"_id": job_id},
                {"$set": {
                    "completed_at": utc_now(),
                    "status": "success" if errors == 0 else "partial_success",
                    "records_processed": processed,
                    "records_created": created,
                    "records_updated": updated,
                    "error_count": errors
                }}
            )

            return {
                "success": True,
                "job_id": job_id,
                "provider": "razorpay",
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Razorpay sync failed: {error_msg}")
            self.db["revenue_sync_jobs"].update_one(
                {"_id": job_id},
                {"$set": {
                    "completed_at": utc_now(),
                    "status": "failed",
                    "error_count": errors + 1,
                    "error_message": error_msg
                }}
            )
            return {
                "success": False,
                "job_id": job_id,
                "provider": "razorpay",
                "error": error_msg,
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors + 1
            }
