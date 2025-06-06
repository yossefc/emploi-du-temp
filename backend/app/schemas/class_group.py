"""
Class group schemas for API validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Grade(str, Enum):
    """Grade levels enumeration."""
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


class ClassType(str, Enum):
    """Class type enumeration."""
    REGULAR = "regular"
    ADVANCED = "advanced"
    SPECIAL_NEEDS = "special_needs"


class ClassGroupBase(BaseModel):
    """Base class group schema."""
    code: str = Field(..., min_length=1, max_length=10)  # e.g., "9A", "10B"
    name: str
    grade: Grade
    class_type: ClassType = ClassType.REGULAR
    student_count: int = Field(..., ge=1, le=50)
    is_boys_only: bool = False
    is_girls_only: bool = False
    is_mixed: bool = True
    primary_language: str = Field(default="he", pattern="^(he|fr)$")
    homeroom_teacher_id: Optional[int] = None


class ClassGroupCreate(ClassGroupBase):
    """Schema for class group creation."""
    pass


class ClassGroupUpdate(BaseModel):
    """Schema for class group update."""
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = None
    grade: Optional[Grade] = None
    class_type: Optional[ClassType] = None
    student_count: Optional[int] = Field(None, ge=1, le=50)
    is_boys_only: Optional[bool] = None
    is_girls_only: Optional[bool] = None
    is_mixed: Optional[bool] = None
    primary_language: Optional[str] = Field(None, pattern="^(he|fr)$")
    homeroom_teacher_id: Optional[int] = None


class ClassGroupInDB(ClassGroupBase):
    """Schema for class group in database."""
    id: int
    
    class Config:
        from_attributes = True


class ClassGroup(ClassGroupInDB):
    """Schema for class group response."""
    subject_requirements: List["ClassSubjectRequirement"] = []


class ClassSubjectRequirementBase(BaseModel):
    """Base schema for class subject requirements."""
    class_group_id: int
    subject_id: int
    hours_per_week: int = Field(..., ge=1, le=10)
    preferred_teacher_id: Optional[int] = None
    requires_double_period: bool = False
    max_per_day: int = Field(default=2, ge=1, le=4)
    min_days_between: int = Field(default=0, ge=0, le=3)


class ClassSubjectRequirementCreate(ClassSubjectRequirementBase):
    """Schema for creating class subject requirement."""
    pass


class ClassSubjectRequirementUpdate(BaseModel):
    """Schema for updating class subject requirement."""
    hours_per_week: Optional[int] = Field(None, ge=1, le=10)
    preferred_teacher_id: Optional[int] = None
    requires_double_period: Optional[bool] = None
    max_per_day: Optional[int] = Field(None, ge=1, le=4)
    min_days_between: Optional[int] = Field(None, ge=0, le=3)


class ClassSubjectRequirement(ClassSubjectRequirementBase):
    """Schema for class subject requirement response."""
    id: int
    subject: "SubjectBasic"
    preferred_teacher: Optional["TeacherBasic"] = None
    
    class Config:
        from_attributes = True


# Import at the end to avoid circular imports
from app.schemas.subject import SubjectBasic
from app.schemas.teacher import TeacherBasic

ClassSubjectRequirement.model_rebuild()
ClassGroup.model_rebuild() 