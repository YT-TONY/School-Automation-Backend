# app/models/school.py

from __future__ import annotations
import uuid
import enum
from typing import TYPE_CHECKING, Optional, Dict, Any, List
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class SchoolType(str, enum.Enum):
    DAY = "DAY"
    BOARDING = "BOARDING"
    MIXED = "MIXED"

class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    subdomain: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)

    # School Classification Type
    school_type: Mapped[SchoolType] = mapped_column(
        Enum(SchoolType, name="school_type_enum"), default=SchoolType.MIXED, nullable=False
    )

    # Tier Control (1 = Starter, 2 = Complete OS)
    tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Dynamic HIG Branding Configuration
    branding: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "primary_color": "#1E3A8A",
            "secondary_color": "#F59E0B",
            "background_color": "#F8FAFC",
            "logo_url": None,
            "favicon_url": None,
            "motto": None,
            "report_card_template": "standard_v1"
        }
    )

    # School Rule Configurations
    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "enable_whatsapp_bot": False,
            "allow_parent_pin_purchase": True,
            "pass_mark_threshold": 50,
            "minimum_payment_percentage": 50,
            "current_session": "2025/2026",
            "current_term": "First Term"
        }
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    users: Mapped[List[User]] = relationship("User", back_populates="school", cascade="all, delete-orphan")