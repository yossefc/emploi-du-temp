"""Contraintes de PLACEMENT de matière — bilingues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _new_assumption(ctx: "SolverContext", name: str):
    return ctx.model.NewBoolVar(name)


def _subject_label(ctx, subject_id: int) -> str:
    for g in ctx.groups:
        if g.subject_id == subject_id:
            try:
                return g.subject.name_he or g.subject.code
            except Exception:
                pass
    return f"#{subject_id}"


class SubjectRequiredSlotRangeConstraint(BaseConstraint):
    constraint_type = "subject_required_slot_range"

    def __init__(self, *, subject_id: int, min_slot: int, max_slot: int,
                 days: Optional[list[int]] = None, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.min_slot = min_slot
        self.max_slot = max_slot
        self.days = days

    def apply(self, ctx):
        group_ids = [g.id for g in ctx.groups if g.subject_id == self.subject_id]
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_subj_range_{self.db_id or 'sys'}_{self.subject_id}")
        self.assumption_literal = lit
        days_filter = set(self.days) if self.days is not None else None
        for g_id in group_ids:
            for (day, slot), var in ctx.assigned[g_id].items():
                if days_filter is not None and day not in days_filter:
                    continue
                if slot < self.min_slot or slot > self.max_slot:
                    ctx.model.Add(var == 0).OnlyEnforceIf(lit)

    def explain(self, ctx):
        subj = _subject_label(ctx, self.subject_id)
        return ConstraintExplanation(
            title_he=f"{subj} : משבצות נדרשות",
            title_fr=f"{subj} : créneaux imposés",
            detail_he=f"המקצוע חייב להיות בין משבצות {self.min_slot + 1} ו-{self.max_slot + 1}.",
            detail_fr=f"Cette matière doit être placée entre les créneaux {self.min_slot + 1} et {self.max_slot + 1}.",
            origin=self.origin_description or "מנהל",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], min_slot=params["min_slot"],
                   max_slot=params["max_slot"], days=params.get("days"),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class SubjectMaxPerDayConstraint(BaseConstraint):
    constraint_type = "subject_max_per_day"

    def __init__(self, *, subject_id: int, max_per_day: int,
                 class_id: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.max_per_day = max_per_day
        self.class_id = class_id

    def apply(self, ctx):
        group_ids = [g.id for g in ctx.groups if g.subject_id == self.subject_id]
        if self.class_id is not None:
            cls_groups = set(ctx.groups_of_class(self.class_id))
            group_ids = [g for g in group_ids if g in cls_groups]
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_subj_max_day_{self.db_id or 'sys'}_{self.subject_id}")
        self.assumption_literal = lit
        for day in ctx.active_days():
            total = sum(
                ctx.assigned[g_id][(day, s)]
                for g_id in group_ids
                for s in ctx.active_slots(day)
            )
            ctx.model.Add(total <= self.max_per_day).OnlyEnforceIf(lit)

    def explain(self, ctx):
        subj = _subject_label(ctx, self.subject_id)
        scope_he = f"כיתה #{self.class_id}" if self.class_id else "כל הכיתות"
        scope_fr = f"classe #{self.class_id}" if self.class_id else "toutes classes"
        return ConstraintExplanation(
            title_he=f"תקרה יומית : {subj}",
            title_fr=f"Plafond journalier : {subj}",
            detail_he=f"מקסימום {self.max_per_day} משבצות ביום עבור {scope_he}.",
            detail_fr=f"Max {self.max_per_day} créneau(x)/jour pour {scope_fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], max_per_day=params["max_per_day"],
                   class_id=params.get("class_id"),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class SubjectConsecutiveHoursConstraint(BaseConstraint):
    constraint_type = "subject_consecutive_hours"

    def __init__(self, *, subject_id: int, consecutive_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.consecutive_hours = consecutive_hours

    def apply(self, ctx):
        group_ids = [g.id for g in ctx.groups if g.subject_id == self.subject_id]
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_subj_consec_{self.db_id or 'sys'}_{self.subject_id}")
        self.assumption_literal = lit
        for g_id in group_ids:
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                for i, s_left in enumerate(slots):
                    for j in range(i + 2, len(slots)):
                        s_right = slots[j]
                        for k in range(i + 1, j):
                            s_mid = slots[k]
                            ctx.model.Add(
                                ctx.assigned[g_id][(day, s_left)]
                                + ctx.assigned[g_id][(day, s_right)]
                                - ctx.assigned[g_id][(day, s_mid)]
                                <= 1
                            ).OnlyEnforceIf(lit)

    def explain(self, ctx):
        subj = _subject_label(ctx, self.subject_id)
        return ConstraintExplanation(
            title_he=f"{subj} : משבצות רצופות",
            title_fr=f"{subj} : créneaux consécutifs",
            detail_he=f"המקצוע חייב לתפוס {self.consecutive_hours} משבצות ברצף.",
            detail_fr=f"Cette matière doit occuper {self.consecutive_hours} créneau(x) d'affilée.",
            origin=self.origin_description or "פדגוגי",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], consecutive_hours=params["consecutive_hours"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
