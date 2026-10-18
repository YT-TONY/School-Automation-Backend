# app/schemas/user.py

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.TEACHER

class UserPermissionsUpdate(BaseModel):
    is_exam_officer: Optional[bool] = None
    is_class_teacher: Optional[bool] = None
    can_enroll_students: Optional[bool] = None
    can_manage_fees: Optional[bool] = None
    can_approve_results: Optional[bool] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    school_id: Optional[uuid.UUID] = None
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole
    is_active: bool
    is_exam_officer: bool
    is_class_teacher: bool
    can_enroll_students: bool
    can_manage_fees: bool
    can_approve_results: bool
    created_at: datetime

    class Config:
        from_attributes = True