"""Import du dataset consolidé תשפ"ז dans l'application.

Crée l'école 'amit-tashpaz' avec :
- Grille א'-ה' × 11 périodes (P1-P11 → slot 0-10)
- Classes / matières / profs / groupes / cohortes du dataset final
- Contraintes :
  * dispos שחף (block_slot_teacher, 1 par prof×jour)
  * overrides Yossef / טוולייה / אליקים (remplacent leurs dispos שחף)
  * teacher_free_day pour chaque prof réel
  * extra_hours_at_day_edge pour chaque cohorte à volumes inégaux

Usage : DATABASE_URL='sqlite:///./demo.db' python scripts/import_tashpaz.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")
os.environ.setdefault("SECRET_KEY", "this-is-a-test-secret-key-32chars-yes")

from sqlalchemy.orm import sessionmaker

from app.db.base import engine, Base
import app.models  # noqa: F401
from app.models import (
    Class, Constraint, ConstraintOriginRole, ConstraintPriority, ConstraintType,
    Grade, Group, GroupType, GroupingPolicy, ParallelCohort, School, Subject,
    Teacher, TimeSlot,
)

DATA = Path(r"D:\emploi-du-temp-projet\donnees-tashpaz\dataset_tashpaz_final.json")

# 10 périodes de cours par jour (P1-P10), comme dans l'emploi du temps תשפ"ו.
# La prière (תפילה) se tient en « période 0 », avant P1, et n'est pas modélisée.
N_PERIODS = 10
# Semaine dim→jeu, plus un vendredi de 4 périodes réservé aux מגמות de יא.
N_DAYS = 6
FRIDAY_PERIODS = 4
FRIDAY = 5

# Overrides de disponibilité (remplacent les dispos שחף de ces profs)
# day: 0=א' … 4=ה' ; slots 0-10 = P1-P11
OVERRIDES = {
    "כהן זרדי יוסף אליהו": [   # dispo א'≤P5, ב'≤P6, ה'≤P4 (כפר הרואה + trajet)
        {"day": 0, "slots": list(range(5, N_PERIODS))},
        {"day": 1, "slots": list(range(6, N_PERIODS))},
        {"day": 4, "slots": list(range(4, N_PERIODS))},
    ],
    "טוולייה דבורה הוגט": [    # autre école : ב' dispo dès P6, ג' dispo jusqu'à P5
        {"day": 1, "slots": list(range(0, 5))},
        {"day": 2, "slots": list(range(5, N_PERIODS))},
    ],
    "בן שלמה אליקים": [        # option A : א'+ד' complets, ב' dès P5, jamais ג'/ה'
        {"day": 1, "slots": list(range(0, 4))},
        {"day": 2, "slots": list(range(0, N_PERIODS))},
        {"day": 4, "slots": list(range(0, N_PERIODS))},
    ],
    "ממן חנן": [               # ne vient que dimanche et mercredi (Yossef 07/08)
        {"day": 1, "slots": list(range(0, N_PERIODS))},
        {"day": 2, "slots": list(range(0, N_PERIODS))},
        {"day": 4, "slots": list(range(0, N_PERIODS))},
    ],
    "קנימח ניר": [             # autre école (Yossef 11/08)
        {"day": 0, "slots": [6, 7, 8]},        # dimanche P7-P9
        {"day": 1, "slots": [0, 1, 2]},        # lundi P1-P3
        {"day": 4, "slots": [5, 6]},           # jeudi P6-P7
    ],
    "בוקריס יצחק": [           # message du 11/08 : mardi dès le matin (3-4h),
        # lundi jamais, dimanche et jeudi seulement à partir de P7.
        {"day": 0, "slots": list(range(0, 6))},          # dimanche avant P7
        {"day": 1, "slots": list(range(0, N_PERIODS))},  # lundi entier
        {"day": 3, "slots": list(range(0, N_PERIODS))},  # mercredi entier (11/08)
        {"day": 4, "slots": list(range(0, 6))},          # jeudi avant P7
    ],
    "רחום שני": [              # Yossef 12/08 : « dimanche toute la journée,
        # lundi toute la journée, mardi que les premières heures ». Elle
        # commence un doctorat et passe à 50 %.
        {"day": 2, "slots": list(range(4, N_PERIODS))},   # mardi après P4
        {"day": 3, "slots": list(range(0, N_PERIODS))},   # mercredi
        {"day": 4, "slots": list(range(0, N_PERIODS))},   # jeudi
    ],
    "חדד מוראל": [             # jour de congé déplacé du dimanche au MARDI
        # (Yossef 12/08). Son questionnaire demandait dimanche en 1er choix,
        # mardi en 3e. Le dimanche fermait הבעה pour les trois שכבות ; le
        # mardi est déjà pris par les maths, donc l'y déplacer ne coûte rien
        # et rend le dimanche à הבעה.
        {"day": 2, "slots": list(range(0, N_PERIODS))},
    ],
    "יפרח אורי": [             # indispos transmises par Yossef (11/08)
        {"day": 0, "slots": [5, 6, 7]},        # dimanche P6-P8
        {"day": 1, "slots": [0, 1, 2]},        # lundi P1-P3
        {"day": 4, "slots": [4, 5]},           # jeudi P5-P6
    ],
    "בגו יהונתן": [            # ne travaille QUE le mercredi — CONFIRMÉ (10/08)
        {"day": 0, "slots": list(range(0, N_PERIODS))},
        {"day": 1, "slots": list(range(0, N_PERIODS))},
        {"day": 2, "slots": list(range(0, N_PERIODS))},
        {"day": 4, "slots": list(range(0, N_PERIODS))},
    ],
}

# Profs qui renoncent explicitement à leur jour de congé (Yossef 07/08 :
# « moi je ne veux pas de jour de congé »). Ses créneaux sont déjà très
# réduits par כפר הרואה : lui imposer un jour de congé en plus ne laisserait
# pas la place à son service.
NO_FREE_DAY = {"כהן זרדי יוסף אליהו"}

# Indisponibilités traitées comme un SOUHAIT et non comme un mur (Yossef 11/08 :
# « ne prends pas en compte les contraintes de ניר mais essaie de ne pas trop le
# pénaliser »). קנימח est dans les trois barrettes de maths du lycée ; croisées
# avec celles de בוקריס, ses indispos ne laissaient que 13 créneaux pour les 15
# heures de י + י"א. Chaque heure posée hors de ses disponibilités coûte
# SOFT_OVERRIDE_WEIGHT : le solveur n'en placera que le strict nécessaire.
SOFT_OVERRIDES = {"קנימח ניר"}
SOFT_OVERRIDE_WEIGHT = 150

# ---- Arbitrages MATHS du 12/08 -------------------------------------------
# « Pour les maths du lycée, ouvre le dimanche, ne prends pas en considération
#   les demandes des profs pour le dimanche. Le mercredi est journée de congé
#   pour les profs de maths. »
# Le dimanche était fermé aux barrettes de י et י"א par les indispos croisées
# de בוקריס (présent seulement à partir de P7) et de קנימח (bloqué P7-P9) :
# les deux ne se croisaient qu'une heure par semaine.
MATH_SUNDAY_OPEN = True
MATH_WEDNESDAY_OFF = True

# רחום שני ne garde que DEUX classes de חטיבה sur trois (Yossef 12/08,
# « à toi de choisir »). Retirée de la barrette de ט : c'était la plus
# étroite des trois (12 départs de bloc possibles contre 18 pour ז et ח),
# donc celle que son départ soulage le plus.
DROP_GROUPS = [
    {"teacher": "רחום שני", "subject": "מתמטיקה",
     "classes": ["ט-1", "ט-3", "ט-4", "ט-5"]},
]

# Souhaits personnels du שאלון (remarques libres) — préférences souples qui
# S'AJOUTENT aux dispos שחף, sans les remplacer. Chaque heure posée dans ces
# créneaux coûte `w` : le solveur les évite sauf nécessité.
SOFT_WISHES = {
    # « אני זקוקה ליום כלשהו במהלך השבוע (עדיף יום ראשון) לסיים בסוף
    #   השעה החמישית » — dimanche ≤ P5.
    "חורי שירלי": [{"day": 0, "slots": list(range(5, N_PERIODS)), "w": 60}],
    # « מבקש לסיים ביום ראשון עד 14:30 » (≈ P7) ; second choix mardi 13:30,
    # non codé — le premier suffit, l'autre jouerait contre les maths du mardi.
    "לוי יהונתן": [{"day": 0, "slots": list(range(7, N_PERIODS)), "w": 60}],
}

# Blocages hérités de תשפ"ו que Yossef a annulés : le jour de repos reste
# garanti mais le solveur choisit lequel. דיין דניאל (10/08) : « il lui faut
# un jour de repos — si tu veux donne-lui un autre jour ».
DROP_INHERITED_BLOCKS = {
    "דיין דניאל",
    # מימון נתנאל : jeudi hérité de תשפ"ו, jamais reconfirmé — il n'a pas
    # répondu au questionnaire. C'était, avec le dimanche de חדד, ce qui
    # rendait les blocs de 2h de הבעה mathématiquement impossibles : les
    # quatre profs communs aux trois barrettes fermaient dimanche ET jeudi.
    # Arbitrage Yossef 12/08. Son jour de congé reste garanti, le solveur
    # choisit lequel.
    "מימון נתנאל",
    # « רעות a un seul jour de congé » (Yossef 10/08). תשפ"ו lui en bloquait
    # deux (dimanche + jeudi) ; son questionnaire ne demande que le jeudi.
    # Son dimanche est rendu : elle enseigne l'anglais dans TROIS barrettes
    # (י, יא, יב) et ses deux jours bloqués tombaient sur les seuls créneaux
    # encore libres autour des מגמות.
    "יצחקי רעות",
}

# Classes חינוך מיוחד : journée qui s'arrête à P5 (« et pas plus », Yossef).
SHORT_DAY_CLASSES = ["ח-2"]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    Base.metadata.create_all(engine)   # au cas où (nouveaux enums OK, pas de CHECK)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()

    if db.query(School).filter_by(code="amit-tashpaz").first():
        print("École amit-tashpaz déjà importée — supprime-la d'abord si tu veux réimporter.")
        return

    school = School(code="amit-tashpaz", name='אמי"ת בר אילן נתניה תשפ"ז',
                     default_language="he")
    db.add(school)
    db.flush()

    # Grille : 5 jours × 10 périodes de cours (P1-P10).
    # תפילה occupe la « période 0 » avant P1 et reste hors modèle : c'est la
    # structure réelle de תשפ"ו (emploi_du_temps_tashpau_long.csv), confirmée
    # par Yossef le 07/08.
    # Vendredi rouvert sur 4 périodes UNIQUEMENT pour la barrette de מגמות
    # de יא (Yossef 10/08 : « pour ma מגמה il y a la possibilité le vendredi
    # 4 heures »). Les 22 autres classes n'y ont aucun cours : elles sont
    # bloquées ce jour-là juste après.
    for d in range(N_DAYS):
        for s in range(FRIDAY_PERIODS if d == 5 else N_PERIODS):
            db.add(TimeSlot(
                school_id=school.id, day_of_week=d, slot_index=s,
                start_time=time(min(8 + s, 23), 0), end_time=time(min(8 + s, 23), 45),
                is_active=True, is_break=False, label=f"P{s+1}",
            ))

    # Grades
    GRADES = [("G7", "שכבה ז", 7), ("G8", "שכבה ח", 8), ("G9", "שכבה ט", 9),
              ("G10", "שכבה י", 10), ("G11", 'שכבה י"א', 11), ("G12", 'שכבה י"ב', 12)]
    grades = {}
    for code, name, order in GRADES:
        g = Grade(school_id=school.id, code=code, name=name, order=order,
                  grouping_policy=GroupingPolicy.GROUP_CENTRIC)
        db.add(g); db.flush()
        grades[code] = g

    def grade_of(cls_code: str):
        prefix = cls_code.split("-")[0].strip()
        return grades[{"ז": "G7", "ח": "G8", "ט": "G9",
                       "י": "G10", "יא": "G11", "יב": "G12"}.get(prefix, "G7")]

    # Classes
    classes = {}
    for c in data["classes"]:
        cls = Class(school_id=school.id, grade_id=grade_of(c).id,
                    code=c, name=c, student_count=25)
        db.add(cls); db.flush()
        classes[c] = cls

    # Matières
    subjects = {}
    for i, s in enumerate(data["subjects"]):
        subj = Subject(school_id=school.id, code=f"S{i+1:02d}",
                        name_fr=s, name_he=s, is_active=True)
        db.add(subj); db.flush()
        subjects[s] = subj

    # Profs réels
    teachers = {}
    for i, t in enumerate(data["teachers"]):
        obj = Teacher(school_id=school.id, code=f"T{i+1:02d}",
                       first_name=t["name"], last_name="",
                       languages=["he"], is_active=True)
        db.add(obj); db.flush()
        teachers[t["name"]] = obj

    # Placeholders (postes à pourvoir)
    for i, name in enumerate(data["placeholders"]):
        obj = Teacher(school_id=school.id, code=f"X{i+1:02d}",
                       first_name=name, last_name="",
                       languages=["he"], is_active=True)
        db.add(obj); db.flush()
        teachers[name] = obj

    # Cohortes
    cohort_objs = []
    for c in data["cohorts"]:
        first_cls = c["classes"][0] if c["classes"] else None
        pc = ParallelCohort(
            school_id=school.id,
            grade_id=grade_of(first_cls).id if first_cls else None,
            label=c["label"][:190],
        )
        db.add(pc); db.flush()
        cohort_objs.append(pc)

    # Groupes — en retirant ceux que Yossef a explicitement supprimés
    def _dropped(g):
        for d in DROP_GROUPS:
            if (g["teacher"] == d["teacher"] and g["subject"] == d["subject"]
                    and sorted(g["classes"]) == sorted(d["classes"])):
                return True
        return False

    n_dropped = sum(1 for g in data["groups"] if _dropped(g))
    data["groups"] = [g for g in data["groups"] if not _dropped(g)]
    if n_dropped:
        print(f"   {n_dropped} groupe(s) retiré(s) sur décision de Yossef "
              f"(רחום שני : 2 classes de חטיבה au lieu de 3)")

    n_groups = 0
    for g in data["groups"]:
        grp = Group(
            school_id=school.id,
            grade_id=grade_of(g["classes"][0]).id if g["classes"] else grades["G7"].id,
            subject_id=subjects[g["subject"]].id,
            label=f"{g['subject']} {'+'.join(g['classes'])}"[:190],
            hours_per_week=max(1, g["hours"]),
            group_type=GroupType.LEVEL_GROUP if g["cohort"] is not None else GroupType.WHOLE_CLASS,
            can_split=bool(g.get("can_split")),
            parallel_cohort_id=cohort_objs[g["cohort"]].id if g["cohort"] is not None else None,
        )
        grp.teachers.append(teachers[g["teacher"]])
        for c in g["classes"]:
            grp.source_classes.append(classes[c])
        db.add(grp)
        n_groups += 1
    db.flush()

    # ---- Contraintes ----
    n_constraints = 0

    def add_constraint(ctype, params, desc, role=ConstraintOriginRole.SCHOOL_ADMIN,
                       priority=ConstraintPriority.HARD, weight=None):
        nonlocal n_constraints
        db.add(Constraint(
            school_id=school.id, constraint_type=ctype,
            priority=priority, weight=weight, parameters=params,
            is_active=True, origin_role=role, origin_description=desc,
        ))
        n_constraints += 1

    math_teachers = {g["teacher"] for g in data["groups"]
                     if g["subject"] == "מתמטיקה" and g["teacher"]}

    # 1. Dispos שחף (sauf profs overridés)
    #
    # JOURS DE CONGÉ FLEXIBLES (Yossef 12/08 : « peut-être faut adapter les
    # jours de congé ? »). תשפ"ו concentrait 29 des 37 jours de congé sur le
    # mardi (13) et le mercredi (16) : ces deux journées se vidaient de leurs
    # profs et tout se reportait sur dimanche et jeudi. Or 19 de ces profs
    # n'ont jamais répondu au questionnaire — leur jour était reconduit par
    # défaut — et 3 en demandaient un autre.
    # On ne garde donc en dur que les indisponibilités PARTIELLES (vraies
    # contraintes horaires) ; les journées entières héritées deviennent
    # flexibles : le droit au jour de congé reste garanti par TEACHER_FREE_DAY
    # et le vœu du questionnaire pèse en préférence.
    FLEX_FREE_DAYS = os.environ.get("FIXED_FREE_DAYS", "") != "1"
    FULL_DAY_THRESHOLD = 8
    n_freed = 0
    for t in data["teachers"]:
        name = t["name"]
        if name in OVERRIDES or name in DROP_INHERITED_BLOCKS or not t["blocked"]:
            continue
        by_day = defaultdict(list)
        for b in t["blocked"]:
            by_day[b["day"]].append(b["slot"])
        for d, slots in by_day.items():
            if MATH_SUNDAY_OPEN and d == 0 and name in math_teachers:
                continue        # dimanche rouvert aux profs de maths
            if FLEX_FREE_DAYS and len(set(slots)) >= FULL_DAY_THRESHOLD:
                n_freed += 1
                continue        # jour de congé hérité → rendu au solveur
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [d], "slot_indices": sorted(set(slots)),
                 "target_id": teachers[name].id},
                f"אילוצי שחף — {name}", ConstraintOriginRole.TEACHER,
            )
    if n_freed:
        print(f"   {n_freed} jours de congé hérités rendus flexibles "
              f"(droit au congé garanti, jour choisi par le solveur)")

    # 1-bis. Arbitrages MATHS (Yossef 12/08)
    if MATH_WEDNESDAY_OFF:
        n_wed = 0
        for name in sorted(math_teachers):
            if name not in teachers:
                continue
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [3], "slot_indices": list(range(N_PERIODS)),
                 "target_id": teachers[name].id},
                f"יום רביעי — יום חופש למורי המתמטיקה — {name}",
                ConstraintOriginRole.SCHOOL_ADMIN,
            )
            n_wed += 1
        print(f"   {n_wed} profs de maths : mercredi = jour de congé")

    # 2. Overrides (Yossef / טוולייה / אליקים)
    for name, blocks in OVERRIDES.items():
        if name not in teachers:
            print(f"  ⚠ Override : prof introuvable {name}")
            continue
        soft = name in SOFT_OVERRIDES
        for b in blocks:
            # « Pour les maths du lycée, ouvre le dimanche — ne prends pas en
            # considération les demandes des profs pour le dimanche » (12/08).
            # C'est le croisement בוקריס × קנימח qui ne laissait qu'UNE heure
            # commune le dimanche aux barrettes de י et י"א.
            if MATH_SUNDAY_OPEN and b["day"] == 0 and name in math_teachers:
                continue
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [b["day"]], "slot_indices": b["slots"],
                 "target_id": teachers[name].id},
                (f"בקשת זמינות (רצוי) — {name}" if soft
                 else f"עבודה בבי\"ס אחר / כולל — {name}"),
                ConstraintOriginRole.TEACHER,
                priority=ConstraintPriority.SOFT if soft else ConstraintPriority.HARD,
                weight=SOFT_OVERRIDE_WEIGHT if soft else None,
            )

    # 2-bis. Souhaits personnels du שאלון (souples, en plus des dispos שחף)
    for name, wishes in SOFT_WISHES.items():
        if name not in teachers:
            print(f"  ⚠ Souhait : prof introuvable {name}")
            continue
        for wsh in wishes:
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [wsh["day"]], "slot_indices": wsh["slots"],
                 "target_id": teachers[name].id},
                f"בקשה אישית מהשאלון — {name}",
                ConstraintOriginRole.TEACHER,
                priority=ConstraintPriority.SOFT, weight=wsh["w"],
            )

    # 3. Jours travaillés : barème officiel liant le volume frontal au nombre
    #    de jours autorisés (עוז לתמורה au lycée, אופק חדש au collège).
    #      ≤12h → 2 jours max · 13-17h → 3 · 18-21h → 4 · ≥22h → 5
    #    S'y ajoute la règle « on ne fait pas venir un prof pour une heure » :
    #    tout jour travaillé compte au moins 2 heures.
    #    Le barème porte sur la PRÉSENCE TOTALE, pas sur les seules heures de
    #    cours : אלמו רפאל (chef du collège) n'a que 8h frontales mais 37h de
    #    responsabilités — il est à l'école les 5 jours et peut justement
    #    servir à boucher les trous (Yossef 07/08).
    hours_of = defaultdict(int)
    for g in data["groups"]:
        hours_of[g["teacher"]] += max(1, g["hours"])

    def max_days(h: int) -> int:
        if h <= 12:
            return 2
        if h <= 17:
            return 3
        if h <= 21:
            return 4
        return 5

    n_resp = 0
    for t in data["teachers"]:
        frontal = hours_of[t["name"]]
        resp = t.get("responsibility_hours", 0)
        presence = frontal + resp
        if resp >= 8 and max_days(presence) > max_days(frontal):
            n_resp += 1
        # Au moins un jour de congé pour tout le monde (règle Yossef 06/08),
        # et davantage pour les petits services.
        free = max(1, 5 - max_days(presence))
        if t["name"] in NO_FREE_DAY:
            free = 0
        add_constraint(
            ConstraintType.TEACHER_FREE_DAY,
            {"teacher_id": teachers[t["name"]].id, "min_free_days": free,
             "min_hours_per_day": 2},
            f"ימי עבודה — {t['name']} ({frontal}ש' פרונטלי + {resp}ש' תפקיד, "
            f"עד {5 - free} ימים)",
        )
    print(f"   {n_resp} profs à responsabilités gardent plus de jours "
          f"grâce à leurs heures de תפקיד")

    # « לא משובץ ont aussi un jour de congé » (Yossef 10/08) : le futur
    # titulaire du poste aura les mêmes droits, autant le prévoir maintenant.
    ph_hours = defaultdict(int)
    for g in data["groups"]:
        if g["placeholder"]:
            ph_hours[g["teacher"]] += max(1, g["hours"])
    for name, h in ph_hours.items():
        add_constraint(
            ConstraintType.TEACHER_FREE_DAY,
            {"teacher_id": teachers[name].id,
             "min_free_days": max(1, 5 - max_days(h)), "min_hours_per_day": 3},
            f"ימי עבודה — {name} ({h}ש')",
        )
    print(f"   {len(ph_hours)} postes à pourvoir ont aussi un jour de congé")

    # 3-bis. Jour de congé SOUHAITÉ (questionnaire תשפ"ז, 1er/2e/3e choix).
    # Préférence pondérée, jamais bloquante : 14 profs sur 31 demandent le
    # mardi, il est donc impossible de tous les satisfaire.
    n_pref = 0
    for t in data["teachers"]:
        days = t.get("preferred_free_days") or []
        if not days:
            continue
        db.add(Constraint(
            school_id=school.id,
            constraint_type=ConstraintType.TEACHER_PREFERRED_FREE_DAY,
            priority=ConstraintPriority.SOFT, weight=40,
            parameters={"teacher_id": teachers[t["name"]].id, "days": days},
            is_active=True, origin_role=ConstraintOriginRole.TEACHER,
            origin_description=f"יום חופשי מבוקש (שאלון תשפ\"ז) — {t['name']}",
        ))
        n_constraints += 1
        n_pref += 1
    print(f"   {n_pref} jours de congé souhaités repris du questionnaire תשפ\"ז")

    # 3a-bis. Classes חינוך מיוחד : « finir le plus tôt possible » — géré
    # comme une pénalité croissante dans le moteur (SHORT_DAY_CLASS_CODES),
    # pas comme un plafond dur : leurs volumes (26-31h) dépassent les 25h
    # que permettrait un vrai plafond P5.

    # 3a-bis-2. Plafonds propres aux classes חנ"מ (Yossef 10/08) :
    # « ז-2 ne peut pas finir plus que P6 » → P7-P10 fermés.
    # « ח-2 essaie d'accepter qu'une heure pour P7 » → P8-P10 fermés, P7 reste
    #   ouvert mais la pénalité de journée courte le rend coûteux.
    # ז-2 : P7 reste ouvert mais coûteux (pénalité journée courte) → une seule
    # journée par semaine y va. En le fermant, sa semaine serait figée au
    # créneau près : 30h pour 30 créneaux (arbitrage Yossef 10/08).
    for code, last_open in (("ז-2", 6), ("ח-2", 6)):
        if code in classes:
            add_constraint(
                ConstraintType.BLOCK_SLOT_CLASS,
                {"days": list(range(5)),
                 "slot_indices": list(range(last_open + 1, N_PERIODS)),
                 "target_id": classes[code].id},
                f"{code} — מסיימת ב-P{last_open + 1}",
            )

    # 3a-ter. Lundi : le COLLÈGE (ז/ח/ט) s'arrête à P6.
    #
    # ישיבת מנטורים occupe lundi P5-P6 et mobilise 21 profs, qui sont les
    # מחנכים des 13 classes. Les classes peuvent malgré tout tourner à ces
    # heures-là : l'emploi du temps de תשפ"ו le montre — 12 classes de חטיבה
    # avaient cours lundi P5 et P6, tenues par 17 profs dont 16 NON-mentors
    # (barrettes d'anglais en ז, de maths en ט, sport, של"ח). Le solveur doit
    # donc y placer des matières dont les profs ne sont pas mentors.
    # Filet de sécurité : le moteur autorise une fin de journée dès P5 ce
    # jour-là (« même faire finir une classe en P5 c'est ok », Yossef 07/08).
    # Le lycée n'est pas concerné : יא-2 est à 50h, un plafond le lundi lui
    # serait arithmétiquement impossible.
    # Fin réelle du lundi en תשפ"ו (« regarde ce qui a été fait l'année
    # dernière », Yossef 10/08) : ז et ח allaient jusqu'à P7, ט jusqu'à P9.
    # Le lundi n'était donc PAS un jour court — mon plafond à P6 était une
    # invention, et c'est lui qui étouffait le collège.
    MONDAY_LAST = {"ז": 7, "ח": 7, "ט": 9}
    n_monday = 0
    for code, cls in classes.items():
        g = code.split("-")[0]
        if g not in MONDAY_LAST:
            continue
        last = MONDAY_LAST[g]
        if last >= N_PERIODS:
            continue
        add_constraint(
            ConstraintType.BLOCK_SLOT_CLASS,
            {"days": [1], "slot_indices": list(range(last, N_PERIODS)),
             "target_id": cls.id},
            f"יום שני — {code} מסיימת ב-P{last} (כמו תשפ\"ו)",
        )
        n_monday += 1

    # 3a-quater. Fin de journée du collège : P8, comme Yossef le voulait dès le
    # départ. Ses fichiers du 10/08 ramènent les classes de חטיבה à 29-37h, ce
    # qui tient dans 6 + 4×8 = 38 créneaux — la règle redevient donc possible
    # (avant, ט-1/ט-3/ט-4 étaient à 41h et il fallait P9). Les classes qui
    # frôlent la capacité gardent P9 en soupape via le garde-fou ci-dessous.
    LATE_SLOTS = [8, 9]
    EXTRA_LATE = {"אמירים"}

    # Charge réelle de chaque classe (une barrette compte son enveloppe une
    # seule fois) : les classes trop chargées ne peuvent pas se priver de P10.
    env = defaultdict(int)
    for g in data["groups"]:
        if g["cohort"] is not None:
            env[g["cohort"]] = max(env[g["cohort"]], max(1, g["hours"]))
    load, seen = defaultdict(int), defaultdict(set)
    for g in data["groups"]:
        for c in g["classes"]:
            if g["cohort"] is not None:
                if g["cohort"] in seen[c]:
                    continue
                seen[c].add(g["cohort"]); load[c] += env[g["cohort"]]
            else:
                load[c] += max(1, g["hours"])
    # Capacité si P9-P10 sont fermés : lundi P1-P6 + 4 jours P1-P8.
    CAP_WITHOUT_LATE = 6 + 4 * 8
    overloaded = {c for c in classes
                  if c.split("-")[0] in ("ז", "ח", "ט")
                  and load[c] > CAP_WITHOUT_LATE - 2}
    if overloaded:
        print(f"   ⚠ {len(overloaded)} classes gardent l'accès à P9 faute de marge : "
              + ", ".join(f"{c} ({load[c]}h)" for c in sorted(overloaded)))

    hativa_ids = {cls.id for code, cls in classes.items()
                  if code.split("-")[0] in ("ז", "ח", "ט")}
    n_late = 0
    for g in data["groups"]:
        if g["subject"] in EXTRA_LATE:
            continue
        if not any(classes[c].id in hativa_ids for c in g["classes"]):
            continue
        # P9 rouvert pour la seule שכבה ט (arbitrage Yossef 10/08) : ses quatre
        # classes ont 37h pour 38 créneaux si P9 est fermé — une heure de marge
        # ne suffit pas. Les autres niveaux s'arrêtent bien à P8.
        needs_p9 = any(c.split("-")[0] == "ט" for c in g["classes"])
        slots = [9] if needs_p9 else LATE_SLOTS
        grp_obj = next((x for x in db.query(Group).filter_by(school_id=school.id)
                        if x.label == f"{g['subject']} {'+'.join(g['classes'])}"[:190]), None)
        if grp_obj is None:
            continue
        add_constraint(
            ConstraintType.BLOCK_SLOT_GROUP,
            {"days": list(range(5)), "slot_indices": slots,
             "target_id": grp_obj.id},
            f"חטיבה מסיימת ב-P8 — {grp_obj.label[:70]}",
        )
        n_late += 1
    print(f"   {n_late} groupes de חטיבה bloqués après P8 "
          f"(P9-P10 réservés à {', '.join(EXTRA_LATE)})")

    # 3b. Ouverture de journée : מחנכים ומנטורים en tout début de matinée.
    # מנטורים = exigence ferme (Yossef) ; les autres = préférence forte —
    # en dur elles étaient infaisables (שיח בוקר : 42h pour 10 classes ne
    # tient pas dans P1-P2).
    add_constraint_soft = lambda subj, lo, hi, w, desc: db.add(Constraint(
        school_id=school.id,
        constraint_type=ConstraintType.SUBJECT_PREFERRED_SLOT_RANGE,
        priority=ConstraintPriority.SOFT, weight=w,
        parameters={"subject_id": subjects[subj].id, "min_slot": lo, "max_slot": hi},
        is_active=True, origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
        origin_description=desc,
    ))

    if "מנטורים" in subjects:
        add_constraint(
            ConstraintType.SUBJECT_REQUIRED_SLOT_RANGE,
            {"subject_id": subjects["מנטורים"].id, "min_slot": 0, "max_slot": 2},
            "מנטורים בשלוש השעות הראשונות בלבד",
        )

    # Les matières de fond ne se donnent pas en fin de journée (Yossef 09/08 :
    # « tout ce qui est תנ"ך תלמוד שפה אזרחות ne peut pas après P8 », et les
    # maths « c'est plus le matin ou début après-midi »). Règle DURE, à prendre
    # comme principe général et non comme correction d'un cas isolé.
    CORE_LAST_SLOT = 7            # index de P8
    # Élargi le 10/08 : « י היסטוריה en P9-P10 pas possible, trop tard » et
    # « יא impossible les heures d'anglais en P9 et P10, de même pour ספרות
    # et היסטוריה ». Toutes les matières académiques s'arrêtent donc à P8.
    for subj_name in ("תנ\"ך", "תלמוד", "הבעה", "לשון", "אזרחות",
                      "הלכה", "מחשבת ישראל",
                      "היסטוריה", "אנגלית", "ספרות"):
        if subj_name in subjects:
            add_constraint(
                ConstraintType.SUBJECT_REQUIRED_SLOT_RANGE,
                {"subject_id": subjects[subj_name].id,
                 "min_slot": 0, "max_slot": CORE_LAST_SLOT},
                f"{subj_name} — לא אחרי P{CORE_LAST_SLOT + 1}",
            )

    # מתמטיקה : exception demandée par Yossef le 11/08 — « les maths peuvent
    # finir à P10, mais seulement les heures extra ». Le socle commun de chaque
    # barrette reste donc borné à P8 ; seules les heures de תגבור, celles que
    # les groupes renforcés ont EN PLUS du socle, peuvent descendre en P9-P10.
    # Sans cette exception les barrettes de י et י"א tombaient à 11 créneaux
    # utilisables pour 15 heures : c'est elle qui rendait le modèle impossible.
    cohort_min = defaultdict(lambda: 99)
    for g in data["groups"]:
        if g["cohort"] is not None:
            cohort_min[g["cohort"]] = min(cohort_min[g["cohort"]], g["hours"])
    n_math_base = 0
    for g in data["groups"]:
        if g["subject"] != "מתמטיקה":
            continue
        # heure extra = groupe qui dépasse le socle commun de sa barrette
        if g["cohort"] is not None and g["hours"] > cohort_min[g["cohort"]]:
            continue
        label = f"{g['subject']} {'+'.join(g['classes'])}"[:190]
        grp_obj = db.query(Group).filter_by(school_id=school.id, label=label).first()
        if grp_obj is None:
            continue
        add_constraint(
            ConstraintType.BLOCK_SLOT_GROUP,
            {"days": list(range(5)),
             "slot_indices": list(range(CORE_LAST_SLOT + 1, N_PERIODS)),
             "target_id": grp_obj.id},
            f"מתמטיקה (שעות הבסיס) — לא אחרי P{CORE_LAST_SLOT + 1}",
        )
        n_math_base += 1
    print(f"   מתמטיקה : {n_math_base} groupes de base bornés à P8, "
          f"les heures de תגבור peuvent aller jusqu'à P10")
    # Hors modèle désormais : תפילה (avant P1) et שיח בוקר (= מנטורים, qui
    # porte déjà la contrainte dure P1-P3).
    #
    # « Le top est de commencer par du kodesh, מחנכים, מנטור » (Yossef 07/08) :
    # les matières de קודש sont tirées vers l'ouverture de la journée, en
    # complément de מנטורים déjà imposé en P1-P3.
    # « Les מגמות en général c'est fin de journée » et « אמירים doit être fin
    # de journée » : elles sont tirées vers les dernières périodes.
    LAST = N_PERIODS - 1
    for subj_name, lo, hi, w in [
        ("חינוך", 0, 2, 40),
        ("תנ\"ך", 0, 2, 45),
        ("תלמוד", 0, 2, 55),
        ("הלכה", 0, 2, 30),
        ("מחשבת ישראל", 0, 3, 25),
        # « les maths c'est plus le matin ou début après-midi » (Yossef 09/08)
        ("מתמטיקה", 0, 4, 45),
        ("אנגלית", 1, 5, 25),
        # « ne pas commencer la journée par של"ח, היסטוריה, חנ"ג » — simple
        # préférence, jamais une interdiction (Yossef 10/08 : « seulement une
        # préférence »). Les interdire jusqu'à P4 resserrait trop le milieu
        # de journée, alors que P1-P3 sont déjà pris par les מנטורים.
        # « tu peux mettre des P1 mais le mieux est fin après-midi »
        # (Yossef 10/08) : aucune interdiction, mais la préférence vise
        # vraiment la fin de journée — P6 et au-delà.
        ("של\"ח", 5, LAST, 50),
        ("חנ\"ג", 5, LAST, 50),
        ("היסטוריה", 5, CORE_LAST_SLOT, 50),
        # « les מגמות peuvent commencer plus tôt, même la première heure —
        # juste ne pas mettre plein d'heures au début » (Yossef 10/08).
        # La fenêtre s'ouvre donc dès P3 : ce qui compte est qu'elles pèsent
        # sur la fin de journée, pas qu'elles soient interdites le matin.
        ("אמירים", 5, LAST, 55),
        ("מחשבים", 2, LAST, 45),
        ("אלקטרוניקה", 2, LAST, 45),
        ("פיזיקה", 2, LAST, 45),
        ("רובוטיקה", 2, LAST, 45),
        ("תעבורה", 2, LAST, 45),
        ("תקשוב", 2, LAST, 45),
    ]:
        if subj_name in subjects:
            where = "בפתיחת היום" if lo == 0 else "בסוף היום"
            add_constraint_soft(subj_name, lo, hi, w, f"{subj_name} — עדיף {where}")
            n_constraints += 1

    # ---- ישיבות ----
    # Une réunion est modélisée comme un « groupe sans élèves » : elle a des
    # profs mais aucune classe. La contrainte de non-chevauchement des profs
    # garantit alors que chacun est libre au moment choisi, et le solveur
    # cherche le créneau commun. Fenêtre : lundi à partir de P5 (Yossef 07/08),
    # sauf les deux réunions dont le jour est imposé autrement.
    #
    # ⚠ Seules les réunions dont je connais TOUS les participants sont créées.
    # Les autres attendent les noms manquants (voir reunions-qui-est-qui.md).
    # Composition et durée : lues dans le rikuz (`data["meetings"]`), pas
    # devinées — « regarde comment étaient les réunions l'année dernière, ce
    # sont les mêmes » (Yossef 07/08).
    #
    # ישיבת מנטורים : lundi P5-P6 (Yossef 07/08). Elle dure justement 2h dans
    # le rikuz, et cette fenêtre a été vérifiée faisable.
    #
    # Les QUATRE AUTRES sont libres sur toute la semaine : « trouve-leur une
    # place dans la semaine, pas obligé le lundi, mais adaptée à l'emploi du
    # temps des profs sans trou » (Yossef 07/08). Les entasser dans lundi
    # P7-P10 était infaisable — 6h de réunion pour 4 créneaux, avec אלמו רפאל
    # et יפרח הילה présents dans trois d'entre elles. Le solveur leur trouve
    # maintenant un créneau où tous les participants sont libres, et la
    # pénalité de trous prof les colle naturellement aux cours existants.
    MENTORS_SLOT = {"days": [1], "slots": [4, 5]}
    FREE_WEEK = {"days": list(range(5)), "slots": list(range(N_PERIODS))}
    DIM_OR_MAR = {"days": [0, 2], "slots": list(range(4, N_PERIODS))}

    MEETINGS = [(m["label"], m["participants"],
                 MENTORS_SLOT if m["label"] == "ישיבת מנטורים" else FREE_WEEK,
                 m["hours"])
                for m in data.get("meetings", [])]
    # חלוצים חינוכיים : absente du rikuz, donnée par אוריה — dimanche ou mardi.
    MEETINGS.append(("חלוצים חינוכיים",
                     ["דקל עידו יהודה", "רחום שני", "אל חדד דוד",
                      "אברהמי מאיר חיים"], DIM_OR_MAR, 1))

    meet_subj = Subject(school_id=school.id, code="S99", name_fr="ישיבות",
                        name_he="ישיבות", is_active=True, color_hex="#475569")
    db.add(meet_subj); db.flush()
    subjects["ישיבות"] = meet_subj

    n_meet = 0
    for label, participants, window, hours in MEETINGS:
        people = sorted({p for p in participants if p in teachers})
        missing = sorted({p for p in participants if p not in teachers})
        if missing:
            print(f"  ⚠ {label} : participants introuvables — {', '.join(missing)}")
        if len(people) < 2:
            print(f"  ⚠ {label} : ignorée (moins de 2 participants connus)")
            continue
        grp = Group(school_id=school.id, grade_id=grades["G7"].id,
                    subject_id=meet_subj.id, label=label[:190],
                    hours_per_week=hours, group_type=GroupType.WHOLE_CLASS)
        for p in people:
            grp.teachers.append(teachers[p])
        db.add(grp); db.flush()
        # Hors de la fenêtre autorisée : créneaux interdits pour ce groupe.
        forbidden = defaultdict(list)
        for d in range(5):
            for s in range(N_PERIODS):
                if d not in window["days"] or s not in window["slots"]:
                    forbidden[d].append(s)
        for d, slots in forbidden.items():
            add_constraint(
                ConstraintType.BLOCK_SLOT_GROUP,
                {"days": [d], "slot_indices": slots, "target_id": grp.id},
                f"חלון ישיבה — {label}",
            )
        n_meet += 1
        wh = ", ".join(f"{['א','ב','ג','ד','ה'][d]}" for d in window["days"])
        ws = "-".join(f"P{s+1}" for s in (window["slots"][0], window["slots"][-1])) \
            if len(window["slots"]) > 1 else f"P{window['slots'][0]+1}"
        print(f"  ✓ {label} : {len(people)} participants · {hours}h · יום {wh} {ws}")

    # « Il faudrait les faire finir à P6 au mieux » (Yossef 07/08) : préférence
    # et non obligation — en dur on retomberait sur la saturation qui bloquait
    # déjà le lundi après-midi. ישיבת מנטורים, à P5-P6, est dans la fenêtre.
    if n_meet:
        add_constraint_soft("ישיבות", 0, 5, 35, "ישיבות — עדיף עד P6")
        n_constraints += 1

    # 3a-quinquies. « Tous les dimanches doivent commencer par les מחנכים »
    # (Yossef 09/08). Au תיכון, le מחנך est le prof de גמרא de la classe :
    # son תלמוד est épinglé dimanche P1. חוזה שנהב בועז, directeur, ouvre
    # avec 2h (« rav חוזה doit commencer le dimanche matin par 2h תלמוד »).
    # HARD relaxable : si une classe ne peut pas l'honorer, le MUS la nomme.
    LYCEE = ("י", "יא", "יב")
    n_pin = 0
    for g in data["groups"]:
        if g["subject"] != "תלמוד" or len(g["classes"]) != 1:
            continue
        if g["classes"][0].split("-")[0] not in LYCEE:
            continue
        grp_obj = next((x for x in db.query(Group).filter_by(school_id=school.id)
                        if x.label == f"{g['subject']} {'+'.join(g['classes'])}"[:190]), None)
        if grp_obj is None:
            continue
        positions = [[0, 0]]
        if g["teacher"] == "חוזה שנהב בועז":
            positions.append([0, 1])
        add_constraint(
            ConstraintType.GROUP_PINNED_SLOT,
            {"group_id": grp_obj.id, "positions": positions},
            f"יום ראשון נפתח עם המחנך — {grp_obj.label[:70]}",
        )
        n_pin += 1
    print(f"   {n_pin} classes de תיכון ouvrent le dimanche avec leur מחנך (תלמוד P1)")

    # 3a-sexies. Vendredi : fermé à tout le monde sauf à la מגמת מחשבים de
    # Yossef (« que pour moi le vendredi », 11/08). C'est exactement ce que
    # faisait תשפ"ו : le seul cours du vendredi au lycée était מחשבים avec
    # כהן זרדי — י-1 et י-2 en P1-P3, יא-1/2/3 en P1-P2.
    #
    # ⚠ On parcourt les groupes EN BASE et non le dataset : les ישיבות
    # n'existent que côté base, et deux groupes peuvent partager le même
    # libellé (בגו et פטרוק co-enseignent אלקטרוניקה י) — la recherche par
    # libellé en laissait passer un, qui atterrissait le vendredi.
    yossef_id = teachers["כהן זרדי יוסף אליהו"].id
    n_fri = 0
    for grp_obj in db.query(Group).filter_by(school_id=school.id).all():
        allowed = (grp_obj.subject is not None
                   and (grp_obj.subject.name_he or "").strip() == "מחשבים"
                   and any(t.id == yossef_id for t in grp_obj.teachers))
        if allowed:
            continue
        add_constraint(
            ConstraintType.BLOCK_SLOT_GROUP,
            {"days": [FRIDAY], "slot_indices": list(range(FRIDAY_PERIODS)),
             "target_id": grp_obj.id},
            f"יום שישי סגור — {grp_obj.label[:70]}",
        )
        n_fri += 1
    print(f"   vendredi ouvert 4 périodes pour la seule מגמת מחשבים de כהן זרדי "
          f"({n_fri} groupes bloqués ce jour-là)")

    # 4. Surplus de barrette en fin de journée — UNIQUEMENT pour les liens
    # mono-matière (règle יחידות 3/5 : les heures de surplus des 5 יח' vont
    # en fin de journée). Les clusters מגמות multi-matières n'y sont pas soumis.
    group_hours_by_cohort = defaultdict(set)
    for g in data["groups"]:
        if g["cohort"] is not None:
            group_hours_by_cohort[g["cohort"]].add(max(1, g["hours"]))
    n_edge = 0
    # Priorité SOFT : c'est une préférence de placement, pas une obligation.
    # En dur elle exigeait le surplus dans les 3 dernières périodes de la
    # grille (P9-P11) alors que les classes finissent vers P8 → modèle
    # infaisable dès que plusieurs barrettes inégales coexistent.
    for ci, hours_set in group_hours_by_cohort.items():
        if len(hours_set) >= 2 and data["cohorts"][ci].get("same_subject"):
            db.add(Constraint(
                school_id=school.id,
                constraint_type=ConstraintType.EXTRA_HOURS_AT_DAY_EDGE,
                priority=ConstraintPriority.HARD, weight=130,
                parameters={"cohort_id": cohort_objs[ci].id,
                            "edge": "end", "edge_size": 3},
                is_active=True, origin_role=ConstraintOriginRole.SCHOOL_ADMIN,
                origin_description=f"שעות עודף בסוף היום — {cohort_objs[ci].label[:80]}",
            ))
            n_constraints += 1
            n_edge += 1

    db.commit()
    n_split = sum(1 for g in data["groups"] if g.get("can_split"))
    print(f"   {n_split} cours marqués « לפצל שעות » (2h pas forcément ensemble)")
    print(f"✅ Import terminé — school_id={school.id}")
    print(f"   {len(classes)} classes, {len(subjects)} matières, "
          f"{len(data['teachers'])} profs + {len(data['placeholders'])} placeholders")
    print(f"   {n_groups} groupes, {len(cohort_objs)} cohortes")
    print(f"   {n_constraints} contraintes (dont {n_edge} extra_hours_at_day_edge, "
          f"{n_monday} plafonds lundi pour la חטיבה)")


if __name__ == "__main__":
    main()
