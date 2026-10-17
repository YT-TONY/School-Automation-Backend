# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1.endpoints import schools, auth, users, academic, students, results, pins, admin_schools

api_router = APIRouter()

api_router.include_router(schools.router, prefix="/schools", tags=["Schools (Public Config)"])
api_router.include_router(admin_schools.router, prefix="/admin/schools", tags=["Super Admin Platform Management"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User & Staff Management"])
api_router.include_router(academic.router, prefix="/academic", tags=["Academic Setup"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(results.router, prefix="/results", tags=["Result Engine"])
api_router.include_router(pins.router, prefix="/pins", tags=["Scratch PIN Engine"])