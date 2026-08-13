import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from src.config.settings import settings
from src.database.connection import get_client
from src.store_analytics import service

logger = logging.getLogger("store_analytics_scheduler")
scheduler = AsyncIOScheduler()


def scheduled_sync_job():
    """Background cron job executing periodic Google Play store analytics synchronization."""
    logger.info("[Store Analytics Scheduler] Running periodic sync job...")
    try:
        client = get_client()
        db = client[settings.MONGODB_DB_NAME]
        res = service.sync_google_play_data(db)
        logger.info(f"[Store Analytics Scheduler] Sync finished: {res.message}")
    except Exception as e:
        logger.error(f"[Store Analytics Scheduler] Periodic sync failed: {e}")


def start_store_analytics_scheduler():
    """Start background scheduler if not already running."""
    if not scheduler.running:
        interval_hours = getattr(settings, "PLAY_STORE_SYNC_INTERVAL_HOURS", 24)
        scheduler.add_job(
            scheduled_sync_job,
            "interval",
            hours=interval_hours,
            id="store_analytics_daily_sync",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"[Store Analytics Scheduler] Started scheduler (Interval: {interval_hours} hours).")


def shutdown_store_analytics_scheduler():
    """Shutdown background scheduler gracefully on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Store Analytics Scheduler] Shutdown complete.")
