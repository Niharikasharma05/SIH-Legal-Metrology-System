"""initial infrastructure schema

Revision ID: 0001_initial_infrastructure
Revises:
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_infrastructure"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("input_type", sa.String(length=16), nullable=False, server_default="image"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("product_name", sa.String(length=255)),
        sa.Column("category", sa.String(length=100)),
        sa.Column("raw_text", sa.Text()),
        sa.Column("mrp", sa.String(length=255)),
        sa.Column("net_quantity", sa.String(length=255)),
        sa.Column("date_of_mfg", sa.String(length=255)),
        sa.Column("manufacturer_address", sa.Text()),
        sa.Column("consumer_care", sa.String(length=255)),
        sa.Column("font_ok", sa.Boolean()),
        sa.Column("required_mm", sa.Numeric()),
        sa.Column("placement_ok", sa.Boolean()),
        sa.Column("issues", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("input_type IN ('image', 'listing')", name="scan_input_type"),
        sa.CheckConstraint("status IN ('pending', 'processing', 'failed', 'COMPLIANT', 'WARNING', 'VIOLATION')", name="scan_status"),
    )
    op.create_table(
        "scan_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False, unique=True),
        sa.Column("label", sa.String(length=16), nullable=False, server_default="other"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_text", sa.Text()),
        sa.Column("font_ok", sa.Boolean()),
        sa.Column("required_mm", sa.Numeric()),
        sa.Column("placement_ok", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("label IN ('front', 'back', 'side', 'other')", name="scan_image_label"),
        sa.CheckConstraint("status IN ('pending', 'processing', 'failed', 'done')", name="scan_image_status"),
    )
    op.create_index("ix_scan_images_scan_id", "scan_images", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_scan_images_scan_id", table_name="scan_images")
    op.drop_table("scan_images")
    op.drop_table("scans")
