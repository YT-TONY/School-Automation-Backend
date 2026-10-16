#app/api/v1/endpoints/results.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.tenant import get_current_tenant
from app.models.result import Result
from app.models.pin import ResultPin
from app.models.student import Student

router = APIRouter()

class ResultEntry(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    session: str
    term: str
    ca_score: float
    exam_score: float

class CheckResultRequest(BaseModel):
    admission_number: str
    pin_code: str
    session: str
    term: str

@router.post("/batch-upload", status_code=status.HTTP_201_CREATED)
async def upload_results(
    entries: List[ResultEntry],
    db: AsyncSession = Depends(get_db)
):
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing.")

    db_objects = []
    for entry in entries:
        total = entry.ca_score + entry.exam_score
        grade = "A" if total >= 70 else "B" if total >= 60 else "C" if total >= 50 else "D" if total >= 45 else "F"
        
        res = Result(
            school_id=tenant_id,
            student_id=entry.student_id,
            subject_id=entry.subject_id,
            session=entry.session,
            term=entry.term,
            ca_score=entry.ca_score,
            exam_score=entry.exam_score,
            total_score=total,
            grade=grade
        )
        db_objects.append(res)

    db.add_all(db_objects)
    await db.commit()
    return {"inserted": len(db_objects)}

@router.post("/verify-and-view")
async def verify_pin_and_get_results(
    payload: CheckResultRequest,
    db: AsyncSession = Depends(get_db)
):
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing.")

    # 1. Verify Student
    student_q = select(Student).where(
        Student.admission_number == payload.admission_number,
        Student.school_id == tenant_id
    )
    student_res = await db.execute(student_q)
    student = student_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student admission record not found.")

    # 2. Verify Scratch PIN
    pin_q = select(ResultPin).where(
        ResultPin.pin_code == payload.pin_code,
        ResultPin.school_id == tenant_id
    )
    pin_res = await db.execute(pin_q)
    pin = pin_res.scalars().first()

    if not pin:
        raise HTTPException(status_code=400, detail="Invalid scratch PIN code.")
    if pin.use_count >= pin.max_uses:
        raise HTTPException(status_code=400, detail="Scratch PIN usage limit exceeded.")

    # 3. Deduct/Increment PIN Usage
    pin.use_count += 1
    await db.commit()

    # 4. Fetch Results
    results_q = select(Result).where(
        Result.student_id == student.id,
        Result.session == payload.session,
        Result.term == payload.term,
        Result.school_id == tenant_id
    )
    results_res = await db.execute(results_q)
    scores = results_res.scalars().all()

    return {
        "student": {
            "name": f"{student.first_name} {student.last_name}",
            "admission_number": student.admission_number
        },
        "session": payload.session,
        "term": payload.term,
        "pin_remaining_uses": pin.max_uses - pin.use_count,
        "results": [
            {
                "subject_id": str(s.subject_id),
                "ca_score": s.ca_score,
                "exam_score": s.exam_score,
                "total_score": s.total_score,
                "grade": s.grade
            } for s in scores
        ]
    }