# app/api/v1/endpoints/pins.py  (drop-in replacement)
#
# Changes from your version:
#   - /generate now sets serial_number and batch_number (both are NOT NULL) and returns batch_number.
#   - /buy-online is removed: it created inactive PINs without any payment, and returned a made-up
#     checkout link. PIN purchases now go only through POST /payments/initialize, and the webhook
#     creates the PINs after Paystack confirms the payment.

import secrets
import string
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import require_roles
from app.core.tenant import require_tenant_id
from app.models.pin import ResultPin
from app.models.user import User, UserRole
from app.schemas.pin import PinGenerateRequest, PinGenerateResponse, PinResponse

router = APIRouter()

ADMIN_OR_BURSAR = [UserRole.SCHOOL_ADMIN, UserRole.BURSAR, UserRole.SUPER_ADMIN]
MAX_PINS_PER_BATCH = 1000


def _generate_random_pin(length: int = 12) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_serial() -> str:
    return "SN-" + "".join(secrets.choice(string.digits) for _ in range(10))


# --- 1. Admin Bulk PIN Generation ---
@router.post("/generate", response_model=PinGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_result_pins(
    payload: PinGenerateRequest,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_BURSAR)),
    db: AsyncSession = Depends(get_db),
):
    if not 1 <= payload.quantity <= MAX_PINS_PER_BATCH:
        raise HTTPException(status_code=400, detail=f"Quantity must be between 1 and {MAX_PINS_PER_BATCH}.")
    if payload.max_uses < 1:
        raise HTTPException(status_code=400, detail="max_uses must be at least 1.")

    for _ in range(payload.quantity):
        db.add(ResultPin(
            school_id=tenant_id,
            pin_code=_generate_random_pin(12),
            serial_number=_generate_serial(),
            batch_number=payload.batch_number,
            max_uses=payload.max_uses,
            times_used=0,
            is_active=True,
        ))

    await db.commit()
    return PinGenerateResponse(
        generated_count=payload.quantity,
        batch_number=payload.batch_number,
        message=f"Successfully generated {payload.quantity} scratch PINs.",
    )


# --- 2. List School Scratch PINs ---
@router.get("/", response_model=List[PinResponse])
async def list_pins(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_BURSAR)),
    db: AsyncSession = Depends(get_db),
):
    query = select(ResultPin).where(ResultPin.school_id == tenant_id).offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()
