"""
Subject schemas for API validation with bilingual support.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import re


class SubjectType(str, Enum):
    """Subject type enumeration."""
    OBLIGATOIRE = "obligatoire"      # Mandatory subjects
    OPTIONNELLE = "optionnelle"      # Optional subjects
    SPECIALISEE = "specialisee"      # Specialized subjects
    ACADEMIC = "academic"            # Keep existing for compatibility
    SPORTS = "sports"
    ARTS = "arts"
    RELIGIOUS = "religious"
    LANGUAGE = "language"
    SCIENCE_LAB = "science_lab"


class SubjectBase(BaseModel):
    """Base subject schema with bilingual support."""
    code: str = Field(..., min_length=1, max_length=20, description="Unique alphanumeric code")
    nom_fr: str = Field(..., min_length=1, max_length=255, description="French name (required)")
    nom_he: str = Field(..., min_length=1, max_length=255, description="Hebrew name (required)")
    niveau_requis: str = Field(..., min_length=1, max_length=50, description="Required level (e.g., '6ème', '5ème')")
    heures_semaine: int = Field(..., ge=1, le=40, description="Hours per week (1-40)")
    type_matiere: SubjectType = Field(default=SubjectType.OBLIGATOIRE, description="Subject type")
    description_fr: Optional[str] = Field(None, description="French description")
    description_he: Optional[str] = Field(None, description="Hebrew description")
    
    # Legacy compatibility fields
    requires_lab: bool = False
    requires_special_room: bool = False
    requires_consecutive_hours: bool = False
    max_hours_per_day: int = Field(default=2, ge=1, le=8)
    is_religious: bool = False
    requires_gender_separation: bool = False

    @validator('code')
    def validate_code(cls, v):
        """Validate code is alphanumeric."""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Code must be alphanumeric (letters, numbers, underscore, hyphen only)')
        return v.upper()

    @validator('nom_fr', 'nom_he')
    def validate_names_not_empty(cls, v):
        """Ensure names are not empty after stripping."""
        if not v or not v.strip():
            raise ValueError('Names cannot be empty')
        return v.strip()

    @validator('heures_semaine')
    def validate_heures_semaine(cls, v):
        """Validate hours per week is coherent."""
        if v <= 0:
            raise ValueError('Hours per week must be greater than 0')
        if v > 40:
            raise ValueError('Hours per week cannot exceed 40')
        return v


class SubjectCreate(SubjectBase):
    """Schema for subject creation."""
    pass


class SubjectUpdate(BaseModel):
    """Schema for subject update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    nom_fr: Optional[str] = Field(None, min_length=1, max_length=255)
    nom_he: Optional[str] = Field(None, min_length=1, max_length=255)
    niveau_requis: Optional[str] = Field(None, min_length=1, max_length=50)
    heures_semaine: Optional[int] = Field(None, ge=1, le=40)
    type_matiere: Optional[SubjectType] = None
    description_fr: Optional[str] = None
    description_he: Optional[str] = None
    requires_lab: Optional[bool] = None
    requires_special_room: Optional[bool] = None
    requires_consecutive_hours: Optional[bool] = None
    max_hours_per_day: Optional[int] = Field(None, ge=1, le=8)
    is_religious: Optional[bool] = None
    requires_gender_separation: Optional[bool] = None

    @validator('code')
    def validate_code(cls, v):
        """Validate code is alphanumeric."""
        if v is not None:
            if not re.match(r'^[A-Za-z0-9_-]+$', v):
                raise ValueError('Code must be alphanumeric (letters, numbers, underscore, hyphen only)')
            return v.upper()
        return v

    @validator('nom_fr', 'nom_he')
    def validate_names_not_empty(cls, v):
        """Ensure names are not empty after stripping."""
        if v is not None:
            if not v.strip():
                raise ValueError('Names cannot be empty')
            return v.strip()
        return v


class SubjectInDB(SubjectBase):
    """Schema for subject in database."""
    id: int
    
    # Legacy fields for compatibility
    name_fr: Optional[str] = None
    name_he: Optional[str] = None
    subject_type: Optional[SubjectType] = None
    
    class Config:
        from_attributes = True


class Subject(SubjectInDB):
    """Schema for subject response."""
    pass


class SubjectWithTeachers(Subject):
    """Subject schema with assigned teachers."""
    teachers: List['TeacherBasic'] = []
    
    class Config:
        from_attributes = True


class SubjectBasic(BaseModel):
    """Basic subject info for nested responses."""
    id: int
    code: str
    nom_fr: str
    nom_he: str
    type_matiere: SubjectType
    heures_semaine: int
    niveau_requis: str
    
    class Config:
        from_attributes = True


class SubjectSearch(BaseModel):
    """Schema for subject search results."""
    subjects: List[Subject]
    total: int
    page: int
    per_page: int
    total_pages: int


# For circular import resolution
from app.schemas.teacher import TeacherBasic
SubjectWithTeachers.model_rebuild() 