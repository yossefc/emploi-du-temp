"""TimetableEngine — orchestrateur du solveur.

Flow :
1. Charger les données de l'école (groups, teachers, classes, rooms, time_slots, cohorts)
2. Charger les contraintes actives (DB) + désactiver celles passées en `disabled_constraint_ids`
3. Construire le SolverContext + variables CP-SAT (assigned, room_used)
4. Appliquer contraintes structurelles + DB
5. Solve avec assumptions
6. Si INFEASIBLE → extraire MUS via SufficientAssumptionsForInfeasibility() → SolveConflict
7. Si FEASIBLE/OPTIMAL → écrire les ScheduleEntry → SolveSuccess

Contraintes implicites ajoutées par l'engine (pas dans la table DB) :
- 4 structurelles (TEACHER/CLASS/ROOM no-overlap, PARALLEL_COHORT same-slot)
- GROUP_HOURS_PER_WEEK pour chaque Group (basé sur Group.hours_per_week)
- TEACHER_QUALIFIED_FOR_SUBJECT (préflight)
- Room assignment : si assigned[g][d,s] = 1, exactement une room compatible utilisée
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional, Union

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.models import (
    Class,
    Constraint as DBConstraint,
    Group,
    ParallelCohort,
    Room,
    Schedule,
    ScheduleEntry,
    ScheduleStatus,
    School,
    Teacher,
    TimeSlot,
)
from app.solver.constraints import (
    STRUCTURAL_CONSTRAINTS,
    from_db as constraint_from_db,
)
from app.solver.constraints.assignment import TeacherQualifiedForSubjectConstraint
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation
from app.solver.constraints.volume import GroupHoursPerWeekConstraint
from app.solver.context import SolverContext


# ---------------------------------------------------------------------------
# Résultats
# ---------------------------------------------------------------------------

@dataclass
class ConflictItem:
    """Une contrainte identifiée comme causant l'infaisabilité."""
    constraint_id: Optional[int]      # None si contrainte système (qualif, hours_per_week implicite)
    constraint_type: str
    explanation: ConstraintExplanation


@dataclass
class SolveConflict:
    """Résultat quand le solveur est INFEASIBLE. Contient le sous-ensemble
    minimal de contraintes en conflit, prêt à être présenté à l'utilisateur."""
    conflicts: list[ConflictItem]
    solver_time_seconds: float

    @property
    def is_success(self) -> bool:
        return False


@dataclass
class SolveSuccess:
    """Résultat quand un planning a été généré."""
    schedule_id: int
    placed_entries: int
    relaxed_constraint_ids: list[int]
    solver_time_seconds: float

    @property
    def is_success(self) -> bool:
        return True


SolveResult = Union[SolveSuccess, SolveConflict]


@dataclass
class SolveTimeout:
    """Cas dégénéré : ni faisable ni prouvé infaisable dans le temps imparti."""
    solver_time_seconds: float
    is_success: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

@dataclass
class _AppliedConstraint:
    """Track interne : contrainte appliquée + son origine pour le MUS."""
    instance: BaseConstraint
    db_id: Optional[int]               # None si système


class TimetableEngine:
    def __init__(self, db: Session, school_id: int):
        self.db = db
        self.school_id = school_id
        # Map index de literal CP-SAT → metadata (pour décoder le MUS)
        self._literal_index_to_applied: dict[int, _AppliedConstraint] = {}

    # ---- API publique ----
    def generate(
        self,
        *,
        schedule_name: str = "Généré",
        disabled_constraint_ids: Iterable[int] = (),
        max_time_seconds: float = 30.0,
    ) -> SolveResult | SolveTimeout:
        disabled = set(disabled_constraint_ids)
        ctx = self._load_data()
        self._create_variables(ctx)

        applied = self._apply_constraints(ctx, disabled=disabled)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        status = solver.Solve(ctx.model)
        elapsed = solver.WallTime()

        if status == cp_model.INFEASIBLE:
            return self._build_conflict(ctx, solver, applied, elapsed)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._save_solution(
                ctx, solver, schedule_name, list(disabled), elapsed
            )

        return SolveTimeout(solver_time_seconds=elapsed)

    # ---- Chargement données ----
    def _load_data(self) -> SolverContext:
        school = self.db.query(School).filter_by(id=self.school_id).one()
        groups = self.db.query(Group).filter_by(school_id=self.school_id).all()
        teachers = self.db.query(Teacher).filter_by(school_id=self.school_id, is_active=True).all()
        classes = self.db.query(Class).filter_by(school_id=self.school_id).all()
        rooms = self.db.query(Room).filter_by(school_id=self.school_id, is_active=True).all()
        time_slots = self.db.query(TimeSlot).filter_by(school_id=self.school_id).all()
        cohorts = self.db.query(ParallelCohort).filter_by(school_id=self.school_id).all()

        ctx = SolverContext(
            model=cp_model.CpModel(),
            school=school,
            groups=groups,
            teachers=teachers,
            classes=classes,
            rooms=rooms,
            time_slots=time_slots,
            parallel_cohorts=cohorts,
        )
        ctx.build_caches()
        return ctx

    # ---- Variables CP-SAT ----
    def _create_variables(self, ctx: SolverContext) -> None:
        positions = ctx.all_active_positions()
        for g in ctx.groups:
            ctx.assigned[g.id] = {}
            for (d, s) in positions:
                ctx.assigned[g.id][(d, s)] = ctx.model.NewBoolVar(f"x_g{g.id}_d{d}_s{s}")

            # Variables d'assignation de salle (uniquement pour salles compatibles)
            compatible = ctx.compatible_rooms(g.id)
            if compatible:
                ctx.room_used[g.id] = {}
                for (d, s) in positions:
                    ctx.room_used[g.id][(d, s)] = {
                        r.id: ctx.model.NewBoolVar(f"r_g{g.id}_d{d}_s{s}_r{r.id}")
                        for r in compatible
                    }
                    # Si assigned, exactement 1 salle utilisée ; sinon, aucune.
                    ctx.model.Add(
                        sum(ctx.room_used[g.id][(d, s)].values())
                        == ctx.assigned[g.id][(d, s)]
                    )

    # ---- Application des contraintes ----
    def _apply_constraints(
        self,
        ctx: SolverContext,
        disabled: set[int],
    ) -> list[_AppliedConstraint]:
        applied: list[_AppliedConstraint] = []

        # 1. Structurelles (toujours actives, jamais relaxables)
        for cls in STRUCTURAL_CONSTRAINTS:
            inst = cls()
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=None))

        # 2. Système implicite : volume horaire de chaque Group
        for g in ctx.groups:
            inst = GroupHoursPerWeekConstraint(
                group_id=g.id, hours=g.hours_per_week,
                origin_description=f"Volume défini sur le Group « {g.label} »",
            )
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=None))
            if inst.assumption_literal is not None:
                ctx.model.AddAssumption(inst.assumption_literal)
                self._literal_index_to_applied[inst.assumption_literal.Index()] = applied[-1]

        # 3. Préflight : qualification prof
        qualif = TeacherQualifiedForSubjectConstraint()
        qualif.apply(ctx)
        applied.append(_AppliedConstraint(instance=qualif, db_id=None))
        if qualif.assumption_literal is not None:
            ctx.model.AddAssumption(qualif.assumption_literal)
            self._literal_index_to_applied[qualif.assumption_literal.Index()] = applied[-1]

        # 4. Contraintes DB actives
        db_constraints = (
            self.db.query(DBConstraint)
            .filter(DBConstraint.school_id == self.school_id, DBConstraint.is_active.is_(True))
            .all()
        )
        for dbc in db_constraints:
            if dbc.id in disabled:
                continue
            try:
                inst = constraint_from_db(dbc)
            except ValueError:
                # Type non implémenté (ex: préférence v2) → on ignore
                continue
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=dbc.id))
            if inst.assumption_literal is not None:
                ctx.model.AddAssumption(inst.assumption_literal)
                self._literal_index_to_applied[inst.assumption_literal.Index()] = applied[-1]

        return applied

    # ---- INFEASIBLE → MUS ----
    def _build_conflict(
        self,
        ctx: SolverContext,
        solver: cp_model.CpSolver,
        applied: list[_AppliedConstraint],
        elapsed: float,
    ) -> SolveConflict:
        mus_indices = solver.SufficientAssumptionsForInfeasibility() or []
        conflicts: list[ConflictItem] = []
        seen: set[int] = set()

        for idx in mus_indices:
            ac = self._literal_index_to_applied.get(idx)
            if ac is None or id(ac) in seen:
                continue
            seen.add(id(ac))
            conflicts.append(ConflictItem(
                constraint_id=ac.db_id,
                constraint_type=ac.instance.constraint_type,
                explanation=ac.instance.explain(ctx, lang="fr"),
            ))

        return SolveConflict(conflicts=conflicts, solver_time_seconds=elapsed)

    # ---- FEASIBLE → écrire ScheduleEntry ----
    def _save_solution(
        self,
        ctx: SolverContext,
        solver: cp_model.CpSolver,
        schedule_name: str,
        disabled: list[int],
        elapsed: float,
    ) -> SolveSuccess:
        sched = Schedule(
            school_id=self.school_id,
            name=schedule_name,
            status=ScheduleStatus.DRAFT,
            generated_at=datetime.now(timezone.utc),
            relaxed_constraints_report={"disabled_constraint_ids": disabled},
            quality_score={"solver_time_seconds": elapsed},
        )
        self.db.add(sched)
        self.db.flush()

        count = 0
        for g_id, slot_map in ctx.assigned.items():
            for (d, s), var in slot_map.items():
                if solver.Value(var) != 1:
                    continue
                # Salle assignée (s'il y a des salles candidates)
                room_id = None
                if g_id in ctx.room_used:
                    for r_id, rvar in ctx.room_used[g_id][(d, s)].items():
                        if solver.Value(rvar) == 1:
                            room_id = r_id
                            break
                entry = ScheduleEntry(
                    schedule_id=sched.id, group_id=g_id, room_id=room_id,
                    day_of_week=d, slot_index=s,
                )
                self.db.add(entry)
                count += 1

        self.db.commit()
        self.db.refresh(sched)
        return SolveSuccess(
            schedule_id=sched.id,
            placed_entries=count,
            relaxed_constraint_ids=disabled,
            solver_time_seconds=elapsed,
        )
