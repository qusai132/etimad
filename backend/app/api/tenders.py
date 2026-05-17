from typing import Optional
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas.tender import TenderRead, TenderList, TenderFilter
from app.services.tender_service import get_tenders, get_tender_by_id

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("", response_model=TenderList)
async def list_tenders(
    search: Optional[str] = Query(None, description="Search in title, entity, ref number"),
    is_relevant: Optional[bool] = Query(None),
    notification_sent: Optional[bool] = Query(None),
    entity: Optional[str] = Query(None),
    activity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    filters = TenderFilter(
        search=search,
        is_relevant=is_relevant,
        notification_sent=notification_sent,
        entity=entity,
        activity=activity,
        page=page,
        page_size=page_size,
    )
    tenders, total = await get_tenders(db, filters)
    pages = math.ceil(total / page_size) if total else 0
    return TenderList(
        items=tenders,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{tender_id}", response_model=TenderRead)
async def get_tender(tender_id: int, db: AsyncSession = Depends(get_async_db)):
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender
