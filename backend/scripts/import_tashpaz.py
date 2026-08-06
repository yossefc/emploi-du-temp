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

# Overrides de disponibilité (remplacent les dispos שחף de ces profs)
# day: 0=א' … 4=ה' ; slots 0-10 = P1-P11
OVERRIDES = {
    "כהן זרדי יוסף אליהו": [   # dispo א'≤P5, ב'≤P6, ה'≤P4 (כפר הרואה + trajet)
        {"day": 0, "slots": list(range(5, 11))},
        {"day": 1, "slots": list(range(6, 11))},
        {"day": 4, "slots": list(range(4, 11))},
    ],
    "טוולייה דבורה הוגט": [    # autre école : ב' dispo dès P6, ג' dispo jusqu'à P5
        {"day": 1, "slots": list(range(0, 5))},
        {"day": 2, "slots": list(range(5, 11))},
    ],
    "בן שלמה אליקים": [        # option A : א'+ד' complets, ב' dès P5, jamais ג'/ה'
        {"day": 1, "slots": list(range(0, 4))},
        {"day": 2, "slots": list(range(0, 11))},
        {"day": 4, "slots": list(range(0, 11))},
    ],
}


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

    # Grille : 5 jours × 11 périodes
    for d in range(5):
        for s in range(11):
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

    # Groupes
    n_groups = 0
    for g in data["groups"]:
        grp = Group(
            school_id=school.id,
            grade_id=grade_of(g["classes"][0]).id if g["classes"] else grades["G7"].id,
            subject_id=subjects[g["subject"]].id,
            label=f"{g['subject']} {'+'.join(g['classes'])}"[:190],
            hours_per_week=max(1, g["hours"]),
            group_type=GroupType.LEVEL_GROUP if g["cohort"] is not None else GroupType.WHOLE_CLASS,
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

    def add_constraint(ctype, params, desc, role=ConstraintOriginRole.SCHOOL_ADMIN):
        nonlocal n_constraints
        db.add(Constraint(
            school_id=school.id, constraint_type=ctype,
            priority=ConstraintPriority.HARD, parameters=params,
            is_active=True, origin_role=role, origin_description=desc,
        ))
        n_constraints += 1

    # 1. Dispos שחף (sauf profs overridés)
    for t in data["teachers"]:
        name = t["name"]
        if name in OVERRIDES or not t["blocked"]:
            continue
        by_day = defaultdict(list)
        for b in t["blocked"]:
            by_day[b["day"]].append(b["slot"])
        for d, slots in by_day.items():
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [d], "slot_indices": sorted(set(slots)),
                 "target_id": teachers[name].id},
                f"אילוצי שחף — {name}", ConstraintOriginRole.TEACHER,
            )

    # 2. Overrides (Yossef / טוולייה / אליקים)
    for name, blocks in OVERRIDES.items():
        if name not in teachers:
            print(f"  ⚠ Override : prof introuvable {name}")
            continue
        for b in blocks:
            add_constraint(
                ConstraintType.BLOCK_SLOT_TEACHER,
                {"days": [b["day"]], "slot_indices": b["slots"],
                 "target_id": teachers[name].id},
                f"עבודה בבי\"ס אחר / כולל — {name}", ConstraintOriginRole.TEACHER,
            )

    # 3. Jour libre pour chaque prof réel
    for t in data["teachers"]:
        add_constraint(
            ConstraintType.TEACHER_FREE_DAY,
            {"teacher_id": teachers[t["name"]].id, "min_free_days": 1},
            f"יום חופשי — {t['name']}",
        )

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
    for subj_name, lo, hi, w in [
        ("תפילה", 0, 0, 60),
        ("שיח בוקר", 0, 1, 50),
        ("חינוך", 0, 2, 40),
    ]:
        if subj_name in subjects:
            add_constraint_soft(subj_name, lo, hi, w,
                                f"{subj_name} — עדיף בפתיחת היום")
            n_constraints += 1

    # 4. Surplus de barrette en fin de journée — UNIQUEMENT pour les liens
    # mono-matière (règle יחידות 3/5 : les heures de surplus des 5 יח' vont
    # en fin de journée). Les clusters מגמות multi-matières n'y sont pas soumis.
    group_hours_by_cohort = defaultdict(set)
    for g in data["groups"]:
        if g["cohort"] is not None:
            group_hours_by_cohort[g["cohort"]].add(max(1, g["hours"]))
    n_edge = 0
    for ci, hours_set in group_hours_by_cohort.items():
        if len(hours_set) >= 2 and data["cohorts"][ci].get("same_subject"):
            add_constraint(
                ConstraintType.EXTRA_HOURS_AT_DAY_EDGE,
                {"cohort_id": cohort_objs[ci].id, "edge": "end", "edge_size": 3},
                f"שעות עודף בסוף היום — {cohort_objs[ci].label[:80]}",
            )
            n_edge += 1

    db.commit()
    print(f"✅ Import terminé — school_id={school.id}")
    print(f"   {len(classes)} classes, {len(subjects)} matières, "
          f"{len(data['teachers'])} profs + {len(data['placeholders'])} placeholders")
    print(f"   {n_groups} groupes, {len(cohort_objs)} cohortes")
    print(f"   {n_constraints} contraintes (dont {n_edge} extra_hours_at_day_edge)")


if __name__ == "__main__":
    main()
