from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.tender import Tender, ScrapeJob
from app.schemas.tender import TenderCreate, TenderFilter

logger = get_logger(__name__)


async def upsert_tender(db: AsyncSession, tender_data: TenderCreate) -> tuple[Tender, bool]:
    result = await db.execute(
        select(Tender).where(Tender.reference_number == tender_data.reference_number)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for field, value in tender_data.model_dump(exclude_none=True).items():
            if field not in ("is_relevant", "relevance_score", "notification_sent"):
                setattr(existing, field, value)
        existing.updated_at = datetime.now(timezone.utc)
        return existing, False
    else:
        tender = Tender(**tender_data.model_dump())
        db.add(tender)
        return tender, True


async def get_tenders(db: AsyncSession, filters: TenderFilter) -> tuple[List[Tender], int]:
    query = select(Tender)

    if filters.search:
        term = f"%{filters.search}%"
        query = query.where(
            or_(
                Tender.title.ilike(term),
                Tender.entity.ilike(term),
                Tender.reference_number.ilike(term),
                Tender.activity.ilike(term),
            )
        )
    if filters.is_relevant is not None:
        query = query.where(Tender.is_relevant == filters.is_relevant)
    if filters.notification_sent is not None:
        query = query.where(Tender.notification_sent == filters.notification_sent)
    if filters.entity:
        query = query.where(Tender.entity.ilike(f"%{filters.entity}%"))
    if filters.activity:
        query = query.where(Tender.activity.ilike(f"%{filters.activity}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = (
        query.order_by(Tender.created_at.desc())
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_tender_by_id(db: AsyncSession, tender_id: int) -> Optional[Tender]:
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    return result.scalar_one_or_none()


async def get_unmatched_tenders(db: AsyncSession) -> List[Tender]:
    result = await db.execute(
        select(Tender).where(Tender.is_relevant.is_(None))
    )
    return result.scalars().all()


async def get_relevant_unnotified(db: AsyncSession) -> List[Tender]:
    result = await db.execute(
        select(Tender).where(
            Tender.is_relevant == True,
            Tender.notification_sent == False,
        )
    )
    return result.scalars().all()


async def mark_notification_sent(db: AsyncSession, tender_id: int) -> None:
    await db.execute(
        update(Tender)
        .where(Tender.id == tender_id)
        .values(notification_sent=True, notification_sent_at=datetime.now(timezone.utc))
    )


async def create_scrape_job(db: AsyncSession) -> ScrapeJob:
    job = ScrapeJob(status="running", started_at=datetime.now(timezone.utc))
    db.add(job)
    await db.flush()
    return job


async def finish_scrape_job(
    db: AsyncSession,
    job: ScrapeJob,
    status: str,
    tenders_found: int = 0,
    tenders_new: int = 0,
    pages_scraped: int = 0,
    error_message: Optional[str] = None,
) -> None:
    job.status = status
    job.finished_at = datetime.now(timezone.utc)
    job.tenders_found = tenders_found
    job.tenders_new = tenders_new
    job.pages_scraped = pages_scraped
    job.error_message = error_message


def get_unmatched_tenders_sync(db: Session) -> List[Tender]:
    return db.execute(
        select(Tender).where(Tender.is_relevant.is_(None))
    ).scalars().all()


def upsert_tender_sync(db: Session, tender_data: TenderCreate) -> tuple[Tender, bool]:
    existing = db.execute(
        select(Tender).where(Tender.reference_number == tender_data.reference_number)
    ).scalar_one_or_none()

    if existing:
        for field, value in tender_data.model_dump(exclude_none=True).items():
            if field not in ("is_relevant", "relevance_score", "notification_sent"):
                setattr(existing, field, value)
        existing.updated_at = datetime.now(timezone.utc)
        return existing, False
    else:
        tender = Tender(**tender_data.model_dump())
        db.add(tender)
        db.flush()
        return tender, True
