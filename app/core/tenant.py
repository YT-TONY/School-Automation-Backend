#app/core/tenant.py

import uuid
from contextvars import ContextVar
from typing import Optional
from fastapi import HTTPException, status

_tenant_school_id: ContextVar[Optional[uuid.UUID]] = ContextVar("tenant_school_id", default=None)
_tenant_subdomain: ContextVar[Optional[str]] = ContextVar("tenant_subdomain", default=None)
_tenant_domain: ContextVar[Optional[str]] = ContextVar("tenant_domain", default=None)

def set_current_tenant(
    school_id: Optional[uuid.UUID] = None,
    subdomain: Optional[str] = None,
    domain: Optional[str] = None
) -> None:
    _tenant_school_id.set(school_id)
    _tenant_subdomain.set(subdomain)
    _tenant_domain.set(domain)

def get_current_tenant() -> Optional[uuid.UUID]:
    return _tenant_school_id.get()

def get_current_subdomain() -> Optional[str]:
    return _tenant_subdomain.get()

def get_current_domain() -> Optional[str]:
    return _tenant_domain.get()

def require_tenant_id() -> uuid.UUID:
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context missing. Provide a valid X-Tenant-ID header or access via a recognized school domain."
        )
    return tenant_id