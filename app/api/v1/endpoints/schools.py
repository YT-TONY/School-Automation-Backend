# app/api/v1/endpoints/schools.py

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
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
    tier: int
    branding: Dict[str, Any]
    settings: Dict[str, Any]

@router.get("/config", response_model=SchoolConfigResponse)
async def get_school_public_config(current_school: School = Depends(get_current_school)):
    return SchoolConfigResponse(
        id=str(current_school.id),
        name=current_school.name,
        slug=current_school.slug,
        subdomain=current_school.subdomain,
        custom_domain=current_school.custom_domain,
        tier=current_school.tier,
        branding=current_school.branding or {
            "primary_color": "#1E3A8A",
            "secondary_color": "#F59E0B",
            "background_color": "#F8FAFC"
        },
        settings=current_school.settings or {
            "enable_whatsapp_bot": False,
            "allow_parent_pin_purchase": True,
            "pass_mark_threshold": 50,
            "current_session": "2025/2026",
            "current_term": "First Term"
        }
    )