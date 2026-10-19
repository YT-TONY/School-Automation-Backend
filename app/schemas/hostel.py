# app/schemas/hostel.py

import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.models.hostel import GenderRestriction, ReservationStatus

class HostelRoomCreate(BaseModel):
    room_number: str
    capacity: int = 4
    termly_fee: float

class HostelCreate(BaseModel):
    name: str
    gender: GenderRestriction = GenderRestriction.MIXED
    description: Optional[str] = None
    rooms: List[HostelRoomCreate] = []

class HostelRoomResponse(BaseModel):
    id: uuid.UUID
    room_number: str
    capacity: int
    termly_fee: float
    occupied_count: int = 0
    available_beds: int = 0

    class Config:
        from_attributes = True

class HostelResponse(BaseModel):
    id: uuid.UUID
    name: str
    gender: GenderRestriction
    description: Optional[str] = None
    rooms: List[HostelRoomResponse] = []

    class Config:
        from_attributes = True

class BedReservationRequest(BaseModel):
    student_id: uuid.UUID
    room_id: uuid.UUID
    session: str
    term: str

class BedReservationResponse(BaseModel):
    allocation_id: uuid.UUID
    student_id: uuid.UUID
    room_number: str
    hostel_name: str
    status: ReservationStatus
    termly_fee: float
    message: str