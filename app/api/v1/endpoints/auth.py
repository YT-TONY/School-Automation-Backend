# app/api/v1/endpoints/auth.py

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.tenant import get_current_tenant
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_tenant_id: Optional[uuid.UUID] = Header(None, alias="X-Tenant-ID"),
    tenant_id: Optional[uuid.UUID] = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    # Validate tenant context if explicitly supplied; fall back to user's assigned school_id
    active_tenant = x_tenant_id or tenant_id
    if user.role != UserRole.SUPER_ADMIN and active_tenant:
        if user.school_id != active_tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not belong to the requested school portal."
            )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    school_id_str = str(user.school_id) if user.school_id else None

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "school_id": school_id_str,
            "role": role_str
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=role_str
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user