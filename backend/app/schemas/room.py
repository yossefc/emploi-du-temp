"""Pydantic schemas pour Room."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomBase(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=200)
    capacity: int = Field(default=30, ge=1)
    room_type: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[int] = None
    equipment: Optional[dict[str, Any]] = None
    is_active: bool = True


class RoomCreate(RoomBase):
    school_id: int


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    capacity: Optional[int] = Field(None, ge=1)
    room_type: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[int] = None
    equipment: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class RoomRead(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
