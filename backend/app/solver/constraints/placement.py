"""Contraintes de PLACEMENT de matière — bilingues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation, Suggestion


def _disable_self_suggestion(constraint_id, title_he, title_fr):
    if constraint_id is None:
        return None
    return Suggestion(
        kind="disable_constraint",
        title_he=f"בטל את האילוץ \"{title_he}\"",
        title_fr=f"Désactiver la contrainte « {title_fr} »",
        description_he="האילוץ יישאר במאגר אך לא ייעשה בו שימוש בייצור הבא.",
        description_fr="La contrainte reste en base mais ne sera plus appliquée.",
        auto_action={"verb": "patch_constraint", "target_id": constraint_id, "patch": {"is_active": False}},
    )

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
        suggestions = []
        # Suggestion 1 : désactiver
        sug = _disable_self_suggestion(self.db_id, f"{subj} : משבצות נדרשות", f"{subj} : créneaux imposés")
        if sug:
            suggestions.append(sug)
        # Suggestion 2 : élargir la plage
        if self.db_id:
            new_min = max(0, self.min_slot - 1)
            new_max = self.max_slot + 1
            suggestions.append(Suggestion(
                kind="patch_constraint",
                title_he=f"הרחב את הטווח : משבצות {new_min + 1}-{new_max + 1}",
                title_fr=f"Élargir la plage : créneaux {new_min + 1}-{new_max + 1}",
                description_he="הרחב את החלון של משבצת אחת בכל צד.",
                description_fr="Étend la fenêtre d'un créneau de chaque côté.",
                auto_action={
                    "verb": "patch_constraint", "target_id": self.db_id,
                    "patch": {"parameters": {"subject_id": self.subject_id, "min_slot": new_min, "max_slot": new_max,
                                              **({"days": self.days} if self.days else {})}},
                },
            ))
        return ConstraintExplanation(
            title_he=f"{subj} : משבצות נדרשות",
            title_fr=f"{subj} : créneaux imposés",
            detail_he=f"המקצוע חייב להיות בין משבצות {self.min_slot + 1} ו-{self.max_slot + 1}.",
            detail_fr=f"Cette matière doit être placée entre les créneaux {self.min_slot + 1} et {self.max_slot + 1}.",
            origin=self.origin_description or "מנהל",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], min_slot=params["min_slot"],
                   max_slot=params["max_slot"], days=params.get("days"),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class SubjectPreferredSlotRangeConstraint(BaseConstraint):
    """Version SOFT de SUBJECT_REQUIRED_SLOT_RANGE.

    « Le mieux est de commencer la journée par מחנכים/מנטורים » : on pénalise
    chaque heure placée hors de la fenêtre souhaitée au lieu de l'interdire.
    Sans assumption literal → jamais responsable d'une infaisabilité.
    """
    constraint_type = "subject_preferred_slot_range"

    def __init__(self, *, subject_id: int, min_slot: int, max_slot: int, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.min_slot = min_slot
        self.max_slot = max_slot

    def apply(self, ctx):
        group_ids = [g.id for g in ctx.groups if g.subject_id == self.subject_id]
        if not group_ids:
            return
        weight = self.weight or 30
        for g_id in group_ids:
            for (day, slot), var in ctx.assigned[g_id].items():
                if slot < self.min_slot or slot > self.max_slot:
                    # Plus on s'éloigne de la fenêtre, plus c'est pénalisé.
                    distance = (
                        self.min_slot - slot if slot < self.min_slot else slot - self.max_slot
                    )
                    ctx.soft_penalty_terms.append((var, weight * min(distance, 4)))

    def explain(self, ctx):
        subj = _subject_label(ctx, self.subject_id)
        return ConstraintExplanation(
            title_he=f"{subj} : משבצות מועדפות",
            title_fr=f"{subj} : créneaux préférés",
            detail_he=f"עדיף שהמקצוע יהיה בין משבצות {self.min_slot + 1} ל-{self.max_slot + 1}.",
            detail_fr=f"Cette matière devrait être placée entre les créneaux "
                      f"{self.min_slot + 1} et {self.max_slot + 1}.",
            origin=self.origin_description or "מנהל",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], min_slot=params["min_slot"],
                   max_slot=params["max_slot"],
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
        suggestions = []
        sug = _disable_self_suggestion(self.db_id, f"תקרה יומית {subj}", f"Plafond {subj}")
        if sug:
            suggestions.append(sug)
        # Suggestion : augmenter le plafond d'1
        if self.db_id:
            suggestions.append(Suggestion(
                kind="patch_constraint",
                title_he=f"העלה את התקרה ל-{self.max_per_day + 1} שעות ביום",
                title_fr=f"Augmenter le plafond à {self.max_per_day + 1}h/jour",
                description_he="הוסף שעה אחת לתקרה היומית.",
                description_fr="Ajoute 1h au plafond journalier.",
                auto_action={
                    "verb": "patch_constraint", "target_id": self.db_id,
                    "patch": {"parameters": {"subject_id": self.subject_id, "max_per_day": self.max_per_day + 1,
                                              **({"class_id": self.class_id} if self.class_id else {})}},
                },
            ))
        return ConstraintExplanation(
            title_he=f"תקרה יומית : {subj}",
            title_fr=f"Plafond journalier : {subj}",
            detail_he=f"מקסימום {self.max_per_day} משבצות ביום עבור {scope_he}.",
            detail_fr=f"Max {self.max_per_day} créneau(x)/jour pour {scope_fr}.",
            origin=self.origin_description or "מנהל",
            suggestions=suggestions,
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
        suggestions = []
        sug = _disable_self_suggestion(self.db_id, f"{subj} רצף", f"{subj} consécutif")
        if sug:
            suggestions.append(sug)
        if self.db_id and self.consecutive_hours > 1:
            suggestions.append(Suggestion(
                kind="patch_constraint",
                title_he=f"צמצם הדרישה ל-{self.consecutive_hours - 1} משבצות ברצף",
                title_fr=f"Réduire l'exigence à {self.consecutive_hours - 1} créneau(x) consécutifs",
                description_he="הקטנה של הדרישה לרצף יכולה לעזור לפותר למצוא פתרון.",
                description_fr="Réduire l'exigence de consécutivité aide le solveur.",
                auto_action={
                    "verb": "patch_constraint", "target_id": self.db_id,
                    "patch": {"parameters": {"subject_id": self.subject_id, "consecutive_hours": self.consecutive_hours - 1}},
                },
            ))
        return ConstraintExplanation(
            title_he=f"{subj} : משבצות רצופות",
            title_fr=f"{subj} : créneaux consécutifs",
            detail_he=f"המקצוע חייב לתפוס {self.consecutive_hours} משבצות ברצף.",
            detail_fr=f"Cette matière doit occuper {self.consecutive_hours} créneau(x) d'affilée.",
            origin=self.origin_description or "פדגוגי",
            suggestions=suggestions,
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(subject_id=params["subject_id"], consecutive_hours=params["consecutive_hours"],
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
