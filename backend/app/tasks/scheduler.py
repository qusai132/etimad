from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.logging import get_logger
from app.tasks.scrape_task import run_scrape_job, run_matching_job, run_notification_job

logger = get_logger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler():
    scheduler = get_scheduler()
    if scheduler.running:
        return

    scheduler.add_job(
        run_scrape_job,
        trigger=IntervalTrigger(minutes=settings.SCRAPER_INTERVAL_MINUTES),
        id="scrape_tenders",
        name="Scrape Etimad Tenders",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        run_matching_job,
        trigger=IntervalTrigger(minutes=max(settings.SCRAPER_INTERVAL_MINUTES // 2, 5)),
        id="match_tenders",
        name="Match Tenders with Company Profile",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        run_notification_job,
        trigger=IntervalTrigger(minutes=15),
        id="send_notifications",
        name="Send Email Notifications",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        scrape_interval_minutes=settings.SCRAPER_INTERVAL_MINUTES,
    )


def stop_scheduler():
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("scheduler_stopped")
