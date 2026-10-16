import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.tenant import set_current_tenant

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract tenant via custom header or subdomain parsing
        tenant_header = request.headers.get("X-Tenant-ID")
        school_id = None

        if tenant_header:
            try:
                school_id = uuid.UUID(tenant_header)
            except ValueError:
                pass

        # Set request context
        set_current_tenant(school_id)

        response = await call_next(request)
        return response