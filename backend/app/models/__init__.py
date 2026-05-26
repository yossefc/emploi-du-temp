"""Modèles SQLAlchemy — v2 refonte.

Ordre d'import important pour résoudre les relations (back_populates).
"""

# 1. Tables d'association (pas de classes, juste des metadata)
from app.models.associations import (
    teacher_qualified_subjects,
    group_teachers,
    group_source_classes,
)

# 2. School (racine) et utilisateurs
from app.models.school import School
from app.models.user import User, UserRole

# 3. Configuration école
from app.models.time_grid import TimeSlot

# 4. Entités métier — ordre : independents → dependents
from app.models.subject import Subject
from app.models.room import Room
from app.models.teacher import Teacher
from app.models.grade import Grade, GroupingPolicy
from app.models.klass import Class
from app.models.group import Group, GroupType, ParallelCohort

# 5. Contraintes et planning
from app.models.constraint import (
    Constraint,
    ConstraintType,
    ConstraintPriority,
    ConstraintOriginRole,
)
from app.models.schedule import Schedule, ScheduleEntry, ScheduleStatus


__all__ = [
    # Associations
    "teacher_qualified_subjects", "group_teachers", "group_source_classes",
    # Tenant & users
    "School", "User", "UserRole",
    # Time grid
    "TimeSlot",
    # Entités
    "Subject", "Room", "Teacher", "Grade", "GroupingPolicy", "Class",
    "Group", "GroupType", "ParallelCohort",
    # Contraintes & planning
    "Constraint", "ConstraintType", "ConstraintPriority", "ConstraintOriginRole",
    "Schedule", "ScheduleEntry", "ScheduleStatus",
]
