# app/models/grading.py

import uuid
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class GradingScale(Base):
    __tablename__ = "grading_scales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    
    grade_letter: Mapped[str] = mapped_column(String(10), nullable=False)   # e.g., "A1", "A", "DISTINCTION"
    min_score: Mapped[float] = mapped_column(Float, nullable=False)         # e.g., 75.0
    max_score: Mapped[float] = mapped_column(Float, nullable=False)         # e.g., 100.0
    remark: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g., "Excellent"

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_grading_scale_school_min", "school_id", "min_score"),
    )