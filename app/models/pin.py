#app/models/pin.py

from __future__ import annotations
import uuid
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ResultPin(Base):
    __tablename__ = "result_pins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    pin_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(50), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False)

    max_uses: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_pin_school_code", "school_id", "pin_code", unique=True),
    )