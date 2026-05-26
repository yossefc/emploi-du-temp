"""Pydantic schemas pour Group + ParallelCohort."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import GroupType


# -- Group -----------------------------------------------------------------

class GroupBase(BaseModel):
    label: str = Field(..., max_length=200)
    group_type: GroupType = GroupType.WHOLE_CLASS
    hours_per_week: int = Field(..., ge=1, le=40)
    student_count: Optional[int] = Field(None, ge=0)
    parallel_cohort_id: Optional[int] = None


class GroupCreate(GroupBase):
    school_id: int
    grade_id: int
    subject_id: int
    teacher_ids: list[int] = Field(default_factory=list)
    source_class_ids: list[int] = Field(default_factory=list)


class GroupUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=200)
    group_type: Optional[GroupType] = None
    hours_per_week: Optional[int] = Field(None, ge=1, le=40)
    student_count: Optional[int] = Field(None, ge=0)
    parallel_cohort_id: Optional[int] = None
    teacher_ids: Optional[list[int]] = None
    source_class_ids: Optional[list[int]] = None


class GroupRead(GroupBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    grade_id: int
    subject_id: int
    teacher_ids: list[int] = Field(default_factory=list)
    source_class_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


# -- ParallelCohort --------------------------------------------------------

class ParallelCohortBase(BaseModel):
    label: str = Field(..., max_length=200)
    grade_id: Optional[int] = None


class ParallelCohortCreate(ParallelCohortBase):
    school_id: int


class ParallelCohortUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=200)
    grade_id: Optional[int] = None


class ParallelCohortRead(ParallelCohortBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    group_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
