import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider
from src.integrations.razorpay.client import RazorpayClient
from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueSyncJob, utc_now

logger = logging.getLogger("razorpay_efv_provider")

class RazorpayEFVProvider(BaseRevenueProvider):
    """Razorpay Ingestion Provider for the second Razorpay Account (Used only for EFV Framework)."""

    def __init__(self, db: Database):
        self.db = db
        self.client = RazorpayClient(
            key_id=settings.RAZORPAY_EFV_KEY_ID or "",
            key_secret=settings.RAZORPAY_EFV_KEY_SECRET or "",
            webhook_secret=settings.RAZORPAY_EFV_WEBHOOK_SECRET
        )

    @property
    def provider_name(self) -> str:
        return "razorpay_efv"

    def is_configured(self) -> bool:
        return bool(settings.RAZORPAY_EFV_ENABLED and settings.RAZORPAY_EFV_KEY_ID and settings.RAZORPAY_EFV_KEY_SECRET)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Razorpay EFV account credentials (Key ID or Secret) missing."}
        try:
            res = self.client.fetch_payments(count=1)
            return {"healthy": True, "message": "Successfully connected to Razorpay EFV Account."}
        except Exception as e:
            return {"healthy": False, "message": f"Connection failed: {str(e)}"}

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Razorpay EFV credentials not configured.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }

        # If sync requests another product, we skip since this account is only used for EFV Framework
        if product_code and product_code.lower() != "all" and product_code.lower() != "efvframework":
            return {
                "success": True,
                "message": "Razorpay EFV is configured only for EFV Framework. Skipped.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }

        job_id = f"job_razorpay_efv_{int(datetime.now(timezone.utc).timestamp())}"
        sync_job = RevenueSyncJob.create_dict(
            provider="razorpay_efv",
            product_code="efvframework",
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

        try:
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
                            provider="razorpay_efv",
                            product_code="efvframework",
                            external_id=pay_id,
                            event_type="payment",
                            payload=pay,
                            processed=True
                        )
                        raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
                        self.db["revenue_raw_events"].update_one(
                            {"provider": "razorpay_efv", "external_id": pay_id},
                            {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
                            upsert=True
                        )

                        # Parse currency units
                        curr = (pay.get("currency") or "INR").upper()
                        divisor = 100.0 if curr in ["INR", "USD", "EUR", "GBP", "AUD", "CAD"] else 1.0

                        gross = float(pay.get("amount") or 0) / divisor
                        refunded = float(pay.get("amount_refunded") or 0) / divisor
                        fee = float(pay.get("fee") or 0) / divisor
                        tax = float(pay.get("tax") or 0) / divisor
                        net = gross - refunded - fee - tax

                        created_ts = pay.get("created_at")
                        tx_date = datetime.fromtimestamp(created_ts, timezone.utc) if created_ts else utc_now()

                        status_raw = pay.get("status", "captured").lower()
                        status_norm = "completed" if status_raw in ["captured", "paid"] else status_raw

                        tx_dict = RevenueTransaction.create_dict(
                            source="razorpay_efv",
                            provider="razorpay_efv",
                            product_code="efvframework",
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
                            reporting_amount=gross,
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
                            "provider": "razorpay_efv",
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
                        logger.error(f"Error processing Razorpay EFV transaction item {pay.get('id')}: {item_err}")
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
                "provider": "razorpay_efv",
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Razorpay EFV sync failed: {str(e)}")
            self.db["revenue_sync_jobs"].update_one(
                {"_id": job_id},
                {"$set": {
                    "completed_at": utc_now(),
                    "status": "failed",
                    "error_count": errors + 1,
                    "error_message": str(e)
                }}
            )
            return {
                "success": False,
                "job_id": job_id,
                "provider": "razorpay_efv",
                "error": str(e),
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors + 1
            }
