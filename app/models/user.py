# app/models/user.py

from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import School

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    PRINCIPAL = "PRINCIPAL"
    VICE_PRINCIPAL_ACADEMIC = "VICE_PRINCIPAL_ACADEMIC"
    VICE_PRINCIPAL_ADMIN = "VICE_PRINCIPAL_ADMIN"
    EXAM_OFFICER = "EXAM_OFFICER"
    TEACHER = "TEACHER"
    FORM_TEACHER = "FORM_TEACHER"
    BURSAR = "BURSAR"
    STUDENT = "STUDENT"
    PARENT = "PARENT"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.TEACHER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Dynamic Admin Toggleable Permission Flags
    is_exam_officer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_class_teacher: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_enroll_students: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_manage_fees: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_approve_results: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    school: Mapped[Optional["School"]] = relationship("School", back_populates="users")

    __table_args__ = (
        Index("idx_user_school_email", "school_id", "email", unique=True),
    )