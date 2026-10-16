#app/models/academic.py

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, List
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student

class ClassArm(Base):
    __tablename__ = "class_arms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "JSS 1A", "SS 3B"

    # Relationships
    students: Mapped[List[Student]] = relationship("Student", back_populates="class_arm")

    __table_args__ = (
        Index("idx_class_arm_school_name", "school_id", "name", unique=True),
    )

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Mathematics"
    code: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g., "MTH101"

    __table_args__ = (
        Index("idx_subject_school_code", "school_id", "code", unique=True),
    )