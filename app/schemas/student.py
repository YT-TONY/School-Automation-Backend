#app/schemas/student.py

import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.academic import StudentStatus

class StudentCreate(BaseModel):
    admission_number: str
    full_name: str
    class_arm_id: Optional[uuid.UUID] = None
    photo_url: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    admission_number: str
    full_name: str
    status: StudentStatus
    class_arm_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True