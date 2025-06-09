"""
Class group schemas for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
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
    """Base class group schema with enhanced fields."""
    code: str = Field(..., min_length=1, max_length=20, description="Unique class code")
    nom: str = Field(..., min_length=1, max_length=255, description="Class name")
    niveau: str = Field(..., min_length=1, max_length=50, description="Class level (e.g., '6ème', '5ème')")
    effectif: int = Field(..., ge=1, le=50, description="Number of students")
    
    # Optional fields
    class_type: ClassType = ClassType.REGULAR
    description: Optional[str] = Field(None, description="Class description")
    academic_year: Optional[str] = Field(None, max_length=20, description="Academic year (e.g., '2024-2025')")
    
    # Schedule preferences (JSON structure)
    horaires_preferes: Optional[Dict[str, Any]] = Field(None, description="Preferred schedule slots")
    
    # Legacy compatibility fields
    name: Optional[str] = Field(None, description="Legacy name field")
    grade: Optional[Grade] = Field(None, description="Legacy grade field")
    student_count: Optional[int] = Field(None, ge=1, le=50, description="Legacy student count")
    
    # Settings
    is_boys_only: bool = False
    is_girls_only: bool = False
    is_mixed: bool = True
    primary_language: str = Field(default="he", pattern="^(he|fr)$")
    homeroom_teacher_id: Optional[int] = None
    is_active: bool = True

    @validator('code')
    def validate_code(cls, v):
        """Validate class code format."""
        if not v or not v.strip():
            raise ValueError('Class code cannot be empty')
        return v.strip().upper()
    
    @validator('effectif', 'student_count')
    def validate_student_count(cls, v):
        """Validate student count is reasonable."""
        if v is not None and (v < 1 or v > 50):
            raise ValueError('Student count must be between 1 and 50')
        return v


class ClassGroupCreate(ClassGroupBase):
    """Schema for class group creation."""
    # Subject IDs to assign as mandatory subjects
    subject_ids: Optional[List[int]] = Field(None, description="List of mandatory subject IDs")


class ClassGroupUpdate(BaseModel):
    """Schema for class group update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    nom: Optional[str] = Field(None, min_length=1, max_length=255)
    niveau: Optional[str] = Field(None, min_length=1, max_length=50)
    effectif: Optional[int] = Field(None, ge=1, le=50)
    class_type: Optional[ClassType] = None
    description: Optional[str] = None
    academic_year: Optional[str] = Field(None, max_length=20)
    horaires_preferes: Optional[Dict[str, Any]] = None
    is_boys_only: Optional[bool] = None
    is_girls_only: Optional[bool] = None
    is_mixed: Optional[bool] = None
    primary_language: Optional[str] = Field(None, pattern="^(he|fr)$")
    homeroom_teacher_id: Optional[int] = None
    is_active: Optional[bool] = None

    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Class code cannot be empty')
            return v.strip().upper()
        return v


class ClassGroupInDB(ClassGroupBase):
    """Schema for class group in database."""
    id: int
    
    class Config:
        from_attributes = True


class ClassGroupWithSubjects(ClassGroupInDB):
    """Class group schema with assigned subjects."""
    matieres_obligatoires: List['SubjectBasic'] = []
    homeroom_teacher: Optional['TeacherBasic'] = None
    
    class Config:
        from_attributes = True


class ClassGroup(ClassGroupInDB):
    """Schema for class group response."""
    pass


class ClassGroupBasic(BaseModel):
    """Basic class group info for nested responses."""
    id: int
    code: str
    nom: str
    niveau: str
    effectif: int
    class_type: ClassType
    
    class Config:
        from_attributes = True


class ClassSubjectAssignment(BaseModel):
    """Schema for assigning subjects to a class."""
    subject_ids: List[int] = Field(..., min_items=1, description="List of subject IDs to assign")
    
    @validator('subject_ids')
    def validate_subject_ids(cls, v):
        if not v:
            raise ValueError('At least one subject ID must be provided')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate subject IDs are not allowed')
        return v


# Legacy schemas for compatibility
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
ClassGroupWithSubjects.model_rebuild() 