"""
Main API router for v1.
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    users,
    teachers,
    subjects,
    class_groups,
    rooms,
    schedules,
    ai,
    import_data
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(class_groups.router, prefix="/classes", tags=["classes"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(import_data.router, prefix="/import", tags=["import"]) 