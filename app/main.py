# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.tenant_middleware import TenantMiddleware
from app.api.v1.router import api_router

app = FastAPI(
    title="Multi-Tenant School Platform API",
    description="Backend API supporting dynamic white-label school portals and PIN result checking.",
    version="1.0.0"
)

# Configure CORS for multi-domain white-label support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows dynamic custom school domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach Tenant Resolution Middleware
app.add_middleware(TenantMiddleware)

# Attach Centralized V1 API Router (Includes /schools, /auth, /students, /results, /pins)
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "Multi-Tenant School Backend Engine",
        "version": "1.0.0"
    }