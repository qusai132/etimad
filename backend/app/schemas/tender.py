from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TenderBase(BaseModel):
    reference_number: str
    title: str
    entity: Optional[str] = None
    activity: Optional[str] = None
    tender_type: Optional[str] = None
    tender_number: Optional[str] = None
    publish_date: Optional[datetime] = None
    last_enquiry_date: Optional[datetime] = None
    last_offer_date: Optional[datetime] = None
    award_date: Optional[datetime] = None
    document_price: Optional[float] = None
    document_price_currency: Optional[str] = None
    tender_details: Optional[str] = None
    purpose: Optional[str] = None
    conditions: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[str] = None
    details_url: Optional[str] = None


class TenderCreate(TenderBase):
    raw_html: Optional[str] = None
    scraped_at: Optional[datetime] = None


class TenderRead(TenderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_relevant: Optional[bool] = None
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None
    matched_at: Optional[datetime] = None
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None


class TenderList(BaseModel):
    items: List[TenderRead]
    total: int
    page: int
    page_size: int
    pages: int


class ScrapeJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    tenders_found: int
    tenders_new: int
    pages_scraped: int
    error_message: Optional[str] = None
    created_at: datetime


class TenderFilter(BaseModel):
    search: Optional[str] = None
    is_relevant: Optional[bool] = None
    notification_sent: Optional[bool] = None
    entity: Optional[str] = None
    activity: Optional[str] = None
    page: int = 1
    page_size: int = 20
