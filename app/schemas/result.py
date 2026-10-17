# app/schemas/result.py

import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.models.result import ResultStatus

class ResultEntry(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    session: str
    term: str
    ca_score: float = 0.0
    exam_score: float = 0.0

class ResultStatusUpdate(BaseModel):
    session: str
    term: str
    target_status: ResultStatus
    class_arm_id: Optional[uuid.UUID] = None
    student_id: Optional[uuid.UUID] = None

class StatusUpdateResponse(BaseModel):
    updated_count: int
    new_status: ResultStatus
    message: str

class CheckResultRequest(BaseModel):
    admission_number: str
    pin_code: str
    session: str
    term: str

class ScoreDetail(BaseModel):
    subject_id: uuid.UUID
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    ca_score: float
    exam_score: float
    total_score: float
    grade: Optional[str] = None
    status: ResultStatus

class StudentResultSheet(BaseModel):
    student_id: uuid.UUID
    student_name: str
    admission_number: str
    session: str
    term: str
    pin_remaining_uses: Optional[int] = None
    results: List[ScoreDetail]