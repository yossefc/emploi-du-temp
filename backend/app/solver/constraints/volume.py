"""Contraintes de VOLUMES horaires (HARD relaxables) — bilingues + suggestions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import (
    BaseConstraint,
    ConstraintExplanation,
    Suggestion,
)

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _new_assumption(ctx: "SolverContext", name: str):
    return ctx.model.NewBoolVar(name)


class GroupHoursPerWeekConstraint(BaseConstraint):
    constraint_type = "group_hours_per_week"

    def __init__(self, *, group_id: int, hours: int, **kwargs):
        super().__init__(**kwargs)
        self.group_id = group_id
        self.hours = hours

    def apply(self, ctx):
        if self.group_id not in ctx.assigned:
            return
        lit = _new_assumption(ctx, f"assum_grp_hours_{self.db_id or 'sys'}_{self.group_id}")
        self.assumption_literal = lit
        total = sum(ctx.assigned[self.group_id].values())
        ctx.model.Add(total == self.hours).OnlyEnforceIf(lit)

    def explain(self, ctx):
        label = f"#{self.group_id}"
        group = None
        try:
            group = ctx.group(self.group_id)
            label = group.label
        except KeyError:
            pass

        suggestions: list[Suggestion] = []
        if group:
            if group.hours_per_week > 1:
                new_h = group.hours_per_week - 1
                suggestions.append(Suggestion(
                    kind="reduce_group_hours",
                    title_he=f"צמצם «{label}» ל-{new_h} שעות בשבוע",
                    title_fr=f"Réduire « {label} » à {new_h}h/sem",
                    description_he="הקטנה בשעה אחת עשויה לפתור את הקונפליקט.",
                    description_fr="Réduire d'une heure peut suffire à résoudre le conflit.",
                    auto_action={
                        "verb": "patch_group",
                        "target_id": group.id,
                        "patch": {"hours_per_week": new_h},
                    },
                ))
            suggestions.append(Suggestion(
                kind="remove_group",
                title_he=f"מחק את הקבוצה «{label}»",
                title_fr=f"Supprimer le groupe « {label} »",
                description_he="הקבוצה תוסר לחלוטין מהמערכת.",
                description_fr="Le groupe sera complètement retiré de la planification.",
            ))

        return ConstraintExplanation(
            title_he=f"נפח שעות : {label}",
            title_fr=f"Volume horaire : {label}",
            detail_he=f"הקבוצה דורשת בדיוק {self.hours} משבצות בשבוע.",
            detail_fr=f"Ce groupe doit avoir exactement {self.hours} créneau(x) par semaine.",
            origin=self.origin_description or "הגדרת קבוצה",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(group_id=params["group_id"], hours=params["hours"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherMaxHoursWeekConstraint(BaseConstraint):
    constraint_type = "teacher_max_hours_week"

    def __init__(self, *, teacher_id: int, max_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_hours = max_hours

    def apply(self, ctx):
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_t_week_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit
        total = sum(
            ctx.assigned[g_id][(d, s)]
            for g_id in group_ids
            for (d, s) in ctx.all_active_positions()
        )
        ctx.model.Add(total <= self.max_hours).OnlyEnforceIf(lit)

    def explain(self, ctx):
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        sug = None
        if self.db_id:
            sug = Suggestion(
                kind="patch_constraint",
                title_he=f"העלה את התקרה השבועית ל-{self.max_hours + 2}",
                title_fr=f"Augmenter le plafond hebdo à {self.max_hours + 2}",
                description_he="הגדל את התקרה בשעתיים.",
                description_fr="Augmente le plafond de 2h.",
                auto_action={
                    "verb": "patch_constraint", "target_id": self.db_id,
                    "patch": {"parameters": {"teacher_id": self.teacher_id, "max_hours": self.max_hours + 2}},
                },
            )
        return ConstraintExplanation(
            title_he=f"תקרה שבועית : {name}",
            title_fr=f"Plafond hebdo : {name}",
            detail_he=f"{name} מוגבל ל-{self.max_hours} שעות לשבוע.",
            detail_fr=f"{name} ne doit pas dépasser {self.max_hours} créneaux par semaine.",
            origin=self.origin_description or "חוזה",
            suggestions=[s for s in [sug] if s],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(teacher_id=params["teacher_id"], max_hours=params["max_hours"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherMaxHoursDayConstraint(BaseConstraint):
    constraint_type = "teacher_max_hours_day"

    def __init__(self, *, teacher_id: int, max_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_hours = max_hours

    def apply(self, ctx):
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_t_day_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit
        for day in ctx.active_days():
            total = sum(
                ctx.assigned[g_id][(day, s)]
                for g_id in group_ids
                for s in ctx.active_slots(day)
            )
            ctx.model.Add(total <= self.max_hours).OnlyEnforceIf(lit)

    def explain(self, ctx):
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"תקרה יומית : {name}",
            title_fr=f"Plafond journalier : {name}",
            detail_he=f"{name} מוגבל ל-{self.max_hours} שעות ביום.",
            detail_fr=f"{name} ne doit pas dépasser {self.max_hours} créneaux par jour.",
            origin=self.origin_description or "מנהל",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(teacher_id=params["teacher_id"], max_hours=params["max_hours"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherMaxConsecutiveConstraint(BaseConstraint):
    constraint_type = "teacher_max_consecutive"

    def __init__(self, *, teacher_id: int, max_consecutive: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_consecutive = max_consecutive

    def apply(self, ctx):
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        n = self.max_consecutive
        lit = _new_assumption(ctx, f"assum_t_consec_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit
        for day in ctx.active_days():
            slots = ctx.active_slots(day)
            for i in range(len(slots) - n):
                window = slots[i : i + n + 1]
                window_sum = sum(
                    ctx.assigned[g_id][(day, s)]
                    for g_id in group_ids
                    for s in window
                )
                ctx.model.Add(window_sum <= n).OnlyEnforceIf(lit)

    def explain(self, ctx):
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"ללא רצף ארוך : {name}",
            title_fr=f"Pas d'enchaînement long : {name}",
            detail_he=f"{name} לא צריך יותר מ-{self.max_consecutive} שיעורים ברצף.",
            detail_fr=f"{name} ne doit pas avoir plus de {self.max_consecutive} cours consécutifs.",
            origin=self.origin_description or "רווחת המורה",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(teacher_id=params["teacher_id"], max_consecutive=params["max_consecutive"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
