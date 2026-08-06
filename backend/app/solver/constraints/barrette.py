"""EXTRA_HOURS_AT_DAY_EDGE — bilingue."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class ExtraHoursAtDayEdgeConstraint(BaseConstraint):
    constraint_type = "extra_hours_at_day_edge"

    def __init__(self, *, cohort_id: int, edge: str = "end", edge_size: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.cohort_id = cohort_id
        self.edge = edge
        # Fenêtre "fin de journée" = les `edge_size` dernières périodes du jour.
        # Cas réel : 5 יח' = 7h, 3 יח' = 4h → les 3h de surplus doivent tomber
        # dans les dernières périodes pour ne pas trouer la journée des 3 יח'.
        self.edge_size = max(1, edge_size)

    def apply(self, ctx):
        cohort = next((c for c in ctx.parallel_cohorts if c.id == self.cohort_id), None)
        if cohort is None or not cohort.groups:
            return
        group_ids = [g.id for g in cohort.groups]
        if len(group_ids) < 2:
            return
        max_hours = max(g.hours_per_week for g in cohort.groups)
        short_groups = [g for g in cohort.groups if g.hours_per_week < max_hours]
        max_groups = [g for g in cohort.groups if g.hours_per_week == max_hours]
        if not short_groups:
            return
        lit = ctx.model.NewBoolVar(f"assum_extra_edge_{self.db_id or 'sys'}_{self.cohort_id}")
        self.assumption_literal = lit
        for day in ctx.active_days():
            slots = ctx.active_slots(day)
            if not slots:
                continue
            if self.edge == "end":
                edge_slots = set(slots[-self.edge_size:])
            else:
                edge_slots = set(slots[: self.edge_size])
            for slot in slots:
                if slot in edge_slots:
                    continue
                # Hors fenêtre de bord : l'enveloppe ne tourne que si les courts
                # tournent aussi → le surplus est repoussé en bord de journée.
                for g_max in max_groups:
                    for g_short in short_groups:
                        ctx.model.Add(
                            ctx.assigned[g_max.id][(day, slot)]
                            <= ctx.assigned[g_short.id][(day, slot)]
                        ).OnlyEnforceIf(lit)

    def explain(self, ctx):
        edge_he = "סוף" if self.edge == "end" else "תחילת"
        edge_fr = "fin" if self.edge == "end" else "début"
        return ConstraintExplanation(
            title_he=f"שעות נוספות בקצה היום (הקבצה #{self.cohort_id})",
            title_fr=f"Heures supp. en {edge_fr} de journée (cohorte #{self.cohort_id})",
            detail_he=f"שעות שבהן רק הקבוצות הארוכות לומדות יוקצו ב{edge_he} היום.",
            detail_fr=(
                f"Les heures où seuls les groupes les plus longs travaillent "
                f"doivent être placées en {edge_fr} de journée."
            ),
            origin=self.origin_description or "פרקטיקה בית-ספרית",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(cohort_id=params["cohort_id"], edge=params.get("edge", "end"),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
