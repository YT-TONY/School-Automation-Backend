#app/schemas/pin.py

import uuid
from pydantic import BaseModel

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