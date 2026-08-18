"""TimetableEngine — orchestrateur du solveur.

Flow :
1. Charger les données de l'école (groups, teachers, classes, rooms, time_slots, cohorts)
2. Charger les contraintes actives (DB) + désactiver celles passées en `disabled_constraint_ids`
3. Construire le SolverContext + variables CP-SAT (assigned, room_used)
4. Appliquer contraintes structurelles + DB
5. Solve avec assumptions
6. Si INFEASIBLE → extraire MUS via SufficientAssumptionsForInfeasibility() → SolveConflict
7. Si FEASIBLE/OPTIMAL → écrire les ScheduleEntry → SolveSuccess

Contraintes implicites ajoutées par l'engine (pas dans la table DB) :
- 4 structurelles (TEACHER/CLASS/ROOM no-overlap, PARALLEL_COHORT same-slot)
- GROUP_HOURS_PER_WEEK pour chaque Group (basé sur Group.hours_per_week)
- TEACHER_QUALIFIED_FOR_SUBJECT (préflight)
- Room assignment : si assigned[g][d,s] = 1, exactement une room compatible utilisée
"""

from __future__ import annotations

import json
import logging
import os
import time as _time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Union

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.models import (
    Class,
    Constraint as DBConstraint,
    Group,
    ParallelCohort,
    Room,
    Schedule,
    ScheduleEntry,
    ScheduleStatus,
    School,
    Teacher,
    TimeSlot,
)
from app.solver.constraints import (
    STRUCTURAL_CONSTRAINTS,
    from_db as constraint_from_db,
)
from app.solver.constraints.assignment import TeacherQualifiedForSubjectConstraint
from app.solver.constraints.base import BaseConstraint, ConstraintExplanation
from app.solver.constraints.volume import GroupHoursPerWeekConstraint
from app.solver.context import SolverContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Résultats
# ---------------------------------------------------------------------------

@dataclass
class ConflictItem:
    """Une contrainte identifiée comme causant l'infaisabilité."""
    constraint_id: Optional[int]      # None si contrainte système (qualif, hours_per_week implicite)
    constraint_type: str
    explanation: ConstraintExplanation


@dataclass
class SolveConflict:
    """Résultat quand le solveur est INFEASIBLE. Contient le sous-ensemble
    minimal de contraintes en conflit, prêt à être présenté à l'utilisateur."""
    conflicts: list[ConflictItem]
    solver_time_seconds: float

    @property
    def is_success(self) -> bool:
        return False


@dataclass
class SolveSuccess:
    """Résultat quand un planning a été généré."""
    schedule_id: int
    placed_entries: int
    relaxed_constraint_ids: list[int]
    solver_time_seconds: float

    @property
    def is_success(self) -> bool:
        return True


SolveResult = Union[SolveSuccess, SolveConflict]


@dataclass
class SolveTimeout:
    """Cas dégénéré : ni faisable ni prouvé infaisable dans le temps imparti."""
    solver_time_seconds: float
    is_success: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Matières exemptées de la règle « 2h consécutives » : elles se donnent
# naturellement en heures isolées réparties dans la semaine.
# Classes à journée courte (חינוך מיוחד) : elles doivent finir le plus tôt
# possible. Chaque période au-delà de P5 leur coûte, de plus en plus cher.
SHORT_DAY_CLASS_CODES = {"ז-2", "ח-2", "ט-2"}

# חנ"מ plafonnées à P6 : 30h pour 30 créneaux, remplissage à 100 %. Yossef
# (12/08) leur accorde P7 UNE FOIS par semaine — la 31e case qui donne enfin
# une marge au solveur. L'import ouvre P7 ; ici on limite à un seul jour.
P7_ONCE_CLASSES = {"ז-2", "ח-2"}
P7_SLOT = 6
SHORT_DAY_TARGET_SLOT = 4      # index de P5 : au-delà, ça pénalise

# Part du budget réservée à la phase stricte. Les garanties élèves priment sur
# tout le reste : mieux vaut chercher longtemps une solution stricte que se
# rabattir vite sur une solution souple pleine de trous.
STRICT_PHASE_SHARE = 0.85


class _ProgressCallback(cp_model.CpSolverSolutionCallback):
    """Affiche chaque amélioration et coupe la recherche quand elle stagne.

    Le solveur trouve une bonne solution en quelques minutes puis passe des
    heures à grappiller quelques points de pénalité. Ce callback affiche la
    progression en direct (« où en est-il ? ») et arrête la recherche après
    `stagnation_seconds` sans aucune amélioration — ce qui ramène en pratique
    une génération de 4 h à 30-60 min sans perte visible de qualité.
    """

    def __init__(self, stagnation_seconds: float = 900.0, label: str = "",
                 ctx: Optional[SolverContext] = None,
                 snapshot_path: Optional[Path] = None):
        super().__init__()
        self._stagnation = stagnation_seconds
        self._label = label
        self._n = 0
        self._best: Optional[float] = None
        self._last_improve = 0.0
        self._first_at: Optional[float] = None
        self._ctx = ctx
        self._snap = snapshot_path
        self._last_snap = -1e9

    def _write_snapshot(self, t: float) -> None:
        """Sauvegarde la meilleure solution du moment, consultable pendant
        que le solveur continue (Yossef 12/08 : « je peux aussi voir »)."""
        if self._ctx is None or self._snap is None:
            return
        if t - self._last_snap < 60:       # au plus une fois par minute
            return
        self._last_snap = t
        try:
            out: dict[str, list[list[int]]] = {}
            for g_id, slot_map in self._ctx.assigned.items():
                lab = self._ctx.group(g_id).label
                poss = [[d, s] for (d, s), v in slot_map.items() if self.Value(v)]
                if poss:
                    out.setdefault(lab, [])
                    for p in poss:
                        if p not in out[lab]:
                            out[lab].append(p)
            self._snap.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._snap.with_suffix(".tmp")
            tmp.write_text(json.dumps(
                {"_meta": {"penalty": self._best, "minutes": round(t / 60, 1),
                           "phase": self._label}, "groups": out},
                ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._snap)
        except Exception as exc:                      # jamais bloquer la recherche
            logging.getLogger(__name__).warning("snapshot échoué : %s", exc)

    def on_solution_callback(self) -> None:
        self._n += 1
        obj = self.ObjectiveValue()
        t = self.WallTime()
        if self._first_at is None:
            self._first_at = t
        improved = self._best is None or obj < self._best - 1e-6
        if improved:
            delta = "" if self._best is None else f"  (−{self._best - obj:,.0f})"
            self._best = obj
            self._last_improve = t
            print(f"   [{self._label}] solution #{self._n} à {t/60:5.1f} min : "
                  f"pénalité {obj:,.0f}{delta}", flush=True)
            self._write_snapshot(t)
        elif self._stagnation > 0 and (t - self._last_improve) > self._stagnation:
            print(f"   [{self._label}] plus d'amélioration depuis "
                  f"{self._stagnation/60:.0f} min — arrêt anticipé à {t/60:.1f} min",
                  flush=True)
            self.StopSearch()

    def summarize(self, solver) -> None:
        if self._n == 0:
            print(f"   [{self._label}] aucune solution trouvée "
                  f"({solver.WallTime()/60:.1f} min)", flush=True)
            return
        print(f"   [{self._label}] {self._n} solutions · 1re à "
              f"{(self._first_at or 0)/60:.1f} min · meilleure pénalité "
              f"{self._best:,.0f} · dernière amélioration à "
              f"{self._last_improve/60:.1f} min", flush=True)

# Matière technique portant les ישיבות : groupes de profs sans élèves.
MEETING_SUBJECT = "ישיבות"

BLOCK_EXEMPT_SUBJECTS = {
    'חנ"ג',          # sport
    "מנטורים",       # mentors
    "שיח בוקר",      # échange du matin
    "חינוך",         # heure de vie de classe
    'של"ח',          # sortie / terrain
    "תפילה",         # prière
    # ישיבות n'est PAS exemptée : une réunion de 2h doit se tenir d'un seul
    # tenant. Exemptée, le solveur plaçait ישיבת מחנכים dimanche P3 puis P10.
    # תקשוב non plus : l'emploi du temps תשפ"ו la donne à 100 % en blocs
    # (3 journées de 2h, 15 de 3h et plus). L'exempter aurait poussé ממן חנן,
    # qui ne vient que 2 jours, vers des heures isolées.
    # מחשבת ישראל : « tu peux couper מחשבת en 2, pas obligé de les mettre
    # ensemble » (Yossef 09/08).
    "מחשבת ישראל",
}

# Les מגמות — et elles seules — peuvent faire 3h et plus d'affilée
# (Yossef 08/08 : « que les מגמות »). C'est aussi la pratique de תשפ"ו :
# 19 journées de 3h+ pour מחשבים, 15 pour תקשוב, 12 pour אלקטרוניקה.
# Partout ailleurs, 2h d'affilée est un maximum DUR en mode strict.
MEGAMA_SUBJECTS = {"מחשבים", "אלקטרוניקה", "פיזיקה", "רובוטיקה",
                   "צרפתית- מגמה", "תעבורה", "תקשוב"}

# Matières « en plus » tolérées après la fin de journée du collège (P9-P10).
EXTRA_LATE_SUBJECTS = {"אמירים"}

# Profs autorisés au פיצול : la même matière en DEUX blocs le même jour
# (≤4h/jour au total). C'est la pratique réelle de תשפ"ו :
# · בגו יהונתן ne travaille QUE le mercredi — ses 8h s'y découpent ;
# · דיין משה donnait תלמוד ז en 2h+2h le même jour (P3-P4 puis P7-P8) —
#   « regarde ce qui a été fait l'année dernière » (Yossef 10/08). Sans ça,
#   ses trois barrettes de תלמוד ne tiennent pas sur ses 4 jours.
SPLIT_OK_TEACHERS = {"בגו יהונתן", "דיין משה"}

# Profs dont les heures se donnent par blocs de 2h ou 3h, jamais une heure
# isolée (Yossef 11/08 : « tu peux grouper ses cours en 2 ou 3h ensemble »).
# יצחקי רעות porte les TROIS barrettes d'anglais du lycée — 14h qui ne peuvent
# jamais se chevaucher. Dispersées à l'heure, elles lui faisaient 11 trous.
PAIR_TEACHERS = {"יצחקי רעות"}

# Niveaux de la חטיבה : régime « blocs de 2h obligatoires, jamais 3h de suite ».
HATIVA_LEVELS = {"ז", "ח", "ט"}

# Matières dont les heures se donnent une par jour, jamais deux le même jour :
# « מנטורים, le mieux c'est de les séparer toutes les heures » (Yossef 10/08).
SPREAD_STRICT_SUBJECTS = {"מנטורים"}

# Lycee : matieres dont le volume (8h/classe pour תלמוד) et les jours comptes
# des profs interdisent le bloc de 2h strict. Plafond 3h au lieu de 2h.
LYC3_SUBJECTS = {"תלמוד", 'תנ"ך', "היסטוריה", "אזרחות"}

# Lycee : matieres qui peuvent se donner en DEUX blocs dans la journee
# (2+2 ou 2+1+1) — Yossef 13/08, faute de profs disponibles.
# Yossef 14/08 : « oui bloc mais pas dans la meme journee » — 2+2 veut
# dire deux JOURS differents. Aucune matiere du lycee ne se coupe dans
# la journee.
SPLIT_LYC_SUBJECTS = set()

# Lycee : matieres plafonnees a 2h par jour, etalees sur 2-3 jours.
# Elles ont P8-P9 en compensation (Yossef 13-14/08).
LYC2_STRICT_SUBJECTS = {"היסטוריה", "אזרחות"}


@dataclass
class _AppliedConstraint:
    """Track interne : contrainte appliquée + son origine pour le MUS."""
    instance: BaseConstraint
    db_id: Optional[int]               # None si système


class TimetableEngine:
    def __init__(self, db: Session, school_id: int):
        self.db = db
        self.school_id = school_id
        # Map index de literal CP-SAT → metadata (pour décoder le MUS)
        self._literal_index_to_applied: dict[int, _AppliedConstraint] = {}

    # ---- API publique ----
    def generate(
        self,
        *,
        schedule_name: str = "Généré",
        disabled_constraint_ids: Iterable[int] = (),
        max_time_seconds: float = 30.0,
    ) -> SolveResult | SolveTimeout:
        """Résolution en DEUX PHASES.

        Phase 1 — contraintes EN DUR (pas d'assumptions) : CP-SAT est
        beaucoup plus rapide sans littéraux d'assomption (mesuré ×10+ sur
        l'école réelle : FEASIBLE en 4 min là où le mode assumptions timeout).

        Phase 2 — uniquement si INFEASIBLE : on reconstruit le modèle avec
        les assumptions pour extraire le MUS (dialogue de conflit).
        """
        disabled = set(disabled_constraint_ids)

        # Phase 1a : mode STRICT — les exigences absolues de l'école (départ à
        # P1, aucun trou élève, aucune matière éclatée) sont des contraintes
        # dures. Yossef, 07/08 : « oblige les cours commencent P1 et 0 trous
        # obligatoire ». On lui donne donc l'essentiel du budget : le repli
        # souple ne sert que si le strict est réellement infaisable, et un
        # repli prématuré coûte très cher (11 trous élèves, 18 départs après
        # P1 et 56 matières éclatées lors de la v19).
        ctx, solver, status, _ = self._build_and_solve(
            disabled, max_time_seconds * STRICT_PHASE_SHARE,
            use_assumptions=False, strict=True,
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._save_solution(
                ctx, solver, schedule_name, list(disabled), solver.WallTime(),
                strict=True,
            )

        # Phase 1b : mode souple — ces exigences redeviennent des pénalités.
        ctx, solver, status, _ = self._build_and_solve(
            disabled, max_time_seconds, use_assumptions=False,
        )
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._save_solution(
                ctx, solver, schedule_name, list(disabled), solver.WallTime()
            )
        if status != cp_model.INFEASIBLE:
            return SolveTimeout(solver_time_seconds=solver.WallTime())

        # Phase 2 : diagnostic MUS avec assumptions
        mus_budget = max(30.0, max_time_seconds)
        ctx2, solver2, status2, applied2 = self._build_and_solve(
            disabled, mus_budget, use_assumptions=True,
        )
        if status2 == cp_model.INFEASIBLE:
            return self._build_conflict(ctx2, solver2, applied2, solver2.WallTime())
        if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Rare (budget différent) : on a finalement trouvé une solution.
            return self._save_solution(
                ctx2, solver2, schedule_name, list(disabled), solver2.WallTime()
            )
        return SolveTimeout(solver_time_seconds=solver2.WallTime())

    def _build_and_solve(
        self,
        disabled: set[int],
        max_time_seconds: float,
        *,
        use_assumptions: bool,
        strict: bool = False,
    ):
        """Construit le modèle complet et le résout. Retourne (ctx, solver, status, applied)."""
        self._literal_index_to_applied = {}
        ctx = self._load_data()
        self._create_variables(ctx)

        applied = self._apply_constraints(
            ctx, disabled=disabled, use_assumptions=use_assumptions
        )

        # Objectifs qualité automatiques (école israélienne)
        self._apply_quality_objectives(ctx, strict=strict)
        if ctx.soft_penalty_terms:
            ctx.model.Minimize(sum(expr * weight for expr, weight in ctx.soft_penalty_terms))

        # Warm start : le planning précédent guide la recherche (stabilité + vitesse)
        self._add_warm_start_hints(ctx)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.num_search_workers = 11

        # Arrêt intelligent (Yossef 12/08 : « il peut finir avant ? »). Le
        # solveur trouve une bonne solution assez vite puis grappille pendant
        # des heures. On lui coupe la recherche dès qu'il n'améliore plus.
        # STAGNATION_SECONDS = 0 désactive (comportement historique).
        # Gel ciblé : on fige tout ce qui va déjà bien et on ne laisse le
        # solveur retravailler que les classes citées (Yossef 12/08 : « je peux
        # aussi voir et lui dire quoi améliorer »). Une réparation ciblée prend
        # des minutes là où une recherche complète prend des heures.
        self._apply_freeze(ctx)

        cb = _ProgressCallback(
            stagnation_seconds=float(os.environ.get("SOLVER_STAGNATION", "900")),
            label="strict" if strict else "souple",
            ctx=ctx,
            snapshot_path=self._warm_start_path().with_name(
                f"school_{self.school_id}_live.json"),
        )
        status = solver.Solve(ctx.model, cb)
        cb.summarize(solver)
        return ctx, solver, status, applied

    # ---- Gel ciblé (réparation d'un planning existant) ----
    def _apply_freeze(self, ctx: SolverContext) -> None:
        """FREEZE_EXCEPT='ז-1,ח-3' : fige le planning sauf ces classes.

        Lit la solution de référence dans warm_start/school_<id>_live.json (ou
        le warm start normal) et impose ses créneaux à TOUS les groupes qui ne
        touchent aucune des classes citées. Le solveur ne retravaille alors que
        ce qui pose problème — et il le fait en minutes.
        """
        raw = os.environ.get("FREEZE_EXCEPT", "").strip()
        if not raw:
            return
        free_classes = {c.strip() for c in raw.split(",") if c.strip()}
        src = self._warm_start_path().with_name(f"school_{self.school_id}_live.json")
        if not src.exists():
            src = self._warm_start_path()
        if not src.exists():
            print(f"   ⚠ FREEZE_EXCEPT ignoré : aucune solution de référence", flush=True)
            return
        data = json.loads(src.read_text(encoding="utf-8"))
        ref = data.get("groups", data)          # snapshot live ou warm start
        n_frozen = 0
        for g in ctx.groups:
            if {c.code for c in g.source_classes} & free_classes:
                continue                         # classe à retravailler → libre
            poss = ref.get(g.label)
            if not poss:
                continue
            allowed = {(d, s) for d, s in poss}
            for pos, var in ctx.assigned[g.id].items():
                ctx.model.Add(var == (1 if pos in allowed else 0))
            n_frozen += 1
        print(f"   🔒 gel ciblé : {n_frozen} groupes figés, "
              f"libres = {', '.join(sorted(free_classes))}", flush=True)

    # ---- Chargement données ----
    def _load_data(self) -> SolverContext:
        school = self.db.query(School).filter_by(id=self.school_id).one()
        groups = self.db.query(Group).filter_by(school_id=self.school_id).all()
        teachers = self.db.query(Teacher).filter_by(school_id=self.school_id, is_active=True).all()
        classes = self.db.query(Class).filter_by(school_id=self.school_id).all()
        rooms = self.db.query(Room).filter_by(school_id=self.school_id, is_active=True).all()
        time_slots = self.db.query(TimeSlot).filter_by(school_id=self.school_id).all()
        cohorts = self.db.query(ParallelCohort).filter_by(school_id=self.school_id).all()

        ctx = SolverContext(
            model=cp_model.CpModel(),
            school=school,
            groups=groups,
            teachers=teachers,
            classes=classes,
            rooms=rooms,
            time_slots=time_slots,
            parallel_cohorts=cohorts,
        )
        ctx.build_caches()
        return ctx

    # ---- Variables CP-SAT ----
    def _create_variables(self, ctx: SolverContext) -> None:
        """Variables de décision.

        Salles : en Israël chaque classe a sa כיתת אם (salle fixe) — l'export
        iscool n'affiche même pas les salles. On ne crée donc des variables de
        salle QUE pour les matières exigeant un type spécial (labo, gym…).
        Les autres cours héritent implicitement de la salle de classe
        (room_id NULL dans ScheduleEntry). Sur AMIT ça élimine ~450 000
        variables du modèle.
        """
        positions = ctx.all_active_positions()
        for g in ctx.groups:
            ctx.assigned[g.id] = {}
            for (d, s) in positions:
                ctx.assigned[g.id][(d, s)] = ctx.model.NewBoolVar(f"x_g{g.id}_d{d}_s{s}")

            # Variables de salle : seulement si la matière exige un type spécial
            if not g.subject.required_room_type:
                continue
            compatible = ctx.compatible_rooms(g.id)
            if compatible:
                ctx.room_used[g.id] = {}
                for (d, s) in positions:
                    ctx.room_used[g.id][(d, s)] = {
                        r.id: ctx.model.NewBoolVar(f"r_g{g.id}_d{d}_s{s}_r{r.id}")
                        for r in compatible
                    }
                    # Si assigned, exactement 1 salle utilisée ; sinon, aucune.
                    ctx.model.Add(
                        sum(ctx.room_used[g.id][(d, s)].values())
                        == ctx.assigned[g.id][(d, s)]
                    )

    # ---- Objectifs qualité (école israélienne) ----
    def _apply_quality_objectives(self, ctx: SolverContext, strict: bool = False) -> None:
        import os
        _relax = set(filter(None, os.environ.get("STRICT_RELAX", "").split(",")))
        def _hard(feature: str) -> bool:
            """Diagnostic : la règle `feature` est-elle dure dans cette passe ?"""
            return strict and feature not in _relax
        """Ajoute les pénalités SOFT toujours actives qui font la différence
        entre un planning « légal » et un planning utilisable :

        1. Journée d'une classe = bloc continu qui commence à P1 et va au
           moins jusqu'à P6 (règle de l'école) :
             - aucun trou entre deux cours              → poids 100
             - la journée démarre bien à la 1re période → poids 90
             - elle ne s'arrête pas avant la 6e         → poids 70
        2. Blocs de 2h (demande de l'école) : une matière présente 2× dans la
           même journée doit l'être en heures CONSÉCUTIVES, jamais éparpillée
           (1h le matin + 1h l'après-midi est interdit). Concrètement :
             - au plus UN bloc contigu par (group, jour)      → poids 80
             - au plus 2h par jour (pas de bloc de 3h+)       → poids 40
             - viser ⌈h/2⌉ jours (donc des paires, pas des 1h)→ poids 15
           Exceptions (`BLOCK_EXEMPT_SUBJECTS` + cours ≤ 2h/sem) : sport,
           mentors, heure de vie… → au contraire étalés 1h/jour (poids 8).
        3. Trous profs : un créneau vide entre deux cours d'un prof le même
           jour coûte (poids 6) — « pas trop de trous pour les profs », mais
           toujours subordonné à la compacité des classes.

        `strict=True` : les deux exigences absolues de l'école (aucun trou
        élève, aucune matière éclatée dans la journée) deviennent des
        contraintes DURES au lieu de pénalités. Le solveur ne peut alors plus
        « acheter » une violation, et l'espace de recherche se réduit
        fortement. L'appelant retombe sur strict=False si c'est infaisable.
        """
        # W_BOOST : en phase souple, multiplie les pénalités des règles qui
        # deviennent DURES en strict — la souple converge vers un planning
        # strict-compatible qui sert de warm start (12/08).
        _B = int(os.environ.get("W_BOOST", "1"))
        WEIGHT_GAP = 100 * _B
        WEIGHT_DAY_START = 90 * _B   # classe qui ne commence pas à P1
        WEIGHT_DAY_END = 70      # classe qui termine avant P6
        WEIGHT_SPLIT = 80 * _B   # matière éclatée dans la journée
        WEIGHT_LONG_BLOCK = 40   # plus de 2h d'affilée
        WEIGHT_DAY_SPREAD = 30   # 1h isolée au lieu d'une paire
        WEIGHT_DOUBLE = 8        # doublement des matières exemptées
        # Trou dans la journée d'un prof. Relevé de 6 à 22 le 07/08 : le barème
        # ימי עבודה concentre les services sur moins de jours, ce qui faisait
        # passer les trous de 164 à 288. À 6 points ils pesaient moins de 5 %
        # de l'objectif, donc le solveur les ignorait.
        WEIGHT_TEACHER_GAP = 22
        # Attente de 3h d'affilée ou plus. Le plafond « 3 trous par semaine »
        # a été abandonné le 11/08 : ce n'est pas le nombre de trous qui gêne
        # (ils sont légalement remplis par des heures de שהייה et פרטני) mais
        # la longueur de l'attente. Un trou de 3h de suite est inacceptable
        # pour n'importe quel prof — d'où un poids qui écrase tout le reste.
        WEIGHT_TEACHER_LONG_GAP = 500
        # חטיבה : 3h de suite de la même matière, et heure isolée hors paire.
        # « En ז les cours de maths sont éparpillés, impossible — groupe de 2 ;
        # de même pour תלמוד, 3 heures de suite » (Yossef 11/08).
        WEIGHT_HATIVA_TRIPLE = 300 * _B
        WEIGHT_HATIVA_PAIR = 300 * _B
        # Deux jours où la bande de מגמה démarre à la même heure. « Un jour en
        # P3, un autre en P5, un autre en P7 » (Yossef 12/08) : préférence
        # forte, pas une interdiction — la bande doit tourner dans la journée.
        WEIGHT_MEGA_SAME_START = 120
        WEIGHT_SHORT_DAY = 25    # par période au-delà de P5 pour les חנ"מ
        WEIGHT_EMPTY_DAY = 260   # journée vide : très cher, mais pas interdit
        MIN_END_SLOT = 5         # index de P6 : la journée va au moins jusque-là
        SHORT_END_SLOT = 4       # index de P5 : plancher des journées écourtées
        MIN_FLOOR_SLOT = 3       # index de P4 : aucune journée ne finit avant

        # --- 1. Compacité par classe ---
        # Le vendredi (4 périodes, réservé aux מגמות de יא) n'est pas une
        # journée d'école ordinaire : il ne compte ni pour « cours tous les
        # jours » ni pour le plancher de fin de journée.
        SHORT_WEEKDAY = 5
        school_days = [d for d in ctx.active_days() if d != SHORT_WEEKDAY]
        n_active_days = max(1, len(school_days))
        for cls in ctx.classes:
            group_ids = ctx.groups_of_class(cls.id)
            if not group_ids:
                continue

            # Charge hebdo réelle (une cohorte occupe la classe le temps de
            # son enveloppe, comptée une seule fois).
            standalone = 0
            cohort_env: dict[int, int] = {}
            for g_id in group_ids:
                g = ctx.group(g_id)
                if g.parallel_cohort_id is None:
                    standalone += g.hours_per_week
                else:
                    cohort_env[g.parallel_cohort_id] = max(
                        cohort_env.get(g.parallel_cohort_id, 0), g.hours_per_week
                    )
            class_hours = standalone + sum(cohort_env.values())
            is_short_day = cls.code in SHORT_DAY_CLASS_CODES
            # Le plancher « pas avant P6 » ne s'applique ni aux classes à
            # journée courte (חנ"מ), ni à celles qui n'ont pas assez d'heures
            # pour tenir 6 périodes tous les jours.
            enforce_min_end = (
                not is_short_day
                and class_hours >= (MIN_END_SLOT + 1) * n_active_days
            )
            # Marge de sécurité : י-2 a EXACTEMENT 30h = 6h × 5 jours. Exiger
            # P6 partout revenait à fixer sa semaine au créneau près — prouvé
            # infaisable avec les dispos de ses profs. En dessous de 2h de
            # marge, le plancher descend à P5 (arbitrage Yossef 10/08 :
            # « י-2 peut finir à P5 »).
            # Seuil élargi de +2 à +4 : י-2 (32h) a exactement 2h de marge
            # au-dessus du minimum de 30h, et son mardi est amputé (סבח et
            # גוואטה absents). La bissection additive a prouvé que c'est
            # précisément cette classe qui rend la règle « fin ≥ P6 »
            # contradictoire avec « zéro trou » et « départ à P1 ».
            tight_margin = (
                class_hours < (MIN_END_SLOT + 1) * n_active_days + 4
            )
            # Une classe a cours TOUS les jours de la semaine. Sans cette règle
            # le solveur supprime une journée entière (la règle « P1 → au moins
            # P6 » ne portait que sur les jours actifs, et concentrer la semaine
            # sur 4 jours réduit la pénalité d'étalement des matières) : 6 des
            # 23 classes se retrouvaient avec un lundi totalement vide.
            min_day_hours = 3 if is_short_day else (MIN_END_SLOT + 1)
            enforce_all_days = class_hours >= min_day_hours * n_active_days

            # חנ"מ : finir au plus tôt — chaque période après P5 coûte, et le
            # coût grandit avec l'heure, donc la journée se tasse vers le matin.
            if is_short_day:
                for day in ctx.active_days():
                    for s in ctx.active_slots(day):
                        if s <= SHORT_DAY_TARGET_SLOT:
                            continue
                        lateness = s - SHORT_DAY_TARGET_SLOT
                        for g_id in group_ids:
                            ctx.soft_penalty_terms.append(
                                (ctx.assigned[g_id][(day, s)], WEIGHT_SHORT_DAY * lateness)
                            )
            # Représentants dédupliqués par cohorte (même logique que ClassNoOverlap)
            def _is_megama_cohort(gs: list[int]) -> bool:
                return len(gs) >= 2 and all(
                    (ctx.group(gid).subject.name_he or "").strip()
                    in MEGAMA_SUBJECTS for gid in gs)

            by_cohort: dict[int | None, list[int]] = {}
            for g_id in group_ids:
                g = ctx.group(g_id)
                by_cohort.setdefault(g.parallel_cohort_id, []).append(g_id)

            p7_days: list[cp_model.IntVar] = []
            for day in school_days:
                slots = ctx.active_slots(day)
                if len(slots) < 3:
                    continue
                # busy[s] = OR(cours de la classe à ce créneau)
                busy: dict[int, cp_model.IntVar] = {}
                for s in slots:
                    reps = []
                    for cohort_id, gs in by_cohort.items():
                        if cohort_id is None:
                            reps.extend(ctx.assigned[g][(day, s)] for g in gs)
                        elif _is_megama_cohort(gs):
                            # BUG corrigé le 13/08 : une cohorte de מגמות n'est
                            # PAS synchronisée, son enveloppe ne represente donc
                            # pas les autres filieres. En prenant l'enveloppe,
                            # תקשוב seul en P9-P10 laissait la classe « libre »
                            # aux yeux du moteur — et ses eleves avec 3h de trou
                            # (יב-3 dimanche, schedule 7). On prend le MAX de
                            # toutes les filieres : si l'une tourne, la classe
                            # est occupee.
                            reps.extend(ctx.assigned[g][(day, s)] for g in gs)
                        else:
                            g_env = max(gs, key=lambda gid: ctx.group(gid).hours_per_week)
                            reps.append(ctx.assigned[g_env][(day, s)])
                    b = ctx.model.NewBoolVar(f"busy_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(b, reps)
                    busy[s] = b

                # ז-2 / ח-2 : P7 ouvert UNE SEULE FOIS dans la semaine
                # (Yossef 12/08). Ces deux classes de חנ"מ ont 30h pour
                # 30 créneaux si elles s'arrêtent à P6 — remplissage à 100 %,
                # aucune marge. Cette 31e case leur en donne enfin une.
                if cls.code in P7_ONCE_CLASSES and P7_SLOT in busy:
                    p7_days.append(busy[P7_SLOT])

                # before[i] = classe a eu cours à un créneau <= i
                # after[i]  = classe a cours à un créneau >= i
                before: dict[int, cp_model.IntVar] = {}
                after: dict[int, cp_model.IntVar] = {}
                prev = None
                for s in slots:
                    v = ctx.model.NewBoolVar(f"bef_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if prev is None else [busy[s], prev])
                    before[s] = v
                    prev = v
                nxt = None
                for s in reversed(slots):
                    v = ctx.model.NewBoolVar(f"aft_c{cls.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if nxt is None else [busy[s], nxt])
                    after[s] = v
                    nxt = v

                # gap[i] = 1 ssi cours avant ET cours après ET créneau vide
                # (linéarisé : gap >= before[i-1] + after[i+1] - busy[i] - 1 ;
                #  la minimisation pousse gap à 0 quand c'est permis)
                for idx in range(1, len(slots) - 1):
                    s = slots[idx]
                    if _hard("gaps"):
                        # Aucun trou toléré : cours avant + cours après ⇒ occupé
                        ctx.model.Add(
                            before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] <= 1
                        )
                        continue
                    gap = ctx.model.NewBoolVar(f"gap_c{cls.id}_d{day}_s{s}")
                    ctx.model.Add(
                        gap >= before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] - 1
                    )
                    ctx.soft_penalty_terms.append((gap, WEIGHT_GAP))

                # Amplitude de journée : une classe qui a cours ce jour-là
                # commence à P1 et ne termine pas avant P6 (règle de l'école).
                day_active = ctx.model.NewBoolVar(f"dayon_c{cls.id}_d{day}")
                ctx.model.AddMaxEquality(day_active, list(busy.values()))

                # Créneaux réellement ouverts à cette classe ce jour-là : le
                # lundi, la חטיבה s'arrête tôt pour libérer les ישיבות. Sans
                # cette prise en compte, on lui demandait d'aller jusqu'à P6
                # un jour où l'école lui ferme P5 et au-delà — contradiction
                # qui rendait TOUT le mode strict infaisable.
                blocked = ctx.class_blocked.get((cls.id, day), set())
                open_slots = [s for s in slots if s not in blocked]
                if not open_slots:
                    continue
                # Les jours où l'école raccourcit la journée d'une classe, on
                # baisse aussi le plancher de fin : le lundi la חטיבה peut
                # s'arrêter dès P5 (« même faire finir une classe en P5 c'est
                # ok », Yossef 07/08), ce qui donne au solveur la marge dont il
                # a besoin pendant que les 21 mentors sont en réunion.
                # Jour écourté par l'école (lundi חטיבה) : plancher P4 — pendant
                # la réunion des mentors (P5-P6), les profs restants ne suffisent
                # plus à couvrir les 13 classes depuis la disparition de
                # כישורי חיים qui se chargeait de ce créneau en תשפ"ו
                # (arbitrage Yossef 10/08 : « חטיבה peut finir P4 lundi »).
                # Plancher DUR : P4 (« 0 trous obligatoire, tu peux lâcher la
                # fin de journée max P4 », Yossef 10/08). Le zéro trou et le
                # départ à P1 restent intouchables ; c'est la fin de journée
                # qui cède, et seulement là où c'est nécessaire puisque P6
                # reste visé par la pénalité ci-dessous.
                floor = MIN_FLOOR_SLOT
                prefer = MIN_END_SLOT
                # « Aucune journee ne finit avant P6, a part le lundi »
                # (Yossef 14/08). Le lundi garde son plancher bas : les
                # reunions y liberent la fin de journee. Les חנ"מ gardent
                # leur fin anticipee. Soupape : STRICT_RELAX=end6.
                if day != 1 and not is_short_day and _hard("end6"):
                    floor = max(floor, MIN_END_SLOT)
                # « Les ט doivent finir un peu plus tard » (Yossef 13/08) :
                # ils sortaient a P5 le mardi. Plancher remonte a P6 et cible
                # P8 — ils ont droit a P9 par ailleurs.
                # « Les ט doivent finir un peu plus tard » (Yossef 13/08).
                # תשפ"ו le confirme : ט-1/3/4 finissaient a P8 tous les jours
                # (P9 le lundi) ; seul ט-2, le חנ"מ, sortait a P6-P7.
                if ((cls.code or "").split("-")[0].strip() == "ט"
                        and not is_short_day):
                    # Plancher DUR laisse a P4 : le remonter a P7 rendait la
                    # marche 1 introuvable (13/08 soir). On vise P8 par la
                    # penalite, ce qui reproduit תשפ"ו sans bloquer le modele.
                    prefer = 7
                last_required = (
                    open_slots[floor]
                    if enforce_min_end and len(open_slots) > floor
                    else None
                )
                first_slot = open_slots[0]
                # Viser P6 : pénalité si la journée s'arrête avant, sans
                # jamais l'interdire.
                if (enforce_min_end and not blocked
                        and len(open_slots) > prefer and prefer > floor):
                    short_end = ctx.model.NewBoolVar(f"shortend_c{cls.id}_d{day}")
                    ctx.model.Add(short_end >= day_active - busy[open_slots[prefer]])
                    ctx.soft_penalty_terms.append((short_end, WEIGHT_DAY_END))

                # « Cours tous les jours » : préférence LOURDE, pas une
                # obligation. C'est une règle que j'avais ajoutée moi-même
                # (six classes se retrouvaient sans cours le lundi), et elle
                # est la dernière à rendre le modèle infaisable : combinée au
                # zéro trou et au départ à P1, elle exige un bloc continu
                # depuis P1 les cinq jours, ce qu'aucune disponibilité prof ne
                # permet partout. Le solveur donnera les 5 jours à presque
                # toutes les classes et signalera les exceptions.
                if enforce_all_days:
                    # « 5 jours obligatoires » (Yossef 13/08) : י-2 avait perdu
                    # son jeudi et recupere 10h le dimanche.
                    if _hard("allday"):
                        ctx.model.Add(day_active == 1)
                    else:
                        empty = ctx.model.NewBoolVar(f"emptyday_c{cls.id}_d{day}")
                        ctx.model.Add(empty >= 1 - day_active)
                        ctx.soft_penalty_terms.append((empty, WEIGHT_EMPTY_DAY))
                if strict:
                    if _hard("start"):
                        ctx.model.Add(busy[first_slot] == day_active)
                    if last_required is not None and _hard("end"):
                        ctx.model.Add(busy[last_required] >= day_active)
                else:
                    late = ctx.model.NewBoolVar(f"late_c{cls.id}_d{day}")
                    ctx.model.Add(late >= day_active - busy[first_slot])
                    ctx.soft_penalty_terms.append((late, WEIGHT_DAY_START))
                    if last_required is not None:
                        early = ctx.model.NewBoolVar(f"early_c{cls.id}_d{day}")
                        ctx.model.Add(early >= day_active - busy[last_required])
                        ctx.soft_penalty_terms.append((early, WEIGHT_DAY_END))

            # « ז-2 et ח-2 peuvent aller jusqu'à P7 UNE FOIS dans la semaine »
            # (Yossef 12/08) : une seule journée de la semaine touche P7.
            if p7_days:
                ctx.model.Add(sum(p7_days) <= 1)

        # --- 1-bis. מתמטיקה : seules les heures EXTRA (au-delà du socle commun
        # de la barrette) peuvent tomber après P8 (Yossef 11/08 : « math
        # peuvent finir à p10 mais seulement les heures extra »). L'import
        # bloque P9-P10 pour les groupes au socle ; ici on borne les groupes
        # renforcés : pas plus de (heures - socle) créneaux tardifs.
        for g in ctx.groups:
            if (g.subject.name_he or "").strip() != "מתמטיקה":
                continue
            if g.parallel_cohort_id is None or g.parallel_cohort is None:
                continue
            cmin = min(o.hours_per_week for o in g.parallel_cohort.groups)
            if g.hours_per_week <= cmin:
                continue
            late_vars = [ctx.assigned[g.id][(d, s)]
                         for d in ctx.active_days()
                         for s in ctx.active_slots(d) if s > 7]
            if late_vars:
                ctx.model.Add(sum(late_vars) <= g.hours_per_week - cmin)

        # --- 1-ter. Vendredi : une seule classe (Yossef 12/08 : « si tu mets
        # le vendredi tu es obligé de mettre une seule classe »). Le vendredi
        # n'est ouvert qu'aux groupes de מחשבים de כהן זרדי ; au plus UN des
        # trois peut y avoir cours.
        FRIDAY = 5
        fri_slots = ctx.active_slots(FRIDAY)
        if fri_slots:
            fri_used = []
            for g in ctx.groups:
                fvars = [ctx.assigned[g.id][(FRIDAY, s)] for s in fri_slots
                         if (FRIDAY, s) in ctx.assigned[g.id]]
                if not fvars:
                    continue
                u = ctx.model.NewBoolVar(f"friuse_g{g.id}")
                ctx.model.AddMaxEquality(u, fvars)
                fri_used.append(u)
            if len(fri_used) >= 2:
                ctx.model.Add(sum(fri_used) <= 1)

        # --- 1-quater. Départ des bandes de מגמה (Yossef 12/08) : « ils
        # peuvent commencer à P1 mais que le mercredi ; les autres jours ils
        # peuvent commencer un jour en P3, un autre en P5, un autre en P7 ».
        # Donc : hors mercredi la bande ne démarre jamais avant P3, et deux
        # jours ne démarrent pas à la même heure — la bande tourne dans la
        # journée au lieu de figer les mêmes créneaux toute la semaine.
        WEDNESDAY = 3
        mega_by_cohort: dict[int, list] = defaultdict(list)
        for g in ctx.groups:
            if (g.subject.name_he or "").strip() in MEGAMA_SUBJECTS \
                    and g.parallel_cohort_id is not None:
                mega_by_cohort[g.parallel_cohort_id].append(g)
        for coh_id, gs in mega_by_cohort.items():
            starts_by_slot: dict[int, list] = defaultdict(list)
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                if not slots:
                    continue
                # band[s] : au moins une filière de la bande tourne en s
                band = {}
                for s in slots:
                    b = ctx.model.NewBoolVar(f"mgb_c{coh_id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(
                        b, [ctx.assigned[g.id][(day, s)] for g in gs])
                    band[s] = b

                # Hors mercredi la bande ne démarre pas avant P3 : il suffit
                # d'interdire toute activité sur P1-P2 ce jour-là.
                if day != WEDNESDAY and _hard("megastart"):
                    for s in slots:
                        if s < 2:
                            ctx.model.Add(band[s] == 0)

                # started[s] = la bande a déjà tourné en s ou avant.
                # start[s] = started[s] − started[s−1] vaut 1 au tout premier
                # créneau occupé de la journée, 0 partout ailleurs.
                started = {}
                prefix = []
                for s in slots:
                    prefix.append(band[s])
                    v = ctx.model.NewBoolVar(f"mgo_c{coh_id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, list(prefix))
                    started[s] = v
                if day != WEDNESDAY:
                    prev = None
                    for s in slots:
                        st = started[s] if prev is None else (started[s] - prev)
                        starts_by_slot[s].append(st)
                        prev = started[s]

            # Deux jours ne commencent pas à la même heure : un jour P3,
            # un autre P5, un autre P7.
            for s, flags in starts_by_slot.items():
                if len(flags) >= 2:
                    dup = ctx.model.NewIntVar(0, len(flags), f"mgdup_c{coh_id}_s{s}")
                    ctx.model.Add(dup >= sum(flags) - 1)
                    ctx.soft_penalty_terms.append((dup, WEIGHT_MEGA_SAME_START))

        # --- 2. Blocs de 2h consécutives (ou étalement pour les exemptées) ---
        days_list = ctx.active_days()
        n_days = len(days_list)
        for g in ctx.groups:
            if g.hours_per_week <= 1 or n_days == 0:
                continue
            subject_he = (g.subject.name_he or "").strip()

            # Une réunion se tient d'un seul tenant, le même jour. La règle
            # générale ne suffit pas : un cours de 2h est exempté d'office, et
            # la branche « exemptée » pénalise justement d'avoir 2h le même
            # jour — c'est ce qui envoyait ישיבת מחנכים dimanche P3 puis P10.
            if subject_he == MEETING_SUBJECT:
                day_used = []
                for day in days_list:
                    slots = ctx.active_slots(day)
                    if not slots:
                        continue
                    total = sum(ctx.assigned[g.id][(day, s)] for s in slots)
                    used = ctx.model.NewBoolVar(f"muse_g{g.id}_d{day}")
                    ctx.model.Add(total <= len(slots) * used)
                    ctx.model.Add(total >= used)
                    day_used.append(used)
                    # Un seul bloc continu dans la journée.
                    prev = None
                    starts = []
                    for s in slots:
                        st = ctx.model.NewBoolVar(f"mstart_g{g.id}_d{day}_s{s}")
                        cur = ctx.assigned[g.id][(day, s)]
                        ctx.model.Add(st >= cur if prev is None else st >= cur - prev)
                        starts.append(st)
                        prev = cur
                    ctx.model.Add(sum(starts) <= 1)
                if day_used and _hard("meet"):
                    ctx.model.Add(sum(day_used) == 1)   # tout le même jour
                continue

            exempt = subject_he in BLOCK_EXEMPT_SUBJECTS or g.hours_per_week <= 2

            # Régime חטיבה (Yossef 11/08) : « au collège ne pas faire 3 heures
            # de suite de la même matière, faire le moins de séparé, il faut
            # qu'il y ait des blocs de deux heures par matière, obligé ».
            # Donc : jamais plus de 2h/jour, et jamais une heure isolée — sauf
            # une seule fois quand le volume hebdomadaire est impair (5h = 2+2+1).
            # Le sport, של"ח, מנטורים et חינוך gardent leur régime dispersé.
            # La colonne « לפצל שעות » du fichier de Yossef dit quelles matières
            # PEUVENT se donner heure par heure (12/08 : « pas toutes les
            # matières doivent être un bloc de deux heures, dans l'Excel il y a
            # un signe »). Les matières cochées — אזרחות, היסטוריה, חנ"ג,
            # מנטורים et une partie de הלכה — échappent donc à la règle des
            # paires. C'est précisément de les y avoir soumises qui rendait le
            # mode strict INFEASIBLE : elles apportent 6 à 9 heures par classe
            # qui doivent rester libres de s'insérer entre les blocs.
            _skip = {c.strip() for c in os.environ.get("PAIRS_SKIP", "").split(",") if c.strip()}
            _in_hativa = any((c.code or "").split("-")[0] in HATIVA_LEVELS
                             for c in g.source_classes)
            hativa_pairs = (
                (not exempt)
                and not bool(getattr(g, "can_split", False))
                and subject_he not in _skip
                and any((c.code or "").split("-")[0] in HATIVA_LEVELS
                        and (c.code or "") not in _skip
                        and (c.code or "").split("-")[0] not in _skip
                        for c in g.source_classes))
            # Yossef 14/08 : « ז-2, pas 4h dans la meme journee mais 2+2 ».
            # Les classes de PAIRS_SKIP (ז-2, י-2) sont dispensees de l'
            # OBLIGATION de paires — mais le PLAFOND de 2h par jour et par
            # matiere s'applique quand meme a tout le college.
            hativa_cap = (not exempt) and _in_hativa and not hativa_pairs
            pair_deficits = []

            day_used_vars = []
            for day in days_list:
                slots = ctx.active_slots(day)
                if not slots:
                    continue
                day_total = sum(ctx.assigned[g.id][(day, s)] for s in slots)

                if exempt:
                    # Matières hors blocs : au plus 1h/jour, réparties.
                    if subject_he in SPREAD_STRICT_SUBJECTS and _hard("ment3"):
                        # « 3h de suite de מנטורים en ז-4, faut changer »
                        # (Yossef 13/08) : 3h jamais, 2h tolerees mais cheres.
                        ctx.model.Add(day_total <= 2)
                    if subject_he in SPREAD_STRICT_SUBJECTS and _hard("spread1"):
                        # 1h/jour ideal — desactive par defaut le 13/08
                        # (« tu peux faire 2h mentor si c'est complique »).
                        ctx.model.Add(day_total <= 1)
                    else:
                        excess = ctx.model.NewIntVar(0, len(slots), f"dbl_g{g.id}_d{day}")
                        ctx.model.Add(excess >= day_total - 1)
                        _w_dbl = 250 if subject_he in SPREAD_STRICT_SUBJECTS else WEIGHT_DOUBLE
                        ctx.soft_penalty_terms.append((excess, _w_dbl))
                        # Jamais coupée dans la journée — vaut aussi pour les
                        # matières hors blocs (חנ"ג יב-1 P5+P8, 12/08) : si 2h
                        # le même jour, elles se suivent.
                        if _hard("split"):
                            st_ex, prev_ex = [], None
                            for s in slots:
                                v = ctx.model.NewBoolVar(f"xstart_g{g.id}_d{day}_s{s}")
                                cur = ctx.assigned[g.id][(day, s)]
                                if prev_ex is None:
                                    ctx.model.Add(v >= cur)
                                else:
                                    ctx.model.Add(v >= cur - prev_ex)
                                st_ex.append(v)
                                prev_ex = cur
                            ctx.model.Add(sum(st_ex) <= 1)
                    continue

                # a) Compter les débuts de bloc : start[s] = 1 si le cours
                #    commence ici (actif en s, inactif au créneau précédent).
                starts = []
                prev = None
                for s in slots:
                    st = ctx.model.NewBoolVar(f"bstart_g{g.id}_d{day}_s{s}")
                    cur = ctx.assigned[g.id][(day, s)]
                    if prev is None:
                        ctx.model.Add(st >= cur)
                    else:
                        ctx.model.Add(st >= cur - prev)
                    starts.append(st)
                    prev = cur
                # >1 début = matière éclatée dans la journée
                teacher_names = {t.first_name for t in g.teachers}
                # Groupe « enveloppe » d'une barrette inégale : ses heures en
                # extra peuvent s'enchaîner longuement en fin de journée
                # (« pour math tu peux faire comme anglais ; même plus que 3h
                # d'affilée en fin de journée », Yossef 11/08).
                is_envelope = bool(
                    g.parallel_cohort_id is not None
                    and g.parallel_cohort is not None
                    and any(o.hours_per_week < g.hours_per_week
                            for o in g.parallel_cohort.groups))
                # « לפצל שעות » coché par Yossef sur ce cours : ses heures
                # peuvent se donner en deux fois dans la journée. C'est cette
                # colonne, restée inexploitée, qui rendait la règle du bloc
                # unique contradictoire avec le zéro trou.
                # « Beaucoup de profs manquent, donc le mieux est 2+2, sinon
                # 2+1+1 » (Yossef 13/08) : היסטוריה et אזרחות du lycee peuvent
                # se donner en deux blocs dans la journee.
                _lyc = any((c.code or "").split("-")[0].strip() in ("י", "יא", "יב")
                           for c in g.source_classes)
                split_ok = (bool(teacher_names & SPLIT_OK_TEACHERS)
                            or bool(getattr(g, "can_split", False))
                            or (_lyc and subject_he in SPLIT_LYC_SUBJECTS))
                if _hard("split"):
                    # un seul bloc — deux pour les profs au régime פיצול
                    ctx.model.Add(sum(starts) <= (2 if split_ok else 1))
                else:
                    split = ctx.model.NewIntVar(0, len(slots), f"bsplit_g{g.id}_d{day}")
                    ctx.model.Add(split >= sum(starts) - 1)
                    ctx.soft_penalty_terms.append((split, WEIGHT_SPLIT))

                # c) Jour utilisé ? (pour viser des paires plutôt que des 1h)
                used = ctx.model.NewBoolVar(f"bused_g{g.id}_d{day}")
                ctx.model.Add(day_total <= len(slots) * used)
                ctx.model.Add(day_total >= used)
                day_used_vars.append(used)

                # b) Pas plus de 2h d'affilée. Seules les מגמות y échappent
                #    (Yossef 08/08 : « que les מגמות ») — mais elles ne
                #    peuvent pas non plus tenir en une heure isolée : un
                #    atelier d'une heure n'a pas de sens pédagogique.
                if (hativa_cap and _hard("pairs")
                        and os.environ.get("HATIVA_CAP", "1") == "1"):
                    ctx.model.Add(day_total <= 2)
                if hativa_pairs:
                    # 3h dans la journée reste possible — « pour les matières
                    # de 5h au collège tu peux faire 3+2, mais ce n'est pas top,
                    # 3h d'affilée c'est dur pour un prof » (Yossef 12/08).
                    # תשפ"ו lui donne raison : les 5h y étaient en 2+2+1, et il
                    # n'y a eu que 22 blocs de 3h+ sur 595. D'où : plafond dur à
                    # 3h, mais chaque 3e heure coûte cher — c'est une soupape,
                    # pas un format.
                    if _hard("pairs"):
                        # « Essaye de deplacer la 3e heure de math un autre
                        # jour pour ne pas avoir 3h de suite » (Yossef 13/08) :
                        # les 5h se donnent en 2+2+1, jamais 3+2.
                        # EXCEPTION (14/08) : les barrettes ou enseigne
                        # רחום שני — dispo dim+lun+mar-matin seulement — ont
                        # droit a 3+2. La barrette etant simultanee, le droit
                        # vaut pour toute la cohorte.
                        # « Deplace la 3e heure un autre jour SI C'EST
                        # POSSIBLE » (Yossef 13/08) : plafond DUR a 3h,
                        # et la 3e heure coute cher (WEIGHT_HATIVA_TRIPLE
                        # ci-dessous) — le solveur fait 2+2+1 partout ou il
                        # peut, 3+2 seulement la ou il faut (רחום שני...).
                        if os.environ.get("PAIRS_CAP3", "1") == "1":
                            ctx.model.Add(day_total <= 3)
                    over = ctx.model.NewIntVar(0, len(slots), f"h3_g{g.id}_d{day}")
                    ctx.model.Add(over >= day_total - 2)
                    ctx.soft_penalty_terms.append((over, WEIGHT_HATIVA_TRIPLE))
                    # une heure seule ce jour-là = un « manque » à comptabiliser
                    deficit = ctx.model.NewIntVar(0, 2, f"hpair_g{g.id}_d{day}")
                    ctx.model.Add(deficit >= 2 * used - day_total)
                    pair_deficits.append(deficit)
                elif subject_he in MEGAMA_SUBJECTS or (teacher_names & PAIR_TEACHERS):
                    if _hard("meg2"):
                        ctx.model.Add(day_total >= 2 * used)
                    # « 4h de suite de מגמות au milieu de la journee, pas
                    # possible » (Yossef 13/08) : au-dela de 3h il faut que la
                    # bande touche la fin de journee (P8+).
                    if _hard("meg4"):
                        tail = [ctx.assigned[g.id][(day, s)] for s in slots if s >= 7]
                        if tail:
                            at_end = ctx.model.NewBoolVar(f"megend_g{g.id}_d{day}")
                            ctx.model.AddMaxEquality(at_end, tail)
                            ctx.model.Add(day_total <= 3).OnlyEnforceIf(at_end.Not())
                        else:
                            ctx.model.Add(day_total <= 3)
                elif not is_envelope:
                    # Yossef 12/08 : blocs de 2h visés au lycée (en dur c'était
                    # infaisable — תלמוד 8h, profs à jours comptés) : chaque
                    # heure au-delà de 2 dans la journée coûte 100 au lycée.
                    is_lycee = any((c.code or "").split("-")[0].strip() in ("י", "יא", "יב")
                                   for c in g.source_classes)
                    # Yossef 13/08 : « 3-4h de suite d'histoire ou de תנ"ך,
                    # pas possible ». Blocs de 2h au lycee — DUR. Exception :
                    # les membres d'une barrette INEGALE, dont les heures extra
                    # s'enchainent en fin de journee (בוקריס : 6-7h de maths
                    # sur 2 jours utiles). Soupapes : STRICT_RELAX=lyc2,
                    # LYC2_SKIP=<matiere ou prof>.
                    in_unequal_cohort = bool(
                        g.parallel_cohort_id is not None
                        and g.parallel_cohort is not None
                        and any(o.hours_per_week != g.hours_per_week
                                for o in g.parallel_cohort.groups))
                    _lyc2_skip = {x.strip() for x in os.environ.get("LYC2_SKIP", "").split(",") if x.strip()}
                    if (is_lycee and subject_he != "ישיבות" and _hard("lyc2")
                            and not in_unequal_cohort
                            and subject_he not in _lyc2_skip
                            and not (teacher_names & _lyc2_skip)):
                        if subject_he in LYC2_STRICT_SUBJECTS:
                            # « Le mieux c'est 2+2, sinon 2+1+1 » (Yossef
                            # 13-14/08) : 2h par jour maximum, etalees sur
                            # deux ou trois JOURS — jamais deux blocs dans la
                            # meme journee. P8-P9 leur sont ouverts en
                            # compensation.
                            ctx.model.Add(day_total <= 2)
                        else:
                            # « Pas tous ensemble » : jamais 4 heures
                            # D'AFFILEE. Cale sur תשפ"ו, ou 2h etait la norme
                            # (187 journees) et 3h existait (68).
                            for i2 in range(len(slots) - 3):
                                w = slots[i2:i2 + 4]
                                if w[3] == w[0] + 3:
                                    ctx.model.Add(
                                        sum(ctx.assigned[g.id][(day, s)] for s in w) <= 3)
                    over = ctx.model.NewIntVar(0, len(slots), f"blong_g{g.id}_d{day}")
                    ctx.model.Add(over >= day_total - 2)
                    ctx.soft_penalty_terms.append(
                        (over, 100 if is_lycee else WEIGHT_LONG_BLOCK))

                # « Si tu veux faire une suite de 4h d'affilee — מגמות ou
                # heures extra de maths — il faut commencer a P6, pas a P4 »
                # (Yossef 14/08). Toute sequence de 4 heures consecutives doit
                # donc demarrer au creneau P6 (index 5) ou plus tard.
                if _hard("run4"):
                    for i4 in range(len(slots) - 3):
                        w = slots[i4:i4 + 4]
                        if w[3] == w[0] + 3 and w[0] < 5:
                            ctx.model.Add(
                                sum(ctx.assigned[g.id][(day, s)] for s in w) <= 3)

                # « Pour les י, les cours suivis de math, mieux vaut commencer
                # a partir de P5 ou P6 » (Yossef 13/08) : un bloc de 3h+ de
                # maths au lycee ne demarre pas avant P5.
                if (subject_he == "מתמטיקה" and _hard("math5")
                        and any((c.code or "").split("-")[0].strip() in ("י", "יא", "יב")
                                for c in g.source_classes)):
                    for i in range(len(slots) - 2):
                        w = slots[i:i + 3]
                        if w[2] == w[0] + 2 and w[0] < 4:
                            ctx.model.Add(
                                sum(ctx.assigned[g.id][(day, s)] for s in w) <= 2)

                # « On ne peut pas mettre 3 heures de suite en plein milieu de
                # la journée » (Yossef 12/08) : une 3e heure consécutive n'est
                # licite qu'en fin de journée (P7+). DUR en strict (sauf
                # MID3_SKIP : מתמטיקה — verrou בוקריס), pénalité 200 sinon.
                _mid3_skip = {x.strip() for x in os.environ.get("MID3_SKIP", "").split(",") if x.strip()}
                if (subject_he not in MEGAMA_SUBJECTS and subject_he != "ישיבות"
                        and subject_he not in _mid3_skip
                        and not (teacher_names & _mid3_skip)):
                    for i in range(len(slots) - 2):
                        s0, s1, s2 = slots[i], slots[i + 1], slots[i + 2]
                        if s2 <= 5 and s1 == s0 + 1 and s2 == s1 + 1:
                            w3 = (ctx.assigned[g.id][(day, s0)]
                                  + ctx.assigned[g.id][(day, s1)]
                                  + ctx.assigned[g.id][(day, s2)])
                            if _hard("mid3"):
                                ctx.model.Add(w3 <= 2)
                            else:
                                ov3 = ctx.model.NewBoolVar(
                                    f"mid3_g{g.id}_d{day}_i{i}")
                                ctx.model.Add(w3 - 2 <= ov3)
                                ctx.soft_penalty_terms.append((ov3, 200))

            # c-bis) חטיבה : toutes les journées en paires, sauf une seule
            # heure isolée tolérée quand le volume hebdomadaire est impair.
            if pair_deficits:
                allowed = g.hours_per_week % 2
                if _hard("pairs") and os.environ.get("PAIRS_PART", "1") == "1":
                    ctx.model.Add(sum(pair_deficits) <= allowed)
                else:
                    lone = ctx.model.NewIntVar(0, 2 * len(pair_deficits), f"hlone_g{g.id}")
                    ctx.model.Add(lone >= sum(pair_deficits) - allowed)
                    ctx.soft_penalty_terms.append((lone, WEIGHT_HATIVA_PAIR))

            # d) Nombre de jours ≈ ⌈h/2⌉ : au-delà, ce sont des heures isolées.
            if day_used_vars:
                target_days = (g.hours_per_week + 1) // 2
                extra_days = ctx.model.NewIntVar(0, n_days, f"bdays_g{g.id}")
                ctx.model.Add(extra_days >= sum(day_used_vars) - target_days)
                ctx.soft_penalty_terms.append((extra_days, WEIGHT_DAY_SPREAD))

        # --- 3. Trous profs (même chaîne before/after que la compacité classe) ---
        # Plafond hebdomadaire : « il faut qu'il y ait chez les profs max 3
        # trous » (Yossef 07/08). Dur en mode strict, repli en pénalité sinon.
        # « ט-4 le meme jour toute la journee avec le meme prof, ils vont
        # peter un cable » (Yossef 13/08) : בראונר y faisait 8h d'affilee le
        # mardi. Un prof ne donne pas plus de 4h par jour a une meme classe.
        # Soupape : STRICT_RELAX=samet.
        if _hard("samet"):
            for cls in ctx.classes:
                by_teacher: dict[int, list[int]] = {}
                for g_id in ctx.groups_of_class(cls.id):
                    for t in ctx.group(g_id).teachers:
                        by_teacher.setdefault(t.id, []).append(g_id)
                for tid, gids in by_teacher.items():
                    if len(gids) < 2:
                        continue
                    for day in ctx.active_days():
                        slots = ctx.active_slots(day)
                        if len(slots) < 5:
                            continue
                        ctx.model.Add(
                            sum(ctx.assigned[g][(day, s)] for g in gids for s in slots) <= 4
                        )

        for teacher in ctx.teachers:
            group_ids = ctx.groups_of_teacher(teacher.id)
            if len(group_ids) == 0:
                continue
            week_gaps: list[cp_model.IntVar] = []
            late_days: list[cp_model.IntVar] = []
            for day in ctx.active_days():
                slots = ctx.active_slots(day)
                if len(slots) < 3:
                    continue
                busy: dict[int, cp_model.IntVar] = {}
                for s in slots:
                    b = ctx.model.NewBoolVar(f"tbusy_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(
                        b, [ctx.assigned[g][(day, s)] for g in group_ids]
                    )
                    busy[s] = b
                # « Pas toujours les mêmes qui finissent tard » (12/08) :
                # jours en P8+ pénalisés au-delà de 2/semaine.
                _lates = [busy[s] for s in slots if s >= 7]
                if _lates:
                    lv = ctx.model.NewBoolVar(f"tlate_t{teacher.id}_d{day}")
                    ctx.model.AddMaxEquality(lv, _lates)
                    late_days.append(lv)
                before: dict[int, cp_model.IntVar] = {}
                after: dict[int, cp_model.IntVar] = {}
                prev = None
                for s in slots:
                    v = ctx.model.NewBoolVar(f"tbef_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if prev is None else [busy[s], prev])
                    before[s] = v
                    prev = v
                nxt = None
                for s in reversed(slots):
                    v = ctx.model.NewBoolVar(f"taft_t{teacher.id}_d{day}_s{s}")
                    ctx.model.AddMaxEquality(v, [busy[s]] if nxt is None else [busy[s], nxt])
                    after[s] = v
                    nxt = v
                day_gaps: list[cp_model.IntVar] = []
                for idx in range(1, len(slots) - 1):
                    s = slots[idx]
                    gap = ctx.model.NewBoolVar(f"tgap_t{teacher.id}_d{day}_s{s}")
                    ctx.model.Add(
                        gap >= before[slots[idx - 1]] + after[slots[idx + 1]] - busy[s] - 1
                    )
                    ctx.soft_penalty_terms.append((gap, WEIGHT_TEACHER_GAP))
                    week_gaps.append(gap)
                    day_gaps.append(gap)

                # Ce qui compte n'est pas le NOMBRE de trous mais leur LONGUEUR
                # (Yossef 11/08) : « selon אופק חדש et עוז לתמורה il faudrait
                # remplir de P1 jusqu'au dernier cours avec des heures de שהייה
                # et פרטני — mais ce n'est pas sympa pour un prof de venir une
                # heure et attendre 3h ou plus, aucun prof ». Un trou isolé est
                # donc du temps de présence normal et rémunéré ; une attente de
                # 3h d'affilée ne l'est pas.
                for i in range(len(day_gaps) - 2):
                    run = day_gaps[i:i + 3]
                    if _hard("tgap3"):
                        ctx.model.Add(sum(run) <= 2)
                    else:
                        long_gap = ctx.model.NewBoolVar(
                            f"tlonggap_t{teacher.id}_d{day}_i{i}")
                        ctx.model.Add(sum(run) - 2 <= long_gap)
                        ctx.soft_penalty_terms.append(
                            (long_gap, WEIGHT_TEACHER_LONG_GAP))

            if len(late_days) > 2:
                lover = ctx.model.NewIntVar(0, 5, f"tlateover_t{teacher.id}")
                ctx.model.Add(lover >= sum(late_days) - 2)
                ctx.soft_penalty_terms.append((lover, 35))

    # ---- Warm start ----
    def _warm_start_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "warm_start" / f"school_{self.school_id}.json"

    def save_warm_start(self, ctx: SolverContext, solver: cp_model.CpSolver) -> None:
        """Mémorise la solution, indexée par LIBELLÉ de groupe.

        Pas par identifiant : réimporter l'école régénère les groupes avec de
        nouveaux ids, alors que le libellé (« מתמטיקה ז-1+ז-3+ז-4 ») survit.
        """
        placement: dict[str, list[list[int]]] = {}
        for g_id, var_map in ctx.assigned.items():
            label = ctx.group(g_id).label
            for (day, slot), var in var_map.items():
                if solver.Value(var):
                    placement.setdefault(label, []).append([day, slot])
        p = self._warm_start_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(placement, ensure_ascii=False), encoding="utf-8")

    def _add_warm_start_hints(self, ctx: SolverContext) -> None:
        """Point de départ = la dernière solution connue.

        CP-SAT ne repart pas de zéro : il commence par cette solution et la
        répare là où elle viole les nouvelles règles (c'est de la Large
        Neighborhood Search). Reconstruire un modèle neuf à chaque fois sans
        indice, c'est refaire tout le chemin déjà parcouru.

        Deux sources, dans l'ordre : le planning en base s'il existe, sinon le
        fichier mémorisé — indispensable ici, parce que le cycle
        « suppression de l'école puis réimport » efface les plannings ET
        renumérote les groupes.
        """
        by_label: dict[str, list[tuple[int, int]]] = {}
        prev = (
            self.db.query(Schedule)
            .filter(Schedule.school_id == self.school_id)
            .order_by(Schedule.id.desc())
            .first()
        )
        if prev is not None:
            for e in self.db.query(ScheduleEntry).filter_by(schedule_id=prev.id).all():
                g = self.db.get(Group, e.group_id)
                if g is not None:
                    by_label.setdefault(g.label, []).append((e.day_of_week, e.slot_index))
        else:
            p = self._warm_start_path()
            if p.exists():
                try:
                    saved = json.loads(p.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    saved = {}
                for label, positions in saved.items():
                    by_label[label] = [(d, s) for d, s in positions]
        if not by_label:
            return
        # Deux groupes peuvent porter le même libellé (barrettes, réunions) :
        # sans déduplication on indique deux fois la même variable et CP-SAT
        # rejette le modèle — « The solution hint contains duplicate variables ».
        hinted: set[int] = set()
        for g_id, var_map in ctx.assigned.items():
            for pos in set(by_label.get(ctx.group(g_id).label, ())):
                var = var_map.get(pos)
                if var is not None and var.Index() not in hinted:
                    ctx.model.AddHint(var, 1)
                    hinted.add(var.Index())
        if hinted:
            logger.info("Warm start : %d placements repris comme point de départ", hinted)

    # ---- Application des contraintes ----
    def _apply_constraints(
        self,
        ctx: SolverContext,
        disabled: set[int],
        use_assumptions: bool = True,
    ) -> list[_AppliedConstraint]:
        applied: list[_AppliedConstraint] = []

        def register(inst: BaseConstraint, entry: _AppliedConstraint) -> None:
            """Assumption (phase MUS) ou littéral forcé vrai (phase rapide)."""
            lit = inst.assumption_literal
            if lit is None:
                return
            if use_assumptions:
                ctx.model.AddAssumption(lit)
                self._literal_index_to_applied[lit.Index()] = entry
            else:
                ctx.model.Add(lit == 1)

        # 1. Structurelles (toujours actives, jamais relaxables)
        for cls in STRUCTURAL_CONSTRAINTS:
            inst = cls()
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=None))

        # 2. Système implicite : volume horaire de chaque Group
        for g in ctx.groups:
            inst = GroupHoursPerWeekConstraint(
                group_id=g.id, hours=g.hours_per_week,
                origin_description=f"Volume défini sur le Group « {g.label} »",
            )
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=None))
            register(inst, applied[-1])

        # 3. Préflight : qualification prof
        qualif = TeacherQualifiedForSubjectConstraint()
        qualif.apply(ctx)
        applied.append(_AppliedConstraint(instance=qualif, db_id=None))
        register(qualif, applied[-1])

        # 4. Contraintes DB actives
        db_constraints = (
            self.db.query(DBConstraint)
            .filter(DBConstraint.school_id == self.school_id, DBConstraint.is_active.is_(True))
            .all()
        )
        for dbc in db_constraints:
            if dbc.id in disabled:
                continue
            try:
                inst = constraint_from_db(dbc)
            except ValueError:
                # Type non implémenté (ex: préférence v2) → on ignore
                continue
            inst.apply(ctx)
            applied.append(_AppliedConstraint(instance=inst, db_id=dbc.id))
            register(inst, applied[-1])

        return applied

    # ---- INFEASIBLE → MUS ----
    def _build_conflict(
        self,
        ctx: SolverContext,
        solver: cp_model.CpSolver,
        applied: list[_AppliedConstraint],
        elapsed: float,
    ) -> SolveConflict:
        mus_indices = solver.SufficientAssumptionsForInfeasibility() or []
        conflicts: list[ConflictItem] = []
        seen: set[int] = set()

        for idx in mus_indices:
            ac = self._literal_index_to_applied.get(idx)
            if ac is None or id(ac) in seen:
                continue
            seen.add(id(ac))
            conflicts.append(ConflictItem(
                constraint_id=ac.db_id,
                constraint_type=ac.instance.constraint_type,
                explanation=ac.instance.explain(ctx),
            ))

        return SolveConflict(conflicts=conflicts, solver_time_seconds=elapsed)

    # ---- FEASIBLE → écrire ScheduleEntry ----
    def _save_solution(
        self,
        ctx: SolverContext,
        solver: cp_model.CpSolver,
        schedule_name: str,
        disabled: list[int],
        elapsed: float,
        strict: bool = False,
    ) -> SolveSuccess:
        quality: dict = {"solver_time_seconds": elapsed, "strict_quality": strict}
        # Mémorise la solution : la prochaine génération repartira de là
        # au lieu de refaire tout le chemin.
        try:
            self.save_warm_start(ctx, solver)
        except OSError as exc:
            logger.warning("Warm start non sauvegardé : %s", exc)
        if ctx.soft_penalty_terms:
            # Somme pondérée des pénalités (0 = planning parfait côté SOFT)
            quality["soft_penalty"] = int(solver.ObjectiveValue())
        sched = Schedule(
            school_id=self.school_id,
            name=schedule_name,
            status=ScheduleStatus.DRAFT,
            generated_at=datetime.now(timezone.utc),
            relaxed_constraints_report={"disabled_constraint_ids": disabled},
            quality_score=quality,
        )
        self.db.add(sched)
        self.db.flush()

        count = 0
        for g_id, slot_map in ctx.assigned.items():
            for (d, s), var in slot_map.items():
                if solver.Value(var) != 1:
                    continue
                # Salle assignée (s'il y a des salles candidates)
                room_id = None
                if g_id in ctx.room_used:
                    for r_id, rvar in ctx.room_used[g_id][(d, s)].items():
                        if solver.Value(rvar) == 1:
                            room_id = r_id
                            break
                entry = ScheduleEntry(
                    schedule_id=sched.id, group_id=g_id, room_id=room_id,
                    day_of_week=d, slot_index=s,
                )
                self.db.add(entry)
                count += 1

        self.db.commit()
        self.db.refresh(sched)
        return SolveSuccess(
            schedule_id=sched.id,
            placed_entries=count,
            relaxed_constraint_ids=disabled,
            solver_time_seconds=elapsed,
        )
