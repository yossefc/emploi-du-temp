"""
Schedule models for managing generated timetables.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.constraint import DayOfWeek


class Schedule(Base):
    """Main schedule/timetable model."""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    academic_year = Column(String)  # e.g., "2024-2025"
    semester = Column(Integer)  # 1 or 2
    
    # Status
    status = Column(String, default="draft")  # draft, active, archived
    is_active = Column(Boolean, default=False)
    
    # Generation metadata
    generation_time_seconds = Column(Float)
    solver_status = Column(String)  # optimal, feasible, infeasible, timeout
    objective_value = Column(Float)  # Optimization score
    conflicts_json = Column(JSON)  # List of conflicts if any
    
    # Versioning
    version = Column(Integer, default=1)
    parent_schedule_id = Column(Integer, ForeignKey("schedules.id"))
    
    # AI modifications tracking
    ai_modifications = Column(JSON)  # Track changes made by AI
    manual_modifications = Column(JSON)  # Track manual changes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    entries = relationship("ScheduleEntry", back_populates="schedule", cascade="all, delete-orphan")
    parent_schedule = relationship("Schedule", remote_side=[id], backref="child_schedules")
    created_by = relationship("User", foreign_keys=[created_by_id])


class ScheduleEntry(Base):
    """Individual schedule entries (lessons)."""
    __tablename__ = "schedule_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    
    # Core scheduling data
    day_of_week = Column(Integer, nullable=False)  # 0-5 (Sunday-Friday)
    period = Column(Integer, nullable=False)  # Period number (1-10)
    
    # Resources
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    
    # Additional info
    is_double_period = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Modification tracking
    is_locked = Column(Boolean, default=False)  # Prevent automatic changes
    modified_by_ai = Column(Boolean, default=False)
    modification_reason = Column(String)
    
    # Relationships
    schedule = relationship("Schedule", back_populates="entries")
    class_group = relationship("ClassGroup", back_populates="schedules")
    subject = relationship("Subject")
    teacher = relationship("Teacher")
    room = relationship("Room", back_populates="schedules")


class ScheduleConflict(Base):
    """Track conflicts in schedules for analysis."""
    __tablename__ = "schedule_conflicts"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    conflict_type = Column(String, nullable=False)  # teacher_overlap, room_overlap, constraint_violation
    severity = Column(String, default="error")  # error, warning, info
    description = Column(Text)
    involved_entries = Column(JSON)  # IDs of schedule entries involved
    constraint_details = Column(JSON)  # Details about which constraint was violated
    resolution_suggestions = Column(JSON)  # AI-generated suggestions
    
    # Relationships
    schedule = relationship("Schedule") 