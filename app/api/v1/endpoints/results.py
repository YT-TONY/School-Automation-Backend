# app/api/v1/endpoints/results.py

import csv
import io
import uuid
from typing import List, Dict, Set, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import openpyxl
from jinja2 import Template

from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.core.tenant import require_tenant_id, require_tier, get_current_school
from app.models.academic import Subject, ClassArm
from app.models.audit import ResultStatusAudit
from app.models.grading import GradingScale
from app.models.pin import ResultPin
from app.models.psychomotor import AffectivePsychomotorDomain
from app.models.remark import TerminalRemark
from app.models.result import Result, ResultStatus
from app.models.school import School
from app.models.student import Student
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User, UserRole
from app.schemas.audit import ResultStatusAuditResponse
from app.schemas.psychomotor import AffectivePsychomotorPayload, AffectivePsychomotorResponse
from app.schemas.result import (
    CheckResultRequest,
    ResultEntry,
    ResultStatusUpdate,
    ScoreDetail,
    StatusUpdateResponse,
    StudentResultSheet,
    BroadsheetResponse,
    BroadsheetRow,
    RemarkUpdatePayload,
    RemarkResponse,
)

router = APIRouter()

VALID_PREDECESSORS: Dict[ResultStatus, Set[ResultStatus]] = {
    ResultStatus.SUBMITTED_BY_TEACHER: {ResultStatus.DRAFT},
    ResultStatus.COMPILED_BY_CLASS_TEACHER: {ResultStatus.SUBMITTED_BY_TEACHER},
    ResultStatus.APPROVED_BY_VP: {ResultStatus.COMPILED_BY_CLASS_TEACHER},
    ResultStatus.PUBLISHED: {ResultStatus.APPROVED_BY_VP},
    ResultStatus.DRAFT: {
        ResultStatus.SUBMITTED_BY_TEACHER,
        ResultStatus.COMPILED_BY_CLASS_TEACHER,
        ResultStatus.APPROVED_BY_VP,
        ResultStatus.PUBLISHED
    }
}

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

# Helper: Dynamic Grade Resolution Engine
async def _resolve_grade(total_score: float, tenant_id: uuid.UUID, db: AsyncSession) -> str:
    scales_q = select(GradingScale).where(GradingScale.school_id == tenant_id).order_by(GradingScale.min_score.desc())
    scales_res = await db.execute(scales_q)
    scales = scales_res.scalars().all()

    if scales:
        for scale in scales:
            if scale.min_score <= total_score <= scale.max_score:
                return scale.grade_letter
            if total_score >= scale.min_score and scale == scales[0]:
                return scale.grade_letter

    # Default WAEC Standard Scale Fallback
    if total_score >= 70:
        return "A"
    elif total_score >= 60:
        return "B"
    elif total_score >= 50:
        return "C"
    elif total_score >= 45:
        return "D"
    return "F"

# --- 1. Batch Score Ingestion ---
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
        grade = await _resolve_grade(total, tenant_id, db)

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

# --- 2. CSV File Ingestion Endpoint ---
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
        grade = await _resolve_grade(total, tenant_id, db)

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

# --- 3. Audit Log Review Endpoint ---
@router.get("/audits", response_model=List[ResultStatusAuditResponse])
async def list_result_audits(
    session: Optional[str] = None,
    term: Optional[str] = None,
    class_arm_id: Optional[uuid.UUID] = None,
    student_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Allows Vice Principals, Exam Officers, and Admins to inspect historical result status transitions."""
    ALLOWED_ROLES = [
        UserRole.SCHOOL_ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.PRINCIPAL,
        UserRole.VICE_PRINCIPAL_ACADEMIC,
        UserRole.VICE_PRINCIPAL_ADMIN
    ]
    if current_user.role not in ALLOWED_ROLES and not current_user.is_exam_officer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view result transition audit logs."
        )

    query = select(ResultStatusAudit).where(ResultStatusAudit.school_id == tenant_id)

    if session:
        query = query.where(ResultStatusAudit.session == session)
    if term:
        query = query.where(ResultStatusAudit.term == term)
    if class_arm_id:
        query = query.where(ResultStatusAudit.class_arm_id == class_arm_id)
    if student_id:
        query = query.where(ResultStatusAudit.student_id == student_id)
    if user_id:
        query = query.where(ResultStatusAudit.user_id == user_id)

    query = query.order_by(ResultStatusAudit.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()

# --- 4. Behavioral Ratings ---
@router.patch("/behavioral-ratings", response_model=AffectivePsychomotorResponse, dependencies=[Depends(require_tier(2))])
async def update_behavioral_ratings(
    payload: AffectivePsychomotorPayload,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles([UserRole.FORM_TEACHER, UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    q = select(AffectivePsychomotorDomain).where(
        AffectivePsychomotorDomain.school_id == tenant_id,
        AffectivePsychomotorDomain.student_id == payload.student_id,
        AffectivePsychomotorDomain.session == payload.session,
        AffectivePsychomotorDomain.term == payload.term
    )
    res = await db.execute(q)
    rating = res.scalars().first()

    if not rating:
        rating = AffectivePsychomotorDomain(
            school_id=tenant_id,
            student_id=payload.student_id,
            session=payload.session,
            term=payload.term,
            punctuality=payload.punctuality,
            neatness=payload.neatness,
            leadership=payload.leadership,
            honesty=payload.honesty,
            politeness=payload.politeness,
            handwriting=payload.handwriting,
            sports_and_games=payload.sports_and_games,
            craft_and_art=payload.craft_and_art
        )
        db.add(rating)
    else:
        rating.punctuality = payload.punctuality
        rating.neatness = payload.neatness
        rating.leadership = payload.leadership
        rating.honesty = payload.honesty
        rating.politeness = payload.politeness
        rating.handwriting = payload.handwriting
        rating.sports_and_games = payload.sports_and_games
        rating.craft_and_art = payload.craft_and_art

    await db.commit()
    await db.refresh(rating)

    resp = AffectivePsychomotorResponse.model_validate(rating)
    resp.message = "Affective & Psychomotor ratings updated successfully."
    return resp

# --- 5. Historical Trends ---
@router.get("/historical-trends/student/{student_id}", dependencies=[Depends(require_tier(2))])
async def get_student_historical_trends(
    student_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    q = (
        select(
            Result.session,
            Result.term,
            func.avg(Result.total_score).label("term_average"),
            func.sum(Result.total_score).label("total_aggregate"),
            func.count(Result.id).label("subject_count")
        )
        .where(
            Result.school_id == tenant_id,
            Result.student_id == student_id,
            Result.status == ResultStatus.PUBLISHED
        )
        .group_by(Result.session, Result.term)
        .order_by(Result.session.asc(), Result.term.asc())
    )
    res = await db.execute(q)
    rows = res.all()

    trends = [
        {
            "session": r.session,
            "term": r.term,
            "term_average": round(float(r.term_average), 2),
            "total_aggregate": float(r.total_aggregate),
            "subject_count": r.subject_count
        } for r in rows
    ]
    return {"student_id": student_id, "historical_terms_count": len(trends), "performance_history": trends}

# --- 6. PDF Report Card Download ---
@router.get("/download-pdf", dependencies=[Depends(require_tier(2))])
async def download_student_report_card_pdf(
    student_id: uuid.UUID,
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    school: School = Depends(get_current_school),
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
        {
            "subject": r.subject_name,
            "ca": r.Result.ca_score,
            "exam": r.Result.exam_score,
            "total": r.Result.total_score,
            "grade": r.Result.grade
        } for r in rows
    ]
    term_avg = round((sum(s["total"] for s in scores) / len(scores)), 2) if scores else 0.0

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; color: #1e293b; }
            .header { text-align: center; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }
            .school-name { font-size: 24px; font-weight: bold; color: {{ primary_color }}; }
            .details { margin: 20px 0; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
            th { background-color: #f1f5f9; }
            .summary { margin-top: 20px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="school-name">{{ school_name }}</div>
            <div>OFFICIAL TERMINAL REPORT CARD</div>
            <div>{{ term }} - {{ session }}</div>
        </div>
        <div class="details">
            <div><strong>Student:</strong> {{ student_name }} ({{ admission_number }})</div>
            <div><strong>Average:</strong> {{ term_average }}%</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Subject</th><th>CA Score</th><th>Exam Score</th><th>Total</th><th>Grade</th>
                </tr>
            </thead>
            <tbody>
                {% for item in scores %}
                <tr>
                    <td>{{ item.subject }}</td>
                    <td>{{ item.ca }}</td>
                    <td>{{ item.exam }}</td>
                    <td>{{ item.total }}</td>
                    <td>{{ item.grade }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="summary">Term Average Score: {{ term_average }}%</div>
    </body>
    </html>
    """

    template = Template(html_template)
    rendered_html = template.render(
        school_name=school.name,
        primary_color=school.branding.get("primary_color", "#1E3A8A"),
        student_name=student.full_name,
        admission_number=student.admission_number,
        session=session,
        term=term,
        scores=scores,
        term_average=term_avg
    )

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        media_type = "application/pdf"
        filename = f"Report_Card_{student.admission_number}_{session}_{term}.pdf".replace(" ", "_")
    except ImportError:
        pdf_bytes = rendered_html.encode("utf-8")
        media_type = "text/html"
        filename = f"Report_Card_{student.admission_number}_{session}_{term}.html".replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- 7. Remarks ---
@router.patch("/remarks", response_model=RemarkResponse, dependencies=[Depends(require_tier(2))])
async def update_terminal_remarks(
    payload: RemarkUpdatePayload,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles([UserRole.FORM_TEACHER, UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    q = select(TerminalRemark).where(
        TerminalRemark.school_id == tenant_id,
        TerminalRemark.student_id == payload.student_id,
        TerminalRemark.session == payload.session,
        TerminalRemark.term == payload.term
    )
    res = await db.execute(q)
    remark = res.scalars().first()

    if not remark:
        remark = TerminalRemark(
            school_id=tenant_id,
            student_id=payload.student_id,
            session=payload.session,
            term=payload.term,
            form_teacher_remark=payload.form_teacher_remark,
            principal_remark=payload.principal_remark
        )
        db.add(remark)
    else:
        if payload.form_teacher_remark is not None:
            remark.form_teacher_remark = payload.form_teacher_remark
        if payload.principal_remark is not None:
            remark.principal_remark = payload.principal_remark

    await db.commit()
    await db.refresh(remark)

    return RemarkResponse(
        student_id=remark.student_id,
        session=remark.session,
        term=remark.term,
        form_teacher_remark=remark.form_teacher_remark,
        principal_remark=remark.principal_remark,
        message="Terminal remark updated successfully."
    )

# --- 8. Result Approval Workflow ---
@router.patch("/status", response_model=StatusUpdateResponse)
async def update_result_status(
    payload: ResultStatusUpdate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target = payload.target_status
    if target == ResultStatus.COMPILED_BY_CLASS_TEACHER and not (current_user.is_class_teacher or current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN, UserRole.FORM_TEACHER]):
        raise HTTPException(status_code=403, detail="Only Form/Class Teachers or Admins can transition results to COMPILED.")

    if target == ResultStatus.APPROVED_BY_VP and not (current_user.role in [UserRole.VICE_PRINCIPAL_ACADEMIC, UserRole.PRINCIPAL, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN] or current_user.can_approve_results):
        raise HTTPException(status_code=403, detail="Only Vice Principals or authorized approvers can approve results.")

    if target == ResultStatus.PUBLISHED and not (current_user.role in [UserRole.VICE_PRINCIPAL_ACADEMIC, UserRole.PRINCIPAL, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN] or current_user.can_approve_results or current_user.is_exam_officer):
        raise HTTPException(status_code=403, detail="Only Vice Principals, Exam Officers, or Admins can publish final gradebooks.")

    query = select(Result).where(
        Result.school_id == tenant_id,
        Result.session == payload.session,
        Result.term == payload.term
    )
    if payload.student_id:
        query = query.where(Result.student_id == payload.student_id)
    if payload.class_arm_id:
        student_subquery = select(Student.id).where(
            Student.school_id == tenant_id,
            Student.class_arm_id == payload.class_arm_id
        )
        query = query.where(Result.student_id.in_(student_subquery))

    res = await db.execute(query)
    existing_results = res.scalars().all()

    if not existing_results:
        raise HTTPException(status_code=404, detail="No matching result entries found to transition.")

    allowed_preds = VALID_PREDECESSORS.get(target, set())
    invalid_transitions = [r for r in existing_results if r.status not in allowed_preds]

    is_admin = current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]
    if invalid_transitions and not is_admin:
        sample = invalid_transitions[0]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal transition gate skip: Cannot move results from '{sample.status.value}' directly to '{target.value}' without intermediate approval."
        )

    previous_statuses = {r.status.value for r in existing_results}
    prev_status_summary = ", ".join(previous_statuses)

    stmt = (
        update(Result)
        .where(Result.id.in_([r.id for r in existing_results]))
        .values(status=target)
    )
    await db.execute(stmt)

    audit_log = ResultStatusAudit(
        school_id=tenant_id,
        user_id=current_user.id,
        session=payload.session,
        term=payload.term,
        class_arm_id=payload.class_arm_id,
        student_id=payload.student_id,
        previous_status=prev_status_summary,
        target_status=target,
        records_affected=len(existing_results)
    )
    db.add(audit_log)
    await db.commit()

    return {
        "updated_count": len(existing_results),
        "new_status": target,
        "message": f"Successfully transitioned {len(existing_results)} result entries to {target.value}. Transition logged to audit ledger."
    }

# --- 9. Broadsheet ---
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

    remarks_q = select(TerminalRemark).where(
        TerminalRemark.school_id == tenant_id,
        TerminalRemark.session == session,
        TerminalRemark.term == term,
        TerminalRemark.student_id.in_(student_ids)
    )
    remarks_res = await db.execute(remarks_q)
    remark_map = {r.student_id: r.form_teacher_remark for r in remarks_res.scalars().all()}

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
            "position": 0,
            "form_teacher_remark": remark_map.get(s_id)
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

# --- 10. Excel Export ---
@router.get("/broadsheet/export", dependencies=[Depends(require_tier(2))])
async def export_class_broadsheet_excel(
    class_arm_id: uuid.UUID,
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    broadsheet = await get_class_broadsheet(class_arm_id, session, term, tenant_id, db)

    arm_q = select(ClassArm).where(ClassArm.id == class_arm_id)
    arm_res = await db.execute(arm_q)
    arm = arm_res.scalars().first()
    arm_name = arm.name if arm else "Class_Arm"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Broadsheet_{session.replace('/', '_')}"

    headers = ["Position", "Admission No", "Student Name"]
    subject_codes = [s["code"] for s in broadsheet.subjects]
    headers.extend(subject_codes)
    headers.extend(["Total Aggregate", "Average Score", "Form Teacher Remark"])
    ws.append(headers)

    for row in broadsheet.rows:
        data_row = [row.position, row.admission_number, row.student_name]
        for code in subject_codes:
            data_row.append(row.subject_scores.get(code, "-"))
        data_row.extend([row.total_aggregate, round(row.average_score, 2), row.form_teacher_remark or ""])
        ws.append(data_row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Broadsheet_{arm_name}_{session}_{term}.xlsx".replace(" ", "_")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- 11. Admin / Teacher Result Viewer ---
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

    remarks_q = select(TerminalRemark).where(
        TerminalRemark.school_id == tenant_id,
        TerminalRemark.student_id == student.id,
        TerminalRemark.session == session,
        TerminalRemark.term == term
    )
    remarks_res = await db.execute(remarks_q)
    remark = remarks_res.scalars().first()

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
        form_teacher_remark=remark.form_teacher_remark if remark else None,
        principal_remark=remark.principal_remark if remark else None,
        results=scores
    )

# --- 12. Public PIN-Protected Result Engine ---
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

    remarks_q = select(TerminalRemark).where(
        TerminalRemark.school_id == tenant_id,
        TerminalRemark.student_id == student.id,
        TerminalRemark.session == payload.session,
        TerminalRemark.term == payload.term
    )
    remarks_res = await db.execute(remarks_q)
    remark = remarks_res.scalars().first()

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
        form_teacher_remark=remark.form_teacher_remark if remark else None,
        principal_remark=remark.principal_remark if remark else None,
        results=scores
    )