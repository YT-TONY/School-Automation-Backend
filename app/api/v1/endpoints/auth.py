# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.tenant import get_current_school
from app.models.school import School
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    current_school: School = Depends(get_current_school),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(
        User.email == form_data.username,
        User.school_id == current_school.id
    )
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password for this school portal.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "school_id": str(current_school.id),
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