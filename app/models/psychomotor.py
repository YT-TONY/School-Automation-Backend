# app/models/psychomotor.py

import uuid
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class AffectivePsychomotorDomain(Base):
    __tablename__ = "affective_psychomotor_domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)

    # Affective Domain Ratings (1 to 5)
    punctuality: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    neatness: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    leadership: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    honesty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    politeness: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Psychomotor Domain Ratings (1 to 5)
    handwriting: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    sports_and_games: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    craft_and_art: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_affective_unique", "school_id", "student_id", "session", "term", unique=True),
    )