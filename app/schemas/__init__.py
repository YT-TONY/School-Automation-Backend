# app/schemas/__init__.py

from app.schemas.school import SchoolConfigResponse
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.result import (
    ResultEntry,
    ResultStatusUpdate,
    StatusUpdateResponse,
    CheckResultRequest,
    StudentResultSheet,
    ScoreDetail,
)
from app.schemas.pin import PinGenerateRequest, PinGenerateResponse, PinResponse
from app.schemas.academic import (
    ClassArmCreate,
    ClassArmResponse,
    SubjectCreate,
    SubjectResponse,
)

__all__ = [
    "SchoolConfigResponse",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "StudentCreate",
    "StudentResponse",
    "ResultEntry",
    "ResultStatusUpdate",
    "StatusUpdateResponse",
    "CheckResultRequest",
    "StudentResultSheet",
    "ScoreDetail",
    "PinGenerateRequest",
    "PinGenerateResponse",
    "PinResponse",
    "ClassArmCreate",
    "ClassArmResponse",
    "SubjectCreate",
    "SubjectResponse",
]