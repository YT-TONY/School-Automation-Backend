#app/api/v1/endpoints/students.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.tenant import get_current_tenant
from app.models.student import Student

router = APIRouter()

class StudentCreate(BaseModel):
    admission_number: str
    first_name: str
    last_name: str
    gender: str
    class_arm_id: Optional[uuid.UUID] = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    admission_number: str
    first_name: str
    last_name: str
    gender: str
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db)
):
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing.")

    student = Student(
        school_id=tenant_id,
        admission_number=payload.admission_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        class_arm_id=payload.class_arm_id
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student

@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing.")

    query = (
        select(Student)
        .where(Student.school_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()