import os
import io
import gzip
import csv
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider
from src.analytics.app_store.auth import AppStoreConnectAuth
from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueSyncJob, utc_now

logger = logging.getLogger("apple_app_store_revenue")


class AppleAppStoreProvider(BaseRevenueProvider):
    """Apple App Store Connect Financial & Sales Revenue Provider."""

    def __init__(self, db: Database):
        self.db = db
        key_id = settings.APP_STORE_CONNECT_KEY_ID or settings.APPLE_KEY_ID or "HFP6J73293"
        issuer_id = settings.APP_STORE_CONNECT_ISSUER_ID or "2ee8709c-344f-4cfe-9ac2-87402b62f37f"
        
        # Locate .p8 private key file
        pk_path = settings.APP_STORE_CONNECT_PRIVATE_KEY_PATH or "keys/AuthKey_HFP6J73293.p8"
        if not os.path.isabs(pk_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            abs_pk_path = os.path.join(base_dir, pk_path)
            if not os.path.exists(abs_pk_path):
                # Try backend/keys or root
                alt_path = os.path.join(base_dir, "keys", f"AuthKey_{key_id}.p8")
                if os.path.exists(alt_path):
                    pk_path = alt_path
                else:
                    pk_path = abs_pk_path
            else:
                pk_path = abs_pk_path

        self.auth = AppStoreConnectAuth(
            issuer_id=issuer_id,
            key_id=key_id,
            private_key=pk_path
        ) if os.path.exists(pk_path) else None

    @property
    def provider_name(self) -> str:
        return "app_store"

    def is_configured(self) -> bool:
        return bool(self.auth is not None and getattr(self.auth, "private_key", None))

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Apple App Store Connect .p8 key / credentials not found."}
        try:
            token = self.auth.generate_token()
            res = requests.get(
                "https://api.appstoreconnect.apple.com/v1/apps",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15
            )
            if res.status_code == 200:
                apps_data = res.json().get("data", [])
                return {
                    "healthy": True,
                    "message": f"Successfully connected to App Store Connect. Accessible apps: {len(apps_data)}."
                }
            return {
                "healthy": False,
                "message": f"App Store Connect returned HTTP {res.status_code}: {res.text[:150]}"
            }
        except Exception as e:
            return {"healthy": False, "message": f"App Store Connect connection error: {str(e)}"}

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "error": "Apple App Store Connect credentials missing."}

        job_id = f"job_apple_{int(datetime.now(timezone.utc).timestamp())}"
        sync_job = RevenueSyncJob.create_dict(
            provider="app_store",
            product_code=product_code or "all",
            sync_type="finance_reports",
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
            token = self.auth.generate_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Attempt to fetch sales reports via App Store Connect Sales Reports endpoint
            vendor_num = settings.APPLE_VENDOR_NUMBER or "81234567"
            report_date = (from_date or utc_now()).strftime("%Y-%m-%d")

            # Try to fetch summary sales report
            url = f"https://api.appstoreconnect.apple.com/v1/salesReports?filter[frequency]=DAILY&filter[reportType]=SALES&filter[reportSubType]=SUMMARY&filter[vendorNumber]={vendor_num}&filter[reportDate]={report_date}"
            res = requests.get(url, headers=headers, timeout=25)

            if res.status_code == 200:
                # Gzipped TSV content
                content = gzip.decompress(res.content).decode("utf-8", errors="replace")
                raw_event = RevenueRawEvent.create_dict(
                    provider="app_store",
                    product_code=product_code or "all",
                    external_id=f"apple_sales_{report_date}",
                    event_type="sales_report",
                    payload={"report_date": report_date, "raw_sample": content[:200]},
                    processed=True
                )
                self.db["revenue_raw_events"].update_one(
                    {"provider": "app_store", "external_id": f"apple_sales_{report_date}"},
                    {"$set": raw_event},
                    upsert=True
                )

                reader = csv.DictReader(io.StringIO(content), delimiter="\t")
                for row in reader:
                    processed += 1
                    sku = row.get("SKU") or row.get("Apple Identifier") or f"apple_tx_{processed}"
                    prod = "ailegal" if "legal" in sku.lower() else "aisa"

                    if product_code and product_code.lower() != "all" and prod != product_code.lower():
                        continue

                    units = int(row.get("Units", 1) or 1)
                    proceeds_per_unit = float(row.get("Developer Proceeds", 0) or 0)
                    gross_per_unit = float(row.get("Customer Price", 0) or proceeds_per_unit)
                    
                    gross = gross_per_unit * units
                    net = proceeds_per_unit * units
                    fee = gross - net
                    curr = row.get("Currency of Proceeds", "INR") or "INR"

                    tx_dict = RevenueTransaction.create_dict(
                        source="app_store",
                        provider="app_store",
                        product_code=prod,
                        platform="ios",
                        external_transaction_id=f"apple_{sku}_{report_date}",
                        transaction_type="subscription" if "sub" in sku.lower() else "inapp_purchase",
                        gross_amount=gross,
                        tax_amount=0.0,
                        fee_amount=fee,
                        refund_amount=0.0,
                        net_amount=net,
                        currency=curr,
                        reporting_amount=gross,
                        reporting_currency="INR",
                        country=row.get("Country Code", "IN") or "IN",
                        status="completed",
                        raw_reference=f"apple_sales_{report_date}",
                        metadata=dict(row)
                    )

                    query = {
                        "provider": "app_store",
                        "product_code": prod,
                        "external_transaction_id": tx_dict["external_transaction_id"],
                        "transaction_type": tx_dict["transaction_type"]
                    }
                    ex = self.db["revenue_transactions"].find_one(query)
                    if ex:
                        self.db["revenue_transactions"].update_one(query, {"$set": tx_dict})
                        updated += 1
                    else:
                        self.db["revenue_transactions"].insert_one(tx_dict)
                        created += 1

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
                "provider": "app_store",
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Apple App Store sync note: {e}")
            self.db["revenue_sync_jobs"].update_one(
                {"_id": job_id},
                {"$set": {
                    "completed_at": utc_now(),
                    "status": "failed",
                    "error_message": str(e)
                }}
            )
            return {"success": False, "error": str(e), "job_id": job_id}
