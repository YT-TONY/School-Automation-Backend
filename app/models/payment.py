# app/models/payment.py

import enum
import uuid
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, Enum, JSON, Integer, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"

class PaymentType(str, enum.Enum):
    SCHOOL_FEES = "SCHOOL_FEES"
    ONLINE_PIN = "ONLINE_PIN"
    HOSTEL_FEE = "HOSTEL_FEE"

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    paystack_access_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    amount_total: Mapped[float] = mapped_column(Float, nullable=False)    # Total charged in Naira
    amount_school: Mapped[float] = mapped_column(Float, nullable=False)   # Net payout to school
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False)    # Markup (500 or 1000)

    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType, name="paymenttype"), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="paymentstatus"), nullable=False, default=PaymentStatus.PENDING, index=True)
    
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    receipt: Mapped[Optional["PaymentReceipt"]] = relationship("PaymentReceipt", back_populates="transaction", uselist=False)

class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payment_transactions.id", ondelete="CASCADE"), nullable=False, unique=True)

    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    payer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)
    items_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Immutable snapshot of paid items
    
    issued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    transaction: Mapped["PaymentTransaction"] = relationship("PaymentTransaction", back_populates="receipt")