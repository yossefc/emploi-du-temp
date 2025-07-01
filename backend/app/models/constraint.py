"""
Constraint models for managing scheduling constraints.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Enum, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
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
    notes = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("Teacher", back_populates="availabilities")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('teacher_id', 'day_of_week', 'start_time', 'end_time', name='uq_teacher_availability'),
    )
    
    # Validations
    @validates('start_time', 'end_time')
    def validate_times(self, key, value):
        if hasattr(self, 'start_time') and hasattr(self, 'end_time'):
            if self.start_time and self.end_time and self.start_time >= self.end_time:
                raise ValueError("Start time must be before end time")
        return value
    
    def __repr__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"<TeacherAvailability(teacher_id={self.teacher_id}, {self.day_of_week.name} {self.start_time}-{self.end_time}, {status})>"


class TeacherPreference(Base):
    """Teacher preferences (soft constraints)."""
    __tablename__ = "teacher_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    preference_type = Column(String(100), nullable=False)  # e.g., "no_early_monday", "consecutive_classes"
    parameters = Column(JSON)  # Additional parameters for the preference
    weight = Column(Integer, default=1)  # Importance weight (1-10)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("Teacher", back_populates="preferences")
    
    # Validations
    @validates('weight')
    def validate_weight(self, key, value):
        if value is not None and (value < 1 or value > 10):
            raise ValueError("Weight must be between 1 and 10")
        return value
    
    def __repr__(self):
        return f"<TeacherPreference(teacher_id={self.teacher_id}, type='{self.preference_type}', weight={self.weight})>"


class RoomUnavailability(Base):
    """Room unavailability constraints."""
    __tablename__ = "room_unavailabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String(500), nullable=True)
    is_recurring = Column(Boolean, default=True)  # Weekly recurring or one-time
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room = relationship("Room", back_populates="unavailabilities")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('room_id', 'day_of_week', 'start_time', 'end_time', name='uq_room_unavailability'),
    )
    
    # Validations
    @validates('start_time', 'end_time')
    def validate_times(self, key, value):
        if hasattr(self, 'start_time') and hasattr(self, 'end_time'):
            if self.start_time and self.end_time and self.start_time >= self.end_time:
                raise ValueError("Start time must be before end time")
        return value
    
    def __repr__(self):
        return f"<RoomUnavailability(room_id={self.room_id}, {self.day_of_week.name} {self.start_time}-{self.end_time})>"


class ClassSubjectRequirement(Base):
    """Requirements for subjects per class."""
    __tablename__ = "class_subject_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False)  # Updated to match migration
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    hours_per_week = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=True)  # Added from migration
    preferred_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    
    # Special requirements
    requires_double_period = Column(Boolean, default=False)
    max_per_day = Column(Integer, default=2)
    min_days_between = Column(Integer, default=0)  # Minimum days between lessons
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    class_group = relationship("ClassGroup", back_populates="subject_requirements")
    subject = relationship("Subject", back_populates="class_requirements")
    preferred_teacher = relationship("Teacher", foreign_keys=[preferred_teacher_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', name='uq_class_subject'),
    )
    
    # Validations
    @validates('hours_per_week')
    def validate_hours_per_week(self, key, value):
        if value is not None and (value < 1 or value > 20):
            raise ValueError("Hours per week must be between 1 and 20")
        return value
    
    @validates('max_per_day')
    def validate_max_per_day(self, key, value):
        if value is not None and (value < 1 or value > 8):
            raise ValueError("Max per day must be between 1 and 8")
        return value
    
    @validates('min_days_between')
    def validate_min_days_between(self, key, value):
        if value is not None and (value < 0 or value > 5):
            raise ValueError("Min days between must be between 0 and 5")
        return value
    
    def __repr__(self):
        return f"<ClassSubjectRequirement(class_id={self.class_id}, subject_id={self.subject_id}, hours={self.hours_per_week})>"


class GlobalConstraint(Base):
    """Global scheduling constraints."""
    __tablename__ = "global_constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    constraint_type = Column(Enum(ConstraintType), default=ConstraintType.HARD)
    description = Column(String(500), nullable=True)
    parameters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Validations
    @validates('name')
    def validate_name(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Constraint name cannot be empty")
        return value.strip()
    
    def __repr__(self):
        return f"<GlobalConstraint(id={self.id}, name='{self.name}', type='{self.constraint_type.value}', active={self.is_active})>"
    
    # Examples of global constraints:
    # - "no_teacher_gaps": Teachers shouldn't have gaps in their daily schedule
    # - "lunch_break": All classes must have a lunch break between 12:00-14:00
    # - "prayer_time": Friday prayer time must be kept free
    # - "gender_separation": Boys and girls sports classes cannot be at the same time 