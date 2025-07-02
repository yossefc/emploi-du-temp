"""
Schedule schemas for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, time
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
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Schedule name",
        examples=["Emploi du temps Septembre 2024", "Horaire Semestre 1"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Schedule description",
        examples=["Emploi du temps principal pour le premier semestre"]
    )
    academic_year: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{4}$",
        description="Academic year in format YYYY-YYYY",
        examples=["2024-2025", "2023-2024"]
    )
    semester: Optional[int] = Field(
        None, 
        ge=1, 
        le=2,
        description="Semester number (1 or 2)",
        examples=[1, 2]
    )
    status: ScheduleStatus = Field(
        default=ScheduleStatus.DRAFT,
        description="Schedule status"
    )
    is_active: bool = Field(
        default=False,
        description="Whether this schedule is currently active"
    )

    @validator('academic_year')
    def validate_academic_year(cls, v):
        """Validate academic year format."""
        if v is None:
            return v
        try:
            start_year, end_year = v.split('-')
            if int(end_year) != int(start_year) + 1:
                raise ValueError('End year must be exactly one year after start year')
        except (ValueError, AttributeError):
            raise ValueError('Academic year must be in format YYYY-YYYY with consecutive years')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Emploi du temps Septembre 2024",
                "description": "Emploi du temps principal pour le premier semestre",
                "academic_year": "2024-2025",
                "semester": 1,
                "status": "draft",
                "is_active": False
            }
        }


class ScheduleCreate(ScheduleBase):
    """Schema for schedule creation."""
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Emploi du temps Septembre 2024",
                "description": "Emploi du temps principal pour le premier semestre",
                "academic_year": "2024-2025",
                "semester": 1,
                "status": "draft",
                "is_active": False
            }
        }


class ScheduleUpdate(BaseModel):
    """Schema for schedule update."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Schedule name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Schedule description"
    )
    academic_year: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{4}$",
        description="Academic year in format YYYY-YYYY"
    )
    semester: Optional[int] = Field(
        None, 
        ge=1, 
        le=2,
        description="Semester number (1 or 2)"
    )
    status: Optional[ScheduleStatus] = Field(
        None,
        description="Schedule status"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether this schedule is currently active"
    )

    @validator('academic_year')
    def validate_academic_year(cls, v):
        """Validate academic year format."""
        if v is None:
            return v
        try:
            start_year, end_year = v.split('-')
            if int(end_year) != int(start_year) + 1:
                raise ValueError('End year must be exactly one year after start year')
        except (ValueError, AttributeError):
            raise ValueError('Academic year must be in format YYYY-YYYY with consecutive years')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Emploi du temps Octobre 2024",
                "status": "active",
                "is_active": True
            }
        }


class ScheduleResponse(ScheduleBase):
    """Schema for schedule response."""
    id: int = Field(description="Schedule unique identifier")
    generation_time_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="Time taken to generate schedule in seconds"
    )
    solver_status: Optional[str] = Field(
        None,
        description="Status from the constraint solver"
    )
    objective_value: Optional[float] = Field(
        None,
        description="Optimization objective value"
    )
    conflicts_json: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="JSON representation of conflicts"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Schedule version number"
    )
    parent_schedule_id: Optional[int] = Field(
        None,
        description="ID of parent schedule if this is a modification"
    )
    ai_modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="AI-suggested modifications"
    )
    manual_modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Manual modifications made"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp"
    )
    created_by_id: Optional[int] = Field(
        None,
        description="ID of user who created the schedule"
    )
    entries: List["ScheduleEntryResponse"] = Field(
        default=[],
        description="List of schedule entries"
    )
    conflicts: List["ScheduleConflict"] = Field(
        default=[],
        description="List of scheduling conflicts"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Emploi du temps Septembre 2024",
                "description": "Emploi du temps principal pour le premier semestre",
                "academic_year": "2024-2025",
                "semester": 1,
                "status": "active",
                "is_active": True,
                "generation_time_seconds": 45.2,
                "solver_status": "optimal",
                "objective_value": 0.95,
                "version": 1,
                "created_at": "2024-09-01T08:00:00Z",
                "updated_at": "2024-09-01T08:45:00Z",
                "entries": [],
                "conflicts": []
            }
        }


class ScheduleEntryBase(BaseModel):
    """Base schedule entry schema."""
    schedule_id: int = Field(description="Schedule ID")
    day_of_week: int = Field(
        ..., 
        ge=0, 
        le=5,
        description="Day of week (0=Sunday, 5=Friday)",
        examples=[0, 1, 2, 3, 4, 5]
    )
    period: int = Field(
        ..., 
        ge=0, 
        le=9,
        description="Period number (0-9)",
        examples=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    )
    class_group_id: int = Field(description="Class group ID")
    subject_id: int = Field(description="Subject ID")
    teacher_id: int = Field(description="Teacher ID")
    room_id: int = Field(description="Room ID")
    is_double_period: bool = Field(
        default=False,
        description="Whether this is a double period"
    )
    notes: Optional[str] = Field(
        None,
        max_length=200,
        description="Additional notes for this entry"
    )
    is_locked: bool = Field(
        default=False,
        description="Whether this entry is locked from modifications"
    )
    modified_by_ai: bool = Field(
        default=False,
        description="Whether this entry was modified by AI"
    )
    modification_reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Reason for modification"
    )

    @validator('period')
    def validate_period_range(cls, v):
        """Validate period number."""
        if v < 0 or v > 9:
            raise ValueError('Period must be between 0 and 9')
        return v

    class Config:
        from_attributes = True


class ScheduleEntryCreate(ScheduleEntryBase):
    """Schema for creating schedule entry."""
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "schedule_id": 1,
                "day_of_week": 1,
                "period": 2,
                "class_group_id": 1,
                "subject_id": 1,
                "teacher_id": 1,
                "room_id": 1,
                "is_double_period": False,
                "notes": "Cours de révision",
                "is_locked": False
            }
        }


class ScheduleEntryUpdate(BaseModel):
    """Schema for updating schedule entry."""
    day_of_week: Optional[int] = Field(
        None, 
        ge=0, 
        le=5,
        description="Day of week (0=Sunday, 5=Friday)"
    )
    period: Optional[int] = Field(
        None, 
        ge=0, 
        le=9,
        description="Period number (0-9)"
    )
    teacher_id: Optional[int] = Field(
        None,
        description="Teacher ID"
    )
    room_id: Optional[int] = Field(
        None,
        description="Room ID"
    )
    notes: Optional[str] = Field(
        None,
        max_length=200,
        description="Additional notes"
    )
    is_locked: Optional[bool] = Field(
        None,
        description="Whether entry is locked"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "teacher_id": 2,
                "room_id": 3,
                "notes": "Changement de salle",
                "is_locked": True
            }
        }


class ScheduleEntryResponse(ScheduleEntryBase):
    """Schema for schedule entry response."""
    id: int = Field(description="Entry unique identifier")
    class_group: "ClassGroupBasic" = Field(description="Class group information")
    subject: "SubjectBasic" = Field(description="Subject information")
    teacher: "TeacherBasic" = Field(description="Teacher information")
    room: "RoomBasic" = Field(description="Room information")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "schedule_id": 1,
                "day_of_week": 1,
                "period": 2,
                "class_group_id": 1,
                "subject_id": 1,
                "teacher_id": 1,
                "room_id": 1,
                "is_double_period": False,
                "notes": "Cours de révision",
                "is_locked": False,
                "modified_by_ai": False,
                "class_group": {
                    "id": 1,
                    "code": "6A",
                    "name": "Sixième A"
                },
                "subject": {
                    "id": 1,
                    "code": "MATH",
                    "name_he": "מתמטיקה",
                    "name_fr": "Mathématiques"
                },
                "teacher": {
                    "id": 1,
                    "code": "T001",
                    "first_name": "Jean",
                    "last_name": "Dupont"
                },
                "room": {
                    "id": 1,
                    "code": "S101",
                    "name": "Salle 101"
                }
            }
        }


class ScheduleConflictBase(BaseModel):
    """Base schedule conflict schema."""
    schedule_id: int = Field(description="Schedule ID")
    conflict_type: str = Field(
        description="Type of conflict",
        examples=["teacher_overlap", "room_overlap", "constraint_violation"]
    )
    severity: str = Field(
        default="error",
        pattern="^(error|warning|info)$",
        description="Conflict severity level",
        examples=["error", "warning", "info"]
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable conflict description"
    )
    involved_entries: List[int] = Field(
        default=[],
        description="List of entry IDs involved in the conflict"
    )
    constraint_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional constraint details"
    )
    resolution_suggestions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Suggested resolutions for the conflict"
    )

    class Config:
        from_attributes = True


class ScheduleConflict(ScheduleConflictBase):
    """Schema for schedule conflict response."""
    id: int = Field(description="Conflict unique identifier")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "schedule_id": 1,
                "conflict_type": "teacher_overlap",
                "severity": "error",
                "description": "Le professeur T001 est assigné à deux cours simultanément",
                "involved_entries": [1, 2],
                "constraint_details": {
                    "teacher_id": 1,
                    "overlapping_periods": ["Monday-2", "Monday-2"]
                },
                "resolution_suggestions": [
                    {
                        "type": "change_teacher",
                        "suggestion": "Assigner un autre professeur à l'un des cours"
                    }
                ]
            }
        }


class GenerateScheduleRequest(BaseModel):
    """Request schema for schedule generation."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name for the generated schedule",
        examples=["Emploi du temps automatique", "Génération Septembre 2024"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the schedule to generate"
    )
    academic_year: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{4}$",
        description="Academic year in format YYYY-YYYY",
        examples=["2024-2025"]
    )
    semester: Optional[int] = Field(
        None, 
        ge=1, 
        le=2,
        description="Semester number (1 or 2)",
        examples=[1, 2]
    )
    time_limit_seconds: Optional[int] = Field(
        None, 
        ge=10, 
        le=600,
        description="Maximum time to spend generating the schedule",
        examples=[60, 120, 300]
    )

    @validator('academic_year')
    def validate_academic_year(cls, v):
        """Validate academic year format."""
        if v is None:
            return v
        try:
            start_year, end_year = v.split('-')
            if int(end_year) != int(start_year) + 1:
                raise ValueError('End year must be exactly one year after start year')
        except (ValueError, AttributeError):
            raise ValueError('Academic year must be in format YYYY-YYYY with consecutive years')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Emploi du temps automatique Septembre 2024",
                "description": "Génération automatique pour le premier semestre",
                "academic_year": "2024-2025",
                "semester": 1,
                "time_limit_seconds": 120
            }
        }


class GenerateScheduleResponse(BaseModel):
    """Response schema for schedule generation."""
    schedule_id: int = Field(description="ID of the generated schedule")
    status: SolverStatus = Field(description="Generation status")
    generation_time: float = Field(
        ge=0,
        description="Time taken to generate in seconds"
    )
    objective_value: Optional[float] = Field(
        None,
        description="Optimization objective value achieved"
    )
    entries_count: int = Field(
        ge=0,
        description="Number of schedule entries created"
    )
    conflicts_count: int = Field(
        ge=0,
        description="Number of conflicts found"
    )
    message: str = Field(
        description="Human-readable result message"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "schedule_id": 1,
                    "status": "optimal",
                    "generation_time": 45.2,
                    "objective_value": 0.95,
                    "entries_count": 120,
                    "conflicts_count": 0,
                    "message": "Emploi du temps généré avec succès sans conflit"
                },
                {
                    "schedule_id": 2,
                    "status": "feasible",
                    "generation_time": 120.0,
                    "objective_value": 0.82,
                    "entries_count": 115,
                    "conflicts_count": 3,
                    "message": "Emploi du temps généré avec quelques conflits mineurs"
                }
            ]
        }


# Basic schemas for nested responses
class ClassGroupBasic(BaseModel):
    """Basic class group info."""
    id: int = Field(description="Class group unique identifier")
    code: str = Field(description="Class group code")
    name: str = Field(description="Class group name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "6A",
                "name": "Sixième A"
            }
        }


class SubjectBasic(BaseModel):
    """Basic subject info."""
    id: int = Field(description="Subject unique identifier")
    code: str = Field(description="Subject code")
    name_he: str = Field(description="Subject name in Hebrew")
    name_fr: str = Field(description="Subject name in French")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "MATH",
                "name_he": "מתמטיקה",
                "name_fr": "Mathématiques"
            }
        }


class TeacherBasic(BaseModel):
    """Basic teacher info."""
    id: int = Field(description="Teacher unique identifier")
    code: str = Field(description="Teacher code")
    first_name: str = Field(description="Teacher's first name")
    last_name: str = Field(description="Teacher's last name")
    
    @property
    def full_name(self) -> str:
        """Get teacher's full name."""
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "T001",
                "first_name": "Jean",
                "last_name": "Dupont"
            }
        }


class RoomBasic(BaseModel):
    """Basic room info."""
    id: int = Field(description="Room unique identifier")
    code: str = Field(description="Room code")
    name: str = Field(description="Room name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "S101",
                "name": "Salle 101"
            }
        }


# Rebuild models to handle forward references
ScheduleEntryResponse.model_rebuild()
ScheduleResponse.model_rebuild() 