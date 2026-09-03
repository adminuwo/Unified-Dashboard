from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path  # type: ignore
from fastapi.responses import RedirectResponse, JSONResponse  # type: ignore

from src.admin.router import get_current_admin
from src.marketing.models import (
    MarketingLinkCreate,
    BatchMarketingLinkCreate,
    MarketingLinkResponse,
    MarketingAnalyticsSummary,
)
from src.marketing.service import MarketingService, PRODUCT_CATALOG, PLATFORM_CONFIG

router = APIRouter(prefix="/api/marketing", tags=["Marketing & Referrals"])
redirect_router = APIRouter(tags=["Public Redirector"])


def _get_base_url(request: Request) -> str:
    """Resolve current public host base URL."""
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    return f"{proto}://{host}"


# ==============================================================================
# 📊 1. Analytics & Metadata Endpoints
# ==============================================================================
@router.get("/config", summary="Get supported products & platform metadata")
async def get_marketing_config():
    return {
        "products": PRODUCT_CATALOG,
        "platforms": PLATFORM_CONFIG,
    }


@router.get("/analytics/summary", summary="Get overarching marketing telemetry KPI cards & graphs")
async def get_analytics_summary(admin_user: str = Depends(get_current_admin)):
    return MarketingService.get_analytics_summary()


# ==============================================================================
# 🔗 2. Link Management Endpoints
# ==============================================================================
@router.post("/links", response_model=Dict[str, Any], summary="Create single marketing tracking link")
async def create_marketing_link(
    data: MarketingLinkCreate,
    request: Request,
    admin_user: str = Depends(get_current_admin)
):
    base_url = _get_base_url(request)
    return MarketingService.create_link(data, base_request_url=base_url, creator=admin_user or "Admin")


@router.post("/links/batch", response_model=List[Dict[str, Any]], summary="Batch generate tracking links across multiple platforms")
async def create_batch_marketing_links(
    data: BatchMarketingLinkCreate,
    request: Request,
    admin_user: str = Depends(get_current_admin)
):
    base_url = _get_base_url(request)
    return MarketingService.create_batch_links(data, base_request_url=base_url, creator=admin_user or "Admin")


@router.get("/links", summary="List all marketing links with filtering")
async def list_marketing_links(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for post or campaign name"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    is_active: Optional[bool] = Query(None, description="Filter active/paused"),
    limit: int = Query(200, ge=1, le=1000),
    admin_user: str = Depends(get_current_admin)
):
    base_url = _get_base_url(request)
    return MarketingService.list_links(
        search=search,
        product_id=product_id,
        platform=platform,
        is_active=is_active,
        limit=limit,
        base_request_url=base_url
    )


@router.get("/links/{link_id}", summary="Get deep-dive telemetry for specific marketing link")
async def get_link_details(
    link_id: str,
    request: Request,
    admin_user: str = Depends(get_current_admin)
):
    base_url = _get_base_url(request)
    details = MarketingService.get_link_details(link_id, base_request_url=base_url)
    if not details:
        raise HTTPException(status_code=404, detail="Marketing link not found")
    return details


@router.patch("/links/{link_id}/status", summary="Toggle link active or paused status")
async def toggle_link_status(
    link_id: str,
    payload: Dict[str, bool],
    admin_user: str = Depends(get_current_admin)
):
    is_active = payload.get("is_active", True)
    success = MarketingService.toggle_status(link_id, is_active)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to update link status")
    return {"success": True, "link_id": link_id, "is_active": is_active}


@router.delete("/links/{link_id}", summary="Archive/delete marketing link")
async def delete_marketing_link(
    link_id: str,
    admin_user: str = Depends(get_current_admin)
):
    success = MarketingService.delete_link(link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to delete marketing link")
    return {"success": True, "message": "Marketing link and associated telemetry deleted"}


# ==============================================================================
# 🚀 3. Public High-Speed Telemetry Redirector Endpoint (/r/{slug})
# ==============================================================================
@redirect_router.get("/r/{slug}", summary="Public redirection endpoint that logs telemetry and redirects")
async def public_redirector(slug: str, request: Request):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", request.headers.get("referrer", ""))

    dest_url = MarketingService.record_click(
        slug=slug,
        ip=client_ip,
        user_agent=user_agent,
        referrer=referrer
    )

    if not dest_url:
        # Fallback to main AISA landing if link paused or invalid
        return RedirectResponse(url="https://aisa24.com?ref=invalid_or_expired_link", status_code=302)

    return RedirectResponse(url=dest_url, status_code=302)
