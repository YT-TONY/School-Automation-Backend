# app/schemas/school.py

import uuid
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.models.school import SchoolType

class SchoolConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
    school_type: SchoolType
    tier: int
    branding: Dict[str, Any]
    settings: Dict[str, Any]

    class Config:
        from_attributes = True