"""Contraintes de co-enseignement / coordination prof — bilingues.

TEACHERS_MUST_TEACH_TOGETHER : un ensemble de profs doivent enseigner aux
mêmes créneaux (tous présents ou tous absents). Cas d'usage AMIT :
- Prière du matin (TEFILA) supervisée par 2 profs ensemble
- Co-titularité d'une classe avec planning aligné
- Activité commune (sortie scolaire avec accompagnants)

NB : si vous voulez juste qu'UN cours soit co-enseigné par N profs, utilisez
simplement Group.teachers = [A, B] (déjà supporté).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import (
    BaseConstraint,
    ConstraintExplanation,
    Suggestion,
)

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class TeachersMustTeachTogetherConstraint(BaseConstraint):
    constraint_type = "teachers_must_teach_together"

    def __init__(self, *, teacher_ids: list[int], **kwargs):
        super().__init__(**kwargs)
        self.teacher_ids = teacher_ids

    def apply(self, ctx: "SolverContext") -> None:
        if len(self.teacher_ids) < 2:
            return

        lit = ctx.model.NewBoolVar(f"assum_teachers_together_{self.db_id or 'sys'}")
        self.assumption_literal = lit

        # Pour chaque (day, slot), forcer sum_groups(teacher_i) == sum_groups(teacher_j)
        # Comme TeacherNoOverlap garantit que chaque sum est 0 ou 1, ça veut dire :
        # tous les profs enseignent au même créneau, OU aucun.
        for day, slot in ctx.all_active_positions():
            sums = []
            for tid in self.teacher_ids:
                gids = ctx.groups_of_teacher(tid)
                if not gids:
                    sums.append(None)  # prof sans groups
                    continue
                expr = sum(ctx.assigned[g_id][(day, slot)] for g_id in gids)
                sums.append(expr)

            valid = [s for s in sums if s is not None]
            for i in range(len(valid) - 1):
                ctx.model.Add(valid[i] == valid[i + 1]).OnlyEnforceIf(lit)

    def explain(self, ctx) -> ConstraintExplanation:
        names = []
        for tid in self.teacher_ids:
            try:
                t = ctx.teacher(tid)
                names.append(t.full_name)
            except KeyError:
                names.append(f"#{tid}")
        joined = " + ".join(names)

        suggestions: list[Suggestion] = []
        if self.db_id:
            suggestions.append(Suggestion(
                kind="disable_constraint",
                title_he=f"בטל את האילוץ \"מורים יחד : {joined}\"",
                title_fr=f"Désactiver la contrainte « Profs ensemble : {joined} »",
                description_he="המורים יוכלו ללמד בנפרד.",
                description_fr="Les profs pourront enseigner indépendamment.",
                auto_action={
                    "verb": "patch_constraint",
                    "target_id": self.db_id,
                    "patch": {"is_active": False},
                },
            ))

        return ConstraintExplanation(
            title_he=f"מורים מלמדים יחד : {joined}",
            title_fr=f"Profs enseignent ensemble : {joined}",
            detail_he=(
                f"כל המורים האלה חייבים ללמד באותן משבצות זמן "
                f"(כולם נוכחים או אף אחד)."
            ),
            detail_fr=(
                f"Tous ces profs doivent enseigner aux mêmes créneaux "
                f"(tous présents ou aucun)."
            ),
            origin=self.origin_description or "מנהל",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_ids=params["teacher_ids"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )

    @classmethod
    def parameters_schema(cls) -> dict:
        return {
            "type": "object",
            "properties": {
                "teacher_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                },
            },
            "required": ["teacher_ids"],
        }
