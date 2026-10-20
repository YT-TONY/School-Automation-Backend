# app/schemas/psychomotor.py

import uuid
from pydantic import BaseModel, Field

class AffectivePsychomotorPayload(BaseModel):
    student_id: uuid.UUID
    session: str
    term: str
    punctuality: int = Field(default=3, ge=1, le=5)
    neatness: int = Field(default=3, ge=1, le=5)
    leadership: int = Field(default=3, ge=1, le=5)
    honesty: int = Field(default=3, ge=1, le=5)
    politeness: int = Field(default=3, ge=1, le=5)
    handwriting: int = Field(default=3, ge=1, le=5)
    sports_and_games: int = Field(default=3, ge=1, le=5)
    craft_and_art: int = Field(default=3, ge=1, le=5)

class AffectivePsychomotorResponse(AffectivePsychomotorPayload):
    id: uuid.UUID
    message: str

    class Config:
        from_attributes = True