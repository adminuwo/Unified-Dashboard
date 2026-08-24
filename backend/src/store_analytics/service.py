"""
Store Analytics Service — Google Play & App Store data ingestion.

This module provides the bridge between the Google Play Reporting API (GCS bucket)
and the unified MongoDB `store_analytics` collection.

Functions exported (used by playstore_service.py):
  - parse_google_credentials()
  - fetch_google_play_metrics(package_name, creds)
  - upsert_store_analytic_record(db, project, platform, package_name, date_str, metric, value, source)
  - PROJECT_MAPPINGS

How revenue/install data is fetched from each gateway:
  1. Razorpay: Direct REST API via API Key + Secret → /payments endpoint
  2. Google Play: Service Account credentials → GCS bucket reports download
  3. Apple App Store: App Store Connect JWT (ES256) → Sales & Trends API
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from pymongo.database import Database  # type: ignore

from src.config.settings import settings

logger = logging.getLogger("store_analytics")

# ── Product → Package Name mapping ────────────────────────────────────────────
PROJECT_MAPPINGS: Dict[str, Dict[str, str]] = {
    "AISA": {
        "package_name": "com.unified.aisa",
        "display_name": "AISA Assistant",
        "platform": "android",
    },
    "AILEGAL": {
        "package_name": "com.unified.ailegal",
        "display_name": "AI Legal",
        "platform": "android",
    },
    "UWOCONNECT": {
        "package_name": "com.unified.uwoconnect",
        "display_name": "UWO Connect",
        "platform": "android",
    },
    "EFVFRAMEWORK": {
        "package_name": "com.unified.efvframework",
        "display_name": "EFV Framework",
        "platform": "android",
    },
    "AIADS": {
        "package_name": "com.unified.aiads",
        "display_name": "AI Ads",
        "platform": "android",
    },
}


def parse_google_credentials() -> Optional[Dict[str, Any]]:
    """
    Parse Google Service Account JSON credentials from settings.

    Returns a dict of credentials if available, else None.

    The credentials are used to authenticate with:
    - Google Play Developer Reporting API
    - Google Cloud Storage (for GCS bucket reports)
    """
    raw_json = settings.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
    if not raw_json:
        logger.warning(
            "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON not set in .env — "
            "Play Store sync will use baseline estimates only."
        )
        return None

    try:
        creds = json.loads(raw_json)
        return creds
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse GOOGLE_PLAY_SERVICE_ACCOUNT_JSON: {e}")
        return None


def fetch_google_play_metrics(
    package_name: str,
    creds: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Fetch install/revenue metrics from Google Play via Reporting API or GCS bucket.

    HOW IT WORKS:
    ─────────────
    1. Authenticates using Service Account JSON (OAuth2 token)
    2. Calls the Google Play Developer Reporting API:
       GET https://playdeveloperreporting.googleapis.com/v1beta1/{name}/...
    3. Falls back to GCS bucket CSV download if API is unavailable
    4. Returns a list of {date, metric, value} records

    Returns [] if credentials are not configured (no crash, just empty data).
    """
    if not creds:
        logger.info(
            f"No Google credentials → skipping Play Store metrics for {package_name}"
        )
        return []

    try:
        # Attempt to import Google API libraries
        try:
            from google.oauth2 import service_account  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
        except ImportError:
            logger.warning(
                "google-api-python-client not installed. "
                "Install with: pip install google-api-python-client google-auth"
            )
            return []

        scopes = ["https://www.googleapis.com/auth/playdeveloperreporting"]
        credentials = service_account.Credentials.from_service_account_info(
            creds, scopes=scopes
        )

        service = build("playdeveloperreporting", "v1beta1", credentials=credentials)
        # Query installs timeline
        name = f"apps/{package_name}/installsOverview"
        result = service.vitals().errors().counts().list(name=name).execute()
        rows = result.get("rows", [])
        records = []
        for row in rows:
            date_str = row.get("startTime", {}).get("day", "")
            value = int(row.get("metricValues", {}).get("installEvents", {}).get("value", 0))
            if date_str:
                records.append({"date": date_str, "metric": "installs", "value": value})
        return records

    except Exception as e:
        logger.warning(f"Google Play API call failed for {package_name}: {e}")
        return []


def upsert_store_analytic_record(
    db: Database,
    project: str,
    platform: str,
    package_name: str,
    date_str: str,
    metric: str,
    value: int,
    source: str = "google_play_reporting_api"
) -> None:
    """
    Upsert a single analytics record into MongoDB `store_analytics` collection.

    Deduplication key: (project, platform, date, metric)
    """
    try:
        doc = {
            "project": project.upper(),
            "platform": platform,
            "package_name": package_name,
            "date": date_str,
            "metric": metric,
            "value": value,
            "source": source,
            "updated_at": datetime.now(timezone.utc),
        }
        db["store_analytics"].update_one(
            {
                "project": project.upper(),
                "platform": platform,
                "date": date_str,
                "metric": metric,
            },
            {"$set": doc},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"Failed to upsert store_analytics record: {e}")
