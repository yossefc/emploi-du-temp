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


class GroupPinnedSlotConstraint(BaseConstraint):
    """Épingle un groupe sur des créneaux précis.

    Sert à la règle « tous les dimanches doivent commencer par les מחנכים »
    (Yossef 09/08) : le cours du מחנך de chaque classe est fixé au dimanche
    P1. Le directeur חוזה שנהב בועז y ajoute une seconde heure de תלמוד.

    `positions` = [[jour, créneau], …]. HARD relaxable : si une classe ne peut
    pas l'honorer, le MUS la désigne nommément.
    """
    constraint_type = "group_pinned_slot"

    def __init__(self, *, group_id: int, positions: list, **kwargs):
        super().__init__(**kwargs)
        self.group_id = group_id
        self.positions = [tuple(p) for p in positions]

    def apply(self, ctx: "SolverContext") -> None:
        var_map = ctx.assigned.get(self.group_id)
        if not var_map or not self.positions:
            return
        lit = ctx.model.NewBoolVar(f"assum_pin_{self.db_id or 'sys'}_{self.group_id}")
        self.assumption_literal = lit
        for pos in self.positions:
            var = var_map.get(pos)
            if var is not None:
                ctx.model.Add(var == 1).OnlyEnforceIf(lit)

    def explain(self, ctx) -> ConstraintExplanation:
        label = f"#{self.group_id}"
        try:
            label = ctx.group(self.group_id).label
        except KeyError:
            pass
        he = ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]
        where = ", ".join(f"{he[d]} P{s + 1}" for d, s in self.positions
                          if 0 <= d < 5)
        return ConstraintExplanation(
            title_he=f"שיבוץ קבוע : {label}",
            title_fr=f"Créneau imposé : {label}",
            detail_he=f"הקבוצה חייבת להתקיים ב{where}.",
            detail_fr=f"Ce groupe doit avoir lieu sur {where}.",
            origin=self.origin_description or "מדיניות בית הספר",
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(group_id=params["group_id"], positions=params.get("positions", []),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherPreferredFreeDayConstraint(BaseConstraint):
    """Jour de congé SOUHAITÉ par le prof, par ordre de préférence.

    Source : questionnaire תשפ"ז « יום חופשי נוסף מועדף » où chaque prof a
    classé jusqu'à trois jours. On pénalise chaque heure travaillée sur le
    jour demandé, d'autant plus fort que le choix est haut placé. Le prof
    obtient son jour quand c'est possible, sans jamais bloquer le modèle.

    `days` = liste d'indices de jours, du plus souhaité au moins souhaité.
    """
    constraint_type = "teacher_preferred_free_day"

    def __init__(self, *, teacher_id: int, days: list[int], **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.days = days

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids or not self.days:
            return
        base = self.weight or 40
        for rank, day in enumerate(self.days):
            if day not in ctx.active_days():
                continue
            slots = ctx.active_slots(day)
            if not slots:
                continue
            # UN seul terme par jour souhaité : « ce prof travaille-t-il ce
            # jour-là ? ». Pénaliser chaque heure séparément produisait des
            # milliers de termes (30 profs × 3 jours × 10 créneaux × leurs
            # groupes), ce qui alourdissait assez l'objectif pour faire échouer
            # la phase stricte — et on y perdait les garanties de classe.
            busy = ctx.model.NewBoolVar(f"pfd_t{self.teacher_id}_d{day}")
            ctx.model.AddMaxEquality(
                busy, [ctx.assigned[g][(day, s)] for g in group_ids for s in slots])
            # 1er choix plein tarif, 2e à 60 %, 3e à 35 %. Volontairement plus
            # léger qu'un trou élève (100) : « oblige les cours commencent P1
            # et 0 trous obligatoire », le confort du prof ne doit jamais
            # l'emporter sur la journée des élèves.
            w = max(1, int(base * (1.0, 0.6, 0.35)[min(rank, 2)]))
            ctx.soft_penalty_terms.append((busy, w * 2))

    def explain(self, ctx) -> ConstraintExplanation:
        name = f"#{self.teacher_id}"
        try:
            name = ctx.teacher(self.teacher_id).full_name
        except KeyError:
            pass
        he = ["ראשון", "שני", "שלישי", "רביעי", "חמישי"]
        lst = ", ".join(he[d] for d in self.days if 0 <= d < 5)
        return ConstraintExplanation(
            title_he=f"יום חופשי מבוקש : {name}",
            title_fr=f"Jour de congé souhaité : {name}",
            detail_he=f"{name} ביקש/ה יום חופשי ב: {lst} (לפי סדר עדיפות).",
            detail_fr=f"{name} a demandé un jour de congé : {lst} (par ordre de préférence).",
            origin=self.origin_description or 'שאלון מורים תשפ"ז',
            suggestions=[],
        )

    @classmethod
    def _build_from_params(cls, *, params, db_id, priority, weight, origin_description):
        return cls(teacher_id=params["teacher_id"], days=params.get("days", []),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)


class TeacherFreeDayConstraint(BaseConstraint):
    """Nombre de jours travaillés par un prof, et volume minimum par journée.

    Deux règles israéliennes réunies ici parce qu'elles portent sur la même
    variable « ce prof travaille-t-il tel jour ? » :

    1. `min_free_days` jour(s) sans aucun cours (יום חופשי). Le barème officiel
       lie le nombre de jours autorisés au volume frontal — עוז לתמורה au lycée,
       אופק חדש au collège :

           ≤ 12h  → 2 jours max      18-21h → 4 jours max
           13-17h → 3 jours max      ≥ 22h  → 5 jours

    2. `min_hours_per_day` : on ne fait pas venir un prof pour une seule heure.
       Un jour travaillé compte au moins 2 heures.

    HARD relaxable : une contrainte par prof → si infaisable, le MUS désigne
    précisément le prof concerné.
    """
    constraint_type = "teacher_free_day"

    def __init__(self, *, teacher_id: int, min_free_days: int = 1,
                 min_hours_per_day: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.teacher_id = teacher_id
        self.min_free_days = min_free_days
        self.min_hours_per_day = min_hours_per_day

    def apply(self, ctx: "SolverContext") -> None:
        group_ids = ctx.groups_of_teacher(self.teacher_id)
        if not group_ids:
            return
        # Le vendredi n'est PAS un jour de congé : 4 périodes, réservé à la
        # מגמת מחשבים. Le compter rendait la règle « au moins un jour de
        # congé » creuse — 38 profs travaillaient les 5 jours dim→jeu (12/08).
        days = [d for d in ctx.active_days() if d < 5]
        lit = ctx.model.NewBoolVar(f"assum_freeday_{self.db_id or 'sys'}_{self.teacher_id}")
        self.assumption_literal = lit

        total_hours = sum(ctx.group(g).hours_per_week for g in group_ids)
        day_busy_vars, day_totals = [], []
        for day in days:
            slots = ctx.active_slots(day)
            total = sum(ctx.assigned[g][(day, s)] for g in group_ids for s in slots)
            busy = ctx.model.NewBoolVar(f"fd_busy_t{self.teacher_id}_d{day}")
            # total <= M*busy : si busy=0 alors aucun cours ce jour
            ctx.model.Add(total <= len(slots) * busy)
            # ... et s'il vient, c'est pour au moins min_hours_per_day heures.
            # Garde-fou : un prof dont le service total est plus petit que ce
            # minimum ne peut évidemment pas le respecter.
            if self.min_hours_per_day > 1 and total_hours >= self.min_hours_per_day:
                ctx.model.Add(
                    total >= self.min_hours_per_day * busy
                ).OnlyEnforceIf(lit)
            day_busy_vars.append(busy)
            day_totals.append(total)

        # Équilibrage : « il faut que ce soit pédagogique pour les profs comme
        # pour les élèves » (Yossef 08/08). On pénalise la journée la plus
        # chargée au-delà de ce qu'une répartition égale donnerait, ce qui
        # écarte les semaines en 9-3-6-3 au profit des 5-5-6-5.
        allowed = max(1, len(days) - self.min_free_days)
        target = -(-total_hours // allowed) + 1        # ⌈h/jours⌉ + 1 de jeu
        if total_hours >= 6 and target < len(ctx.active_slots(days[0])):
            peak = ctx.model.NewIntVar(0, 40, f"fd_peak_t{self.teacher_id}")
            ctx.model.AddMaxEquality(peak, day_totals)
            over_peak = ctx.model.NewIntVar(0, 40, f"fd_peakover_t{self.teacher_id}")
            ctx.model.Add(over_peak >= peak - target)
            ctx.soft_penalty_terms.append((over_peak, 45))

        # Le PREMIER jour de congé est dur : c'est la règle de l'école, tout
        # prof en a un. Les jours supplémentaires imposés par le barème
        # ימי עבודה sont SOUPLES : ils butent sur la structure des barrettes.
        # ממן חנן, 11h, tombe dans la tranche « 2 jours max », mais ses heures
        # de תקשוב vivent dans les הקבצות de מגמות étalées sur la semaine — en
        # dur, sa seule contrainte rendait tout le modèle infaisable. Et
        # l'emploi du temps réel de תשפ"ו le confirme : 14 profs sur 67 y
        # dépassaient déjà le barème.
        # min_free_days == 0 : le prof renonce à son jour de congé (Yossef).
        if self.min_free_days >= 1 and len(days) > 1:
            ctx.model.Add(sum(day_busy_vars) <= len(days) - 1).OnlyEnforceIf(lit)
        extra = self.min_free_days - 1
        if extra >= 1 and len(days) > self.min_free_days:
            over = ctx.model.NewIntVar(0, extra, f"fd_over_t{self.teacher_id}")
            ctx.model.Add(
                over >= sum(day_busy_vars) - (len(days) - self.min_free_days)
            )
            ctx.soft_penalty_terms.append((over, self.weight or 110))

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
                   min_hours_per_day=params.get("min_hours_per_day", 2),
                   db_id=db_id, priority=priority, weight=weight,
                   origin_description=origin_description)
