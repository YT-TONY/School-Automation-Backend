# app/schemas/academic.py

import uuid
from typing import Optional
from pydantic import BaseModel

class ClassArmCreate(BaseModel):
    name: str  # e.g., "JSS 1A", "SS 3B"
    form_teacher_id: Optional[uuid.UUID] = None

class ClassArmUpdate(BaseModel):
    name: Optional[str] = None
    form_teacher_id: Optional[uuid.UUID] = None

class ClassArmResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    form_teacher_id: Optional[uuid.UUID] = None
    form_teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class SubjectCreate(BaseModel):
    name: str  # e.g., "Mathematics"
    code: str  # e.g., "MTH101"

class SubjectResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    code: str

    class Config:
        from_attributes = True