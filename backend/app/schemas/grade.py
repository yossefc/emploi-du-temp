"""Pydantic schemas pour Grade (שכבה)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import GroupingPolicy


class GradeBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    order: int = Field(..., ge=0, le=20)
    grouping_policy: GroupingPolicy = GroupingPolicy.CLASS_CENTRIC


class GradeCreate(GradeBase):
    school_id: int


class GradeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    order: Optional[int] = Field(None, ge=0, le=20)
    grouping_policy: Optional[GroupingPolicy] = None


class GradeRead(GradeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
