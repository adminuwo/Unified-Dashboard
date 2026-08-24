import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("cashfree_client")

class CashfreeClient:
    """Client for interacting with Cashfree Payment Gateway APIs."""
    
    PRODUCTION_URL = "https://api.cashfree.com/pg"
    SANDBOX_URL = "https://sandbox.cashfree.com/pg"

    def __init__(self, app_id: str, secret_key: str, environment: str = "production"):
        self.app_id = app_id.strip() if app_id else ""
        self.secret_key = secret_key.strip() if secret_key else ""
        self.environment = environment.lower().strip()
        self.base_url = self.PRODUCTION_URL if self.environment == "production" else self.SANDBOX_URL

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-api-version": "2023-08-01",
            "x-client-id": self.app_id,
            "x-client-secret": self.secret_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> requests.Response:
        if not self.app_id or not self.secret_key:
            raise ValueError("Cashfree credentials (app_id and secret_key) are not configured.")
        
        url = f"{self.base_url}/{path.lstrip('/')}"
        return requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            params=params,
            json=json_data,
            timeout=20
        )

    def test_credentials(self) -> bool:
        """Test API connectivity and credential validity."""
        try:
            # We fetch a dummy order ID. If credentials are correct, it should return 404 (Not Found) or 200.
            # If credentials are wrong, it should return 401 (Unauthorized) or 403 (Forbidden).
            resp = self._request("GET", "/orders/conn_test_verify_id_123")
            if resp.status_code in [401, 403]:
                return False
            return True
        except Exception as e:
            logger.error(f"Error testing Cashfree credentials: {e}")
            return False

    def fetch_settlements(self, limit: int = 50, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch settlement records from Cashfree PG."""
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
            
        try:
            resp = self._request("GET", "/settlements", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            else:
                logger.error(f"Failed to fetch settlements: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Cashfree settlements: {e}")
            return []

    def fetch_settlement_reconciliation(self, settlement_id: int) -> List[Dict[str, Any]]:
        """Fetch transactions settled under a specific settlement ID."""
        try:
            resp = self._request("GET", f"/settlements/{settlement_id}/reconciliation")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            else:
                logger.error(f"Failed to fetch settlement recon for {settlement_id}: {resp.status_code} {resp.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Cashfree settlement reconciliation: {e}")
            return []
