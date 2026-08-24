from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseRevenueProvider(ABC):
    """Abstract base provider for all payment and app store revenue sources."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique slug identifying provider (e.g., 'razorpay', 'google_play', 'app_store', 'stripe')."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if credentials and configs are present and valid."""
        pass

    @abstractmethod
    def sync_transactions(
        self,
        product_code: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Synchronize transactions from provider API/reports.
        Returns summary: { 'processed': int, 'created': int, 'updated': int, 'errors': int }
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test API connectivity and credential validity."""
        pass
