#app/api/v1/endpoints/schools.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.tenant import get_current_school
from app.models.school import School

router = APIRouter()

class SchoolConfigResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    branding: Dict[str, Any]

@router.get("/config", response_model=SchoolConfigResponse)
async def get_school_public_config(current_school: School = Depends(get_current_school)):
    return {
        "id": str(current_school.id),
        "name": current_school.name,
        "slug": current_school.slug,
        "logo_url": current_school.logo_url,
        "address": current_school.address,
        "phone": current_school.phone,
        "email": current_school.email,
        "branding": current_school.branding or {
            "primary_color": "#1E3A8A",
            "secondary_color": "#F59E0B",
            "background_color": "#F8FAFC"
        }
    }