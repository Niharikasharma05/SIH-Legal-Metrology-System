"""add misleading-declaration fields to scans

Revision ID: 0003_misleading_declaration_fields
Revises: 09a7b14a5415
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_misleading_fields"
down_revision = "09a7b14a5415"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scans",
        sa.Column("unit_price", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "scans",
        sa.Column("discount_claim", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "scans",
        sa.Column("free_qty_claim", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scans", "free_qty_claim")
    op.drop_column("scans", "discount_claim")
    op.drop_column("scans", "unit_price")
