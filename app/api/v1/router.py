#app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1.endpoints import schools, auth, students, results, pins

api_router = APIRouter()

api_router.include_router(schools.router, prefix="/schools", tags=["Schools"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(results.router, prefix="/results", tags=["Result Engine"])
api_router.include_router(pins.router, prefix="/pins", tags=["Scratch PIN Engine"])