from app.schemas.school import SchoolConfigResponse
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.result import (
    ResultEntry,
    CheckResultRequest,
    StudentResultSheet,
    ScoreDetail,
)
from app.schemas.pin import PinGenerateRequest, PinGenerateResponse, PinResponse

__all__ = [
    "SchoolConfigResponse",
    "TokenResponse",
    "UserResponse",
    "StudentCreate",
    "StudentResponse",
    "ResultEntry",
    "CheckResultRequest",
    "StudentResultSheet",
    "ScoreDetail",
    "PinGenerateRequest",
    "PinGenerateResponse",
    "PinResponse",
]