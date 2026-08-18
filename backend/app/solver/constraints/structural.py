"""Contraintes STRUCTURELLES — toujours actives, jamais relaxables.

Sans elles, le modèle produit des solutions non-cohérentes (deux cours
en même temps pour la même classe, etc.). Pas stockées en DB, pas
exposées à l'utilisateur. Ajoutées automatiquement par l'engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models import ConstraintPriority
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation

if TYPE_CHECKING:
    from app.solver.context import SolverContext


class _StructuralConstraint(BaseConstraint):
    """Marker base : pas de from_db, pas d'assumption."""
    def __init__(self) -> None:
        super().__init__(priority=ConstraintPriority.HARD)

    @classmethod
    def _build_from_params(cls, **kwargs):  # type: ignore[override]
        raise NotImplementedError("Contraintes structurelles non instanciables depuis la DB.")


class TeacherNoOverlapConstraint(_StructuralConstraint):
    """Un prof ne peut être qu'à un endroit à un instant."""
    constraint_type = "teacher_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for teacher in ctx.teachers:
            group_ids = ctx.groups_of_teacher(teacher.id)
            if len(group_ids) < 2:
                continue
            for day, slot in ctx.all_active_positions():
                # AddAtMostOne : propagateur dédié, bien plus efficace que sum()<=1
                ctx.model.AddAtMostOne(
                    ctx.assigned[g_id][(day, slot)] for g_id in group_ids
                )

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות מורה (מבני)",
            title_fr="Cohérence prof (structurelle)",
            detail_he="מורה לא יכול ללמד שני שיעורים במקביל.",
            detail_fr="Un même enseignant ne peut donner qu'un cours à la fois.",
            origin="מערכת",
        )


class ClassNoOverlapConstraint(_StructuralConstraint):
    """Une classe ne suit qu'un cours à la fois.

    Subtilité barrette : si une classe contribue à PLUSIEURS Groups d'une
    même ParallelCohort, on compte la cohorte comme un seul représentant
    (les autres Groups sont déjà forcés égaux par PARALLEL_COHORT_SAME_SLOT).
    """
    constraint_type = "class_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for cls in ctx.classes:
            group_ids = ctx.groups_of_class(cls.id)
            if len(group_ids) < 2:
                continue
            by_cohort: dict[int | None, list[int]] = {}
            for g_id in group_ids:
                g = ctx.group(g_id)
                by_cohort.setdefault(g.parallel_cohort_id, []).append(g_id)

            # Cohortes de מגמות : découplées de la simultanéité (cf.
            # ParallelCohortSameSlotConstraint), donc l'enveloppe ne représente
            # plus les autres filières. Sémantique תשפ"ו : les מגמות peuvent
            # tourner ENTRE ELLES au même créneau (chaque élève n'est que dans
            # une filière) mais jamais par-dessus un cours commun de la classe
            # — c'est ce trou qui posait אלקטרוניקה sur אנגלית et רובוטיקה
            # sur תנ"ך (Yossef, 11/08).
            def _is_megama_cohort(gs: list[int]) -> bool:
                return len(gs) >= 2 and all(
                    (ctx.group(gid).subject.name_he or "").strip()
                    in MEGAMA_TRACK_SUBJECTS for gid in gs)

            for day, slot in ctx.all_active_positions():
                reps = []
                for cohort_id, gs in by_cohort.items():
                    if cohort_id is None:
                        reps.extend(ctx.assigned[g][(day, slot)] for g in gs)
                    elif _is_megama_cohort(gs):
                        # « une מגמה tourne » = max des filières ; ce booléen
                        # entre dans le AddAtMostOne comme n'importe quel cours.
                        mega = ctx.model.NewBoolVar(
                            f"mega_c{cls.id}_co{cohort_id}_d{day}_s{slot}")
                        ctx.model.AddMaxEquality(
                            mega, [ctx.assigned[g][(day, slot)] for g in gs])
                        reps.append(mega)
                    else:
                        # Représentant = le group ENVELOPPE (max hours) : avec la
                        # sémantique subset, si la cohorte tourne à ce créneau,
                        # c'est lui qui est actif.
                        g_env = max(gs, key=lambda gid: ctx.group(gid).hours_per_week)
                        reps.append(ctx.assigned[g_env][(day, slot)])
                if len(reps) >= 2:
                    ctx.model.AddAtMostOne(reps)

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות כיתה (מבני)",
            title_fr="Cohérence classe (structurelle)",
            detail_he="כיתה לא יכולה להשתתף בשני שיעורים במקביל.",
            detail_fr="Une classe ne peut suivre qu'un cours à la fois.",
            origin="מערכת",
        )


class RoomNoOverlapConstraint(_StructuralConstraint):
    """Une salle accueille au plus une classe à la fois."""
    constraint_type = "room_no_overlap"

    def apply(self, ctx: "SolverContext") -> None:
        for room in ctx.rooms:
            for day, slot in ctx.all_active_positions():
                vars_ = []
                for g_id, slot_map in ctx.room_used.items():
                    if (day, slot) in slot_map and room.id in slot_map[(day, slot)]:
                        vars_.append(slot_map[(day, slot)][room.id])
                if len(vars_) >= 2:
                    ctx.model.AddAtMostOne(vars_)

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="עקביות חדר (מבני)",
            title_fr="Cohérence salle (structurelle)",
            detail_he="חדר יכול לארח רק שיעור אחד בכל זמן.",
            detail_fr="Une salle n'accueille qu'un cours à la fois.",
            origin="מערכת",
        )


# Filières de מגמה : chaque groupe est une population d'élèves à part.
# Elles partagent une barrette pour l'organisation, mais rien ne les
# oblige à tourner à la même heure.
MEGAMA_TRACK_SUBJECTS = {"מחשבים", "אלקטרוניקה", "פיזיקה", "רובוטיקה",
                         "תעבורה", "תקשוב", "צרפתית- מגמה"}

# Cout d'une filiere qui tourne SEULE en milieu de journee (Yossef 13/08 :
# « מה יעשו תלמידים ממגמה אחרת ? »). Tres cher, mais pas interdit : le
# croisement des disponibilites de בגו/ממן/זרדי/טוולייה l'interdirait.
import os as _os_mod
_SYNC_W = int(_os_mod.environ.get("SYNC_WEIGHT", "600"))


class ParallelCohortSameSlotConstraint(_StructuralConstraint):
    """Sémantique ENVELOPPE des barrettes (הקבצות) israéliennes.

    Cas réel AMIT : Math 5 yehidot (5h) + Math 4 (4h) + Math 3 (3h) dans la
    même הקבצה. Forcer l'égalité totale rendrait le modèle infaisable
    (5h ≠ 3h). La vraie sémantique :

    - Les groups au volume MAX (l'« enveloppe ») tournent tous exactement
      aux mêmes créneaux (égalité stricte entre eux).
    - Les groups plus courts tournent UNIQUEMENT pendant les créneaux de
      l'enveloppe (subset) — jamais en dehors.
    - Les heures « en plus » de l'enveloppe (où les courts ne tournent pas)
      sont poussées en bord de journée par EXTRA_HOURS_AT_DAY_EDGE.
    """
    constraint_type = "parallel_cohort_same_slot"

    def apply(self, ctx: "SolverContext") -> None:
        for cohort in ctx.parallel_cohorts:
            groups = list(cohort.groups)
            if len(groups) < 2:
                continue
            # Les filières de מגמה ne s'attendent pas : « tu n'es pas obligé de
            # mettre les מגמות en parallèle de בגו ; un jour ceux-là finiront
            # plus tard, et les autres l'autre jour » (Yossef 10/08). Ce sont
            # des groupes d'élèves distincts, pas une classe qu'on partage à la
            # même heure — les forcer à la simultanéité propageait à six
            # classes les 8h que בגו fige le mercredi.
            import os as _os
            is_megama = all((g.subject.name_he or "").strip() in MEGAMA_TRACK_SUBJECTS
                            for g in groups)
            # « Un prof de מגמה ne peut pas enseigner en plein milieu de la
            # journée sans les autres מגמות — les autres élèves vont faire
            # quoi ? La même chose pour toutes les הקבצות » (Yossef 12/08).
            # Mi-journée (P2-P6, hors vendredi) : tous les groupes d'une
            # cohorte tournent ENSEMBLE. Aux bords, מגמות découplées et heures
            # extra enchainees.
            # SYNC_SOFT ne contient plus que les barrettes de מתמטיקה du lycee
            # (22,23,24) : ce ne sont PAS des מגמות mais des groupes de niveau
            # d'une meme matiere, et les fenetres de בוקריס / קנימח / יפרח
            # empechent la synchronisation dure (Yossef 14/08 : « בוקריס ne
            # fait pas partie des מגמות »). Les vraies מגמות (12,13,14) sont
            # regies par le DEPART COMMUN, en dur.
            # Ancien commentaire : penalite 120/h au lieu de
            # dur (bissection 12/08 : dispos בגו/ממן/זרדי/טוולייה/בוקריס).
            sync_mid = True
            _sync_skip = {int(x) for x in _os.environ.get("SYNC_SKIP", "").split(",") if x.strip()}
            if cohort.id in _sync_skip:
                sync_mid = False
            # Yossef 13/08 : « מחשבים ביב יום חמישי שהוא לבד באמצע השיעורים
            # האחרים — מה יעשו תלמידים ממגמה אחרת ? ». Les cohortes de מגמות
            # (12,13,14) repassent en DUR au milieu de journee : une filiere
            # seule y laisse les autres eleves sans cours. Seules les
            # barrettes de maths du lycee (22,23,24) restent souples — leurs
            # profs n'ont pas assez de creneaux communs (prouve le 12/08).
            # Sync totale des filieres = impossible (בגו mercredi seul, ממן
            # dim+mer, זרדי, טוולייה : aucun creneau commun suffisant).
            # On garde donc la souplesse mais on la rend TRES chere : 600 pts
            # par heure desynchronisee au milieu de journee, au lieu de 120.
            # En תשפ"ו, 24 creneaux mi-journee sur 27 avaient 2 a 4 filieres
            # ensemble — c'est ce profil que le solveur doit retrouver.
            _soft_sync = {int(x) for x in _os.environ.get(
                "SYNC_SOFT", "22,23,24").split(",") if x.strip()}
            soft_sync = cohort.id in _soft_sync
            MID = {1, 2, 3, 4, 5}
            max_h = max(g.hours_per_week for g in groups)
            envelope = [g.id for g in groups if g.hours_per_week == max_h]
            shorter = [g.id for g in groups if g.hours_per_week < max_h]
            ref = envelope[0]
            for pos in ctx.all_active_positions():
                ref_var = ctx.assigned[ref][pos]
                # Le vendredi est un jour « bord » : 4 periodes, seule la
                # מגמת מחשבים y est ouverte — pas de synchronisation.
                mid = sync_mid and pos[1] in MID and pos[0] != 5
                if is_megama:
                    continue
                # Egalite stricte entre les groups enveloppe
                for other in envelope[1:]:
                    ctx.model.Add(ctx.assigned[other][pos] == ref_var)
                # Les courts tournent QUE quand l'enveloppe tourne — et en
                # plein milieu de journee, AVEC elle.
                for short in shorter:
                    ctx.model.Add(ctx.assigned[short][pos] <= ref_var)
                    if mid:
                        if soft_sync:
                            d = ctx.model.NewBoolVar(
                                f"sync_co{cohort.id}_g{short}_d{pos[0]}_s{pos[1]}")
                            ctx.model.Add(d >= ref_var - ctx.assigned[short][pos])
                            ctx.soft_penalty_terms.append((d, _SYNC_W))
                        else:
                            ctx.model.Add(ctx.assigned[short][pos] == ref_var)

            # --- מגמות : DEPART COMMUN, encodage leger -------------------
            # Yossef 13/08 : « בגו mercredi de P5 a P11, les autres מגמות de
            # P5 a P8, et le reste de leurs heures un autre jour, sans lui ».
            # Toutes les filieres actives un jour donne DEMARRENT ensemble ;
            # chacune s'arrete quand ses heures du jour sont faites — elles ne
            # suivent pas בגו jusqu'a P11.
            #
            # Encodage LINEAIRE : une variable « la bande tourne » par creneau,
            # au lieu de comparer les filieres deux a deux (l'encodage
            # quadratique du 13/08 rendait meme la marche 1 introuvable).
            if is_megama and sync_mid and _os.environ.get("MEGA_SYNC", "0") == "1":
                gids = [g.id for g in groups]
                for day in ctx.active_days():
                    slots = ctx.active_slots(day)
                    if len(slots) < 2:
                        continue
                    band, act = {}, {}
                    for s in slots:
                        b = ctx.model.NewBoolVar(f"band_co{cohort.id}_d{day}_s{s}")
                        ctx.model.AddMaxEquality(
                            b, [ctx.assigned[gid][(day, s)] for gid in gids])
                        band[s] = b
                    for gid in gids:
                        a = ctx.model.NewBoolVar(f"mact_co{cohort.id}_g{gid}_d{day}")
                        ctx.model.AddMaxEquality(
                            a, [ctx.assigned[gid][(day, s)] for s in slots])
                        act[gid] = a
                    prev = None
                    for s in slots:
                        st = ctx.model.NewBoolVar(f"bst_co{cohort.id}_d{day}_s{s}")
                        if prev is None:
                            ctx.model.Add(st == band[s])
                        else:
                            ctx.model.Add(st >= band[s] - prev)
                            ctx.model.Add(st <= band[s])
                            ctx.model.Add(st + prev <= 1)
                        for gid in gids:
                            ctx.model.Add(
                                ctx.assigned[gid][(day, s)] >= st + act[gid] - 1)
                        prev = band[s]

    def explain(self, ctx) -> ConstraintExplanation:
        return ConstraintExplanation(
            title_he="הקבצות מקבילות (מבני)",
            title_fr="Barrettes parallèles (structurelle)",
            detail_he="קבוצות באותה הקבצה רצות באותם זמנים (הקצרות בתוך מעטפת הארוכות).",
            detail_fr="Les groupes d'une barrette tournent ensemble (les courts dans l'enveloppe des longs).",
            origin="מערכת",
        )
