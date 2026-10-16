#app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.tenant_middleware import TenantMiddleware
from app.api.v1.endpoints import schools, auth

app = FastAPI(title="Multi-Tenant School Platform API")

# Configure CORS for multi-domain support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows dynamic custom school domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach Tenant Resolution Middleware
app.add_middleware(TenantMiddleware)

# Include Routers
app.add_prefix = "/api/v1"
app.include_router(schools.router, prefix="/api/v1/schools", tags=["Schools"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {"status": "online", "system": "Multi-Tenant School Backend"}