"""
Database models package.
"""

# Ajouter en premier pour éviter les imports circulaires
from app.models.associations import (
    teacher_subjects,
    class_mandatory_subjects,
    class_preferred_rooms
)

# Puis importer les modèles
from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.models.subject import Subject, SubjectType, configure_subject_relationships
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

# Configure relationships after all models are imported
configure_subject_relationships()

__all__ = [
    # Associations (tables d'association)
    "teacher_subjects",
    "class_mandatory_subjects", 
    "class_preferred_rooms",
    
    # User models
    "User",
    "UserRole",
    
    # Core models
    "Teacher",
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