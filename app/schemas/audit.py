# app/schemas/audit.py

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.result import ResultStatus

class ResultStatusAuditResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    user_id: uuid.UUID
    session: str
    term: str
    class_arm_id: Optional[uuid.UUID] = None
    student_id: Optional[uuid.UUID] = None
    previous_status: str
    target_status: ResultStatus
    records_affected: int
    created_at: datetime

    class Config:
        from_attributes = True