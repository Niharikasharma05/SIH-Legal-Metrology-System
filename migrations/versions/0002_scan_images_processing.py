"""add scan image processing fields

Revision ID: 0002_scan_images_processing
Revises: 0001_initial_infrastructure
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_scan_images_processing"
down_revision = "0001_initial_infrastructure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scan_images",
        sa.Column(
            "declarations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "scan_images",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "scan_images",
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "scan_images",
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("scan_images", "error_message")
    op.drop_column("scan_images", "processed_at")
    op.drop_column("scan_images", "started_at")
    op.drop_column("scan_images", "declarations")