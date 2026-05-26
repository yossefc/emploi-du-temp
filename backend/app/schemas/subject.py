"""Pydantic schemas pour Subject."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubjectBase(BaseModel):
    code: str = Field(..., max_length=30)
    name_fr: str = Field(..., max_length=200)
    name_he: str = Field(..., max_length=200)
    abbreviation: Optional[str] = Field(None, max_length=15)
    color_hex: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    required_room_type: Optional[str] = Field(None, max_length=50)
    is_religious: bool = False
    is_active: bool = True


class SubjectCreate(SubjectBase):
    school_id: int


class SubjectUpdate(BaseModel):
    name_fr: Optional[str] = Field(None, max_length=200)
    name_he: Optional[str] = Field(None, max_length=200)
    abbreviation: Optional[str] = Field(None, max_length=15)
    color_hex: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    required_room_type: Optional[str] = Field(None, max_length=50)
    is_religious: Optional[bool] = None
    is_active: Optional[bool] = None


class SubjectRead(SubjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
