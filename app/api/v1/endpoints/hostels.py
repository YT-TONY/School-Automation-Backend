# app/api/v1/endpoints/hostels.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.core.tenant import require_tenant_id, require_tier, get_current_school
from app.models.hostel import Hostel, HostelRoom, BedAllocation, ReservationStatus
from app.models.school import School, SchoolType
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.hostel import (
    HostelCreate,
    HostelResponse,
    HostelRoomResponse,
    BedReservationRequest,
    BedReservationResponse,
)

router = APIRouter()

ADMIN_ROLES = [UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]

# --- Dependency: Restrict Hostel Features to BOARDING or MIXED Schools Only ---
async def require_boarding_or_mixed_school(
    school: School = Depends(get_current_school)
):
    if school.school_type == SchoolType.DAY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hostel and boarding management is disabled for Day-only institutions."
        )
    return school

# --- 1. Admin Hostel Setup ---
@router.post("/", response_model=HostelResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_tier(2)), Depends(require_boarding_or_mixed_school)])
async def create_hostel_and_rooms(
    payload: HostelCreate,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    hostel = Hostel(
        school_id=tenant_id,
        name=payload.name,
        gender=payload.gender,
        description=payload.description
    )
    db.add(hostel)
    await db.flush()

    for r in payload.rooms:
        room = HostelRoom(
            school_id=tenant_id,
            hostel_id=hostel.id,
            room_number=r.room_number,
            capacity=r.capacity,
            termly_fee=r.termly_fee
        )
        db.add(room)

    await db.commit()
    
    query = select(Hostel).options(selectinload(Hostel.rooms)).where(Hostel.id == hostel.id)
    res = await db.execute(query)
    return res.scalars().first()

# --- 2. List Hostels & Availability ---
@router.get("/", response_model=List[HostelResponse], dependencies=[Depends(require_tier(2)), Depends(require_boarding_or_mixed_school)])
async def list_hostels(
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    query = select(Hostel).options(selectinload(Hostel.rooms).selectinload(HostelRoom.allocations)).where(Hostel.school_id == tenant_id)
    res = await db.execute(query)
    hostels = res.scalars().all()

    response = []
    for h in hostels:
        rooms_data = []
        for r in h.rooms:
            active_allocations = len([a for a in r.allocations if a.status != ReservationStatus.VACATED])
            rooms_data.append(HostelRoomResponse(
                id=r.id,
                room_number=r.room_number,
                capacity=r.capacity,
                termly_fee=r.termly_fee,
                occupied_count=active_allocations,
                available_beds=max(0, r.capacity - active_allocations)
            ))
        response.append(HostelResponse(
            id=h.id,
            name=h.name,
            gender=h.gender,
            description=h.description,
            rooms=rooms_data
        ))
    return response

# --- 3. Student Self-Service Bed Space Reservation ---
@router.post("/reserve-bed", response_model=BedReservationResponse, dependencies=[Depends(require_tier(2)), Depends(require_boarding_or_mixed_school)])
async def reserve_bed_space(
    payload: BedReservationRequest,
    tenant_id: uuid.UUID = Depends(require_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    student_q = select(Student).where(Student.id == payload.student_id, Student.school_id == tenant_id)
    student_res = await db.execute(student_q)
    student = student_res.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    room_q = select(HostelRoom).options(selectinload(HostelRoom.allocations), selectinload(HostelRoom.hostel)).where(
        HostelRoom.id == payload.room_id,
        HostelRoom.school_id == tenant_id
    )
    room_res = await db.execute(room_q)
    room = room_res.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Hostel room not found.")

    active_allocations = [a for a in room.allocations if a.status != ReservationStatus.VACATED]
    if len(active_allocations) >= room.capacity:
        raise HTTPException(status_code=400, detail="This room is fully booked. Please select another room.")

    existing_q = select(BedAllocation).where(
        BedAllocation.school_id == tenant_id,
        BedAllocation.student_id == payload.student_id,
        BedAllocation.session == payload.session,
        BedAllocation.term == payload.term,
        BedAllocation.status != ReservationStatus.VACATED
    )
    existing_res = await db.execute(existing_q)
    if existing_res.scalars().first():
        raise HTTPException(status_code=400, detail="Student already has an active bed space reservation for this term.")

    allocation = BedAllocation(
        school_id=tenant_id,
        room_id=room.id,
        student_id=student.id,
        session=payload.session,
        term=payload.term,
        status=ReservationStatus.RESERVED
    )
    db.add(allocation)
    await db.commit()
    await db.refresh(allocation)

    return BedReservationResponse(
        allocation_id=allocation.id,
        student_id=student.id,
        room_number=room.room_number,
        hostel_name=room.hostel.name,
        status=allocation.status,
        termly_fee=room.termly_fee,
        message=f"Bed space reserved successfully in {room.hostel.name} ({room.room_number}). Boarding fee appended to invoice."
    )