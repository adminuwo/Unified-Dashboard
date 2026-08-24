import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database  # type: ignore

from src.config.settings import settings
from src.integrations.base import BaseRevenueProvider

logger = logging.getLogger("stripe_provider")


class StripeProvider(BaseRevenueProvider):
    """Pluggable Stripe Provider (Disabled by default)."""

    def __init__(self, db: Database):
        self.db = db
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.enabled = settings.STRIPE_ENABLED

    @property
    def provider_name(self) -> str:
        return "stripe"

    def is_configured(self) -> bool:
        return bool(self.enabled and self.secret_key)

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"healthy": False, "message": "Stripe is disabled or secret key not configured."}
        return {"healthy": True, "message": "Stripe module loaded (inactive)."}

    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "message": "Stripe is disabled or not configured in settings.",
                "processed": 0,
                "created": 0,
                "updated": 0,
                "errors": 0
            }
        return {"success": True, "processed": 0, "created": 0, "updated": 0, "errors": 0}
