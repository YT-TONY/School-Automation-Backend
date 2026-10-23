# app/models/__init__.py

from app.core.database import Base
from app.models.school import School
from app.models.user import User, UserRole
from app.models.academic import ClassArm, Subject
from app.models.student import Student, StudentStatus
from app.models.result import Result, ResultStatus
from app.models.pin import ResultPin
from app.models.teacher_assignment import TeacherAssignment
from app.models.fee import FeeItem, FeeType, StudentFeeSelection
from app.models.remark import TerminalRemark
from app.models.audit import ResultStatusAudit
from app.models.psychomotor import AffectivePsychomotorDomain
from app.models.hostel import Hostel, HostelRoom, BedAllocation, ReservationStatus
from app.models.grading import GradingScale
from app.models.payment import PaymentTransaction, PaymentReceipt, PaymentStatus, PaymentType

__all__ = [
    "Base",
    "School",
    "User",
    "UserRole",
    "ClassArm",
    "Subject",
    "Student",
    "StudentStatus",
    "Result",
    "ResultStatus",
    "ResultPin",
    "TeacherAssignment",
    "FeeItem",
    "FeeType",
    "StudentFeeSelection",
    "TerminalRemark",
    "ResultStatusAudit",
    "AffectivePsychomotorDomain",
    "Hostel",
    "HostelRoom",
    "BedAllocation",
    "ReservationStatus",
    "GradingScale",
    "PaymentTransaction",
    "PaymentReceipt",
    "PaymentStatus",
    "PaymentType",
]