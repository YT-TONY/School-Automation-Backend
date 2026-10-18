# app/api/v1/endpoints/pins.py

import secrets
import string
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import require_roles
from app.core.tenant import require_tenant_id, get_current_school
from app.models.pin import ResultPin
from app.models.school import School
from app.models.user import User, UserRole
from app.schemas.pin import (
    PinGenerateRequest,
    PinGenerateResponse,
    PinResponse,
    OnlinePinPurchaseRequest,
    OnlinePinPurchaseResponse
)

router = APIRouter()

ADMIN_OR_BURSAR = [UserRole.SCHOOL_ADMIN, UserRole.BURSAR, UserRole.SUPER_ADMIN]

def _generate_random_pin(length: int = 12) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# --- 1. Admin Bulk PIN Generation ---
@router.post("/generate", response_model=PinGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_result_pins(
    payload: PinGenerateRequest,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_BURSAR)),
    db: AsyncSession = Depends(get_db)
):
    created_pins = []
    for _ in range(payload.quantity):
        pin_code = _generate_random_pin(12)
        pin = ResultPin(
            school_id=tenant_id,
            pin_code=pin_code,
            max_uses=payload.max_uses,
            times_used=0,
            is_active=True
        )
        db.add(pin)
        created_pins.append(pin)

    await db.commit()
    return PinGenerateResponse(
        generated_count=len(created_pins),
        max_uses_per_pin=payload.max_uses,
        message=f"Successfully generated {len(created_pins)} scratch PINs."
    )

# --- 2. Public / Parent Online PIN Purchase ---
@router.post("/buy-online", response_model=OnlinePinPurchaseResponse)
async def buy_pin_online(
    payload: OnlinePinPurchaseRequest,
    school: School = Depends(get_current_school),
    db: AsyncSession = Depends(get_db)
):
    if not school.settings.get("allow_parent_pin_purchase", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Online PIN purchasing is currently disabled by this school."
        )

    pin_price = float(school.settings.get("pin_price_amount", 1500.0))
    total_amount = pin_price * payload.quantity

    for _ in range(payload.quantity):
        pin_code = _generate_random_pin(12)
        new_pin = ResultPin(
            school_id=school.id,
            pin_code=pin_code,
            max_uses=5,
            times_used=0,
            is_active=False
        )
        db.add(new_pin)

    await db.commit()

    return OnlinePinPurchaseResponse(
        school_name=school.name,
        quantity=payload.quantity,
        unit_price=pin_price,
        total_amount=total_amount,
        payer_email=payload.payer_email,
        payment_reference=f"PIN-{uuid.uuid4().hex[:10].upper()}",
        checkout_url=f"https://checkout.paystack.com/pay/{school.slug}-pin-purchase"
    )

# --- 3. List School Scratch PINs ---
@router.get("/", response_model=List[PinResponse])
async def list_pins(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_BURSAR)),
    db: AsyncSession = Depends(get_db)
):
    query = select(ResultPin).where(ResultPin.school_id == tenant_id).offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()