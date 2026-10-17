# app/schemas/admin_school.py

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

class SchoolOnboardCreate(BaseModel):
    name: str                            # e.g. "St. Gregory's College"
    slug: str                            # e.g. "stgregory"
    subdomain: Optional[str] = None      # e.g. "stgregory"
    custom_domain: Optional[str] = None  # e.g. "stgregoryscollege.com"
    tier: int = 1
    branding: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

    # Primary School Admin Credentials
    admin_email: EmailStr
    admin_full_name: str
    admin_password: str
    admin_phone: Optional[str] = None

class SchoolOnboardResponse(BaseModel):
    school_id: uuid.UUID
    school_name: str
    slug: str
    subdomain: Optional[str]
    custom_domain: Optional[str]
    admin_user_id: uuid.UUID
    admin_email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True