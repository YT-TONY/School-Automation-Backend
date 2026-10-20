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
    RemarkUpdatePayload,
    RemarkResponse,
)
from app.schemas.pin import (
    PinGenerateRequest,
    PinGenerateResponse,
    PinResponse,
    OnlinePinPurchaseRequest,
    OnlinePinPurchaseResponse,
)
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
from app.schemas.psychomotor import (
    AffectivePsychomotorPayload,
    AffectivePsychomotorResponse,
)
from app.schemas.hostel import (
    HostelCreate,
    HostelResponse,
    HostelRoomResponse,
    BedReservationRequest,
    BedReservationResponse,
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
    "RemarkUpdatePayload",
    "RemarkResponse",
    "PinGenerateRequest",
    "PinGenerateResponse",
    "PinResponse",
    "OnlinePinPurchaseRequest",
    "OnlinePinPurchaseResponse",
    "ClassArmCreate",
    "ClassArmResponse",
    "SubjectCreate",
    "SubjectResponse",
    "FeeItemCreate",
    "FeeItemResponse",
    "PackageSelectionRequest",
    "StudentInvoiceResponse",
    "FeeItemDetail",
    "AffectivePsychomotorPayload",
    "AffectivePsychomotorResponse",
    "HostelCreate",
    "HostelResponse",
    "HostelRoomResponse",
    "BedReservationRequest",
    "BedReservationResponse",
]