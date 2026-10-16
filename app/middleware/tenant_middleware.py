#app/middleware/tenant_middleware.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.tenant import set_current_tenant

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Parse direct UUID header if supplied
        tenant_header = request.headers.get("X-Tenant-ID")
        school_id = None
        if tenant_header:
            try:
                school_id = uuid.UUID(tenant_header)
            except ValueError:
                pass

        # 2. Extract domain/subdomain from HTTP Host header
        raw_host = request.headers.get("X-Tenant-Domain") or request.headers.get("host", "")
        domain = raw_host.split(":")[0].lower()

        subdomain = request.headers.get("X-Tenant-Subdomain")
        if not subdomain:
            if "localhost" in domain or "127.0.0.1" in domain:
                subdomain = "default"
            else:
                parts = domain.split(".")
                subdomain = parts[0] if len(parts) > 2 else domain

        # 3. Bind to Request State & ContextVars
        request.state.school_id = school_id
        request.state.tenant_domain = domain
        request.state.tenant_subdomain = subdomain

        set_current_tenant(
            school_id=school_id,
            subdomain=subdomain,
            domain=domain
        )

        response = await call_next(request)
        return response