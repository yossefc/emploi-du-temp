"""
ClassGroup model for managing student classes.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum, JSON, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
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
    
    # Basic information
    nom = Column(String(255), nullable=False)  # Class name
    niveau = Column(String(50), nullable=False)  # Level (e.g., "6ème", "5ème")
    effectif = Column(Integer, nullable=False)  # Number of students
    
    # Legacy fields for compatibility
    name = Column(String(255), nullable=True)
    grade = Column(Enum(Grade), nullable=True)
    student_count = Column(Integer, nullable=True)
    
    class_type = Column(Enum(ClassType), default=ClassType.REGULAR)
    
    # Schedule preferences (JSON format)
    horaires_preferes = Column(JSON, nullable=True)  # Preferred schedule slots
    
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
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    matieres_obligatoires = relationship(
        "Subject", 
        secondary=class_group_subjects, 
        back_populates="class_groups",
        lazy="select"
    )
    
    homeroom_teacher = relationship("Teacher", foreign_keys=[homeroom_teacher_id])
    
    # Legacy relationships
    subject_requirements = relationship("ClassSubjectRequirement", back_populates="class_group", cascade="all, delete-orphan")
    schedules = relationship("ScheduleEntry", back_populates="class_group") 