"""
Subject model for managing school subjects.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship, validates
import enum
import re

from app.db.base import Base


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
    code = Column(String(20), unique=True, index=True, nullable=False)
    name_he = Column(String(255), nullable=False)  # Hebrew name
    name_fr = Column(String(255), nullable=False)  # French name
    subject_type = Column(Enum(SubjectType), default=SubjectType.ACADEMIC)
    
    # Visual and display properties (added from migration)
    color_hex = Column(String(7), nullable=True)  # Color for UI display
    abbreviation = Column(String(10), nullable=True)  # Short abbreviation
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Requirements
    requires_lab = Column(Boolean, default=False)
    requires_special_room = Column(Boolean, default=False)
    requires_consecutive_hours = Column(Boolean, default=False)
    max_hours_per_day = Column(Integer, default=2)
    
    # Israeli-specific settings
    is_religious = Column(Boolean, default=False)
    requires_gender_separation = Column(Boolean, default=False)
    
    # Relationships will be set after import to avoid circular imports
    class_requirements = relationship("ClassSubjectRequirement", back_populates="subject")
    class_groups = relationship("ClassGroup", secondary="class_group_subjects", back_populates="subjects")
    
    # Validations
    @validates('code')
    def validate_code(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Subject code cannot be empty")
        return value.strip().upper()
    
    @validates('color_hex')
    def validate_color_hex(self, key, value):
        if value and not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return value
    
    @validates('max_hours_per_day')
    def validate_max_hours_per_day(self, key, value):
        if value is not None and (value < 1 or value > 8):
            raise ValueError("Max hours per day must be between 1 and 8")
        return value
    
    @validates('abbreviation')
    def validate_abbreviation(self, key, value):
        if value and len(value) > 10:
            raise ValueError("Abbreviation cannot be longer than 10 characters")
        return value.upper() if value else value
    
    # Properties
    @property
    def display_name(self):
        """Get localized display name (Hebrew by default)."""
        return self.name_he
    
    @property
    def display_name_fr(self):
        """Get French display name."""
        return self.name_fr
    
    @property
    def short_name(self):
        """Get abbreviated name or code."""
        return self.abbreviation or self.code
    
    @property
    def is_lab_subject(self):
        """Check if subject requires lab facilities."""
        return self.requires_lab or self.subject_type == SubjectType.SCIENCE_LAB
    
    @property
    def teacher_count(self):
        """Get number of teachers who can teach this subject."""
        return len(self.teachers) if hasattr(self, 'teachers') else 0
    
    def get_localized_name(self, language="he"):
        """Get subject name in specified language."""
        if language == "fr":
            return self.name_fr
        return self.name_he
    
    def __repr__(self):
        return f"<Subject(id={self.id}, code='{self.code}', name_he='{self.name_he}', active={self.is_active})>"


# Configure relationship after class definition to avoid circular imports
def configure_subject_relationships():
    """Configure Subject relationships after all models are loaded."""
    from app.models.teacher import teacher_subjects
    Subject.teachers = relationship("Teacher", secondary=teacher_subjects, back_populates="subjects") 