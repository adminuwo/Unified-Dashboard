import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider
from src.integrations.cashfree.client import CashfreeClient
from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueSyncJob, utc_now

logger = logging.getLogger("cashfree_provider")

class CashfreeProvider(BaseRevenueProvider):
    """Cashfree PG Ingestion Provider (Used only for EFV Framework)."""

    def __init__(self, db: Database):
        self.db = db
        self.client = CashfreeClient(
            app_id=settings.CASHFREE_APP_ID or "",
            secret_key=settings.CASHFREE_SECRET_KEY or "",
            environment=settings.CASHFREE_ENVIRONMENT
        )

    @property
    def provider_name(self) -> str:
        return "cashfree"

    def is_configured(self) -> bool:
        return bool(settings.CASHFREE_ENABLED and settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Cashfree credentials (App ID or Secret Key) missing."}
        try:
            success = self.client.test_credentials()
            if success:
                return {"healthy": True, "message": f"Successfully connected to Cashfree {settings.CASHFREE_ENVIRONMENT.title()} API."}
            else:
                return {"healthy": False, "message": "Invalid Cashfree Client ID or Secret Key."}
        except Exception as e:
            return {"healthy": False, "message": f"Cashfree connection failed: {str(e)}"}

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Cashfree integration not configured.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }

        # If sync requests another product, we skip since Cashfree is only used for EFV Framework
        if product_code and product_code.lower() != "all" and product_code.lower() != "efvframework":
            return {
                "success": True,
                "message": "Cashfree is configured only for EFV Framework. Skipped.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }

        job_id = f"job_cashfree_{int(datetime.now(timezone.utc).timestamp())}"
        sync_job = RevenueSyncJob.create_dict(
            provider="cashfree",
            product_code="efvframework",
            sync_type="settlements_recon",
            started_at=utc_now(),
            status="running",
            job_id=job_id
        )
        self.db["revenue_sync_jobs"].insert_one(sync_job)

        processed = 0
        created = 0
        updated = 0
        errors = 0

        try:
            # 1. Fetch settlements
            settlements = self.client.fetch_settlements(limit=50)
            
            for setl in settlements:
                settlement_id = setl.get("settlement_id")
                if not settlement_id:
                    continue
                
                # 2. Fetch recon transactions for each settlement
                txs = self.client.fetch_settlement_reconciliation(settlement_id)
                for tx in txs:
                    processed += 1
                    try:
                        tx_id = tx.get("cf_payment_id") or tx.get("payment_id") or f"cf_tx_{processed}"
                        order_id = tx.get("order_id") or tx.get("cf_order_id")
                        
                        # Store raw event
                        raw_event = RevenueRawEvent.create_dict(
                            provider="cashfree",
                            product_code="efvframework",
                            external_id=tx_id,
                            event_type="payment",
                            payload=tx,
                            processed=True
                        )
                        raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
                        self.db["revenue_raw_events"].update_one(
                            {"provider": "cashfree", "external_id": tx_id},
                            {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
                            upsert=True
                        )

                        # Parse transaction amounts
                        gross = float(tx.get("order_amount") or tx.get("payment_amount") or 0.0)
                        fee = float(tx.get("service_charge") or tx.get("charges") or 0.0)
                        tax = float(tx.get("service_tax") or tx.get("tax") or 0.0)
                        net = float(tx.get("settlement_amount") or (gross - fee - tax))
                        
                        tx_date_raw = tx.get("payment_time") or tx.get("settlement_date")
                        tx_date = utc_now()
                        if tx_date_raw:
                            try:
                                tx_date = datetime.fromisoformat(tx_date_raw.replace("Z", "+00:00"))
                            except ValueError:
                                pass

                        # Map into RevenueTransaction
                        tx_dict = RevenueTransaction.create_dict(
                            source="cashfree",
                            provider="cashfree",
                            product_code="efvframework",
                            platform="web",
                            external_transaction_id=tx_id,
                            external_order_id=order_id,
                            transaction_type="payment",
                            gross_amount=gross,
                            tax_amount=tax,
                            fee_amount=fee,
                            refund_amount=0.0,
                            net_amount=net,
                            currency=tx.get("payment_currency", "INR") or "INR",
                            reporting_amount=gross,
                            reporting_currency="INR",
                            exchange_rate=1.0,
                            transaction_date=tx_date,
                            country="IN",
                            status="completed",
                            customer_email=tx.get("customer_email"),
                            raw_reference=tx_id,
                            metadata=tx
                        )

                        query = {
                            "provider": "cashfree",
                            "external_transaction_id": tx_id,
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
                        logger.error(f"Error processing Cashfree transaction item: {item_err}")
                        errors += 1

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
                "provider": "cashfree",
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Cashfree sync failed: {e}")
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
                "provider": "cashfree",
                "error": str(e),
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors + 1
            }
