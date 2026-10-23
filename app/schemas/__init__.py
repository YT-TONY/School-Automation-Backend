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
    ClassArmUpdate,
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
from app.schemas.grading import (
    GradingScaleCreate,
    GradingScaleUpdate,
    GradingScaleResponse,
)
from app.schemas.audit import ResultStatusAuditResponse
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentReceiptResponse,
    TransactionStatusResponse,
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
    "ClassArmUpdate",
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
    "GradingScaleCreate",
    "GradingScaleUpdate",
    "GradingScaleResponse",
    "ResultStatusAuditResponse",
    "PaymentInitializeRequest",
    "PaymentInitializeResponse",
    "PaymentReceiptResponse",
    "TransactionStatusResponse",
]