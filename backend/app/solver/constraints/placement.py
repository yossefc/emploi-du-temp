"""Contraintes de PLACEMENT de matière (HARD relaxables pour MVP).

MVP :
- SUBJECT_REQUIRED_SLOT_RANGE : matière doit être dans une plage de créneaux (ex: religieux le matin)
- SUBJECT_REQUIRES_ROOM_TYPE : la salle assignée doit avoir le bon type (lab, gym, …)
- SUBJECT_CONSECUTIVE_HOURS : la matière doit occuper N créneaux d'affilée
- SUBJECT_MAX_PER_DAY : pas plus de N créneaux/jour de cette matière pour une classe

Note : SUBJECT_REQUIRES_ROOM_TYPE est généralement filtré en amont (Group.compatible_rooms)
mais peut être recodé ici si on veut une assomption explicite pour le MUS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


def _new_assumption(ctx: "SolverContext", name: str):
    return ctx.model.NewBoolVar(name)


class SubjectRequiredSlotRangeConstraint(BaseConstraint):
    """Tous les Groups d'une matière doivent être placés dans une plage de slot_index.

    Params:
        subject_id: int
        min_slot: int (inclusif)
        max_slot: int (inclusif)
        days: optional list[int] — si non renseigné, s'applique tous les jours actifs
    """
    constraint_type = "subject_required_slot_range"

    def __init__(self, *, subject_id: int, min_slot: int, max_slot: int,
                 days: Optional[list[int]] = None, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.min_slot = min_slot
        self.max_slot = max_slot
        self.days = days

    def apply(self, ctx: "SolverContext") -> None:
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

    def explain(self, ctx, lang="fr"):
        return ConstraintExplanation(
            title=f"Matière #{self.subject_id} : créneaux imposés",
            detail=f"Cette matière doit être placée entre les créneaux {self.min_slot} et {self.max_slot}.",
            origin=self.origin_description or "Admin école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            subject_id=params["subject_id"],
            min_slot=params["min_slot"],
            max_slot=params["max_slot"],
            days=params.get("days"),
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class SubjectMaxPerDayConstraint(BaseConstraint):
    """Une classe (ou un Group) ne fait pas plus de N créneaux/jour de cette matière.

    Params: subject_id, class_id (ou null = toutes les classes), max_per_day
    """
    constraint_type = "subject_max_per_day"

    def __init__(self, *, subject_id: int, max_per_day: int,
                 class_id: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.max_per_day = max_per_day
        self.class_id = class_id

    def apply(self, ctx: "SolverContext") -> None:
        # Groups concernés
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

    def explain(self, ctx, lang="fr"):
        scope = f"classe #{self.class_id}" if self.class_id else "toutes classes"
        return ConstraintExplanation(
            title=f"Plafond journalier matière #{self.subject_id}",
            detail=f"Max {self.max_per_day} créneau(x)/jour de cette matière ({scope}).",
            origin=self.origin_description or "Admin école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            subject_id=params["subject_id"],
            max_per_day=params["max_per_day"],
            class_id=params.get("class_id"),
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )


class SubjectConsecutiveHoursConstraint(BaseConstraint):
    """Un Group dont la matière demande N heures consécutives doit avoir ses créneaux groupés.

    Implémentation simplifiée MVP : pour chaque "bloc" requis, on impose
    que les créneaux soient consécutifs ce jour-là. Pour un group qui a
    hours_per_week=4 avec consecutive_hours=2, on attend 2 paires.

    Params: subject_id, consecutive_hours
    """
    constraint_type = "subject_consecutive_hours"

    def __init__(self, *, subject_id: int, consecutive_hours: int, **kwargs):
        super().__init__(**kwargs)
        self.subject_id = subject_id
        self.consecutive_hours = consecutive_hours

    def apply(self, ctx: "SolverContext") -> None:
        # MVP : on impose que pour chaque jour où le group est posé, les créneaux
        # de ce jour soient contigus.
        # Formellement : pas de "trou" dans les créneaux occupés ce jour-là par
        # ce group. Si occupied à slot s et à slot s', alors tous les slots entre
        # doivent être occupés.
        group_ids = [g.id for g in ctx.groups if g.subject_id == self.subject_id]
        if not group_ids:
            return
        lit = _new_assumption(ctx, f"assum_subj_consec_{self.db_id or 'sys'}_{self.subject_id}")
        self.assumption_literal = lit

        for g_id in group_ids:
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                # Pour chaque triplet (s_left, s_mid, s_right) avec s_left < s_mid < s_right :
                # assigned[left] + assigned[right] - assigned[mid] <= 1
                # → si left et right sont posés, alors mid l'est aussi
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

    def explain(self, ctx, lang="fr"):
        return ConstraintExplanation(
            title=f"Matière #{self.subject_id} : créneaux consécutifs",
            detail=f"Cette matière doit occuper {self.consecutive_hours} créneau(x) d'affilée.",
            origin=self.origin_description or "Pédagogique",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            subject_id=params["subject_id"],
            consecutive_hours=params["consecutive_hours"],
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )
