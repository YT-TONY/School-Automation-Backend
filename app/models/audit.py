# app/models/audit.py

import uuid
from sqlalchemy import String, ForeignKey, DateTime, Integer, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.result import ResultStatus

class ResultStatusAudit(Base):
    __tablename__ = "result_status_audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    class_arm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    target_status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus, name="resultstatus"), nullable=False)
    records_affected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)