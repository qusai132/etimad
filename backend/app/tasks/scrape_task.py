import asyncio
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal, SyncSessionLocal
from app.services.scraper import EtimadScraper
from app.services.matcher import TenderMatcher
from app.services.email_service import send_tender_alert
from app.services.tender_service import (
    upsert_tender,
    create_scrape_job,
    finish_scrape_job,
    get_unmatched_tenders,
    mark_notification_sent,
    get_relevant_unnotified,
)
from app.schemas.tender import TenderCreate

logger = get_logger(__name__)


async def run_scrape_job() -> dict:
    logger.info("scrape_job_started")
    async with AsyncSessionLocal() as db:
        job = await create_scrape_job(db)
        await db.commit()
        job_id = job.id

    tenders_found = 0
    tenders_new = 0
    pages_scraped = 0
    error_msg = None

    try:
        scraper = EtimadScraper()
        tender_data_list: list[TenderCreate] = []

        async def collect(tender: TenderCreate):
            tender_data_list.append(tender)

        scraped = await scraper.scrape_all(on_tender_scraped=collect)
        tenders_found = len(scraped)

        async with AsyncSessionLocal() as db:
            for tender_data in scraped:
                try:
                    tender, is_new = await upsert_tender(db, tender_data)
                    if is_new:
                        tenders_new += 1
                except Exception as e:
                    logger.error("tender_upsert_failed", ref=tender_data.reference_number, error=str(e))
            await db.commit()

        async with AsyncSessionLocal() as db:
            job_result = await db.get(type(job).__class__, job_id)

        logger.info(
            "scrape_job_completed",
            found=tenders_found,
            new=tenders_new,
        )

    except Exception as e:
        error_msg = str(e)
        logger.error("scrape_job_failed", error=error_msg)

    async with AsyncSessionLocal() as db:
        from app.models.tender import ScrapeJob
        from sqlalchemy import select
        result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
        job_obj = result.scalar_one_or_none()
        if job_obj:
            await finish_scrape_job(
                db,
                job_obj,
                status="failed" if error_msg else "completed",
                tenders_found=tenders_found,
                tenders_new=tenders_new,
                pages_scraped=pages_scraped,
                error_message=error_msg,
            )
            await db.commit()

    return {
        "job_id": job_id,
        "tenders_found": tenders_found,
        "tenders_new": tenders_new,
        "error": error_msg,
    }


async def run_matching_job() -> dict:
    logger.info("matching_job_started")
    matcher = TenderMatcher()

    async with AsyncSessionLocal() as db:
        unmatched = await get_unmatched_tenders(db)

        if not unmatched:
            logger.info("no_unmatched_tenders")
            return {"matched": 0, "relevant": 0}

        updated = await matcher.run_matching(unmatched)
        await db.commit()

        relevant = [t for t in updated if t.is_relevant]
        logger.info("matching_done", total=len(updated), relevant=len(relevant))

    return {"matched": len(updated), "relevant": len(relevant)}


async def run_notification_job() -> dict:
    logger.info("notification_job_started")
    sent_count = 0

    async with AsyncSessionLocal() as db:
        tenders = await get_relevant_unnotified(db)

        for tender in tenders:
            try:
                success = await send_tender_alert(tender)
                if success:
                    await mark_notification_sent(db, tender.id)
                    sent_count += 1
            except Exception as e:
                logger.error("notification_failed", tender_id=tender.id, error=str(e))

        await db.commit()

    logger.info("notification_job_done", sent=sent_count)
    return {"notifications_sent": sent_count}


def run_scrape_sync():
    asyncio.run(run_scrape_job())


def run_matching_sync():
    asyncio.run(run_matching_job())


def run_notifications_sync():
    asyncio.run(run_notification_job())
