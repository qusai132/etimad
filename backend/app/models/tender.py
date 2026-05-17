from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Float, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core identification
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    activity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tender_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tender_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Dates
    publish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_enquiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_offer_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    award_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Financial
    document_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    document_price_currency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Details
    tender_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # URLs and raw data
    details_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI matching
    is_relevant: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notification
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Tender id={self.id} ref={self.reference_number!r}>"


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    tenders_found: Mapped[int] = mapped_column(Integer, default=0)
    tenders_new: Mapped[int] = mapped_column(Integer, default=0)
    pages_scraped: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
