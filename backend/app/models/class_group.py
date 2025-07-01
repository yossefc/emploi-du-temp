"""
ClassGroup model for managing student classes.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class Grade(str, enum.Enum):
    """Grade levels enumeration."""
    GRADE_6 = "6"
    GRADE_7 = "7"
    GRADE_8 = "8"
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


class ClassType(str, enum.Enum):
    """Class type enumeration."""
    REGULAR = "regular"
    ADVANCED = "advanced"
    SPECIAL_NEEDS = "special_needs"


# Association table for many-to-many relationship between ClassGroup and Subject
class_group_subjects = Table(
    'class_group_subjects',
    Base.metadata,
    Column('class_group_id', Integer, ForeignKey('class_groups.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True)
)


class ClassGroup(Base):
    """ClassGroup model with enhanced functionality."""
    __tablename__ = "class_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "9A", "10B"
    
    # Basic information - unified English names
    name = Column(String(255), nullable=False)  # Class name
    grade_level = Column(String(50), nullable=False)  # Level (e.g., "6ème", "5ème")
    student_count = Column(Integer, nullable=False)  # Number of students
    
    class_type = Column(Enum(ClassType), default=ClassType.REGULAR)
    
    # Schedule preferences (JSON format)
    schedule_preferences = Column(JSON, nullable=True)  # Preferred schedule slots
    
    # Additional metadata
    description = Column(Text, nullable=True)
    academic_year = Column(String(20), nullable=True)  # e.g., "2024-2025"
    
    # Israeli-specific settings
    is_boys_only = Column(Boolean, default=False)
    is_girls_only = Column(Boolean, default=False)
    is_mixed = Column(Boolean, default=True)
    primary_language = Column(String(2), default="he")  # 'he' or 'fr'
    
    # Homeroom teacher
    homeroom_teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subjects = relationship(
        "Subject", 
        secondary=class_group_subjects, 
        back_populates="class_groups",
        lazy="select"
    )
    
    homeroom_teacher = relationship("Teacher", foreign_keys=[homeroom_teacher_id])
    subject_requirements = relationship("ClassSubjectRequirement", back_populates="class_group", cascade="all, delete-orphan")
    schedule_entries = relationship("ScheduleEntry", back_populates="class_group")
    
    # Validations
    @validates('student_count')
    def validate_student_count(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Student count cannot be negative")
        return value
    
    @validates('code')
    def validate_code(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Class code cannot be empty")
        return value.strip().upper()
    
    # Properties
    @property
    def display_name(self):
        """Get formatted display name."""
        return f"{self.code} - {self.name}"
    
    @property
    def is_gender_separated(self):
        """Check if class is gender separated."""
        return self.is_boys_only or self.is_girls_only
    
    @property
    def grade_numeric(self):
        """Get numeric grade level."""
        try:
            return int(self.grade_level)
        except (ValueError, TypeError):
            return None
    
    def __repr__(self):
        return f"<ClassGroup(id={self.id}, code='{self.code}', name='{self.name}', students={self.student_count})>" 