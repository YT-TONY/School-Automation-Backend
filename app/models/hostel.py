# app/models/hostel.py

from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student

class GenderRestriction(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    MIXED = "MIXED"

class ReservationStatus(str, enum.Enum):
    RESERVED = "RESERVED"  # Pending fee payment
    CONFIRMED = "CONFIRMED"# Fully paid
    VACATED = "VACATED"

class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False) # e.g., "St. Augustine Hall"
    gender: Mapped[GenderRestriction] = mapped_column(Enum(GenderRestriction, name="gender_restriction_enum"), default=GenderRestriction.MIXED, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rooms: Mapped[List["HostelRoom"]] = relationship("HostelRoom", back_populates="hostel", cascade="all, delete-orphan")

class HostelRoom(Base):
    __tablename__ = "hostel_rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    hostel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True)

    room_number: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "Room 101"
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    termly_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="rooms")
    allocations: Mapped[List["BedAllocation"]] = relationship("BedAllocation", back_populates="room", cascade="all, delete-orphan")

class BedAllocation(Base):
    __tablename__ = "bed_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hostel_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    session: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus, name="reservation_status_enum"), default=ReservationStatus.RESERVED, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    room: Mapped["HostelRoom"] = relationship("HostelRoom", back_populates="allocations")
    student: Mapped["Student"] = relationship("Student")

    __table_args__ = (
        Index("idx_bed_allocation_unique", "school_id", "student_id", "session", "term", unique=True),
    )