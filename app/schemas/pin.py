# app/schemas/pin.py

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr

class PinGenerateRequest(BaseModel):
    quantity: int = 50
    batch_number: str = "BATCH-01"
    max_uses: int = 5

class PinGenerateResponse(BaseModel):
    generated_count: int
    batch_number: str
    message: str

class PinResponse(BaseModel):
    id: uuid.UUID
    serial_number: str
    batch_number: str
    max_uses: int
    times_used: int
    is_active: bool

    class Config:
        from_attributes = True

class OnlinePinPurchaseRequest(BaseModel):
    quantity: int = 1
    payer_email: EmailStr
    payer_phone: Optional[str] = None

class OnlinePinPurchaseResponse(BaseModel):
    school_name: str
    quantity: int
    unit_price: float
    total_amount: float
    payer_email: str
    payment_reference: str
    checkout_url: str