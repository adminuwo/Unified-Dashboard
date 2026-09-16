import re
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse, unquote

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
        "play_store_url": "https://play.google.com/store/apps/details?id=com.uwo.aisa",
        "app_store_url": "https://apps.apple.com/app/id6779135418",
        "web_url": "https://aisa24.com",
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
        "play_store_url": "https://play.google.com/store/apps/details?id=com.uwo.ailegal",
        "app_store_url": "https://apps.apple.com/app/id6797449251",
        "web_url": "https://ailegal.aisa24.com",
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

        # If targeting Google Play, ensure Play Store referrer param carries the attribution token
        if "play.google.com" in parsed.netloc or "play.google.com" in base_url:
            inner_ref = f"utm_source={query_dict.get('utm_source', 'referral')}&utm_campaign={query_dict.get('utm_campaign', 'campaign')}&slug={slug}&ref={slug}"
            query_dict["referrer"] = inner_ref

        new_query = urlencode(query_dict)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    @staticmethod
    def create_link(data: MarketingLinkCreate, base_request_url: str = "", creator: str = "Admin") -> Dict[str, Any]:
        db = _get_db()

        product_info = PRODUCT_CATALOG.get(data.product_id, PRODUCT_CATALOG["custom"])

        # Resolve smart link flags & platform URLs
        is_smart = bool(
            data.is_smart_link 
            or (data.custom_target_url and "smart_app" in data.custom_target_url.lower())
            or (data.android_url and data.ios_url)
        )
        android_url = (data.android_url or "").strip() or product_info.get("play_store_url")
        ios_url = (data.ios_url or "").strip() or product_info.get("app_store_url")
        web_url = (data.web_url or "").strip() or product_info.get("web_url") or product_info.get("url") or "https://aisa24.com"

        # Resolve target base URL (ALWAYS honor custom_target_url if provided unless it is smart_app placeholder)
        if data.custom_target_url and data.custom_target_url.strip() and data.custom_target_url.strip() != "smart_app":
            target_url = data.custom_target_url.strip()
        elif is_smart and web_url:
            target_url = web_url
        else:
            target_url = product_info.get("url") or "https://aisa24.com" 

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
            "is_smart_link": is_smart,
            "android_url": android_url if is_smart else None,
            "ios_url": ios_url if is_smart else None,
            "web_url": web_url if is_smart else None,
            "total_clicks": 0,
            "unique_clicks": 0,
            "unique_ips": [],
            "total_downloads": 0,
            "android_downloads": 0,
            "ios_downloads": 0,
            "unique_installs": 0,
            "unique_devices": [],
            "is_active": True,
            "created_by": creator,
            "created_at": now,
            "updated_at": now,
            "last_clicked_at": None,
            "last_downloaded_at": None,
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
                is_smart_link=data.is_smart_link,
                android_url=data.android_url,
                ios_url=data.ios_url,
                web_url=data.web_url,
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
            item.pop("unique_devices", None)
            item["total_downloads"] = int(item.get("total_downloads") or 0)
            item["android_downloads"] = int(item.get("android_downloads") or 0)
            item["ios_downloads"] = int(item.get("ios_downloads") or 0)
            item["unique_installs"] = int(item.get("unique_installs") or 0)
            total_c = item.get("total_clicks", 0)
            item["conversion_rate"] = round((item["total_downloads"] / total_c * 100), 1) if total_c > 0 else 0.0
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
    def generate_fingerprint(
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device: Optional[str] = None,
        os: Optional[str] = None,
    ) -> str:
        """Generates a deterministic digital fingerprint from client signals."""
        raw = f"{ip or ''}|{user_agent or ''}|{device or ''}|{os or ''}"
        return f"fp_{hashlib.sha256(raw.encode()).hexdigest()[:20]}"

    @staticmethod
    def record_click(
        slug: str,
        ip: str,
        user_agent: str,
        referrer: Optional[str] = None,
        fingerprint: Optional[str] = None,
    ) -> Optional[str]:
        """Logs click telemetry asynchronously and returns destination URL for redirect."""
        db = _get_db()
        link = db.marketing_links.find_one({"slug": slug})

        if not link or not link.get("is_active", True):
            return None

        now = datetime.now(timezone.utc)
        clean_ip = (ip or "").strip()
        ip_hash = hashlib.sha256((clean_ip or "127.0.0.1").encode()).hexdigest()[:16]

        ua_parsed = MarketingService.parse_user_agent(user_agent)

        clean_fp = (fingerprint or "").strip()
        if not clean_fp and (clean_ip or user_agent):
            clean_fp = MarketingService.generate_fingerprint(
                ip=clean_ip,
                user_agent=user_agent,
                device=ua_parsed.get("device"),
                os=ua_parsed.get("os"),
            )

        click_doc = {
            "link_id": str(link["_id"]),
            "slug": slug,
            "product_id": link.get("product_id"),
            "platform": link.get("platform"),
            "campaign_name": link.get("campaign_name"),
            "post_name": link.get("post_name"),
            "timestamp": now,
            "client_ip": clean_ip or None,
            "ip_hash": ip_hash,
            "fingerprint": clean_fp or None,
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

        dest_url = link.get("full_destination_url") or link.get("target_url")
        if link.get("is_smart_link"):
            os_name = (ua_parsed.get("os") or "").lower()
            raw_ua = (user_agent or "").lower()
            prod_info = PRODUCT_CATALOG.get(link.get("product_id"), {})

            if "android" in os_name or "android" in raw_ua:
                dest_url = link.get("android_url") or prod_info.get("play_store_url") or dest_url
            elif "ios" in os_name or "iphone" in raw_ua or "ipad" in raw_ua:
                dest_url = link.get("ios_url") or prod_info.get("app_store_url") or dest_url
            else:
                dest_url = link.get("web_url") or prod_info.get("web_url") or link.get("target_url") or dest_url

        if dest_url and "play.google.com" in dest_url and "referrer=" not in dest_url:
            sep = "&" if "?" in dest_url else "?"
            platform_tag = link.get("platform") or "custom_referral"
            dest_url = f"{dest_url}{sep}referrer=utm_source%3D{platform_tag}%26slug%3D{slug}%26ref%3D{slug}"
        return dest_url

    @staticmethod
    def record_install(
        slug: Optional[str] = None,
        product_id: Optional[str] = None,
        install_referrer: Optional[str] = None,
        platform: str = "android",
        device_id: Optional[str] = None,
        version: Optional[str] = None,
        ip: Optional[str] = None,
        referral_code: Optional[str] = None,
        ref_code: Optional[str] = None,
        app_code: Optional[str] = None,
        user_id: Optional[str] = None,
        fingerprint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records verified app install telemetry from mobile app install referrer or iOS IP/fingerprint matching."""
        db = _get_db()
        now = datetime.now(timezone.utc)

        # 1. Resolve effective slug from slug, referral_code, ref_code
        target_slug = (slug or referral_code or ref_code or "").strip()
        effective_product = (product_id or app_code or "").strip().lower()

        norm_platform = (platform or "android").strip().lower()
        if "ios" in norm_platform or "iphone" in norm_platform or "ipad" in norm_platform:
            norm_platform = "ios"
        elif "android" in norm_platform:
            norm_platform = "android"

        attribution_method = "direct" if target_slug else ("referrer_param" if install_referrer else "none")

        # 2. Extract slug from install_referrer if not explicitly passed
        if not target_slug and install_referrer:
            raw_ref = str(install_referrer).strip()
            decoded_ref = unquote(raw_ref)

            # Try matching on both decoded and raw strings
            for candidate_str in [decoded_ref, raw_ref]:
                match = re.search(r'(?:slug|ref_id|ref_code|referral_code|ref|utm_content)=([a-zA-Z0-9_\-]+)', candidate_str, re.IGNORECASE)
                if match:
                    target_slug = match.group(1).strip()
                    attribution_method = "install_referrer"
                    break

        link = None
        if target_slug:
            # Exact match, case-insensitive match, or prefix strip
            link = db.marketing_links.find_one({"slug": target_slug})
            if not link:
                link = db.marketing_links.find_one({"slug": {"$regex": f"^{re.escape(target_slug)}$", "$options": "i"}})
            if not link and target_slug.lower().startswith("ref-"):
                link = db.marketing_links.find_one({"slug": {"$regex": f"^{re.escape(target_slug[4:])}$", "$options": "i"}})

        # 3. Probabilistic Attribution (Strictly iOS only):
        # Android strictly requires the official Google Play Install Referrer API.
        # iOS has no install referrer API, so it uses 72-hour probabilistic IP and fingerprint matching.
        clean_ip = (ip or "").strip()
        clean_fp = (fingerprint or "").strip()

        if not link and norm_platform == "ios" and (clean_ip or clean_fp):
            ip_hash = hashlib.sha256(clean_ip.encode()).hexdigest()[:16] if clean_ip else ""
            time_window = now - timedelta(hours=72)

            prod_filter: Dict[str, Any] = {}
            if effective_product and effective_product not in ["unknown", "custom"]:
                norm_pid = effective_product.replace("-", "").replace("_", "")
                patterns = [effective_product, norm_pid]
                if norm_pid in ["ailegal", "ai-legal", "legal"]:
                    patterns.extend(["ailegal", "ai-legal"])
                elif norm_pid in ["aisa"]:
                    patterns.extend(["aisa"])
                prod_filter = {"product_id": {"$in": list(set(patterns))}}

            candidate_click = None
            matched_method = None

            # Priority 1: Both IP and Fingerprint match
            if clean_ip and clean_fp:
                both_query: Dict[str, Any] = {
                    "$and": [
                        {"$or": [{"client_ip": clean_ip}, {"ip_hash": ip_hash}]},
                        {"fingerprint": clean_fp}
                    ],
                    "timestamp": {"$gte": time_window},
                    **prod_filter
                }
                candidate_click = db.marketing_clicks.find_one(both_query, sort=[("timestamp", -1)])
                if not candidate_click and prod_filter:
                    # Fallback without product filter
                    both_query_gen = {
                        "$and": [
                            {"$or": [{"client_ip": clean_ip}, {"ip_hash": ip_hash}]},
                            {"fingerprint": clean_fp}
                        ],
                        "timestamp": {"$gte": time_window}
                    }
                    candidate_click = db.marketing_clicks.find_one(both_query_gen, sort=[("timestamp", -1)])
                if candidate_click:
                    matched_method = "ip_fingerprint_match"

            # Priority 2: Fingerprint alone matches (e.g. user rotated network/Wi-Fi after click)
            if not candidate_click and clean_fp:
                fp_query: Dict[str, Any] = {
                    "fingerprint": clean_fp,
                    "timestamp": {"$gte": time_window},
                    **prod_filter
                }
                candidate_click = db.marketing_clicks.find_one(fp_query, sort=[("timestamp", -1)])
                if not candidate_click and prod_filter:
                    fp_query_gen = {
                        "fingerprint": clean_fp,
                        "timestamp": {"$gte": time_window}
                    }
                    candidate_click = db.marketing_clicks.find_one(fp_query_gen, sort=[("timestamp", -1)])
                if candidate_click:
                    matched_method = "fingerprint_match"

            # Priority 3: IP alone matches (e.g. fingerprint not provided or changed)
            if not candidate_click and clean_ip:
                ip_query: Dict[str, Any] = {
                    "$or": [
                        {"client_ip": clean_ip},
                        {"ip_hash": ip_hash}
                    ],
                    "timestamp": {"$gte": time_window},
                    **prod_filter
                }
                candidate_click = db.marketing_clicks.find_one(ip_query, sort=[("timestamp", -1)])
                if not candidate_click:
                    # Fallback to any recent mobile/OS click from this IP
                    os_query = {
                        "$or": [
                            {"os": {"$in": ["iOS", "ios"]}},
                            {"device_type": "Mobile"},
                            {"client_ip": clean_ip},
                            {"ip_hash": ip_hash}
                        ],
                        "timestamp": {"$gte": time_window}
                    }
                    candidate_click = db.marketing_clicks.find_one(os_query, sort=[("timestamp", -1)])
                if candidate_click:
                    matched_method = "ip_match"

            if candidate_click and candidate_click.get("slug"):
                found_slug = candidate_click["slug"]
                link = db.marketing_links.find_one({"slug": found_slug})
                if link:
                    target_slug = found_slug
                    attribution_method = matched_method or "ip_match"

        dev_key = device_id or clean_fp or (f"{clean_ip}_{norm_platform}" if clean_ip else str(uuid.uuid4()))
        resolved_product = (link.get("product_id") if link else effective_product) or "unknown"
        link_id_str = str(link["_id"]) if link else None
        clean_device = (device_id or "").strip()

        # Multi-Tier Deduplication & Reinstall Detection
        is_reinstall = False
        duplicate_reason = None
        matched_previous_id = None

        # Check 1: Explicit Device ID match
        if clean_device and clean_device not in ["unknown", "undefined", "null"]:
            if link and clean_device in (link.get("unique_devices") or []):
                is_reinstall = True
                duplicate_reason = "device_id_in_link"
            else:
                q: Dict[str, Any] = {"device_id": clean_device}
                if link_id_str:
                    q["$or"] = [{"link_id": link_id_str}, {"slug": target_slug}, {"product_id": resolved_product}]
                else:
                    q["product_id"] = resolved_product
                prev = db.marketing_installs.find_one(q, sort=[("timestamp", -1)])
                if prev:
                    is_reinstall = True
                    duplicate_reason = "device_id_match"
                    matched_previous_id = str(prev.get("_id"))

        # Check 2: Device Fingerprint match
        if not is_reinstall and clean_fp and clean_fp not in ["unknown", "undefined", "null"]:
            if link and clean_fp in (link.get("unique_fingerprints") or []):
                is_reinstall = True
                duplicate_reason = "fingerprint_in_link"
            else:
                q_fp: Dict[str, Any] = {"fingerprint": clean_fp}
                if link_id_str:
                    q_fp["$or"] = [{"link_id": link_id_str}, {"slug": target_slug}, {"product_id": resolved_product}]
                else:
                    q_fp["product_id"] = resolved_product
                prev = db.marketing_installs.find_one(q_fp, sort=[("timestamp", -1)])
                if prev:
                    is_reinstall = True
                    duplicate_reason = "fingerprint_match"
                    matched_previous_id = str(prev.get("_id"))

        # Check 3: Authenticated User ID match
        if not is_reinstall and user_id and str(user_id).strip() not in ["", "none", "null"]:
            prev = db.marketing_installs.find_one({"user_id": str(user_id).strip(), "product_id": resolved_product})
            if prev:
                is_reinstall = True
                duplicate_reason = "user_id_match"
                matched_previous_id = str(prev.get("_id"))

        # Check 4: IP + Referral Link / Product Heuristic
        # Detects uninstalls and reinstalls where client device_id generated a new ephemeral UUID (dev_...)
        if not is_reinstall and clean_ip and clean_ip not in ["127.0.0.1", "localhost"]:
            ip_query: Dict[str, Any] = {
                "ip": clean_ip,
                "platform": norm_platform,
            }
            if link_id_str:
                ip_query["$or"] = [{"link_id": link_id_str}, {"slug": target_slug}]
            else:
                ip_query["product_id"] = resolved_product

            prev = db.marketing_installs.find_one(ip_query, sort=[("timestamp", -1)])
            if prev:
                prev_dev = prev.get("device_id") or ""
                # If both have verified distinct hardware IDs (android_... or idfv_), they are separate devices on the same Wi-Fi.
                # If either has an ephemeral dev_ prefix or matching ID or missing, it is a reinstall.
                is_both_distinct_hardware = (
                    clean_device.startswith("android_") and prev_dev.startswith("android_") and clean_device != prev_dev
                ) or (
                    clean_device.startswith("idfv_") and prev_dev.startswith("idfv_") and clean_device != prev_dev
                )
                if not is_both_distinct_hardware:
                    is_reinstall = True
                    duplicate_reason = "ip_referral_reinstall_heuristic"
                    matched_previous_id = str(prev.get("_id"))

        is_unique = not is_reinstall

        install_doc = {
            "link_id": link_id_str,
            "slug": target_slug or "unknown",
            "product_id": resolved_product,
            "platform": norm_platform,
            "device_id": clean_device or None,
            "fingerprint": clean_fp or None,
            "install_referrer": install_referrer,
            "version": version or "1.0.0",
            "ip": clean_ip or None,
            "user_id": user_id,
            "timestamp": now,
            "attributed": bool(link),
            "attribution_method": attribution_method,
            "is_unique": is_unique,
            "is_reinstall": is_reinstall,
            "duplicate_reason": duplicate_reason,
            "reinstall_of": matched_previous_id,
        }
        db.marketing_installs.insert_one(install_doc)

        curr_total = 0
        curr_android = 0
        curr_ios = 0
        if link:
            curr_total = int(link.get("total_downloads") or 0)
            curr_android = int(link.get("android_downloads") or 0)
            curr_ios = int(link.get("ios_downloads") or 0)
            curr_unique = int(link.get("unique_installs") or 0)
            raw_devices = link.get("unique_devices")
            unique_devices = raw_devices if isinstance(raw_devices, list) else []
            raw_fps = link.get("unique_fingerprints")
            unique_fps = raw_fps if isinstance(raw_fps, list) else []

            if is_unique:
                new_total = curr_total + 1
                new_android = curr_android + (1 if norm_platform == "android" else 0)
                new_ios = curr_ios + (1 if norm_platform == "ios" else 0)
                new_unique = curr_unique + 1
            else:
                # Reinstall: Do NOT increment download counters
                new_total = curr_total
                new_android = curr_android
                new_ios = curr_ios
                new_unique = curr_unique

            update_set = {
                "total_downloads": new_total,
                "android_downloads": new_android,
                "ios_downloads": new_ios,
                "unique_installs": new_unique,
                "last_downloaded_at": now if is_unique else link.get("last_downloaded_at", now),
                "last_reinstall_at": now if is_reinstall else link.get("last_reinstall_at"),
                "updated_at": now
            }
            store_key = clean_device or clean_fp or dev_key
            push_ops: Dict[str, Any] = {}
            if is_unique:
                if not isinstance(raw_devices, list):
                    update_set["unique_devices"] = [store_key] if store_key else []
                elif store_key and store_key not in unique_devices:
                    push_ops["unique_devices"] = {"$each": [store_key], "$slice": -5000}

                if not isinstance(raw_fps, list):
                    update_set["unique_fingerprints"] = [clean_fp] if clean_fp else []
                elif clean_fp and clean_fp not in unique_fps:
                    push_ops["unique_fingerprints"] = {"$each": [clean_fp], "$slice": -5000}

            update_ops: Dict[str, Any] = {"$set": update_set}
            if push_ops:
                update_ops["$push"] = push_ops

            db.marketing_links.update_one({"_id": link["_id"]}, update_ops)

        # 5. Dual-write to central app_downloads collection ONLY if unique
        if is_unique:
            try:
                db["app_downloads"].insert_one({
                    "application_id": link_id_str or "marketing_attribution",
                    "app_code": resolved_product if resolved_product != "unknown" else "aisa",
                    "platform": norm_platform,
                    "version": version or "1.0.0",
                    "ip_country": "IN",
                    "ip": clean_ip or None,
                    "fingerprint": clean_fp or None,
                    "attribution_method": attribution_method,
                    "user_id": user_id,
                    "created_at": now,
                })
            except Exception as e:
                print(f"[MarketingService] app_downloads log notice: {e}")

        return {
            "success": True,
            "slug": target_slug or "unknown",
            "attributed": bool(link),
            "attribution_method": attribution_method,
            "product_id": resolved_product,
            "platform": norm_platform,
            "fingerprint": clean_fp or None,
            "is_unique": is_unique,
            "is_reinstall": is_reinstall,
            "total_downloads": new_total if link else (1 if is_unique else 0),
            "android_downloads": new_android if link else (1 if is_unique and norm_platform == "android" else 0),
            "ios_downloads": new_ios if link else (1 if is_unique and norm_platform == "ios" else 0),
        }

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        """Returns overall marketing KPI cards, top performing posts, and platform distribution."""
        db = _get_db()

        unique_filter = {"is_reinstall": {"$ne": True}}
        total_links = db.marketing_links.count_documents({})
        total_clicks = db.marketing_clicks.count_documents({})
        total_downloads = db.marketing_installs.count_documents(unique_filter)
        total_android_downloads = db.marketing_installs.count_documents({
            **unique_filter,
            "platform": {"$in": ["android", "Android"]}
        })
        total_ios_downloads = db.marketing_installs.count_documents({
            **unique_filter,
            "platform": {"$in": ["ios", "iOS", "Ios"]}
        })

        # Unique reach across all clicks
        unique_reach = len(db.marketing_clicks.distinct("ip_hash"))
        overall_conversion_rate = round((total_downloads / total_clicks * 100), 1) if total_clicks > 0 else 0.0

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
            "total_downloads": total_downloads,
            "android_downloads": total_android_downloads,
            "ios_downloads": total_ios_downloads,
            "downloads_by_platform": {
                "android": total_android_downloads,
                "ios": total_ios_downloads,
            },
            "overall_conversion_rate": overall_conversion_rate,
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

        installs = list(db.marketing_installs.find({"slug": link["slug"]}).sort("timestamp", -1).limit(50))
        for inst in installs:
            inst["id"] = str(inst["_id"])
            inst["_id"] = str(inst["_id"])
            inst["platform"] = (inst.get("platform") or "android").lower()
            inst["attribution_method"] = inst.get("attribution_method") or "direct"
            inst["is_unique"] = inst.get("is_unique", True)
            inst["is_reinstall"] = inst.get("is_reinstall", False)

        link["total_downloads"] = int(link.get("total_downloads") or 0)
        link["android_downloads"] = int(link.get("android_downloads") or 0)
        link["ios_downloads"] = int(link.get("ios_downloads") or 0)
        link["unique_installs"] = int(link.get("unique_installs") or 0)
        total_c = link.get("total_clicks", 0)
        link["conversion_rate"] = round((link["total_downloads"] / total_c * 100), 1) if total_c > 0 else 0.0

        return {"link": link, "recent_clicks": clicks, "recent_installs": installs}

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

    @staticmethod
    def migrate_legacy_links() -> None:
        """Ensure all marketing links have proper non-null numeric counters and arrays."""
        try:
            db = _get_db()
            links = list(db.marketing_links.find({}))
            for l in links:
                updates = {}
                if l.get("total_downloads") is None:
                    updates["total_downloads"] = 0
                if l.get("android_downloads") is None:
                    updates["android_downloads"] = 0
                if l.get("ios_downloads") is None:
                    updates["ios_downloads"] = 0
                if l.get("unique_installs") is None:
                    updates["unique_installs"] = 0
                if l.get("unique_devices") is None or not isinstance(l.get("unique_devices"), list):
                    updates["unique_devices"] = []
                if l.get("total_clicks") is None:
                    updates["total_clicks"] = 0
                if l.get("unique_clicks") is None:
                    updates["unique_clicks"] = 0
                if l.get("unique_ips") is None or not isinstance(l.get("unique_ips"), list):
                    updates["unique_ips"] = []
                if updates:
                    db.marketing_links.update_one({"_id": l["_id"]}, {"$set": updates})
        except Exception as e:
            print(f"[MarketingService] Migration notice: {e}")

    @staticmethod
    def reconcile_duplicate_installs() -> Dict[str, Any]:
        """Scans marketing_installs and marketing_links to deduplicate any reinstall records and reconcile counters."""
        db = _get_db()
        reconciled_links = 0
        marked_duplicates = 0

        try:
            links = list(db.marketing_links.find({}))
            for link in links:
                slug = link.get("slug")
                link_id = str(link["_id"])

                installs = list(db.marketing_installs.find({
                    "$or": [{"link_id": link_id}, {"slug": slug}]
                }).sort("timestamp", 1))

                seen_devices = set()
                seen_ips = set()
                seen_fps = set()
                unique_android = 0
                unique_ios = 0
                link_unique_devices = []

                for inst in installs:
                    dev = (inst.get("device_id") or "").strip()
                    ip = (inst.get("ip") or "").strip()
                    fp = (inst.get("fingerprint") or "").strip()
                    platform = (inst.get("platform") or "android").lower()

                    is_dup = False
                    dup_reason = None

                    if dev and dev in seen_devices:
                        is_dup = True
                        dup_reason = "reconcile_device_id"
                    elif fp and fp in seen_fps:
                        is_dup = True
                        dup_reason = "reconcile_fingerprint"
                    elif ip and ip not in ["127.0.0.1", "localhost"] and (ip, platform) in seen_ips:
                        is_dup = True
                        dup_reason = "reconcile_ip_platform"

                    if is_dup:
                        marked_duplicates += 1
                        db.marketing_installs.update_one(
                            {"_id": inst["_id"]},
                            {"$set": {"is_unique": False, "is_reinstall": True, "duplicate_reason": dup_reason}}
                        )
                    else:
                        db.marketing_installs.update_one(
                            {"_id": inst["_id"]},
                            {"$set": {"is_unique": True, "is_reinstall": False}}
                        )
                        if dev:
                            seen_devices.add(dev)
                            link_unique_devices.append(dev)
                        if fp:
                            seen_fps.add(fp)
                        if ip:
                            seen_ips.add((ip, platform))
                        if "ios" in platform:
                            unique_ios += 1
                        else:
                            unique_android += 1

                total_u = unique_android + unique_ios
                db.marketing_links.update_one(
                    {"_id": link["_id"]},
                    {"$set": {
                        "total_downloads": total_u,
                        "android_downloads": unique_android,
                        "ios_downloads": unique_ios,
                        "unique_installs": total_u,
                        "unique_devices": link_unique_devices[:5000],
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
                reconciled_links += 1

        except Exception as e:
            print(f"[MarketingService] reconcile_duplicate_installs notice: {e}")

        return {"reconciled_links": reconciled_links, "marked_duplicates": marked_duplicates}

