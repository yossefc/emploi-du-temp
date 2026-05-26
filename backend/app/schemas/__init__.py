"""Schemas Pydantic — v2."""

from app.schemas.constraint import (
    ConstraintBase,
    ConstraintCreate,
    ConstraintRead,
    ConstraintUpdate,
)
from app.schemas.grade import GradeBase, GradeCreate, GradeRead, GradeUpdate
from app.schemas.group import (
    GroupBase,
    GroupCreate,
    GroupRead,
    GroupUpdate,
    ParallelCohortBase,
    ParallelCohortCreate,
    ParallelCohortRead,
    ParallelCohortUpdate,
)
from app.schemas.klass import ClassBase, ClassCreate, ClassRead, ClassUpdate
from app.schemas.room import RoomBase, RoomCreate, RoomRead, RoomUpdate
from app.schemas.schedule import (
    ConstraintConflictInfo,
    GenerateRequest,
    GenerateResponseConflict,
    GenerateResponseSuccess,
    GenerateResponseTimeout,
    ScheduleEntryRead,
    ScheduleRead,
    ScheduleWithEntries,
)
from app.schemas.school import SchoolBase, SchoolCreate, SchoolRead, SchoolUpdate
from app.schemas.subject import SubjectBase, SubjectCreate, SubjectRead, SubjectUpdate
from app.schemas.teacher import TeacherBase, TeacherCreate, TeacherRead, TeacherUpdate
from app.schemas.time_slot import (
    TimeGridReplace,
    TimeSlotBase,
    TimeSlotCreate,
    TimeSlotRead,
    TimeSlotUpdate,
)

__all__ = [
    # School
    "SchoolBase", "SchoolCreate", "SchoolRead", "SchoolUpdate",
    # Grade
    "GradeBase", "GradeCreate", "GradeRead", "GradeUpdate",
    # Class
    "ClassBase", "ClassCreate", "ClassRead", "ClassUpdate",
    # Subject
    "SubjectBase", "SubjectCreate", "SubjectRead", "SubjectUpdate",
    # Teacher
    "TeacherBase", "TeacherCreate", "TeacherRead", "TeacherUpdate",
    # Room
    "RoomBase", "RoomCreate", "RoomRead", "RoomUpdate",
    # TimeSlot
    "TimeSlotBase", "TimeSlotCreate", "TimeSlotRead", "TimeSlotUpdate",
    "TimeGridReplace",
    # Group + ParallelCohort
    "GroupBase", "GroupCreate", "GroupRead", "GroupUpdate",
    "ParallelCohortBase", "ParallelCohortCreate", "ParallelCohortRead", "ParallelCohortUpdate",
    # Constraints
    "ConstraintBase", "ConstraintCreate", "ConstraintRead", "ConstraintUpdate",
    # Schedules
    "ScheduleEntryRead", "ScheduleRead", "ScheduleWithEntries",
    "GenerateRequest", "GenerateResponseSuccess", "GenerateResponseConflict",
    "GenerateResponseTimeout", "ConstraintConflictInfo",
]
