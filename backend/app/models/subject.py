"""
Subject model for managing school subjects.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base
from app.models.teacher import teacher_subjects


class SubjectType(str, enum.Enum):
    """Subject type enumeration."""
    ACADEMIC = "academic"
    SPORTS = "sports"
    ARTS = "arts"
    RELIGIOUS = "religious"
    LANGUAGE = "language"
    SCIENCE_LAB = "science_lab"


class Subject(Base):
    """Subject model."""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name_he = Column(String, nullable=False)  # Hebrew name
    name_fr = Column(String, nullable=False)  # French name
    subject_type = Column(Enum(SubjectType), default=SubjectType.ACADEMIC)
    
    # Requirements
    requires_lab = Column(Boolean, default=False)
    requires_special_room = Column(Boolean, default=False)
    requires_consecutive_hours = Column(Boolean, default=False)
    max_hours_per_day = Column(Integer, default=2)
    
    # Israeli-specific settings
    is_religious = Column(Boolean, default=False)
    requires_gender_separation = Column(Boolean, default=False)
    
    # Relationships
    teachers = relationship("Teacher", secondary=teacher_subjects, back_populates="subjects")
    class_requirements = relationship("ClassSubjectRequirement", back_populates="subject") 