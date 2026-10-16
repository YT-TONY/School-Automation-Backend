from contextvars import ContextVar
from typing import Optional
import uuid

# Request-scoped ContextVar for active school tenant
_tenant_school_id: ContextVar[Optional[uuid.UUID]] = ContextVar("tenant_school_id", default=None)

def set_current_tenant(school_id: Optional[uuid.UUID]) -> None:
    _tenant_school_id.set(school_id)

def get_current_tenant() -> Optional[uuid.UUID]:
    return _tenant_school_id.get()