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

# Matières exemptées de la règle « 2h consécutives » : elles se donnent
# naturellement en heures isolées réparties dans la semaine.
BLOCK_EXEMPT_SUBJECTS = {
    'חנ"ג',          # sport
    "מנטורים",       # mentors
    "שיח בוקר",      # échange du matin
    "חינוך",         # heure de vie de classe
    'של"ח',          # sortie / terrain
    "תפילה",         # prière
    "כישורי חיים",   # compétences de vie
}


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

        # Phase 1a : mode STRICT — les exigences absolues de l'école (aucun
        # trou élève, aucune matière éclatée) sont des contraintes dures.
        ctx, solver, status, _ = self._build_and_solve(
            disabled, max_time_seconds * 0.6, use_assumptions=False, strict=True,
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._save_solution(
                ctx, solver, schedule_name, list(disabled), solver.WallTime(),
                strict=True,
            )

        # Phase 1b : mode souple — ces exigences redeviennent des pénalités.
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
        strict: bool = False,
    ):
        """Construit le modèle complet et le résout. Retourne (ctx, solver, status, applied)."""
        self._literal_index_to_applied = {}
        ctx = self._load_data()
        self._create_variables(ctx)

        applied = self._apply_constraints(
            ctx, disabled=disabled, use_assumptions=use_assumptions
        )

        # Objectifs qualité automatiques (école israélienne)
        self._apply_quality_objectives(ctx, strict=strict)
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
    def _apply_quality_objectives(self, ctx: SolverContext, strict: bool = False) -> None:
        """Ajoute les pénalités SOFT toujours actives qui font la différence
        entre un planning « légal » et un planning utilisable :

        1. Journée d'une classe = bloc continu qui commence à P1 et va au
           moins jusqu'à P6 (règle de l'école) :
             - aucun trou entre deux cours              → poids 100
             - la journée démarre bien à la 1re période → poids 90
             - elle ne s'arrête pas avant la 6e         → poids 70
        2. Blocs de 2h (demande de l'école) : une matière présente 2× dans la
           même journée doit l'être en heures CONSÉCUTIVES, jamais éparpillée
           (1h le matin + 1h l'après-midi est interdit). Concrètement :
             - au plus UN bloc contigu par (group, jour)      → poids 80
             - au plus 2h par jour (pas de bloc de 3h+)       → poids 40
             - viser ⌈h/2⌉ jours (donc des paires, pas des 1h)→ poids 15
           Exceptions (`BLOCK_EXEMPT_SUBJECTS` + cours ≤ 2h/sem) : sport,
           mentors, heure de vie… → au contraire étalés 1h/jour (poids 8).
        3. Trous profs : un créneau vide entre deux cours d'un prof le même
           jour coûte (poids 6) — « pas trop de trous pour les profs », mais
           toujours subordonné à la compacité des classes.

        `strict=True` : les deux exigences absolues de l'école (aucun trou
        élève, aucune matière éclatée dans la journée) deviennent des
        contraintes DURES au lieu de pénalités. Le solveur ne peut alors plus
        « acheter » une violation, et l'espace de recherche se réduit
        fortement. L'appelant retombe sur strict=False si c'est infaisable.
        """
        WEIGHT_GAP = 100
        WEIGHT_DAY_START = 90    # classe qui ne commence pas à P1
        WEIGHT_DAY_END = 70      # classe qui termine avant P6
        WEIGHT_SPLIT = 80        # matière éclatée dans la journée
        WEIGHT_LONG_BLOCK = 40   # plus de 2h d'affilée
        WEIGHT_DAY_SPREAD = 30   # 1h isolée au lieu d'une paire
        WEIGHT_DOUBLE = 8        # doublement des matières exemptées
        WEIGHT_TEACHER_GAP = 6
        MIN_END_SLOT = 5         # index de P6 : la journée va au moins jusque-là

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
                    if strict:
                        # Aucun trou toléré : cours avant + cours après ⇒ occupé
                        ctx.model.Add(
                            before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] <= 1
                        )
                        continue
                    gap = ctx.model.NewBoolVar(f"gap_c{cls.id}_d{day}_s{s}")
                    ctx.model.Add(
                        gap >= before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] - 1
                    )
                    ctx.soft_penalty_terms.append((gap, WEIGHT_GAP))

                # Amplitude de journée : une classe qui a cours ce jour-là
                # commence à P1 et ne termine pas avant P6 (règle de l'école).
                day_active = ctx.model.NewBoolVar(f"dayon_c{cls.id}_d{day}")
                ctx.model.AddMaxEquality(day_active, list(busy.values()))
                first_slot = slots[0]
                last_required = slots[MIN_END_SLOT] if len(slots) > MIN_END_SLOT else None
                if strict:
                    ctx.model.Add(busy[first_slot] == day_active)
                    if last_required is not None:
                        ctx.model.Add(busy[last_required] >= day_active)
                else:
                    late = ctx.model.NewBoolVar(f"late_c{cls.id}_d{day}")
                    ctx.model.Add(late >= day_active - busy[first_slot])
                    ctx.soft_penalty_terms.append((late, WEIGHT_DAY_START))
                    if last_required is not None:
                        early = ctx.model.NewBoolVar(f"early_c{cls.id}_d{day}")
                        ctx.model.Add(early >= day_active - busy[last_required])
                        ctx.soft_penalty_terms.append((early, WEIGHT_DAY_END))

        # --- 2. Blocs de 2h consécutives (ou étalement pour les exemptées) ---
        days_list = ctx.active_days()
        n_days = len(days_list)
        for g in ctx.groups:
            if g.hours_per_week <= 1 or n_days == 0:
                continue
            subject_he = (g.subject.name_he or "").strip()
            exempt = subject_he in BLOCK_EXEMPT_SUBJECTS or g.hours_per_week <= 2

            day_used_vars = []
            for day in days_list:
                slots = ctx.active_slots(day)
                if not slots:
                    continue
                day_total = sum(ctx.assigned[g.id][(day, s)] for s in slots)

                if exempt:
                    # Matières hors blocs : au plus 1h/jour, réparties.
                    excess = ctx.model.NewIntVar(0, len(slots), f"dbl_g{g.id}_d{day}")
                    ctx.model.Add(excess >= day_total - 1)
                    ctx.soft_penalty_terms.append((excess, WEIGHT_DOUBLE))
                    continue

                # a) Compter les débuts de bloc : start[s] = 1 si le cours
                #    commence ici (actif en s, inactif au créneau précédent).
                starts = []
                prev = None
                for s in slots:
                    st = ctx.model.NewBoolVar(f"bstart_g{g.id}_d{day}_s{s}")
                    cur = ctx.assigned[g.id][(day, s)]
                    if prev is None:
                        ctx.model.Add(st >= cur)
                    else:
                        ctx.model.Add(st >= cur - prev)
                    starts.append(st)
                    prev = cur
                # >1 début = matière éclatée dans la journée
                if strict:
                    ctx.model.Add(sum(starts) <= 1)   # un seul bloc, point
                else:
                    split = ctx.model.NewIntVar(0, len(slots), f"bsplit_g{g.id}_d{day}")
                    ctx.model.Add(split >= sum(starts) - 1)
                    ctx.soft_penalty_terms.append((split, WEIGHT_SPLIT))

                # b) Pas plus de 2h d'affilée
                over = ctx.model.NewIntVar(0, len(slots), f"blong_g{g.id}_d{day}")
                ctx.model.Add(over >= day_total - 2)
                ctx.soft_penalty_terms.append((over, WEIGHT_LONG_BLOCK))

                # c) Jour utilisé ? (pour viser des paires plutôt que des 1h)
                used = ctx.model.NewBoolVar(f"bused_g{g.id}_d{day}")
                ctx.model.Add(day_total <= len(slots) * used)
                ctx.model.Add(day_total >= used)
                day_used_vars.append(used)

            # d) Nombre de jours ≈ ⌈h/2⌉ : au-delà, ce sont des heures isolées.
            if day_used_vars:
                target_days = (g.hours_per_week + 1) // 2
                extra_days = ctx.model.NewIntVar(0, n_days, f"bdays_g{g.id}")
                ctx.model.Add(extra_days >= sum(day_used_vars) - target_days)
                ctx.soft_penalty_terms.append((extra_days, WEIGHT_DAY_SPREAD))

        # --- 3. Trous profs (même chaîne before/after que la compacité classe) ---
        for teacher in ctx.teachers:
            group_ids = ctx.groups_of_teacher(teacher.id)
            if len(group_ids) == 0:
                continue
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                if len(slots) < 3:
                    continue
                busy: dict[int, cp_model.IntVar] = {}
                for s in slots:
                    b = ctx.model.NewBoolVar(f"tbusy_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(
                        b, [ctx.assigned[g][(day, s)] for g in group_ids]
                    )
                    busy[s] = b
                before: dict[int, cp_model.IntVar] = {}
                after: dict[int, cp_model.IntVar] = {}
                prev = None
                for s in slots:
                    v = ctx.model.NewBoolVar(f"tbef_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if prev is None else [busy[s], prev])
                    before[s] = v
                    prev = v
                nxt = None
                for s in reversed(slots):
                    v = ctx.model.NewBoolVar(f"taft_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if nxt is None else [busy[s], nxt])
                    after[s] = v
                    nxt = v
                for idx in range(1, len(slots) - 1):
                    s = slots[idx]
                    gap = ctx.model.NewBoolVar(f"tgap_t{teacher.id}_d{day}_s{s}")
                    ctx.model.Add(
                        gap >= before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] - 1
                    )
                    ctx.soft_penalty_terms.append((gap, WEIGHT_TEACHER_GAP))

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
        strict: bool = False,
    ) -> SolveSuccess:
        quality: dict = {"solver_time_seconds": elapsed, "strict_quality": strict}
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
