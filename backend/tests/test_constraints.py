"""Tests des contraintes du solveur (Phase 2).

Stratégie :
- Pour chaque type, vérifier qu'il s'instancie depuis params JSON
- Pour les contraintes-clés, MONTER un mini SolverContext et lancer un solve
  CP-SAT pour vérifier le comportement réel (contrainte respectée ou violée
  selon l'attendu).
- Vérifier que les contraintes HARD produisent bien un assumption_literal
  (essentiel pour l'extraction MUS en Phase 3).
"""

from __future__ import annotations

from datetime import time

import pytest
from ortools.sat.python import cp_model

from app.models import (
    Class,
    Constraint as DBConstraint,
    ConstraintOriginRole,
    ConstraintPriority,
    ConstraintType,
    Grade,
    Group,
    GroupingPolicy,
    GroupType,
    ParallelCohort,
    Room,
    School,
    Subject,
    Teacher,
    TimeSlot,
)
from app.solver.constraints import (
    CONSTRAINT_REGISTRY,
    STRUCTURAL_CONSTRAINTS,
    from_db,
)
from app.solver.constraints.base import BaseConstraint
from app.solver.constraints.block_slot import (
    BlockSlotSchoolConstraint,
    BlockSlotTeacherConstraint,
)
from app.solver.constraints.structural import (
    ClassNoOverlapConstraint,
    ParallelCohortSameSlotConstraint,
    TeacherNoOverlapConstraint,
)
from app.solver.constraints.volume import (
    GroupHoursPerWeekConstraint,
    TeacherMaxHoursDayConstraint,
)
from app.solver.context import SolverContext


# ---------------------------------------------------------------------------
# Helpers : construire un SolverContext minimal de toutes pièces
# ---------------------------------------------------------------------------

def make_ctx(
    *,
    groups: list[Group],
    teachers: list[Teacher],
    classes: list[Class],
    rooms: list[Room] = (),
    time_slots: list[TimeSlot] = None,
    cohorts: list[ParallelCohort] = (),
    days: int = 2,
    slots_per_day: int = 3,
) -> tuple[SolverContext, cp_model.CpModel]:
    """Construit un SolverContext + variables CP-SAT pour les tests.

    Si time_slots non fourni : génère days × slots_per_day actifs, pas de breaks.
    """
    model = cp_model.CpModel()

    if time_slots is None:
        time_slots = []
        for d in range(days):
            for s in range(slots_per_day):
                time_slots.append(TimeSlot(
                    school_id=1, day_of_week=d, slot_index=s,
                    start_time=time(8 + s, 0), end_time=time(8 + s, 45),
                    is_active=True, is_break=False,
                ))

    ctx = SolverContext(
        model=model,
        school=School(id=1, code="test", name="Test"),
        groups=groups,
        teachers=teachers,
        classes=classes,
        rooms=list(rooms),
        time_slots=time_slots,
        parallel_cohorts=list(cohorts),
    )
    ctx.build_caches()

    # Créer les BoolVars assigned[g][d,s] pour chaque group × position active
    positions = ctx.all_active_positions()
    for g in groups:
        ctx.assigned[g.id] = {
            (d, s): model.NewBoolVar(f"x_g{g.id}_d{d}_s{s}")
            for (d, s) in positions
        }
        # room_used si on a des rooms
        if rooms:
            ctx.room_used[g.id] = {}
            for (d, s) in positions:
                ctx.room_used[g.id][(d, s)] = {
                    r.id: model.NewBoolVar(f"r_g{g.id}_d{d}_s{s}_r{r.id}")
                    for r in rooms
                }

    return ctx, model


def make_group(
    *, gid: int, subject_id: int = 1, hours: int = 1,
    teachers: list[Teacher] = (), classes: list[Class] = (),
    label: str = None,
) -> Group:
    g = Group(
        id=gid, school_id=1, grade_id=1, subject_id=subject_id,
        label=label or f"G{gid}", hours_per_week=hours,
        group_type=GroupType.WHOLE_CLASS,
    )
    g.teachers = list(teachers)
    g.source_classes = list(classes)
    return g


def solve_and_get(model: cp_model.CpModel) -> tuple[int, cp_model.CpSolver]:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    return status, solver


# ---------------------------------------------------------------------------
# Registry + instanciation
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_all_db_types_registered(self):
        """Tous les ConstraintType (sauf préfs v2) doivent être dans le registry."""
        registered = set(CONSTRAINT_REGISTRY.keys())
        # Les types v2 (préférences) sont définis dans l'enum mais pas implémentés MVP
        v2_only = {
            ConstraintType.TEACHER_PREFER_MORNING.value,
            ConstraintType.TEACHER_PREFER_AFTERNOON.value,
            ConstraintType.TEACHER_AVOID_GAPS.value,
            ConstraintType.TEACHER_PREFER_GROUPED_DAYS.value,
            ConstraintType.TEACHER_MIN_BREAK_AFTER.value,
            ConstraintType.SUBJECT_PREFERRED_SLOT_RANGE.value,
            ConstraintType.SUBJECT_NOT_CONSECUTIVE_DAYS.value,
            ConstraintType.SUBJECT_REQUIRES_ROOM_TYPE.value,
        }
        all_types = {ct.value for ct in ConstraintType}
        expected_mvp = all_types - v2_only
        missing = expected_mvp - registered
        assert not missing, f"Types MVP non implémentés : {missing}"

    def test_structural_constraints_present(self):
        assert len(STRUCTURAL_CONSTRAINTS) == 4
        names = {c.__name__ for c in STRUCTURAL_CONSTRAINTS}
        assert "TeacherNoOverlapConstraint" in names
        assert "ParallelCohortSameSlotConstraint" in names

    def test_from_db_factory(self):
        db_c = DBConstraint(
            id=1, school_id=1,
            constraint_type=ConstraintType.BLOCK_SLOT_TEACHER,
            priority=ConstraintPriority.HARD,
            parameters={"days": [0], "slot_indices": [0], "target_id": 5},
            origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
        )
        inst = from_db(db_c)
        assert isinstance(inst, BlockSlotTeacherConstraint)
        assert inst.target_id == 5
        assert inst.positions == [(0, 0)]


# ---------------------------------------------------------------------------
# STRUCTURAL : teacher no-overlap
# ---------------------------------------------------------------------------

class TestTeacherNoOverlap:
    def test_two_groups_same_teacher_cannot_share_slot(self):
        """Un prof avec 2 Groups : ils ne peuvent pas être au même créneau."""
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c1 = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        c2 = Class(id=2, school_id=1, grade_id=1, code="C2", name="C2", student_count=20)
        g1 = make_group(gid=1, teachers=[t], classes=[c1], hours=2)
        g2 = make_group(gid=2, teachers=[t], classes=[c2], hours=2)

        ctx, model = make_ctx(groups=[g1, g2], teachers=[t], classes=[c1, c2],
                               days=1, slots_per_day=4)
        TeacherNoOverlapConstraint().apply(ctx)
        # Forcer g1, g2 à être planifiés (2h chacun)
        model.Add(sum(ctx.assigned[1].values()) == 2)
        model.Add(sum(ctx.assigned[2].values()) == 2)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        # Vérifier qu'aucun slot n'a les 2 groupes en même temps
        for d, s in ctx.all_active_positions():
            assert solver.Value(ctx.assigned[1][(d, s)]) + solver.Value(ctx.assigned[2][(d, s)]) <= 1

    def test_infeasible_when_no_room_left(self):
        """Si on demande plus d'heures que de créneaux disponibles → infeasible."""
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        # 2 groups × 3h chacun = 6h, mais on n'a que 4 slots → impossible
        g1 = make_group(gid=1, teachers=[t], classes=[c], hours=3)
        g2 = make_group(gid=2, teachers=[t], classes=[c], hours=3)

        ctx, model = make_ctx(groups=[g1, g2], teachers=[t], classes=[c],
                               days=1, slots_per_day=4)
        TeacherNoOverlapConstraint().apply(ctx)
        model.Add(sum(ctx.assigned[1].values()) == 3)
        model.Add(sum(ctx.assigned[2].values()) == 3)

        status, _ = solve_and_get(model)
        assert status == cp_model.INFEASIBLE


# ---------------------------------------------------------------------------
# STRUCTURAL : parallel cohort same slot (BARRETTE — le cœur du problème)
# ---------------------------------------------------------------------------

class TestParallelCohortSameSlot:
    def test_two_groups_in_cohort_must_be_at_same_slot(self):
        """Math 5 & Math 3 dans la même cohorte → mêmes créneaux."""
        t1 = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="A", languages=["he"])
        t2 = Teacher(id=2, school_id=1, code="T2", first_name="B", last_name="B", languages=["he"])
        c1 = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        c2 = Class(id=2, school_id=1, grade_id=1, code="C2", name="C2", student_count=20)

        cohort = ParallelCohort(id=1, school_id=1, grade_id=1, label="Math barrette")

        g1 = make_group(gid=1, teachers=[t1], classes=[c1], hours=2, label="Math 5")
        g2 = make_group(gid=2, teachers=[t2], classes=[c2], hours=2, label="Math 3")
        g1.parallel_cohort_id = 1
        g2.parallel_cohort_id = 1
        cohort.groups = [g1, g2]

        ctx, model = make_ctx(
            groups=[g1, g2], teachers=[t1, t2], classes=[c1, c2],
            cohorts=[cohort], days=2, slots_per_day=3,
        )
        ParallelCohortSameSlotConstraint().apply(ctx)
        model.Add(sum(ctx.assigned[1].values()) == 2)
        model.Add(sum(ctx.assigned[2].values()) == 2)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        # Vérifier : sur chaque (d,s), assigned[1] == assigned[2]
        for d, s in ctx.all_active_positions():
            assert solver.Value(ctx.assigned[1][(d, s)]) == solver.Value(ctx.assigned[2][(d, s)])

    def test_cohort_with_different_hours_infeasible(self):
        """Si dans une cohorte g1 a 3h et g2 a 2h → infaisable (forcés égaux)."""
        t1 = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="A", languages=["he"])
        t2 = Teacher(id=2, school_id=1, code="T2", first_name="B", last_name="B", languages=["he"])
        c1 = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        c2 = Class(id=2, school_id=1, grade_id=1, code="C2", name="C2", student_count=20)

        cohort = ParallelCohort(id=1, school_id=1, grade_id=1, label="C")
        g1 = make_group(gid=1, teachers=[t1], classes=[c1], hours=3, label="g1")
        g2 = make_group(gid=2, teachers=[t2], classes=[c2], hours=2, label="g2")
        g1.parallel_cohort_id = 1
        g2.parallel_cohort_id = 1
        cohort.groups = [g1, g2]

        ctx, model = make_ctx(groups=[g1, g2], teachers=[t1, t2], classes=[c1, c2],
                               cohorts=[cohort], days=2, slots_per_day=4)
        ParallelCohortSameSlotConstraint().apply(ctx)
        model.Add(sum(ctx.assigned[1].values()) == 3)
        model.Add(sum(ctx.assigned[2].values()) == 2)

        status, _ = solve_and_get(model)
        # Sans EXTRA_HOURS_AT_DAY_EDGE → contradiction, le cohort force égalité partout
        assert status == cp_model.INFEASIBLE


# ---------------------------------------------------------------------------
# BLOCK_SLOT : avec assumption literal
# ---------------------------------------------------------------------------

class TestBlockSlotTeacher:
    def test_block_prevents_group_at_slot(self):
        """Prof bloqué jour 0 slot 0 → ses groupes ne peuvent être là."""
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        g = make_group(gid=1, teachers=[t], classes=[c], hours=1)

        ctx, model = make_ctx(groups=[g], teachers=[t], classes=[c],
                               days=1, slots_per_day=3)
        cstr = BlockSlotTeacherConstraint(
            positions=[(0, 0)], target_id=1,
            priority=ConstraintPriority.HARD,
        )
        cstr.apply(ctx)
        # Activer l'assomption
        assert cstr.assumption_literal is not None
        model.AddAssumption(cstr.assumption_literal)

        model.Add(sum(ctx.assigned[1].values()) == 1)
        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        # Slot bloqué → forcément 0
        assert solver.Value(ctx.assigned[1][(0, 0)]) == 0

    def test_assumption_literal_enables_mus_extraction(self):
        """Pierre angulaire de la Phase 3 : sans assumption, MUS impossible."""
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        # 1 slot dispo, 1h à caser, MAIS on bloque ce slot → infaisable
        g = make_group(gid=1, teachers=[t], classes=[c], hours=1)

        ctx, model = make_ctx(groups=[g], teachers=[t], classes=[c],
                               days=1, slots_per_day=1)
        cstr = BlockSlotTeacherConstraint(
            positions=[(0, 0)], target_id=1, priority=ConstraintPriority.HARD,
        )
        cstr.apply(ctx)
        model.AddAssumption(cstr.assumption_literal)
        model.Add(sum(ctx.assigned[1].values()) == 1)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.INFEASIBLE
        # CP-SAT doit identifier l'assumption comme cause
        sufficient = solver.SufficientAssumptionsForInfeasibility()
        # Au moins notre literal doit en faire partie
        assert cstr.assumption_literal.Index() in sufficient


# ---------------------------------------------------------------------------
# BLOCK_SLOT_SCHOOL : tous les groupes touchés
# ---------------------------------------------------------------------------

class TestBlockSlotSchool:
    def test_blocks_all_groups(self):
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        g1 = make_group(gid=1, teachers=[t], classes=[c], hours=1)
        g2 = make_group(gid=2, teachers=[t], classes=[c], hours=1)

        ctx, model = make_ctx(groups=[g1, g2], teachers=[t], classes=[c],
                               days=1, slots_per_day=3)
        cstr = BlockSlotSchoolConstraint(
            positions=[(0, 0)], target_id=None, priority=ConstraintPriority.HARD,
        )
        cstr.apply(ctx)
        model.AddAssumption(cstr.assumption_literal)
        model.Add(sum(ctx.assigned[1].values()) == 1)
        model.Add(sum(ctx.assigned[2].values()) == 1)
        # avec teacher_no_overlap, 2 groupes ne peuvent pas être au même slot
        TeacherNoOverlapConstraint().apply(ctx)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        # Aucun groupe sur (0,0)
        assert solver.Value(ctx.assigned[1][(0, 0)]) == 0
        assert solver.Value(ctx.assigned[2][(0, 0)]) == 0


# ---------------------------------------------------------------------------
# VOLUMES
# ---------------------------------------------------------------------------

class TestGroupHoursPerWeek:
    def test_exact_hours_enforced(self):
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        g = make_group(gid=1, teachers=[t], classes=[c], hours=3)

        ctx, model = make_ctx(groups=[g], teachers=[t], classes=[c], days=2, slots_per_day=3)
        cstr = GroupHoursPerWeekConstraint(group_id=1, hours=3,
                                            priority=ConstraintPriority.HARD)
        cstr.apply(ctx)
        model.AddAssumption(cstr.assumption_literal)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        total = sum(solver.Value(v) for v in ctx.assigned[1].values())
        assert total == 3


class TestTeacherMaxHoursDay:
    def test_caps_at_max(self):
        t = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="B", languages=["fr"])
        c = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        g = make_group(gid=1, teachers=[t], classes=[c], hours=4)

        # 2 jours × 4 slots, max 2/jour
        ctx, model = make_ctx(groups=[g], teachers=[t], classes=[c], days=2, slots_per_day=4)
        cstr = TeacherMaxHoursDayConstraint(
            teacher_id=1, max_hours=2, priority=ConstraintPriority.HARD,
        )
        cstr.apply(ctx)
        model.AddAssumption(cstr.assumption_literal)
        model.Add(sum(ctx.assigned[1].values()) == 4)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        # Vérifier : jamais plus de 2/jour
        for day in [0, 1]:
            day_total = sum(
                solver.Value(ctx.assigned[1][(day, s)])
                for s in range(4)
            )
            assert day_total <= 2


# ---------------------------------------------------------------------------
# Test d'intégration : un mini cas avec plusieurs contraintes
# ---------------------------------------------------------------------------

class TestMiniIntegration:
    def test_full_mini_solve(self):
        """Mini cas réaliste :
        - 2 profs, 2 classes, 1 matière
        - 2 groupes (1 par classe), 2h chacun
        - Structurelles + hours_per_week
        - Le solveur doit placer les 4 heures sans conflits.
        """
        t1 = Teacher(id=1, school_id=1, code="T1", first_name="A", last_name="A", languages=["he"])
        t2 = Teacher(id=2, school_id=1, code="T2", first_name="B", last_name="B", languages=["he"])
        c1 = Class(id=1, school_id=1, grade_id=1, code="C1", name="C1", student_count=20)
        c2 = Class(id=2, school_id=1, grade_id=1, code="C2", name="C2", student_count=20)
        g1 = make_group(gid=1, teachers=[t1], classes=[c1], hours=2)
        g2 = make_group(gid=2, teachers=[t2], classes=[c2], hours=2)

        ctx, model = make_ctx(groups=[g1, g2], teachers=[t1, t2], classes=[c1, c2],
                               days=2, slots_per_day=3)
        TeacherNoOverlapConstraint().apply(ctx)
        ClassNoOverlapConstraint().apply(ctx)
        for cstr in [
            GroupHoursPerWeekConstraint(group_id=1, hours=2),
            GroupHoursPerWeekConstraint(group_id=2, hours=2),
        ]:
            cstr.apply(ctx)
            model.AddAssumption(cstr.assumption_literal)

        status, solver = solve_and_get(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        # Chaque groupe a bien ses 2h
        for g_id in [1, 2]:
            assert sum(solver.Value(v) for v in ctx.assigned[g_id].values()) == 2
