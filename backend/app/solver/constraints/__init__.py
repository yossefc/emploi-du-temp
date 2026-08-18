"""Package des contraintes du solveur.

Expose :
- `BaseConstraint`, `ConstraintExplanation` (interfaces)
- `STRUCTURAL_CONSTRAINTS` : liste des classes structurelles à instancier automatiquement
- `CONSTRAINT_REGISTRY` : ConstraintType (str enum value) → classe BaseConstraint
- `from_db(db_constraint)` : factory qui instancie la bonne classe depuis une ligne DB
"""

from __future__ import annotations

from app.models import Constraint as DBConstraint
from app.models import ConstraintType
from app.solver.constraints.assignment import (
    TeacherLanguageRequiredConstraint,
    TeacherQualifiedForSubjectConstraint,
)
from app.solver.constraints.preferences import (
    TeacherAvoidGapsConstraint,
    TeacherPreferAfternoonConstraint,
    TeacherPreferGroupedDaysConstraint,
    TeacherPreferMorningConstraint,
)
from app.solver.constraints.teaching import (
    TeacherFreeDayConstraint,
    TeacherPreferredFreeDayConstraint,
    GroupPinnedSlotConstraint,
    TeachersMustTeachTogetherConstraint,
)
from app.solver.constraints.barrette import ExtraHoursAtDayEdgeConstraint
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation
from app.solver.constraints.block_slot import (
    BlockSlotClassConstraint,
    BlockSlotGroupConstraint,
    BlockSlotRoomConstraint,
    BlockSlotSchoolConstraint,
    BlockSlotTeacherConstraint,
)
from app.solver.constraints.placement import (
    SubjectConsecutiveHoursConstraint,
    SubjectMaxPerDayConstraint,
    SubjectPreferredSlotRangeConstraint,
    SubjectRequiredSlotRangeConstraint,
)
from app.solver.constraints.structural import (
    ClassNoOverlapConstraint,
    ParallelCohortSameSlotConstraint,
    RoomNoOverlapConstraint,
    TeacherNoOverlapConstraint,
)
from app.solver.constraints.volume import (
    GroupHoursPerWeekConstraint,
    TeacherMaxConsecutiveConstraint,
    TeacherMaxHoursDayConstraint,
    TeacherMaxHoursWeekConstraint,
)


# Contraintes structurelles toujours ajoutées par l'engine (pas en DB).
STRUCTURAL_CONSTRAINTS: list[type[BaseConstraint]] = [
    TeacherNoOverlapConstraint,
    ClassNoOverlapConstraint,
    RoomNoOverlapConstraint,
    ParallelCohortSameSlotConstraint,
]


# Registry : ConstraintType.value (str) -> classe BaseConstraint
# Permet de retrouver la classe à instancier depuis une ligne `constraints` de la DB.
CONSTRAINT_REGISTRY: dict[str, type[BaseConstraint]] = {
    # Blocages
    ConstraintType.BLOCK_SLOT_SCHOOL.value: BlockSlotSchoolConstraint,
    ConstraintType.BLOCK_SLOT_CLASS.value: BlockSlotClassConstraint,
    ConstraintType.BLOCK_SLOT_GROUP.value: BlockSlotGroupConstraint,
    ConstraintType.BLOCK_SLOT_TEACHER.value: BlockSlotTeacherConstraint,
    ConstraintType.BLOCK_SLOT_ROOM.value: BlockSlotRoomConstraint,
    # Placement matière
    ConstraintType.SUBJECT_REQUIRED_SLOT_RANGE.value: SubjectRequiredSlotRangeConstraint,
    ConstraintType.SUBJECT_PREFERRED_SLOT_RANGE.value: SubjectPreferredSlotRangeConstraint,
    ConstraintType.SUBJECT_MAX_PER_DAY.value: SubjectMaxPerDayConstraint,
    ConstraintType.SUBJECT_CONSECUTIVE_HOURS.value: SubjectConsecutiveHoursConstraint,
    # Volumes
    ConstraintType.GROUP_HOURS_PER_WEEK.value: GroupHoursPerWeekConstraint,
    ConstraintType.TEACHER_MAX_HOURS_WEEK.value: TeacherMaxHoursWeekConstraint,
    ConstraintType.TEACHER_MAX_HOURS_DAY.value: TeacherMaxHoursDayConstraint,
    ConstraintType.TEACHER_MAX_CONSECUTIVE.value: TeacherMaxConsecutiveConstraint,
    # Affectation
    ConstraintType.TEACHER_QUALIFIED_FOR_SUBJECT.value: TeacherQualifiedForSubjectConstraint,
    ConstraintType.TEACHER_LANGUAGE_REQUIRED.value: TeacherLanguageRequiredConstraint,
    ConstraintType.TEACHERS_MUST_TEACH_TOGETHER.value: TeachersMustTeachTogetherConstraint,
    ConstraintType.TEACHER_FREE_DAY.value: TeacherFreeDayConstraint,
    ConstraintType.TEACHER_PREFERRED_FREE_DAY.value: TeacherPreferredFreeDayConstraint,
    ConstraintType.GROUP_PINNED_SLOT.value: GroupPinnedSlotConstraint,
    # Préférences SOFT
    ConstraintType.TEACHER_PREFER_MORNING.value: TeacherPreferMorningConstraint,
    ConstraintType.TEACHER_PREFER_AFTERNOON.value: TeacherPreferAfternoonConstraint,
    ConstraintType.TEACHER_PREFER_GROUPED_DAYS.value: TeacherPreferGroupedDaysConstraint,
    ConstraintType.TEACHER_AVOID_GAPS.value: TeacherAvoidGapsConstraint,
    # Barrette
    ConstraintType.EXTRA_HOURS_AT_DAY_EDGE.value: ExtraHoursAtDayEdgeConstraint,
}


def from_db(db_constraint: DBConstraint) -> BaseConstraint:
    """Instancie la bonne classe BaseConstraint depuis une ligne `constraints` DB."""
    cls = CONSTRAINT_REGISTRY.get(db_constraint.constraint_type.value)
    if cls is None:
        raise ValueError(
            f"Type de contrainte inconnu / non implémenté : {db_constraint.constraint_type}"
        )
    return cls.from_db(db_constraint)


__all__ = [
    "BaseConstraint",
    "ConstraintExplanation",
    "STRUCTURAL_CONSTRAINTS",
    "CONSTRAINT_REGISTRY",
    "from_db",
]
