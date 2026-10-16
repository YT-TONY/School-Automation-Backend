#app/schemas/result.py

import uuid
from pydantic import BaseModel
from typing import List, Optional

class ResultEntry(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    session: str
    term: str
    ca_score: float = 0.0
    exam_score: float = 0.0

class CheckResultRequest(BaseModel):
    admission_number: str
    pin_code: str
    session: str
    term: str

class ScoreDetail(BaseModel):
    subject_id: uuid.UUID
    ca_score: float
    exam_score: float
    total_score: float
    grade: Optional[str] = None

class StudentResultSheet(BaseModel):
    student_name: str
    admission_number: str
    session: str
    term: str
    pin_remaining_uses: int
    results: List[ScoreDetail]