"""Contraintes de VOLUMES horaires (HARD relaxables).

- GROUP_HOURS_PER_WEEK : un Group doit avoir exactement N heures/semaine
- TEACHER_MAX_HOURS_WEEK / DAY : plafonds prof
- TEACHER_MAX_CONSECUTIVE : pas plus de N cours d'affilée

NOTE: GROUP_HOURS_PER_WEEK est généralement renseigné directement sur le Group
(`group.hours_per_week`). Cette contrainte permet de surcharger via la table
`constraints` (ex: ajustement temporaire admin).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _new_assumption(ctx: "SolverContext", name: str):
    lit = ctx.model.NewBoolVar(name)
    return lit


class GroupHoursPerWeekConstraint(BaseConstraint):
    """`sum(assigned[g][d][s]) == hours_per_week` pour ce group."""
    constraint_type = "group_hours_per_week"

    def __init__(self, *, group_id: int, hours: int, **kwargs):
        super().__init__(**kwargs)
        self.group_id = group_id
        self.hours = hours

    def apply(self, ctx: "SolverContext") -> None:
        if self.group_id not in ctx.assigned:
            return
        lit = _new_assumption(ctx, f"assum_grp_hours_{self.db_id or 'sys'}_{self.group_id}")
        self.assumption_literal = lit
        total = sum(ctx.assigned[self.group_id].values())
        ctx.model.Add(total == self.hours).OnlyEnforceIf(lit)

    def explain(self, ctx, lang="fr"):
        try:
            g = ctx.group(self.group_id)
            label = g.label
        except KeyError:
            label = f"Groupe #{self.group_id}"
        return ConstraintExplanation(
            title=f"Volume horaire : {label}",
            detail=f"Ce groupe doit avoir exactement {self.hours} créneau(x) par semaine.",
            origin=self.origin_description or "Admin école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            group_id=params["group_id"],
            hours=params["hours"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherMaxHoursWeekConstraint(BaseConstraint):
    """Plafond hebdo pour un prof. `sum over all (d,s) and groups of teacher <= max`."""
    constraint_type = "teacher_max_hours_week"

    def __init__(self, *, teacher_id: int, max_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_hours = max_hours

    def apply(self, ctx: "SolverContext") -> None:
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

    def explain(self, ctx, lang="fr"):
        try:
            t = ctx.teacher(self.teacher_id)
            who = t.full_name
        except KeyError:
            who = f"Prof #{self.teacher_id}"
        return ConstraintExplanation(
            title=f"Plafond hebdo : {who}",
            detail=f"{who} ne doit pas dépasser {self.max_hours} créneaux par semaine.",
            origin=self.origin_description or "Admin école / contrat",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            max_hours=params["max_hours"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherMaxHoursDayConstraint(BaseConstraint):
    """Plafond journalier prof."""
    constraint_type = "teacher_max_hours_day"

    def __init__(self, *, teacher_id: int, max_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_hours = max_hours

    def apply(self, ctx: "SolverContext") -> None:
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

    def explain(self, ctx, lang="fr"):
        try:
            who = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            who = f"Prof #{self.teacher_id}"
        return ConstraintExplanation(
            title=f"Plafond journalier : {who}",
            detail=f"{who} ne doit pas dépasser {self.max_hours} créneaux par jour.",
            origin=self.origin_description or "Admin école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            max_hours=params["max_hours"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherMaxConsecutiveConstraint(BaseConstraint):
    """Pas plus de N cours consécutifs sans pause."""
    constraint_type = "teacher_max_consecutive"

    def __init__(self, *, teacher_id: int, max_consecutive: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.max_consecutive = max_consecutive

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        n = self.max_consecutive
        lit = _new_assumption(ctx, f"assum_t_consec_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit
        # Pour chaque fenêtre glissante de (n+1) créneaux consécutifs d'un jour,
        # au plus n peuvent être enseignés.
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

    def explain(self, ctx, lang="fr"):
        try:
            who = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            who = f"Prof #{self.teacher_id}"
        return ConstraintExplanation(
            title=f"Pas d'enchaînement long : {who}",
            detail=f"{who} ne doit pas avoir plus de {self.max_consecutive} cours consécutifs.",
            origin=self.origin_description or "Bien-être prof",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            max_consecutive=params["max_consecutive"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )
