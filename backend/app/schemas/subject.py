"""
Subject schemas for API validation.
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class SubjectType(str, Enum):
    """Subject type enumeration."""
    ACADEMIC = "academic"
    SPORTS = "sports"
    ARTS = "arts"
    RELIGIOUS = "religious"
    LANGUAGE = "language"
    SCIENCE_LAB = "science_lab"


class SubjectBase(BaseModel):
    """Base subject schema."""
    code: str = Field(..., min_length=1, max_length=20)
    name_he: str
    name_fr: str
    subject_type: SubjectType = SubjectType.ACADEMIC
    requires_lab: bool = False
    requires_special_room: bool = False
    requires_consecutive_hours: bool = False
    max_hours_per_day: int = Field(default=2, ge=1, le=4)
    is_religious: bool = False
    requires_gender_separation: bool = False


class SubjectCreate(SubjectBase):
    """Schema for subject creation."""
    pass


class SubjectUpdate(BaseModel):
    """Schema for subject update."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name_he: Optional[str] = None
    name_fr: Optional[str] = None
    subject_type: Optional[SubjectType] = None
    requires_lab: Optional[bool] = None
    requires_special_room: Optional[bool] = None
    requires_consecutive_hours: Optional[bool] = None
    max_hours_per_day: Optional[int] = Field(None, ge=1, le=4)
    is_religious: Optional[bool] = None
    requires_gender_separation: Optional[bool] = None


class SubjectInDB(SubjectBase):
    """Schema for subject in database."""
    id: int
    
    class Config:
        from_attributes = True


class Subject(SubjectInDB):
    """Schema for subject response."""
    pass


class SubjectBasic(BaseModel):
    """Basic subject info for nested responses."""
    id: int
    code: str
    name_he: str
    name_fr: str
    subject_type: SubjectType
    
    class Config:
        from_attributes = True 