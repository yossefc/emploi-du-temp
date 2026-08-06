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
        """Résolution en DEUX PHASES.

        Phase 1 — contraintes EN DUR (pas d'assumptions) : CP-SAT est
        beaucoup plus rapide sans littéraux d'assomption (mesuré ×10+ sur
        l'école réelle : FEASIBLE en 4 min là où le mode assumptions timeout).

        Phase 2 — uniquement si INFEASIBLE : on reconstruit le modèle avec
        les assumptions pour extraire le MUS (dialogue de conflit).
        """
        disabled = set(disabled_constraint_ids)

        # Phase 1 : rapide, en dur
        ctx, solver, status, _ = self._build_and_solve(
            disabled, max_time_seconds, use_assumptions=False,
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._save_solution(
                ctx, solver, schedule_name, list(disabled), solver.WallTime()
            )
        if status != cp_model.INFEASIBLE:
            return SolveTimeout(solver_time_seconds=solver.WallTime())

        # Phase 2 : diagnostic MUS avec assumptions
        mus_budget = max(30.0, max_time_seconds)
        ctx2, solver2, status2, applied2 = self._build_and_solve(
            disabled, mus_budget, use_assumptions=True,
        )
        if status2 == cp_model.INFEASIBLE:
            return self._build_conflict(ctx2, solver2, applied2, solver2.WallTime())
        if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Rare (budget différent) : on a finalement trouvé une solution.
            return self._save_solution(
                ctx2, solver2, schedule_name, list(disabled), solver2.WallTime()
            )
        return SolveTimeout(solver_time_seconds=solver2.WallTime())

    def _build_and_solve(
        self,
        disabled: set[int],
        max_time_seconds: float,
        *,
        use_assumptions: bool,
    ):
        """Construit le modèle complet et le résout. Retourne (ctx, solver, status, applied)."""
        self._literal_index_to_applied = {}
        ctx = self._load_data()
        self._create_variables(ctx)

        applied = self._apply_constraints(
            ctx, disabled=disabled, use_assumptions=use_assumptions
        )

        # Objectifs qualité automatiques (école israélienne)
        self._apply_quality_objectives(ctx)
        if ctx.soft_penalty_terms:
            ctx.model.Minimize(sum(expr * weight for expr, weight in ctx.soft_penalty_terms))

        # Warm start : le planning précédent guide la recherche (stabilité + vitesse)
        self._add_warm_start_hints(ctx)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.num_search_workers = 8
        status = solver.Solve(ctx.model)
        return ctx, solver, status, applied

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
        """Variables de décision.

        Salles : en Israël chaque classe a sa כיתת אם (salle fixe) — l'export
        iscool n'affiche même pas les salles. On ne crée donc des variables de
        salle QUE pour les matières exigeant un type spécial (labo, gym…).
        Les autres cours héritent implicitement de la salle de classe
        (room_id NULL dans ScheduleEntry). Sur AMIT ça élimine ~450 000
        variables du modèle.
        """
        positions = ctx.all_active_positions()
        for g in ctx.groups:
            ctx.assigned[g.id] = {}
            for (d, s) in positions:
                ctx.assigned[g.id][(d, s)] = ctx.model.NewBoolVar(f"x_g{g.id}_d{d}_s{s}")

            # Variables de salle : seulement si la matière exige un type spécial
            if not g.subject.required_room_type:
                continue
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

    # ---- Objectifs qualité (école israélienne) ----
    def _apply_quality_objectives(self, ctx: SolverContext) -> None:
        """Ajoute les pénalités SOFT toujours actives qui font la différence
        entre un planning « légal » et un planning utilisable :

        1. Compacité classe (אין חלונות) : un créneau vide entre deux cours
           d'une même classe le même jour coûte cher (poids 40). En Israël un
           élève ne peut pas rester sans cours au milieu de la journée.
        2. Étalement matière : le même group 2× le même jour coûte (poids 8)
           — un cours de 4h/sem doit s'étaler sur 4 jours, pas 2. Si une
           contrainte HARD subject_consecutive_hours existe, elle gagne
           (la pénalité devient un coût constant sans effet sur l'optimum).
        """
        WEIGHT_GAP = 40
        WEIGHT_DOUBLE = 8

        # --- 1. Compacité par classe ---
        for cls in ctx.classes:
            group_ids = ctx.groups_of_class(cls.id)
            if not group_ids:
                continue
            # Représentants dédupliqués par cohorte (même logique que ClassNoOverlap)
            by_cohort: dict[int | None, list[int]] = {}
            for g_id in group_ids:
                g = ctx.group(g_id)
                by_cohort.setdefault(g.parallel_cohort_id, []).append(g_id)

            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                if len(slots) < 3:
                    continue
                # busy[s] = OR(cours de la classe à ce créneau)
                busy: dict[int, cp_model.IntVar] = {}
                for s in slots:
                    reps = []
                    for cohort_id, gs in by_cohort.items():
                        if cohort_id is None:
                            reps.extend(ctx.assigned[g][(day, s)] for g in gs)
                        else:
                            g_env = max(gs, key=lambda gid: ctx.group(gid).hours_per_week)
                            reps.append(ctx.assigned[g_env][(day, s)])
                    b = ctx.model.NewBoolVar(f"busy_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(b, reps)
                    busy[s] = b

                # before[i] = classe a eu cours à un créneau <= i
                # after[i]  = classe a cours à un créneau >= i
                before: dict[int, cp_model.IntVar] = {}
                after: dict[int, cp_model.IntVar] = {}
                prev = None
                for s in slots:
                    v = ctx.model.NewBoolVar(f"bef_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if prev is None else [busy[s], prev])
                    before[s] = v
                    prev = v
                nxt = None
                for s in reversed(slots):
                    v = ctx.model.NewBoolVar(f"aft_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if nxt is None else [busy[s], nxt])
                    after[s] = v
                    nxt = v

                # gap[i] = 1 ssi cours avant ET cours après ET créneau vide
                # (linéarisé : gap >= before[i-1] + after[i+1] - busy[i] - 1 ;
                #  la minimisation pousse gap à 0 quand c'est permis)
                for idx in range(1, len(slots) - 1):
                    s = slots[idx]
                    gap = ctx.model.NewBoolVar(f"gap_c{cls.id}_d{day}_s{s}")
                    ctx.model.Add(
                        gap >= before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] - 1
                    )
                    ctx.soft_penalty_terms.append((gap, WEIGHT_GAP))

        # --- 2. Étalement matière (max 1 cours/jour par group si évitable) ---
        n_days = len(ctx.active_days())
        for g in ctx.groups:
            if g.hours_per_week <= 1 or n_days == 0:
                continue
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                day_total = sum(ctx.assigned[g.id][(day, s)] for s in slots)
                excess = ctx.model.NewIntVar(0, len(slots), f"dbl_g{g.id}_d{day}")
                ctx.model.Add(excess >= day_total - 1)
                ctx.soft_penalty_terms.append((excess, WEIGHT_DOUBLE))

    # ---- Warm start ----
    def _add_warm_start_hints(self, ctx: SolverContext) -> None:
        """Indice de départ = le planning le plus récent de cette école."""
        prev = (
            self.db.query(Schedule)
            .filter(Schedule.school_id == self.school_id)
            .order_by(Schedule.id.desc())
            .first()
        )
        if prev is None:
            return
        entries = self.db.query(ScheduleEntry).filter_by(schedule_id=prev.id).all()
        for e in entries:
            var_map = ctx.assigned.get(e.group_id)
            if var_map and (e.day_of_week, e.slot_index) in var_map:
                ctx.model.AddHint(var_map[(e.day_of_week, e.slot_index)], 1)

    # ---- Application des contraintes ----
    def _apply_constraints(
        self,
        ctx: SolverContext,
        disabled: set[int],
        use_assumptions: bool = True,
    ) -> list[_AppliedConstraint]:
        applied: list[_AppliedConstraint] = []

        def register(inst: BaseConstraint, entry: _AppliedConstraint) -> None:
            """Assumption (phase MUS) ou littéral forcé vrai (phase rapide)."""
            lit = inst.assumption_literal
            if lit is None:
                return
            if use_assumptions:
                ctx.model.AddAssumption(lit)
                self._literal_index_to_applied[lit.Index()] = entry
            else:
                ctx.model.Add(lit == 1)

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
            register(inst, applied[-1])

        # 3. Préflight : qualification prof
        qualif = TeacherQualifiedForSubjectConstraint()
        qualif.apply(ctx)
        applied.append(_AppliedConstraint(instance=qualif, db_id=None))
        register(qualif, applied[-1])

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
            register(inst, applied[-1])

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
                explanation=ac.instance.explain(ctx),
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
        quality: dict = {"solver_time_seconds": elapsed}
        if ctx.soft_penalty_terms:
            # Somme pondérée des pénalités (0 = planning parfait côté SOFT)
            quality["soft_penalty"] = int(solver.ObjectiveValue())
        sched = Schedule(
            school_id=self.school_id,
            name=schedule_name,
            status=ScheduleStatus.DRAFT,
            generated_at=datetime.now(timezone.utc),
            relaxed_constraints_report={"disabled_constraint_ids": disabled},
            quality_score=quality,
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
