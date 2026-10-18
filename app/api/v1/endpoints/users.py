# app/api/v1/endpoints/users.py

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import require_roles, get_password_hash
from app.core.tenant import require_tenant_id, require_tier
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserPermissionsUpdate

router = APIRouter()

ADMIN_ROLES = [
    UserRole.SCHOOL_ADMIN,
    UserRole.PRINCIPAL,
    UserRole.VICE_PRINCIPAL_ACADEMIC,
    UserRole.VICE_PRINCIPAL_ADMIN,
    UserRole.SUPER_ADMIN
]

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    payload: UserCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_admin: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    existing_query = select(User).where(User.school_id == tenant_id, User.email == payload.email)
    existing_res = await db.execute(existing_query)
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{payload.email}' already exists in this school."
        )

    is_exam_officer = payload.role == UserRole.EXAM_OFFICER
    is_class_teacher = payload.role == UserRole.FORM_TEACHER
    can_enroll = payload.role in [UserRole.SCHOOL_ADMIN, UserRole.VICE_PRINCIPAL_ADMIN]

    user = User(
        school_id=tenant_id,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=payload.role,
        is_active=True,
        is_exam_officer=is_exam_officer,
        is_class_teacher=is_class_teacher,
        can_enroll_students=can_enroll
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- Tier 2 Feature: Granular Permission Toggles ---
@router.patch("/{user_id}/permissions", response_model=UserResponse, dependencies=[Depends(require_tier(2))])
async def toggle_staff_permissions(
    user_id: uuid.UUID,
    payload: UserPermissionsUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_admin: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Tier 2 Feature: Toggles specific operational privileges for a staff member."""
    query = select(User).where(User.id == user_id, User.school_id == tenant_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user record not found.")

    if payload.is_exam_officer is not None:
        user.is_exam_officer = payload.is_exam_officer
    if payload.is_class_teacher is not None:
        user.is_class_teacher = payload.is_class_teacher
    if payload.can_enroll_students is not None:
        user.can_enroll_students = payload.can_enroll_students
    if payload.can_manage_fees is not None:
        user.can_manage_fees = payload.can_manage_fees
    if payload.can_approve_results is not None:
        user.can_approve_results = payload.can_approve_results

    await db.commit()
    await db.refresh(user)
    return user

@router.get("/", response_model=List[UserResponse])
async def list_staff_users(
    role: Optional[UserRole] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_admin: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.school_id == tenant_id)
    if role:
        query = query.where(User.role == role)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserResponse)
async def get_staff_user_by_id(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_admin: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.id == user_id, User.school_id == tenant_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_staff_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_admin: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.id == user_id, User.school_id == tenant_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    await db.commit()
    await db.refresh(user)
    return user