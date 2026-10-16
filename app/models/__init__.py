# app/models/__init__.py

from app.core.database import Base
from app.models.school import School
from app.models.user import User, UserRole
from app.models.academic import ClassArm, Subject
from app.models.student import Student, StudentStatus
from app.models.result import Result, ResultStatus
from app.models.pin import ResultPin

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
]