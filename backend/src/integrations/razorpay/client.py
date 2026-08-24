import time
import hmac
import hashlib
import logging
from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("razorpay_client")


class RazorpayClient:
    """Client for interacting with official Razorpay REST APIs."""
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self, key_id: str, key_secret: str, webhook_secret: Optional[str] = None):
        self.key_id = key_id.strip() if key_id else ""
        self.key_secret = key_secret.strip() if key_secret else ""
        self.webhook_secret = webhook_secret.strip() if webhook_secret else ""
        self.auth = HTTPBasicAuth(self.key_id, self.key_secret) if self.key_id and self.key_secret else None

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.auth:
            raise ValueError("Razorpay credentials (key_id and key_secret) are not configured.")

        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    params=params,
                    json=json_data,
                    timeout=20
                )
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", int(backoff)))
                    logger.warning(f"Razorpay rate limit hit. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    backoff *= 2
                    continue

                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Razorpay request failed permanently: {method} {url}: {e}")
                    raise
                time.sleep(backoff)
                backoff *= 2

        raise Exception(f"Failed to complete request to Razorpay endpoint {path}")

    def fetch_payments(self, count: int = 100, skip: int = 0, from_ts: Optional[int] = None, to_ts: Optional[int] = None) -> Dict[str, Any]:
        """Fetch list of payments from Razorpay API."""
        params: Dict[str, Any] = {"count": count, "skip": skip}
        if from_ts:
            params["from"] = from_ts
        if to_ts:
            params["to"] = to_ts
        return self._request("GET", "/payments", params=params)

    def fetch_payment_by_id(self, payment_id: str) -> Dict[str, Any]:
        """Fetch details of a single payment."""
        return self._request("GET", f"/payments/{payment_id}")

    def fetch_refunds(self, count: int = 100, skip: int = 0, from_ts: Optional[int] = None, to_ts: Optional[int] = None) -> Dict[str, Any]:
        """Fetch refunds list."""
        params: Dict[str, Any] = {"count": count, "skip": skip}
        if from_ts:
            params["from"] = from_ts
        if to_ts:
            params["to"] = to_ts
        return self._request("GET", "/refunds", params=params)

    def fetch_subscriptions(self, count: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Fetch recurring subscriptions list."""
        params: Dict[str, Any] = {"count": count, "skip": skip}
        return self._request("GET", "/subscriptions", params=params)

    def fetch_settlements(self, count: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Fetch bank settlements / payouts."""
        params: Dict[str, Any] = {"count": count, "skip": skip}
        return self._request("GET", "/settlements", params=params)

    def fetch_invoices(self, count: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Fetch invoices."""
        params: Dict[str, Any] = {"count": count, "skip": skip}
        return self._request("GET", "/invoices", params=params)

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature for incoming webhooks."""
        if not self.webhook_secret or not signature:
            return False
        expected = hmac.new(self.webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
