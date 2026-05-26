"""Contraintes STRUCTURELLES — toujours actives, jamais relaxables.

Sans elles, le modèle produit des solutions non-cohérentes (deux cours
en même temps pour la même classe, etc.). Pas stockées en DB, pas
exposées à l'utilisateur. Ajoutées automatiquement par l'engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import ConstraintPriority
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class _StructuralConstraint(BaseConstraint):
    """Marker base : pas de from_db, pas d'assumption."""
    def __init__(self) -> None:
        super().__init__(priority=ConstraintPriority.HARD)

    @classmethod
    def _build_from_params(cls, **kwargs):  # type: ignore[override]
        raise NotImplementedError("Contraintes structurelles non instanciables depuis la DB.")


class TeacherNoOverlapConstraint(_StructuralConstraint):
    """Un prof ne peut être qu'à un endroit à un instant."""
    constraint_type = "teacher_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for teacher in ctx.teachers:
            group_ids = ctx.groups_of_teacher(teacher.id)
            if len(group_ids) < 2:
                continue
            for day, slot in ctx.all_active_positions():
                vars_ = [ctx.assigned[g_id][(day, slot)] for g_id in group_ids]
                ctx.model.Add(sum(vars_) <= 1)

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות מורה (מבני)",
            title_fr="Cohérence prof (structurelle)",
            detail_he="מורה לא יכול ללמד שני שיעורים במקביל.",
            detail_fr="Un même enseignant ne peut donner qu'un cours à la fois.",
            origin="מערכת",
        )


class ClassNoOverlapConstraint(_StructuralConstraint):
    """Une classe ne suit qu'un cours à la fois.

    Subtilité barrette : si une classe contribue à PLUSIEURS Groups d'une
    même ParallelCohort, on compte la cohorte comme un seul représentant
    (les autres Groups sont déjà forcés égaux par PARALLEL_COHORT_SAME_SLOT).
    """
    constraint_type = "class_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for cls in ctx.classes:
            group_ids = ctx.groups_of_class(cls.id)
            if len(group_ids) < 2:
                continue
            by_cohort: dict[int | None, list[int]] = {}
            for g_id in group_ids:
                g = ctx.group(g_id)
                by_cohort.setdefault(g.parallel_cohort_id, []).append(g_id)

            for day, slot in ctx.all_active_positions():
                reps = []
                for cohort_id, gs in by_cohort.items():
                    if cohort_id is None:
                        reps.extend(ctx.assigned[g][(day, slot)] for g in gs)
                    else:
                        reps.append(ctx.assigned[gs[0]][(day, slot)])
                if len(reps) >= 2:
                    ctx.model.Add(sum(reps) <= 1)

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות כיתה (מבני)",
            title_fr="Cohérence classe (structurelle)",
            detail_he="כיתה לא יכולה להשתתף בשני שיעורים במקביל.",
            detail_fr="Une classe ne peut suivre qu'un cours à la fois.",
            origin="מערכת",
        )


class RoomNoOverlapConstraint(_StructuralConstraint):
    """Une salle accueille au plus une classe à la fois."""
    constraint_type = "room_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for room in ctx.rooms:
            for day, slot in ctx.all_active_positions():
                vars_ = []
                for g_id, slot_map in ctx.room_used.items():
                    if (day, slot) in slot_map and room.id in slot_map[(day, slot)]:
                        vars_.append(slot_map[(day, slot)][room.id])
                if len(vars_) >= 2:
                    ctx.model.Add(sum(vars_) <= 1)

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות חדר (מבני)",
            title_fr="Cohérence salle (structurelle)",
            detail_he="חדר יכול לארח רק שיעור אחד בכל זמן.",
            detail_fr="Une salle n'accueille qu'un cours à la fois.",
            origin="מערכת",
        )


class ParallelCohortSameSlotConstraint(_StructuralConstraint):
    """Tous les Groups d'une ParallelCohort doivent être au même créneau."""
    constraint_type = "parallel_cohort_same_slot"

    def apply(self, ctx: "SolverContext") -> None:
        for cohort in ctx.parallel_cohorts:
            group_ids = [g.id for g in cohort.groups]
            if len(group_ids) < 2:
                continue
            ref = group_ids[0]
            for other in group_ids[1:]:
                for day, slot in ctx.all_active_positions():
                    ctx.model.Add(ctx.assigned[ref][(day, slot)] == ctx.assigned[other][(day, slot)])

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="הקבצות מקבילות (מבני)",
            title_fr="Barrettes parallèles (structurelle)",
            detail_he="כל קבוצות באותה הקבצה חייבות להיות באותו זמן.",
            detail_fr="Les groupes d'une même barrette doivent être au même créneau.",
            origin="מערכת",
        )
