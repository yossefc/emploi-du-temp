"""Routeur principal de l'API v2."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    classes,
    constraints,
    grades,
    groups,
    rooms,
    schedules,
    schools,
    subjects,
    teachers,
)

api_router = APIRouter()

# CRUD entités de configuration école
api_router.include_router(schools.router, prefix="/schools", tags=["schools"])
api_router.include_router(grades.router, prefix="/grades", tags=["grades"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])

# Groups + cohorts (le routeur définit lui-même /groups et /cohorts)
api_router.include_router(groups.router, prefix="")

# Génération + dialogue
api_router.include_router(constraints.router, prefix="/constraints", tags=["constraints"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
