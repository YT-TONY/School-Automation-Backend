# app/models/student.py

from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.academic import ClassArm
    from app.models.result import Result

class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    GRADUATED = "GRADUATED"
    WITHDRAWN = "WITHDRAWN"

class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_arm_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("class_arms.id", ondelete="SET NULL"), nullable=True)

    admission_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parent_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    parent_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[StudentStatus] = mapped_column(Enum(StudentStatus, name="student_status_enum"), default=StudentStatus.ACTIVE, nullable=False)

    # Relationships
    class_arm: Mapped[Optional[ClassArm]] = relationship("ClassArm", back_populates="students")
    results: Mapped[List[Result]] = relationship("Result", back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    __table_args__ = (
        Index("idx_student_school_admission", "school_id", "admission_number", unique=True),
    )