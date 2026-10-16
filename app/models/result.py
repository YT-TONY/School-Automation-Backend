from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.academic import Student, Subject

class ResultStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"

class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    session: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2025/2026"[cite: 1]
    term: Mapped[str] = mapped_column(String(20), nullable=False)     # e.g., "First Term"[cite: 1]

    ca_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # Continuous Assessment[cite: 1]
    exam_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Exam Score[cite: 1]
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)# Calculated Total[cite: 1]

    grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)        # A, B, C, etc.[cite: 1]
    grade_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # 5.0, 4.0, etc.[cite: 1]
    teacher_remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus, name="result_status_enum"), default=ResultStatus.DRAFT, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    student: Mapped[Student] = relationship("Student", back_populates="results")
    subject: Mapped[Subject] = relationship("Subject")

    __table_args__ = (
        Index("idx_result_unique_entry", "school_id", "student_id", "subject_id", "session", "term", unique=True),
    )

class ResultPin(Base):
    __tablename__ = "result_pins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    pin_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True) # Unhashed or Hashed PIN[cite: 1]
    serial_number: Mapped[str] = mapped_column(String(50), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False)         # Batch tag[cite: 1]

    max_uses: Mapped[int] = mapped_column(Integer, default=5, nullable=False)       # Allowed checks count[cite: 1]
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_pin_school_code", "school_id", "pin_code", unique=True),
    )