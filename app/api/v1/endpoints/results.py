# app/api/v1/endpoints/results.py

import csv
import io
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import require_roles
from app.core.tenant import require_tenant_id, require_tier
from app.models.academic import Subject
from app.models.pin import ResultPin
from app.models.result import Result, ResultStatus
from app.models.student import Student
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User, UserRole
from app.schemas.result import (
    CheckResultRequest,
    ResultEntry,
    ResultStatusUpdate,
    ScoreDetail,
    StatusUpdateResponse,
    StudentResultSheet,
    BroadsheetResponse,
    BroadsheetRow,
)

router = APIRouter()

async def _verify_teacher_assignment(
    user: User,
    subject_id: uuid.UUID,
    class_arm_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession
):
    if user.role in [UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN, UserRole.PRINCIPAL] or user.is_exam_officer:
        return True

    q = select(TeacherAssignment).where(
        TeacherAssignment.school_id == tenant_id,
        TeacherAssignment.teacher_id == user.id,
        TeacherAssignment.subject_id == subject_id,
        TeacherAssignment.class_arm_id == class_arm_id
    )
    res = await db.execute(q)
    if not res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to upload scores for this subject and class arm."
        )

@router.post("/batch-upload", status_code=status.HTTP_201_CREATED)
async def upload_results(
    entries: List[ResultEntry],
    class_arm_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles([UserRole.TEACHER, UserRole.FORM_TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if entries:
        await _verify_teacher_assignment(current_user, entries[0].subject_id, class_arm_id, tenant_id, db)

    db_objects = []
    for entry in entries:
        ca_total = entry.ca_score if entry.ca_score is not None else (entry.test1_score + entry.test2_score + entry.assignment_score)
        total = ca_total + entry.exam_score
        grade = (
            "A" if total >= 70
            else "B" if total >= 60
            else "C" if total >= 50
            else "D" if total >= 45
            else "F"
        )

        res = Result(
            school_id=tenant_id,
            student_id=entry.student_id,
            subject_id=entry.subject_id,
            session=entry.session,
            term=entry.term,
            test1_score=entry.test1_score,
            test2_score=entry.test2_score,
            assignment_score=entry.assignment_score,
            ca_score=ca_total,
            exam_score=entry.exam_score,
            total_score=total,
            grade=grade,
            status=ResultStatus.DRAFT
        )
        db_objects.append(res)

    db.add_all(db_objects)
    await db.commit()
    return {"inserted": len(db_objects), "status": ResultStatus.DRAFT}

@router.post("/upload-file", status_code=status.HTTP_201_CREATED)
async def upload_results_csv(
    file: UploadFile = File(...),
    subject_id: uuid.UUID = Form(...),
    class_arm_id: uuid.UUID = Form(...),
    session: str = Form(...),
    term: str = Form(...),
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles([UserRole.TEACHER, UserRole.FORM_TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    await _verify_teacher_assignment(current_user, subject_id, class_arm_id, tenant_id, db)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    buffer = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(buffer)

    db_objects = []
    for row in reader:
        adm_no = row.get("admission_number", "").strip().upper()
        if not adm_no:
            continue

        student_q = select(Student).where(Student.admission_number == adm_no, Student.school_id == tenant_id)
        student_res = await db.execute(student_q)
        student = student_res.scalars().first()
        if not student:
            continue

        t1 = float(row.get("test1", 0.0))
        t2 = float(row.get("test2", 0.0))
        assign = float(row.get("assignment", 0.0))
        exam = float(row.get("exam", 0.0))
        ca_tot = t1 + t2 + assign
        total = ca_tot + exam

        grade = "A" if total >= 70 else "B" if total >= 60 else "C" if total >= 50 else "D" if total >= 45 else "F"

        res = Result(
            school_id=tenant_id,
            student_id=student.id,
            subject_id=subject_id,
            session=session,
            term=term,
            test1_score=t1,
            test2_score=t2,
            assignment_score=assign,
            ca_score=ca_tot,
            exam_score=exam,
            total_score=total,
            grade=grade,
            status=ResultStatus.DRAFT
        )
        db_objects.append(res)

    db.add_all(db_objects)
    await db.commit()
    return {"parsed_and_inserted": len(db_objects), "filename": file.filename}

@router.patch("/status", response_model=StatusUpdateResponse)
async def update_result_status(
    payload: ResultStatusUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        update(Result)
        .where(
            Result.school_id == tenant_id,
            Result.session == payload.session,
            Result.term == payload.term
        )
        .values(status=payload.target_status)
    )

    if payload.student_id:
        stmt = stmt.where(Result.student_id == payload.student_id)

    if payload.class_arm_id:
        student_subquery = select(Student.id).where(
            Student.school_id == tenant_id,
            Student.class_arm_id == payload.class_arm_id
        )
        stmt = stmt.where(Result.student_id.in_(student_subquery))

    res = await db.execute(stmt)
    await db.commit()

    return {
        "updated_count": res.rowcount,
        "new_status": payload.target_status,
        "message": f"Successfully transitioned {res.rowcount} result entries to {payload.target_status.value}."
    }

@router.get("/broadsheet/class-arm/{class_arm_id}", response_model=BroadsheetResponse, dependencies=[Depends(require_tier(2))])
async def get_class_broadsheet(
    class_arm_id: uuid.UUID,
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    students_q = select(Student).where(Student.school_id == tenant_id, Student.class_arm_id == class_arm_id)
    students_res = await db.execute(students_q)
    students = students_res.scalars().all()
    if not students:
        raise HTTPException(status_code=404, detail="No students found in this class arm.")

    student_map = {s.id: s for s in students}
    student_ids = list(student_map.keys())

    results_q = (
        select(Result, Subject.name.label("subject_name"), Subject.code.label("subject_code"))
        .join(Subject, Result.subject_id == Subject.id)
        .where(
            Result.school_id == tenant_id,
            Result.session == session,
            Result.term == term,
            Result.student_id.in_(student_ids)
        )
    )
    results_res = await db.execute(results_q)
    rows = results_res.all()

    subject_dict = {}
    student_scores = {s_id: {} for s_id in student_ids}

    for r in rows:
        subj_code = r.subject_code or str(r.Result.subject_id)
        subject_dict[subj_code] = r.subject_name
        student_scores[r.Result.student_id][subj_code] = r.Result.total_score

    broadsheet_rows = []
    for s_id, scores in student_scores.items():
        st = student_map[s_id]
        agg = sum(scores.values())
        avg = (agg / len(scores)) if scores else 0.0
        broadsheet_rows.append({
            "student_id": st.id,
            "student_name": st.full_name,
            "admission_number": st.admission_number,
            "subject_scores": scores,
            "total_aggregate": agg,
            "average_score": avg,
            "position": 0
        })

    broadsheet_rows.sort(key=lambda x: x["total_aggregate"], reverse=True)
    for idx, row in enumerate(broadsheet_rows, start=1):
        row["position"] = idx

    subjects_list = [{"code": k, "name": v} for k, v in subject_dict.items()]

    return BroadsheetResponse(
        class_arm_id=class_arm_id,
        session=session,
        term=term,
        subjects=subjects_list,
        rows=[BroadsheetRow(**r) for r in broadsheet_rows]
    )

@router.get("/admin/student/{student_id}", response_model=StudentResultSheet)
async def get_admin_student_results(
    student_id: uuid.UUID,
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    student_q = select(Student).where(Student.id == student_id, Student.school_id == tenant_id)
    student_res = await db.execute(student_q)
    student = student_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    results_q = (
        select(Result, Subject.name.label("subject_name"), Subject.code.label("subject_code"))
        .join(Subject, Result.subject_id == Subject.id)
        .where(
            Result.student_id == student.id,
            Result.session == session,
            Result.term == term,
            Result.school_id == tenant_id
        )
    )
    results_res = await db.execute(results_q)
    rows = results_res.all()

    scores = [
        ScoreDetail(
            subject_id=r.Result.subject_id,
            subject_name=r.subject_name,
            subject_code=r.subject_code,
            test1_score=r.Result.test1_score,
            test2_score=r.Result.test2_score,
            assignment_score=r.Result.assignment_score,
            ca_score=r.Result.ca_score,
            exam_score=r.Result.exam_score,
            total_score=r.Result.total_score,
            grade=r.Result.grade,
            status=r.Result.status
        ) for r in rows
    ]

    term_avg = (sum(s.total_score for s in scores) / len(scores)) if scores else 0.0

    return StudentResultSheet(
        student_id=student.id,
        student_name=student.full_name,
        admission_number=student.admission_number,
        session=session,
        term=term,
        pin_remaining_uses=None,
        term_average=round(term_avg, 2),
        results=scores
    )

@router.post("/verify-and-view", response_model=StudentResultSheet)
async def verify_pin_and_get_results(
    payload: CheckResultRequest,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    student_q = select(Student).where(
        Student.admission_number == payload.admission_number,
        Student.school_id == tenant_id
    )
    student_res = await db.execute(student_q)
    student = student_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student admission record not found.")

    pin_q = select(ResultPin).where(
        ResultPin.pin_code == payload.pin_code,
        ResultPin.school_id == tenant_id,
        ResultPin.is_active == True
    )
    pin_res = await db.execute(pin_q)
    pin = pin_res.scalars().first()

    if not pin:
        raise HTTPException(status_code=400, detail="Invalid or deactivated scratch PIN code.")
    if pin.times_used >= pin.max_uses:
        raise HTTPException(status_code=400, detail="Scratch PIN usage limit exceeded.")

    results_q = (
        select(Result, Subject.name.label("subject_name"), Subject.code.label("subject_code"))
        .join(Subject, Result.subject_id == Subject.id)
        .where(
            Result.student_id == student.id,
            Result.session == payload.session,
            Result.term == payload.term,
            Result.school_id == tenant_id,
            Result.status == ResultStatus.PUBLISHED
        )
    )
    results_res = await db.execute(results_q)
    rows = results_res.all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published results available for this term/session yet. Contact your school administration."
        )

    pin.times_used += 1
    await db.commit()

    scores = []
    strongest_subject, weakest_subject = None, None
    max_score, min_score = -1.0, 101.0

    for r in rows:
        tot = r.Result.total_score
        if tot > max_score:
            max_score = tot
            strongest_subject = r.subject_name
        if tot < min_score:
            min_score = tot
            weakest_subject = r.subject_name

        scores.append(ScoreDetail(
            subject_id=r.Result.subject_id,
            subject_name=r.subject_name,
            subject_code=r.subject_code,
            test1_score=r.Result.test1_score,
            test2_score=r.Result.test2_score,
            assignment_score=r.Result.assignment_score,
            ca_score=r.Result.ca_score,
            exam_score=r.Result.exam_score,
            total_score=r.Result.total_score,
            grade=r.Result.grade,
            status=r.Result.status
        ))

    term_avg = (sum(s.total_score for s in scores) / len(scores)) if scores else 0.0

    return StudentResultSheet(
        student_id=student.id,
        student_name=student.full_name,
        admission_number=student.admission_number,
        session=payload.session,
        term=payload.term,
        pin_remaining_uses=pin.max_uses - pin.times_used,
        class_position="Verified",
        term_average=round(term_avg, 2),
        strongest_subject=strongest_subject,
        weakest_subject=weakest_subject,
        results=scores
    )