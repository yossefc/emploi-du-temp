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
        self.edge_size = max(1, edge_size)

    def apply(self, ctx):
        """Pousse le surplus d'une barrette inégale vers le bord de journée.

        Cas réel : 5 יח' = 7h, 3 יח' = 4h. Pendant les 4h communes tout le monde
        travaille ; les 3h de surplus des 5 יח' doivent tomber au bord de la
        journée, sinon les élèves de 3 יח' ont un trou.

        Formulation SOUPLE et volontaire. La version dure précédente imposait le
        surplus dans les `edge_size` dernières périodes de la GRILLE (P9-P11 sur
        une grille de 11), alors que les classes finissent vers P8 : le surplus
        n'avait aucun créneau licite et le modèle devenait infaisable dès que
        plusieurs barrettes inégales coexistaient. On pénalise désormais chaque
        heure de surplus proportionnellement à sa précocité dans la journée : le
        solveur la repousse en fin de journée quand c'est possible, et accepte
        un compromis quand ça ne l'est pas.
        """
        cohort = next((c for c in ctx.parallel_cohorts if c.id == self.cohort_id), None)
        if cohort is None or not cohort.groups or len(cohort.groups) < 2:
            return
        max_hours = max(g.hours_per_week for g in cohort.groups)
        short_groups = [g for g in cohort.groups if g.hours_per_week < max_hours]
        max_groups = [g for g in cohort.groups if g.hours_per_week == max_hours]
        if not short_groups:
            return

        # Groupes de TOUTES les classes concernées : c'est par rapport à leur
        # journée réelle qu'on juge « la fin », pas par rapport à la grille.
        class_ids = {c.id for g in cohort.groups for c in g.source_classes}
        cohort_ids = {g.id for g in cohort.groups}
        # Les heures en extra peuvent s'ENCHAÎNER en fin de journée : c'est ce
        # que faisait תשפ"ו (anglais יב lundi P7-P8-P9, les trois profs à 5h
        # pendant qu'אליס n'avait qu'une heure le mardi). Ma version initiale
        # interdisait tout cours après une heure en extra, y compris les autres
        # heures en extra — ce qui exigeait une fin de journée distincte par
        # heure excédentaire : 8 fins pour יב, qui n'a que 5 jours. On exclut
        # donc la barrette elle-même de l'interdiction.
        neighbour_ids = ({gid for cid in class_ids for gid in ctx.groups_of_class(cid)}
                         - cohort_ids)

        lit = ctx.model.NewBoolVar(f"assum_extra_edge_{self.db_id or 'sys'}_{self.cohort_id}")
        self.assumption_literal = lit
        weight = self.weight or 45
        for day in ctx.active_days():
            slots = ctx.active_slots(day)
            if len(slots) < 2:
                continue
            for idx, slot in enumerate(slots[:-1]):
                for g_max in max_groups:
                    for g_short in short_groups:
                        # surplus = l'enveloppe tourne sans le groupe court :
                        # une partie des élèves n'a pas cours à ce moment-là.
                        surplus = ctx.model.NewBoolVar(
                            f"surplus_{self.cohort_id}_{g_max.id}_{g_short.id}_{day}_{slot}")
                        a_max = ctx.assigned[g_max.id][(day, slot)]
                        a_short = ctx.assigned[g_short.id][(day, slot)]
                        ctx.model.Add(surplus >= a_max - a_short)
                        # ... alors plus rien après, pour ces classes, ce jour-là :
                        # les élèves libérés rentrent chez eux au lieu d'attendre.
                        # « י lundi P7 : pas tout le monde a maths — les heures
                        # en extra doivent être fin de journée » (Yossef 10/08).
                        for later in slots[idx + 1:]:
                            for gid in neighbour_ids:
                                var = ctx.assigned[gid].get((day, later))
                                if var is not None:
                                    ctx.model.Add(var == 0).OnlyEnforceIf([lit, surplus])
                        ctx.soft_penalty_terms.append((surplus, weight))

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
                   edge_size=params.get("edge_size", 3),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
