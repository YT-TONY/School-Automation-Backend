# app/schemas/__init__.py

from app.schemas.school import SchoolConfigResponse
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.user import UserCreate, UserUpdate, UserPermissionsUpdate
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.result import (
    ResultEntry,
    ResultStatusUpdate,
    StatusUpdateResponse,
    CheckResultRequest,
    StudentResultSheet,
    ScoreDetail,
    BroadsheetRow,
    BroadsheetResponse,
)
from app.schemas.pin import PinGenerateRequest, PinGenerateResponse, PinResponse
from app.schemas.academic import (
    ClassArmCreate,
    ClassArmResponse,
    SubjectCreate,
    SubjectResponse,
)
from app.schemas.fee import (
    FeeItemCreate,
    FeeItemResponse,
    PackageSelectionRequest,
    StudentInvoiceResponse,
    FeeItemDetail,
)

__all__ = [
    "SchoolConfigResponse",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "UserPermissionsUpdate",
    "StudentCreate",
    "StudentResponse",
    "ResultEntry",
    "ResultStatusUpdate",
    "StatusUpdateResponse",
    "CheckResultRequest",
    "StudentResultSheet",
    "ScoreDetail",
    "BroadsheetRow",
    "BroadsheetResponse",
    "PinGenerateRequest",
    "PinGenerateResponse",
    "PinResponse",
    "ClassArmCreate",
    "ClassArmResponse",
    "SubjectCreate",
    "SubjectResponse",
    "FeeItemCreate",
    "FeeItemResponse",
    "PackageSelectionRequest",
    "StudentInvoiceResponse",
    "FeeItemDetail",
]