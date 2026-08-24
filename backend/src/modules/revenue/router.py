from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.admin.router import get_current_admin
from src.middleware.authentication import validate_optional_app_key
from src.modules.revenue.service import RevenueService
from src.modules.revenue.schemas import (
    RevenueOverviewResponse,
    ProductsRevenueResponse,
    ProvidersRevenueResponse,
    PlatformsRevenueResponse,
    RevenueTrendResponse,
    TransactionsListResponse,
    TransactionItem,
    SyncHealthResponse,
    ReconciliationResponse,
    SyncNowRequest,
    SyncNowResponse,
    PaymentEventIngestRequest,
    PaymentEventIngestResponse
)

router = APIRouter(prefix="/admin/revenue", tags=["Revenue Intelligence"])
public_revenue_router = APIRouter(prefix="/revenue", tags=["Revenue Ingestion"])


@public_revenue_router.post("/ingest", response_model=PaymentEventIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/ingest", response_model=PaymentEventIngestResponse, status_code=status.HTTP_200_OK)
def ingest_payment(
    req: PaymentEventIngestRequest,
    db: Database = Depends(get_db),
    app: Optional[Any] = Depends(validate_optional_app_key)
):
    """Ingest payment events from connected applications (AISA, AI Legal, UWO, etc.)."""
    service = RevenueService(db)
    result = service.ingest_payment_event(req)
    return result



def _resolve_period_dates(period: Optional[str], from_date: Optional[str], to_date: Optional[str]):
    from_dt = datetime.fromisoformat(from_date) if from_date else None
    to_dt = datetime.fromisoformat(to_date) if to_date else None
    
    if not from_dt and period:
        p = period.lower().strip()
        now = datetime.now(timezone.utc)
        if p == "7d":
            from_dt = now - timedelta(days=7)
        elif p == "30d":
            from_dt = now - timedelta(days=30)
        elif p == "90d":
            from_dt = now - timedelta(days=90)
        elif p == "1y":
            from_dt = now - timedelta(days=365)
        elif p in ["all", "lifetime"]:
            from_dt = None
            
    return from_dt, to_dt


@router.get("/overview", response_model=RevenueOverviewResponse)
def get_revenue_overview(
    period: Optional[str] = Query("30d", description="Time period: 7d, 30d, 90d, 1y, all"),
    from_date: Optional[str] = Query(None, alias="from", description="ISO start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="ISO end date (YYYY-MM-DD)"),
    product: Optional[str] = Query(None, description="Filter by product code"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    currency: str = Query("INR", description="Reporting currency"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Retrieve normalized organization revenue KPIs & financial overview."""
    service = RevenueService(db)
    from_dt, to_dt = _resolve_period_dates(period, from_date, to_date)

    return service.aggregator.get_overview(
        from_date=from_dt,
        to_date=to_dt,
        product_code=product,
        provider=provider,
        platform=platform,
        currency=currency
    )


@router.get("/products", response_model=ProductsRevenueResponse)
def get_revenue_by_product(
    period: Optional[str] = Query("30d"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get financial performance broken down by product."""
    service = RevenueService(db)
    from_dt, to_dt = _resolve_period_dates(period, from_date, to_date)
    items = service.aggregator.get_by_product(from_date=from_dt, to_date=to_dt)
    return {"products": items, "currency": "INR"}


@router.get("/providers", response_model=ProvidersRevenueResponse)
def get_revenue_by_provider(
    period: Optional[str] = Query("30d"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get revenue split across payment gateways and app stores."""
    service = RevenueService(db)
    from_dt, to_dt = _resolve_period_dates(period, from_date, to_date)
    items = service.aggregator.get_by_provider(from_date=from_dt, to_date=to_dt)
    return {"providers": items, "currency": "INR"}


@router.get("/platforms", response_model=PlatformsRevenueResponse)
def get_revenue_by_platform(
    period: Optional[str] = Query("30d"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get revenue breakdown by deployment platform (Android, iOS, Web)."""
    service = RevenueService(db)
    from_dt, to_dt = _resolve_period_dates(period, from_date, to_date)
    items = service.aggregator.get_by_platform(from_date=from_dt, to_date=to_dt)
    return {"platforms": items, "currency": "INR"}


@router.get("/trend", response_model=RevenueTrendResponse)
def get_revenue_trend(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, 1y, all)"),
    product: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get timeseries revenue trend (Gross, Refunds, Net)."""
    service = RevenueService(db)
    points = service.aggregator.get_trend(period=period, product_code=product, provider=provider)
    return {"period": period, "data": points, "currency": "INR"}



@router.get("/transactions", response_model=TransactionsListResponse)
def get_transactions_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    product: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get paginated, filterable financial transactions explorer."""
    service = RevenueService(db)
    query = {}
    if product and product.lower() != "all":
        query["product_code"] = product.lower()
    if provider and provider.lower() != "all":
        query["provider"] = provider.lower()
    if platform and platform.lower() != "all":
        query["platform"] = platform.lower()
    if status and status.lower() != "all":
        query["status"] = status.lower()
    if transaction_type and transaction_type.lower() != "all":
        query["transaction_type"] = transaction_type.lower()
    if search:
        query["$or"] = [
            {"external_transaction_id": {"$regex": search, "$options": "i"}},
            {"customer_email": {"$regex": search, "$options": "i"}},
            {"external_order_id": {"$regex": search, "$options": "i"}}
        ]

    items, total = service.repo.get_transactions_paginated(query, page=page, page_size=page_size)
    return {
        "total_count": total,
        "page": page,
        "page_size": page_size,
        "transactions": items
    }


@router.get("/transactions/{transaction_id}")
def get_transaction_details(
    transaction_id: str,
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get full audit and raw event details for a single transaction."""
    service = RevenueService(db)
    tx = service.repo.get_transaction_by_id(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    raw_event = None
    if tx.get("raw_reference") or tx.get("external_transaction_id"):
        raw_id = tx.get("raw_reference") or tx.get("external_transaction_id")
        raw_event = db["revenue_raw_events"].find_one({"external_id": raw_id})
        if raw_event:
            raw_event["id"] = str(raw_event.get("_id"))

    return {
        "transaction": tx,
        "raw_event": raw_event
    }


@router.get("/health", response_model=SyncHealthResponse)
def get_sync_health(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get provider synchronization status, health, and data freshness metrics."""
    service = RevenueService(db)
    items = service.get_sync_health()
    return {"providers": items}


@router.get("/reconciliation", response_model=ReconciliationResponse)
def get_reconciliation_report(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Get reconciliation report comparing provider data vs normalized internal database."""
    service = RevenueService(db)
    records = service.run_reconciliation()
    return {"items": records}


@router.post("/sync", response_model=SyncNowResponse)
def trigger_sync_now(
    req: SyncNowRequest,
    request: Request,
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Manually trigger real-time synchronization with live provider APIs."""
    service = RevenueService(db)
    client_ip = request.client.host if request.client else None

    if req.provider and req.provider.lower() != "all":
        res = service.sync_single_provider(req.provider, product_code=req.product_code)
    else:
        res = service.sync_all_providers(product_code=req.product_code)

    service.record_audit(
        admin_user=admin,
        action="manual_sync_triggered",
        provider=req.provider,
        product=req.product_code,
        ip=client_ip,
        details=res
    )

    return res


@router.get("/registry")
def get_product_registry(
    admin: str = Depends(get_current_admin),
    db: Database = Depends(get_db)
):
    """Retrieve canonical multi-product configurations."""
    service = RevenueService(db)
    return service.repo.get_product_registry()
