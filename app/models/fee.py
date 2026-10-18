# app/models/fee.py

import uuid
import enum
from typing import Optional, List
from sqlalchemy import String, Float, Boolean, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class FeeType(str, enum.Enum):
    MANDATORY = "MANDATORY"      # Tuition, Development Fee
    OPTIONAL = "OPTIONAL"        # Bus Transport, After-School Lessons, Boarding
    CONDITIONAL = "CONDITIONAL"  # WAEC/NECO (SS3), BECE (JSS3), Common Entrance (Primary 5)

class FeeItem(Base):
    __tablename__ = "fee_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType, name="fee_type_enum"), default=FeeType.MANDATORY, nullable=False)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)

    # List of class level names this fee targets e.g. ["SS3"] or ["JSS3", "SS3"]
    applicable_classes: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class StudentFeeSelection(Base):
    """Tracks optional/conditional package selections toggled by parents or school admins for a student."""
    __tablename__ = "student_fee_selections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_items.id", ondelete="CASCADE"), nullable=False)

    is_selected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_student_fee_selection_unique", "school_id", "student_id", "fee_item_id", unique=True),
    )