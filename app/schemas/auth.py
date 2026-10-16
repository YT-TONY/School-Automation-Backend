#app/schemas/auth.py

import uuid
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: EmailStr
    role: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True