"""
Schedule schemas for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ScheduleStatus(str, Enum):
    """Schedule status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SolverStatus(str, Enum):
    """Solver status enumeration."""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
    INVALID = "invalid"


class ScheduleBase(BaseModel):
    """Base schedule schema."""
    name: str
    description: Optional[str] = None
    academic_year: Optional[str] = None  # e.g., "2024-2025"
    semester: Optional[int] = Field(None, ge=1, le=2)
    status: ScheduleStatus = ScheduleStatus.DRAFT
    is_active: bool = False


class ScheduleCreate(ScheduleBase):
    """Schema for schedule creation."""
    pass


class ScheduleUpdate(BaseModel):
    """Schema for schedule update."""
    name: Optional[str] = None
    description: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=2)
    status: Optional[ScheduleStatus] = None
    is_active: Optional[bool] = None


class ScheduleInDB(ScheduleBase):
    """Schema for schedule in database."""
    id: int
    generation_time_seconds: Optional[float] = None
    solver_status: Optional[str] = None
    objective_value: Optional[float] = None
    conflicts_json: Optional[List[Dict[str, Any]]] = None
    version: int = 1
    parent_schedule_id: Optional[int] = None
    ai_modifications: Optional[Dict[str, Any]] = None
    manual_modifications: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class Schedule(ScheduleInDB):
    """Schema for schedule response."""
    entries: List["ScheduleEntry"] = []
    conflicts: List["ScheduleConflict"] = []


class ScheduleEntryBase(BaseModel):
    """Base schedule entry schema."""
    schedule_id: int
    day_of_week: int = Field(..., ge=0, le=5)  # 0-5 (Sunday-Friday)
    period: int = Field(..., ge=0, le=9)  # Period number (0-9)
    class_group_id: int
    subject_id: int
    teacher_id: int
    room_id: int
    is_double_period: bool = False
    notes: Optional[str] = None
    is_locked: bool = False
    modified_by_ai: bool = False
    modification_reason: Optional[str] = None


class ScheduleEntryCreate(ScheduleEntryBase):
    """Schema for creating schedule entry."""
    pass


class ScheduleEntryUpdate(BaseModel):
    """Schema for updating schedule entry."""
    day_of_week: Optional[int] = Field(None, ge=0, le=5)
    period: Optional[int] = Field(None, ge=0, le=9)
    teacher_id: Optional[int] = None
    room_id: Optional[int] = None
    notes: Optional[str] = None
    is_locked: Optional[bool] = None


class ScheduleEntry(ScheduleEntryBase):
    """Schema for schedule entry response."""
    id: int
    class_group: "ClassGroupBasic"
    subject: "SubjectBasic"
    teacher: "TeacherBasic"
    room: "RoomBasic"
    
    class Config:
        from_attributes = True


class ScheduleConflictBase(BaseModel):
    """Base schedule conflict schema."""
    schedule_id: int
    conflict_type: str  # teacher_overlap, room_overlap, constraint_violation
    severity: str = "error"  # error, warning, info
    description: str
    involved_entries: List[int] = []
    constraint_details: Optional[Dict[str, Any]] = None
    resolution_suggestions: Optional[List[Dict[str, Any]]] = None


class ScheduleConflict(ScheduleConflictBase):
    """Schema for schedule conflict response."""
    id: int
    
    class Config:
        from_attributes = True


class GenerateScheduleRequest(BaseModel):
    """Request schema for schedule generation."""
    name: str
    description: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=2)
    time_limit_seconds: Optional[int] = Field(None, ge=10, le=600)


class GenerateScheduleResponse(BaseModel):
    """Response schema for schedule generation."""
    schedule_id: int
    status: SolverStatus
    generation_time: float
    objective_value: Optional[float] = None
    entries_count: int
    conflicts_count: int
    message: str


# Basic schemas for nested responses
class ClassGroupBasic(BaseModel):
    """Basic class group info."""
    id: int
    code: str
    name: str
    
    class Config:
        from_attributes = True


class SubjectBasic(BaseModel):
    """Basic subject info."""
    id: int
    code: str
    name_he: str
    name_fr: str
    
    class Config:
        from_attributes = True


class TeacherBasic(BaseModel):
    """Basic teacher info."""
    id: int
    code: str
    first_name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True


class RoomBasic(BaseModel):
    """Basic room info."""
    id: int
    code: str
    name: str
    
    class Config:
        from_attributes = True


# Rebuild models to handle forward references
ScheduleEntry.model_rebuild()
Schedule.model_rebuild() 