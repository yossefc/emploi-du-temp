"""
ClassGroup model for managing student classes.
"""

from sqlalchemy import Column, Integer, String, Boolean, Enum
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


class ClassGroup(Base):
    """ClassGroup model."""
    __tablename__ = "class_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "9A", "10B"
    name = Column(String, nullable=False)
    grade = Column(Enum(Grade), nullable=False)
    class_type = Column(Enum(ClassType), default=ClassType.REGULAR)
    student_count = Column(Integer, nullable=False)
    
    # Israeli-specific settings
    is_boys_only = Column(Boolean, default=False)
    is_girls_only = Column(Boolean, default=False)
    is_mixed = Column(Boolean, default=True)
    primary_language = Column(String(2), default="he")  # 'he' or 'fr'
    
    # Homeroom teacher
    homeroom_teacher_id = Column(Integer, nullable=True)
    
    # Relationships
    subject_requirements = relationship("ClassSubjectRequirement", back_populates="class_group", cascade="all, delete-orphan")
    schedules = relationship("ScheduleEntry", back_populates="class_group") 