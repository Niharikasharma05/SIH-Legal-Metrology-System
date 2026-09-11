"""add users and scan ownership

Revision ID: 0002_users_and_scan_ownership
Revises: 0001_initial_infrastructure
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_users_and_scan_ownership"
down_revision = "0001_initial_infrastructure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="officer"),
        sa.CheckConstraint("role IN ('officer', 'admin')", name="user_role"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.add_column("scans", sa.Column("scanned_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_scans_scanned_by_id_users", "scans", "users", ["scanned_by_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_scans_scanned_by_id", "scans", ["scanned_by_id"])


def downgrade() -> None:
    op.drop_index("ix_scans_scanned_by_id", table_name="scans")
    op.drop_constraint("fk_scans_scanned_by_id_users", "scans", type_="foreignkey")
    op.drop_column("scans", "scanned_by_id")
    op.drop_table("users")
