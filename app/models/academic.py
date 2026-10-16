from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.result import Result

class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    GRADUATED = "GRADUATED"
    WITHDRAWN = "WITHDRAWN"

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
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Mathematics"[cite: 1]
    code: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g., "MTH101"[cite: 1]

    __table_args__ = (
        Index("idx_subject_school_code", "school_id", "code", unique=True),
    )

class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_arm_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("class_arms.id", ondelete="SET NULL"), nullable=True)

    admission_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. STU20260045[cite: 1]
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    parent_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    parent_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[StudentStatus] = mapped_column(Enum(StudentStatus, name="student_status_enum"), default=StudentStatus.ACTIVE, nullable=False)

    # Relationships
    class_arm: Mapped[Optional[ClassArm]] = relationship("ClassArm", back_populates="students")
    results: Mapped[List[Result]] = relationship("Result", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_student_school_admission", "school_id", "admission_number", unique=True),
    )