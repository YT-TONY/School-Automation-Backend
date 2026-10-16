#app/schemas/school.py

import uuid
from pydantic import BaseModel
from typing import Dict, Any, Optional

class SchoolConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
    branding: Dict[str, Any]
    settings: Dict[str, Any]

    class Config:
        from_attributes = True