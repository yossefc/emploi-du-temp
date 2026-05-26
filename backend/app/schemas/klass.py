"""Pydantic schemas pour Class."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClassBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    student_count: int = Field(default=0, ge=0)
    homeroom_teacher_id: Optional[int] = None


class ClassCreate(ClassBase):
    school_id: int
    grade_id: int


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    student_count: Optional[int] = Field(None, ge=0)
    homeroom_teacher_id: Optional[int] = None


class ClassRead(ClassBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    grade_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
