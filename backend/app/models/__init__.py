"""
Database models package.
"""

from app.models.user import User, UserRole
from app.models.teacher import Teacher, teacher_subjects
from app.models.subject import Subject, SubjectType
from app.models.class_group import ClassGroup, Grade, ClassType
from app.models.room import Room, RoomType
from app.models.constraint import (
    DayOfWeek,
    ConstraintType,
    TeacherAvailability,
    TeacherPreference,
    RoomUnavailability,
    ClassSubjectRequirement,
    GlobalConstraint
)
from app.models.schedule import Schedule, ScheduleEntry, ScheduleConflict

__all__ = [
    # User models
    "User",
    "UserRole",
    
    # Core models
    "Teacher",
    "teacher_subjects",
    "Subject",
    "SubjectType",
    "ClassGroup",
    "Grade",
    "ClassType",
    "Room",
    "RoomType",
    
    # Constraint models
    "DayOfWeek",
    "ConstraintType",
    "TeacherAvailability",
    "TeacherPreference",
    "RoomUnavailability",
    "ClassSubjectRequirement",
    "GlobalConstraint",
    
    # Schedule models
    "Schedule",
    "ScheduleEntry",
    "ScheduleConflict"
] 