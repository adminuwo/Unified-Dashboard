"""
sync_historical_aisa_payments.py
─────────────────────────────────────────────────────────────────────────────
Reads historical payment and invoice records from AISA MongoDB in STRICTLY
READ-ONLY mode, transforms each into the canonical Unified Payment JSON format,
and inserts/upserts them directly into the Unified Dashboard database.

Zero writes or mutations are performed on the AISA database.
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient  # type: ignore

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import settings
from src.database.connection import get_db, init_db
from src.database.models import RevenueTransaction, RevenueRawEvent, utc_now

# AISA MongoDB URI (Read-only source)
AISA_MONGO_URI = "mongodb+srv://admin_db_user:gwmmWiKmK4wCit1L@cluster0.u5wdauj.mongodb.net/AISA?appName=Cluster0"
UNIFIED_MONGO_URI = settings.MONGODB_URL


def run_historical_sync():
    print("=" * 70)
    print(">> HISTORICAL PAYMENT SYNC: AISA -> UNIFIED DASHBOARD")
    print("   Policy: Strictly Read-Only on AISA DB (Zero Mutations)")
    print("=" * 70)

    # 1. Connect to AISA Database (READ-ONLY)
    print(f"\n[1/3] Connecting to AISA Database...")
    aisa_client = MongoClient(AISA_MONGO_URI, readPreference='secondaryPreferred', serverSelectionTimeoutMS=10000)
    try:
        aisa_db = aisa_client.get_default_database()
    except Exception:
        aisa_db = aisa_client["AISA"]
    print(f"[OK] Connected to AISA DB: {aisa_db.name}")

    # 2. Connect to Unified Dashboard Database (DESTINATION)
    print(f"\n[2/3] Connecting to Unified Dashboard Database...")
    unified_client = MongoClient(UNIFIED_MONGO_URI, serverSelectionTimeoutMS=10000)
    try:
        unified_db = unified_client.get_default_database()
    except Exception:
        unified_db = unified_client[settings.MONGODB_DB_NAME]
    print(f"[OK] Connected to Unified Dashboard DB: {unified_db.name}")

    # 3. Read Invoices & Subscriptions from AISA
    print(f"\n[3/3] Querying historical payments from AISA...")
    
    # Cache users and plans for quick lookup
    users_cursor = aisa_db["users"].find({}, {"_id": 1, "name": 1, "email": 1})
    users_map = {str(u["_id"]): u for u in users_cursor}

    plans_cursor = aisa_db["plans"].find({})
    plans_map = {str(p["_id"]): p for p in plans_cursor}

    # Fetch all invoices from AISA
    invoices = list(aisa_db["invoices"].find({}))
    print(f"Found {len(invoices)} total invoice records in AISA.")

    # Fetch subscriptions that have paymentId or transactionId
    subscriptions = list(aisa_db["subscriptions"].find({
        "$or": [
            {"paymentId": {"$exists": True, "$ne": None, "$ne": ""}},
            {"transactionId": {"$exists": True, "$ne": None, "$ne": ""}}
        ]
    }))
    print(f"Found {len(subscriptions)} total subscription payment records in AISA.")

    synced_tx_ids = set()
    total_processed = 0
    total_created = 0
    total_updated = 0
    errors = 0

    # A. Process Invoices First
    for inv in invoices:
        try:
            payment_id = str(inv.get("paymentId") or "").strip()
            if not payment_id or payment_id in ["mock_payment_id_for_now", "null", "undefined"]:
                inv_id = str(inv.get("_id"))
                payment_id = f"aisa_inv_{inv_id}"

            synced_tx_ids.add(payment_id)
            total_processed += 1

            user_id = str(inv.get("userId") or "")
            user = users_map.get(user_id, {})

            plan_id = str(inv.get("planId") or "")
            plan = plans_map.get(plan_id, {})
            plan_name = plan.get("planName") or inv.get("planName") or "AISA Subscription"

            gross_amount = float(inv.get("totalAmount") or inv.get("planPrice") or 0.0)
            tax_amount = float(inv.get("gstAmount") or inv.get("igst") or (inv.get("cgst", 0) + inv.get("sgst", 0)) or 0.0)
            net_amount = float(inv.get("baseAmount") or (gross_amount - tax_amount))
            fee_amount = round(gross_amount * 0.02, 2)  # Standard Razorpay 2% fee estimate if not specified

            gateway = str(inv.get("paymentGateway") or "razorpay").lower()
            platform = "ios" if "apple" in gateway or "app_store" in gateway else "web"
            provider = "app_store" if platform == "ios" else "razorpay"

            created_date = inv.get("invoiceDate") or inv.get("createdAt") or utc_now()
            if isinstance(created_date, str):
                try:
                    created_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
                except Exception:
                    created_date = utc_now()

            status_raw = str(inv.get("paymentStatus") or "completed").lower()
            status_norm = "completed" if status_raw in ["captured", "paid", "success", "completed"] else status_raw

            billing = inv.get("billingDetails") or {}
            cust_name = billing.get("name") or billing.get("billingName") or user.get("name") or (user.get("email", "").split("@")[0] if user.get("email") else "AISA User")
            cust_email = user.get("email") or billing.get("email")

            # 1. Standardized JSON Payload for Unified Dashboard
            json_payload = {
                "product_code": "aisa",
                "product_name": "AISA Assistant",
                "platform": platform,
                "provider": provider,
                "transaction_id": payment_id,
                "order_id": inv.get("orderId"),
                "transaction_type": "payment",
                "amount": gross_amount,
                "tax_amount": tax_amount,
                "fee_amount": fee_amount,
                "refund_amount": 0.0,
                "net_amount": net_amount,
                "currency": str(inv.get("currency") or "INR").upper(),
                "status": status_norm,
                "customer_id": user_id or None,
                "customer_email": cust_email,
                "customer_name": cust_name,
                "plan_id": plan.get("planId") or plan_id or None,
                "plan_name": plan_name,
                "billing_cycle": inv.get("billingCycle") or "monthly",
                "transaction_date": created_date.isoformat() if hasattr(created_date, "isoformat") else str(created_date),
                "is_test": "mock" in payment_id.lower() or "test" in payment_id.lower(),
                "metadata": {
                    "source": "historical_aisa_invoice_sync",
                    "invoice_number": inv.get("invoiceNumber"),
                    "invoice_id": str(inv.get("_id")),
                    "subscription_id": str(inv.get("subscriptionId") or ""),
                    "billing_details": billing
                }
            }

            # 2. Raw Event Upsert
            raw_event = RevenueRawEvent.create_dict(
                provider=provider,
                product_code="aisa",
                external_id=payment_id,
                event_type="historical_sync",
                payload=json_payload,
                processed=True
            )
            raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
            unified_db["revenue_raw_events"].update_one(
                {"provider": provider, "external_id": payment_id},
                {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
                upsert=True
            )

            # 3. Revenue Transaction Upsert
            tx_dict = RevenueTransaction.create_dict(
                source=provider,
                provider=provider,
                product_code="aisa",
                platform=platform,
                external_transaction_id=payment_id,
                external_order_id=inv.get("orderId"),
                transaction_type="payment",
                gross_amount=gross_amount,
                tax_amount=tax_amount,
                fee_amount=fee_amount,
                refund_amount=0.0,
                net_amount=net_amount,
                currency=str(inv.get("currency") or "INR").upper(),
                reporting_amount=gross_amount,
                reporting_currency="INR",
                exchange_rate=1.0,
                transaction_date=created_date,
                country="IN",
                status=status_norm,
                is_test=json_payload["is_test"],
                customer_id=user_id or None,
                customer_email=cust_email,
                plan_id=plan.get("planId") or plan_id or None,
                raw_reference=payment_id,
                metadata=json_payload["metadata"]
            )

            query = {
                "provider": provider,
                "external_transaction_id": payment_id,
                "transaction_type": "payment"
            }
            existing = unified_db["revenue_transactions"].find_one(query)
            if existing:
                update_dict = {k: v for k, v in tx_dict.items() if k != "_id"}
                unified_db["revenue_transactions"].update_one(query, {"$set": update_dict})
                total_updated += 1
            else:
                unified_db["revenue_transactions"].insert_one(tx_dict)
                total_created += 1

        except Exception as e:
            errors += 1
            print(f"  ✗ Error syncing invoice {inv.get('_id')}: {e}")

    # B. Process Subscriptions (any not covered by invoices)
    for sub in subscriptions:
        try:
            payment_id = str(sub.get("paymentId") or sub.get("transactionId") or "").strip()
            if not payment_id or payment_id in ["mock_payment_id_for_now", "null", "undefined"] or payment_id in synced_tx_ids:
                continue

            synced_tx_ids.add(payment_id)
            total_processed += 1

            user_id = str(sub.get("userId") or "")
            user = users_map.get(user_id, {})

            plan_id = str(sub.get("planId") or "")
            plan = plans_map.get(plan_id, {})
            plan_name = plan.get("planName") or "AISA Subscription"

            billing_cycle = str(sub.get("billingCycle") or "monthly").lower()
            plan_price = float(plan.get("priceYearly") if billing_cycle == "yearly" else plan.get("priceMonthly") or 0.0)
            gross_amount = plan_price
            tax_amount = round(gross_amount - (gross_amount / 1.18), 2)
            net_amount = round(gross_amount - tax_amount, 2)
            fee_amount = round(gross_amount * 0.02, 2)

            is_apple = bool(sub.get("originalTransactionId") or sub.get("productId") or "ios" in payment_id.lower())
            platform = "ios" if is_apple else "web"
            provider = "app_store" if is_apple else "razorpay"

            created_date = sub.get("subscriptionStart") or sub.get("createdAt") or utc_now()
            status_raw = str(sub.get("subscriptionStatus") or "active").lower()
            status_norm = "completed" if status_raw in ["active", "completed"] else status_raw

            cust_name = user.get("name") or (user.get("email", "").split("@")[0] if user.get("email") else "AISA User")
            cust_email = user.get("email")

            json_payload = {
                "product_code": "aisa",
                "product_name": "AISA Assistant",
                "platform": platform,
                "provider": provider,
                "transaction_id": payment_id,
                "transaction_type": "payment",
                "amount": gross_amount,
                "tax_amount": tax_amount,
                "fee_amount": fee_amount,
                "refund_amount": 0.0,
                "net_amount": net_amount,
                "currency": "INR",
                "status": status_norm,
                "customer_id": user_id or None,
                "customer_email": cust_email,
                "customer_name": cust_name,
                "plan_id": plan.get("planId") or plan_id or None,
                "plan_name": plan_name,
                "billing_cycle": billing_cycle,
                "transaction_date": created_date.isoformat() if hasattr(created_date, "isoformat") else str(created_date),
                "is_test": "mock" in payment_id.lower() or "test" in payment_id.lower(),
                "metadata": {
                    "source": "historical_aisa_subscription_sync",
                    "subscription_id": str(sub.get("_id")),
                    "original_transaction_id": sub.get("originalTransactionId")
                }
            }

            raw_event = RevenueRawEvent.create_dict(
                provider=provider,
                product_code="aisa",
                external_id=payment_id,
                event_type="historical_sync",
                payload=json_payload,
                processed=True
            )
            raw_set = {k: v for k, v in raw_event.items() if k != "_id"}
            unified_db["revenue_raw_events"].update_one(
                {"provider": provider, "external_id": payment_id},
                {"$set": raw_set, "$setOnInsert": {"_id": raw_event["_id"]}},
                upsert=True
            )

            tx_dict = RevenueTransaction.create_dict(
                source=provider,
                provider=provider,
                product_code="aisa",
                platform=platform,
                external_transaction_id=payment_id,
                transaction_type="payment",
                gross_amount=gross_amount,
                tax_amount=tax_amount,
                fee_amount=fee_amount,
                refund_amount=0.0,
                net_amount=net_amount,
                currency="INR",
                reporting_amount=gross_amount,
                reporting_currency="INR",
                exchange_rate=1.0,
                transaction_date=created_date,
                country="IN",
                status=status_norm,
                is_test=json_payload["is_test"],
                customer_id=user_id or None,
                customer_email=cust_email,
                plan_id=plan.get("planId") or plan_id or None,
                raw_reference=payment_id,
                metadata=json_payload["metadata"]
            )

            query = {
                "provider": provider,
                "external_transaction_id": payment_id,
                "transaction_type": "payment"
            }
            existing = unified_db["revenue_transactions"].find_one(query)
            if existing:
                update_dict = {k: v for k, v in tx_dict.items() if k != "_id"}
                unified_db["revenue_transactions"].update_one(query, {"$set": update_dict})
                total_updated += 1
            else:
                unified_db["revenue_transactions"].insert_one(tx_dict)
                total_created += 1

        except Exception as e:
            errors += 1
            print(f"  [ERR] Error syncing subscription {sub.get('_id')}: {e}")

    print("\n" + "=" * 70)
    print("[SUCCESS] HISTORICAL SYNC COMPLETE!")
    print(f"   * Records Processed : {total_processed}")
    print(f"   * Records Created   : {total_created}")
    print(f"   * Records Updated   : {total_updated}")
    print(f"   * Errors Encountered: {errors}")
    print(f"   * AISA Database     : 100% UNTOUCHED & UNMODIFIED")
    print("=" * 70)


if __name__ == "__main__":
    run_historical_sync()
