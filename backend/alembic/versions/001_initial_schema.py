"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=True),
        sa.Column("activity", sa.Text(), nullable=True),
        sa.Column("tender_type", sa.String(200), nullable=True),
        sa.Column("tender_number", sa.String(100), nullable=True),
        sa.Column("publish_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_enquiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_offer_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("award_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_price", sa.Float(), nullable=True),
        sa.Column("document_price_currency", sa.String(20), nullable=True),
        sa.Column("tender_details", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Text(), nullable=True),
        sa.Column("details_url", sa.Text(), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("is_relevant", sa.Boolean(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("relevance_reason", sa.Text(), nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False, default=False),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_number", name="uq_tenders_reference_number"),
    )
    op.create_index("ix_tenders_id", "tenders", ["id"])
    op.create_index("ix_tenders_reference_number", "tenders", ["reference_number"])
    op.create_index("ix_tenders_is_relevant", "tenders", ["is_relevant"])
    op.create_index("ix_tenders_notification_sent", "tenders", ["notification_sent"])
    op.create_index("ix_tenders_publish_date", "tenders", ["publish_date"])

    op.create_table(
        "scrape_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenders_found", sa.Integer(), default=0, nullable=False),
        sa.Column("tenders_new", sa.Integer(), default=0, nullable=False),
        sa.Column("pages_scraped", sa.Integer(), default=0, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_jobs_id", "scrape_jobs", ["id"])


def downgrade() -> None:
    op.drop_table("scrape_jobs")
    op.drop_table("tenders")
