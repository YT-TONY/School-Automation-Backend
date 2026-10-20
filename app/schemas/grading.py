# app/schemas/grading.py

import uuid
from typing import Optional
from pydantic import BaseModel, Field

class GradingScaleCreate(BaseModel):
    grade_letter: str = Field(..., max_length=10, description="Grade designation (e.g., A1, B2, A, DISTINCTION)")
    min_score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(..., ge=0.0, le=100.0)
    remark: Optional[str] = Field(None, max_length=50)

class GradingScaleUpdate(BaseModel):
    grade_letter: Optional[str] = Field(None, max_length=10)
    min_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    remark: Optional[str] = Field(None, max_length=50)

class GradingScaleResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    grade_letter: str
    min_score: float
    max_score: float
    remark: Optional[str]

    class Config:
        from_attributes = True