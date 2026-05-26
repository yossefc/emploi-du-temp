"""Pydantic schemas pour les contraintes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConstraintOriginRole, ConstraintPriority, ConstraintType


class ConstraintBase(BaseModel):
    constraint_type: ConstraintType
    priority: ConstraintPriority = ConstraintPriority.HARD
    weight: Optional[int] = Field(default=None, ge=1, le=100)
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    origin_role: ConstraintOriginRole = ConstraintOriginRole.SCHOOL_ADMIN
    origin_description: Optional[str] = None
    origin_raw_text: Optional[str] = None


class ConstraintCreate(ConstraintBase):
    school_id: int


class ConstraintUpdate(BaseModel):
    """Patch : tous les champs optionnels."""
    priority: Optional[ConstraintPriority] = None
    weight: Optional[int] = Field(default=None, ge=1, le=100)
    parameters: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    origin_description: Optional[str] = None


class ConstraintRead(ConstraintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    origin_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
