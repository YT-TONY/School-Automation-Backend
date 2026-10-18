# app/models/result.py

from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Float, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.academic import Subject

class ResultStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED_BY_TEACHER = "SUBMITTED_BY_TEACHER"
    COMPILED_BY_CLASS_TEACHER = "COMPILED_BY_CLASS_TEACHER"
    APPROVED_BY_VP = "APPROVED_BY_VP"
    PUBLISHED = "PUBLISHED"

class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)

    # Granular Continuous Assessment Breakdown
    test1_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    test2_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    assignment_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    ca_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)     # Cumulative CA
    exam_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)   # Exam Score
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Final Total Score

    grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    grade_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    teacher_remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus, name="result_status_enum"), default=ResultStatus.DRAFT, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped[Student] = relationship("Student", back_populates="results")
    subject: Mapped[Subject] = relationship("Subject")

    __table_args__ = (
        Index("idx_result_unique_entry", "school_id", "student_id", "subject_id", "session", "term", unique=True),
    )