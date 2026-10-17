# app/api/v1/endpoints/admin_schools.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_password_hash, require_roles
from app.models.school import School
from app.models.user import User, UserRole
from app.schemas.admin_school import SchoolOnboardCreate, SchoolOnboardResponse

router = APIRouter()

SUPER_ADMIN_ROLE = [UserRole.SUPER_ADMIN]

@router.post("/", response_model=SchoolOnboardResponse, status_code=status.HTTP_201_CREATED)
async def register_new_school_tenant(
    payload: SchoolOnboardCreate,
    current_user: User = Depends(require_roles(SUPER_ADMIN_ROLE)),
    db: AsyncSession = Depends(get_db)
):
    # 1. Check for slug/subdomain/custom_domain uniqueness
    slug_q = select(School).where(
        (School.slug == payload.slug) |
        (School.subdomain == payload.subdomain) |
        (School.custom_domain == payload.custom_domain)
    )
    res = await db.execute(slug_q)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A school with this slug, subdomain, or custom domain already exists."
        )

    # 2. Create School Instance
    new_school = School(
        name=payload.name,
        slug=payload.slug.lower(),
        subdomain=payload.subdomain.lower() if payload.subdomain else None,
        custom_domain=payload.custom_domain.lower() if payload.custom_domain else None,
        tier=payload.tier,
        branding=payload.branding or {
            "primary_color": "#1E3A8A",
            "secondary_color": "#F59E0B",
            "background_color": "#F8FAFC"
        },
        settings=payload.settings or {
            "enable_whatsapp_bot": False,
            "allow_parent_pin_purchase": True,
            "pass_mark_threshold": 50,
            "current_session": "2025/2026",
            "current_term": "First Term"
        }
    )
    db.add(new_school)
    await db.flush()  # Populates new_school.id

    # 3. Create Primary SCHOOL_ADMIN User
    admin_user = User(
        school_id=new_school.id,
        email=payload.admin_email,
        hashed_password=get_password_hash(payload.admin_password),
        full_name=payload.admin_full_name,
        phone_number=payload.admin_phone,
        role=UserRole.SCHOOL_ADMIN,
        is_active=True
    )
    db.add(admin_user)

    await db.commit()
    await db.refresh(new_school)
    await db.refresh(admin_user)

    return SchoolOnboardResponse(
        school_id=new_school.id,
        school_name=new_school.name,
        slug=new_school.slug,
        subdomain=new_school.subdomain,
        custom_domain=new_school.custom_domain,
        admin_user_id=admin_user.id,
        admin_email=admin_user.email,
        created_at=new_school.created_at
    )