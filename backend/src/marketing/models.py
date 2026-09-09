from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MarketingLinkCreate(BaseModel):
    product_id: str = Field(..., description="Target product: aisa, aimall, efv, ailegal, uwo, uwoconnect, yugamc, or custom")
    product_name: Optional[str] = None
    custom_target_url: Optional[str] = None
    platform: str = Field(..., description="Distribution platform: instagram, linkedin, youtube, twitter, whatsapp, meta_ads, google_ads, reddit, telegram, email, or other")
    campaign_name: str = Field(..., description="Campaign group name e.g. diwali_sale_2026, launch_v2")
    post_name: str = Field(..., description="Specific post identifier e.g. Reel 1 - AI Lawyer, Story 2 - 50% Off, Bio Link")
    channel_type: Optional[str] = "organic"  # organic, paid_ad, influencer, partner, referral
    custom_slug: Optional[str] = None
    notes: Optional[str] = None


class BatchMarketingLinkCreate(BaseModel):
    product_id: str = Field(..., description="Target product identifier")
    custom_target_url: Optional[str] = None
    campaign_name: str = Field(..., description="Campaign group name")
    post_name: str = Field(..., description="Post / Content identifier")
    platforms: List[str] = Field(..., min_items=1, description="List of platform IDs to generate links for")
    channel_type: Optional[str] = "organic"
    notes: Optional[str] = None


class MarketingLinkResponse(BaseModel):
    id: str
    slug: str
    product_id: str
    product_name: str
    target_url: str
    full_destination_url: str
    short_url: str
    platform: str
    campaign_name: str
    post_name: str
    channel_type: str
    total_clicks: int = 0
    unique_clicks: int = 0
    total_downloads: int = 0
    android_downloads: int = 0
    ios_downloads: int = 0
    unique_installs: int = 0
    conversion_rate: Optional[float] = 0.0
    is_active: bool = True
    created_by: Optional[str] = "Admin"
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_clicked_at: Optional[datetime] = None


class InstallTelemetryCreate(BaseModel):
    product_id: Optional[str] = Field(None, description="Product code e.g. ailegal, aisa")
    app_code: Optional[str] = Field(None, description="Alternative alias for product_id")
    slug: Optional[str] = Field(None, description="Referral campaign slug")
    referral_code: Optional[str] = Field(None, description="Referral code alias for slug")
    ref_code: Optional[str] = Field(None, description="Short referral code alias")
    install_referrer: Optional[str] = Field(None, description="Raw Google Play install referrer string")
    platform: str = Field("android", description="Mobile OS platform: android or ios")
    device_id: Optional[str] = Field(None, description="Unique client device fingerprint or UUID")
    version: Optional[str] = Field("1.0.0", description="Installed app version")
    ip: Optional[str] = Field(None, description="Explicit client IP if provided")
    user_id: Optional[str] = Field(None, description="Authenticated user ID if available")


class ClickTelemetry(BaseModel):
    slug: str
    timestamp: datetime
    ip_hash: str
    user_agent: Optional[str] = None
    device_type: str = "Desktop"  # Mobile, Desktop, Tablet, Bot
    browser: str = "Unknown"
    os: str = "Unknown"
    referrer: Optional[str] = None
    country: Optional[str] = "India"
    city: Optional[str] = None


class MarketingAnalyticsSummary(BaseModel):
    total_links: int
    total_clicks: int
    unique_reach: int
    total_downloads: int = 0
    android_downloads: int = 0
    ios_downloads: int = 0
    downloads_by_platform: Dict[str, int] = Field(default_factory=dict)
    overall_conversion_rate: float = 0.0
    top_product: Optional[Dict[str, Any]] = None
    top_platform: Optional[Dict[str, Any]] = None
    top_post: Optional[Dict[str, Any]] = None
    platform_distribution: List[Dict[str, Any]]
    product_distribution: List[Dict[str, Any]]
    device_distribution: List[Dict[str, Any]]
    recent_clicks: List[Dict[str, Any]]
