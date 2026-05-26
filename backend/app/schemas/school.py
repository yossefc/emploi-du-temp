"""Pydantic schemas pour School."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SchoolBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    timezone: str = Field(default="Asia/Jerusalem", max_length=50)
    default_language: str = Field(default="fr", max_length=5)
    is_active: bool = True


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    default_language: Optional[str] = Field(None, max_length=5)
    is_active: Optional[bool] = None


class SchoolRead(SchoolBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
