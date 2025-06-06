"""
Teacher schemas for API validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import time


class TeacherBase(BaseModel):
    """Base teacher schema."""
    code: str = Field(..., min_length=1, max_length=20)
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    max_hours_per_week: int = Field(default=30, ge=1, le=50)
    max_hours_per_day: int = Field(default=8, ge=1, le=12)
    prefers_consecutive_hours: bool = True
    is_active: bool = True
    primary_language: str = Field(default="he", pattern="^(he|fr)$")
    can_teach_in_french: bool = False
    can_teach_in_hebrew: bool = True


class TeacherCreate(TeacherBase):
    """Schema for teacher creation."""
    subject_ids: List[int] = []


class TeacherUpdate(BaseModel):
    """Schema for teacher update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    max_hours_per_week: Optional[int] = Field(None, ge=1, le=50)
    max_hours_per_day: Optional[int] = Field(None, ge=1, le=12)
    prefers_consecutive_hours: Optional[bool] = None
    is_active: Optional[bool] = None
    primary_language: Optional[str] = Field(None, pattern="^(he|fr)$")
    can_teach_in_french: Optional[bool] = None
    can_teach_in_hebrew: Optional[bool] = None
    subject_ids: Optional[List[int]] = None


class TeacherInDB(TeacherBase):
    """Schema for teacher in database."""
    id: int
    
    class Config:
        from_attributes = True


class Teacher(TeacherInDB):
    """Schema for teacher response."""
    subjects: List["SubjectBasic"] = []
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class TeacherAvailabilityBase(BaseModel):
    """Base schema for teacher availability."""
    teacher_id: int
    day_of_week: int = Field(..., ge=0, le=5)  # 0-5 (Sunday-Friday)
    start_time: time
    end_time: time
    is_available: bool = True


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    """Schema for creating teacher availability."""
    pass


class TeacherAvailability(TeacherAvailabilityBase):
    """Schema for teacher availability response."""
    id: int
    
    class Config:
        from_attributes = True


class TeacherPreferenceBase(BaseModel):
    """Base schema for teacher preferences."""
    teacher_id: int
    preference_type: str
    parameters: dict = {}
    weight: int = Field(default=1, ge=1, le=10)


class TeacherPreferenceCreate(TeacherPreferenceBase):
    """Schema for creating teacher preference."""
    pass


class TeacherPreference(TeacherPreferenceBase):
    """Schema for teacher preference response."""
    id: int
    
    class Config:
        from_attributes = True


class TeacherBasic(BaseModel):
    """Basic teacher info for nested responses."""
    id: int
    code: str
    first_name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True


# Import at the end to avoid circular imports
from app.schemas.subject import SubjectBasic
Teacher.model_rebuild() 