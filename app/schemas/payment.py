# app/schemas/payment.py

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from app.models.payment import PaymentStatus, PaymentType

class PaymentInitializeRequest(BaseModel):
    student_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    payment_type: PaymentType
    amount: float = Field(..., gt=0, description="Base amount in Naira (excluding platform markup)")
    payer_email: EmailStr
    quantity: int = Field(default=1, ge=1, description="Used for online scratch PIN quantity")

class PaymentInitializeResponse(BaseModel):
    authorization_url: str
    access_code: str
    reference: str
    total_charged: float
    platform_markup: float

class PaymentReceiptResponse(BaseModel):
    id: uuid.UUID
    receipt_number: str
    payer_name: str
    payer_email: str
    amount_paid: float
    items_summary: Dict[str, Any]
    issued_at: datetime

    class Config:
        from_attributes = True

class TransactionStatusResponse(BaseModel):
    reference: str
    status: PaymentStatus
    amount_total: float
    payment_type: PaymentType
    receipt: Optional[PaymentReceiptResponse] = None

    class Config:
        from_attributes = True