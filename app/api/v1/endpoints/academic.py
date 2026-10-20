# app/api/v1/endpoints/academic.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.core.tenant import require_tenant_id
from app.models.academic import ClassArm, Subject
from app.models.grading import GradingScale
from app.models.user import User, UserRole
from app.schemas.academic import (
    ClassArmCreate,
    ClassArmUpdate,
    ClassArmResponse,
    SubjectCreate,
    SubjectResponse,
)
from app.schemas.grading import (
    GradingScaleCreate,
    GradingScaleUpdate,
    GradingScaleResponse,
)

router = APIRouter()

ADMIN_ROLES = [
    UserRole.SCHOOL_ADMIN,
    UserRole.SUPER_ADMIN,
    UserRole.PRINCIPAL,
    UserRole.VICE_PRINCIPAL_ACADEMIC,
]

# --- Class Arm Endpoints ---

@router.post("/class-arms", response_model=ClassArmResponse, status_code=status.HTTP_201_CREATED)
async def create_class_arm(
    payload: ClassArmCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
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

    if payload.form_teacher_id:
        teacher_q = select(User).where(User.id == payload.form_teacher_id, User.school_id == tenant_id)
        teacher_res = await db.execute(teacher_q)
        if not teacher_res.scalars().first():
            raise HTTPException(status_code=404, detail="Assigned form teacher does not exist in this school.")

    class_arm = ClassArm(
        school_id=tenant_id,
        name=payload.name,
        form_teacher_id=payload.form_teacher_id
    )
    db.add(class_arm)
    await db.commit()
    
    query = select(ClassArm).options(selectinload(ClassArm.form_teacher)).where(ClassArm.id == class_arm.id)
    res = await db.execute(query)
    arm = res.scalars().first()

    return ClassArmResponse(
        id=arm.id,
        school_id=arm.school_id,
        name=arm.name,
        form_teacher_id=arm.form_teacher_id,
        form_teacher_name=arm.form_teacher.full_name if arm.form_teacher else None
    )

@router.get("/class-arms", response_model=List[ClassArmResponse])
async def list_class_arms(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(ClassArm)
        .options(selectinload(ClassArm.form_teacher))
        .where(ClassArm.school_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    arms = result.scalars().all()

    return [
        ClassArmResponse(
            id=arm.id,
            school_id=arm.school_id,
            name=arm.name,
            form_teacher_id=arm.form_teacher_id,
            form_teacher_name=arm.form_teacher.full_name if arm.form_teacher else None
        ) for arm in arms
    ]

@router.put("/class-arms/{class_arm_id}", response_model=ClassArmResponse)
async def update_class_arm(
    class_arm_id: uuid.UUID,
    payload: ClassArmUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(ClassArm).options(selectinload(ClassArm.form_teacher)).where(ClassArm.id == class_arm_id, ClassArm.school_id == tenant_id)
    res = await db.execute(query)
    arm = res.scalars().first()
    if not arm:
        raise HTTPException(status_code=404, detail="Class arm not found.")

    if payload.name is not None:
        arm.name = payload.name
    if payload.form_teacher_id is not None:
        if payload.form_teacher_id:
            teacher_q = select(User).where(User.id == payload.form_teacher_id, User.school_id == tenant_id)
            teacher_res = await db.execute(teacher_q)
            if not teacher_res.scalars().first():
                raise HTTPException(status_code=404, detail="Assigned form teacher does not exist in this school.")
        arm.form_teacher_id = payload.form_teacher_id

    await db.commit()
    
    query_re = select(ClassArm).options(selectinload(ClassArm.form_teacher)).where(ClassArm.id == class_arm_id)
    res_re = await db.execute(query_re)
    updated_arm = res_re.scalars().first()

    return ClassArmResponse(
        id=updated_arm.id,
        school_id=updated_arm.school_id,
        name=updated_arm.name,
        form_teacher_id=updated_arm.form_teacher_id,
        form_teacher_name=updated_arm.form_teacher.full_name if updated_arm.form_teacher else None
    )

# --- Subject Endpoints ---

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
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

# --- Customizable Grading Scale Endpoints ---

@router.post("/grading-scales", response_model=GradingScaleResponse, status_code=status.HTTP_201_CREATED)
async def create_grading_scale(
    payload: GradingScaleCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    if payload.min_score >= payload.max_score:
        raise HTTPException(status_code=400, detail="min_score must be strictly less than max_score.")

    scale = GradingScale(
        school_id=tenant_id,
        grade_letter=payload.grade_letter.upper(),
        min_score=payload.min_score,
        max_score=payload.max_score,
        remark=payload.remark
    )
    db.add(scale)
    await db.commit()
    await db.refresh(scale)
    return scale

@router.get("/grading-scales", response_model=List[GradingScaleResponse])
async def list_grading_scales(
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = select(GradingScale).where(GradingScale.school_id == tenant_id).order_by(GradingScale.min_score.desc())
    res = await db.execute(query)
    return res.scalars().all()

@router.put("/grading-scales/{scale_id}", response_model=GradingScaleResponse)
async def update_grading_scale(
    scale_id: uuid.UUID,
    payload: GradingScaleUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(GradingScale).where(GradingScale.id == scale_id, GradingScale.school_id == tenant_id)
    res = await db.execute(query)
    scale = res.scalars().first()
    if not scale:
        raise HTTPException(status_code=404, detail="Grading scale item not found.")

    if payload.grade_letter is not None:
        scale.grade_letter = payload.grade_letter.upper()
    if payload.min_score is not None:
        scale.min_score = payload.min_score
    if payload.max_score is not None:
        scale.max_score = payload.max_score
    if payload.remark is not None:
        scale.remark = payload.remark

    if scale.min_score >= scale.max_score:
        raise HTTPException(status_code=400, detail="min_score must be strictly less than max_score.")

    await db.commit()
    await db.refresh(scale)
    return scale

@router.delete("/grading-scales/{scale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grading_scale(
    scale_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(GradingScale).where(GradingScale.id == scale_id, GradingScale.school_id == tenant_id)
    res = await db.execute(query)
    scale = res.scalars().first()
    if not scale:
        raise HTTPException(status_code=404, detail="Grading scale item not found.")

    await db.delete(scale)
    await db.commit()
    return None