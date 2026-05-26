"""Pydantic schemas pour TimeSlot + grille horaire."""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimeSlotBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Dim, 1=Lun, ..., 6=Sam")
    slot_index: int = Field(..., ge=0)
    start_time: time
    end_time: time
    is_break: bool = False
    is_active: bool = True
    label: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def _start_before_end(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time doit être avant end_time")
        return self


class TimeSlotCreate(TimeSlotBase):
    school_id: int


class TimeSlotUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_break: Optional[bool] = None
    is_active: Optional[bool] = None
    label: Optional[str] = Field(None, max_length=100)


class TimeSlotRead(TimeSlotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int


class TimeGridReplace(BaseModel):
    """Body pour remplacer toute la grille d'une école (POST /schools/{id}/time-grid)."""
    slots: list[TimeSlotBase]
