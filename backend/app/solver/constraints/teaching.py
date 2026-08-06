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


class TeacherFreeDayConstraint(BaseConstraint):
    """Le prof doit avoir au moins `min_free_days` jour(s) SANS AUCUN cours.

    Règle israélienne standard (יום חופשי). HARD relaxable : une contrainte
    par prof → si infaisable, le MUS désigne précisément le prof concerné.
    """
    constraint_type = "teacher_free_day"

    def __init__(self, *, teacher_id: int, min_free_days: int = 1, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.min_free_days = min_free_days

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        days = ctx.active_days()
        if len(days) <= self.min_free_days:
            return
        lit = ctx.model.NewBoolVar(f"assum_freeday_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit

        day_busy_vars = []
        for day in days:
            slots = ctx.active_slots(day)
            total = sum(ctx.assigned[g][(day, s)] for g in group_ids for s in slots)
            busy = ctx.model.NewBoolVar(f"fd_busy_t{self.teacher_id}_d{day}")
            # total <= M*busy : si busy=0 alors aucun cours ce jour
            ctx.model.Add(total <= len(slots) * busy)
            day_busy_vars.append(busy)

        ctx.model.Add(
            sum(day_busy_vars) <= len(days) - self.min_free_days
        ).OnlyEnforceIf(lit)

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        suggestions = []
        if self.db_id:
            suggestions.append(Suggestion(
                kind="disable_constraint",
                title_he=f"ותרו על יום חופשי עבור {name}",
                title_fr=f"Renoncer au jour libre de {name}",
                description_he="המורה יעבוד כל ימות השבוע.",
                description_fr="Le prof travaillera tous les jours de la semaine.",
                auto_action={"verb": "patch_constraint", "target_id": self.db_id,
                             "patch": {"is_active": False}},
            ))
        return ConstraintExplanation(
            title_he=f"יום חופשי : {name}",
            title_fr=f"Jour libre : {name}",
            detail_he=f"{name} חייב לפחות {self.min_free_days} יום בשבוע ללא שיעורים.",
            detail_fr=f"{name} doit avoir au moins {self.min_free_days} jour/sem sans cours.",
            origin=self.origin_description or "מדיניות בית הספר",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(teacher_id=params["teacher_id"],
                   min_free_days=params.get("min_free_days", 1),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
