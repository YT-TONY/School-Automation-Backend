# app/api/v1/endpoints/students.py

import re
import secrets
import string
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_password_hash, require_roles
from app.core.tenant import require_tenant_id
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter()

ADMIN_OR_TEACHER_ROLES = [
    UserRole.SCHOOL_ADMIN,
    UserRole.PRINCIPAL,
    UserRole.VICE_PRINCIPAL,
    UserRole.TEACHER,
    UserRole.CLASS_TEACHER,
    UserRole.SUPER_ADMIN
]

async def _generate_unique_admission_number(last_name: str, school_id: uuid.UUID, db: AsyncSession) -> str:
    clean_surname = re.sub(r'[^A-Za-z]', '', last_name).upper() or "STUDENT"
    for _ in range(10):  # Retry collision loop
        digits = ''.join(secrets.choice(string.digits) for _ in range(6))
        candidate = f"{clean_surname}{digits}"
        query = select(Student).where(Student.school_id == school_id, Student.admission_number == candidate)
        res = await db.execute(query)
        if not res.scalars().first():
            return candidate
    raise HTTPException(status_code=500, detail="Could not generate a unique admission number. Try again.")

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    payload: StudentCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_TEACHER_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    # 1. Resolve or Auto-Generate Admission Number
    if payload.admission_number and payload.admission_number.strip():
        admission_num = payload.admission_number.strip().upper()
        # Verify no collision
        query = select(Student).where(Student.school_id == tenant_id, Student.admission_number == admission_num)
        res = await db.execute(query)
        if res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admission number '{admission_num}' already exists in this school."
            )
    else:
        admission_num = await _generate_unique_admission_number(payload.last_name, tenant_id, db)

    # 2. Instantiate Student Model
    student = Student(
        school_id=tenant_id,
        admission_number=admission_num,
        first_name=payload.first_name,
        last_name=payload.last_name,
        middle_name=payload.middle_name,
        class_arm_id=payload.class_arm_id,
        photo_url=payload.photo_url,
        parent_phone=payload.parent_phone,
        parent_email=payload.parent_email
    )
    db.add(student)

    # 3. Seed User account for student if student_email provided
    temp_password = None
    if payload.student_email:
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        student_user = User(
            school_id=tenant_id,
            email=payload.student_email,
            hashed_password=get_password_hash(temp_password),
            full_name=f"{payload.first_name} {payload.last_name}",
            phone_number=payload.parent_phone,
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(student_user)

    await db.commit()
    await db.refresh(student)

    response_data = StudentResponse.model_validate(student)
    response_data.generated_temp_password = temp_password
    return response_data

@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_TEACHER_ROLES)),
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

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student_by_id(
    student_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_TEACHER_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Student).where(Student.id == student_id, Student.school_id == tenant_id)
    result = await db.execute(query)
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found.")

    return student

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student_profile(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_TEACHER_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Student).where(Student.id == student_id, Student.school_id == tenant_id)
    result = await db.execute(query)
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found.")

    if payload.first_name is not None:
        student.first_name = payload.first_name
    if payload.last_name is not None:
        student.last_name = payload.last_name
    if payload.middle_name is not None:
        student.middle_name = payload.middle_name
    if payload.class_arm_id is not None:
        student.class_arm_id = payload.class_arm_id
    if payload.photo_url is not None:
        student.photo_url = payload.photo_url
    if payload.parent_phone is not None:
        student.parent_phone = payload.parent_phone
    if payload.parent_email is not None:
        student.parent_email = payload.parent_email
    if payload.status is not None:
        student.status = payload.status

    await db.commit()
    await db.refresh(student)
    return student