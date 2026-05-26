"""Routeur principal de l'API v2."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import constraints, schedules

api_router = APIRouter()

api_router.include_router(constraints.router, prefix="/constraints", tags=["constraints"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
