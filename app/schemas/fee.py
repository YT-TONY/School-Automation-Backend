# app/schemas/fee.py

import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.models.fee import FeeType

class FeeItemCreate(BaseModel):
    title: str
    amount: float
    fee_type: FeeType = FeeType.MANDATORY
    session: str
    term: str
    applicable_classes: Optional[List[str]] = None
    is_new_student_only: bool = False

class FeeItemResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    title: str
    amount: float
    fee_type: FeeType
    session: str
    term: str
    applicable_classes: Optional[List[str]] = None
    is_new_student_only: bool
    is_active: bool

    class Config:
        from_attributes = True

class PackageSelectionRequest(BaseModel):
    student_id: uuid.UUID
    selected_fee_item_ids: List[uuid.UUID]

class FeeItemDetail(BaseModel):
    fee_item_id: uuid.UUID
    title: str
    amount: float
    fee_type: FeeType
    is_selected: bool

class StudentInvoiceResponse(BaseModel):
    student_id: uuid.UUID
    student_name: str
    admission_number: str
    session: str
    term: str
    minimum_payment_percentage_required: int
    boarding_fee: float = 0.0
    mandatory_items: List[FeeItemDetail]
    optional_items: List[FeeItemDetail]
    new_student_packages: List[FeeItemDetail]
    total_amount_due: float