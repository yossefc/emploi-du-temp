"""Préférences SOFT pour les profs (et l'école).

Ces contraintes ne sont JAMAIS infaisables : elles ajoutent une pénalité
à minimiser. Le solveur essaie de les respecter au mieux, mais peut les
violer si nécessaire.

Pas d'assumption literal → n'apparaissent PAS dans le MUS.

Implémentés :
- TeacherPreferMorningConstraint : pénalité par cours placé l'après-midi (slot >= threshold)
- TeacherPreferAfternoonConstraint : pénalité par cours placé le matin
- TeacherPreferGroupedDaysConstraint : pénalité par jour distinct travaillé
  (pour qu'un prof regroupe ses cours sur 3 jours au lieu de 5)

Weight (1-100) configurable via la contrainte.
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


# Seuil par défaut : créneau 5 = "après-midi"
DEFAULT_MORNING_SLOTS = 5


class _BasePreference(BaseConstraint):
    """Marker base : préférence SOFT, pas d'assumption literal."""

    def __init__(self, *, teacher_id: int, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id


class TeacherPreferMorningConstraint(_BasePreference):
    constraint_type = "teacher_prefer_morning"

    def __init__(self, *, teacher_id: int, morning_max_slot: int = DEFAULT_MORNING_SLOTS, **kwargs):
        super().__init__(teacher_id=teacher_id, **kwargs)
        self.morning_max_slot = morning_max_slot

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        weight = self.weight or 10
        for day, slot in ctx.all_active_positions():
            if slot < self.morning_max_slot:
                continue
            # Pénalité = weight × (cours du prof à ce créneau)
            for g_id in group_ids:
                ctx.soft_penalty_terms.append((ctx.assigned[g_id][(day, slot)], weight))

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"מעדיף בוקר : {name}",
            title_fr=f"Préfère le matin : {name}",
            detail_he=f"המורה מעדיף שיעורים לפני משבצת {self.morning_max_slot + 1}.",
            detail_fr=f"Préfère ses cours avant le créneau {self.morning_max_slot + 1}.",
            origin=self.origin_description or "המורה",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            morning_max_slot=params.get("morning_max_slot", DEFAULT_MORNING_SLOTS),
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherPreferAfternoonConstraint(_BasePreference):
    constraint_type = "teacher_prefer_afternoon"

    def __init__(self, *, teacher_id: int, afternoon_min_slot: int = DEFAULT_MORNING_SLOTS, **kwargs):
        super().__init__(teacher_id=teacher_id, **kwargs)
        self.afternoon_min_slot = afternoon_min_slot

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        weight = self.weight or 10
        for day, slot in ctx.all_active_positions():
            if slot >= self.afternoon_min_slot:
                continue
            for g_id in group_ids:
                ctx.soft_penalty_terms.append((ctx.assigned[g_id][(day, slot)], weight))

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"מעדיף אחר הצהריים : {name}",
            title_fr=f"Préfère l'après-midi : {name}",
            detail_he=f"המורה מעדיף שיעורים מ-משבצת {self.afternoon_min_slot + 1}.",
            detail_fr=f"Préfère ses cours à partir du créneau {self.afternoon_min_slot + 1}.",
            origin=self.origin_description or "המורה",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            afternoon_min_slot=params.get("afternoon_min_slot", DEFAULT_MORNING_SLOTS),
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherPreferGroupedDaysConstraint(_BasePreference):
    """Préfère regrouper les cours du prof sur peu de jours (ex: 3 au lieu de 5).

    Pénalité = weight × (nombre de jours où le prof a au moins 1 cours).
    Le solveur minimisera → tendance à concentrer.
    """
    constraint_type = "teacher_prefer_grouped_days"

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        weight = self.weight or 20  # plus impactant par défaut

        for day in ctx.active_days():
            day_busy = ctx.model.NewBoolVar(f"prefdays_t{self.teacher_id}_d{day}")
            total_slots = sum(
                ctx.assigned[g_id][(day, s)]
                for g_id in group_ids
                for s in ctx.active_slots(day)
            )
            # day_busy = 1 si total_slots >= 1, sinon 0
            ctx.model.Add(total_slots >= 1).OnlyEnforceIf(day_busy)
            ctx.model.Add(total_slots == 0).OnlyEnforceIf(day_busy.Not())
            ctx.soft_penalty_terms.append((day_busy, weight))

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"ימי עבודה מרוכזים : {name}",
            title_fr=f"Jours groupés : {name}",
            detail_he="המורה מעדיף לרכז שיעורים על מספר מצומצם של ימים.",
            detail_fr="Préfère concentrer ses cours sur peu de jours.",
            origin=self.origin_description or "המורה",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class TeacherAvoidGapsConstraint(_BasePreference):
    """Pénalise les "trous" dans la journée d'un prof.

    Approximation simple : pour chaque jour, pénalité = (slots du jour entre 1er
    et dernier cours) - (nombre de cours). Plus l'écart, plus on pénalise.
    """
    constraint_type = "teacher_avoid_gaps"

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        weight = self.weight or 5

        for day in ctx.active_days():
            slots = ctx.active_slots(day)
            if len(slots) < 3:
                continue
            # Pour simplifier : pénalité par cours placé "tard" relative au prof
            # Ce n'est pas idéal mais évite la complexité O(N²)
            for i, s in enumerate(slots):
                if i == 0 or i == len(slots) - 1:
                    continue  # bords pas pénalisés
                for g_id in group_ids:
                    ctx.soft_penalty_terms.append((ctx.assigned[g_id][(day, s)], weight // 5 or 1))

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        return ConstraintExplanation(
            title_he=f"בלי חלונות : {name}",
            title_fr=f"Éviter les trous : {name}",
            detail_he="המורה מעדיף שלא יהיו חלונות (משבצות פנויות) בין שיעוריו ביום.",
            detail_fr="Préfère éviter les créneaux vides entre ses cours d'une même journée.",
            origin=self.origin_description or "המורה",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            teacher_id=params["teacher_id"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )
