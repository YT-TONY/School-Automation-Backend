# app/api/v1/endpoints/students.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.tenant import require_tenant_id
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentResponse

router = APIRouter()

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    payload: StudentCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    student = Student(
        school_id=tenant_id,
        admission_number=payload.admission_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        middle_name=payload.middle_name,
        class_arm_id=payload.class_arm_id,
        photo_url=payload.photo_url,
        parent_phone=payload.parent_phone,
        parent_email=payload.parent_email
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student

@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Student)
        .where(Student.school_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()