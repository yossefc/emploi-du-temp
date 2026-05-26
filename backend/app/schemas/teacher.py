"""Pydantic schemas pour Teacher."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeacherBase(BaseModel):
    code: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    max_hours_per_week: Optional[int] = Field(None, ge=1, le=60)
    max_hours_per_day: Optional[int] = Field(None, ge=1, le=12)
    languages: list[str] = Field(default_factory=lambda: ["fr", "he"])
    is_active: bool = True


class TeacherCreate(TeacherBase):
    school_id: int
    qualified_subject_ids: list[int] = Field(default_factory=list)


class TeacherUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    max_hours_per_week: Optional[int] = Field(None, ge=1, le=60)
    max_hours_per_day: Optional[int] = Field(None, ge=1, le=12)
    languages: Optional[list[str]] = None
    is_active: Optional[bool] = None
    qualified_subject_ids: Optional[list[int]] = None


class TeacherRead(TeacherBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    qualified_subject_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
