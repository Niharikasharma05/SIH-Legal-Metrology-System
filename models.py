"""Persistent scan records. Processing behavior is introduced in Phase 2."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Account used for JWT authentication and scan ownership."""

    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(16), nullable=False, default="officer", server_default="officer")

    scans: Mapped[list["Scan"]] = relationship(back_populates="scanned_by")


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint("input_type IN ('image', 'listing')", name="scan_input_type"),
        CheckConstraint("status IN ('pending', 'processing', 'failed', 'COMPLIANT', 'WARNING', 'VIOLATION')", name="scan_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scanned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    input_type: Mapped[str] = mapped_column(String(16), nullable=False, default="image")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_name: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))
    raw_text: Mapped[str | None] = mapped_column(Text)
    mrp: Mapped[str | None] = mapped_column(String(255))
    net_quantity: Mapped[str | None] = mapped_column(String(255))
    date_of_mfg: Mapped[str | None] = mapped_column(String(255))
    manufacturer_address: Mapped[str | None] = mapped_column(Text)
    consumer_care: Mapped[str | None] = mapped_column(String(255))
    font_ok: Mapped[bool | None]
    required_mm: Mapped[float | None]
    placement_ok: Mapped[bool | None]
    issues: Mapped[dict | list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    images: Mapped[list["ScanImage"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    scanned_by: Mapped[User | None] = relationship(back_populates="scans")


class ScanImage(Base):
    __tablename__ = "scan_images"
    __table_args__ = (
        CheckConstraint("label IN ('front', 'back', 'side', 'other')", name="scan_image_label"),
        CheckConstraint("status IN ('pending', 'processing', 'failed', 'done')", name="scan_image_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(16), nullable=False, default="other")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_text: Mapped[str | None] = mapped_column(Text)
    font_ok: Mapped[bool | None]
    required_mm: Mapped[float | None]
    placement_ok: Mapped[bool | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    scan: Mapped[Scan] = relationship(back_populates="images")
