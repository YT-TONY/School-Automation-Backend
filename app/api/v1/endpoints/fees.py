# app/api/v1/endpoints/fees.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.tenant import require_tenant_id, require_tier
from app.core.security import require_roles
from app.models.fee import FeeItem, FeeType, StudentFeeSelection
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.fee import (
    FeeItemCreate,
    FeeItemResponse,
    PackageSelectionRequest,
    StudentInvoiceResponse,
    FeeItemDetail,
)

router = APIRouter()

# Restricted to Tier 2 Tenants
ADMIN_OR_BURSAR = [UserRole.SCHOOL_ADMIN, UserRole.BURSAR, UserRole.SUPER_ADMIN]

@router.post("/items", response_model=FeeItemResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_tier(2))])
async def create_fee_item(
    payload: FeeItemCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_OR_BURSAR)),
    db: AsyncSession = Depends(get_db)
):
    item = FeeItem(
        school_id=tenant_id,
        title=payload.title,
        amount=payload.amount,
        fee_type=payload.fee_type,
        session=payload.session,
        term=payload.term,
        applicable_classes=payload.applicable_classes
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@router.get("/items", response_model=List[FeeItemResponse], dependencies=[Depends(require_tier(2))])
async def list_fee_items(
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = select(FeeItem).where(
        FeeItem.school_id == tenant_id,
        FeeItem.session == session,
        FeeItem.term == term,
        FeeItem.is_active == True
    )
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/select-packages", status_code=status.HTTP_200_OK, dependencies=[Depends(require_tier(2))])
async def save_student_package_selection(
    payload: PackageSelectionRequest,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Allows parents or admins to toggle optional/conditional fee selections for a student."""
    # Delete previous optional selections for clean state
    clear_stmt = select(StudentFeeSelection).where(
        StudentFeeSelection.school_id == tenant_id,
        StudentFeeSelection.student_id == payload.student_id
    )
    existing_res = await db.execute(clear_stmt)
    for record in existing_res.scalars().all():
        await db.delete(record)

    new_selections = [
        StudentFeeSelection(
            school_id=tenant_id,
            student_id=payload.student_id,
            fee_item_id=item_id,
            is_selected=True
        )
        for item_id in payload.selected_fee_item_ids
    ]
    db.add_all(new_selections)
    await db.commit()
    return {"message": "Fee selections saved successfully.", "count": len(new_selections)}

@router.get("/invoice/{student_id}", response_model=StudentInvoiceResponse, dependencies=[Depends(require_tier(2))])
async def generate_student_invoice(
    student_id: uuid.UUID,
    session: str,
    term: str,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Dynamically calculates custom invoice based on mandatory fees + parent selected optional fees."""
    student_q = select(Student).where(Student.id == student_id, Student.school_id == tenant_id)
    student_res = await db.execute(student_q)
    student = student_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    # 1. Fetch active fee items for term
    items_q = select(FeeItem).where(
        FeeItem.school_id == tenant_id,
        FeeItem.session == session,
        FeeItem.term == term,
        FeeItem.is_active == True
    )
    items_res = await db.execute(items_q)
    all_items = items_res.scalars().all()

    # 2. Fetch student's optional selections
    selections_q = select(StudentFeeSelection.fee_item_id).where(
        StudentFeeSelection.school_id == tenant_id,
        StudentFeeSelection.student_id == student_id,
        StudentFeeSelection.is_selected == True
    )
    sel_res = await db.execute(selections_q)
    selected_ids = set(sel_res.scalars().all())

    mandatory_list, optional_list = [], []
    total_due = 0.0

    for item in all_items:
        detail = FeeItemDetail(
            fee_item_id=item.id,
            title=item.title,
            amount=item.amount,
            fee_type=item.fee_type,
            is_selected=(item.id in selected_ids) if item.fee_type != FeeType.MANDATORY else True
        )

        if item.fee_type == FeeType.MANDATORY:
            mandatory_list.append(detail)
            total_due += item.amount
        else:
            optional_list.append(detail)
            if item.id in selected_ids:
                total_due += item.amount

    return StudentInvoiceResponse(
        student_id=student.id,
        student_name=student.full_name,
        admission_number=student.admission_number,
        session=session,
        term=term,
        mandatory_items=mandatory_list,
        optional_items=optional_list,
        total_amount_due=round(total_due, 2)
    )