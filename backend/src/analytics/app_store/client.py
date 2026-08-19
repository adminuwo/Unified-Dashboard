import requests
import time
from typing import Dict, Any, Optional

from src.analytics.app_store.auth import AppStoreConnectAuth

class AppStoreConnectClient:
    BASE_URL = "https://api.appstoreconnect.apple.com/v1"
    
    def __init__(self, auth: AppStoreConnectAuth):
        self.auth = auth
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        token = self.auth.generate_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        max_retries = 3
        
        for attempt in range(max_retries):
            headers = self._get_headers()
            response = self.session.request(method, url, headers=headers, **kwargs)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            return response
            
        raise Exception(f"Max retries exceeded for {url}")

    def get_apps(self) -> Dict[str, Any]:
        res = self._request("GET", "/apps")
        return res.json()
        
    def get_report_requests(self, filter_app_id: str) -> Dict[str, Any]:
        res = self._request("GET", f"/analyticsReportRequests?filter[app]={filter_app_id}")
        return res.json()
        
    def get_reports(self, request_id: str) -> Dict[str, Any]:
        res = self._request("GET", f"/analyticsReportRequests/{request_id}/reports")
        return res.json()

    def get_instances(self, report_id: str) -> Dict[str, Any]:
        res = self._request("GET", f"/analyticsReports/{report_id}/instances")
        return res.json()

    def get_segments(self, instance_id: str) -> Dict[str, Any]:
        res = self._request("GET", f"/analyticsReportInstances/{instance_id}/segments")
        return res.json()
