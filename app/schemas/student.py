# app/schemas/student.py

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.student import StudentStatus

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    admission_number: Optional[str] = None  # Auto-generated if omitted: e.g. NNADI482019
    student_email: Optional[EmailStr] = None # Used to generate student User login
    class_arm_id: Optional[uuid.UUID] = None
    photo_url: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    class_arm_id: Optional[uuid.UUID] = None
    photo_url: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    status: Optional[StudentStatus] = None

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
    parent_email: Optional[str] = None
    generated_temp_password: Optional[str] = None  # Returned only on creation for admin distribution

    class Config:
        from_attributes = True