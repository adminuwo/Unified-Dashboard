import logging
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from src.database.connection import get_db_instance
from src.unified_analytics import (
    ga4_service,
    playstore_service,
    appstore_service,
    gcp_monitoring_service,
    aggregator_service
)

logger = logging.getLogger("unified_analytics_scheduler")
scheduler: BackgroundScheduler | None = None


def job_sync_gcp_monitoring():
    """GCP Monitoring Cron Job: Runs every 5 minutes."""
    try:
        db = get_db_instance()
        logger.info("[Scheduler] Executing GCP Cloud Monitoring sync (5 min interval)...")
        gcp_monitoring_service.get_gcp_backend_monitoring(db, hours=24)
    except Exception as e:
        logger.error(f"[Scheduler] Error during GCP sync: {e}")


def job_sync_ga4_web_analytics():
    """GA4 Web Analytics Cron Job: Runs Hourly."""
    try:
        db = get_db_instance()
        logger.info("[Scheduler] Executing GA4 Web Analytics sync (Hourly)...")
        aggregator_service.get_web_analytics(db, app_code="all", days=30, force_refresh=True)
    except Exception as e:
        logger.error(f"[Scheduler] Error during GA4 sync: {e}")


def job_sync_playstore_analytics():
    """Google Play Store Reporting Cron Job: Runs every 6 hours."""
    try:
        db = get_db_instance()
        logger.info("[Scheduler] Executing Google Play Store sync (6 hours)...")
        playstore_service.sync_playstore_data(db)
        # Clear analytics cache to show fresh data immediately
        db["analytics_cache"].delete_many({})
    except Exception as e:
        logger.error(f"[Scheduler] Error during Play Store sync: {e}")


def job_sync_appstore_analytics():
    """Apple App Store Connect Reporting Cron Job: Runs every 12 hours."""
    try:
        db = get_db_instance()
        logger.info("[Scheduler] Executing App Store Connect sync (12 hours)...")
        appstore_service.sync_appstore_data(db)
        # Clear analytics cache to show fresh data immediately
        db["analytics_cache"].delete_many({})
    except Exception as e:
        logger.error(f"[Scheduler] Error during App Store sync: {e}")


def start_unified_analytics_scheduler():
    """Initialize and start the background scheduler with Phase 3 cron jobs."""
    global scheduler
    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler(daemon=True)

    # 1. GCP Monitoring: Every 5 minutes
    scheduler.add_job(
        job_sync_gcp_monitoring,
        trigger=IntervalTrigger(minutes=5),
        id="sync_gcp_monitoring_job",
        replace_existing=True
    )

    # 2. GA4: Hourly
    scheduler.add_job(
        job_sync_ga4_web_analytics,
        trigger=IntervalTrigger(hours=1),
        id="sync_ga4_web_analytics_job",
        replace_existing=True
    )

    # 3. Google Play API: Every 6 hours
    scheduler.add_job(
        job_sync_playstore_analytics,
        trigger=IntervalTrigger(hours=6),
        id="sync_playstore_analytics_job",
        replace_existing=True
    )

    # 4. Apple App Store: Every 12 hours
    scheduler.add_job(
        job_sync_appstore_analytics,
        trigger=IntervalTrigger(hours=12),
        id="sync_appstore_analytics_job",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Unified Analytics multi-cron scheduler started successfully.")


def shutdown_unified_analytics_scheduler():
    """Gracefully shutdown background scheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Unified Analytics scheduler shut down.")
