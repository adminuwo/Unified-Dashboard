from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PeriodSchema(BaseModel):
    from_date: str = Field(..., alias="from")
    to_date: str = Field(..., alias="to")

    class Config:
        populate_by_name = True


class RevenueOverviewResponse(BaseModel):
    period: PeriodSchema
    gross_revenue: float
    refunds: float
    fees: float
    taxes: float
    net_revenue: float
    active_subscriptions: int = 0
    mrr: float = 0.0
    arr: float = 0.0
    currency: str = "INR"
    growth_pct: float = 0.0
    last_synced_at: Optional[datetime] = None


class ProductRevenueItem(BaseModel):
    product_code: str
    name: str
    gross: float
    refunds: float
    fees: float = 0.0
    taxes: float = 0.0
    net: float
    growth: str = "+0%"


class ProductsRevenueResponse(BaseModel):
    products: List[ProductRevenueItem]
    currency: str = "INR"


class ProviderRevenueItem(BaseModel):
    provider: str
    name: str
    gross: float
    refunds: float
    net: float
    share_pct: float = 0.0


class ProvidersRevenueResponse(BaseModel):
    providers: List[ProviderRevenueItem]
    currency: str = "INR"


class PlatformRevenueItem(BaseModel):
    platform: str
    gross: float
    net: float
    share_pct: float = 0.0


class PlatformsRevenueResponse(BaseModel):
    platforms: List[PlatformRevenueItem]
    currency: str = "INR"


class TrendDataPoint(BaseModel):
    date: str
    gross: float
    refunds: float
    net: float


class RevenueTrendResponse(BaseModel):
    period: str
    data: List[TrendDataPoint]
    currency: str = "INR"


class TransactionItem(BaseModel):
    id: str
    source: str
    provider: str
    product_code: str
    platform: str
    external_transaction_id: str
    external_order_id: Optional[str] = None
    transaction_type: str
    gross_amount: float
    tax_amount: float
    fee_amount: float
    refund_amount: float
    net_amount: float
    currency: str
    reporting_amount: float
    reporting_currency: str
    transaction_date: datetime
    country: str
    status: str
    customer_email: Optional[str] = None
    raw_reference: Optional[str] = None


class TransactionsListResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    transactions: List[TransactionItem]


class SyncHealthItem(BaseModel):
    provider: str
    status: str  # healthy, warning, failed, not_configured
    enabled: bool
    last_successful_sync: Optional[datetime] = None
    last_failed_sync: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    data_freshness: str = "Real-time"
    message: Optional[str] = None


class SyncHealthResponse(BaseModel):
    providers: List[SyncHealthItem]


class ReconciliationItem(BaseModel):
    provider: str
    product_code: str
    period: str
    provider_reported_amount: float
    database_amount: float
    difference: float
    status: str  # RECONCILED, ATTENTION
    currency: str = "INR"
    notes: Optional[str] = None


class ReconciliationResponse(BaseModel):
    items: List[ReconciliationItem]


class SyncNowRequest(BaseModel):
    provider: Optional[str] = "all"
    product_code: Optional[str] = "all"


class SyncNowResponse(BaseModel):
    success: bool
    provider: str
    message: str
    processed: int = 0
    created: int = 0
    updated: int = 0
    errors: int = 0
    synced_at: datetime


class PaymentEventIngestRequest(BaseModel):
    product_code: str = Field(..., description="Canonical product code (e.g. aisa, ailegal, uwoconnect, efvframework, aiads, other)")
    product_name: Optional[str] = Field(None, description="Human readable product or application name")
    platform: Optional[str] = Field("web", description="Platform: web, ios, android")
    provider: str = Field("razorpay", description="Payment provider or gateway: razorpay, razorpay_efv, app_store, cashfree, manual")
    transaction_id: str = Field(..., description="Unique transaction ID or provider payment ID (e.g. pay_xxx)")
    order_id: Optional[str] = Field(None, description="Order ID (e.g. order_xxx)")
    transaction_type: Optional[str] = Field("payment", description="Transaction type: payment, subscription, refund")
    amount: float = Field(..., gt=0, description="Gross transaction amount in reporting currency")
    tax_amount: Optional[float] = Field(0.0, description="Calculated tax amount (e.g. GST)")
    fee_amount: Optional[float] = Field(0.0, description="Gateway processing fees")
    refund_amount: Optional[float] = Field(0.0, description="Refunded amount if any")
    net_amount: Optional[float] = Field(None, description="Net revenue (amount - tax - fee - refund). If omitted, automatically computed.")
    currency: Optional[str] = Field("INR", description="Currency ISO 3-letter code")
    status: Optional[str] = Field("completed", description="Payment status: completed, captured, paid, pending, failed, refunded")
    customer_id: Optional[str] = Field(None, description="Application customer/user ID")
    customer_email: Optional[str] = Field(None, description="Customer email address")
    customer_name: Optional[str] = Field(None, description="Customer name")
    plan_id: Optional[str] = Field(None, description="Plan ID")
    plan_name: Optional[str] = Field(None, description="Plan name (e.g. Creator, Pro, Founder)")
    billing_cycle: Optional[str] = Field("monthly", description="Billing cycle: monthly, yearly, lifetime")
    transaction_date: Optional[datetime] = Field(None, description="Timestamp of the transaction")
    is_test: Optional[bool] = Field(False, description="Whether this is a test/mock transaction")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional arbitrary metadata (notes, invoice details, etc.)")


class PaymentEventIngestResponse(BaseModel):
    success: bool
    transaction_id: str
    product_code: str
    status: str
    message: str
    created: bool
    updated: bool
    recorded_at: datetime


class CheckoutSessionCreateRequest(BaseModel):
    product_code: str = Field("ailegal", description="Canonical product code (e.g. ailegal, aisa)")
    platform: str = Field("android", description="Platform: android or web")
    plan_id: str = Field("ailegal_pro_monthly", description="Plan ID to subscribe to")
    amount: float = Field(999.0, gt=0, description="Gross amount in INR")
    currency: str = Field("INR", description="Currency code")
    customer_id: Optional[str] = Field(None, description="User ID")
    customer_email: Optional[str] = Field(None, description="User email")
    customer_name: Optional[str] = Field(None, description="User full name")
    callback_url: Optional[str] = Field(None, description="Deep link or web callback URL")


class CheckoutSessionResponse(BaseModel):
    success: bool
    order_id: str
    amount: float
    currency: str
    key_id: str
    product_code: str
    platform: str
    plan_id: str
    checkout_url: str
    callback_url: str
    prefill: Optional[Dict[str, str]] = None


class CheckoutVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: Optional[str] = ""
    product_code: str = "ailegal"
    platform: str = "android"
    provider: str = "razorpay"
    plan_id: Optional[str] = "ailegal_pro_monthly"
    amount: Optional[float] = 999.0
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None


class CheckoutVerifyResponse(BaseModel):
    success: bool
    signature_valid: bool
    product_code: str
    platform: str
    order_id: str
    payment_id: str
    status: str
    plan_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


class AppleVerifyRequest(BaseModel):
    product_code: str = Field("ailegal", description="Canonical product code: ailegal, aisa")
    transaction_id: str = Field(..., description="StoreKit 2 transactionId or originalTransactionId")
    signed_payload: Optional[str] = Field(None, description="StoreKit 2 signed JWS payload (verification.jwsRepresentation)")
    bundle_id: Optional[str] = Field(None, description="App bundle ID (e.g. com.uwo.ailegal)")
    customer_id: Optional[str] = Field(None, description="User ID")
    customer_email: Optional[str] = Field(None, description="User email")
    plan_id: Optional[str] = Field(None, description="StoreKit product ID (e.g. com.uwo.ailegal.pro.monthly)")
    amount: Optional[float] = Field(None, description="Transaction amount if known")
    is_sandbox: bool = Field(False, description="Whether this is an Apple Sandbox transaction")


class AppleVerifyResponse(BaseModel):
    success: bool
    product_code: str
    bundle_id: str
    product_id: str
    transaction_id: str
    original_transaction_id: str
    purchase_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    is_active: bool
    environment: str
    message: str


class AppleNotificationWebhookRequest(BaseModel):
    signedPayload: str = Field(..., description="Signed JWS payload from App Store Server Notifications V2")


class SubscriptionStatusResponse(BaseModel):
    is_active: bool
    product_code: str
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    platform_source: Optional[str] = None  # android, ios, web
    provider: Optional[str] = None         # razorpay, app_store, cashfree
    credits_remaining: int = 5
    expires_at: Optional[datetime] = None
    auto_renew: bool = False
    original_transaction_id: Optional[str] = None
    message: str

