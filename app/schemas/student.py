# app/schemas/student.py

import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.student import StudentStatus

class StudentCreate(BaseModel):
    admission_number: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    class_arm_id: Optional[uuid.UUID] = None
    photo_url: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    admission_number: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    full_name: str
    status: StudentStatus
    class_arm_id: Optional[uuid.UUID] = None
    photo_url: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None

    class Config:
        from_attributes = True