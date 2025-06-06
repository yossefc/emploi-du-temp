"""
Teacher management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.teacher import Teacher as TeacherSchema

router = APIRouter()


@router.get("/", response_model=List[TeacherSchema])
async def get_teachers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all teachers."""
    # Implementation would query Teacher model
    return [] 