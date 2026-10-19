# app/schemas/result.py

import uuid
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.models.result import ResultStatus

class ResultEntry(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    session: str
    term: str
    test1_score: float = Field(default=0.0, ge=0.0, le=100.0)
    test2_score: float = Field(default=0.0, ge=0.0, le=100.0)
    assignment_score: float = Field(default=0.0, ge=0.0, le=100.0)
    ca_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    exam_score: float = Field(default=0.0, ge=0.0, le=100.0)

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
    test1_score: float = 0.0
    test2_score: float = 0.0
    assignment_score: float = 0.0
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
    class_position: Optional[str] = None
    term_average: Optional[float] = None
    strongest_subject: Optional[str] = None
    weakest_subject: Optional[str] = None
    results: List[ScoreDetail]

class BroadsheetRow(BaseModel):
    student_id: uuid.UUID
    student_name: str
    admission_number: str
    subject_scores: Dict[str, float]
    total_aggregate: float
    average_score: float
    position: int

class BroadsheetResponse(BaseModel):
    class_arm_id: uuid.UUID
    session: str
    term: str
    subjects: List[Dict[str, str]]
    rows: List[BroadsheetRow]