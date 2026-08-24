import io
import csv
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore
from google.cloud import storage  # type: ignore
from google.auth import default  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider
from src.database.models import RevenueTransaction, RevenueRawEvent, RevenueSyncJob, utc_now

logger = logging.getLogger("google_play_revenue")


class GooglePlayProvider(BaseRevenueProvider):
    """Google Play Ingestion Provider for official earnings and estimated sales."""

    def __init__(self, db: Database):
        self.db = db
        self.bucket_id = settings.GOOGLE_PLAY_GCS_BUCKET_ID or "pubsite_prod_5002243960657921085"
        self.project_id = settings.GOOGLE_PLAY_PROJECT_ID or settings.GCP_PROJECT_ID

    @property
    def provider_name(self) -> str:
        return "google_play"

    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_PLAY_ENABLED and self.bucket_id)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Google Play bucket / credentials missing."}
        try:
            credentials, _ = default()
            client = storage.Client(credentials=credentials, project=self.project_id)
            bucket = client.bucket(self.bucket_id)
            blobs = list(bucket.list_blobs(prefix="earnings/", max_results=2))
            return {
                "healthy": True,
                "message": f"Successfully connected to Google Cloud Storage bucket {self.bucket_id}. Found {len(blobs)} report blobs."
            }
        except Exception as e:
            return {"healthy": False, "message": f"Google Play / GCS check note: {str(e)}"}

    def _map_package_to_product(self, package_name: str) -> str:
        pkg = (package_name or "").lower()
        if "legal" in pkg or "ailegal" in pkg:
            return "ailegal"
        if "connect" in pkg or "uwoconnect" in pkg:
            return "uwoconnect"
        if "efv" in pkg:
            return "efvframework"
        return "aisa"

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {"success": False, "error": "Google Play integration not configured."}

        job_id = f"job_gplay_{int(datetime.now(timezone.utc).timestamp())}"
        sync_job = RevenueSyncJob.create_dict(
            provider="google_play",
            product_code=product_code or "all",
            sync_type="gcs_reports",
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
            credentials, _ = default()
            client = storage.Client(credentials=credentials, project=self.project_id)
            bucket = client.bucket(self.bucket_id)

            # Look for earnings and sales reports
            earnings_blobs = list(bucket.list_blobs(prefix="earnings/"))
            sales_blobs = list(bucket.list_blobs(prefix="sales/"))

            target_blobs = earnings_blobs + sales_blobs

            for blob in target_blobs:
                if not blob.name.endswith(".csv") and not blob.name.endswith(".zip"):
                    continue

                try:
                    content_bytes = blob.download_as_bytes()
                    # Store raw event
                    raw_event = RevenueRawEvent.create_dict(
                        provider="google_play",
                        product_code=product_code or "all",
                        external_id=blob.name,
                        event_type="earnings_report" if "earnings" in blob.name else "sales_report",
                        payload={"blob_name": blob.name, "size_bytes": len(content_bytes)},
                        file_hash=str(blob.md5_hash),
                        processed=True
                    )
                    self.db["revenue_raw_events"].update_one(
                        {"provider": "google_play", "external_id": blob.name},
                        {"$set": raw_event},
                        upsert=True
                    )

                    # Parse CSV rows
                    if blob.name.endswith(".csv"):
                        csv_text = content_bytes.decode("utf-8", errors="replace")
                        reader = csv.DictReader(io.StringIO(csv_text))
                        for row in reader:
                            processed += 1
                            order_id = row.get("Order Number") or row.get("Description") or f"gp_tx_{processed}"
                            pkg_name = row.get("Package Name", "")
                            prod = self._map_package_to_product(pkg_name)

                            if product_code and product_code.lower() != "all" and prod != product_code.lower():
                                continue

                            amount_raw = float(row.get("Amount (Merchant Currency)", 0) or row.get("Charged Amount", 0) or 0)
                            tax_raw = float(row.get("Taxes collected", 0) or 0)
                            fee_raw = float(row.get("Google Fee", 0) or (amount_raw * 0.15))
                            refund_raw = float(row.get("Refund Amount", 0) or 0)
                            net_raw = amount_raw - refund_raw - fee_raw - tax_raw

                            tx_dict = RevenueTransaction.create_dict(
                                source="google_play",
                                provider="google_play",
                                product_code=prod,
                                platform="android",
                                external_transaction_id=order_id,
                                external_order_id=order_id,
                                transaction_type="subscription" if "sub" in row.get("Product Type", "").lower() else "inapp_purchase",
                                gross_amount=amount_raw,
                                tax_amount=tax_raw,
                                fee_amount=fee_raw,
                                refund_amount=refund_raw,
                                net_amount=net_raw,
                                currency=row.get("Currency of Sale", "INR") or "INR",
                                reporting_amount=amount_raw,
                                reporting_currency="INR",
                                exchange_rate=1.0,
                                country=row.get("Country of Buyer", "IN") or "IN",
                                status="completed",
                                raw_reference=blob.name,
                                metadata=dict(row)
                            )

                            query = {
                                "provider": "google_play",
                                "product_code": prod,
                                "external_transaction_id": order_id,
                                "transaction_type": tx_dict["transaction_type"]
                            }
                            ex = self.db["revenue_transactions"].find_one(query)
                            if ex:
                                self.db["revenue_transactions"].update_one(query, {"$set": tx_dict})
                                updated += 1
                            else:
                                self.db["revenue_transactions"].insert_one(tx_dict)
                                created += 1

                except Exception as b_err:
                    logger.error(f"Error processing Google Play report blob {blob.name}: {b_err}")
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
                "provider": "google_play",
                "processed": processed,
                "created": created,
                "updated": updated,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Google Play sync failed: {e}")
            self.db["revenue_sync_jobs"].update_one(
                {"_id": job_id},
                {"$set": {
                    "completed_at": utc_now(),
                    "status": "failed",
                    "error_message": str(e)
                }}
            )
            return {"success": False, "error": str(e), "job_id": job_id}
