"""Contraintes spécifiques aux BARRETTES / הקבצות (HARD ou SOFT selon usage).

EXTRA_HOURS_AT_DAY_EDGE :
Quand un Group a plus d'heures/semaine que d'autres Groups de sa cohorte
parallèle (ex: Math 5 yehidot a 5h, Math 3 yehidot a 3h), les 2h "en plus"
doivent être placées en fin de journée — sinon les élèves de Math 3 sont
coincés à attendre. Idem si "début de journée" est mieux pour l'école.

Application : pour les créneaux où la cohorte n'est PAS unanime (certains
groupes sont posés, d'autres pas), forcer le créneau à être en bord de
journée (premier ou dernier slot actif).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class ExtraHoursAtDayEdgeConstraint(BaseConstraint):
    """Quand les groupes d'une cohorte n'ont pas tous le même hours_per_week,
    les "heures en plus" du groupe le plus long doivent être au bord du jour.

    Params:
        cohort_id: int                # ParallelCohort
        edge: "end" | "start"         # défaut: "end"
    """
    constraint_type = "extra_hours_at_day_edge"

    def __init__(self, *, cohort_id: int, edge: str = "end", **kwargs):
        super().__init__(**kwargs)
        self.cohort_id = cohort_id
        self.edge = edge

    def apply(self, ctx: "SolverContext") -> None:
        cohort = next((c for c in ctx.parallel_cohorts if c.id == self.cohort_id), None)
        if cohort is None or not cohort.groups:
            return

        group_ids = [g.id for g in cohort.groups]
        # Le groupe avec le plus d'heures
        max_hours = max(g.hours_per_week for g in cohort.groups)
        # Groups au max — pas d'"extra" pour eux
        # Groups en dessous — leurs créneaux sont "intérieurs" à la cohorte
        # Quand un (day, slot) a SEULEMENT le(s) groupe(s) à max posé(s),
        # ça compte comme "extra hour" — qui doit être en bord.

        lit = ctx.model.NewBoolVar(f"assum_extra_edge_{self.db_id or 'sys'}_{self.cohort_id}")
        self.assumption_literal = lit

        for day in ctx.active_days():
            slots = ctx.active_slots(day)
            if not slots:
                continue
            edge_slot = slots[-1] if self.edge == "end" else slots[0]
            for slot in slots:
                if slot == edge_slot:
                    continue
                # Sur ce créneau intérieur : si certains groupes de la cohorte sont posés
                # mais pas tous, c'est une "extra hour" placée au mauvais endroit.
                # On l'interdit : pour tout couple (g_max, g_short), si g_max est posé,
                # g_short doit l'être aussi (sauf si on est en edge).
                short_groups = [g for g in cohort.groups if g.hours_per_week < max_hours]
                max_groups = [g for g in cohort.groups if g.hours_per_week == max_hours]
                if not short_groups:
                    continue
                for g_max in max_groups:
                    for g_short in short_groups:
                        # assigned[g_max] <= assigned[g_short] (sur ce slot intérieur)
                        # → si g_max posé alors g_short posé aussi
                        ctx.model.Add(
                            ctx.assigned[g_max.id][(day, slot)]
                            <= ctx.assigned[g_short.id][(day, slot)]
                        ).OnlyEnforceIf(lit)

    def explain(self, ctx, lang="fr"):
        return ConstraintExplanation(
            title=f"Heures supp. cohorte #{self.cohort_id} en bord de journée",
            detail=(
                f"Les heures où seuls les groupes les plus longs travaillent "
                f"doivent être placées {'en fin' if self.edge == 'end' else 'en début'} de journée."
            ),
            origin=self.origin_description or "Pratique école",
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(
            cohort_id=params["cohort_id"],
            edge=params.get("edge", "end"),
            db_id=db_id, priority=priority, weight=weight,
            origin_description=origin_description,
        )
