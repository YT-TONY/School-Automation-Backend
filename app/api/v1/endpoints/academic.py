# app/api/v1/endpoints/academic.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.tenant import require_tenant_id
from app.models.academic import ClassArm, Subject
from app.schemas.academic import (
    ClassArmCreate,
    ClassArmResponse,
    SubjectCreate,
    SubjectResponse,
)

router = APIRouter()

# --- Class Arm Endpoints ---

@router.post("/class-arms", response_model=ClassArmResponse, status_code=status.HTTP_201_CREATED)
async def create_class_arm(
    payload: ClassArmCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    # Enforce uniqueness per school
    existing_query = select(ClassArm).where(
        ClassArm.school_id == tenant_id,
        ClassArm.name == payload.name
    )
    existing_res = await db.execute(existing_query)
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class arm '{payload.name}' already exists for this school."
        )

    class_arm = ClassArm(
        school_id=tenant_id,
        name=payload.name
    )
    db.add(class_arm)
    await db.commit()
    await db.refresh(class_arm)
    return class_arm

@router.get("/class-arms", response_model=List[ClassArmResponse])
async def list_class_arms(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(ClassArm)
        .where(ClassArm.school_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()

# --- Subject Endpoints ---

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    # Enforce subject code uniqueness per school
    existing_query = select(Subject).where(
        Subject.school_id == tenant_id,
        Subject.code == payload.code
    )
    existing_res = await db.execute(existing_query)
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject code '{payload.code}' already exists for this school."
        )

    subject = Subject(
        school_id=tenant_id,
        name=payload.name,
        code=payload.code
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Subject)
        .where(Subject.school_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()