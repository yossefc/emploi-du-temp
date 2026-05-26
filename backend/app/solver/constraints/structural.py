"""Contraintes STRUCTURELLES — toujours actives, jamais relaxables.

Sans elles, le modèle produit des solutions non-cohérentes (deux cours
en même temps pour la même classe, etc.). Pas stockées en DB, pas
exposées à l'utilisateur. Ajoutées automatiquement par l'engine.

Ces classes n'ont pas de `from_db` car elles ne viennent pas de la table
`constraints`. Elles sont instanciées directement par l'engine et n'utilisent
PAS d'assumption literal (non relaxables).
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

    def explain(self, ctx, lang="fr") -> ConstraintExplanation:
        return ConstraintExplanation(
            title="Cohérence prof (structurelle)",
            detail="Un même enseignant ne peut donner qu'un cours à la fois.",
            origin="système (non modifiable)",
        )


class ClassNoOverlapConstraint(_StructuralConstraint):
    """Une classe ne suit qu'un cours à la fois.

    Subtilité barrette : si une classe contribue à PLUSIEURS Groups d'une
    même ParallelCohort (cas Math 5/4/3 yehidot sur une שכבה), les élèves
    sont **dispatchés** entre les groupes — c'est UNE situation valide pour
    la classe (tous ses élèves ont math, simplement à des niveaux différents).

    On compte donc une cohorte comme **un seul représentant** dans le calcul
    de "non-chevauchement" (les autres Groups de la cohorte sont déjà forcés
    égaux par PARALLEL_COHORT_SAME_SLOT).

    Sans cette finesse, ClassNoOverlap interdirait toute barrette dont les
    Groups partagent les source_classes — cas iscool standard.
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
                        # 1 seul représentant par cohorte (égalité garantie par PARALLEL_COHORT_SAME_SLOT)
                        reps.append(ctx.assigned[gs[0]][(day, slot)])
                if len(reps) >= 2:
                    ctx.model.Add(sum(reps) <= 1)

    def explain(self, ctx, lang="fr") -> ConstraintExplanation:
        return ConstraintExplanation(
            title="Cohérence classe (structurelle)",
            detail="Une classe ne peut suivre qu'un cours à la fois.",
            origin="système (non modifiable)",
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

    def explain(self, ctx, lang="fr") -> ConstraintExplanation:
        return ConstraintExplanation(
            title="Cohérence salle (structurelle)",
            detail="Une salle n'accueille qu'un cours à la fois.",
            origin="système (non modifiable)",
        )


class ParallelCohortSameSlotConstraint(_StructuralConstraint):
    """Tous les Groups d'une ParallelCohort doivent être au même créneau.

    Implémenté en forçant l'égalité de `assigned[g1] == assigned[g2]` pour
    chaque paire (g1, g2) dans la cohorte, sur chaque (day, slot).
    """
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

    def explain(self, ctx, lang="fr") -> ConstraintExplanation:
        return ConstraintExplanation(
            title="Barrettes parallèles (structurelle)",
            detail="Les groupes d'une même barrette doivent être au même créneau.",
            origin="système (non modifiable)",
        )
