"""
Constraint models for managing scheduling constraints.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class DayOfWeek(int, enum.Enum):
    """Day of week enumeration (Israeli week: Sunday=0 to Friday=5)."""
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5


class ConstraintType(str, enum.Enum):
    """Constraint type enumeration."""
    HARD = "hard"  # Must be satisfied
    SOFT = "soft"  # Should be satisfied if possible


class TeacherAvailability(Base):
    """Teacher availability constraints."""
    __tablename__ = "teacher_availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)  # True = available, False = unavailable
    
    # Relationships
    teacher = relationship("Teacher", back_populates="availabilities")


class TeacherPreference(Base):
    """Teacher preferences (soft constraints)."""
    __tablename__ = "teacher_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    preference_type = Column(String, nullable=False)  # e.g., "no_early_monday", "consecutive_classes"
    parameters = Column(JSON)  # Additional parameters for the preference
    weight = Column(Integer, default=1)  # Importance weight (1-10)
    
    # Relationships
    teacher = relationship("Teacher", back_populates="preferences")


class RoomUnavailability(Base):
    """Room unavailability constraints."""
    __tablename__ = "room_unavailabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String)
    
    # Relationships
    room = relationship("Room", back_populates="unavailabilities")


class ClassSubjectRequirement(Base):
    """Requirements for subjects per class."""
    __tablename__ = "class_subject_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    hours_per_week = Column(Integer, nullable=False)
    preferred_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    
    # Special requirements
    requires_double_period = Column(Boolean, default=False)
    max_per_day = Column(Integer, default=2)
    min_days_between = Column(Integer, default=0)  # Minimum days between lessons
    
    # Relationships
    class_group = relationship("ClassGroup", back_populates="subject_requirements")
    subject = relationship("Subject", back_populates="class_requirements")
    preferred_teacher = relationship("Teacher", foreign_keys=[preferred_teacher_id])


class GlobalConstraint(Base):
    """Global scheduling constraints."""
    __tablename__ = "global_constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    constraint_type = Column(Enum(ConstraintType), default=ConstraintType.HARD)
    description = Column(String)
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    # Examples of global constraints:
    # - "no_teacher_gaps": Teachers shouldn't have gaps in their daily schedule
    # - "lunch_break": All classes must have a lunch break between 12:00-14:00
    # - "prayer_time": Friday prayer time must be kept free
    # - "gender_separation": Boys and girls sports classes cannot be at the same time 