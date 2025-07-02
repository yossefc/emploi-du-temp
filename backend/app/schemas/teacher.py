"""
Teacher schemas for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import time
import re


class TeacherBase(BaseModel):
    """Base teacher schema with common fields."""
    code: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Unique teacher code",
        examples=["T001", "MATH01", "FR_DUPONT"]
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Teacher's first name",
        examples=["Jean", "Sarah", "יוסף"]
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Teacher's last name",
        examples=["Dupont", "Cohen", "לוי"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Teacher's email address",
        examples=["jean.dupont@school.edu", "sarah.cohen@ecole.fr"]
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="Teacher's phone number",
        examples=["+33123456789", "05-1234-5678", "0501234567"]
    )
    max_hours_per_week: int = Field(
        default=30, 
        ge=1, 
        le=50,
        description="Maximum teaching hours per week",
        examples=[20, 30, 40]
    )
    max_hours_per_day: int = Field(
        default=8, 
        ge=1, 
        le=12,
        description="Maximum teaching hours per day",
        examples=[6, 8, 10]
    )
    prefers_consecutive_hours: bool = Field(
        default=True,
        description="Whether teacher prefers consecutive teaching hours"
    )
    is_active: bool = Field(
        default=True,
        description="Whether teacher is currently active"
    )
    primary_language: str = Field(
        default="he", 
        pattern="^(he|fr)$",
        description="Primary teaching language",
        examples=["he", "fr"]
    )
    can_teach_in_french: bool = Field(
        default=False,
        description="Can teach subjects in French"
    )
    can_teach_in_hebrew: bool = Field(
        default=True,
        description="Can teach subjects in Hebrew"
    )

    @validator('code')
    def validate_code(cls, v):
        """Validate teacher code format."""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Code must contain only letters, numbers, underscores and hyphens')
        return v.upper()

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        # Remove spaces and common separators
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^[\+]?[0-9]{9,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v

    @validator('max_hours_per_day', always=True)
    def validate_daily_hours(cls, v, values):
        """Ensure daily hours don't exceed weekly hours."""
        weekly_hours = values.get('max_hours_per_week', 30)
        if v * 5 < weekly_hours:  # Assuming 5 working days
            raise ValueError('Daily hours * 5 should be at least equal to weekly hours')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "T001",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@school.edu",
                "phone": "+33123456789",
                "max_hours_per_week": 30,
                "max_hours_per_day": 8,
                "prefers_consecutive_hours": True,
                "is_active": True,
                "primary_language": "fr",
                "can_teach_in_french": True,
                "can_teach_in_hebrew": False
            }
        }


class TeacherCreate(TeacherBase):
    """Schema for teacher creation."""
    subject_ids: List[int] = Field(
        default=[],
        description="List of subject IDs this teacher can teach",
        examples=[[1, 2, 3], [5], []]
    )

    @validator('subject_ids')
    def validate_subject_ids(cls, v):
        """Validate subject IDs."""
        if len(v) != len(set(v)):
            raise ValueError('Subject IDs must be unique')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "T001",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@school.edu",
                "phone": "+33123456789",
                "max_hours_per_week": 30,
                "max_hours_per_day": 8,
                "prefers_consecutive_hours": True,
                "is_active": True,
                "primary_language": "fr",
                "can_teach_in_french": True,
                "can_teach_in_hebrew": False,
                "subject_ids": [1, 2, 3]
            }
        }


class TeacherUpdate(BaseModel):
    """Schema for teacher update - all fields optional."""
    code: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=20,
        description="Unique teacher code"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Teacher's first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Teacher's last name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Teacher's email address"
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="Teacher's phone number"
    )
    max_hours_per_week: Optional[int] = Field(
        None, 
        ge=1, 
        le=50,
        description="Maximum teaching hours per week"
    )
    max_hours_per_day: Optional[int] = Field(
        None, 
        ge=1, 
        le=12,
        description="Maximum teaching hours per day"
    )
    prefers_consecutive_hours: Optional[bool] = Field(
        None,
        description="Whether teacher prefers consecutive teaching hours"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether teacher is currently active"
    )
    primary_language: Optional[str] = Field(
        None, 
        pattern="^(he|fr)$",
        description="Primary teaching language"
    )
    can_teach_in_french: Optional[bool] = Field(
        None,
        description="Can teach subjects in French"
    )
    can_teach_in_hebrew: Optional[bool] = Field(
        None,
        description="Can teach subjects in Hebrew"
    )
    subject_ids: Optional[List[int]] = Field(
        None,
        description="List of subject IDs this teacher can teach"
    )

    @validator('code')
    def validate_code(cls, v):
        """Validate teacher code format."""
        if v is None:
            return v
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Code must contain only letters, numbers, underscores and hyphens')
        return v.upper()

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^[\+]?[0-9]{9,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return v

    @validator('subject_ids')
    def validate_subject_ids(cls, v):
        """Validate subject IDs."""
        if v is None:
            return v
        if len(v) != len(set(v)):
            raise ValueError('Subject IDs must be unique')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "new.email@school.edu",
                "max_hours_per_week": 35,
                "is_active": False
            }
        }


class TeacherResponse(TeacherBase):
    """Schema for teacher response."""
    id: int = Field(description="Teacher unique identifier")
    
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
                "last_name": "Dupont",
                "email": "jean.dupont@school.edu",
                "phone": "+33123456789",
                "max_hours_per_week": 30,
                "max_hours_per_day": 8,
                "prefers_consecutive_hours": True,
                "is_active": True,
                "primary_language": "fr",
                "can_teach_in_french": True,
                "can_teach_in_hebrew": False
            }
        }


class TeacherWithSubjects(TeacherResponse):
    """Schema for teacher response with subject relations."""
    subjects: List["SubjectBasic"] = Field(
        default=[],
        description="List of subjects this teacher can teach"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "T001",
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@school.edu",
                "phone": "+33123456789",
                "max_hours_per_week": 30,
                "max_hours_per_day": 8,
                "prefers_consecutive_hours": True,
                "is_active": True,
                "primary_language": "fr",
                "can_teach_in_french": True,
                "can_teach_in_hebrew": False,
                "subjects": [
                    {
                        "id": 1,
                        "code": "MATH",
                        "name_he": "מתמטיקה",
                        "name_fr": "Mathématiques"
                    },
                    {
                        "id": 2,
                        "code": "PHYS",
                        "name_he": "פיזיקה", 
                        "name_fr": "Physique"
                    }
                ]
            }
        }


# Existing schemas with improvements
class TeacherAvailabilityBase(BaseModel):
    """Base schema for teacher availability."""
    teacher_id: int = Field(description="Teacher ID")
    day_of_week: int = Field(
        ..., 
        ge=0, 
        le=5,
        description="Day of week (0=Sunday, 5=Friday)",
        examples=[0, 1, 2, 3, 4, 5]
    )
    start_time: time = Field(
        description="Start time of availability",
        examples=["08:00:00", "13:00:00"]
    )
    end_time: time = Field(
        description="End time of availability",
        examples=["12:00:00", "17:00:00"]
    )
    is_available: bool = Field(
        default=True,
        description="Whether teacher is available during this period"
    )

    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Ensure end time is after start time."""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError('End time must be after start time')
        return v

    class Config:
        from_attributes = True


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    """Schema for creating teacher availability."""
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "teacher_id": 1,
                "day_of_week": 1,
                "start_time": "08:00:00",
                "end_time": "12:00:00",
                "is_available": True
            }
        }


class TeacherAvailability(TeacherAvailabilityBase):
    """Schema for teacher availability response."""
    id: int = Field(description="Availability record ID")
    
    class Config:
        from_attributes = True


class TeacherBasic(BaseModel):
    """Basic teacher info for nested responses."""
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


# Import at the end to avoid circular imports
from app.schemas.subject import SubjectBasic
TeacherWithSubjects.model_rebuild() 