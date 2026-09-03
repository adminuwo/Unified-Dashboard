import re
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from src.database.connection import get_db_instance
from src.marketing.models import (
    MarketingLinkCreate,
    BatchMarketingLinkCreate,
    MarketingLinkResponse,
    MarketingAnalyticsSummary,
)

def _get_db():
    return get_db_instance()

# Product catalog with human-readable names and default production URLs
PRODUCT_CATALOG: Dict[str, Dict[str, str]] = {
    "aisa": {
        "name": "AISA",
        "url": "https://aisa24.com",
        "description": "Next-Gen Enterprise AI Models & Assistant Platform",
        "color": "#6366F1",
    },
    "aimall": {
        "name": "AI-Mall",
        "url": "https://aimall24.com",
        "description": "Multi-Agent AI Marketplace & Productivity Tools",
        "color": "#8B5CF6",
    },
    "efv": {
        "name": "EFV Franchise",
        "url": "https://efv.uwo24.com",
        "description": "Energy & Financial Verification Franchise Portal",
        "color": "#10B981",
    },
    "ailegal": {
        "name": "AI-Legal",
        "url": "https://ailegal.aisa24.com",
        "description": "AI Legal Assistant & Advocates Practice Suite",
        "color": "#D4AF37",
    },
    "uwo": {
        "name": "UWO Web",
        "url": "https://uwo24.com",
        "description": "Unified Web Options Corporate Portal",
        "color": "#3B82F6",
    },
    "uwoconnect": {
        "name": "UWO Connect",
        "url": "https://connect.uwo24.com",
        "description": "Central Identity, SSO & Organization Security Portal",
        "color": "#EC4899",
    },
    "yugamc": {
        "name": "Yugamc",
        "url": "https://yugamc.com",
        "description": "Enterprise Manufacturing & Global Commerce Platform",
        "color": "#F59E0B",
    },
    "custom": {
        "name": "Custom Destination",
        "url": "",
        "description": "Custom Landing Page / Sub-Page / Event URL",
        "color": "#94A3B8",
    },
}

PLATFORM_CONFIG: Dict[str, Dict[str, str]] = {
    "instagram": {"name": "Instagram", "icon": "📸", "default_medium": "social", "color": "#E1306C"},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "default_medium": "social", "color": "#0A66C2"},
    "youtube": {"name": "YouTube", "icon": "▶️", "default_medium": "video", "color": "#FF0000"},
    "twitter": {"name": "Twitter / X", "icon": "🐦", "default_medium": "social", "color": "#1DA1F2"},
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "default_medium": "chat", "color": "#25D366"},
    "meta_ads": {"name": "Meta Ads (FB/IG)", "icon": "📢", "default_medium": "cpc", "color": "#1877F2"},
    "google_ads": {"name": "Google Ads", "icon": "🎯", "default_medium": "cpc", "color": "#4285F4"},
    "reddit": {"name": "Reddit", "icon": "🤖", "default_medium": "community", "color": "#FF4500"},
    "telegram": {"name": "Telegram", "icon": "✈️", "default_medium": "chat", "color": "#0088CC"},
    "email": {"name": "Newsletter / Email", "icon": "✉️", "default_medium": "email", "color": "#64748B"},
    "influencer": {"name": "Influencer Collab", "icon": "⭐", "default_medium": "influencer", "color": "#A855F7"},
    "other": {"name": "Custom Referral", "icon": "🔗", "default_medium": "referral", "color": "#475569"},
}


class MarketingService:
    @staticmethod
    def _sanitize_slug(text: str) -> str:
        """Convert any string into an alphanumeric, URL-safe slug."""
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\-_]+', '-', text)
        return re.sub(r'-+', '-', text).strip('-')

    @staticmethod
    def _generate_unique_slug(product_id: str, platform: str, post_name: str, custom_slug: Optional[str] = None) -> str:
        db = _get_db()
        if custom_slug and custom_slug.strip():
            candidate = MarketingService._sanitize_slug(custom_slug)
            if not db.marketing_links.find_one({"slug": candidate}):
                return candidate

        # Generate smart readable slug: {platform_prefix}-{post_part}-{random_hash}
        p_prefix = platform[:3].lower()
        prod_prefix = product_id[:4].lower()
        post_part = MarketingService._sanitize_slug(post_name)[:12]
        rand_suffix = uuid.uuid4().hex[:5]

        base = f"{prod_prefix}-{p_prefix}-{post_part}".strip('-')
        slug = f"{base}-{rand_suffix}"

        while db.marketing_links.find_one({"slug": slug}):
            slug = f"{base}-{uuid.uuid4().hex[:6]}"

        return slug

    @staticmethod
    def _build_full_utm_url(base_url: str, platform: str, campaign: str, post_name: str, channel_type: str, slug: str) -> str:
        """Appends standardized UTM parameters and referral slug to base target URL."""
        parsed = urlparse(base_url)
        query_dict = dict(parse_qsl(parsed.query))

        platform_info = PLATFORM_CONFIG.get(platform, {"default_medium": "social"})

        query_dict["utm_source"] = platform.lower()
        query_dict["utm_medium"] = platform_info.get("default_medium", "social")
        query_dict["utm_campaign"] = MarketingService._sanitize_slug(campaign)
        query_dict["utm_content"] = MarketingService._sanitize_slug(post_name)
        if channel_type and channel_type != "organic":
            query_dict["utm_term"] = channel_type
        query_dict["ref"] = slug

        new_query = urlencode(query_dict)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    @staticmethod
    def create_link(data: MarketingLinkCreate, base_request_url: str = "", creator: str = "Admin") -> Dict[str, Any]:
        db = _get_db()

        # Resolve target base URL
        product_info = PRODUCT_CATALOG.get(data.product_id, PRODUCT_CATALOG["custom"])
        target_url = data.custom_target_url if data.product_id == "custom" and data.custom_target_url else product_info["url"]
        if not target_url:
            target_url = data.custom_target_url or "https://aisa24.com"

        # Ensure scheme
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "https://" + target_url

        slug = MarketingService._generate_unique_slug(
            product_id=data.product_id,
            platform=data.platform,
            post_name=data.post_name,
            custom_slug=data.custom_slug
        )

        full_dest = MarketingService._build_full_utm_url(
            base_url=target_url,
            platform=data.platform,
            campaign=data.campaign_name,
            post_name=data.post_name,
            channel_type=data.channel_type or "organic",
            slug=slug
        )

        now = datetime.now(timezone.utc)
        doc = {
            "slug": slug,
            "product_id": data.product_id,
            "product_name": data.product_name or product_info["name"],
            "target_url": target_url,
            "full_destination_url": full_dest,
            "platform": data.platform.lower(),
            "campaign_name": data.campaign_name.strip(),
            "post_name": data.post_name.strip(),
            "channel_type": data.channel_type or "organic",
            "notes": data.notes or "",
            "total_clicks": 0,
            "unique_clicks": 0,
            "unique_ips": [],
            "is_active": True,
            "created_by": creator,
            "created_at": now,
            "updated_at": now,
            "last_clicked_at": None,
        }

        res = db.marketing_links.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        doc["id"] = str(res.inserted_id)
        
        # Build short redirect URL
        base_host = base_request_url.rstrip('/') if base_request_url else ""
        doc["short_url"] = f"{base_host}/r/{slug}" if base_host else f"/r/{slug}"
        return doc

    @staticmethod
    def create_batch_links(data: BatchMarketingLinkCreate, base_request_url: str = "", creator: str = "Admin") -> List[Dict[str, Any]]:
        created = []
        for p in data.platforms:
            single_item = MarketingLinkCreate(
                product_id=data.product_id,
                custom_target_url=data.custom_target_url,
                platform=p,
                campaign_name=data.campaign_name,
                post_name=data.post_name,
                channel_type=data.channel_type,
                notes=data.notes,
            )
            link_doc = MarketingService.create_link(single_item, base_request_url=base_request_url, creator=creator)
            created.append(link_doc)
        return created

    @staticmethod
    def list_links(
        search: Optional[str] = None,
        product_id: Optional[str] = None,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        base_request_url: str = ""
    ) -> List[Dict[str, Any]]:
        db = _get_db()
        query: Dict[str, Any] = {}

        if product_id and product_id != "all":
            query["product_id"] = product_id

        if platform and platform != "all":
            query["platform"] = platform.lower()

        if is_active is not None:
            query["is_active"] = is_active

        if search and search.strip():
            s_term = search.strip()
            query["$or"] = [
                {"post_name": {"$regex": s_term, "$options": "i"}},
                {"campaign_name": {"$regex": s_term, "$options": "i"}},
                {"slug": {"$regex": s_term, "$options": "i"}},
                {"product_name": {"$regex": s_term, "$options": "i"}},
            ]

        cursor = db.marketing_links.find(query).sort("created_at", -1).limit(limit)
        results = []
        base_host = base_request_url.rstrip('/') if base_request_url else ""

        for item in cursor:
            item["id"] = str(item["_id"])
            item["_id"] = str(item["_id"])
            item.pop("unique_ips", None)
            item["short_url"] = f"{base_host}/r/{item['slug']}" if base_host else f"/r/{item['slug']}"
            results.append(item)

        return results

    @staticmethod
    def parse_user_agent(ua_string: str) -> Dict[str, str]:
        """Categorize client device, OS, and browser from User-Agent."""
        if not ua_string:
            return {"device": "Desktop", "os": "Unknown", "browser": "Direct / Unknown"}

        ua = ua_string.lower()

        # Device
        if any(w in ua for w in ["iphone", "android", "mobile", "ipod", "blackberry"]):
            device = "Mobile"
        elif "ipad" in ua or "tablet" in ua:
            device = "Tablet"
        else:
            device = "Desktop"

        # OS
        if "windows" in ua:
            os_name = "Windows"
        elif "macintosh" in ua or "mac os" in ua:
            os_name = "macOS"
        elif "android" in ua:
            os_name = "Android"
        elif "iphone" in ua or "ipad" in ua or "ios" in ua:
            os_name = "iOS"
        elif "linux" in ua:
            os_name = "Linux"
        else:
            os_name = "Other"

        # In-App / Social Browser detection
        if "instagram" in ua:
            browser = "Instagram In-App"
        elif "linkedin" in ua:
            browser = "LinkedIn Webview"
        elif "whatsapp" in ua:
            browser = "WhatsApp"
        elif "fban" in ua or "fbav" in ua:
            browser = "Facebook App"
        elif "chrome" in ua and "safari" in ua:
            browser = "Chrome"
        elif "safari" in ua and "chrome" not in ua:
            browser = "Safari"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "edg" in ua:
            browser = "Edge"
        else:
            browser = "Browser"

        return {"device": device, "os": os_name, "browser": browser}

    @staticmethod
    def record_click(slug: str, ip: str, user_agent: str, referrer: Optional[str] = None) -> Optional[str]:
        """Logs click telemetry asynchronously and returns destination URL for redirect."""
        db = _get_db()
        link = db.marketing_links.find_one({"slug": slug})

        if not link or not link.get("is_active", True):
            return None

        now = datetime.now(timezone.utc)
        ip_hash = hashlib.sha256((ip or "127.0.0.1").encode()).hexdigest()[:16]

        ua_parsed = MarketingService.parse_user_agent(user_agent)

        click_doc = {
            "link_id": str(link["_id"]),
            "slug": slug,
            "product_id": link.get("product_id"),
            "platform": link.get("platform"),
            "campaign_name": link.get("campaign_name"),
            "post_name": link.get("post_name"),
            "timestamp": now,
            "ip_hash": ip_hash,
            "user_agent": user_agent[:250] if user_agent else None,
            "device_type": ua_parsed["device"],
            "os": ua_parsed["os"],
            "browser": ua_parsed["browser"],
            "referrer": referrer[:200] if referrer else None,
        }

        db.marketing_clicks.insert_one(click_doc)

        # Check unique click
        is_unique = False
        unique_ips = link.get("unique_ips", [])
        if ip_hash not in unique_ips:
            is_unique = True
            db.marketing_links.update_one(
                {"_id": link["_id"]},
                {
                    "$inc": {"total_clicks": 1, "unique_clicks": 1},
                    "$push": {"unique_ips": {"$each": [ip_hash], "$slice": -5000}},
                    "$set": {"last_clicked_at": now},
                }
            )
        else:
            db.marketing_links.update_one(
                {"_id": link["_id"]},
                {
                    "$inc": {"total_clicks": 1},
                    "$set": {"last_clicked_at": now},
                }
            )

        return link.get("full_destination_url") or link.get("target_url")

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        """Returns overall marketing KPI cards, top performing posts, and platform distribution."""
        db = _get_db()

        total_links = db.marketing_links.count_documents({})
        total_clicks = db.marketing_clicks.count_documents({})

        # Unique reach across all clicks
        unique_reach = len(db.marketing_clicks.distinct("ip_hash"))

        # Platform distribution aggregation
        platform_pipeline = [
            {"$group": {"_id": "$platform", "clicks": {"$sum": 1}}},
            {"$sort": {"clicks": -1}}
        ]
        platform_raw = list(db.marketing_clicks.aggregate(platform_pipeline))
        platform_dist = []
        for p in platform_raw:
            pid = p["_id"] or "other"
            info = PLATFORM_CONFIG.get(pid, {"name": pid.capitalize(), "icon": "🔗", "color": "#64748B"})
            share = round((p["clicks"] / total_clicks * 100), 1) if total_clicks > 0 else 0
            platform_dist.append({
                "platform": pid,
                "name": info.get("name", pid.capitalize()),
                "icon": info.get("icon", "🔗"),
                "color": info.get("color", "#64748B"),
                "clicks": p["clicks"],
                "share_pct": share
            })

        # Product distribution aggregation
        product_pipeline = [
            {"$group": {"_id": "$product_id", "clicks": {"$sum": 1}}},
            {"$sort": {"clicks": -1}}
        ]
        product_raw = list(db.marketing_clicks.aggregate(product_pipeline))
        product_dist = []
        for pr in product_raw:
            pr_id = pr["_id"] or "custom"
            info = PRODUCT_CATALOG.get(pr_id, {"name": pr_id.capitalize(), "color": "#94A3B8"})
            share = round((pr["clicks"] / total_clicks * 100), 1) if total_clicks > 0 else 0
            product_dist.append({
                "product_id": pr_id,
                "name": info.get("name", pr_id.capitalize()),
                "color": info.get("color", "#94A3B8"),
                "clicks": pr["clicks"],
                "share_pct": share
            })

        # Device distribution
        device_pipeline = [
            {"$group": {"_id": "$device_type", "clicks": {"$sum": 1}}},
            {"$sort": {"clicks": -1}}
        ]
        device_raw = list(db.marketing_clicks.aggregate(device_pipeline))
        device_dist = [{"device": d["_id"] or "Unknown", "clicks": d["clicks"]} for d in device_raw]

        # Top Performing Post / Link
        top_post_doc = db.marketing_links.find({}).sort("total_clicks", -1).limit(1)
        top_post = None
        for tp in top_post_doc:
            top_post = {
                "id": str(tp["_id"]),
                "post_name": tp.get("post_name"),
                "campaign_name": tp.get("campaign_name"),
                "product_name": tp.get("product_name"),
                "platform": tp.get("platform"),
                "total_clicks": tp.get("total_clicks", 0),
                "unique_clicks": tp.get("unique_clicks", 0),
            }

        # Top Product & Top Platform
        top_prod = product_dist[0] if product_dist else None
        top_plat = platform_dist[0] if platform_dist else None

        # Recent 10 Clicks stream
        recent_clicks = list(
            db.marketing_clicks.find({})
            .sort("timestamp", -1)
            .limit(10)
        )
        for rc in recent_clicks:
            rc["id"] = str(rc["_id"])
            rc["_id"] = str(rc["_id"])

        return {
            "total_links": total_links,
            "total_clicks": total_clicks,
            "unique_reach": unique_reach,
            "top_product": top_prod,
            "top_platform": top_plat,
            "top_post": top_post,
            "platform_distribution": platform_dist,
            "product_distribution": product_dist,
            "device_distribution": device_dist,
            "recent_clicks": recent_clicks,
            "catalog": PRODUCT_CATALOG,
            "platforms": PLATFORM_CONFIG,
        }

    @staticmethod
    def get_link_details(link_id: str, base_request_url: str = "") -> Optional[Dict[str, Any]]:
        db = _get_db()
        from bson import ObjectId
        try:
            link = db.marketing_links.find_one({"_id": ObjectId(link_id)})
        except Exception:
            link = db.marketing_links.find_one({"slug": link_id})

        if not link:
            return None

        link["id"] = str(link["_id"])
        link["_id"] = str(link["_id"])
        base_host = base_request_url.rstrip('/') if base_request_url else ""
        link["short_url"] = f"{base_host}/r/{link['slug']}" if base_host else f"/r/{link['slug']}"

        # Get device and browser breakdown for this link
        clicks = list(db.marketing_clicks.find({"slug": link["slug"]}).sort("timestamp", -1).limit(50))
        for c in clicks:
            c["id"] = str(c["_id"])
            c["_id"] = str(c["_id"])

        return {"link": link, "recent_clicks": clicks}

    @staticmethod
    def toggle_status(link_id: str, is_active: bool) -> bool:
        db = _get_db()
        from bson import ObjectId
        try:
            res = db.marketing_links.update_one(
                {"_id": ObjectId(link_id)},
                {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc)}}
            )
            return res.modified_count > 0
        except Exception:
            return False

    @staticmethod
    def delete_link(link_id: str) -> bool:
        db = _get_db()
        from bson import ObjectId
        try:
            link = db.marketing_links.find_one({"_id": ObjectId(link_id)})
            if link:
                db.marketing_clicks.delete_many({"slug": link["slug"]})
                db.marketing_links.delete_one({"_id": ObjectId(link_id)})
                return True
        except Exception:
            pass
        return False
