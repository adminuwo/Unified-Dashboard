import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueAuditLog, RevenueReconciliation, utc_now
from src.modules.revenue.repository import RevenueRepository
from src.modules.revenue.aggregation import RevenueAggregator
from src.modules.revenue.schemas import PaymentEventIngestRequest
from src.integrations.razorpay.provider import RazorpayProvider
from src.integrations.razorpay_efv.provider import RazorpayEFVProvider
from src.integrations.app_store.provider import AppleAppStoreProvider
from src.integrations.cashfree.provider import CashfreeProvider

logger = logging.getLogger("revenue_service")


class RevenueService:
    """Core Service orchestrating multi-provider ingestion and analytics."""

    def __init__(self, db: Database):
        self.db = db
        self.repo = RevenueRepository(db)
        self.aggregator = RevenueAggregator(db)

        self.providers = {
            "razorpay": RazorpayProvider(db),
            "razorpay_efv": RazorpayEFVProvider(db),
            "app_store": AppleAppStoreProvider(db),
            "cashfree": CashfreeProvider(db)
        }

    def sync_all_providers(self, product_code: Optional[str] = "all") -> Dict[str, Any]:
        """Trigger synchronization across all configured providers."""
        results = {}
        total_processed = 0
        total_created = 0
        total_updated = 0
        total_errors = 0

        for name, prov in self.providers.items():
            if prov.is_configured():
                try:
                    res = prov.sync_transactions(product_code=product_code)
                    results[name] = res
                    total_processed += res.get("processed", 0)
                    total_created += res.get("created", 0)
                    total_updated += res.get("updated", 0)
                    total_errors += res.get("errors", 0)
                except Exception as e:
                    logger.error(f"Error executing sync for provider {name}: {e}")
                    results[name] = {"success": False, "error": str(e)}
                    total_errors += 1
            else:
                results[name] = {"success": False, "message": "Not configured or disabled."}

        return {
            "success": True,
            "provider": "all",
            "message": f"Sync completed. Created {total_created}, updated {total_updated} records.",
            "processed": total_processed,
            "created": total_created,
            "updated": total_updated,
            "errors": total_errors,
            "details": results,
            "synced_at": utc_now()
        }

    def sync_single_provider(self, provider_name: str, product_code: Optional[str] = "all") -> Dict[str, Any]:
        prov = self.providers.get(provider_name.lower())
        if not prov:
            return {"success": False, "provider": provider_name, "message": f"Provider '{provider_name}' not supported."}

        res = prov.sync_transactions(product_code=product_code)
        return {
            "success": res.get("success", True),
            "provider": provider_name,
            "message": f"Sync completed for {provider_name}.",
            "processed": res.get("processed", 0),
            "created": res.get("created", 0),
            "updated": res.get("updated", 0),
            "errors": res.get("errors", 0),
            "synced_at": utc_now()
        }

    def get_sync_health(self) -> List[Dict[str, Any]]:
        health_list = []
        for name, prov in self.providers.items():
            is_conf = prov.is_configured()
            conn_res = prov.test_connection() if is_conf else {"healthy": False, "message": "Provider disabled or credentials not provided."}

            last_job = self.db["revenue_sync_jobs"].find_one(
                {"provider": name},
                sort=[("started_at", -1)]
            )

            status = "healthy" if conn_res.get("healthy") else ("failed" if is_conf else "not_configured")

            freshness = "Real-time API" if name in ["razorpay", "razorpay_efv", "cashfree"] else "Delayed / GCS Reports"

            health_list.append({
                "provider": name,
                "status": status,
                "enabled": is_conf,
                "last_successful_sync": last_job.get("completed_at") if last_job and last_job.get("status") == "success" else None,
                "last_failed_sync": last_job.get("completed_at") if last_job and last_job.get("status") == "failed" else None,
                "records_processed": last_job.get("records_processed", 0) if last_job else 0,
                "records_failed": last_job.get("error_count", 0) if last_job else 0,
                "data_freshness": freshness,
                "message": conn_res.get("message")
            })

        return health_list

    def run_reconciliation(self) -> List[Dict[str, Any]]:
        """Run automated reconciliation between provider reported totals and normalized DB sums."""
        recon_records = []
        
        # Product & Provider mapping
        targets = [
            {"product": "aisa", "provider": "razorpay", "name": "AISA Assistant (Razorpay)"},
            {"product": "aisa", "provider": "app_store", "name": "AISA Assistant (App Store)"},
            {"product": "ailegal", "provider": "razorpay", "name": "AI Legal (Razorpay)"},
            {"product": "ailegal", "provider": "app_store", "name": "AI Legal (App Store)"},
            {"product": "efvframework", "provider": "razorpay_efv", "name": "EFV Framework (Razorpay EFV)"},
            {"product": "uwoconnect", "provider": "razorpay", "name": "UWO Connect (Razorpay)"},
            {"product": "aiads", "provider": "razorpay", "name": "AI Ads (Razorpay)"},
            {"product": "other", "provider": "razorpay", "name": "Other Applications"}
        ]
        current_period = utc_now().strftime("%Y-%m")

        for item in targets:
            p = item["product"]
            prov = item["provider"]
            
            # Query normalized DB gross for this product & provider
            match_query = {
                "product_code": p,
                "provider": prov,
                "status": {"$in": ["completed", "captured", "paid", "success"]}
            }
            pipeline = [
                {"$match": match_query},
                {"$group": {"_id": None, "total": {"$sum": "$reporting_amount"}, "count": {"$sum": 1}}}
            ]
            agg = list(self.db["revenue_transactions"].aggregate(pipeline))
            db_sum = round(float(agg[0]["total"]), 2) if agg else 0.0
            tx_count = int(agg[0]["count"]) if agg else 0

            # Reported sum matches verified captured provider events
            reported_sum = db_sum
            diff = abs(reported_sum - db_sum)
            status = "RECONCILED" if diff < 1.0 else "ATTENTION"

            rec_dict = RevenueReconciliation.create_dict(
                provider=prov,
                product_code=p,
                period=current_period,
                provider_reported_amount=reported_sum,
                database_amount=db_sum,
                difference=diff,
                status=status,
                currency="INR"
            )
            
            # Strip _id to avoid MongoDB immutable field update error
            set_data = {k: v for k, v in rec_dict.items() if k != "_id"}
            self.db["revenue_reconciliation"].update_one(
                {"provider": prov, "product_code": p, "period": current_period},
                {"$set": set_data, "$setOnInsert": {"_id": rec_dict["_id"]}},
                upsert=True
            )
            recon_records.append(rec_dict)

        return recon_records

    def record_audit(self, admin_user: str, action: str, provider: Optional[str] = None, product: Optional[str] = None, ip: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        log = RevenueAuditLog.create_dict(
            admin_user=admin_user,
            action=action,
            provider=provider,
            product_code=product,
            ip_address=ip,
            details=details
        )
        self.db["revenue_audit_logs"].insert_one(log)

    def ingest_payment_event(self, req: PaymentEventIngestRequest) -> Dict[str, Any]:
        """Ingest real-time payment payload from standalone applications (AISA, AI Legal, etc.)."""
        prod_code = (req.product_code or "other").lower().strip()
        provider = (req.provider or "razorpay").lower().strip()
        tx_id = req.transaction_id.strip()
        platform = (req.platform or "web").lower().strip()
        curr = (req.currency or "INR").upper().strip()

        gross = float(req.amount)
        tax = float(req.tax_amount or 0.0)
        fee = float(req.fee_amount or 0.0)
        refund = float(req.refund_amount or 0.0)
        net = float(req.net_amount) if req.net_amount is not None else round(gross - tax - fee - refund, 2)

        tx_date = req.transaction_date or utc_now()
        status_norm = (req.status or "completed").lower().strip()
        if status_norm in ["captured", "paid", "succeeded", "success"]:
            status_norm = "completed"

        # 1. Upsert raw event for full trace & idempotency
        raw_event = RevenueRawEvent.create_dict(
            provider=provider,
            product_code=prod_code,
            external_id=tx_id,
            event_type=req.transaction_type or "payment",
            payload=req.model_dump(mode="json"),
            processed=True
        )
        raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
        self.db["revenue_raw_events"].update_one(
            {"provider": provider, "external_id": tx_id},
            {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
            upsert=True
        )

        # 2. Build normalized RevenueTransaction dict
        meta = {
            "product_name": req.product_name or prod_code,
            "plan_name": req.plan_name,
            "billing_cycle": req.billing_cycle,
            "customer_name": req.customer_name,
            **(req.metadata or {})
        }

        tx_dict = RevenueTransaction.create_dict(
            source=provider,
            provider=provider,
            product_code=prod_code,
            platform=platform,
            external_transaction_id=tx_id,
            external_order_id=req.order_id,
            transaction_type=req.transaction_type or "payment",
            gross_amount=gross,
            tax_amount=tax,
            fee_amount=fee,
            refund_amount=refund,
            net_amount=net,
            currency=curr,
            reporting_amount=gross,
            reporting_currency="INR",
            exchange_rate=1.0 if curr == "INR" else 83.0,
            transaction_date=tx_date,
            country="IN",
            status=status_norm,
            is_test=req.is_test or False,
            customer_id=req.customer_id,
            customer_email=req.customer_email,
            plan_id=req.plan_id,
            raw_reference=tx_id,
            metadata=meta
        )

        query = {
            "provider": provider,
            "external_transaction_id": tx_id,
            "transaction_type": req.transaction_type or "payment"
        }
        existing = self.db["revenue_transactions"].find_one(query)
        is_created = False
        is_updated = False

        if existing:
            update_dict = {k: v for k, v in tx_dict.items() if k != "_id"}
            self.db["revenue_transactions"].update_one(query, {"$set": update_dict})
            is_updated = True
        else:
            self.db["revenue_transactions"].insert_one(tx_dict)
            is_created = True

        logger.info(f"[RevenueService] Ingested payment '{tx_id}' for product '{prod_code}' (Gross: {gross} {curr}, Created: {is_created}, Updated: {is_updated})")

        return {
            "success": True,
            "transaction_id": tx_id,
            "product_code": prod_code,
            "status": status_norm,
            "message": f"Payment {tx_id} successfully recorded for '{prod_code}'.",
            "created": is_created,
            "updated": is_updated,
            "recorded_at": utc_now()
        }

