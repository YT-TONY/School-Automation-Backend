#app/api/v1/endpoints/pins.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import secrets
import string
import uuid

from app.core.database import get_db
from app.core.tenant import get_current_tenant
from app.models.pin import ResultPin

router = APIRouter()

class PinGenerateRequest(BaseModel):
    quantity: int = 50
    usage_limit: int = 5

class PinGenerateResponse(BaseModel):
    generated_count: int
    message: str

@router.post("/generate", response_model=PinGenerateResponse)
async def generate_pins(
    payload: PinGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing.")

    characters = string.ascii_uppercase + string.digits
    new_pins = []

    for _ in range(payload.quantity):
        serial_no = f"SN-{''.join(secrets.choice(string.digits) for _ in range(8))}"
        raw_pin = ''.join(secrets.choice(characters) for _ in range(12))
        
        pin_obj = ResultPin(
            school_id=tenant_id,
            serial_number=serial_no,
            pin_code=raw_pin,
            max_uses=payload.usage_limit,
            use_count=0
        )
        new_pins.append(pin_obj)

    db.add_all(new_pins)
    await db.commit()

    return {
        "generated_count": len(new_pins),
        "message": f"Successfully generated {len(new_pins)} scratch cards."
    }