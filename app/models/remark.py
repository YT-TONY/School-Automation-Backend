# app/models/remark.py

import uuid
from sqlalchemy import String, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TerminalRemark(Base):
    __tablename__ = "terminal_remarks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)

    form_teacher_remark: Mapped[str] = mapped_column(String(500), nullable=True)
    principal_remark: Mapped[str] = mapped_column(String(500), nullable=True)

    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_terminal_remark_unique", "school_id", "student_id", "session", "term", unique=True),
    )